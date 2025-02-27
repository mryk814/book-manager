import os
import sys

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from controllers.library_controller import LibraryController
from models.book import Book
from models.database import DatabaseManager
from views.batch_metadata_editor import BatchMetadataEditor
from views.dialogs.import_dialog import ImportDialog
from views.dialogs.settings_dialog import SettingsDialog
from views.library_view import LibraryGridView, LibraryListView
from views.metadata_editor import MetadataEditor
from views.reader_view import PDFReaderView
from views.series_editor import SeriesEditor
from views.series_view import SeriesGridView, SeriesListView


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。

    ライブラリビューとPDFリーダービューを含み、
    メニュー、ツールバー、ステータスバーを提供する。
    """

    # カスタムシグナル
    book_opened = pyqtSignal(int)  # book_id

    def __init__(self, db_path="library.db"):
        """
        Parameters
        ----------
        db_path : str, optional
            データベースファイルのパス。デフォルトは'library.db'。
        """
        super().__init__()

        # モデルとコントローラの初期化
        self.db_manager = DatabaseManager(db_path)
        self.library_controller = LibraryController(self.db_manager)

        # ウィンドウの基本設定
        self.setWindowTitle("PDF Library Manager")
        self.setMinimumSize(1024, 768)

        # メインウィジェットとレイアウトの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # ツールバーの設定
        self.setup_toolbar()

        # メニューバーの設定
        self.setup_menubar()

        # メインのスプリッターを作成
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)

        # 左側のライブラリパネルを作成
        self.library_panel = QWidget()
        self.library_layout = QVBoxLayout(self.library_panel)
        self.setup_library_panel()
        self.main_splitter.addWidget(self.library_panel)

        # 右側のリーダーパネルを作成
        self.reader_panel = QWidget()
        self.reader_layout = QVBoxLayout(self.reader_panel)
        self.setup_reader_panel()
        self.main_splitter.addWidget(self.reader_panel)

        # スプリッターの初期サイズを設定
        self.main_splitter.setSizes([300, 700])

        # ステータスバーの設定
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # シグナルとスロットの接続
        self.setup_connections()

        # コンテキストメニュー機能の設定
        self.setup_context_menu_handlers()

    def setup_toolbar(self):
        """ツールバーを設定する。"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)

        # インポートアクション
        self.import_action = QAction("Import", self)
        self.import_action.setStatusTip("Import PDFs to library")
        self.import_action.triggered.connect(self.show_import_dialog)
        self.toolbar.addAction(self.import_action)

        self.toolbar.addSeparator()

        # 複数選択モードの切り替え
        self.multi_select_action = QAction("Multi-Select", self)
        self.multi_select_action.setCheckable(True)
        self.multi_select_action.setStatusTip("Enable multiple selection")
        self.multi_select_action.triggered.connect(self.toggle_multi_select_mode)
        self.toolbar.addAction(self.multi_select_action)

        # 全選択ボタン
        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setStatusTip("Select all visible books")
        self.select_all_action.triggered.connect(self.select_all_books)
        self.select_all_action.setEnabled(False)  # 初期状態では無効
        self.toolbar.addAction(self.select_all_action)

        # 一括操作のドロップダウンボタン
        self.batch_actions_button = QPushButton("Batch Actions")
        self.batch_actions_button.setEnabled(False)  # 初期状態では無効

        # 一括操作メニューの作成
        self.batch_actions_menu = QMenu(self)

        self.batch_edit_action = QAction("Edit Selected Books", self)
        self.batch_edit_action.triggered.connect(self.show_batch_metadata_editor)
        self.batch_actions_menu.addAction(self.batch_edit_action)

        self.batch_add_to_series_action = QAction("Add to Series", self)
        self.batch_add_to_series_action.triggered.connect(
            self.show_batch_add_to_series_dialog
        )
        self.batch_actions_menu.addAction(self.batch_add_to_series_action)

        self.batch_remove_from_series_action = QAction("Remove from Series", self)
        self.batch_remove_from_series_action.triggered.connect(
            self.batch_remove_from_series
        )
        self.batch_actions_menu.addAction(self.batch_remove_from_series_action)

        self.batch_actions_menu.addSeparator()

        # 一括ステータス変更サブメニュー
        self.batch_status_menu = QMenu("Mark as", self)

        self.batch_mark_unread_action = QAction("Unread", self)
        self.batch_mark_unread_action.triggered.connect(
            lambda: self.batch_mark_as_status(Book.STATUS_UNREAD)
        )
        self.batch_status_menu.addAction(self.batch_mark_unread_action)

        self.batch_mark_reading_action = QAction("Reading", self)
        self.batch_mark_reading_action.triggered.connect(
            lambda: self.batch_mark_as_status(Book.STATUS_READING)
        )
        self.batch_status_menu.addAction(self.batch_mark_reading_action)

        self.batch_mark_completed_action = QAction("Completed", self)
        self.batch_mark_completed_action.triggered.connect(
            lambda: self.batch_mark_as_status(Book.STATUS_COMPLETED)
        )
        self.batch_status_menu.addAction(self.batch_mark_completed_action)

        self.batch_actions_menu.addMenu(self.batch_status_menu)

        self.batch_actions_menu.addSeparator()

        self.batch_remove_action = QAction("Remove Selected Books", self)
        self.batch_remove_action.triggered.connect(self.batch_remove_books)
        self.batch_actions_menu.addAction(self.batch_remove_action)

        self.batch_actions_button.setMenu(self.batch_actions_menu)
        self.toolbar.addWidget(self.batch_actions_button)

        self.toolbar.addSeparator()

        # ビュータイプの切り替え
        self.view_label = QLabel("View:")
        self.toolbar.addWidget(self.view_label)

        self.view_type_combo = QComboBox()
        self.view_type_combo.addItems(["Grid View", "List View"])
        self.view_type_combo.currentIndexChanged.connect(self.change_view_type)
        self.toolbar.addWidget(self.view_type_combo)

        self.toolbar.addSeparator()

        # カテゴリフィルタ
        self.category_label = QLabel("Category:")
        self.toolbar.addWidget(self.category_label)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.populate_category_combo()
        self.category_combo.currentIndexChanged.connect(self.filter_by_category)
        self.toolbar.addWidget(self.category_combo)

        self.toolbar.addSeparator()

        # 検索ボックス
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search books...")
        self.search_box.setMinimumWidth(200)
        self.search_box.returnPressed.connect(self.search_books)
        self.toolbar.addWidget(self.search_box)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_books)
        self.toolbar.addWidget(self.search_button)

        # 検索クリアボタン
        self.clear_search_button = QPushButton("Clear")
        self.clear_search_button.clicked.connect(self.clear_search)
        self.toolbar.addWidget(self.clear_search_button)

    def setup_menubar(self):
        """メニューバーを設定する。"""
        # ファイルメニュー
        file_menu = self.menuBar().addMenu("&File")

        import_action = QAction("&Import PDFs...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 編集メニュー
        edit_menu = self.menuBar().addMenu("&Edit")

        edit_metadata_action = QAction("Edit &Metadata...", self)
        edit_metadata_action.setEnabled(False)  # 書籍選択時に有効化
        edit_metadata_action.triggered.connect(self.show_metadata_editor)
        edit_menu.addAction(edit_metadata_action)
        self.edit_metadata_action = edit_metadata_action

        # 複数選択モード切り替え
        multi_select_menu_action = QAction("&Multi-Select Mode", self)
        multi_select_menu_action.setCheckable(True)
        multi_select_menu_action.triggered.connect(self.toggle_multi_select_mode)
        edit_menu.addAction(multi_select_menu_action)
        self.multi_select_menu_action = multi_select_menu_action

        # 選択全選択
        select_all_menu_action = QAction("Select &All", self)
        select_all_menu_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_menu_action.triggered.connect(self.select_all_books)
        select_all_menu_action.setEnabled(False)  # 初期状態では無効
        edit_menu.addAction(select_all_menu_action)
        self.select_all_menu_action = select_all_menu_action

        edit_menu.addSeparator()

        # 一括編集サブメニュー
        batch_menu = QMenu("&Batch Operations", self)

        batch_edit_menu_action = QAction("&Edit Selected Books...", self)
        batch_edit_menu_action.triggered.connect(self.show_batch_metadata_editor)
        batch_edit_menu_action.setEnabled(False)
        batch_menu.addAction(batch_edit_menu_action)
        self.batch_edit_menu_action = batch_edit_menu_action

        batch_add_to_series_menu_action = QAction("&Add to Series...", self)
        batch_add_to_series_menu_action.triggered.connect(
            self.show_batch_add_to_series_dialog
        )
        batch_add_to_series_menu_action.setEnabled(False)
        batch_menu.addAction(batch_add_to_series_menu_action)
        self.batch_add_to_series_menu_action = batch_add_to_series_menu_action

        batch_remove_from_series_menu_action = QAction("&Remove from Series", self)
        batch_remove_from_series_menu_action.triggered.connect(
            self.batch_remove_from_series
        )
        batch_remove_from_series_menu_action.setEnabled(False)
        batch_menu.addAction(batch_remove_from_series_menu_action)
        self.batch_remove_from_series_menu_action = batch_remove_from_series_menu_action

        batch_menu.addSeparator()

        # 一括ステータス変更サブメニュー
        batch_status_menu = QMenu("Mark as", self)

        batch_mark_unread_menu_action = QAction("&Unread", self)
        batch_mark_unread_menu_action.triggered.connect(
            lambda: self.batch_mark_as_status(Book.STATUS_UNREAD)
        )
        batch_mark_unread_menu_action.setEnabled(False)
        batch_status_menu.addAction(batch_mark_unread_menu_action)
        self.batch_mark_unread_menu_action = batch_mark_unread_menu_action

        batch_mark_reading_menu_action = QAction("&Reading", self)
        batch_mark_reading_menu_action.triggered.connect(
            lambda: self.batch_mark_as_status(Book.STATUS_READING)
        )
        batch_mark_reading_menu_action.setEnabled(False)
        batch_status_menu.addAction(batch_mark_reading_menu_action)
        self.batch_mark_reading_menu_action = batch_mark_reading_menu_action

        batch_mark_completed_menu_action = QAction("&Completed", self)
        batch_mark_completed_menu_action.triggered.connect(
            lambda: self.batch_mark_as_status(Book.STATUS_COMPLETED)
        )
        batch_mark_completed_menu_action.setEnabled(False)
        batch_status_menu.addAction(batch_mark_completed_menu_action)
        self.batch_mark_completed_menu_action = batch_mark_completed_menu_action

        batch_menu.addMenu(batch_status_menu)

        batch_menu.addSeparator()

        batch_remove_menu_action = QAction("&Remove Selected Books", self)
        batch_remove_menu_action.triggered.connect(self.batch_remove_books)
        batch_remove_menu_action.setEnabled(False)
        batch_menu.addAction(batch_remove_menu_action)
        self.batch_remove_menu_action = batch_remove_menu_action

        edit_menu.addMenu(batch_menu)

        # 表示メニュー
        view_menu = self.menuBar().addMenu("&View")

        grid_view_action = QAction("&Grid View", self)
        grid_view_action.setCheckable(True)
        grid_view_action.setChecked(True)
        grid_view_action.triggered.connect(
            lambda: self.view_type_combo.setCurrentIndex(0)
        )
        view_menu.addAction(grid_view_action)
        self.grid_view_action = grid_view_action

        list_view_action = QAction("&List View", self)
        list_view_action.setCheckable(True)
        list_view_action.triggered.connect(
            lambda: self.view_type_combo.setCurrentIndex(1)
        )
        view_menu.addAction(list_view_action)
        self.list_view_action = list_view_action

        view_menu.addSeparator()

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh_library)
        view_menu.addAction(refresh_action)

        # ヘルプメニュー
        help_menu = self.menuBar().addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def setup_library_panel(self):
        """ライブラリパネルを設定する。"""
        # メインタブウィジェット（書籍とシリーズ）
        self.main_tabs = QTabWidget()
        self.library_layout.addWidget(self.main_tabs)

        # 書籍タブ
        self.books_tab = QWidget()
        books_layout = QVBoxLayout(self.books_tab)
        books_layout.setContentsMargins(0, 0, 0, 0)
        self.main_tabs.addTab(self.books_tab, "Books")

        # シリーズナビゲーションバー（書籍タブの上部に配置）
        self.series_navigation = QWidget()
        series_navigation_layout = QHBoxLayout(self.series_navigation)
        series_navigation_layout.setContentsMargins(5, 5, 5, 5)

        self.back_to_series_button = QPushButton("← Back to Series")
        self.back_to_series_button.clicked.connect(self.show_series_view)
        self.back_to_series_button.setVisible(False)  # 初期状態では非表示
        series_navigation_layout.addWidget(self.back_to_series_button)

        self.current_series_label = QLabel("")
        self.current_series_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        series_navigation_layout.addWidget(self.current_series_label)

        series_navigation_layout.addStretch(1)

        books_layout.addWidget(self.series_navigation)

        # 書籍ビュータイプのタブウィジェット
        self.library_tabs = QTabWidget()
        books_layout.addWidget(self.library_tabs)

        # グリッドビュータブ
        self.grid_view = LibraryGridView(self.library_controller)
        self.library_tabs.addTab(self.grid_view, "Grid View")

        # リストビュータブ
        self.list_view = LibraryListView(self.library_controller)
        self.library_tabs.addTab(self.list_view, "List View")

        # シリーズタブ
        self.series_tab = QWidget()
        series_layout = QVBoxLayout(self.series_tab)
        series_layout.setContentsMargins(0, 0, 0, 0)
        self.main_tabs.addTab(self.series_tab, "Series")

        # シリーズビュータイプのタブウィジェット
        self.series_tabs = QTabWidget()
        series_layout.addWidget(self.series_tabs)

        # シリーズグリッドビュー
        self.series_grid_view = SeriesGridView(self.library_controller)
        self.series_tabs.addTab(self.series_grid_view, "Grid View")

        # シリーズリストビュー
        self.series_list_view = SeriesListView(self.library_controller)
        self.series_tabs.addTab(self.series_list_view, "List View")

        # タブの変更をツールバーコンボボックスと同期
        self.library_tabs.currentChanged.connect(
            lambda idx: self.view_type_combo.setCurrentIndex(idx)
        )

        # シリーズタブの変更を処理
        self.series_tabs.currentChanged.connect(
            lambda idx: self.update_series_view_state()
        )

        # シリーズ選択シグナルを接続
        self.series_grid_view.series_selected.connect(self.on_series_selected)
        self.series_list_view.series_selected.connect(self.on_series_selected)

        # 現在表示中のシリーズID
        self.current_series_id = None

        # データキャッシュ（パフォーマンス向上用）
        self.series_books_cache = {}

    def setup_reader_panel(self):
        """リーダーパネルを設定する。"""
        # PDF表示用ウィジェット
        self.reader_view = PDFReaderView(self.library_controller)
        self.reader_layout.addWidget(self.reader_view)

    def setup_context_menu_handlers(self):
        """コンテキストメニュー機能のハンドラを設定する。"""
        # グリッドビューのコンテキストメニューハンドラ
        self.grid_view._edit_metadata = self.show_metadata_editor
        self.grid_view._batch_edit_metadata = self.show_batch_metadata_editor
        self.grid_view._add_to_series = self.show_add_to_series_dialog
        self.grid_view._batch_add_to_series = self.show_batch_add_to_series_dialog
        self.grid_view._batch_remove_from_series = self.batch_remove_from_series
        self.grid_view._remove_book = self.remove_book
        self.grid_view._batch_remove_books = self.batch_remove_books

        # リストビューのコンテキストメニューハンドラ
        self.list_view._edit_metadata = self.show_metadata_editor
        self.list_view._batch_edit_metadata = self.show_batch_metadata_editor
        self.list_view._add_to_series = self.show_add_to_series_dialog
        self.list_view._batch_add_to_series = self.show_batch_add_to_series_dialog
        self.list_view._batch_remove_from_series = self.batch_remove_from_series
        self.list_view._remove_book = self.remove_book
        self.list_view._batch_remove_books = self.batch_remove_books

        # シリーズビューのコンテキストメニューハンドラ
        self.series_grid_view._edit_series = self.show_series_editor
        self.series_grid_view._remove_series = self.remove_series

        self.series_list_view._edit_series = self.show_series_editor
        self.series_list_view._remove_series = self.remove_series

    def setup_connections(self):
        """シグナルとスロットを接続する。"""
        # グリッドビューからの選択シグナル
        self.grid_view.book_selected.connect(self.on_book_selected)
        self.grid_view.books_selected.connect(self.on_books_selected)

        # リストビューからの選択シグナル
        self.list_view.book_selected.connect(self.on_book_selected)
        self.list_view.books_selected.connect(self.on_books_selected)

        # リーダービューからの進捗更新シグナル
        self.reader_view.progress_updated.connect(self.on_progress_updated)

    def populate_category_combo(self):
        """カテゴリコンボボックスにデータを設定する。"""
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)

        categories = self.db_manager.get_all_categories()
        for category in categories:
            self.category_combo.addItem(category["name"], category["id"])

    def change_view_type(self, index):
        """
        表示タイプを変更する。

        Parameters
        ----------
        index : int
            コンボボックスのインデックス（0=グリッド, 1=リスト）
        """
        # 現在アクティブなメインタブを取得
        current_main_tab = self.main_tabs.currentWidget()

        if current_main_tab == self.books_tab:
            self.library_tabs.setCurrentIndex(index)

            # メニューの選択状態も更新
            self.grid_view_action.setChecked(index == 0)
            self.list_view_action.setChecked(index == 1)

            # シリーズを表示中なら、ビュー切替時にシリーズフィルタを再適用
            if self.current_series_id and self.back_to_series_button.isVisible():
                self.filter_by_series(self.current_series_id)

        elif current_main_tab == self.series_tab:
            self.series_tabs.setCurrentIndex(index)

    def filter_by_category(self, index):
        """
        カテゴリでフィルタリングする。

        Parameters
        ----------
        index : int
            コンボボックスのインデックス
        """
        category_id = self.category_combo.itemData(index)
        self.grid_view.set_category_filter(category_id)
        self.list_view.set_category_filter(category_id)

    def search_books(self):
        """検索ボックスの内容で書籍を検索する。"""
        query = self.search_box.text().strip()
        if query:
            self.grid_view.search(query)
            self.list_view.search(query)
            self.statusBar.showMessage(f"Search results for: {query}")

    def clear_search(self):
        """検索をクリアし、すべての書籍を表示する。"""
        self.search_box.clear()
        self.grid_view.clear_search()
        self.list_view.clear_search()
        self.statusBar.showMessage("Search cleared")

    def on_book_selected(self, book_id):
        """
        書籍が選択されたときの処理。

        Parameters
        ----------
        book_id : int
            選択された書籍のID
        """
        # メタデータ編集アクションを有効化
        self.edit_metadata_action.setEnabled(True)

        # リーダービューに書籍を読み込む
        success = self.reader_view.load_book(book_id)

        if success:
            # 選択状態をビュー間で同期
            if self.sender() == self.grid_view:
                self.list_view.select_book(book_id, emit_signal=False)
            elif self.sender() == self.list_view:
                self.grid_view.select_book(book_id, emit_signal=False)

            # book_openedシグナルを発火
            self.book_opened.emit(book_id)

            # 書籍の情報をステータスバーに表示
            book = self.library_controller.get_book(book_id)
            if book:
                self.statusBar.showMessage(
                    f"Opened: {book.title} by {book.author or 'Unknown'}"
                )
        else:
            self.statusBar.showMessage("Failed to open book")

    def on_progress_updated(self, book_id, current_page, status):
        """
        読書進捗が更新されたときの処理。

        Parameters
        ----------
        book_id : int
            更新された書籍のID
        current_page : int
            現在のページ番号
        status : str
            読書状態
        """
        # 必要に応じてビューを更新
        self.grid_view.update_book_item(book_id)
        self.list_view.update_book_item(book_id)

        # ステータスバーに進捗を表示
        book = self.library_controller.get_book(book_id)
        if book:
            progress_pct = (
                (current_page + 1) / book.total_pages * 100
                if book.total_pages > 0
                else 0
            )
            self.statusBar.showMessage(
                f"Reading progress: {progress_pct:.1f}% ({current_page + 1}/{book.total_pages})"
            )

    def show_import_dialog(self):
        """PDFインポートダイアログを表示する。"""
        dialog = ImportDialog(self.library_controller, self)
        if dialog.exec():
            self.refresh_library()
            self.statusBar.showMessage("Books imported successfully")

    def show_metadata_editor(self, book_id=None):
        """
        メタデータ編集ダイアログを表示する。

        Parameters
        ----------
        book_id : int, optional
            編集する書籍のID。指定されない場合は現在選択されている書籍を使用。
        """
        # 書籍IDが指定されていない場合は現在選択されている書籍を使用
        if book_id is None:
            book_id = (
                self.grid_view.get_selected_book_id()
                or self.list_view.get_selected_book_id()
            )

        if book_id:
            dialog = MetadataEditor(self.library_controller, book_id, self)
            if dialog.exec():
                # ビューを更新
                self.grid_view.update_book_item(book_id)
                self.list_view.update_book_item(book_id)

                # シリーズビューも更新
                book = self.library_controller.get_book(book_id)
                if book and book.series_id:
                    self.series_grid_view.update_series_item(book.series_id)
                    self.series_list_view.update_series_item(book.series_id)

                self.statusBar.showMessage("Metadata updated successfully")

    def show_add_to_series_dialog(self, book_id):
        """
        シリーズ追加ダイアログを表示する。

        Parameters
        ----------
        book_id : int
            追加する書籍のID
        """
        from PyQt6.QtWidgets import (
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLineEdit,
            QPushButton,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Add to Series")

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        # シリーズ選択
        series_combo = QComboBox()
        series_combo.addItem("-- Select Series --", None)

        # シリーズの一覧を取得
        series_list = self.library_controller.get_all_series()
        for series in series_list:
            series_combo.addItem(series.name, series.id)

        form_layout.addRow("Series:", series_combo)

        # 新しいシリーズの作成
        new_series_layout = QHBoxLayout()
        new_series_edit = QLineEdit()
        new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(new_series_edit)

        create_button = QPushButton("Create")
        new_series_layout.addWidget(create_button)

        form_layout.addRow("New Series:", new_series_layout)

        layout.addLayout(form_layout)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # 「新しいシリーズ作成」ボタンが押されたときの処理
        def create_new_series():
            name = new_series_edit.text().strip()
            if name:
                series_id = self.library_controller.create_series(name=name)
                if series_id:
                    series_combo.addItem(name, series_id)
                    index = series_combo.findData(series_id)
                    if index >= 0:
                        series_combo.setCurrentIndex(index)
                    new_series_edit.clear()

        create_button.clicked.connect(create_new_series)

        # ダイアログを表示
        if dialog.exec():
            series_id = series_combo.currentData()
            if series_id:
                # 書籍をシリーズに追加
                self.library_controller.update_book_metadata(
                    book_id, series_id=series_id
                )

                # ビューを更新
                self.grid_view.update_book_item(book_id)
                self.list_view.update_book_item(book_id)
                self.statusBar.showMessage("Book added to series")

    def remove_book(self, book_id):
        """
        書籍を削除する。

        Parameters
        ----------
        book_id : int
            削除する書籍のID
        """
        from PyQt6.QtWidgets import QMessageBox

        # 書籍情報を取得
        book = self.library_controller.get_book(book_id)
        if not book:
            return

        # 確認ダイアログを表示
        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to remove '{book.title}' from the library?\n\n"
            "This will only remove the book from the library, not delete the file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            # 現在開いている書籍がこれなら閉じる
            if self.reader_view.current_book_id == book_id:
                self.reader_view.close_current_book()

            # 書籍を削除
            success = self.library_controller.remove_book(book_id, delete_file=False)

            if success:
                # 個別にリストから削除（全更新を避けてパフォーマンス向上）
                if book_id in self.grid_view.book_widgets:
                    widget = self.grid_view.book_widgets[book_id]
                    widget.setParent(None)
                    widget.deleteLater()
                    del self.grid_view.book_widgets[book_id]

                # リストビューからも削除
                for i in range(self.list_view.list_widget.count()):
                    item = self.list_view.list_widget.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                        self.list_view.list_widget.takeItem(i)
                        break

                # 選択状態をクリア
                if self.grid_view.selected_book_id == book_id:
                    self.grid_view.selected_book_id = None
                if self.list_view.get_selected_book_id() == book_id:
                    self.list_view.list_widget.clearSelection()

                self.statusBar.showMessage(f"Book '{book.title}' removed from library")

    def show_settings_dialog(self):
        """設定ダイアログを表示する。"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_about_dialog(self):
        """アバウトダイアログを表示する。"""
        QMessageBox.about(
            self,
            "About PDF Library Manager",
            "PDF Library Manager\n\n"
            "A desktop application for managing your PDF book collection.\n"
            "Version 1.0.0",
        )

    def refresh_library(self):
        """ライブラリビューをリフレッシュする。"""
        # キャッシュをクリア
        self.series_books_cache = {}

        # 現在表示中のシリーズがある場合は、そのシリーズの書籍のみをリフレッシュ
        if self.current_series_id and self.back_to_series_button.isVisible():
            self.filter_by_series(self.current_series_id)
        else:
            # 通常のリフレッシュ
            self.grid_view.refresh()
            self.list_view.refresh()

        # シリーズビューもリフレッシュ
        self.series_grid_view.refresh()
        self.series_list_view.refresh()

        # カテゴリコンボボックスを更新
        self.populate_category_combo()

        self.statusBar.showMessage("Library refreshed")

    def closeEvent(self, event):
        """
        ウィンドウが閉じられるときの処理。

        Parameters
        ----------
        event : QCloseEvent
            クローズイベント
        """
        # リソースのクリーンアップ
        self.reader_view.close_current_book()
        self.db_manager.close()
        event.accept()

    def toggle_multi_select_mode(self, enabled):
        """
        複数選択モードを切り替える。

        Parameters
        ----------
        enabled : bool
            複数選択モードを有効にするかどうか
        """
        # ツールバーとメニューの状態を同期
        self.multi_select_action.setChecked(enabled)
        self.multi_select_menu_action.setChecked(enabled)

        # ビューの複数選択モードを切り替え
        self.grid_view.toggle_multi_select_mode(enabled)
        self.list_view.toggle_multi_select_mode(enabled)

        # 全選択アクションの有効/無効を切り替え
        self.select_all_action.setEnabled(enabled)
        self.select_all_menu_action.setEnabled(enabled)

        # 単一選択時のアクションの有効/無効を切り替え
        self.edit_metadata_action.setEnabled(not enabled and self._has_selected_book())

        # 複数選択関連のUIの有効/無効を切り替え
        self.update_batch_actions_state()

        # ステータスバーに表示
        if enabled:
            self.statusBar.showMessage("Multiple selection mode enabled")
        else:
            self.statusBar.showMessage("Multiple selection mode disabled")

    def select_all_books(self):
        """表示されているすべての書籍を選択する。"""
        current_view = self.library_tabs.currentWidget()
        if current_view:
            current_view.select_all()

    def on_book_selected(self, book_id):
        """
        書籍が選択されたときの処理（単一選択）。

        Parameters
        ----------
        book_id : int
            選択された書籍のID
        """
        # 複数選択モードを無効化
        if self.multi_select_action.isChecked():
            self.toggle_multi_select_mode(False)

        # メタデータ編集アクションを有効化
        self.edit_metadata_action.setEnabled(True)

        # リーダービューに書籍を読み込む
        success = self.reader_view.load_book(book_id)

        if success:
            # 選択状態をビュー間で同期
            if self.sender() == self.grid_view:
                self.list_view.select_book(book_id, emit_signal=False)
            elif self.sender() == self.list_view:
                self.grid_view.select_book(book_id, emit_signal=False)

            # book_openedシグナルを発火
            self.book_opened.emit(book_id)

            # 書籍の情報をステータスバーに表示
            book = self.library_controller.get_book(book_id)
            if book:
                self.statusBar.showMessage(
                    f"Opened: {book.title} by {book.author or 'Unknown'}"
                )
        else:
            self.statusBar.showMessage("Failed to open book")

    def on_books_selected(self, book_ids):
        """
        複数の書籍が選択されたときの処理。

        Parameters
        ----------
        book_ids : list
            選択された書籍IDのリスト
        """
        # 選択数をステータスバーに表示
        self.statusBar.showMessage(f"Selected {len(book_ids)} books")

        # 一括操作のUI要素を更新
        self.update_batch_actions_state(len(book_ids) > 0)

        # 選択状態をビュー間で同期（必要に応じて）
        current_view = self.library_tabs.currentWidget()
        if current_view == self.grid_view:
            # 選択がグリッドビューからの場合、リストビューを同期
            self.sync_selection_to_list_view(book_ids)
        elif current_view == self.list_view:
            # 選択がリストビューからの場合、グリッドビューを同期
            self.sync_selection_to_grid_view(book_ids)

    def sync_selection_to_list_view(self, book_ids):
        """
        グリッドビューの選択をリストビューに同期する。

        Parameters
        ----------
        book_ids : list
            選択された書籍IDのリスト
        """
        # 複数選択モードを確保
        self.list_view.toggle_multi_select_mode(True)

        # 現在の選択をクリア
        self.list_view.list_widget.clearSelection()

        # 指定されたIDに対応するアイテムを選択
        for i in range(self.list_view.list_widget.count()):
            item = self.list_view.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in book_ids:
                item.setSelected(True)

    def sync_selection_to_grid_view(self, book_ids):
        """
        リストビューの選択をグリッドビューに同期する。

        Parameters
        ----------
        book_ids : list
            選択された書籍IDのリスト
        """
        # 複数選択モードを確保
        self.grid_view.toggle_multi_select_mode(True)

        # 現在の選択をクリア
        self.grid_view._clear_selection()

        # 指定されたIDを選択
        for book_id in book_ids:
            self.grid_view._select_book(book_id, add_to_selection=True)

    def _has_selected_book(self):
        """
        書籍が選択されているかどうかを確認する。

        Returns
        -------
        bool
            書籍が選択されている場合はTrue
        """
        grid_selected = self.grid_view.get_selected_book_id() is not None
        list_selected = self.list_view.get_selected_book_id() is not None
        return grid_selected or list_selected

    def update_batch_actions_state(self, has_selection=False):
        """
        複数選択関連のUI要素の状態を更新する。

        Parameters
        ----------
        has_selection : bool
            書籍が選択されているかどうか
        """
        # 複数選択モードがアクティブかどうか
        is_multi_select = self.multi_select_action.isChecked()

        # 有効/無効を設定
        enabled = is_multi_select and has_selection

        # ツールバーボタン
        self.batch_actions_button.setEnabled(enabled)

        # メニュー項目
        self.batch_edit_menu_action.setEnabled(enabled)
        self.batch_add_to_series_menu_action.setEnabled(enabled)
        self.batch_remove_from_series_menu_action.setEnabled(enabled)
        self.batch_mark_unread_menu_action.setEnabled(enabled)
        self.batch_mark_reading_menu_action.setEnabled(enabled)
        self.batch_mark_completed_menu_action.setEnabled(enabled)
        self.batch_remove_menu_action.setEnabled(enabled)

    def show_batch_metadata_editor(self, book_ids=None):
        """
        複数書籍のメタデータ一括編集ダイアログを表示する。

        Parameters
        ----------
        book_ids : list, optional
            編集する書籍IDのリスト。指定がない場合は現在選択されている書籍を使用。
        """
        if book_ids is None:
            # 現在のビューに応じて選択書籍を取得
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        try:
            # BatchMetadataEditorをインポート
            from views.batch_metadata_editor import BatchMetadataEditor

            # ダイアログを表示
            dialog = BatchMetadataEditor(self.library_controller, book_ids, self)
            if dialog.exec():
                # 書籍の表示を更新
                for book_id in book_ids:
                    self.grid_view.update_book_item(book_id)
                    self.list_view.update_book_item(book_id)

                self.statusBar.showMessage(
                    f"Updated metadata for {len(book_ids)} books"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def show_batch_add_to_series_dialog(self, book_ids=None):
        """
        複数書籍を一括でシリーズに追加するダイアログを表示する。

        Parameters
        ----------
        book_ids : list, optional
            追加する書籍IDのリスト。指定がない場合は現在選択されている書籍を使用。
        """
        if book_ids is None:
            # 現在のビューに応じて選択書籍を取得
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add to Series")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        # シリーズ選択
        series_combo = QComboBox()
        series_combo.addItem("-- Select Series --", None)

        # シリーズの一覧を取得
        series_list = self.library_controller.get_all_series()
        for series in series_list:
            series_combo.addItem(series.name, series.id)

        form_layout.addRow("Series:", series_combo)

        # 新しいシリーズの作成
        new_series_layout = QHBoxLayout()
        new_series_edit = QLineEdit()
        new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(new_series_edit)

        create_button = QPushButton("Create")
        new_series_layout.addWidget(create_button)

        form_layout.addRow("New Series:", new_series_layout)

        # シリーズ内の順番設定
        order_method_combo = QComboBox()
        order_method_combo.addItem("Auto-assign sequential numbers", "sequential")
        order_method_combo.addItem("Use specific starting number", "specific")
        order_method_combo.addItem("Do not assign order", "none")
        form_layout.addRow("Order Method:", order_method_combo)

        # 開始番号の入力欄
        order_layout = QHBoxLayout()
        start_order_spin = QSpinBox()
        start_order_spin.setMinimum(1)
        start_order_spin.setMaximum(9999)
        start_order_spin.setValue(1)
        order_layout.addWidget(start_order_spin)

        preserve_current_check = QCheckBox("Keep current order when possible")
        preserve_current_check.setChecked(True)
        order_layout.addWidget(preserve_current_check)

        form_layout.addRow("Starting Number:", order_layout)

        # オーダーメソッドが変更されたときのハンドラ
        def update_order_controls():
            method = order_method_combo.currentData()
            enabled = method != "none"
            start_order_spin.setEnabled(enabled)
            preserve_current_check.setEnabled(enabled)

        order_method_combo.currentIndexChanged.connect(update_order_controls)
        update_order_controls()  # 初期状態を設定

        layout.addLayout(form_layout)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # 「新しいシリーズ作成」ボタンが押されたときの処理
        def create_new_series():
            name = new_series_edit.text().strip()
            if name:
                series_id = self.library_controller.create_series(name=name)
                if series_id:
                    series_combo.addItem(name, series_id)
                    index = series_combo.findData(series_id)
                    if index >= 0:
                        series_combo.setCurrentIndex(index)
                    new_series_edit.clear()

        create_button.clicked.connect(create_new_series)

        # ダイアログを表示
        if dialog.exec():
            series_id = series_combo.currentData()
            if series_id:
                # 書籍をシリーズに追加
                order_method = order_method_combo.currentData()

                if order_method == "none":
                    # 順番を指定しない場合はそのまま追加
                    for book_id in book_ids:
                        self.library_controller.update_book_metadata(
                            book_id, series_id=series_id
                        )
                else:
                    # 順番を指定する場合
                    start_order = start_order_spin.value()
                    preserve_current = preserve_current_check.isChecked()

                    # 本のリストを取得
                    books = [
                        self.library_controller.get_book(book_id)
                        for book_id in book_ids
                    ]
                    books = [book for book in books if book]  # Noneをフィルタリング

                    # 自然順ソートを実装（数値を考慮したソート）
                    import re

                    def natural_sort_key(book):
                        """
                        タイトルの自然順でソート
                        """
                        title = book.title if book.title else ""
                        # 数値部分を抽出して数値として扱う
                        return [
                            int(c) if c.isdigit() else c.lower()
                            for c in re.split(r"(\d+)", title)
                        ]

                    if preserve_current:
                        # 現在の順番を維持しつつソート
                        books.sort(
                            key=lambda b: (
                                b.series_id != series_id,
                                b.series_order or float("inf"),
                            )
                        )
                        # 同じ順番の本はタイトルの自然順でソート
                        sorted_books = []
                        current_order = None
                        same_order_books = []

                        for book in books:
                            if book.series_order != current_order:
                                if same_order_books:
                                    # 同じ順番の本をタイトルでソート
                                    sorted_books.extend(
                                        sorted(same_order_books, key=natural_sort_key)
                                    )
                                    same_order_books = []
                                current_order = book.series_order

                            same_order_books.append(book)

                        # 最後の同じ順番の本を処理
                        if same_order_books:
                            sorted_books.extend(
                                sorted(same_order_books, key=natural_sort_key)
                            )

                        books = sorted_books
                    else:
                        # タイトルでソート（自然順）
                        books.sort(key=natural_sort_key)

                    # 各本に順番を割り当て
                    current_order = start_order
                    for book in books:
                        self.library_controller.update_book_metadata(
                            book.id, series_id=series_id, series_order=current_order
                        )
                        current_order += 1

                # ビューを更新
                for book_id in book_ids:
                    self.grid_view.update_book_item(book_id)
                    self.list_view.update_book_item(book_id)

                self.statusBar.showMessage(f"Added {len(book_ids)} books to series")

    def batch_remove_from_series(self, book_ids=None):
        """
        複数書籍を一括でシリーズから削除する。

        Parameters
        ----------
        book_ids : list, optional
            削除する書籍IDのリスト。指定がない場合は現在選択されている書籍を使用。
        """
        if book_ids is None:
            # 現在のビューに応じて選択書籍を取得
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        # 確認ダイアログ
        result = QMessageBox.question(
            self,
            "Confirm Remove from Series",
            f"Are you sure you want to remove {len(book_ids)} books from their series?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # 書籍をシリーズから削除
        for book_id in book_ids:
            self.library_controller.update_book_metadata(
                book_id, series_id=None, series_order=None
            )

        # ビューを更新
        for book_id in book_ids:
            self.grid_view.update_book_item(book_id)
            self.list_view.update_book_item(book_id)

        self.statusBar.showMessage(f"Removed {len(book_ids)} books from series")

    def batch_mark_as_status(self, status, book_ids=None):
        """
        複数書籍の読書状態を一括で設定する。

        Parameters
        ----------
        status : str
            設定する状態
        book_ids : list, optional
            対象の書籍IDリスト。指定がない場合は現在選択されている書籍を使用。
        """
        if book_ids is None:
            # 現在のビューに応じて選択書籍を取得
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        # 状態名をわかりやすい表示に変換
        status_display = {
            "unread": "Unread",
            "reading": "Reading",
            "completed": "Completed",
        }.get(status, status)

        # 書籍の状態を更新
        for book_id in book_ids:
            self.library_controller.update_book_progress(book_id, status=status)

        # ビューを更新
        for book_id in book_ids:
            self.grid_view.update_book_item(book_id)
            self.list_view.update_book_item(book_id)

        self.statusBar.showMessage(f"Marked {len(book_ids)} books as {status_display}")

    def batch_remove_books(self, book_ids=None):
        """
        複数書籍を一括で削除する。

        Parameters
        ----------
        book_ids : list, optional
            削除する書籍IDリスト。指定がない場合は現在選択されている書籍を使用。
        """
        if book_ids is None:
            # 現在のビューに応じて選択書籍を取得
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        # 確認ダイアログ
        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to remove {len(book_ids)} books from the library?\n\n"
            "This will only remove the books from the library, not delete the files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # 現在開いている書籍をチェック
        if self.reader_view.current_book_id in book_ids:
            self.reader_view.close_current_book()

        # 書籍を一括削除
        result = self.library_controller.batch_remove_books(
            book_ids, delete_files=False
        )

        # 成功したIDを処理
        if result["success"]:
            # グリッドビューから削除
            for book_id in result["success"]:
                if book_id in self.grid_view.book_widgets:
                    widget = self.grid_view.book_widgets[book_id]
                    widget.setParent(None)
                    widget.deleteLater()
                    del self.grid_view.book_widgets[book_id]

                    # 選択状態を更新
                    if book_id in self.grid_view.selected_book_ids:
                        self.grid_view.selected_book_ids.remove(book_id)
                    if self.grid_view.selected_book_id == book_id:
                        self.grid_view.selected_book_id = None

            # リストビューから削除
            for book_id in result["success"]:
                for i in range(self.list_view.list_widget.count()):
                    item = self.list_view.list_widget.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                        self.list_view.list_widget.takeItem(i)
                        break

        # 失敗したIDがある場合は警告
        if result["failed"]:
            QMessageBox.warning(
                self, "Warning", f"Failed to remove {len(result['failed'])} books."
            )

        # ステータスバーに表示
        self.statusBar.showMessage(
            f"Removed {len(result['success'])} books from library"
        )

        # 複数選択関連のUIを更新
        self.update_batch_actions_state()

    def on_series_selected(self, series_id):
        """
        シリーズが選択されたときの処理。

        Parameters
        ----------
        series_id : int
            選択されたシリーズのID
        """
        # シリーズを取得
        series = self.library_controller.get_series(series_id)
        if not series:
            self.statusBar.showMessage("Series not found")
            return

        # 現在のシリーズIDを保存
        self.current_series_id = series_id

        # シリーズの書籍をキャッシュに保存
        if series_id not in self.series_books_cache:
            # シリーズに属する書籍を先に取得してキャッシュに保存
            books = self.library_controller.get_all_books(series_id=series_id)
            self.series_books_cache[series_id] = books

        # シリーズのビューを書籍に切り替え
        self.show_series_books(series)

        # スタータスバーにメッセージを表示
        self.statusBar.showMessage(f"Series: {series.name} ({len(series.books)} books)")

    def show_series_books(self, series):
        """
        シリーズに属する書籍を表示する。

        Parameters
        ----------
        series : Series
            表示するシリーズオブジェクト
        """
        # ナビゲーションバーを更新
        self.back_to_series_button.setVisible(True)
        self.current_series_label.setText(f"Series: {series.name}")

        # パフォーマンス改善: フィルタリングを最適化
        self.filter_by_series(series.id)

        # 書籍タブに切り替え
        self.main_tabs.setCurrentWidget(self.books_tab)

    def show_series_view(self):
        """シリーズビューに戻る。"""
        # ナビゲーションバーを更新
        self.back_to_series_button.setVisible(False)
        self.current_series_label.setText("")

        # フィルタをクリア
        self.clear_series_filter()

        # シリーズタブに切り替え
        self.main_tabs.setCurrentWidget(self.series_tab)

    def filter_by_series(self, series_id):
        """
        シリーズでフィルタリングする。

        Parameters
        ----------
        series_id : int
            フィルタリングするシリーズID
        """
        # キャッシュから書籍リストを取得（パフォーマンス改善）
        if series_id in self.series_books_cache:
            books = self.series_books_cache[series_id]
        else:
            # キャッシュにない場合は取得してキャッシュに保存
            books = self.library_controller.get_all_books(series_id=series_id)
            self.series_books_cache[series_id] = books

        # 現在のビューに応じてリストを更新
        current_view = self.library_tabs.currentWidget()
        if current_view == self.grid_view:
            # グリッドビューの表示をクリア
            self.grid_view._clear_grid()
            # シリーズに属する書籍を表示
            self.grid_view._populate_grid(books)
        else:
            # リストビューの表示をクリア
            self.list_view.list_widget.clear()
            # シリーズに属する書籍を表示
            self.list_view._populate_list(books)

    def clear_series_filter(self):
        """シリーズフィルタをクリアする。"""
        self.grid_view.refresh()
        self.list_view.refresh()

        # キャッシュをクリア
        self.current_series_id = None

    def update_series_view_state(self):
        """シリーズビュー状態を更新する。"""
        # 現在のシリーズビュータイプを取得
        current_series_view = self.series_tabs.currentWidget()

        # ビューの選択状態を同期
        if current_series_view == self.series_grid_view:
            # グリッドビューが選択されている場合
            self.grid_view_action.setChecked(True)
            self.list_view_action.setChecked(False)
        else:
            # リストビューが選択されている場合
            self.grid_view_action.setChecked(False)
            self.list_view_action.setChecked(True)

    def show_series_editor(self, series_id=None):
        """
        シリーズ編集ダイアログを表示する。

        Parameters
        ----------
        series_id : int, optional
            編集するシリーズのID。指定されない場合は現在選択されているシリーズを使用。
        """
        # シリーズIDが指定されていない場合は現在選択されているシリーズを使用
        if series_id is None:
            series_id = (
                self.series_grid_view.get_selected_series_id()
                or self.series_list_view.get_selected_series_id()
            )

        if series_id:
            try:
                from views.series_editor import SeriesEditor

                dialog = SeriesEditor(self.library_controller, series_id, self)
                if dialog.exec():
                    # シリーズビューを更新
                    self.series_grid_view.update_series_item(series_id)
                    self.series_list_view.update_series_item(series_id)

                    # 書籍ビューも更新
                    self.refresh_library()

                    self.statusBar.showMessage("Series updated successfully")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to open series editor: {e}"
                )

    def remove_series(self, series_id):
        """
        シリーズを削除する。

        Parameters
        ----------
        series_id : int
            削除するシリーズID
        """
        # シリーズを取得
        series = self.library_controller.get_series(series_id)
        if not series:
            return

        # 確認ダイアログを表示
        books_count = len(series.books)
        message = f"Are you sure you want to remove the series '{series.name}'?"

        if books_count > 0:
            message += f"\n\nThis series contains {books_count} books. "
            message += "The books will remain in your library but will no longer be associated with this series."

        result = QMessageBox.question(
            self,
            "Confirm Delete",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # シリーズ内の全書籍のシリーズIDをNULLに設定
        for book in series.books:
            book.update_metadata(series_id=None, series_order=None)

        # シリーズを削除
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            # カスタムメタデータを削除
            cursor.execute(
                "DELETE FROM custom_metadata WHERE series_id = ?", (series_id,)
            )

            # シリーズを削除
            cursor.execute("DELETE FROM series WHERE id = ?", (series_id,))

            conn.commit()

            # キャッシュからも削除
            if series_id in self.series_books_cache:
                del self.series_books_cache[series_id]

            # シリーズビューを更新
            self.series_grid_view.refresh()
            self.series_list_view.refresh()

            # 現在表示中のシリーズなら元に戻す
            if self.current_series_id == series_id:
                self.show_series_view()

            self.statusBar.showMessage(f"Series '{series.name}' removed")

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to remove series: {e}")
