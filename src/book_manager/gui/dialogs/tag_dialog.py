import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QColorDialog,  # QColorDialogは正しくQtWidgetsから import
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)


class TagDialog(QDialog):
    """タグ管理ダイアログ"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.tags = []

        self._init_ui()
        self._load_tags()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("タグの管理")
        self.resize(500, 400)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # タグテーブルビュー
        self.tag_table = QTableView()
        self.tag_model = QStandardItemModel()
        self.tag_model.setHorizontalHeaderLabels(["タグ名", "色", "使用数"])
        self.tag_table.setModel(self.tag_model)
        self.tag_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.tag_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.tag_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.tag_table.setColumnWidth(1, 80)
        self.tag_table.setColumnWidth(2, 80)
        self.tag_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.tag_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tag_table.doubleClicked.connect(self._edit_tag)
        layout.addWidget(self.tag_table)

        # 操作ボタンのレイアウト
        button_layout = QHBoxLayout()

        # 新規タグ追加
        add_layout = QHBoxLayout()
        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setPlaceholderText("新しいタグ名")
        add_layout.addWidget(self.tag_name_edit)

        self.color_button = QPushButton("色選択")
        self.color_button.clicked.connect(self._select_color)
        self.selected_color = "#1E90FF"  # デフォルト色 (ドジャーブルー)
        self.color_button.setStyleSheet(
            f"background-color: {self.selected_color}; color: white;"
        )
        add_layout.addWidget(self.color_button)

        add_button = QPushButton("追加")
        add_button.clicked.connect(self._add_tag)
        add_layout.addWidget(add_button)

        button_layout.addLayout(add_layout)

        button_layout.addStretch()

        # 編集・削除ボタン
        edit_button = QPushButton("編集")
        edit_button.clicked.connect(self._edit_tag)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("削除")
        delete_button.clicked.connect(self._delete_tag)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_tags(self):
        """タグをデータベースから読み込む"""
        self.tag_model.setRowCount(0)  # クリア
        self.tags = self.db_manager.get_all_tags()

        for tag in self.tags:
            # タグ名のアイテム
            name_item = QStandardItem(tag.name)

            # 色のアイテム
            color_item = QStandardItem()
            color_item.setData(tag.color, Qt.ItemDataRole.UserRole)
            color_item.setText("")  # テキストは表示しない

            # 使用数のアイテム
            count = len(tag.books)
            count_item = QStandardItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 行を追加
            self.tag_model.appendRow([name_item, color_item, count_item])

            # 色を背景色として設定
            color_index = self.tag_model.index(self.tag_model.rowCount() - 1, 1)
            self.tag_model.setData(
                color_index, QColor(tag.color), Qt.ItemDataRole.BackgroundRole
            )

        self.tag_table.resizeColumnsToContents()

    def _select_color(self):
        """色選択ダイアログを表示"""
        current_color = QColor(self.selected_color)
        color = QColorDialog.getColor(current_color, self, "タグの色を選択")

        if color.isValid():
            self.selected_color = color.name()
            self.color_button.setStyleSheet(
                f"background-color: {self.selected_color}; color: {'white' if color.lightness() < 128 else 'black'};"
            )

    def _add_tag(self):
        """新しいタグを追加"""
        tag_name = self.tag_name_edit.text().strip()
        if not tag_name:
            QMessageBox.warning(self, "入力エラー", "タグ名を入力してください。")
            return

        # タグの重複チェック
        for tag in self.tags:
            if tag.name.lower() == tag_name.lower():
                QMessageBox.warning(
                    self, "重複エラー", f"タグ「{tag_name}」は既に存在します。"
                )
                return

        # タグをデータベースに追加
        tag = self.db_manager.get_or_create_tag(tag_name)

        # 色を設定
        self.db_manager.update_tag(tag.id, {"color": self.selected_color})

        # 入力欄をクリア
        self.tag_name_edit.clear()

        # リストを更新
        self._load_tags()

        logging.info(f"タグを追加しました: {tag_name}")

    def _edit_tag(self):
        """選択したタグを編集"""
        selected_indexes = self.tag_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "選択エラー", "編集するタグを選択してください。")
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # タグのIDを取得
        tag = self.tags[row]

        # タグ編集ダイアログを表示
        dialog = TagEditDialog(tag, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # タグを更新
            new_name = dialog.tag_name_edit.text().strip()
            new_color = dialog.selected_color

            # 重複チェック（自分以外）
            for t in self.tags:
                if t.id != tag.id and t.name.lower() == new_name.lower():
                    QMessageBox.warning(
                        self, "重複エラー", f"タグ「{new_name}」は既に存在します。"
                    )
                    return

            # タグを更新
            self.db_manager.update_tag(tag.id, {"name": new_name, "color": new_color})

            # リストを更新
            self._load_tags()

            logging.info(f"タグを更新しました: {tag.name} -> {new_name}")

    def _delete_tag(self):
        """選択したタグを削除"""
        selected_indexes = self.tag_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "選択エラー", "削除するタグを選択してください。")
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # タグのIDを取得
        tag = self.tags[row]

        # 使用数を確認
        books_count = len(tag.books)

        # 削除前の確認
        msg = f"タグ「{tag.name}」を削除しますか？"
        if books_count > 0:
            msg += f"\n\nこのタグは{books_count}冊の書籍に使用されています。"
            msg += "\n削除すると、これらの書籍からタグが削除されます。"

        reply = QMessageBox.question(
            self,
            "タグの削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # タグを削除
            self.db_manager.delete_tag(tag.id)

            # リストを更新
            self._load_tags()

            logging.info(f"タグを削除しました: {tag.name}")


class TagEditDialog(QDialog):
    """タグ編集ダイアログ"""

    def __init__(self, tag, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.selected_color = tag.color

        self._init_ui()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("タグの編集")
        self.resize(300, 120)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # 名前入力
        name_layout = QHBoxLayout()
        name_label = QLabel("タグ名:")
        name_layout.addWidget(name_label)

        self.tag_name_edit = QLineEdit(self.tag.name)
        name_layout.addWidget(self.tag_name_edit)

        layout.addLayout(name_layout)

        # 色選択
        color_layout = QHBoxLayout()
        color_label = QLabel("色:")
        color_layout.addWidget(color_label)

        self.color_button = QPushButton()
        self.color_button.setStyleSheet(
            f"background-color: {self.selected_color}; color: {'white' if QColor(self.selected_color).lightness() < 128 else 'black'};"
        )
        self.color_button.setText("色を選択")
        self.color_button.clicked.connect(self._select_color)
        color_layout.addWidget(self.color_button)

        layout.addLayout(color_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _select_color(self):
        """色選択ダイアログを表示"""
        current_color = QColor(self.selected_color)
        color = QColorDialog.getColor(current_color, self, "タグの色を選択")

        if color.isValid():
            self.selected_color = color.name()
            self.color_button.setStyleSheet(
                f"background-color: {self.selected_color}; color: {'white' if color.lightness() < 128 else 'black'};"
            )
