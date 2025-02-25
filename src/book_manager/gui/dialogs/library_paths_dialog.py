import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class LibraryPathsDialog(QDialog):
    """ライブラリパス設定ダイアログ"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.paths = self.config.get_all_library_paths()

        self._init_ui()
        self._load_paths()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("ライブラリパスの設定")
        self.resize(600, 400)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # 説明ラベル
        label = QLabel(
            "PDFファイルを検索するディレクトリを追加してください。\n追加したディレクトリとそのサブディレクトリが自動的にスキャンされます。"
        )
        layout.addWidget(label)

        # パスリスト
        self.path_list = QListWidget()
        layout.addWidget(self.path_list)

        # ボタンレイアウト
        button_layout = QHBoxLayout()

        # パス追加ボタン
        self.add_button = QPushButton("追加...")
        self.add_button.clicked.connect(self._add_path)
        button_layout.addWidget(self.add_button)

        # パス削除ボタン
        self.remove_button = QPushButton("削除")
        self.remove_button.clicked.connect(self._remove_path)
        self.remove_button.setEnabled(False)  # 初期状態では無効
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # パスリストの選択イベント
        self.path_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_paths(self):
        """パスリストを読み込む"""
        self.path_list.clear()

        for path in self.paths:
            self.path_list.addItem(path)

    def _add_path(self):
        """パスを追加"""
        directory = QFileDialog.getExistingDirectory(
            self, "ライブラリディレクトリを選択", ""
        )

        if directory:
            # 既存パスのチェック
            if directory in self.paths:
                QMessageBox.warning(
                    self, "重複パス", "指定されたパスは既に追加されています。"
                )
                return

            # 追加
            self.paths.append(directory)
            self._load_paths()

    def _remove_path(self):
        """選択されたパスを削除"""
        current_row = self.path_list.currentRow()
        if current_row >= 0:
            removed_path = self.paths.pop(current_row)
            self._load_paths()

    def _on_selection_changed(self):
        """リスト選択変更時の処理"""
        self.remove_button.setEnabled(len(self.path_list.selectedItems()) > 0)

    def save_paths(self):
        """パスを保存"""
        # 設定に保存
        # 既存のパスをクリア
        current_paths = self.config.get_all_library_paths()
        for path in current_paths:
            self.config.remove_library_path(path)

        # 新しいパスを追加
        for path in self.paths:
            self.config.add_library_path(path)

        return True

    def accept(self):
        """OKボタン押下時の処理"""
        if self.save_paths():
            super().accept()

    def get_paths(self):
        """設定されたパスリストを取得"""
        return self.paths
