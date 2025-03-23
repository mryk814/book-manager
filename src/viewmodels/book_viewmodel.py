class BookViewModel:
    """
    書籍データの表示に関するロジックを扱うビューモデルクラス。

    モデルとビューの間の中間層として機能し、
    表示に必要なデータの変換や整形を行う。

    Parameters
    ----------
    book : Book
        書籍オブジェクト
    db_manager : DatabaseManager
        データベースマネージャのインスタンス
    """

    def __init__(self, book, db_manager):
        """
        Parameters
        ----------
        book : Book
            表示対象の書籍
        db_manager : DatabaseManager
            データベース管理オブジェクト
        """
        self.book = book
        self.db_manager = db_manager
        self._series_name = None
        self._category_name = None

    @property
    def id(self):
        """書籍ID"""
        return self.book.id

    @property
    def title(self):
        """タイトル（表示用）"""
        return self.book.title or "No Title"

    @property
    def author(self):
        """著者名（表示用）"""
        return self.book.author or "Unknown Author"

    @property
    def publisher(self):
        """出版社名（表示用）"""
        return self.book.publisher or "Unknown Publisher"

    @property
    def file_path(self):
        """ファイルパス"""
        return self.book.file_path

    @property
    def series_id(self):
        """シリーズID"""
        return self.book.series_id

    @property
    def series_name(self):
        """シリーズ名（表示用）"""
        if self._series_name is None and self.book.series_id:
            series = self.db_manager.get_series(self.book.series_id)
            self._series_name = series.get("name") if series else None
        return self._series_name or "Not in Series"

    @property
    def series_info(self):
        """シリーズ情報（表示用、順番付き）"""
        if not self.book.series_id:
            return ""

        order_text = f" #{self.book.series_order}" if self.book.series_order else ""
        return f"{self.series_name}{order_text}"

    @property
    def category_id(self):
        """カテゴリID"""
        return self.book.category_id

    @property
    def category_name(self):
        """カテゴリ名（表示用）"""
        if self._category_name is None:
            if self.book.category_id:
                # 書籍に直接カテゴリが設定されている場合
                category = self.db_manager.get_category(self.book.category_id)
                self._category_name = category.get("name") if category else None
            elif self.book.series_id:
                # シリーズからカテゴリを取得
                series = self.db_manager.get_series(self.book.series_id)
                if series and series.get("category_id"):
                    category = self.db_manager.get_category(series.get("category_id"))
                    self._category_name = category.get("name") if category else None

        return self._category_name or "Uncategorized"

    @property
    def category_source(self):
        """カテゴリのソース（直接/シリーズ経由）"""
        if self.book.category_id:
            return "direct"
        elif self.book.series_id:
            series = self.db_manager.get_series(self.book.series_id)
            if series and series.get("category_id"):
                return "from_series"
        return None

    @property
    def reading_status(self):
        """読書状態（表示用）"""
        if self.book.status == self.book.STATUS_READING:
            return "Reading"
        elif self.book.status == self.book.STATUS_COMPLETED:
            return "Completed"
        else:
            return "Unread"

    @property
    def reading_progress(self):
        """読書進捗（パーセント）"""
        if self.book.total_pages <= 0:
            return 0
        return (self.book.current_page + 1) / self.book.total_pages * 100

    @property
    def progress_text(self):
        """進捗テキスト（表示用）"""
        if self.book.total_pages <= 0:
            return "No pages"
        return f"{self.book.current_page + 1} / {self.book.total_pages} ({int(self.reading_progress)}%)"

    @property
    def status_color(self):
        """状態に応じた色コード"""
        if self.book.status == self.book.STATUS_UNREAD:
            return "#9e9e9e"  # グレー
        elif self.book.status == self.book.STATUS_READING:
            return "#1976d2"  # 青
        elif self.book.status == self.book.STATUS_COMPLETED:
            return "#43a047"  # 緑
        return "#212121"  # デフォルト（黒）

    def get_cover_image(self, thumbnail_size=None, force_reload=False):
        """
        表紙画像を取得する。

        Parameters
        ----------
        thumbnail_size : tuple, optional
            サムネイルサイズ (width, height)
        force_reload : bool, optional
            強制的に再読み込みするかどうか

        Returns
        -------
        bytes または None
            表紙画像のバイナリデータ
        """
        return self.book.get_cover_image(
            thumbnail_size=thumbnail_size, force_reload=force_reload
        )

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
