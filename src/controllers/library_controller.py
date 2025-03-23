from controllers.book_controller import BookController
from controllers.category_controller import CategoryController
from controllers.import_controller import ImportController
from controllers.reader_controller import ReaderController
from controllers.search_controller import SearchController
from controllers.series_controller import SeriesController


class LibraryController:
    """
    ライブラリのビジネスロジックを管理するコントローラクラス。

    各専門コントローラのファサードとして機能し、
    アプリケーションの他の部分からのアクセスを単純化する。

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

        # 各専門コントローラを初期化
        self.book_controller = BookController(db_manager)
        self.series_controller = SeriesController(db_manager)
        self.category_controller = CategoryController(db_manager)
        self.import_controller = ImportController(db_manager)
        self.reader_controller = ReaderController(db_manager)
        self.search_controller = SearchController(db_manager)

    # BookControllerへの委譲 --------------------
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
        return self.book_controller.get_all_books(category_id, series_id, status)

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
        return self.search_controller.search_books(query)

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
        return self.book_controller.get_book(book_id)

    def get_current_book(self):
        """
        現在アクティブな書籍を取得する。

        Returns
        -------
        Book または None
            現在の書籍、もしくは設定されていない場合はNone
        """
        return self.reader_controller.get_current_book()

    def set_current_book(self, book):
        """
        現在アクティブな書籍を設定する。

        Parameters
        ----------
        book : Book
            アクティブにする書籍
        """
        self.reader_controller.close_current_book()
        self.book_controller.set_current_book(book)

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
        return self.book_controller.update_book_progress(book_id, current_page, status)

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
        return self.book_controller.update_book_metadata(book_id, **metadata)

    def batch_update_metadata(self, book_ids, metadata):
        """
        複数書籍のメタデータを一括更新する。

        Parameters
        ----------
        book_ids : list
            更新する書籍IDのリスト
        metadata : dict
            更新するメタデータのキーと値

        Returns
        -------
        int
            更新された書籍の数
        """
        return self.book_controller.batch_update_metadata(book_ids, metadata)

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
        return self.book_controller.remove_book(book_id, delete_file)

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
        return self.book_controller.batch_remove_books(book_ids, delete_files)

    # SeriesControllerへの委譲 --------------------
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
        return self.series_controller.get_all_series(category_id)

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
        return self.series_controller.get_series(series_id)

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
        return self.series_controller.create_series(name, description, category_id)

    # CategoryControllerへの委譲 --------------------
    def get_all_categories(self):
        """
        すべてのカテゴリを取得する。

        Returns
        -------
        list
            カテゴリ情報の辞書のリスト
        """
        return self.category_controller.get_all_categories()

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
        return self.category_controller.create_category(name, description)

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
        return self.category_controller.get_category(category_id)

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
        return self.category_controller.update_category(category_id, name, description)

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
        return self.category_controller.delete_category(category_id)

    # ImportControllerへの委譲 --------------------
    def import_pdf(
        self,
        file_path,
        title=None,
        author=None,
        publisher=None,
        series_id=None,
        series_order=None,
        category_id=None,
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
        category_id : int, optional
            書籍のカテゴリID

        Returns
        -------
        int または None
            追加された書籍のID、もしくは失敗した場合はNone
        """
        return self.import_controller.import_pdf(
            file_path, title, author, publisher, series_id, series_order, category_id
        )

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
        return self.import_controller.batch_import_pdfs(file_paths, common_metadata)

    # ReaderControllerへの委譲 --------------------
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
        return self.reader_controller.open_book(book_id)

    def close_current_book(self):
        """現在開いている書籍を閉じる。"""
        self.reader_controller.close_current_book()

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
        return self.reader_controller.go_to_page(page_num)

    def go_to_next_page(self):
        """
        次のページに移動する。

        Returns
        -------
        bool
            移動が成功したかどうか
        """
        return self.reader_controller.go_to_next_page()

    def go_to_previous_page(self):
        """
        前のページに移動する。

        Returns
        -------
        bool
            移動が成功したかどうか
        """
        return self.reader_controller.go_to_previous_page()

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
        return self.reader_controller.get_page_pixmap(zoom_factor)

    def get_book_progress(self):
        """
        現在の書籍の読書進捗情報を取得する。

        Returns
        -------
        dict または None
            進捗情報の辞書、もしくは書籍が開かれていない場合はNone
        """
        return self.reader_controller.get_book_progress()

    # SearchControllerへの委譲 --------------------
    def advanced_search(self, criteria):
        """
        複雑な条件による高度な検索を行う。

        Parameters
        ----------
        criteria : dict
            検索条件の辞書

        Returns
        -------
        list
            検索結果の書籍リスト
        """
        return self.search_controller.advanced_search(criteria)

    def search_in_content(self, query, book_ids=None):
        """
        書籍の内容を検索する（フルテキスト検索）。
        注意: 実装されているPDFの場合のみ可能。

        Parameters
        ----------
        query : str
            検索クエリ
        book_ids : list, optional
            検索対象の書籍IDリスト（指定しない場合はすべての書籍）

        Returns
        -------
        dict
            書籍IDをキー、検索結果リストを値とする辞書
        """
        return self.search_controller.search_in_content(query, book_ids)

    def get_books_by_category(self, category_id, **kwargs):
        """
        特定のカテゴリに関連する書籍を取得する。

        Parameters
        ----------
        category_id : int
            カテゴリID
        **kwargs
            その他の検索条件

        Returns
        -------
        list
            書籍オブジェクトのリスト
        """
        return self.get_all_books(category_id=category_id, **kwargs)
