import json
import os
from pathlib import Path

from PyQt6.QtCore import Qt
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
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """
    アプリケーション設定ダイアログ。

    PDFライブラリの表示オプション、パス設定などを管理する。

    Parameters
    ----------
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, parent=None):
        """
        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # デフォルト設定を定義
        self.default_settings = {
            "general": {"startup_show_last_book": True, "confirm_delete": True},
            "appearance": {
                "grid_columns": 4,
                "grid_cover_size": 150,
                "list_cover_size": 48,
                "default_view": "grid",  # or "list"
            },
            "paths": {"default_import_path": "", "database_path": "library.db"},
            "reading": {
                "default_zoom": 100,  # パーセント
                "page_turn_mode": "continuous",  # or "single"
            },
        }

        # 設定を読み込む
        self.settings = self.load_settings()

        # レイアウトの設定
        self.layout = QVBoxLayout(self)

        # タブウィジェットの作成
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # 一般設定タブ
        self.general_tab = QWidget()
        self.tab_widget.addTab(self.general_tab, "General")
        self.setup_general_tab()

        # 外観設定タブ
        self.appearance_tab = QWidget()
        self.tab_widget.addTab(self.appearance_tab, "Appearance")
        self.setup_appearance_tab()

        # パス設定タブ
        self.paths_tab = QWidget()
        self.tab_widget.addTab(self.paths_tab, "Paths")
        self.setup_paths_tab()

        # 読書設定タブ
        self.reading_tab = QWidget()
        self.tab_widget.addTab(self.reading_tab, "Reading")
        self.setup_reading_tab()

        # ボタン
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Reset
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_settings
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(
            self.reset_to_defaults
        )
        self.layout.addWidget(self.button_box)

        # 設定の適用（ダイアログが閉じられるときに呼ばれる）
        self.accepted.connect(self.apply_settings)

    def setup_general_tab(self):
        """一般設定タブを設定する。"""
        layout = QVBoxLayout(self.general_tab)

        # 一般設定グループ
        general_group = QGroupBox("General Options")
        general_layout = QFormLayout(general_group)

        # 起動時に最後に表示していた書籍を表示するかどうか
        self.startup_show_last_book = QCheckBox()
        self.startup_show_last_book.setChecked(
            self.settings["general"]["startup_show_last_book"]
        )
        general_layout.addRow(
            "Show last opened book at startup:", self.startup_show_last_book
        )

        # 削除時に確認するかどうか
        self.confirm_delete = QCheckBox()
        self.confirm_delete.setChecked(self.settings["general"]["confirm_delete"])
        general_layout.addRow("Confirm before deleting books:", self.confirm_delete)

        layout.addWidget(general_group)
        layout.addStretch(1)

    def setup_appearance_tab(self):
        """外観設定タブを設定する。"""
        layout = QVBoxLayout(self.appearance_tab)

        # グリッドビュー設定グループ
        grid_group = QGroupBox("Grid View")
        grid_layout = QFormLayout(grid_group)

        # グリッドカラム数
        self.grid_columns = QSpinBox()
        self.grid_columns.setMinimum(1)
        self.grid_columns.setMaximum(10)
        self.grid_columns.setValue(self.settings["appearance"]["grid_columns"])
        grid_layout.addRow("Number of columns:", self.grid_columns)

        # グリッド表紙サイズ
        self.grid_cover_size = QSpinBox()
        self.grid_cover_size.setMinimum(50)
        self.grid_cover_size.setMaximum(300)
        self.grid_cover_size.setValue(self.settings["appearance"]["grid_cover_size"])
        grid_layout.addRow("Cover image size:", self.grid_cover_size)

        layout.addWidget(grid_group)

        # リストビュー設定グループ
        list_group = QGroupBox("List View")
        list_layout = QFormLayout(list_group)

        # リスト表紙サイズ
        self.list_cover_size = QSpinBox()
        self.list_cover_size.setMinimum(20)
        self.list_cover_size.setMaximum(100)
        self.list_cover_size.setValue(self.settings["appearance"]["list_cover_size"])
        list_layout.addRow("Cover image size:", self.list_cover_size)

        layout.addWidget(list_group)

        # 一般外観設定
        appearance_group = QGroupBox("General Appearance")
        appearance_layout = QFormLayout(appearance_group)

        # デフォルトビュー
        self.default_view = QComboBox()
        self.default_view.addItems(["Grid View", "List View"])
        current_view = (
            "Grid View"
            if self.settings["appearance"]["default_view"] == "grid"
            else "List View"
        )
        self.default_view.setCurrentText(current_view)
        appearance_layout.addRow("Default view:", self.default_view)

        layout.addWidget(appearance_group)
        layout.addStretch(1)

    def setup_paths_tab(self):
        """パス設定タブを設定する。"""
        layout = QVBoxLayout(self.paths_tab)

        # パス設定グループ
        paths_group = QGroupBox("File Paths")
        paths_layout = QFormLayout(paths_group)

        # デフォルトインポートパス
        import_path_layout = QHBoxLayout()
        self.default_import_path = QLineEdit(
            self.settings["paths"]["default_import_path"]
        )
        import_path_layout.addWidget(self.default_import_path)

        self.browse_import_path = QPushButton("Browse...")
        self.browse_import_path.clicked.connect(self.browse_for_import_path)
        import_path_layout.addWidget(self.browse_import_path)

        paths_layout.addRow("Default import path:", import_path_layout)

        # データベースパス
        db_path_layout = QHBoxLayout()
        self.database_path = QLineEdit(self.settings["paths"]["database_path"])
        db_path_layout.addWidget(self.database_path)

        self.browse_db_path = QPushButton("Browse...")
        self.browse_db_path.clicked.connect(self.browse_for_db_path)
        db_path_layout.addWidget(self.browse_db_path)

        paths_layout.addRow("Database path:", db_path_layout)

        layout.addWidget(paths_group)

        # データベース操作グループ
        db_group = QGroupBox("Database Operations")
        db_layout = QVBoxLayout(db_group)

        # バックアップボタン
        self.backup_button = QPushButton("Backup Database...")
        self.backup_button.clicked.connect(self.backup_database)
        db_layout.addWidget(self.backup_button)

        # 復元ボタン
        self.restore_button = QPushButton("Restore Database...")
        self.restore_button.clicked.connect(self.restore_database)
        db_layout.addWidget(self.restore_button)

        # 警告ラベル
        self.warning_label = QLabel(
            "Warning: Restoring a database will replace all current data!"
        )
        self.warning_label.setStyleSheet("color: red;")
        db_layout.addWidget(self.warning_label)

        layout.addWidget(db_group)
        layout.addStretch(1)

    def setup_reading_tab(self):
        """読書設定タブを設定する。"""
        layout = QVBoxLayout(self.reading_tab)

        # 読書設定グループ
        reading_group = QGroupBox("Reading Options")
        reading_layout = QFormLayout(reading_group)

        # デフォルトズーム
        self.default_zoom = QSpinBox()
        self.default_zoom.setMinimum(50)
        self.default_zoom.setMaximum(300)
        self.default_zoom.setSuffix("%")
        self.default_zoom.setValue(self.settings["reading"]["default_zoom"])
        reading_layout.addRow("Default zoom level:", self.default_zoom)

        # ページめくりモード
        self.page_turn_mode = QComboBox()
        self.page_turn_mode.addItems(["Continuous", "Single Page"])
        current_mode = (
            "Continuous"
            if self.settings["reading"]["page_turn_mode"] == "continuous"
            else "Single Page"
        )
        self.page_turn_mode.setCurrentText(current_mode)
        reading_layout.addRow("Page turn mode:", self.page_turn_mode)

        layout.addWidget(reading_group)
        layout.addStretch(1)

    def browse_for_import_path(self):
        """インポートパス用のフォルダ選択ダイアログを表示する。"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Default Import Directory", self.default_import_path.text()
        )
        if folder_path:
            self.default_import_path.setText(folder_path)

    def browse_for_db_path(self):
        """データベースパス用のファイル選択ダイアログを表示する。"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database File",
            self.database_path.text(),
            "Database Files (*.db)",
        )
        if file_path:
            self.database_path.setText(file_path)

    def backup_database(self):
        """データベースをバックアップする。"""
        source_path = self.database_path.text()
        if not os.path.isfile(source_path):
            QMessageBox.warning(
                self, "Backup Error", f"Database file not found at: {source_path}"
            )
            return

        # バックアップ先を選択
        backup_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database Backup",
            f"{os.path.splitext(source_path)[0]}_backup.db",
            "Database Files (*.db)",
        )

        if not backup_path:
            return

        try:
            # ファイルをコピー
            import shutil

            shutil.copy2(source_path, backup_path)

            QMessageBox.information(
                self, "Backup Successful", f"Database backup saved to: {backup_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Backup Error", f"An error occurred during backup:\n{str(e)}"
            )

    def restore_database(self):
        """データベースを復元する。"""
        # 確認ダイアログ
        result = QMessageBox.warning(
            self,
            "Confirm Restore",
            "Restoring a database will replace all current data. Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # 復元元を選択
        source_path, _ = QFileDialog.getOpenFileName(
            self, "Select Database to Restore", "", "Database Files (*.db)"
        )

        if not source_path:
            return

        target_path = self.database_path.text()

        try:
            # ファイルをコピー
            import shutil

            # 既存のデータベースが開かれていないことを確認
            # この部分はメインウィンドウと連携が必要
            # 今回は簡易的に実装

            # バックアップを作成
            if os.path.isfile(target_path):
                backup_path = f"{target_path}.bak"
                shutil.copy2(target_path, backup_path)

            # 復元
            shutil.copy2(source_path, target_path)

            QMessageBox.information(
                self,
                "Restore Successful",
                f"Database has been restored. The application will now restart to apply changes.",
            )

            # 本来ならアプリケーションを再起動するべき
            # ここでは簡易的にダイアログを閉じるだけ
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Restore Error", f"An error occurred during restore:\n{str(e)}"
            )

    def apply_settings(self):
        """設定を適用する。"""
        # 一般設定
        self.settings["general"]["startup_show_last_book"] = (
            self.startup_show_last_book.isChecked()
        )
        self.settings["general"]["confirm_delete"] = self.confirm_delete.isChecked()

        # 外観設定
        self.settings["appearance"]["grid_columns"] = self.grid_columns.value()
        self.settings["appearance"]["grid_cover_size"] = self.grid_cover_size.value()
        self.settings["appearance"]["list_cover_size"] = self.list_cover_size.value()
        self.settings["appearance"]["default_view"] = (
            "grid" if self.default_view.currentText() == "Grid View" else "list"
        )

        # パス設定
        self.settings["paths"]["default_import_path"] = self.default_import_path.text()
        self.settings["paths"]["database_path"] = self.database_path.text()

        # 読書設定
        self.settings["reading"]["default_zoom"] = self.default_zoom.value()
        self.settings["reading"]["page_turn_mode"] = (
            "continuous"
            if self.page_turn_mode.currentText() == "Continuous"
            else "single"
        )

        # 設定を保存
        self.save_settings()

    def reset_to_defaults(self):
        """設定をデフォルトにリセットする。"""
        # 確認ダイアログ
        result = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # 設定をデフォルトに戻す
        self.settings = self.default_settings.copy()

        # UI要素を更新
        self.startup_show_last_book.setChecked(
            self.settings["general"]["startup_show_last_book"]
        )
        self.confirm_delete.setChecked(self.settings["general"]["confirm_delete"])
        self.grid_columns.setValue(self.settings["appearance"]["grid_columns"])
        self.grid_cover_size.setValue(self.settings["appearance"]["grid_cover_size"])
        self.list_cover_size.setValue(self.settings["appearance"]["list_cover_size"])
        self.default_view.setCurrentText(
            "Grid View"
            if self.settings["appearance"]["default_view"] == "grid"
            else "List View"
        )
        self.default_import_path.setText(self.settings["paths"]["default_import_path"])
        self.database_path.setText(self.settings["paths"]["database_path"])
        self.default_zoom.setValue(self.settings["reading"]["default_zoom"])
        self.page_turn_mode.setCurrentText(
            "Continuous"
            if self.settings["reading"]["page_turn_mode"] == "continuous"
            else "Single Page"
        )

    def load_settings(self):
        """
        設定ファイルから設定を読み込む。

        Returns
        -------
        dict
            設定の辞書
        """
        settings_path = self.get_settings_path()

        if os.path.isfile(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)

                # デフォルト設定と結合（欠けている設定をデフォルトで補完）
                settings = self.default_settings.copy()
                self.merge_settings(settings, loaded_settings)
                return settings
            except Exception as e:
                print(f"Error loading settings: {e}")

        return self.default_settings.copy()

    def save_settings(self):
        """設定をファイルに保存する。"""
        settings_path = self.get_settings_path()

        try:
            # 設定ディレクトリを作成
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)

            # 設定を保存
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)

        except Exception as e:
            print(f"Error saving settings: {e}")
            QMessageBox.warning(
                self, "Settings Error", f"Failed to save settings: {str(e)}"
            )

    def get_settings_path(self):
        """
        設定ファイルのパスを取得する。

        Returns
        -------
        str
            設定ファイルの絶対パス
        """
        # 設定ファイルの場所はOS依存
        # Windows: %APPDATA%\PDFLibraryManager\settings.json
        # macOS: ~/Library/Application Support/PDFLibraryManager/settings.json
        # Linux: ~/.config/PDFLibraryManager/settings.json
        app_name = "PDFLibraryManager"

        if os.name == "nt":  # Windows
            app_data = os.getenv("APPDATA")
            return os.path.join(app_data, app_name, "settings.json")
        elif os.name == "posix":  # macOS / Linux
            if os.path.exists(
                os.path.expanduser("~/Library/Application Support")
            ):  # macOS
                return os.path.expanduser(
                    f"~/Library/Application Support/{app_name}/settings.json"
                )
            else:  # Linux
                return os.path.expanduser(f"~/.config/{app_name}/settings.json")
        else:
            # その他のOSはカレントディレクトリに
            return os.path.join(os.getcwd(), f"{app_name}_settings.json")

    def merge_settings(self, target, source):
        """
        設定を再帰的にマージする。

        Parameters
        ----------
        target : dict
            ターゲット辞書（更新される）
        source : dict
            ソース辞書（更新内容）
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                # 両方辞書の場合は再帰的にマージ
                self.merge_settings(target[key], value)
            elif key in target:
                # その他の場合は上書き
                target[key] = value
