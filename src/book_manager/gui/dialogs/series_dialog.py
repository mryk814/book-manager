import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)


class SeriesDialog(QDialog):
    """シリーズ管理ダイアログ"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.series_list = []

        self._init_ui()
        self._load_series()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("シリーズの管理")
        self.resize(600, 500)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # シリーズテーブルビュー
        self.series_table = QTableView()
        self.series_model = QStandardItemModel()
        self.series_model.setHorizontalHeaderLabels(
            ["シリーズ名", "著者", "出版社", "カテゴリ", "書籍数"]
        )
        self.series_table.setModel(self.series_model)

        # カラム幅の設定
        self.series_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.series_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.series_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.series_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.series_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.series_table.setColumnWidth(4, 60)

        self.series_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.series_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.series_table.doubleClicked.connect(self._edit_series)
        layout.addWidget(self.series_table)

        # 操作ボタンのレイアウト
        button_layout = QHBoxLayout()

        # 新規シリーズ追加ボタン
        add_button = QPushButton("新規シリーズ")
        add_button.clicked.connect(self._add_series)
        button_layout.addWidget(add_button)

        button_layout.addStretch()

        # 編集・削除ボタン
        edit_button = QPushButton("編集")
        edit_button.clicked.connect(self._edit_series)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("削除")
        delete_button.clicked.connect(self._delete_series)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_series(self):
        """シリーズをデータベースから読み込む"""
        self.series_model.setRowCount(0)  # クリア
        self.series_list = self.db_manager.get_all_series()

        for series in self.series_list:
            # シリーズ名のアイテム
            name_item = QStandardItem(series.name)

            # 著者のアイテム
            author_item = QStandardItem(series.author if series.author else "")

            # 出版社のアイテム
            publisher_item = QStandardItem(series.publisher if series.publisher else "")

            # カテゴリのアイテム
            category_item = QStandardItem(series.category if series.category else "")

            # 書籍数のアイテム
            count = len(series.books)
            count_item = QStandardItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 行を追加
            self.series_model.appendRow(
                [name_item, author_item, publisher_item, category_item, count_item]
            )

        self.series_table.resizeColumnsToContents()

    def _add_series(self):
        """新しいシリーズを追加"""
        dialog = SeriesEditDialog(None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 入力データを取得
            series_data = dialog.get_series_data()

            # シリーズの重複チェック
            for series in self.series_list:
                if series.name.lower() == series_data["name"].lower():
                    QMessageBox.warning(
                        self,
                        "重複エラー",
                        f"シリーズ「{series_data['name']}」は既に存在します。",
                    )
                    return

            # シリーズをデータベースに追加
            series = self.db_manager.get_or_create_series(series_data["name"])

            # 他の情報を更新
            self.db_manager.update_series(
                series.id,
                {
                    "author": series_data["author"],
                    "publisher": series_data["publisher"],
                    "category": series_data["category"],
                    "description": series_data["description"],
                },
            )

            # リストを更新
            self._load_series()

            logging.info(f"シリーズを追加しました: {series_data['name']}")

    def _edit_series(self):
        """選択したシリーズを編集"""
        selected_indexes = self.series_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(
                self, "選択エラー", "編集するシリーズを選択してください。"
            )
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # シリーズのIDを取得
        series = self.series_list[row]

        # シリーズ編集ダイアログを表示
        dialog = SeriesEditDialog(series, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 入力データを取得
            series_data = dialog.get_series_data()

            # 重複チェック（自分以外）
            for s in self.series_list:
                if s.id != series.id and s.name.lower() == series_data["name"].lower():
                    QMessageBox.warning(
                        self,
                        "重複エラー",
                        f"シリーズ「{series_data['name']}」は既に存在します。",
                    )
                    return

            # シリーズを更新
            self.db_manager.update_series(series.id, series_data)

            # リストを更新
            self._load_series()

            logging.info(
                f"シリーズを更新しました: {series.name} -> {series_data['name']}"
            )

    def _delete_series(self):
        """選択したシリーズを削除"""
        selected_indexes = self.series_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(
                self, "選択エラー", "削除するシリーズを選択してください。"
            )
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # シリーズのIDを取得
        series = self.series_list[row]

        # 使用数を確認
        books_count = len(series.books)

        # 削除前の確認
        msg = f"シリーズ「{series.name}」を削除しますか？"
        if books_count > 0:
            msg += f"\n\nこのシリーズは{books_count}冊の書籍に使用されています。"
            msg += "\n削除すると、これらの書籍からシリーズ情報が削除されます。"

        reply = QMessageBox.question(
            self,
            "シリーズの削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # シリーズを削除
            self.db_manager.delete_series(series.id)

            # リストを更新
            self._load_series()

            logging.info(f"シリーズを削除しました: {series.name}")


class SeriesEditDialog(QDialog):
    """シリーズ編集ダイアログ"""

    # シリーズのカテゴリオプション
    CATEGORY_OPTIONS = ["", "漫画", "小説", "技術書", "雑誌", "ビジネス", "その他"]

    def __init__(self, series, parent=None):
        super().__init__(parent)
        self.series = series

        self._init_ui()
        if series:
            self._load_series_data()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("シリーズの編集" if self.series else "新規シリーズの追加")
        self.resize(400, 300)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # フォームレイアウト
        form_layout = QFormLayout()

        # シリーズ名
        self.name_edit = QLineEdit()
        form_layout.addRow("シリーズ名:", self.name_edit)

        # 著者
        self.author_edit = QLineEdit()
        form_layout.addRow("著者:", self.author_edit)

        # 出版社
        self.publisher_edit = QLineEdit()
        form_layout.addRow("出版社:", self.publisher_edit)

        # カテゴリ
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.CATEGORY_OPTIONS)
        form_layout.addRow("カテゴリ:", self.category_combo)

        # 説明
        self.description_edit = QTextEdit()
        form_layout.addRow("説明:", self.description_edit)

        layout.addLayout(form_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_series_data(self):
        """シリーズデータを読み込む"""
        self.name_edit.setText(self.series.name)
        self.author_edit.setText(self.series.author if self.series.author else "")
        self.publisher_edit.setText(
            self.series.publisher if self.series.publisher else ""
        )

        # カテゴリの設定
        if self.series.category:
            index = self.category_combo.findText(self.series.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        self.description_edit.setText(
            self.series.description if self.series.description else ""
        )

    def get_series_data(self):
        """編集データを取得"""
        return {
            "name": self.name_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "publisher": self.publisher_edit.text().strip(),
            "category": self.category_combo.currentText(),
            "description": self.description_edit.toPlainText().strip(),
        }

    def accept(self):
        """OKボタンが押されたときの処理"""
        # 入力チェック
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "シリーズ名を入力してください。")
            return

        super().accept()
