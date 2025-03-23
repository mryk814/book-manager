import hashlib
import io
import os
import time
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageChops


class Book:
    STATUS_UNREAD = "unread"
    STATUS_READING = "reading"
    STATUS_COMPLETED = "completed"

    _cover_cache = {}
    _cache_size_limit = 300
    _cache_time_limit = 600

    def __init__(self, book_data, db_manager):
        self.data = book_data
        self.db_manager = db_manager
        self._document = None
        self._custom_metadata = None
        self._local_cover_cache = {}

    @property
    def id(self):
        return self.data.get("id")

    @property
    def title(self):
        return self.data.get("title")

    @property
    def author(self):
        return self.data.get("author")

    @property
    def publisher(self):
        return self.data.get("publisher")

    @property
    def file_path(self):
        return self.data.get("file_path")

    @property
    def series_id(self):
        return self.data.get("series_id")

    @property
    def series_order(self):
        return self.data.get("series_order")

    @property
    def status(self):
        return self.data.get("status", self.STATUS_UNREAD)

    @property
    def current_page(self):
        return self.data.get("current_page", 0)

    @property
    def total_pages(self):
        if not self.data.get("total_pages") and self.exists():
            self._load_pdf_metadata()
        return self.data.get("total_pages", 0)

    @property
    def last_read_date(self):
        return self.data.get("last_read_date")

    @property
    def custom_metadata(self):
        if self._custom_metadata is None:
            self._custom_metadata = self.db_manager.get_custom_metadata(book_id=self.id)
        return self._custom_metadata

    @property
    def category_id(self):
        return self.data.get("category_id")

    @property
    def category_name(self):
        if self.category_id:
            category = self.db_manager.get_category(self.category_id)
            return category["name"] if category else None
        return None

    def exists(self):
        return os.path.isfile(self.file_path)

    def open(self):
        if not self.exists():
            return None

        if self._document is None:
            try:
                self._document = fitz.open(self.file_path)

                # 初回オープン時に総ページ数を更新
                if not self.data.get("total_pages"):
                    self._load_pdf_metadata()
            except Exception as e:
                print(f"Error opening PDF: {e}")
                return None

        return self._document

    def close(self):
        if self._document:
            self._document.close()
            self._document = None

    def _load_pdf_metadata(self):
        try:
            doc = self.open()
            if doc:
                total_pages = len(doc)
                self.data["total_pages"] = total_pages
                self.db_manager.update_reading_progress(
                    self.id, total_pages=total_pages
                )

                if not self.title or self.title == os.path.basename(self.file_path):
                    pdf_title = doc.metadata.get("title")
                    if pdf_title:
                        self.data["title"] = pdf_title
                        self.db_manager.update_book(self.id, title=pdf_title)

                if not self.author:
                    pdf_author = doc.metadata.get("author")
                    if pdf_author:
                        self.data["author"] = pdf_author
                        self.db_manager.update_book(self.id, author=pdf_author)
        except Exception as e:
            print(f"Error reading PDF metadata: {e}")

    @classmethod
    def _cleanup_cache(cls):
        current_time = time.time()

        if len(cls._cover_cache) > cls._cache_size_limit:
            entries = sorted(cls._cover_cache.items(), key=lambda x: x[1][0])
            for key, _ in entries[: cls._cache_size_limit // 2]:
                del cls._cover_cache[key]

        expired_keys = [
            key
            for key, (timestamp, _) in cls._cover_cache.items()
            if current_time - timestamp > cls._cache_time_limit
        ]
        for key in expired_keys:
            del cls._cover_cache[key]

    def get_page(self, page_number):
        doc = self.open()
        if not doc or page_number < 0 or page_number >= len(doc):
            return None

        try:
            page = doc[page_number]
            return page.get_pixmap()
        except Exception as e:
            print(f"Error rendering page {page_number}: {e}")
            return None

    def update_progress(self, current_page=None, status=None):
        if current_page is not None and status is None:
            if current_page == 0:
                status = self.STATUS_UNREAD
            elif current_page >= self.total_pages - 1:
                status = self.STATUS_COMPLETED
            else:
                status = self.STATUS_READING

        success = self.db_manager.update_reading_progress(
            self.id, current_page=current_page, status=status
        )

        if success:
            if current_page is not None:
                self.data["current_page"] = current_page
            if status is not None:
                self.data["status"] = status

        return success

    def _get_cache_key(self, thumbnail_size=None, auto_trim=False):
        base_key = f"{self.id}_{self.file_path}"

        if thumbnail_size:
            size_key = f"_{thumbnail_size[0]}x{thumbnail_size[1]}"
            if auto_trim:
                size_key += "_trimmed"
        else:
            size_key = "_full"

        hash_key = hashlib.md5(f"{base_key}{size_key}".encode()).hexdigest()
        return hash_key

    def get_cover_image(self, force_reload=False, thumbnail_size=None, auto_trim=True):
        cache_key = self._get_cache_key(thumbnail_size, auto_trim)

        if not force_reload and cache_key in self._cover_cache:
            timestamp, data = self._cover_cache[cache_key]
            if time.time() - timestamp <= self._cache_time_limit:
                return data

        if not force_reload and cache_key in self._local_cover_cache:
            return self._local_cover_cache[cache_key]

        if (
            not force_reload
            and not thumbnail_size
            and not auto_trim
            and self.data.get("cover_image")
        ):
            self._local_cover_cache[cache_key] = self.data["cover_image"]
            self._cover_cache[cache_key] = (time.time(), self.data["cover_image"])
            if len(self._cover_cache) > self._cache_size_limit:
                self._cleanup_cache()
            return self.data["cover_image"]

        if not self.exists():
            return None

        try:
            doc = self.open()
            if doc and len(doc) > 0:
                page = doc[0]

                if thumbnail_size:
                    rect = page.rect
                    page_width, page_height = rect.width, rect.height
                    target_width, target_height = thumbnail_size
                    scale_width = target_width / page_width
                    scale_height = target_height / page_height
                    scale = min(scale_width, scale_height) * 1.2

                    try:
                        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                    except Exception as e:
                        print(f"Error getting pixmap for thumbnail: {e}")
                        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                else:
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))

                try:
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    if auto_trim:
                        img = self._trim_horizontal_white_borders(img)

                    if thumbnail_size:
                        target_width, target_height = thumbnail_size

                        img_width, img_height = img.size
                        scale_width = target_width / img_width
                        scale_height = target_height / img_height
                        scale = min(scale_width, scale_height)

                        new_width = int(img_width * scale)
                        new_height = int(img_height * scale)

                        img = img.resize((new_width, new_height), Image.LANCZOS)

                        if new_width < target_width or new_height < target_height:
                            new_img = Image.new(
                                "RGB", (target_width, target_height), (255, 255, 255)
                            )
                            paste_x = (target_width - new_width) // 2
                            paste_y = (target_height - new_height) // 2
                            new_img.paste(img, (paste_x, paste_y))
                            img = new_img

                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85, optimize=True)
                    img_data = buffer.getvalue()

                    self._local_cover_cache[cache_key] = img_data
                    self._cover_cache[cache_key] = (time.time(), img_data)

                    if len(self._cover_cache) > self._cache_size_limit:
                        self._cleanup_cache()

                    if not thumbnail_size and not auto_trim:
                        self.db_manager.update_book(self.id, cover_image=img_data)
                        self.data["cover_image"] = img_data

                    return img_data
                except ImportError:
                    img_data = pix.tobytes()
                    self._local_cover_cache[cache_key] = img_data
                    self._cover_cache[cache_key] = (time.time(), img_data)
                    return img_data
                except Exception as e:
                    print(f"Error processing cover image with PIL: {e}")
                    img_data = pix.tobytes()
                    self._local_cover_cache[cache_key] = img_data
                    self._cover_cache[cache_key] = (time.time(), img_data)
                    return img_data
        except Exception as e:
            print(f"Error generating cover image: {e}")

        return None

    def _trim_horizontal_white_borders(self, image, threshold=245, min_margin=5):
        try:
            width, height = image.size

            gray_img = image.convert("L")

            left_bound = 0
            for x in range(width // 4):
                column = [gray_img.getpixel((x, y)) for y in range(0, height, 4)]
                avg_brightness = sum(column) / len(column)

                if avg_brightness < threshold:
                    left_bound = max(0, x - min_margin)
                    break

            right_bound = width - 1
            for x in range(width - 1, width * 3 // 4, -1):
                column = [gray_img.getpixel((x, y)) for y in range(0, height, 4)]
                avg_brightness = sum(column) / len(column)

                if avg_brightness < threshold:
                    right_bound = min(width - 1, x + min_margin)
                    break

            if left_bound > width * 0.05 or right_bound < width * 0.95:
                return image.crop((left_bound, 0, right_bound + 1, height))
        except Exception as e:
            print(f"Error trimming horizontal borders: {e}")

        return image

    def update_metadata(self, **kwargs):
        standard_fields = {
            "title",
            "author",
            "publisher",
            "series_id",
            "series_order",
            "category_id",
        }
        standard_updates = {k: v for k, v in kwargs.items() if k in standard_fields}
        custom_updates = {k: v for k, v in kwargs.items() if k not in standard_fields}

        success = True

        if standard_updates:
            db_success = self.db_manager.update_book(self.id, **standard_updates)
            if db_success:
                for k, v in standard_updates.items():
                    self.data[k] = v
            success = success and db_success

        for key, value in custom_updates.items():
            meta_success = self.db_manager.set_custom_metadata(
                book_id=self.id, key=key, value=value
            )
            if meta_success and self._custom_metadata is not None:
                self._custom_metadata[key] = value
            success = success and meta_success

        return success
