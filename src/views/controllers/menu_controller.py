# src/views/controllers/menu_controller.py
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMenuBar, QToolBar


class MenuController:
    """
    メニューとツールバーを管理するコントローラクラス。

    メインウィンドウのメニュー項目とツールバーの初期化と
    操作を一元管理する。

    Parameters
    ----------
    main_window : MainWindow
        親となるメインウィンドウ
    library_controller : LibraryController
        ライブラリコントローラ
    """

    def __init__(self, main_window, library_controller):
        """
        Parameters
        ----------
        main_window : MainWindow
            親となるメインウィンドウ
        library_controller : LibraryController
            ライブラリコントローラ
        """
        self.main_window = main_window
        self.library_controller = library_controller
        self.actions = {}

        # メニューバーとツールバーの初期化
        self.menu_bar = main_window.menuBar()
        self.toolbar = QToolBar("Main Toolbar")
        main_window.addToolBar(self.toolbar)

        # 各種メニューの作成
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_tools_menu()
        self._create_help_menu()

        # ツールバーの設定
        self._setup_toolbar()

    def _create_file_menu(self):
        """ファイルメニューを作成する"""
        file_menu = self.menu_bar.addMenu("&File")

        # インポートアクション
        import_action = QAction("&Import PDF...", self.main_window)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("Import PDF files to the library")
        import_action.triggered.connect(self.main_window.on_import_pdf)
        file_menu.addAction(import_action)
        self.actions["import"] = import_action

        # バッチインポートアクション
        batch_import_action = QAction("Batch Import...", self.main_window)
        batch_import_action.setStatusTip("Import multiple PDF files at once")
        batch_import_action.triggered.connect(self.main_window.on_batch_import)
        file_menu.addAction(batch_import_action)
        self.actions["batch_import"] = batch_import_action

        file_menu.addSeparator()

        # 終了アクション
        exit_action = QAction("E&xit", self.main_window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)
        self.actions["exit"] = exit_action

    def _create_edit_menu(self):
        """編集メニューを作成する"""
        edit_menu = self.menu_bar.addMenu("&Edit")

        # カテゴリ管理アクション
        manage_categories_action = QAction("Manage &Categories...", self.main_window)
        manage_categories_action.setStatusTip("Manage book categories")
        manage_categories_action.triggered.connect(
            self.main_window.on_manage_categories
        )
        edit_menu.addAction(manage_categories_action)
        self.actions["manage_categories"] = manage_categories_action

        # シリーズ管理アクション
        manage_series_action = QAction("Manage &Series...", self.main_window)
        manage_series_action.setStatusTip("Manage book series")
        manage_series_action.triggered.connect(self.main_window.on_manage_series)
        edit_menu.addAction(manage_series_action)
        self.actions["manage_series"] = manage_series_action

        edit_menu.addSeparator()

        # 設定アクション
        preferences_action = QAction("&Preferences...", self.main_window)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.setStatusTip("Application settings")
        preferences_action.triggered.connect(self.main_window.on_preferences)
        edit_menu.addAction(preferences_action)
        self.actions["preferences"] = preferences_action

    def _create_view_menu(self):
        """表示メニューを作成する"""
        view_menu = self.menu_bar.addMenu("&View")

        # グリッド表示アクション
        grid_view_action = QAction("&Grid View", self.main_window)
        grid_view_action.setShortcut("Ctrl+G")
        grid_view_action.setStatusTip("Switch to grid view")
        grid_view_action.setCheckable(True)
        grid_view_action.triggered.connect(
            lambda: self.main_window.on_switch_view("grid")
        )
        view_menu.addAction(grid_view_action)
        self.actions["grid_view"] = grid_view_action

        # リスト表示アクション
        list_view_action = QAction("&List View", self.main_window)
        list_view_action.setShortcut("Ctrl+L")
        list_view_action.setStatusTip("Switch to list view")
        list_view_action.setCheckable(True)
        list_view_action.triggered.connect(
            lambda: self.main_window.on_switch_view("list")
        )
        view_menu.addAction(list_view_action)
        self.actions["list_view"] = list_view_action

        view_menu.addSeparator()

        # ステータスフィルタサブメニュー
        status_menu = QMenu("Filter by Status", self.main_window)

        # すべて表示
        all_status_action = QAction("All Books", self.main_window)
        all_status_action.setCheckable(True)
        all_status_action.setChecked(True)
        all_status_action.triggered.connect(
            lambda: self.main_window.on_filter_by_status(None)
        )
        status_menu.addAction(all_status_action)
        self.actions["filter_all"] = all_status_action

        # 未読のみ
        unread_action = QAction("Unread Only", self.main_window)
        unread_action.setCheckable(True)
        unread_action.triggered.connect(
            lambda: self.main_window.on_filter_by_status("unread")
        )
        status_menu.addAction(unread_action)
        self.actions["filter_unread"] = unread_action

        # 読書中のみ
        reading_action = QAction("Reading Only", self.main_window)
        reading_action.setCheckable(True)
        reading_action.triggered.connect(
            lambda: self.main_window.on_filter_by_status("reading")
        )
        status_menu.addAction(reading_action)
        self.actions["filter_reading"] = reading_action

        # 完了のみ
        completed_action = QAction("Completed Only", self.main_window)
        completed_action.setCheckable(True)
        completed_action.triggered.connect(
            lambda: self.main_window.on_filter_by_status("completed")
        )
        status_menu.addAction(completed_action)
        self.actions["filter_completed"] = completed_action

        view_menu.addMenu(status_menu)

    def _create_tools_menu(self):
        """ツールメニューを作成する"""
        tools_menu = self.menu_bar.addMenu("&Tools")

        # 検索アクション
        search_action = QAction("&Search...", self.main_window)
        search_action.setShortcut("Ctrl+F")
        search_action.setStatusTip("Search books")
        search_action.triggered.connect(self.main_window.on_search)
        tools_menu.addAction(search_action)
        self.actions["search"] = search_action

        # 高度な検索アクション
        advanced_search_action = QAction("&Advanced Search...", self.main_window)
        advanced_search_action.setShortcut("Ctrl+Shift+F")
        advanced_search_action.setStatusTip("Advanced search with multiple criteria")
        advanced_search_action.triggered.connect(self.main_window.on_advanced_search)
        tools_menu.addAction(advanced_search_action)
        self.actions["advanced_search"] = advanced_search_action

        tools_menu.addSeparator()

        # バッチ処理アクション
        batch_action = QAction("Batch Operations...", self.main_window)
        batch_action.setStatusTip("Perform operations on multiple books")
        batch_action.triggered.connect(self.main_window.on_batch_operations)
        tools_menu.addAction(batch_action)
        self.actions["batch_operations"] = batch_action

    def _create_help_menu(self):
        """ヘルプメニューを作成する"""
        help_menu = self.menu_bar.addMenu("&Help")

        # ヘルプアクション
        help_action = QAction("&Help Contents", self.main_window)
        help_action.setShortcut("F1")
        help_action.setStatusTip("Show the application's help")
        help_action.triggered.connect(self.main_window.on_help)
        help_menu.addAction(help_action)
        self.actions["help"] = help_action

        # アバウトアクション
        about_action = QAction("&About", self.main_window)
        about_action.setStatusTip("Show the application's About box")
        about_action.triggered.connect(self.main_window.on_about)
        help_menu.addAction(about_action)
        self.actions["about"] = about_action

    def _setup_toolbar(self):
        """ツールバーを設定する"""
        # インポートボタン
        self.toolbar.addAction(self.actions["import"])

        # 検索ボタン
        self.toolbar.addAction(self.actions["search"])

        self.toolbar.addSeparator()

        # 表示切替ボタン
        self.toolbar.addAction(self.actions["grid_view"])
        self.toolbar.addAction(self.actions["list_view"])

        # ステータスによるフィルタリングボタン
        self.toolbar.addSeparator()

        # 設定ボタン
        self.toolbar.addAction(self.actions["preferences"])

    def set_view_mode(self, mode):
        """
        表示モードを設定する

        Parameters
        ----------
        mode : str
            'grid'または'list'
        """
        self.actions["grid_view"].setChecked(mode == "grid")
        self.actions["list_view"].setChecked(mode == "list")

    def set_status_filter(self, status):
        """
        ステータスフィルタを設定する

        Parameters
        ----------
        status : str または None
            'unread', 'reading', 'completed'のいずれか、またはNone（すべて表示）
        """
        self.actions["filter_all"].setChecked(status is None)
        self.actions["filter_unread"].setChecked(status == "unread")
        self.actions["filter_reading"].setChecked(status == "reading")
        self.actions["filter_completed"].setChecked(status == "completed")
