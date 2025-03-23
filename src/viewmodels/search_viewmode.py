import re

from models.book import Book


class SeriesViewModel:
    """
    シリーズデータの表示に関するロジックを扱うビューモデルクラス。

    モデルとビューの間の中間層として機能し、
    表示に必要なデータの変換や整形を行う。

    Parameters
    ----------
    series : Series
        シリーズオブジェクト
    db_manager : DatabaseManager
        データベースマネージャのインスタンス
    """

    def __init__(self, series, db_manager):
        """
        Parameters
        ----------
        series : Series
            表示対象のシリーズ
        db_manager : DatabaseManager
            データベース管理オブジェクト
        """
        self.series = series
        self.db_manager = db_manager
        self._reading_stats = None

    @property
    def id(self):
        """シリーズID"""
        return self.series.id

    @property
    def name(self):
        """シリーズ名（表示用）"""
        return self.series.name or "Unnamed Series"

    @property
    def description(self):
        """説明（表示用）"""
        return self.series.description or ""

    @property
    def category_id(self):
        """カテゴリID"""
        return self.series.category_id

    @property
    def category_name(self):
        """カテゴリ名（表示用）"""
        return self.series.category_name or "Uncategorized"

    @property
    def book_count(self):
        """書籍数"""
        return len(self.series.books)

    @property
    def book_count_text(self):
        """書籍数テキスト（表示用）"""
        count = self.book_count
        return f"{count} {'book' if count == 1 else 'books'}"

    @property
    def reading_stats(self):
        """読書状態の集計"""
        if self._reading_stats is None:
            self._reading_stats = self.series.get_reading_status()
        return self._reading_stats

    @property
    def completed_count(self):
        """完了した書籍数"""
        return self.reading_stats.get(Book.STATUS_COMPLETED, 0)

    @property
    def reading_count(self):
        """読書中の書籍数"""
        return self.reading_stats.get(Book.STATUS_READING, 0)

    @property
    def unread_count(self):
        """未読の書籍数"""
        return self.reading_stats.get(Book.STATUS_UNREAD, 0)

    @property
    def progress_percentage(self):
        """シリーズ全体の進捗率（パーセント）"""
        total = self.book_count
        if total == 0:
            return 0
        return int(self.completed_count / total * 100)

    @property
    def progress_text(self):
        """進捗テキスト（表示用）"""
        return f"Completed: {self.progress_percentage}%"

    @property
    def status_summary(self):
        """読書状態の要約（表示用）"""
        return (
            f"{self.completed_count} completed, "
            f"{self.reading_count} reading, "
            f"{self.unread_count} unread"
        )

    def get_first_book(self):
        """
        シリーズの最初の書籍を取得する。

        Returns
        -------
        Book または None
            最初の書籍、または書籍がない場合はNone
        """
        books = self.series.books
        if not books:
            return None

        # 自然順でソート
        sorted_books = self.get_sorted_books()
        return sorted_books[0] if sorted_books else None

    def get_sorted_books(self):
        """
        シリーズ内の書籍をソートして取得する。

        Returns
        -------
        list
            ソートされた書籍リスト
        """
        books = self.series.books
        if not books:
            return []

        # 自然順でソート（数値を考慮したソート）
        def natural_sort_key(book):
            """
            series_orderを最優先し、次にタイトルの自然順でソート
            """
            # series_orderがNoneの場合は最大値とする（最後に表示）
            order = book.series_order if book.series_order is not None else float("inf")
            title = book.title if book.title else ""
            # 数値部分を抽出して数値として扱う
            title_key = [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]
            return (order, title_key)

        return sorted(books, key=natural_sort_key)

    def get_cover_image(self, thumbnail_size=None):
        """
        シリーズの表紙画像を取得する。
        シリーズの最初の書籍の表紙を使用する。

        Parameters
        ----------
        thumbnail_size : tuple, optional
            サムネイルサイズ (width, height)

        Returns
        -------
        bytes または None
            表紙画像のバイナリデータ
        """
        first_book = self.get_first_book()
        if first_book:
            return first_book.get_cover_image(thumbnail_size=thumbnail_size)
        return None

    def truncate_text(self, text, max_length):
        """
        テキストを指定した長さに切り詰める。

        Parameters
        ----------
        text : str
            元のテキスト
        max_length : int
            最大長

        Returns
        -------
        str
            切り詰められたテキスト
        """
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text
