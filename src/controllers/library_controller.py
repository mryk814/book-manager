import os
from pathlib import Path

import fitz  # PyMuPDF

from models.book import Book
from models.series import Series


class LibraryController:
    """
    ライブラリのビジネスロジックを管理するコントローラクラス。

    モデルとビューの間のインタフェースとして機能し、
    書籍、シリーズ、カテゴリなどのライブラリコンテンツを操作する。

    Parameters
    ----------
    db_manager : DatabaseManager
        データベースマネージャーのインスタンス
    """

    def __init__(self, db_manager):
        """
        Parameters
        ----------
        db_manager : DatabaseManager
            データベース接続マネージャ
        """
        self.db_manager = db_manager
        self._current_book = None

    def get_all_books(self, category_id=None, series_id=None, status=None):
        """
        条件に合う書籍のリストを取得する。

        Parameters
        ----------
        category_id : int, optional
            特定のカテゴリに属する書籍のみを取得
        series_id : int, optional
            特定のシリーズに属する書籍のみを取得
        status : str, optional
            特定の読書状態の書籍のみを取得

        Returns
        -------
        list
            Book オブジェクトのリスト
        """
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
        """
        書籍を検索する。

        Parameters
        ----------
        query : str
            検索クエリ

        Returns
        -------
        list
            Book オブジェクトのリスト
        """
        book_data_list = self.db_manager.search_books(query=query)
        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def get_book(self, book_id):
        """
        指定したIDの書籍を取得する。

        Parameters
        ----------
        book_id : int
            書籍のID

        Returns
        -------
        Book または None
            指定IDの書籍、もしくは見つからない場合はNone
        """
        book_data = self.db_manager.get_book(book_id)
        if book_data:
            return Book(book_data, self.db_manager)
        return None

    def get_current_book(self):
        """
        現在アクティブな書籍を取得する。

        Returns
        -------
        Book または None
            現在の書籍、もしくは設定されていない場合はNone
        """
        return self._current_book

    def set_current_book(self, book):
        """
        現在アクティブな書籍を設定する。

        Parameters
        ----------
        book : Book
            アクティブにする書籍
        """
        # 現在の書籍がある場合は閉じる
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
        """
        PDFをライブラリにインポートする。

        Parameters
        ----------
        file_path : str
            PDFファイルへのパス
        title : str, optional
            書籍のタイトル（指定しない場合はファイル名から自動生成）
        author : str, optional
            著者名
        publisher : str, optional
            出版社名
        series_id : int, optional
            所属するシリーズのID
        series_order : int, optional
            シリーズ内の順番

        Returns
        -------
        int または None
            追加された書籍のID、もしくは失敗した場合はNone
        """
        if not os.path.isfile(file_path) or not file_path.lower().endswith(".pdf"):
            return None

        # タイトルが指定されていない場合はファイル名から生成
        if not title:
            title = Path(file_path).stem

        try:
            # ファイルを開いてメタデータを取得
            doc = fitz.open(file_path)

            # 著者が指定されていない場合はPDFから取得
            if not author and "author" in doc.metadata:
                author = doc.metadata["author"]

            # 総ページ数を取得
            total_pages = len(doc)

            # 表紙画像を取得
            cover_image = None
            if total_pages > 0:
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))  # 縮小して取得
                cover_image = pix.tobytes()

            doc.close()

            # データベースに書籍を追加
            book_id = self.db_manager.add_book(
                title=title,
                file_path=file_path,
                series_id=series_id,
                series_order=series_order,
                author=author,
                publisher=publisher,
                cover_image=cover_image,
            )

            # 総ページ数を更新
            self.db_manager.update_reading_progress(book_id, total_pages=total_pages)

            return book_id
        except Exception as e:
            print(f"Error importing PDF: {e}")
            return None

    def batch_import_pdfs(self, file_paths, common_metadata=None):
        """
        複数のPDFを一括インポートする。

        Parameters
        ----------
        file_paths : list
            PDFファイルへのパスのリスト
        common_metadata : dict, optional
            すべての書籍に適用する共通メタデータ

        Returns
        -------
        list
            インポートに成功した書籍IDのリスト
        """
        if common_metadata is None:
            common_metadata = {}

        imported_ids = []

        for file_path in file_paths:
            book_id = self.import_pdf(
                file_path=file_path,
                title=None,  # ファイル名から自動生成
                author=common_metadata.get("author"),
                publisher=common_metadata.get("publisher"),
                series_id=common_metadata.get("series_id"),
                series_order=None,  # 自動的に最後に追加
            )

            if book_id:
                imported_ids.append(book_id)

                # カスタムメタデータがあれば設定
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
        """
        シリーズのリストを取得する。

        Parameters
        ----------
        category_id : int, optional
            特定のカテゴリに属するシリーズのみを取得

        Returns
        -------
        list
            Series オブジェクトのリスト
        """
        series_data_list = self.db_manager.get_all_series(category_id)
        return [
            Series(series_data, self.db_manager) for series_data in series_data_list
        ]

    def get_series(self, series_id):
        """
        指定したIDのシリーズを取得する。

        Parameters
        ----------
        series_id : int
            シリーズのID

        Returns
        -------
        Series または None
            指定IDのシリーズ、もしくは見つからない場合はNone
        """
        series_data = self.db_manager.get_series(series_id)
        if series_data:
            return Series(series_data, self.db_manager)
        return None

    def create_series(self, name, description=None, category_id=None):
        """
        新しいシリーズを作成する。

        Parameters
        ----------
        name : str
            シリーズ名
        description : str, optional
            シリーズの説明
        category_id : int, optional
            所属するカテゴリのID

        Returns
        -------
        int または None
            追加されたシリーズのID、もしくは失敗した場合はNone
        """
        try:
            series_id = self.db_manager.add_series(
                name=name, description=description, category_id=category_id
            )
            return series_id
        except Exception as e:
            print(f"Error creating series: {e}")
            return None

    def get_all_categories(self):
        """
        すべてのカテゴリを取得する。

        Returns
        -------
        list
            カテゴリ情報の辞書のリスト
        """
        return self.db_manager.get_all_categories()

    def create_category(self, name, description=None):
        """
        新しいカテゴリを作成する。

        Parameters
        ----------
        name : str
            カテゴリ名
        description : str, optional
            カテゴリの説明

        Returns
        -------
        int または None
            追加されたカテゴリのID、もしくは失敗した場合はNone
        """
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
        """
        書籍の読書進捗を更新する。

        Parameters
        ----------
        book_id : int
            書籍のID
        current_page : int, optional
            現在のページ番号
        status : str, optional
            読書状態

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        book = self.get_book(book_id)
        if book:
            return book.update_progress(current_page=current_page, status=status)
        return False

    def update_book_metadata(self, book_id, **metadata):
        """
        書籍のメタデータを更新する。

        Parameters
        ----------
        book_id : int
            書籍のID
        **metadata
            更新するメタデータのキーと値

        Returns
        -------
        bool
            更新が成功したかどうか
        """

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
        """
        複数の書籍のメタデータを一括更新する。

        Parameters
        ----------
        book_ids : list
            更新する書籍IDのリスト
        **metadata
            更新するメタデータのキーと値

        Returns
        -------
        int
            更新された書籍の数
        """
        return self.db_manager.batch_update_metadata(book_ids, metadata)

    def remove_book(self, book_id, delete_file=False):
        """
        書籍をライブラリから削除する。

        Parameters
        ----------
        book_id : int
            削除する書籍のID
        delete_file : bool, optional
            ファイル自体も削除するかどうか

        Returns
        -------
        bool
            削除が成功したかどうか
        """
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
        """
        複数の書籍をライブラリから一括で削除する。

        Parameters
        ----------
        book_ids : list
            削除する書籍IDのリスト
        delete_files : bool, optional
            ファイル自体も削除するかどうか

        Returns
        -------
        dict
            成功したIDのリストと失敗したIDのリスト
        """
        if not book_ids:
            return {"success": [], "failed": []}

        success_ids = []
        failed_ids = []

        # 現在開いている書籍をチェック
        current_book = self._current_book
        current_book_id = current_book.id if current_book else None

        for book_id in book_ids:
            # 現在開いている書籍なら閉じる
            if current_book_id == book_id:
                current_book.close()
                self._current_book = None

            # 書籍情報を取得
            book = self.get_book(book_id)
            if not book:
                failed_ids.append(book_id)
                continue

            file_path = book.file_path

            # データベースから削除
            conn = self.db_manager.connect()
            cursor = conn.cursor()

            try:
                # 読書進捗を削除
                cursor.execute(
                    "DELETE FROM reading_progress WHERE book_id = ?", (book_id,)
                )

                # カスタムメタデータを削除
                cursor.execute(
                    "DELETE FROM custom_metadata WHERE book_id = ?", (book_id,)
                )

                # 書籍を削除
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))

                conn.commit()

                # ファイルを削除（オプション）
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
        """
        指定したIDのカテゴリ情報を取得する。

        Parameters
        ----------
        category_id : int
            取得するカテゴリのID

        Returns
        -------
        dict または None
            カテゴリ情報の辞書、もしくは見つからない場合はNone
        """
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
        """
        カテゴリを更新する。

        Parameters
        ----------
        category_id : int
            更新するカテゴリのID
        name : str
            カテゴリ名
        description : str, optional
            カテゴリの説明

        Returns
        -------
        bool
            更新が成功したかどうか
        """
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
        """
        カテゴリを削除する。

        Parameters
        ----------
        category_id : int
            削除するカテゴリのID

        Returns
        -------
        bool
            削除が成功したかどうか
        """
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            # カテゴリに所属するシリーズのカテゴリIDをNULLに設定
            cursor.execute(
                """
                UPDATE series
                SET category_id = NULL
                WHERE category_id = ?
                """,
                (category_id,),
            )

            # カテゴリを削除
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
