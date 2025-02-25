import logging
import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """設定ダイアログ"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.original_settings = {}
        self.current_settings = {}

        self._load_settings()
        self._init_ui()
        self._populate_ui()

    def _load_settings(self):
        """設定を読み込む"""
        # 設定を複製して保持
        self.original_settings = self.config.settings.copy()
        self.current_settings = self.config.settings.copy()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("設定")
        self.resize(600, 450)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # タブウィジェット
        self.tab_widget = QTabWidget()

        # 一般設定タブ
        general_tab = self._create_general_tab()
        self.tab_widget.addTab(general_tab, "一般")

        # 表示設定タブ
        display_tab = self._create_display_tab()
        self.tab_widget.addTab(display_tab, "表示")

        # PDFビューア設定タブ
        viewer_tab = self._create_viewer_tab()
        self.tab_widget.addTab(viewer_tab, "PDFビューア")

        # スキャン設定タブ
        scan_tab = self._create_scan_tab()
        self.tab_widget.addTab(scan_tab, "スキャン")

        layout.addWidget(self.tab_widget)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._apply_settings
        )
        layout.addWidget(button_box)

    def _create_general_tab(self):
        """一般設定タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # アプリケーション情報
        app_group = QGroupBox("アプリケーション情報")
        app_layout = QFormLayout(app_group)

        # アプリケーション名
        self.app_name_edit = QLineEdit()
        app_layout.addRow("アプリケーション名:", self.app_name_edit)

        layout.addWidget(app_group)

        # データベース設定
        db_group = QGroupBox("データベース設定")
        db_layout = QFormLayout(db_group)

        # データベースパス
        db_path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        db_path_layout.addWidget(self.db_path_edit)

        browse_db_button = QPushButton("参照...")
        browse_db_button.clicked.connect(self._browse_db_path)
        db_path_layout.addWidget(browse_db_button)

        db_layout.addRow("データベースパス:", db_path_layout)

        layout.addWidget(db_group)

        # サムネイル設定
        thumbnail_group = QGroupBox("サムネイル設定")
        thumbnail_layout = QFormLayout(thumbnail_group)

        # サムネイルディレクトリ
        thumbnail_dir_layout = QHBoxLayout()
        self.thumbnail_dir_edit = QLineEdit()
        self.thumbnail_dir_edit.setReadOnly(True)
        thumbnail_dir_layout.addWidget(self.thumbnail_dir_edit)

        browse_thumbnail_button = QPushButton("参照...")
        browse_thumbnail_button.clicked.connect(self._browse_thumbnail_dir)
        thumbnail_dir_layout.addWidget(browse_thumbnail_button)

        thumbnail_layout.addRow("サムネイルディレクトリ:", thumbnail_dir_layout)

        layout.addWidget(thumbnail_group)

        # 余白を追加
        layout.addStretch()

        return tab

    def _create_display_tab(self):
        """表示設定タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # UIテーマ設定
        theme_group = QGroupBox("UIテーマ")
        theme_layout = QFormLayout(theme_group)

        # テーマ選択
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ライト", "ダーク"])
        theme_layout.addRow("テーマ:", self.theme_combo)

        layout.addWidget(theme_group)

        # 表示モード設定
        view_group = QGroupBox("表示モード")
        view_layout = QFormLayout(view_group)

        # デフォルト表示モード
        self.default_view_combo = QComboBox()
        self.default_view_combo.addItems(["グリッド表示", "リスト表示", "本棚表示"])
        view_layout.addRow("デフォルト表示:", self.default_view_combo)

        # サムネイルサイズ
        self.thumbnail_size_combo = QComboBox()
        self.thumbnail_size_combo.addItems(["小", "中", "大"])
        view_layout.addRow("サムネイルサイズ:", self.thumbnail_size_combo)

        # ソートフィールド
        self.sort_field_combo = QComboBox()
        self.sort_field_combo.addItems(
            ["タイトル", "著者", "追加日", "最終閲覧日", "評価"]
        )
        view_layout.addRow("ソート項目:", self.sort_field_combo)

        # ソート方向
        self.sort_direction_combo = QComboBox()
        self.sort_direction_combo.addItems(["昇順", "降順"])
        view_layout.addRow("ソート方向:", self.sort_direction_combo)

        layout.addWidget(view_group)

        # 余白を追加
        layout.addStretch()

        return tab

    def _create_viewer_tab(self):
        """PDFビューア設定タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # ページめくり設定
        page_group = QGroupBox("ページめくり設定")
        page_layout = QFormLayout(page_group)

        # ページめくりモード
        self.page_turn_mode_combo = QComboBox()
        self.page_turn_mode_combo.addItems(["単一ページ", "見開き", "連続"])
        page_layout.addRow("ページめくりモード:", self.page_turn_mode_combo)

        # マンガモード（右から左）
        self.manga_mode_check = QCheckBox("マンガモード（右から左への表示）")
        page_layout.addRow("", self.manga_mode_check)

        # 最終ページを記憶
        self.remember_page_check = QCheckBox("最後に開いたページを記憶する")
        page_layout.addRow("", self.remember_page_check)

        layout.addWidget(page_group)

        # 表示設定
        display_group = QGroupBox("表示設定")
        display_layout = QFormLayout(display_group)

        # デフォルトズームレベル
        self.zoom_level_combo = QComboBox()
        self.zoom_level_combo.addItems(
            [
                "ページを画面に合わせる",
                "幅に合わせる",
                "50%",
                "75%",
                "100%",
                "125%",
                "150%",
                "200%",
            ]
        )
        display_layout.addRow("デフォルトズーム:", self.zoom_level_combo)

        layout.addWidget(display_group)

        # 余白を追加
        layout.addStretch()

        return tab

    def _create_scan_tab(self):
        """スキャン設定タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # スキャン設定
        scan_group = QGroupBox("スキャンオプション")
        scan_layout = QFormLayout(scan_group)

        # 起動時にスキャン
        self.scan_on_startup_check = QCheckBox("起動時にライブラリをスキャン")
        scan_layout.addRow("", self.scan_on_startup_check)

        # ディレクトリを監視
        self.watch_directories_check = QCheckBox(
            "ライブラリディレクトリを監視（追加時に自動スキャン）"
        )
        scan_layout.addRow("", self.watch_directories_check)

        # 自動インポート
        self.auto_import_check = QCheckBox("検出されたPDFファイルを自動インポート")
        scan_layout.addRow("", self.auto_import_check)

        layout.addWidget(scan_group)

        # ライブラリパス
        library_group = QGroupBox("ライブラリパス")
        library_layout = QVBoxLayout(library_group)

        self.library_paths_list = QListWidget()
        library_layout.addWidget(self.library_paths_list)

        # ライブラリパス操作ボタン
        path_button_layout = QHBoxLayout()

        add_path_button = QPushButton("追加...")
        add_path_button.clicked.connect(self._add_library_path)
        path_button_layout.addWidget(add_path_button)

        remove_path_button = QPushButton("削除")
        remove_path_button.clicked.connect(self._remove_library_path)
        path_button_layout.addWidget(remove_path_button)

        library_layout.addLayout(path_button_layout)

        layout.addWidget(library_group)

        return tab

    def _populate_ui(self):
        """設定値をUIに反映"""
        # 一般設定
        self.app_name_edit.setText(self.current_settings.get("app_name", "PDF Library"))
        self.db_path_edit.setText(self.current_settings.get("db_path", ""))
        self.thumbnail_dir_edit.setText(self.current_settings.get("thumbnail_dir", ""))

        # 表示設定
        ui_settings = self.current_settings.get("ui", {})

        theme = ui_settings.get("theme", "light")
        self.theme_combo.setCurrentIndex(0 if theme == "light" else 1)

        default_view = ui_settings.get("default_view", "grid")
        if default_view == "grid":
            self.default_view_combo.setCurrentIndex(0)
        elif default_view == "list":
            self.default_view_combo.setCurrentIndex(1)
        elif default_view == "bookshelf":
            self.default_view_combo.setCurrentIndex(2)

        thumbnail_size = ui_settings.get("thumbnail_size", "medium")
        if thumbnail_size == "small":
            self.thumbnail_size_combo.setCurrentIndex(0)
        elif thumbnail_size == "medium":
            self.thumbnail_size_combo.setCurrentIndex(1)
        elif thumbnail_size == "large":
            self.thumbnail_size_combo.setCurrentIndex(2)

        sort_field = ui_settings.get("sort_field", "title")
        if sort_field == "title":
            self.sort_field_combo.setCurrentIndex(0)
        elif sort_field == "author":
            self.sort_field_combo.setCurrentIndex(1)
        elif sort_field == "date_added":
            self.sort_field_combo.setCurrentIndex(2)
        elif sort_field == "last_read":
            self.sort_field_combo.setCurrentIndex(3)
        elif sort_field == "rating":
            self.sort_field_combo.setCurrentIndex(4)

        sort_direction = ui_settings.get("sort_direction", "asc")
        self.sort_direction_combo.setCurrentIndex(0 if sort_direction == "asc" else 1)

        # PDFビューア設定
        viewer_settings = self.current_settings.get("viewer", {})

        page_turn_mode = viewer_settings.get("page_turn_mode", "single")
        if page_turn_mode == "single":
            self.page_turn_mode_combo.setCurrentIndex(0)
        elif page_turn_mode == "double":
            self.page_turn_mode_combo.setCurrentIndex(1)
        elif page_turn_mode == "continuous":
            self.page_turn_mode_combo.setCurrentIndex(2)

        self.manga_mode_check.setChecked(viewer_settings.get("manga_mode", False))
        self.remember_page_check.setChecked(
            viewer_settings.get("remember_last_page", True)
        )

        # ズームレベル
        zoom_level = viewer_settings.get("zoom_level", 1.0)
        zoom_index = 0  # デフォルトは「ページを画面に合わせる」

        if zoom_level == 0.5:
            zoom_index = 2
        elif zoom_level == 0.75:
            zoom_index = 3
        elif zoom_level == 1.0:
            zoom_index = 4
        elif zoom_level == 1.25:
            zoom_index = 5
        elif zoom_level == 1.5:
            zoom_index = 6
        elif zoom_level == 2.0:
            zoom_index = 7

        self.zoom_level_combo.setCurrentIndex(zoom_index)

        # スキャン設定
        scan_options = self.current_settings.get("scan_options", {})

        self.scan_on_startup_check.setChecked(scan_options.get("scan_on_startup", True))
        self.watch_directories_check.setChecked(
            scan_options.get("watch_directories", False)
        )
        self.auto_import_check.setChecked(scan_options.get("auto_import", True))

        # ライブラリパス
        self.library_paths_list.clear()
        for path in self.current_settings.get("library_paths", []):
            self.library_paths_list.addItem(path)

    def _get_settings_from_ui(self):
        """UIから設定値を取得"""
        settings = {}

        # 一般設定
        settings["app_name"] = self.app_name_edit.text()
        settings["db_path"] = self.db_path_edit.text()
        settings["thumbnail_dir"] = self.thumbnail_dir_edit.text()

        # 表示設定
        settings["ui"] = {}
        settings["ui"]["theme"] = (
            "light" if self.theme_combo.currentIndex() == 0 else "dark"
        )

        view_index = self.default_view_combo.currentIndex()
        if view_index == 0:
            settings["ui"]["default_view"] = "grid"
        elif view_index == 1:
            settings["ui"]["default_view"] = "list"
        elif view_index == 2:
            settings["ui"]["default_view"] = "bookshelf"

        size_index = self.thumbnail_size_combo.currentIndex()
        if size_index == 0:
            settings["ui"]["thumbnail_size"] = "small"
        elif size_index == 1:
            settings["ui"]["thumbnail_size"] = "medium"
        elif size_index == 2:
            settings["ui"]["thumbnail_size"] = "large"

        field_index = self.sort_field_combo.currentIndex()
        if field_index == 0:
            settings["ui"]["sort_field"] = "title"
        elif field_index == 1:
            settings["ui"]["sort_field"] = "author"
        elif field_index == 2:
            settings["ui"]["sort_field"] = "date_added"
        elif field_index == 3:
            settings["ui"]["sort_field"] = "last_read"
        elif field_index == 4:
            settings["ui"]["sort_field"] = "rating"

        settings["ui"]["sort_direction"] = (
            "asc" if self.sort_direction_combo.currentIndex() == 0 else "desc"
        )

        # PDFビューア設定
        settings["viewer"] = {}

        mode_index = self.page_turn_mode_combo.currentIndex()
        if mode_index == 0:
            settings["viewer"]["page_turn_mode"] = "single"
        elif mode_index == 1:
            settings["viewer"]["page_turn_mode"] = "double"
        elif mode_index == 2:
            settings["viewer"]["page_turn_mode"] = "continuous"

        settings["viewer"]["manga_mode"] = self.manga_mode_check.isChecked()
        settings["viewer"]["remember_last_page"] = self.remember_page_check.isChecked()

        # ズームレベル
        zoom_index = self.zoom_level_combo.currentIndex()
        if zoom_index == 0:
            settings["viewer"]["zoom_level"] = 1.0  # フィットは1.0として扱う
        elif zoom_index == 1:
            settings["viewer"]["zoom_level"] = 1.0  # 幅に合わせるも1.0として扱う
        elif zoom_index == 2:
            settings["viewer"]["zoom_level"] = 0.5
        elif zoom_index == 3:
            settings["viewer"]["zoom_level"] = 0.75
        elif zoom_index == 4:
            settings["viewer"]["zoom_level"] = 1.0
        elif zoom_index == 5:
            settings["viewer"]["zoom_level"] = 1.25
        elif zoom_index == 6:
            settings["viewer"]["zoom_level"] = 1.5
        elif zoom_index == 7:
            settings["viewer"]["zoom_level"] = 2.0

        # スキャン設定
        settings["scan_options"] = {}
        settings["scan_options"]["scan_on_startup"] = (
            self.scan_on_startup_check.isChecked()
        )
        settings["scan_options"]["watch_directories"] = (
            self.watch_directories_check.isChecked()
        )
        settings["scan_options"]["auto_import"] = self.auto_import_check.isChecked()

        # ライブラリパス
        settings["library_paths"] = []
        for i in range(self.library_paths_list.count()):
            settings["library_paths"].append(self.library_paths_list.item(i).text())

        return settings

    def _apply_settings(self):
        """設定を適用"""
        self.current_settings = self._get_settings_from_ui()

        # 設定をConfigオブジェクトに反映
        for key, value in self.current_settings.items():
            if key in ["ui", "viewer", "scan_options"]:
                # ネストされた辞書の場合
                for sub_key, sub_value in value.items():
                    self.config.set(f"{key}.{sub_key}", sub_value)
            elif key == "library_paths":
                # ライブラリパスを更新
                current_paths = self.config.get_all_library_paths()

                # 既存のパスを削除
                for path in current_paths:
                    self.config.remove_library_path(path)

                # 新しいパスを追加
                for path in value:
                    self.config.add_library_path(path)
            else:
                # 通常の設定値
                self.config.set(key, value)

        logging.info("設定を適用しました")

    def _browse_db_path(self):
        """データベースパスの参照ダイアログ"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "データベースファイルの場所を選択",
            self.db_path_edit.text(),
            "SQLiteデータベース (*.db)",
        )

        if file_path:
            # 拡張子が.dbでない場合は追加
            if not file_path.lower().endswith(".db"):
                file_path += ".db"

            self.db_path_edit.setText(file_path)

    def _browse_thumbnail_dir(self):
        """サムネイルディレクトリの参照ダイアログ"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "サムネイルディレクトリを選択", self.thumbnail_dir_edit.text()
        )

        if dir_path:
            self.thumbnail_dir_edit.setText(dir_path)

    def _add_library_path(self):
        """ライブラリパスを追加"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "ライブラリディレクトリを選択"
        )

        if dir_path:
            # 重複チェック
            for i in range(self.library_paths_list.count()):
                if self.library_paths_list.item(i).text() == dir_path:
                    return

            self.library_paths_list.addItem(dir_path)

    def _remove_library_path(self):
        """選択したライブラリパスを削除"""
        selected_items = self.library_paths_list.selectedItems()
        for item in selected_items:
            self.library_paths_list.takeItem(self.library_paths_list.row(item))

    def accept(self):
        """OKボタンが押されたときの処理"""
        self._apply_settings()
        super().accept()


# ヘルパーウィジェット
class QLineEdit(QLineEdit):
    """QLineEditの拡張クラス"""

    def __init__(self, text=""):
        super().__init__(text)
        self.setMinimumWidth(250)
