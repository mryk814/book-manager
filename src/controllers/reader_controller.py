import fitz  # PyMuPDF

from models.book import Book


class ReaderController:
    """
    PDFリーダー機能を管理するコントローラクラス。

    PDFドキュメントの表示、ページナビゲーション、読書進捗の更新などの機能を提供する。

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
        self._current_page = 0

    def get_current_book(self):
        """
        現在開いている書籍を取得する。

        Returns
        -------
        Book または None
            現在開いている書籍、もしくは開いていない場合はNone
        """
        return self._current_book

    def get_current_page(self):
        """
        現在のページ番号を取得する。

        Returns
        -------
        int
            現在のページ番号（0から始まる）
        """
        return self._current_page

    def open_book(self, book_id):
        """
        書籍を開く。

        Parameters
        ----------
        book_id : int
            開く書籍のID

        Returns
        -------
        bool
            開くことができたかどうか
        """
        # 現在の書籍を閉じる
        self.close_current_book()

        # 書籍を取得
        book_data = self.db_manager.get_book(book_id)
        if not book_data:
            return False

        book = Book(book_data, self.db_manager)
        if not book.exists():
            return False

        # PDFドキュメントを開く
        doc = book.open()
        if not doc:
            return False

        self._current_book = book
        self._current_page = book.current_page

        # 現在のページが範囲外なら0に設定
        if self._current_page >= book.total_pages:
            self._current_page = 0

        return True

    def close_current_book(self):
        """現在開いている書籍を閉じる。"""
        if self._current_book:
            self._current_book.close()
            self._current_book = None
            self._current_page = 0

    def go_to_page(self, page_num):
        """
        指定ページに移動する。

        Parameters
        ----------
        page_num : int
            移動先のページ番号（0から始まる）

        Returns
        -------
        bool
            移動が成功したかどうか
        """
        if not self._current_book:
            return False

        # ページ番号の範囲チェック
        if page_num < 0:
            page_num = 0
        elif page_num >= self._current_book.total_pages:
            page_num = self._current_book.total_pages - 1

        # ページを更新
        self._current_page = page_num

        # 読書進捗を更新
        self.update_reading_progress()

        return True

    def go_to_next_page(self):
        """
        次のページに移動する。

        Returns
        -------
        bool
            移動が成功したかどうか
        """
        return self.go_to_page(self._current_page + 1)

    def go_to_previous_page(self):
        """
        前のページに移動する。

        Returns
        -------
        bool
            移動が成功したかどうか
        """
        return self.go_to_page(self._current_page - 1)

    def get_page_pixmap(self, zoom_factor=1.0):
        """
        現在のページのピクセルマップを取得する。

        Parameters
        ----------
        zoom_factor : float, optional
            ズーム係数（1.0 = 100%）

        Returns
        -------
        fitz.Pixmap または None
            ページのピクセルマップ、もしくはエラー時はNone
        """
        if not self._current_book:
            return None

        try:
            doc = self._current_book.open()
            page = doc[self._current_page]
            matrix = fitz.Matrix(zoom_factor, zoom_factor)
            return page.get_pixmap(matrix=matrix)
        except Exception as e:
            print(f"Error rendering page: {e}")
            return None

    def update_reading_progress(self):
        """
        読書進捗を更新する。

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        if not self._current_book:
            return False

        # 状態の自動判定
        status = None
        total_pages = self._current_book.total_pages

        # すでにCompletedに設定されている場合は、どのページにいても維持する
        if self._current_book.status == Book.STATUS_COMPLETED:
            status = Book.STATUS_COMPLETED
        # それ以外の場合は現在のページに基づいて判定
        elif (
            self._current_page == 0
            and self._current_book.status != Book.STATUS_COMPLETED
        ):
            # 最初のページで、かつまだCompletedでない場合のみUnread
            status = Book.STATUS_UNREAD
        elif self._current_page >= total_pages - 1:
            # 最後のページならCompleted
            status = Book.STATUS_COMPLETED
        else:
            # それ以外はReading
            status = Book.STATUS_READING

        # 読書進捗を更新
        success = self.db_manager.update_reading_progress(
            self._current_book.id, current_page=self._current_page, status=status
        )

        # メモリ上の書籍データも更新
        if success:
            self._current_book.data["current_page"] = self._current_page
            self._current_book.data["status"] = status

        return success

    def get_book_progress(self):
        """
        現在の書籍の読書進捗情報を取得する。

        Returns
        -------
        dict または None
            進捗情報の辞書、もしくは書籍が開かれていない場合はNone
        """
        if not self._current_book:
            return None

        total_pages = self._current_book.total_pages
        current_page = self._current_page

        if total_pages <= 0:
            progress_pct = 0
        else:
            progress_pct = (current_page + 1) / total_pages * 100

        return {
            "book_id": self._current_book.id,
            "title": self._current_book.title,
            "current_page": current_page,
            "total_pages": total_pages,
            "progress_percentage": progress_pct,
            "status": self._current_book.status,
        }

    def search_text(self, text, page_range=None, case_sensitive=False):
        """
        PDFドキュメント内でテキストを検索する。

        Parameters
        ----------
        text : str
            検索するテキスト
        page_range : tuple, optional
            検索するページ範囲 (start, end)、Noneの場合は全ページ
        case_sensitive : bool, optional
            大文字小文字を区別するかどうか

        Returns
        -------
        list
            検索結果のリスト（ページ番号、位置情報）
        """
        if not self._current_book or not text:
            return []

        doc = self._current_book.open()
        if not doc:
            return []

        results = []
        start_page = 0
        end_page = doc.page_count - 1

        if page_range:
            start_page = max(0, page_range[0])
            end_page = min(doc.page_count - 1, page_range[1])

        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]
            matches = page.search_for(text, case_sensitive=case_sensitive)

            if matches:
                results.append({"page": page_num, "matches": matches})

        return results
