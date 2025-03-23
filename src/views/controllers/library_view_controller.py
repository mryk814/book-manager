# src/views/controllers/library_view_controller.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LibraryViewController:
    """
    ライブラリビューを管理するコントローラクラス。

    書籍一覧表示、フィルタリング、ソート機能などを提供する。

    Parameters
    ----------
    parent_widget : QWidget
        親ウィジェット
    library_controller : LibraryController
        ライブラリコントローラ
    """

    def __init__(self, parent_widget, library_controller):
        """
        Parameters
        ----------
        parent_widget : QWidget
            親ウィジェット
        library_controller : LibraryController
            ライブラリコントローラ
        """
        self.parent = parent_widget
        self.library_controller = library_controller

        # 現在の表示モード
        self.current_view_mode = "grid"

        # 現在のフィルタ条件
        self.current_category_id = None
        self.current_series_id = None
        self.current_status = None
        self.current_search_query = ""

        # ウィジェットの作成
        self.main_widget = QWidget(parent_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # フィルターバーの作成
        self._create_filter_bar()

        # 書籍表示エリアの作成
        self._create_book_view()

        # 初期データの読み込み
        self.reload_books()

    def _create_filter_bar(self):
        """フィルターバーを作成する"""
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        # カテゴリフィルター
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        categories = self.library_controller.category_controller.get_all_categories()
        for category in categories:
            self.category_combo.addItem(category["name"], category["id"])
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)

        # シリーズフィルター
        self.series_combo = QComboBox()
        self.series_combo.addItem("All Series", None)
        series_list = self.library_controller.series_controller.get_all_series()
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)
        self.series_combo.currentIndexChanged.connect(self._on_series_changed)

        # 検索ボックス
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.textChanged.connect(self._on_search_text_changed)

        # 検索ボタン
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search_clicked)

        # フィルターバーにウィジェットを追加
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_combo)
        filter_layout.addWidget(QLabel("Series:"))
        filter_layout.addWidget(self.series_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(self.search_button)

        self.layout.addWidget(filter_widget)

    def _create_book_view(self):
        """書籍表示エリアを作成する"""
        # 現在の表示モードに基づいてビューを作成
        if self.current_view_mode == "grid":
            from views.components.book_grid_view import BookGridView

            self.book_view = BookGridView(self.main_widget)
        else:
            from views.components.book_list_view import BookListView

            self.book_view = BookListView(self.main_widget)

        # シグナル接続
        self.book_view.book_selected.connect(self._on_book_selected)
        self.book_view.book_double_clicked.connect(self._on_book_double_clicked)

        self.layout.addWidget(self.book_view)

    def reload_books(self):
        """現在のフィルタ条件に基づいて書籍を再読み込みする"""
        # フィルタ条件に基づいて書籍を取得
        if self.current_search_query:
            # 検索条件がある場合
            books = self.library_controller.search_controller.search_books(
                self.current_search_query,
                {
                    "category_id": self.current_category_id,
                    "series_id": self.current_series_id,
                    "status": self.current_status,
                },
            )
        else:
            # 通常のフィルタリング
            books = self.library_controller.book_controller.get_all_books(
                category_id=self.current_category_id,
                series_id=self.current_series_id,
                status=self.current_status,
            )

        # ビューモデルに変換
        from viewmodels.book_viewmodel import BookViewModel

        book_viewmodels = [
            BookViewModel(book, self.library_controller.db_manager) for book in books
        ]

        # 書籍ビューを更新
        self.book_view.set_books(book_viewmodels)

    def set_view_mode(self, mode):
        """
        表示モードを設定する

        Parameters
        ----------
        mode : str
            'grid'または'list'
        """
        if mode == self.current_view_mode:
            return

        # 現在のモードを保存
        self.current_view_mode = mode

        # 古いビューを削除
        if hasattr(self, "book_view"):
            self.book_view.deleteLater()

        # 新しいビューを作成
        self._create_book_view()

        # 書籍を再読み込み
        self.reload_books()

    def set_filter(self, category_id=None, series_id=None, status=None):
        """
        フィルター条件を設定する

        Parameters
        ----------
        category_id : int, optional
            カテゴリID
        series_id : int, optional
            シリーズID
        status : str, optional
            読書状態
        """
        changed = False

        if category_id != self.current_category_id:
            self.current_category_id = category_id
            # カテゴリコンボボックスを更新
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            changed = True

        if series_id != self.current_series_id:
            self.current_series_id = series_id
            # シリーズコンボボックスを更新
            index = self.series_combo.findData(series_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)
            changed = True

        if status != self.current_status:
            self.current_status = status
            changed = True

        if changed:
            self.reload_books()

    def set_search_query(self, query):
        """
        検索クエリを設定する

        Parameters
        ----------
        query : str
            検索クエリ
        """
        if query != self.current_search_query:
            self.current_search_query = query
            self.search_box.setText(query)
            self.reload_books()

    def _on_category_changed(self, index):
        """カテゴリ選択変更時のハンドラ"""
        category_id = self.category_combo.itemData(index)
        self.current_category_id = category_id

        # シリーズコンボボックスを更新
        self.series_combo.clear()
        self.series_combo.addItem("All Series", None)

        if category_id is not None:
            # 選択したカテゴリに属するシリーズのみを表示
            series_list = self.library_controller.series_controller.get_all_series(
                category_id
            )
        else:
            # すべてのシリーズを表示
            series_list = self.library_controller.series_controller.get_all_series()

        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        # 書籍を再読み込み
        self.reload_books()

    def _on_series_changed(self, index):
        """シリーズ選択変更時のハンドラ"""
        self.current_series_id = self.series_combo.itemData(index)
        self.reload_books()

    def _on_search_text_changed(self, text):
        """検索テキスト変更時のハンドラ"""
        # リアルタイム検索は重いため、ボタンクリック時に実行
        pass

    def _on_search_clicked(self):
        """検索ボタンクリック時のハンドラ"""
        self.current_search_query = self.search_box.text()
        self.reload_books()

    def _on_book_selected(self, book_id):
        """書籍選択時のハンドラ"""
        # MainWindowに選択された書籍を通知
        self.parent.on_book_selected(book_id)

    def _on_book_double_clicked(self, book_id):
        """書籍ダブルクリック時のハンドラ"""
        # MainWindowに書籍を開くよう通知
        self.parent.open_book(book_id)
