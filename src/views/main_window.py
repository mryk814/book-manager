import os
import sys

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from controllers.library_controller import LibraryController
from models.database import DatabaseManager
from views.dialogs.import_dialog import ImportDialog
from views.dialogs.settings_dialog import SettingsDialog
from views.library_view import LibraryGridView, LibraryListView
from views.metadata_editor import MetadataEditor
from views.reader_view import PDFReaderView


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
        # タブウィジェットを作成
        self.library_tabs = QTabWidget()
        self.library_layout.addWidget(self.library_tabs)

        # グリッドビュータブ
        self.grid_view = LibraryGridView(self.library_controller)
        self.library_tabs.addTab(self.grid_view, "Grid View")

        # リストビュータブ
        self.list_view = LibraryListView(self.library_controller)
        self.library_tabs.addTab(self.list_view, "List View")

        # タブの変更をツールバーコンボボックスと同期
        self.library_tabs.currentChanged.connect(
            lambda idx: self.view_type_combo.setCurrentIndex(idx)
        )

    def setup_reader_panel(self):
        """リーダーパネルを設定する。"""
        # PDF表示用ウィジェット
        self.reader_view = PDFReaderView(self.library_controller)
        self.reader_layout.addWidget(self.reader_view)

    def setup_context_menu_handlers(self):
        """コンテキストメニュー機能のハンドラを設定する。"""
        # グリッドビューのコンテキストメニューハンドラ
        self.grid_view._edit_metadata = self.show_metadata_editor
        self.grid_view._add_to_series = self.show_add_to_series_dialog
        self.grid_view._remove_book = self.remove_book

        # リストビューのコンテキストメニューハンドラ
        self.list_view._edit_metadata = self.show_metadata_editor
        self.list_view._add_to_series = self.show_add_to_series_dialog
        self.list_view._remove_book = self.remove_book

    def setup_connections(self):
        """シグナルとスロットを接続する。"""
        # グリッドビューからの選択シグナル
        self.grid_view.book_selected.connect(self.on_book_selected)

        # リストビューからの選択シグナル
        self.list_view.book_selected.connect(self.on_book_selected)

        # リーダービューからの進捗更新シグナル
        self.reader_view.progress_updated.connect(self.on_progress_updated)

    def setup_context_menu_handlers(self):
        """コンテキストメニュー機能のハンドラを設定する。"""
        # グリッドビューのコンテキストメニューハンドラ
        self.grid_view._edit_metadata = self.show_metadata_editor
        self.grid_view._add_to_series = self.show_add_to_series_dialog
        self.grid_view._remove_book = self.remove_book

        # リストビューのコンテキストメニューハンドラ
        self.list_view._edit_metadata = self.show_metadata_editor
        self.list_view._add_to_series = self.show_add_to_series_dialog
        self.list_view._remove_book = self.remove_book

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
        self.library_tabs.setCurrentIndex(index)

        # メニューの選択状態も更新
        self.grid_view_action.setChecked(index == 0)
        self.list_view_action.setChecked(index == 1)

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
            # 書籍を削除
            success = self.library_controller.remove_book(book_id, delete_file=False)

            if success:
                # 現在開いている書籍がこれなら閉じる
                if self.reader_view.current_book_id == book_id:
                    self.reader_view.close_current_book()

                # ライブラリを更新
                self.refresh_library()
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
        self.grid_view.refresh()
        self.list_view.refresh()
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
