import os
from pathlib import Path

import fitz  # PyMuPDF

from models.book import Book
from models.series import Series


class LibraryController:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._current_book = None

    def get_all_books(self, category_id=None, series_id=None, status=None):
        query_params = {}
        if status:
            query_params["status"] = status

        if series_id:
            book_data_list = self.db_manager.get_books_in_series(series_id)

            if status:
                book_data_list = [
                    book for book in book_data_list if book.get("status") == status
                ]
        elif category_id:
            book_data_list = self.db_manager.get_books_by_category(
                category_id, **query_params
            )
        else:
            book_data_list = self.db_manager.search_books(**query_params)

        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def search_books(self, query):
        book_data_list = self.db_manager.search_books(query=query)
        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def get_book(self, book_id):
        book_data = self.db_manager.get_book(book_id)
        if book_data:
            return Book(book_data, self.db_manager)
        return None

    def get_current_book(self):
        return self._current_book

    def set_current_book(self, book):
        if self._current_book:
            self._current_book.close()

        self._current_book = book

    def import_pdf(
        self,
        file_path,
        title=None,
        author=None,
        publisher=None,
        series_id=None,
        series_order=None,
    ):
        if not os.path.isfile(file_path) or not file_path.lower().endswith(".pdf"):
            return None

        if not title:
            title = Path(file_path).stem

        try:
            doc = fitz.open(file_path)

            if not author and "author" in doc.metadata:
                author = doc.metadata["author"]

            total_pages = len(doc)

            cover_image = None
            if total_pages > 0:
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))  # 縮小して取得
                cover_image = pix.tobytes()

            doc.close()

            book_id = self.db_manager.add_book(
                title=title,
                file_path=file_path,
                series_id=series_id,
                series_order=series_order,
                author=author,
                publisher=publisher,
                cover_image=cover_image,
            )

            self.db_manager.update_reading_progress(book_id, total_pages=total_pages)

            return book_id
        except Exception as e:
            print(f"Error importing PDF: {e}")
            return None

    def batch_import_pdfs(self, file_paths, common_metadata=None):
        if common_metadata is None:
            common_metadata = {}

        imported_ids = []

        for file_path in file_paths:
            book_id = self.import_pdf(
                file_path=file_path,
                title=None,
                author=common_metadata.get("author"),
                publisher=common_metadata.get("publisher"),
                series_id=common_metadata.get("series_id"),
                series_order=None,
            )

            if book_id:
                imported_ids.append(book_id)
                custom_metadata = {
                    k: v
                    for k, v in common_metadata.items()
                    if k not in ["author", "publisher", "series_id", "series_order"]
                }

                if custom_metadata:
                    book = self.get_book(book_id)
                    if book:
                        book.update_metadata(**custom_metadata)

        return imported_ids

    def get_all_series(self, category_id=None):
        series_data_list = self.db_manager.get_all_series(category_id)
        return [
            Series(series_data, self.db_manager) for series_data in series_data_list
        ]

    def get_series(self, series_id):
        series_data = self.db_manager.get_series(series_id)
        if series_data:
            return Series(series_data, self.db_manager)
        return None

    def create_series(self, name, description=None, category_id=None):
        try:
            series_id = self.db_manager.add_series(
                name=name, description=description, category_id=category_id
            )
            return series_id
        except Exception as e:
            print(f"Error creating series: {e}")
            return None

    def get_all_categories(self):
        return self.db_manager.get_all_categories()

    def create_category(self, name, description=None):
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
            INSERT INTO categories (name, description)
            VALUES (?, ?)
            """,
                (name, description),
            )

            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating category: {e}")
            conn.rollback()
            return None

    def update_book_progress(self, book_id, current_page=None, status=None):
        book = self.get_book(book_id)
        if book:
            return book.update_progress(current_page=current_page, status=status)
        return False

    def update_book_metadata(self, book_id, **metadata):
        book = self.get_book(book_id)
        if book:
            # 更新を実行
            success = book.update_metadata(**metadata)

            # デバッグ: 更新後のデータベースの状態を直接確認
            if success:
                # データベースから直接クエリで確認
                conn = self.db_manager.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT category_id FROM books WHERE id = ?", (book_id,))
                result = cursor.fetchone()
                if result:
                    print(
                        f"Database after update - Book {book_id}: category_id={result['category_id']}"
                    )

                # 更新後の書籍オブジェクトを取得して確認
                updated_book = self.get_book(book_id)
                print(
                    f"Updated book object - Book {book_id}: category_id={updated_book.category_id}"
                )

            return success
        return False

    def batch_update_metadata(self, book_ids, **metadata):
        return self.db_manager.batch_update_metadata(book_ids, metadata)

    def remove_book(self, book_id, delete_file=False):
        book = self.get_book(book_id)
        if not book:
            return False

        # 現在開いている書籍なら閉じる
        if self._current_book and self._current_book.id == book_id:
            self._current_book.close()
            self._current_book = None

        file_path = book.file_path

        # データベースから削除
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            # 読書進捗を削除
            cursor.execute("DELETE FROM reading_progress WHERE book_id = ?", (book_id,))

            # カスタムメタデータを削除
            cursor.execute("DELETE FROM custom_metadata WHERE book_id = ?", (book_id,))

            # 書籍を削除
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))

            conn.commit()

            # ファイルを削除（オプション）
            if delete_file and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Error deleting file: {e}")

            return True
        except Exception as e:
            print(f"Error removing book: {e}")
            conn.rollback()
            return False

    def batch_remove_books(self, book_ids, delete_files=False):
        if not book_ids:
            return {"success": [], "failed": []}

        success_ids = []
        failed_ids = []

        current_book = self._current_book
        current_book_id = current_book.id if current_book else None

        for book_id in book_ids:
            if current_book_id == book_id:
                current_book.close()
                self._current_book = None
            book = self.get_book(book_id)
            if not book:
                failed_ids.append(book_id)
                continue

            file_path = book.file_path

            conn = self.db_manager.connect()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "DELETE FROM reading_progress WHERE book_id = ?", (book_id,)
                )

                cursor.execute(
                    "DELETE FROM custom_metadata WHERE book_id = ?", (book_id,)
                )

                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))

                conn.commit()

                if delete_files and os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Error deleting file: {e}")

                success_ids.append(book_id)
            except Exception as e:
                print(f"Error removing book {book_id}: {e}")
                conn.rollback()
                failed_ids.append(book_id)

        return {"success": success_ids, "failed": failed_ids}

    def get_category(self, category_id):
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM categories
            WHERE id = ?
            """,
            (category_id,),
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def update_category(self, category_id, name, description=None):
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE categories
                SET name = ?, description = ?
                WHERE id = ?
                """,
                (name, description, category_id),
            )

            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating category: {e}")
            conn.rollback()
            return False

    def delete_category(self, category_id):
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE series
                SET category_id = NULL
                WHERE category_id = ?
                """,
                (category_id,),
            )

            cursor.execute(
                """
                DELETE FROM categories
                WHERE id = ?
                """,
                (category_id,),
            )

            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            conn.rollback()
            return False
