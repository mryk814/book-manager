import logging
import os
import sys

from PyQt6.QtCore import QMutex, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class ScanWorker(QThread):
    """ライブラリスキャンを行うワーカースレッド"""

    progress_signal = pyqtSignal(float, str, int, int)
    finished_signal = pyqtSignal(dict)

    def __init__(self, library_manager, directory=None):
        super().__init__()
        self.library_manager = library_manager
        self.directory = directory
        self.mutex = QMutex()

    def run(self):
        self.mutex.lock()
        try:
            if self.directory:
                result = self.library_manager.scan_directory(
                    self.directory, self.progress_callback
                )
            else:
                result = self.library_manager.scan_all_libraries(self.progress_callback)
            self.finished_signal.emit(result)
        finally:
            self.mutex.unlock()

    def progress_callback(self, progress, message, total, current):
        self.progress_signal.emit(progress, message, total, current)


class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ"""

    def __init__(self, library_manager, config):
        super().__init__()
        self.library_manager = library_manager
        self.config = config
        self.scan_worker = None

        # ウィンドウの設定
        self.setWindowTitle(config.get("app_name", "PDF Library"))
        self.setMinimumSize(1000, 700)

        # UI設定の読み込み
        self.ui_settings = config.get("ui", {})
        self.viewer_settings = config.get("viewer", {})

        # UIの初期化
        self._init_ui()

        # 自動スキャンの設定
        if config.get("scan_options.scan_on_startup", True):
            self._scan_libraries()

    def _init_ui(self):
        """UIの初期化"""
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # メニューバーの作成
        self._create_menu_bar()

        # ツールバーの作成
        self._create_tool_bar()

        # メインコンテンツの作成
        self._create_main_content(main_layout)

        # ステータスバーの作成
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

    def _create_menu_bar(self):
        """メニューバーの作成"""
        menu_bar = self.menuBar()

        # ファイルメニュー
        file_menu = menu_bar.addMenu("ファイル")

        # PDFのインポート
        import_action = QAction("PDFをインポート...", self)
        import_action.triggered.connect(self._import_pdf_files)
        file_menu.addAction(import_action)

        # ディレクトリのスキャン
        scan_dir_action = QAction("ディレクトリをスキャン...", self)
        scan_dir_action.triggered.connect(self._scan_directory)
        file_menu.addAction(scan_dir_action)

        # 全ライブラリのスキャン
        scan_all_action = QAction("全ライブラリをスキャン", self)
        scan_all_action.triggered.connect(self._scan_libraries)
        file_menu.addAction(scan_all_action)

        file_menu.addSeparator()

        # ライブラリパスの設定
        lib_path_action = QAction("ライブラリパスの設定...", self)
        lib_path_action.triggered.connect(self._configure_library_paths)
        file_menu.addAction(lib_path_action)

        # 設定
        settings_action = QAction("設定...", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 編集メニュー
        edit_menu = menu_bar.addMenu("編集")

        # タグ管理
        tags_action = QAction("タグ管理...", self)
        tags_action.triggered.connect(self._manage_tags)
        edit_menu.addAction(tags_action)

        # シリーズ管理
        series_action = QAction("シリーズ管理...", self)
        series_action.triggered.connect(self._manage_series)
        edit_menu.addAction(series_action)

        # カテゴリ管理
        category_action = QAction("カテゴリ管理...", self)
        category_action.triggered.connect(self._manage_categories)
        edit_menu.addAction(category_action)

        # 表示メニュー
        view_menu = menu_bar.addMenu("表示")

        # 表示モード
        view_mode_menu = QMenu("表示モード", self)

        grid_view_action = QAction("グリッド表示", self)
        grid_view_action.setCheckable(True)
        grid_view_action.setChecked(self.ui_settings.get("default_view") == "grid")
        grid_view_action.triggered.connect(lambda: self._change_view_mode("grid"))
        view_mode_menu.addAction(grid_view_action)

        list_view_action = QAction("リスト表示", self)
        list_view_action.setCheckable(True)
        list_view_action.setChecked(self.ui_settings.get("default_view") == "list")
        list_view_action.triggered.connect(lambda: self._change_view_mode("list"))
        view_mode_menu.addAction(list_view_action)

        bookshelf_view_action = QAction("本棚表示", self)
        bookshelf_view_action.setCheckable(True)
        bookshelf_view_action.setChecked(
            self.ui_settings.get("default_view") == "bookshelf"
        )
        bookshelf_view_action.triggered.connect(
            lambda: self._change_view_mode("bookshelf")
        )
        view_mode_menu.addAction(bookshelf_view_action)

        view_menu.addMenu(view_mode_menu)

        # ソート
        sort_menu = QMenu("ソート", self)

        sort_title_action = QAction("タイトル", self)
        sort_title_action.triggered.connect(lambda: self._change_sort("title"))
        sort_menu.addAction(sort_title_action)

        sort_author_action = QAction("著者", self)
        sort_author_action.triggered.connect(lambda: self._change_sort("author"))
        sort_menu.addAction(sort_author_action)

        sort_date_added_action = QAction("追加日", self)
        sort_date_added_action.triggered.connect(
            lambda: self._change_sort("date_added")
        )
        sort_menu.addAction(sort_date_added_action)

        sort_last_read_action = QAction("最終閲覧日", self)
        sort_last_read_action.triggered.connect(lambda: self._change_sort("last_read"))
        sort_menu.addAction(sort_last_read_action)

        view_menu.addMenu(sort_menu)

        # ヘルプメニュー
        help_menu = menu_bar.addMenu("ヘルプ")

        about_action = QAction("このアプリについて", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_tool_bar(self):
        """ツールバーの作成"""
        tool_bar = QToolBar("メインツールバー")
        tool_bar.setIconSize(QSize(24, 24))
        self.addToolBar(tool_bar)

        # インポートボタン
        import_action = QAction("インポート", self)
        import_action.triggered.connect(self._import_pdf_files)
        tool_bar.addAction(import_action)

        # スキャンボタン
        scan_action = QAction("スキャン", self)
        scan_action.triggered.connect(self._scan_libraries)
        tool_bar.addAction(scan_action)

        tool_bar.addSeparator()

        # 表示モード選択
        view_mode_label = QLabel("表示: ")
        tool_bar.addWidget(view_mode_label)

        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["グリッド", "リスト", "本棚"])

        # デフォルト表示モードの設定
        default_view = self.ui_settings.get("default_view", "grid")
        if default_view == "grid":
            self.view_mode_combo.setCurrentIndex(0)
        elif default_view == "list":
            self.view_mode_combo.setCurrentIndex(1)
        elif default_view == "bookshelf":
            self.view_mode_combo.setCurrentIndex(2)

        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        tool_bar.addWidget(self.view_mode_combo)

        tool_bar.addSeparator()

        # 検索ボックス
        search_label = QLabel("検索: ")
        tool_bar.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("タイトル、著者、タグで検索...")
        self.search_box.setMinimumWidth(200)
        self.search_box.returnPressed.connect(self._on_search)
        tool_bar.addWidget(self.search_box)

        # 検索ボタン
        search_button = QPushButton("検索")
        search_button.clicked.connect(self._on_search)
        tool_bar.addWidget(search_button)

        # クリアボタン
        clear_button = QPushButton("クリア")
        clear_button.clicked.connect(self._clear_search)
        tool_bar.addWidget(clear_button)

    def _create_main_content(self, main_layout):
        """メインコンテンツの作成"""
        # スプリッタの作成
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # 左側のカテゴリツリー
        self.category_tree = QTreeView()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setMinimumWidth(200)
        self.category_model = QStandardItemModel()
        self.category_tree.setModel(self.category_model)
        self._init_category_tree()
        self.splitter.addWidget(self.category_tree)

        # 右側のタブウィジェット
        self.content_tabs = QTabWidget()
        self.splitter.addWidget(self.content_tabs)

        # スプリッタの初期サイズ
        self.splitter.setSizes([200, 800])

        # ライブラリビュータブの追加
        # ここでは具体的な実装は省略し、後でライブラリビュークラスを実装
        self.library_view_tab = QWidget()
        self.content_tabs.addTab(self.library_view_tab, "ライブラリ")

        # その他のタブも必要に応じて追加

    def _init_category_tree(self):
        """カテゴリツリーの初期化"""
        self.category_model.clear()

        # ルートアイテム
        root = self.category_model.invisibleRootItem()

        # ライブラリアイテム
        library_item = QStandardItem("ライブラリ")
        root.appendRow(library_item)

        # すべて
        all_books_item = QStandardItem("すべての書籍")
        library_item.appendRow(all_books_item)

        # 最近追加
        recent_item = QStandardItem("最近追加")
        library_item.appendRow(recent_item)

        # 読書状態
        reading_status_item = QStandardItem("読書状態")
        library_item.appendRow(reading_status_item)

        unread_item = QStandardItem("未読")
        reading_status_item.appendRow(unread_item)

        reading_item = QStandardItem("読書中")
        reading_status_item.appendRow(reading_item)

        completed_item = QStandardItem("読了")
        reading_status_item.appendRow(completed_item)

        # お気に入り
        favorites_item = QStandardItem("お気に入り")
        library_item.appendRow(favorites_item)

        # シリーズ
        series_item = QStandardItem("シリーズ")
        root.appendRow(series_item)

        # シリーズの読み込み（後でデータベースから取得）

        # タグ
        tags_item = QStandardItem("タグ")
        root.appendRow(tags_item)

        # タグの読み込み（後でデータベースから取得）

        # カテゴリ
        categories_item = QStandardItem("カテゴリ")
        root.appendRow(categories_item)

        # カテゴリの読み込み（後でデータベースから取得）

        # 初期展開
        self.category_tree.expandAll()

    def _update_category_tree(self):
        """カテゴリツリーを更新"""
        # ここではシリーズ、タグ、カテゴリをデータベースから取得して更新
        # 具体的な実装は省略
        pass

    def _import_pdf_files(self):
        """PDFファイルをインポート"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "PDFファイルのインポート", "", "PDFファイル (*.pdf)"
        )

        if not files:
            return

        progress = QProgressDialog(
            "PDFをインポートしています...", "キャンセル", 0, len(files), self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        imported = 0
        for i, file_path in enumerate(files):
            progress.setValue(i)
            progress.setLabelText(f"インポート中: {os.path.basename(file_path)}")

            if progress.wasCanceled():
                break

            if self.library_manager.import_file(file_path):
                imported += 1

        progress.setValue(len(files))

        QMessageBox.information(
            self, "インポート完了", f"{imported}ファイルをインポートしました。"
        )

        # ビューを更新（後で実装）
        self._update_views()

    def _scan_directory(self):
        """ディレクトリをスキャン"""
        directory = QFileDialog.getExistingDirectory(
            self, "スキャンするディレクトリを選択", ""
        )

        if not directory:
            return

        self._start_scan_worker(directory)

    def _scan_libraries(self):
        """全ライブラリをスキャン"""
        self._start_scan_worker()

    def _start_scan_worker(self, directory=None):
        """スキャンワーカーを開始"""
        if self.scan_worker and self.scan_worker.isRunning():
            QMessageBox.warning(self, "スキャン中", "すでにスキャンが実行中です。")
            return

        # プログレスダイアログの作成
        self.scan_progress = QProgressDialog(
            "ライブラリをスキャンしています...", "キャンセル", 0, 100, self
        )
        self.scan_progress.setWindowTitle("スキャン中")
        self.scan_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.scan_progress.setMinimumDuration(0)
        self.scan_progress.setValue(0)
        self.scan_progress.show()

        # ワーカーの作成と開始
        self.scan_worker = ScanWorker(self.library_manager, directory)
        self.scan_worker.progress_signal.connect(self._update_scan_progress)
        self.scan_worker.finished_signal.connect(self._scan_finished)
        self.scan_worker.start()

    def _update_scan_progress(self, progress, message, total, current):
        """スキャン進捗の更新"""
        if self.scan_progress and not self.scan_progress.wasCanceled():
            try:
                self.scan_progress.setValue(int(progress))
                self.scan_progress.setLabelText(
                    f"スキャン中 ({current}/{total}): {message}"
                )

                if self.scan_progress.wasCanceled():
                    # キャンセル処理（現在のスレッドは終了する必要がある）
                    if self.scan_worker and self.scan_worker.isRunning():
                        self.scan_worker.terminate()
                    self.scan_worker = None
                    self.scan_progress = None
            except Exception as e:
                # 進捗ダイアログが既に閉じられている可能性がある
                print(f"進捗更新エラー: {e}")
                self.scan_progress = None

    def _scan_finished(self, result):
        """スキャン完了時の処理"""
        if self.scan_progress:
            self.scan_progress.setValue(100)
            self.scan_progress.close()
            self.scan_progress = None

        # 結果の表示
        QMessageBox.information(
            self,
            "スキャン完了",
            f"スキャン結果:\n"
            + f"- 追加: {result['added']}書籍\n"
            + f"- スキップ: {result['skipped']}書籍\n"
            + f"- 失敗: {result['failed']}書籍",
        )

        # ビューの更新
        self._update_views()

    def _configure_library_paths(self):
        """ライブラリパスの設定"""
        from book_manager.gui.dialogs.library_paths_dialog import LibraryPathsDialog

        dialog = LibraryPathsDialog(self.config, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # パスが変更された場合、ライブラリを再スキャンするか尋ねる
            reply = QMessageBox.question(
                self,
                "ライブラリのスキャン",
                "ライブラリパスが変更されました。今すぐライブラリをスキャンしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._scan_libraries()

    def _open_settings(self):
        """設定ダイアログを開く"""
        from book_manager.gui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 設定が変更された場合、UIを更新
            self._update_ui_from_settings()

            # ライブラリビューの更新
            self._update_views()

    def _update_ui_from_settings(self):
        """設定に基づいてUIを更新"""
        # ウィンドウタイトルの更新
        self.setWindowTitle(self.config.get("app_name", "PDF Library"))

        # テーマの更新
        theme = self.config.get("ui.theme", "light")
        self._apply_theme(theme)

        # 表示モードの更新
        default_view = self.config.get("ui.default_view", "grid")
        view_index = 0
        if default_view == "grid":
            view_index = 0
        elif default_view == "list":
            view_index = 1
        elif default_view == "bookshelf":
            view_index = 2

        # コンボボックスを更新（シグナルの発生を防ぐためブロック）
        self.view_mode_combo.blockSignals(True)
        self.view_mode_combo.setCurrentIndex(view_index)
        self.view_mode_combo.blockSignals(False)

        # アクションの更新
        for i, mode in enumerate(["grid", "list", "bookshelf"]):
            action = None
            if mode == "grid":
                action = self.findChild(QAction, "grid_view_action")
            elif mode == "list":
                action = self.findChild(QAction, "list_view_action")
            elif mode == "bookshelf":
                action = self.findChild(QAction, "bookshelf_view_action")

            if action:
                action.setChecked(default_view == mode)

    def _manage_tags(self):
        """タグ管理ダイアログを開く"""
        from book_manager.gui.dialogs.tag_dialog import TagDialog

        dialog = TagDialog(self.library_manager.db, self)
        dialog.exec()

        # 必要に応じてビューを更新
        self._update_views()

    def _manage_series(self):
        """シリーズ管理ダイアログを開く"""
        from book_manager.gui.dialogs.series_dialog import SeriesDialog

        dialog = SeriesDialog(self.library_manager.db, self)
        dialog.exec()

        # 必要に応じてビューを更新
        self._update_views()

    def _manage_categories(self):
        """カテゴリ管理ダイアログを開く"""
        from book_manager.gui.dialogs.category_dialog import CategoryDialog

        dialog = CategoryDialog(self.library_manager.db, self)
        dialog.exec()

        # 必要に応じてビューを更新
        self._update_views()

    def _change_view_mode(self, mode):
        """表示モードの変更"""
        index = 0
        if mode == "list":
            index = 1
        elif mode == "bookshelf":
            index = 2

        self.view_mode_combo.setCurrentIndex(index)

    def _on_view_mode_changed(self, index):
        """表示モード変更時の処理"""
        modes = ["grid", "list", "bookshelf"]
        if index < len(modes):
            mode = modes[index]
            self.config.set("ui.default_view", mode)

            # ビューの更新（後で実装）
            self._update_views()

    def _change_sort(self, field):
        """ソートフィールドの変更"""
        # ソート方向の切り替え
        current_field = self.config.get("ui.sort_field", "title")
        current_dir = self.config.get("ui.sort_direction", "asc")

        if current_field == field:
            # 同じフィールドの場合は方向を切り替え
            new_dir = "desc" if current_dir == "asc" else "asc"
            self.config.set("ui.sort_direction", new_dir)
        else:
            # 異なるフィールドの場合は昇順から
            self.config.set("ui.sort_field", field)
            self.config.set("ui.sort_direction", "asc")

        # ビューの更新（後で実装）
        self._update_views()

    def _on_search(self):
        """検索実行"""
        search_term = self.search_box.text().strip()
        if not search_term:
            return

        # 検索の実行（後で実装）
        self._search_books(search_term)

    def _clear_search(self):
        """検索クリア"""
        self.search_box.clear()

        # ビューの更新（後で実装）
        self._update_views()

    def _search_books(self, search_term):
        """書籍を検索"""
        from gui.library_view import LibraryView

        if not search_term.strip():
            # 空の検索語の場合は全ての書籍を表示
            self._update_views()
            return

        # ライブラリビューの取得
        library_view = self.findChild(LibraryView)
        if library_view:
            # 検索を実行
            count = library_view.search(search_term)
            self.status_bar.showMessage(f'検索結果: {count}件 - "{search_term}"')

    def _update_views(self):
        """ビューの更新"""
        # カテゴリツリーの更新
        self._update_category_tree()

        # ライブラリビューの更新（後で実装）
        pass

    def _show_about(self):
        """このアプリについてダイアログを表示"""
        QMessageBox.about(
            self,
            "このアプリについて",
            f"{self.config.get('app_name', 'PDF Library')} v{self.config.get('version', '1.0.0')}\n\n"
            "PDFライブラリ管理アプリケーション",
        )

    def closeEvent(self, event):
        """ウィンドウが閉じられる前の処理"""
        # ワーカースレッドが動いている場合は終了
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.terminate()
            self.scan_worker.wait()

        # 設定の保存
        # その他のクリーンアップ

        event.accept()

    def _configure_library_paths(self):
        """ライブラリパスの設定"""
        from gui.dialogs.library_paths_dialog import LibraryPathsDialog

        dialog = LibraryPathsDialog(self.config, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # パスが変更された場合、ライブラリを再スキャンするか尋ねる
            reply = QMessageBox.question(
                self,
                "ライブラリのスキャン",
                "ライブラリパスが変更されました。今すぐライブラリをスキャンしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._scan_libraries()

    def _apply_theme(self, theme):
        """テーマを適用"""
        if theme == "dark":
            # ダークテーマの適用
            style_sheet = """
            QWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QMenuBar, QMenu {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QToolBar {
                background-color: #2D2D30;
                border-bottom: 1px solid #3F3F46;
            }
            QStatusBar {
                background-color: #007ACC;
                color: #FFFFFF;
            }
            QLineEdit, QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
            }
            QPushButton {
                background-color: #0E639C;
                color: #FFFFFF;
                border: 1px solid #0E639C;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #0D5789;
            }
            QTabWidget::pane {
                border: 1px solid #3F3F46;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #FFFFFF;
                padding: 6px 10px;
                border: 1px solid #3F3F46;
            }
            QTabBar::tab:selected {
                background-color: #007ACC;
            }
            QTableView, QListView, QTreeView {
                background-color: #1E1E1E;
                color: #FFFFFF;
                alternate-background-color: #2D2D30;
                border: 1px solid #3F3F46;
            }
            QHeaderView::section {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
            }
            """
            self.setStyleSheet(style_sheet)
        else:
            # ライトテーマ（デフォルト）
            self.setStyleSheet("")
