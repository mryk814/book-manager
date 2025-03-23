from PyQt6.QtCore import (
    QSettings,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
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
from views.dialogs.import_dialog import ImportDialog
from views.dialogs.settings_dialog import SettingsDialog
from views.library_view import LibraryGridView, LibraryListView
from views.metadata_editor import MetadataEditor
from views.reader_view import PDFReaderView
from views.series_view import (
    SeriesGridView,
    SeriesListView,
)


class MainWindow(QMainWindow):
    book_opened = pyqtSignal(int)  # book_id

    def __init__(self, db_path="library.db", splash=None):
        super().__init__()

        self.splash = splash
        self.loading = True

        self._update_splash("データベース接続を初期化中...")
        self.db_manager = DatabaseManager(db_path)
        self.library_controller = LibraryController(self.db_manager)

        self.setWindowTitle("PDF Library Manager")
        self.setMinimumSize(400, 400)
        self.resize(1600, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._update_splash("UIコンポーネントを初期化中...")

        self.setup_toolbar()

        self.setup_menubar()

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)

        self.library_panel = QWidget()
        self.library_layout = QVBoxLayout(self.library_panel)
        self.setup_library_panel()
        self.main_splitter.addWidget(self.library_panel)

        self.reader_panel = QWidget()
        self.reader_layout = QVBoxLayout(self.reader_panel)
        self.setup_reader_panel()
        self.main_splitter.addWidget(self.reader_panel)

        self.main_splitter.setSizes([550, 700])
        QTimer.singleShot(100, self.set_optimal_splitter_sizes)

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)

        self.left_panel_width = 550

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setMaximumWidth(100)
        self.statusBar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setVisible(True)

        self.statusBar.showMessage("ライブラリデータを読み込み中...")

        self.setup_connections()

        self.setup_context_menu_handlers()

        self.main_tabs.currentChanged.connect(self.on_main_tab_changed)

        self.needs_filter_clear = False

        self.all_series = []

        self.series_books_cache = {}

        self.last_books_tab_index = 0

        self.current_series_id = None
        self.in_series_filtered_mode = False

        QTimer.singleShot(50, self.async_initialize_data)

        self.restore_window_state()

        self.configure_window_for_display()

        self.load_grid_view_settings()

        self.default_sort_by = "title"
        self.default_sort_order = "asc"

        QTimer.singleShot(100, self.apply_window_settings)

    def apply_window_settings(self):
        settings = QSettings("YourOrg", "PDFLibraryManager")

        size = settings.value("window/size")
        if size:
            try:
                if isinstance(size, str):
                    width, height = map(int, size.strip("()").split(","))
                    self.resize(width, height)
                else:
                    self.resize(size)
            except (ValueError, TypeError):
                pass

    def configure_window_for_display(self):
        screen = QApplication.primaryScreen().availableGeometry()

        if screen.width() >= 1920:
            width = int(screen.width() * 0.8)
            height = int(screen.height() * 0.8)
            self.resize(width, height)
        else:
            width = min(1280, int(screen.width() * 0.9))
            height = min(720, int(screen.height() * 0.9))
            self.resize(width, height)

    def load_grid_view_settings(self):
        settings = QSettings("YourOrg", "PDFLibraryManager")

        preferred_columns = settings.value("grid_view/preferred_columns", 5, int)
        self.grid_view.ideal_columns = preferred_columns

        QTimer.singleShot(200, self.adjust_layouts_after_show)

    def adjust_layouts_after_show(self):
        self.set_optimal_splitter_sizes()

        self.grid_view.calculate_grid_columns()
        self.grid_view.relayout_grid()

        self.series_grid_view.calculate_grid_columns()
        self.series_grid_view.relayout_grid()

    def _update_splash(self, message):
        if self.splash:
            self.splash.showMessage(
                message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
            )
            QApplication.processEvents()

    def set_optimal_splitter_sizes(self):
        total_width = self.width()
        left_panel_width = int(total_width * 0.35)
        right_panel_width = total_width - left_panel_width
        self.main_splitter.setSizes([left_panel_width, right_panel_width])
        self.left_panel_width = left_panel_width

    def async_initialize_data(self):
        self._update_splash("書籍データを読み込み中...")
        QTimer.singleShot(0, self.load_books_async)

    def load_books_async(self):
        self.statusBar.showMessage("書籍データを読み込み中...")
        self.grid_view.refresh()
        self.list_view.refresh()

        QTimer.singleShot(100, self.load_series_async)

    def load_series_async(self):
        self.statusBar.showMessage("シリーズデータを読み込み中...")
        self._update_splash("シリーズデータを読み込み中...")

        self.all_series = self.library_controller.get_all_series()
        self.series_grid_view.refresh()
        self.series_list_view.refresh()

        QTimer.singleShot(100, self.finish_loading)

    def finish_loading(self):
        self.loading = False
        self.progress_bar.setVisible(False)
        self.statusBar.showMessage("ライブラリの読み込みが完了しました", 3000)

        QTimer.singleShot(100, self.initial_layout_adjustment)

    def initial_layout_adjustment(self):
        self.grid_view.ensure_correct_layout()
        self.series_grid_view.ensure_correct_layout()
        self.list_view.update()

    def setup_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)

        self.import_action = QAction("Import", self)
        self.import_action.setStatusTip("Import PDFs to library")
        self.import_action.triggered.connect(self.show_import_dialog)
        self.toolbar.addAction(self.import_action)

        self.toolbar.addSeparator()

        self.multi_select_action = QAction("Multi-Select", self)
        self.multi_select_action.setCheckable(True)
        self.multi_select_action.setStatusTip("Enable multiple selection")
        self.multi_select_action.triggered.connect(self.toggle_multi_select_mode)
        self.toolbar.addAction(self.multi_select_action)

        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setStatusTip("Select all visible books")
        self.select_all_action.triggered.connect(self.select_all_books)
        self.select_all_action.setEnabled(False)

        self.batch_actions_button = QPushButton("Batch Actions")
        self.batch_actions_button.setEnabled(False)

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

        self.view_label = QLabel("View:")
        self.toolbar.addWidget(self.view_label)

        self.view_type_combo = QComboBox()
        self.view_type_combo.addItems(["Grid View", "List View"])
        self.view_type_combo.currentIndexChanged.connect(self.change_view_type)
        self.toolbar.addWidget(self.view_type_combo)

        self.toolbar.addSeparator()

        self.category_label = QLabel("Category:")
        self.toolbar.addWidget(self.category_label)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.populate_category_combo()
        self.category_combo.currentIndexChanged.connect(self.filter_by_category)
        self.toolbar.addWidget(self.category_combo)
        self.clear_category_filter_button = QPushButton("Clear")
        self.clear_category_filter_button.clicked.connect(self.clear_category_filter)
        self.toolbar.addWidget(self.clear_category_filter_button)

        self.toolbar.addSeparator()

        self.status_label = QLabel("Status:")
        self.toolbar.addWidget(self.status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", None)
        self.status_combo.addItem("Unread", Book.STATUS_UNREAD)
        self.status_combo.addItem("Reading", Book.STATUS_READING)
        self.status_combo.addItem("Completed", Book.STATUS_COMPLETED)
        self.status_combo.currentIndexChanged.connect(self.filter_by_status)
        self.toolbar.addWidget(self.status_combo)

        self.clear_status_filter_button = QPushButton("Clear")
        self.clear_status_filter_button.clicked.connect(self.clear_status_filter)
        self.toolbar.addWidget(self.clear_status_filter_button)
        self.toolbar.addSeparator()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search books...")
        self.search_box.setMinimumWidth(200)
        self.search_box.returnPressed.connect(self.search_books)
        self.toolbar.addWidget(self.search_box)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_books)
        self.toolbar.addWidget(self.search_button)

        self.clear_search_button = QPushButton("Clear")
        self.clear_search_button.clicked.connect(self.clear_search)
        self.toolbar.addWidget(self.clear_search_button)

    def setup_menubar(self):
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

        edit_menu = self.menuBar().addMenu("&Edit")

        edit_metadata_action = QAction("Edit &Metadata...", self)
        edit_metadata_action.setEnabled(False)  # 書籍選択時に有効化
        edit_metadata_action.triggered.connect(self.show_metadata_editor)
        edit_menu.addAction(edit_metadata_action)
        self.edit_metadata_action = edit_metadata_action

        edit_menu.addSeparator()

        manage_categories_action = QAction("Manage &Categories...", self)
        manage_categories_action.triggered.connect(self.show_category_manager)
        edit_menu.addAction(manage_categories_action)

        multi_select_menu_action = QAction("&Multi-Select Mode", self)
        multi_select_menu_action.setCheckable(True)
        multi_select_menu_action.triggered.connect(self.toggle_multi_select_mode)
        edit_menu.addAction(multi_select_menu_action)
        self.multi_select_menu_action = multi_select_menu_action

        select_all_menu_action = QAction("Select &All", self)
        select_all_menu_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_menu_action.triggered.connect(self.select_all_books)
        select_all_menu_action.setEnabled(False)  # 初期状態では無効
        edit_menu.addAction(select_all_menu_action)
        self.select_all_menu_action = select_all_menu_action

        edit_menu.addSeparator()

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

        help_menu = self.menuBar().addMenu("&Help")

        debug_menu = QMenu("&Debug", self)
        help_menu.addMenu(debug_menu)

        db_inspector_action = QAction("&Database Inspector", self)
        db_inspector_action.triggered.connect(self.show_db_inspector)
        debug_menu.addAction(db_inspector_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def setup_library_panel(self):
        self.main_tabs = QTabWidget()
        self.library_layout.addWidget(self.main_tabs)

        self.books_tab = QWidget()
        books_layout = QVBoxLayout(self.books_tab)
        books_layout.setContentsMargins(0, 0, 0, 0)
        self.main_tabs.addTab(self.books_tab, "Books")

        self.series_navigation = QWidget()
        series_navigation_layout = QHBoxLayout(self.series_navigation)
        series_navigation_layout.setContentsMargins(5, 5, 5, 5)

        self.back_to_series_button = QPushButton("← Back to Series")
        self.back_to_series_button.clicked.connect(self.show_series_view)
        self.back_to_series_button.setVisible(False)
        series_navigation_layout.addWidget(self.back_to_series_button)

        self.current_series_label = QLabel("")
        self.current_series_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        series_navigation_layout.addWidget(self.current_series_label)

        series_navigation_layout.addStretch(1)

        books_layout.addWidget(self.series_navigation)

        self.library_tabs = QTabWidget()
        books_layout.addWidget(self.library_tabs)

        self.grid_view = LibraryGridView(self.library_controller)
        self.library_tabs.addTab(self.grid_view, "Grid View")

        self.list_view = LibraryListView(self.library_controller)
        self.library_tabs.addTab(self.list_view, "List View")

        self.series_tab = QWidget()
        series_layout = QVBoxLayout(self.series_tab)
        series_layout.setContentsMargins(0, 0, 0, 0)
        self.main_tabs.addTab(self.series_tab, "Series")

        self.series_tabs = QTabWidget()
        series_layout.addWidget(self.series_tabs)

        self.series_grid_view = SeriesGridView(self.library_controller)
        self.series_tabs.addTab(self.series_grid_view, "Grid View")

        self.series_list_view = SeriesListView(self.library_controller)
        self.series_tabs.addTab(self.series_list_view, "List View")

        self.library_tabs.currentChanged.connect(
            lambda idx: self.view_type_combo.setCurrentIndex(idx)
        )

        self.series_tabs.currentChanged.connect(
            lambda idx: self.update_series_view_state()
        )

        self.series_grid_view.series_selected.connect(self.on_series_selected)
        self.series_list_view.series_selected.connect(self.on_series_selected)

        self.current_series_id = None

        self.series_books_cache = {}

    def setup_reader_panel(self):
        self.reader_view = PDFReaderView(self.library_controller)
        self.reader_layout.addWidget(self.reader_view)

    def setup_context_menu_handlers(self):
        self.grid_view._edit_metadata = self.show_metadata_editor
        self.grid_view._batch_edit_metadata = self.show_batch_metadata_editor
        self.grid_view._add_to_series = self.show_add_to_series_dialog
        self.grid_view._batch_add_to_series = self.show_batch_add_to_series_dialog
        self.grid_view._batch_remove_from_series = self.batch_remove_from_series
        self.grid_view._remove_book = self.remove_book
        self.grid_view._batch_remove_books = self.batch_remove_books

        self.list_view._edit_metadata = self.show_metadata_editor
        self.list_view._batch_edit_metadata = self.show_batch_metadata_editor
        self.list_view._add_to_series = self.show_add_to_series_dialog
        self.list_view._batch_add_to_series = self.show_batch_add_to_series_dialog
        self.list_view._batch_remove_from_series = self.batch_remove_from_series
        self.list_view._remove_book = self.remove_book
        self.list_view._batch_remove_books = self.batch_remove_books

        self.series_grid_view._edit_series = self.show_series_editor
        self.series_grid_view._remove_series = self.remove_series

        self.series_list_view._edit_series = self.show_series_editor
        self.series_list_view._remove_series = self.remove_series

    def setup_connections(self):
        self.grid_view.book_selected.connect(self.on_book_selected)
        self.grid_view.books_selected.connect(self.on_books_selected)

        self.list_view.book_selected.connect(self.on_book_selected)
        self.list_view.books_selected.connect(self.on_books_selected)

        self.reader_view.progress_updated.connect(self.on_progress_updated)

        self.library_tabs.currentChanged.connect(self.on_library_tab_changed)
        self.main_tabs.currentChanged.connect(self.on_main_tab_changed)

    def populate_category_combo(self):
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)

        categories = self.db_manager.get_all_categories()
        for category in categories:
            self.category_combo.addItem(category["name"], category["id"])

    def change_view_type(self, index):
        current_main_tab = self.main_tabs.currentWidget()

        if current_main_tab == self.books_tab:
            self.library_tabs.setCurrentIndex(index)

            self.grid_view_action.setChecked(index == 0)
            self.list_view_action.setChecked(index == 1)

            if index == 0:
                QTimer.singleShot(100, self.grid_view.ensure_correct_layout)

            if self.current_series_id and self.back_to_series_button.isVisible():
                self.filter_by_series(self.current_series_id)

        elif current_main_tab == self.series_tab:
            self.series_tabs.setCurrentIndex(index)

            if index == 0:
                QTimer.singleShot(100, self.series_grid_view.ensure_correct_layout)

        if index == 0:  # Grid View
            QTimer.singleShot(50, lambda: self.grid_view.ensure_correct_layout())

    def filter_by_category(self, index):
        category_id = self.category_combo.itemData(index)

        self.grid_view.set_category_filter(category_id)
        self.list_view.set_category_filter(category_id)

        self.series_grid_view.set_category_filter(category_id)
        self.series_list_view.set_category_filter(category_id)

        self.update_category_filter_status()

    def search_books(self):
        query = self.search_box.text().strip()
        if query:
            self.grid_view.search(query)
            self.list_view.search(query)
            self.statusBar.showMessage(f"Search results for: {query}")

    def clear_category_filter(self):
        self.category_combo.setCurrentIndex(0)
        self.update_filter_status()

    def clear_search(self):
        self.search_box.clear()
        self.grid_view.clear_search()
        self.list_view.clear_search()
        self.statusBar.showMessage("Search cleared")

    def on_book_selected(self, book_id):
        if self.multi_select_action.isChecked():
            self.toggle_multi_select_mode(False)

        self.edit_metadata_action.setEnabled(True)

        success = self.reader_view.load_book(book_id)

        if success:
            if self.sender() == self.grid_view:
                self.list_view.select_book(book_id, emit_signal=False)
            elif self.sender() == self.list_view:
                self.grid_view.select_book(book_id, emit_signal=False)

            self.book_opened.emit(book_id)

            book = self.library_controller.get_book(book_id)
            if book:
                self.statusBar.showMessage(
                    f"Opened: {book.title} by {book.author or 'Unknown'}"
                )
        else:
            self.statusBar.showMessage("Failed to open book")

    def on_progress_updated(self, book_id, current_page, status):
        self.grid_view.update_book_item(book_id)
        self.list_view.update_book_item(book_id)

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
        dialog = ImportDialog(self.library_controller, self)
        if dialog.exec():
            self.refresh_library()
            self.statusBar.showMessage("Books imported successfully")

    def show_metadata_editor(self, book_id=None):
        if book_id is None:
            book_id = (
                self.grid_view.get_selected_book_id()
                or self.list_view.get_selected_book_id()
            )

        if book_id:
            dialog = MetadataEditor(self.library_controller, book_id, self)
            if dialog.exec():
                self.grid_view.update_book_item(book_id)
                self.list_view.update_book_item(book_id)

                book = self.library_controller.get_book(book_id)
                if book and book.series_id:
                    self.series_grid_view.update_series_item(book.series_id)
                    self.series_list_view.update_series_item(book.series_id)

                self.statusBar.showMessage("Metadata updated successfully")

    def show_add_to_series_dialog(self, book_id):
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

        series_combo = QComboBox()
        series_combo.addItem("-- Select Series --", None)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            series_combo.addItem(series.name, series.id)

        form_layout.addRow("Series:", series_combo)

        new_series_layout = QHBoxLayout()
        new_series_edit = QLineEdit()
        new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(new_series_edit)

        create_button = QPushButton("Create")
        new_series_layout.addWidget(create_button)

        form_layout.addRow("New Series:", new_series_layout)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

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

        if dialog.exec():
            series_id = series_combo.currentData()
            if series_id:
                self.library_controller.update_book_metadata(
                    book_id, series_id=series_id
                )

                self.grid_view.update_book_item(book_id)
                self.list_view.update_book_item(book_id)
                self.statusBar.showMessage("Book added to series")

    def remove_book(self, book_id):
        from PyQt6.QtWidgets import QMessageBox

        book = self.library_controller.get_book(book_id)
        if not book:
            return

        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to remove '{book.title}' from the library?\n\n"
            "This will only remove the book from the library, not delete the file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            if self.reader_view.current_book_id == book_id:
                self.reader_view.close_current_book()

            success = self.library_controller.remove_book(book_id, delete_file=False)

            if success:
                if book_id in self.grid_view.book_widgets:
                    widget = self.grid_view.book_widgets[book_id]
                    widget.setParent(None)
                    widget.deleteLater()
                    del self.grid_view.book_widgets[book_id]

                for i in range(self.list_view.list_widget.count()):
                    item = self.list_view.list_widget.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                        self.list_view.list_widget.takeItem(i)
                        break

                if self.grid_view.selected_book_id == book_id:
                    self.grid_view.selected_book_id = None
                if self.list_view.get_selected_book_id() == book_id:
                    self.list_view.list_widget.clearSelection()

                self.statusBar.showMessage(f"Book '{book.title}' removed from library")

    def show_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About PDF Library Manager",
            "PDF Library Manager\n\n"
            "A desktop application for managing your PDF book collection.\n"
            "Version 1.0.0",
        )

    def refresh_library(self):
        self.series_books_cache = {}
        self.all_series = []

        current_main_tab = self.main_tabs.currentWidget()

        if current_main_tab == self.books_tab:
            self.refresh_books_view()
        else:
            self.load_all_series()

        self.populate_category_combo()

        self.statusBar.showMessage("Library refreshed")

    def closeEvent(self, event):
        self.save_window_state()

        self.reader_view.close_current_book()
        self.db_manager.close()
        event.accept()

    def toggle_multi_select_mode(self, enabled):
        self.multi_select_action.setChecked(enabled)
        self.multi_select_menu_action.setChecked(enabled)

        self.grid_view.toggle_multi_select_mode(enabled)
        self.list_view.toggle_multi_select_mode(enabled)

        self.select_all_action.setEnabled(enabled)
        self.select_all_menu_action.setEnabled(enabled)

        self.edit_metadata_action.setEnabled(not enabled and self._has_selected_book())

        self.update_batch_actions_state()

        if enabled:
            self.statusBar.showMessage("Multiple selection mode enabled")
        else:
            self.statusBar.showMessage("Multiple selection mode disabled")

    def select_all_books(self):
        current_view = self.library_tabs.currentWidget()
        if current_view:
            current_view.select_all()

    def on_books_selected(self, book_ids):
        self.statusBar.showMessage(f"Selected {len(book_ids)} books")

        self.update_batch_actions_state(len(book_ids) > 0)

        current_view = self.library_tabs.currentWidget()
        if current_view == self.grid_view:
            self.sync_selection_to_list_view(book_ids)
        elif current_view == self.list_view:
            self.sync_selection_to_grid_view(book_ids)

    def sync_selection_to_list_view(self, book_ids):
        self.list_view.toggle_multi_select_mode(True)

        self.list_view.list_widget.clearSelection()

        for i in range(self.list_view.list_widget.count()):
            item = self.list_view.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in book_ids:
                item.setSelected(True)

    def sync_selection_to_grid_view(self, book_ids):
        self.grid_view.toggle_multi_select_mode(True)

        self.grid_view._clear_selection()

        for book_id in book_ids:
            self.grid_view._select_book(book_id, add_to_selection=True)

    def _has_selected_book(self):
        grid_selected = self.grid_view.get_selected_book_id() is not None
        list_selected = self.list_view.get_selected_book_id() is not None
        return grid_selected or list_selected

    def update_batch_actions_state(self, has_selection=False):
        is_multi_select = self.multi_select_action.isChecked()

        enabled = is_multi_select and has_selection

        self.batch_actions_button.setEnabled(enabled)

        self.batch_edit_menu_action.setEnabled(enabled)
        self.batch_add_to_series_menu_action.setEnabled(enabled)
        self.batch_remove_from_series_menu_action.setEnabled(enabled)
        self.batch_mark_unread_menu_action.setEnabled(enabled)
        self.batch_mark_reading_menu_action.setEnabled(enabled)
        self.batch_mark_completed_menu_action.setEnabled(enabled)
        self.batch_remove_menu_action.setEnabled(enabled)

    def show_batch_metadata_editor(self, book_ids=None):
        if book_ids is None:
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        try:
            from views.batch_metadata_editor import BatchMetadataEditor

            dialog = BatchMetadataEditor(self.library_controller, book_ids, self)
            if dialog.exec():
                for book_id in book_ids:
                    self.grid_view.update_book_item(book_id)
                    self.list_view.update_book_item(book_id)

                self.statusBar.showMessage(
                    f"Updated metadata for {len(book_ids)} books"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def show_batch_add_to_series_dialog(self, book_ids=None):
        if book_ids is None:
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

        series_combo = QComboBox()
        series_combo.addItem("-- Select Series --", None)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            series_combo.addItem(series.name, series.id)

        form_layout.addRow("Series:", series_combo)

        new_series_layout = QHBoxLayout()
        new_series_edit = QLineEdit()
        new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(new_series_edit)

        create_button = QPushButton("Create")
        new_series_layout.addWidget(create_button)

        form_layout.addRow("New Series:", new_series_layout)

        order_method_combo = QComboBox()
        order_method_combo.addItem("Auto-assign sequential numbers", "sequential")
        order_method_combo.addItem("Use specific starting number", "specific")
        order_method_combo.addItem("Do not assign order", "none")
        form_layout.addRow("Order Method:", order_method_combo)

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

        def update_order_controls():
            method = order_method_combo.currentData()
            enabled = method != "none"
            start_order_spin.setEnabled(enabled)
            preserve_current_check.setEnabled(enabled)

        order_method_combo.currentIndexChanged.connect(update_order_controls)
        update_order_controls()

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

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

        if dialog.exec():
            series_id = series_combo.currentData()
            if series_id:
                order_method = order_method_combo.currentData()

                if order_method == "none":
                    for book_id in book_ids:
                        self.library_controller.update_book_metadata(
                            book_id, series_id=series_id
                        )
                else:
                    start_order = start_order_spin.value()
                    preserve_current = preserve_current_check.isChecked()

                    books = [
                        self.library_controller.get_book(book_id)
                        for book_id in book_ids
                    ]
                    books = [book for book in books if book]

                    import re

                    def natural_sort_key(book):
                        title = book.title if book.title else ""
                        return [
                            int(c) if c.isdigit() else c.lower()
                            for c in re.split(r"(\d+)", title)
                        ]

                    if preserve_current:
                        books.sort(
                            key=lambda b: (
                                b.series_id != series_id,
                                b.series_order or float("inf"),
                            )
                        )
                        sorted_books = []
                        current_order = None
                        same_order_books = []

                        for book in books:
                            if book.series_order != current_order:
                                if same_order_books:
                                    sorted_books.extend(
                                        sorted(same_order_books, key=natural_sort_key)
                                    )
                                    same_order_books = []
                                current_order = book.series_order

                            same_order_books.append(book)

                        if same_order_books:
                            sorted_books.extend(
                                sorted(same_order_books, key=natural_sort_key)
                            )

                        books = sorted_books
                    else:
                        books.sort(key=natural_sort_key)

                    current_order = start_order
                    for book in books:
                        self.library_controller.update_book_metadata(
                            book.id, series_id=series_id, series_order=current_order
                        )
                        current_order += 1

                for book_id in book_ids:
                    self.grid_view.update_book_item(book_id)
                    self.list_view.update_book_item(book_id)

                self.statusBar.showMessage(f"Added {len(book_ids)} books to series")

    def batch_remove_from_series(self, book_ids=None):
        if book_ids is None:
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        result = QMessageBox.question(
            self,
            "Confirm Remove from Series",
            f"Are you sure you want to remove {len(book_ids)} books from their series?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        for book_id in book_ids:
            self.library_controller.update_book_metadata(
                book_id, series_id=None, series_order=None
            )

        for book_id in book_ids:
            self.grid_view.update_book_item(book_id)
            self.list_view.update_book_item(book_id)

        self.statusBar.showMessage(f"Removed {len(book_ids)} books from series")

    def batch_mark_as_status(self, status, book_ids=None):
        if book_ids is None:
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

        status_display = {
            "unread": "Unread",
            "reading": "Reading",
            "completed": "Completed",
        }.get(status, status)

        for book_id in book_ids:
            self.library_controller.update_book_progress(book_id, status=status)

        for book_id in book_ids:
            self.grid_view.update_book_item(book_id)
            self.list_view.update_book_item(book_id)

        self.statusBar.showMessage(f"Marked {len(book_ids)} books as {status_display}")

    def batch_remove_books(self, book_ids=None):
        if book_ids is None:
            current_view = self.library_tabs.currentWidget()
            if current_view == self.grid_view:
                book_ids = self.grid_view.get_selected_book_ids()
            else:
                book_ids = self.list_view.get_selected_book_ids()

        if not book_ids:
            QMessageBox.warning(self, "Warning", "No books selected.")
            return

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

        if self.reader_view.current_book_id in book_ids:
            self.reader_view.close_current_book()

        result = self.library_controller.batch_remove_books(
            book_ids, delete_files=False
        )

        if result["success"]:
            for book_id in result["success"]:
                if book_id in self.grid_view.book_widgets:
                    widget = self.grid_view.book_widgets[book_id]
                    widget.setParent(None)
                    widget.deleteLater()
                    del self.grid_view.book_widgets[book_id]

                    if book_id in self.grid_view.selected_book_ids:
                        self.grid_view.selected_book_ids.remove(book_id)
                    if self.grid_view.selected_book_id == book_id:
                        self.grid_view.selected_book_id = None

            for book_id in result["success"]:
                for i in range(self.list_view.list_widget.count()):
                    item = self.list_view.list_widget.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                        self.list_view.list_widget.takeItem(i)
                        break

        if result["failed"]:
            QMessageBox.warning(
                self, "Warning", f"Failed to remove {len(result['failed'])} books."
            )

        self.statusBar.showMessage(
            f"Removed {len(result['success'])} books from library"
        )

        self.update_batch_actions_state()

    def on_series_selected(self, series_id):
        series = self.library_controller.get_series(series_id)
        if not series:
            self.statusBar.showMessage("Series not found")
            return

        self.current_series_id = series_id

        self.in_series_filtered_mode = True

        self.back_to_series_button.setVisible(True)
        self.current_series_label.setText(f"Series: {series.name}")

        self.apply_series_filter(series_id)

        self.last_books_tab_index = self.library_tabs.currentIndex()

        self.main_tabs.setCurrentWidget(self.books_tab)

        QTimer.singleShot(200, self.ensure_grid_layout)

        self.statusBar.showMessage(f"Series: {series.name} ({len(series.books)} books)")

    def show_series_view(self):
        self.back_to_series_button.setVisible(False)
        self.current_series_label.setText("")

        self.in_series_filtered_mode = False

        self.statusBar.showMessage("Returning to series view...")

        self.main_tabs.setCurrentWidget(self.series_tab)

    def filter_by_series(self, series_id):
        if series_id in self.series_books_cache:
            books = self.series_books_cache[series_id]
        else:
            books = self.library_controller.get_all_books(series_id=series_id)
            self.series_books_cache[series_id] = books

        current_view = self.library_tabs.currentWidget()
        if current_view == self.grid_view:
            self.grid_view._clear_grid()
            self.grid_view._populate_grid(books)
        else:
            self.list_view.list_widget.clear()
            self.list_view._populate_list(books)
        QTimer.singleShot(100, self.ensure_correct_layout)

    def clear_series_filter(self):
        self.current_series_id = None
        self.needs_filter_clear = False

    def update_series_view_state(self):
        current_series_view = self.series_tabs.currentWidget()

        if current_series_view == self.series_grid_view:
            self.grid_view_action.setChecked(True)
            self.list_view_action.setChecked(False)
        else:
            self.grid_view_action.setChecked(False)
            self.list_view_action.setChecked(True)

    def show_series_editor(self, series_id=None):
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
                    self.series_grid_view.update_series_item(series_id)
                    self.series_list_view.update_series_item(series_id)

                    self.refresh_library()

                    self.statusBar.showMessage("Series updated successfully")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to open series editor: {e}"
                )

    def remove_series(self, series_id):
        series = self.library_controller.get_series(series_id)
        if not series:
            return

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

        for book in series.books:
            book.update_metadata(series_id=None, series_order=None)

        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM custom_metadata WHERE series_id = ?", (series_id,)
            )

            cursor.execute("DELETE FROM series WHERE id = ?", (series_id,))

            conn.commit()

            if series_id in self.series_books_cache:
                del self.series_books_cache[series_id]

            self.series_grid_view.refresh()
            self.series_list_view.refresh()

            if self.current_series_id == series_id:
                self.show_series_view()

            self.statusBar.showMessage(f"Series '{series.name}' removed")

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to remove series: {e}")

    def on_main_tab_changed(self, index):
        if index == 0:
            if not self.in_series_filtered_mode:
                self.statusBar.showMessage("Loading books view...")

                QTimer.singleShot(50, lambda: self._async_refresh_books_view())

                current_view = self.library_tabs.currentWidget()
                if current_view == self.grid_view:
                    QTimer.singleShot(100, self.grid_view.ensure_correct_layout)
        else:
            if not self.all_series:
                self.statusBar.showMessage("Loading series view...")

                QTimer.singleShot(50, lambda: self._async_load_all_series())

            current_view = self.series_tabs.currentWidget()
            if current_view == self.series_grid_view:
                QTimer.singleShot(100, self.series_grid_view.ensure_correct_layout)

    def on_library_tab_changed(self, index):
        self.last_books_tab_index = index

        if self.in_series_filtered_mode and self.current_series_id:
            self.apply_series_filter(self.current_series_id)

        current_view = self.library_tabs.currentWidget()
        if current_view == self.grid_view:
            QTimer.singleShot(50, self.grid_view.ensure_correct_layout)
        elif current_view == self.list_view:
            pass

    def load_all_series(self):
        self.all_series = self.library_controller.get_all_series()

        self.series_grid_view.refresh()
        self.series_list_view.refresh()

    def apply_series_filter(self, series_id):
        if series_id not in self.series_books_cache:
            books = self.library_controller.get_all_books(series_id=series_id)
            self.series_books_cache[series_id] = books
        else:
            books = self.series_books_cache[series_id]

        current_view = self.library_tabs.currentWidget()

        if current_view == self.grid_view:
            self.grid_view._clear_grid()
            self.grid_view._populate_grid(books)
        elif current_view == self.list_view:
            self.list_view.list_widget.clear()
            self.list_view._populate_list(books)

    def refresh_books_view(self):
        if self.in_series_filtered_mode and self.current_series_id:
            self.apply_series_filter(self.current_series_id)
        else:
            self.grid_view.refresh()
            self.list_view.refresh()

    def _async_refresh_books_view(self):
        self.refresh_books_view()

        self.statusBar.showMessage("Books view loaded")

    def _async_load_all_series(self):
        self.load_all_series()

        self.statusBar.showMessage("Series view loaded")

    def show_category_manager(self):
        try:
            from views.dialogs.category_manager import CategoryManager

            dialog = CategoryManager(self.library_controller, self)
            dialog.exec()

            self.populate_category_combo()

            self.update_category_filter_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open category manager: {e}")

    def update_category_filter_status(self):
        category_id = self.category_combo.currentData()
        category_name = self.category_combo.currentText()

        if category_id is None:
            self.statusBar.showMessage("Showing all categories")
        else:
            self.statusBar.showMessage(f"Filtered by category: {category_name}")

    def show_db_inspector(self):
        try:
            from views.dialogs.db_inspector import DatabaseInspector

            dialog = DatabaseInspector(self.db_manager, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open database inspector: {e}"
            )

    def on_splitter_moved(self, pos, index):
        self.left_panel_width = pos
        self.user_adjusted_splitter = True

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if (
            not hasattr(self, "user_adjusted_splitter")
            or not self.user_adjusted_splitter
        ):
            QTimer.singleShot(100, self.set_optimal_splitter_sizes)

    def ensure_grid_layout(self):
        current_view = self.library_tabs.currentWidget()
        if current_view == self.grid_view:
            self.grid_view.ensure_correct_layout()

    def filter_by_status(self, index):
        status = self.status_combo.itemData(index)

        self.grid_view.set_status_filter(status)
        self.list_view.set_status_filter(status)

        self.update_filter_status()

    def clear_status_filter(self):
        self.status_combo.setCurrentIndex(0)

    def update_filter_status(self):
        category_id = self.category_combo.currentData()
        category_name = self.category_combo.currentText()

        status_id = self.status_combo.currentData()
        status_name = self.status_combo.currentText()

        filter_msg = []

        if category_id is not None:
            filter_msg.append(f"Category: {category_name}")

        if status_id is not None:
            filter_msg.append(f"Status: {status_name}")

        if filter_msg:
            self.statusBar.showMessage(f"Filtered by {' and '.join(filter_msg)}")
        else:
            self.statusBar.showMessage("Showing all books")

    def save_window_state(self):
        settings = QSettings("YourOrg", "PDFLibraryManager")

        settings.setValue("window/geometry", self.saveGeometry())
        settings.setValue("window/size", self.size())
        settings.setValue("window/pos", self.pos())

        settings.setValue("window/state", self.saveState())

        settings.setValue("splitter/sizes", self.main_splitter.sizes())

        settings.setValue("ui/main_tab_index", self.main_tabs.currentIndex())
        settings.setValue("ui/library_tab_index", self.library_tabs.currentIndex())
        settings.setValue("ui/series_tab_index", self.series_tabs.currentIndex())

        settings.setValue("filters/category_index", self.category_combo.currentIndex())
        settings.setValue("filters/status_index", self.status_combo.currentIndex())
        settings.setValue("filters/search_text", self.search_box.text())

        if self.current_series_id:
            settings.setValue("state/current_series_id", self.current_series_id)

        current_book_id = self.reader_view.current_book_id
        if current_book_id:
            settings.setValue("state/current_book_id", current_book_id)

    def restore_window_state(self):
        settings = QSettings("YourOrg", "PDFLibraryManager")

        geometry = settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

        size = settings.value("window/size")
        pos = settings.value("window/pos")

        if size and pos:
            try:
                if isinstance(size, str):
                    width, height = map(int, size.strip("()").split(","))
                    self.resize(width, height)
                else:
                    self.resize(size)

                if isinstance(pos, str):
                    x, y = map(int, pos.strip("()").split(","))
                    self.move(x, y)
                else:
                    self.move(pos)
            except (ValueError, TypeError):
                print("Failed to restore window size/position, using defaults")

        state = settings.value("window/state")
        if state:
            self.restoreState(state)

        splitter_sizes = settings.value("splitter/sizes")
        if splitter_sizes:
            try:
                int_sizes = [int(size) for size in splitter_sizes]
                self.main_splitter.setSizes(int_sizes)
            except (TypeError, ValueError):
                print("Failed to convert splitter sizes to integers")

        self.pending_ui_restore = {
            "main_tab_index": settings.value("ui/main_tab_index", 0, int),
            "library_tab_index": settings.value("ui/library_tab_index", 0, int),
            "series_tab_index": settings.value("ui/series_tab_index", 0, int),
            "category_index": settings.value("filters/category_index", 0, int),
            "status_index": settings.value("filters/status_index", 0, int),
            "search_text": settings.value("filters/search_text", ""),
            "current_series_id": settings.value("state/current_series_id"),
            "current_book_id": settings.value("state/current_book_id"),
        }

        QTimer.singleShot(500, self.complete_state_restoration)

    def complete_state_restoration(self):
        if not hasattr(self, "pending_ui_restore") or self.loading:
            QTimer.singleShot(500, self.complete_state_restoration)
            return

        self.main_tabs.setCurrentIndex(self.pending_ui_restore["main_tab_index"])
        self.library_tabs.setCurrentIndex(self.pending_ui_restore["library_tab_index"])
        self.series_tabs.setCurrentIndex(self.pending_ui_restore["series_tab_index"])

        self.category_combo.setCurrentIndex(self.pending_ui_restore["category_index"])
        self.status_combo.setCurrentIndex(self.pending_ui_restore["status_index"])

        search_text = self.pending_ui_restore["search_text"]
        if search_text:
            self.search_box.setText(search_text)
            self.search_books()

        current_series_id = self.pending_ui_restore.get("current_series_id")
        if current_series_id:
            self.restore_series_selection(current_series_id)

        current_book_id = self.pending_ui_restore.get("current_book_id")
        if current_book_id:
            self.restore_book_selection(current_book_id)

        del self.pending_ui_restore

    def restore_series_selection(self, series_id):
        if self.main_tabs.currentIndex() == 1:
            if self.series_tabs.currentIndex() == 0:
                self.series_grid_view.select_series(series_id, emit_signal=False)
            else:
                self.series_list_view.select_series(series_id, emit_signal=False)

    def restore_book_selection(self, book_id):
        if self.main_tabs.currentIndex() == 0:
            if self.library_tabs.currentIndex() == 0:
                self.grid_view.select_book(book_id, emit_signal=False)
            else:
                self.list_view.select_book(book_id, emit_signal=False)

            QTimer.singleShot(100, lambda: self.reader_view.load_book(book_id))
