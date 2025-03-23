import os
from pathlib import Path

import fitz  # PyMuPDF


class BookController:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._current_book = None

    def get_all_books(self, category_id=None, series_id=None, status=None):
        from models.book import Book

        query_params = {}
        if status:
            query_params["status"] = status

        if series_id:
            # シリーズIDが指定されている場合は、そのシリーズの書籍のみを取得
            book_data_list = self.db_manager.get_books_in_series(series_id)

            # ステータスフィルタが指定されている場合はさらにフィルタリング
            if status:
                book_data_list = [
                    book for book in book_data_list if book.get("status") == status
                ]
        elif category_id:
            # カテゴリIDが指定されている場合
            book_data_list = self.db_manager.get_books_by_category(
                category_id, **query_params
            )
        else:
            # それ以外は検索条件に基づいて取得
            book_data_list = self.db_manager.search_books(**query_params)

        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def search_books(self, query):
        from models.book import Book

        book_data_list = self.db_manager.search_books(query=query)
        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def get_book(self, book_id):
        from models.book import Book

        book_data = self.db_manager.get_book(book_id)
        if book_data:
            return Book(book_data, self.db_manager)
        return None

    def get_current_book(self):
        return self._current_book

    def set_current_book(self, book):
        # 現在の書籍がある場合は閉じる
        if self._current_book:
            self._current_book.close()

        self._current_book = book

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

    def batch_update_metadata(self, book_ids, metadata):
        return self.db_manager.batch_update_metadata(book_ids, metadata)

    def remove_book(self, book_id, delete_file=False):
        book = self.get_book(book_id)
        if not book:
            return False

        if self._current_book and self._current_book.id == book_id:
            self._current_book.close()
            self._current_book = None

        file_path = book.file_path

        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM reading_progress WHERE book_id = ?", (book_id,))

            cursor.execute("DELETE FROM custom_metadata WHERE book_id = ?", (book_id,))

            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))

            conn.commit()

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
