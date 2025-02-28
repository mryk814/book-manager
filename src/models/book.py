import io
import os
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageChops


class Book:
    """
    PDFの書籍を表すクラス。

    データベース内の書籍レコードのラッパーとして機能し、
    PDFファイルとの連携インターフェースも提供する。

    Parameters
    ----------
    book_data : dict
        データベースから取得した書籍データ
    db_manager : DatabaseManager
        データベースマネージャーのインスタンス
    """

    # 読書状態の定義
    STATUS_UNREAD = "unread"
    STATUS_READING = "reading"
    STATUS_COMPLETED = "completed"

    def __init__(self, book_data, db_manager):
        """
        Parameters
        ----------
        book_data : dict
            書籍の情報を含む辞書
        db_manager : DatabaseManager
            データベース接続マネージャ
        """
        self.data = book_data
        self.db_manager = db_manager
        self._document = None
        self._custom_metadata = None

    @property
    def id(self):
        """書籍のID"""
        return self.data.get("id")

    @property
    def title(self):
        """書籍のタイトル"""
        return self.data.get("title")

    @property
    def author(self):
        """書籍の著者"""
        return self.data.get("author")

    @property
    def publisher(self):
        """書籍の出版社"""
        return self.data.get("publisher")

    @property
    def file_path(self):
        """PDFファイルへのパス"""
        return self.data.get("file_path")

    @property
    def series_id(self):
        """所属するシリーズのID"""
        return self.data.get("series_id")

    @property
    def series_order(self):
        """シリーズ内の順番"""
        return self.data.get("series_order")

    @property
    def status(self):
        """読書状態"""
        return self.data.get("status", self.STATUS_UNREAD)

    @property
    def current_page(self):
        """現在のページ"""
        return self.data.get("current_page", 0)

    @property
    def total_pages(self):
        """総ページ数"""
        if not self.data.get("total_pages") and self.exists():
            self._load_pdf_metadata()
        return self.data.get("total_pages", 0)

    @property
    def last_read_date(self):
        """最後に読んだ日時"""
        return self.data.get("last_read_date")

    @property
    def custom_metadata(self):
        """カスタムメタデータ"""
        if self._custom_metadata is None:
            self._custom_metadata = self.db_manager.get_custom_metadata(book_id=self.id)
        return self._custom_metadata

    @property
    def category_id(self):
        """書籍のカテゴリID"""
        return self.data.get("category_id")

    @property
    def category_name(self):
        """書籍のカテゴリ名"""
        if self.category_id:
            category = self.db_manager.get_category(self.category_id)
            return category["name"] if category else None
        return None

    def exists(self):
        """
        PDFファイルが存在するか確認する。

        Returns
        -------
        bool
            ファイルが存在する場合はTrue、それ以外はFalse
        """
        return os.path.isfile(self.file_path)

    def open(self):
        """
        PDFドキュメントを開く。

        Returns
        -------
        fitz.Document または None
            ドキュメントオブジェクト、もしくはファイルが存在しない場合はNone
        """
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
        """PDFドキュメントを閉じる。"""
        if self._document:
            self._document.close()
            self._document = None

    def _load_pdf_metadata(self):
        """PDFファイルからメタデータを読み込む。"""
        try:
            doc = self.open()
            if doc:
                # 総ページ数を更新
                total_pages = len(doc)
                self.data["total_pages"] = total_pages
                self.db_manager.update_reading_progress(
                    self.id, total_pages=total_pages
                )

                # PDFのメタデータを取得（ただし、手動設定を優先）
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

    def get_page(self, page_number):
        """
        指定ページのPixmapを取得する。

        Parameters
        ----------
        page_number : int
            取得するページ番号（0から始まる）

        Returns
        -------
        fitz.Pixmap または None
            ページのPixmap、もしくはエラー時はNone
        """
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
        """
        読書進捗を更新する。

        Parameters
        ----------
        current_page : int, optional
            現在のページ番号
        status : str, optional
            読書状態 ('unread', 'reading', 'completed')

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        # 状態の自動推定（オプション）
        if current_page is not None and status is None:
            if current_page == 0:
                status = self.STATUS_UNREAD
            elif current_page >= self.total_pages - 1:  # 最後のページか、その近く
                status = self.STATUS_COMPLETED
            else:
                status = self.STATUS_READING

        success = self.db_manager.update_reading_progress(
            self.id, current_page=current_page, status=status
        )

        if success:
            # データをメモリ上でも更新
            if current_page is not None:
                self.data["current_page"] = current_page
            if status is not None:
                self.data["status"] = status

        return success

    def get_cover_image(self, force_reload=False, thumbnail_size=None, auto_trim=True):
        """
        表紙画像を取得する。

        Parameters
        ----------
        force_reload : bool, optional
            強制的にPDFから再ロードするかどうか
        thumbnail_size : tuple, optional
            サムネイルサイズ (width, height)。指定しない場合は通常サイズで取得。
        auto_trim : bool, optional
            左右の白い余白を自動的にトリミングするかどうか

        Returns
        -------
        bytes または None
            表紙画像のバイナリデータ、もしくはエラー時はNone
        """
        # 通常サイズのキャッシュがあり、サムネイルが不要なら通常の処理
        cache_key = "cover_image"
        if thumbnail_size:
            # サムネイルサイズのキーを生成（キャッシュ用）
            cache_key = f"cover_image_{thumbnail_size[0]}x{thumbnail_size[1]}"
            if auto_trim:
                cache_key += "_h_trimmed"  # 水平トリミングを示す

        # キャッシュがあれば使用
        if not force_reload and self.data.get(cache_key):
            return self.data.get(cache_key)

        if not self.exists():
            return None

        try:
            doc = self.open()
            if doc and len(doc) > 0:
                # 最初のページを表紙として使用
                page = doc[0]

                # ピクセルマップを取得
                if thumbnail_size:
                    # サムネイルサイズに応じた縮小率を計算
                    rect = page.rect
                    page_width, page_height = rect.width, rect.height
                    target_width, target_height = thumbnail_size

                    # 縦横比を維持したスケール計算
                    scale_width = target_width / page_width
                    scale_height = target_height / page_height
                    scale = (
                        min(scale_width, scale_height) * 1.2
                    )  # 少し大きめに取得してトリミング可能にする

                    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                else:
                    # 通常サイズ（やや縮小）
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))

                # PIL/Pillowを使用して処理
                try:
                    import io

                    from PIL import Image, ImageChops

                    # ピクセルマップからPIL Imageを作成
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # 自動トリミングを適用（横方向のみ）
                    if auto_trim:
                        img = self._trim_horizontal_white_borders(img)

                    # サムネイルサイズにリサイズ
                    if thumbnail_size:
                        target_width, target_height = thumbnail_size

                        # 縦横比を維持したスケール計算
                        img_width, img_height = img.size
                        scale_width = target_width / img_width
                        scale_height = target_height / img_height
                        scale = min(scale_width, scale_height)

                        new_width = int(img_width * scale)
                        new_height = int(img_height * scale)

                        img = img.resize((new_width, new_height), Image.LANCZOS)

                        # 中央揃えのための処理（余白を追加）
                        if new_width < target_width or new_height < target_height:
                            new_img = Image.new(
                                "RGB", (target_width, target_height), (255, 255, 255)
                            )
                            paste_x = (target_width - new_width) // 2
                            paste_y = (target_height - new_height) // 2
                            new_img.paste(img, (paste_x, paste_y))
                            img = new_img

                    # JPEGとして圧縮保存
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85, optimize=True)
                    img_data = buffer.getvalue()

                    # キャッシュに保存
                    self.data[cache_key] = img_data

                    # 通常サイズの場合はデータベースにも保存
                    if not thumbnail_size and not auto_trim:
                        self.db_manager.update_book(self.id, cover_image=img_data)
                        self.data["cover_image"] = img_data

                    return img_data
                except ImportError:
                    # PILがない場合は圧縮なしで続行
                    img_data = pix.tobytes()
                    self.data[cache_key] = img_data
                    return img_data
        except Exception as e:
            print(f"Error generating cover image: {e}")

        return None

    def _trim_horizontal_white_borders(self, image, threshold=245, min_margin=5):
        """
        画像の左右の白い余白部分のみをトリミングする。
        縦の高さは変更せず、横幅だけを最適化する。

        Parameters
        ----------
        image : PIL.Image
            トリミングする画像
        threshold : int, optional
            白と判断する閾値（0-255）
        min_margin : int, optional
            最低限残す余白のピクセル数

        Returns
        -------
        PIL.Image
            横方向のみトリミングされた画像
        """
        try:
            width, height = image.size

            # 横方向の境界を検出するためのヒストグラム的なアプローチ
            left_bound = 0
            right_bound = width - 1

            # グレースケールに変換して処理を効率化
            gray_img = image.convert("L")

            # 左から内側に向かってスキャン
            for x in range(width // 2):
                # 列の平均明度を計算
                column = [gray_img.getpixel((x, y)) for y in range(height)]
                avg_brightness = sum(column) / len(column)

                # 平均明度が閾値より低い（白でない）場合、これが左の境界
                if avg_brightness < threshold:
                    left_bound = max(0, x - min_margin)  # マージンを考慮
                    break

            # 右から内側に向かってスキャン
            for x in range(width - 1, width // 2, -1):
                # 列の平均明度を計算
                column = [gray_img.getpixel((x, y)) for y in range(height)]
                avg_brightness = sum(column) / len(column)

                # 平均明度が閾値より低い（白でない）場合、これが右の境界
                if avg_brightness < threshold:
                    right_bound = min(width - 1, x + min_margin)  # マージンを考慮
                    break

            # トリミングが必要な場合のみ実行
            if left_bound > 0 or right_bound < width - 1:
                # 水平方向のみトリミング
                return image.crop((left_bound, 0, right_bound + 1, height))
        except Exception as e:
            print(f"Error trimming horizontal borders: {e}")

        # エラー時や変更不要時は元の画像を返す
        return image

    def update_metadata(self, **kwargs):
        """
        書籍のメタデータを更新する。

        Parameters
        ----------
        **kwargs
            更新するフィールドと値のペア

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        # 標準フィールドとカスタムフィールドを分離
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

        # 標準フィールドの更新
        if standard_updates:
            db_success = self.db_manager.update_book(self.id, **standard_updates)
            if db_success:
                # ローカルデータを更新
                for k, v in standard_updates.items():
                    self.data[k] = v
            success = success and db_success

        # カスタムメタデータの更新
        for key, value in custom_updates.items():
            meta_success = self.db_manager.set_custom_metadata(
                book_id=self.id, key=key, value=value
            )
            if meta_success and self._custom_metadata is not None:
                self._custom_metadata[key] = value
            success = success and meta_success

        return success
