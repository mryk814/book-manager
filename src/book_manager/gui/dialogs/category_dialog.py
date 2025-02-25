import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class CategoryDialog(QDialog):
    """カテゴリ管理ダイアログ"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.categories = []

        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("カテゴリの管理")
        self.resize(700, 500)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # スプリットビュー: 左側にカテゴリ一覧、右側にビュー一覧
        main_layout = QHBoxLayout()

        # 左側: カテゴリ一覧
        category_layout = QVBoxLayout()
        category_label = QLabel("カテゴリ一覧:")
        category_layout.addWidget(category_label)

        self.category_table = QTableView()
        self.category_model = QStandardItemModel()
        self.category_model.setHorizontalHeaderLabels(["カテゴリ名", "表示順", "説明"])
        self.category_table.setModel(self.category_model)

        # カラム幅の設定
        self.category_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.category_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.category_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.category_table.setColumnWidth(1, 60)

        self.category_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.category_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self.category_table.selectionModel().selectionChanged.connect(
            self._on_category_selected
        )
        category_layout.addWidget(self.category_table)

        # カテゴリ操作ボタン
        category_button_layout = QHBoxLayout()

        add_category_button = QPushButton("追加")
        add_category_button.clicked.connect(self._add_category)
        category_button_layout.addWidget(add_category_button)

        edit_category_button = QPushButton("編集")
        edit_category_button.clicked.connect(self._edit_category)
        category_button_layout.addWidget(edit_category_button)

        delete_category_button = QPushButton("削除")
        delete_category_button.clicked.connect(self._delete_category)
        category_button_layout.addWidget(delete_category_button)

        category_layout.addLayout(category_button_layout)

        # 右側: ビュー一覧
        view_layout = QVBoxLayout()
        self.view_label = QLabel("ビュー一覧: (カテゴリを選択)")
        view_layout.addWidget(self.view_label)

        self.view_list = QListWidget()
        self.view_list.itemDoubleClicked.connect(self._edit_view)
        view_layout.addWidget(self.view_list)

        # ビュー操作ボタン
        view_button_layout = QHBoxLayout()

        self.add_view_button = QPushButton("追加")
        self.add_view_button.clicked.connect(self._add_view)
        self.add_view_button.setEnabled(False)
        view_button_layout.addWidget(self.add_view_button)

        self.edit_view_button = QPushButton("編集")
        self.edit_view_button.clicked.connect(self._edit_view)
        self.edit_view_button.setEnabled(False)
        view_button_layout.addWidget(self.edit_view_button)

        self.delete_view_button = QPushButton("削除")
        self.delete_view_button.clicked.connect(self._delete_view)
        self.delete_view_button.setEnabled(False)
        view_button_layout.addWidget(self.delete_view_button)

        view_layout.addLayout(view_button_layout)

        # レイアウトを追加
        main_layout.addLayout(category_layout, 3)  # 60%
        main_layout.addLayout(view_layout, 2)  # 40%

        layout.addLayout(main_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_categories(self):
        """カテゴリをデータベースから読み込む"""
        self.category_model.setRowCount(0)  # クリア
        self.categories = self.db_manager.get_all_categories()

        for category in self.categories:
            # カテゴリ名のアイテム
            name_item = QStandardItem(category.name)

            # 表示順のアイテム
            order_item = QStandardItem(str(category.display_order))
            order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 説明のアイテム
            description_item = QStandardItem(
                category.description if category.description else ""
            )

            # 行を追加
            self.category_model.appendRow([name_item, order_item, description_item])

        self.category_table.resizeColumnsToContents()

        # ビューリストをクリア
        self.view_list.clear()
        self.view_label.setText("ビュー一覧: (カテゴリを選択)")
        self.add_view_button.setEnabled(False)
        self.edit_view_button.setEnabled(False)
        self.delete_view_button.setEnabled(False)

    def _on_category_selected(self):
        """カテゴリが選択されたときの処理"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            # 選択解除された場合
            self.view_list.clear()
            self.view_label.setText("ビュー一覧: (カテゴリを選択)")
            self.add_view_button.setEnabled(False)
            self.edit_view_button.setEnabled(False)
            self.delete_view_button.setEnabled(False)
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # カテゴリのIDを取得
        category = self.categories[row]

        # ビュー一覧を更新
        self._load_views(category)

        # ラベルを更新
        self.view_label.setText(f"ビュー一覧: {category.name}")

        # ボタンを有効化
        self.add_view_button.setEnabled(True)

    def _load_views(self, category):
        """カテゴリに属するビューを読み込む"""
        self.view_list.clear()

        views = self.db_manager.get_views_by_category(category.id)

        for view in views:
            item = QListWidgetItem(view.name)
            item.setData(Qt.ItemDataRole.UserRole, view)
            self.view_list.addItem(item)

    def _add_category(self):
        """新しいカテゴリを追加"""
        dialog = CategoryEditDialog(None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 入力データを取得
            category_data = dialog.get_category_data()

            # カテゴリの重複チェック
            for category in self.categories:
                if category.name.lower() == category_data["name"].lower():
                    QMessageBox.warning(
                        self,
                        "重複エラー",
                        f"カテゴリ「{category_data['name']}」は既に存在します。",
                    )
                    return

            # カテゴリをデータベースに追加
            category = self.db_manager.get_or_create_category(
                category_data["name"], category_data["description"]
            )

            # 表示順を更新
            self.db_manager.update_category_display_order(
                category.id, category_data["display_order"]
            )

            # リストを更新
            self._load_categories()

            logging.info(f"カテゴリを追加しました: {category_data['name']}")

    def _edit_category(self):
        """選択したカテゴリを編集"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(
                self, "選択エラー", "編集するカテゴリを選択してください。"
            )
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # カテゴリのIDを取得
        category = self.categories[row]

        # カテゴリ編集ダイアログを表示
        dialog = CategoryEditDialog(category, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 入力データを取得
            category_data = dialog.get_category_data()

            # 重複チェック（自分以外）
            for c in self.categories:
                if (
                    c.id != category.id
                    and c.name.lower() == category_data["name"].lower()
                ):
                    QMessageBox.warning(
                        self,
                        "重複エラー",
                        f"カテゴリ「{category_data['name']}」は既に存在します。",
                    )
                    return

            # カテゴリを更新
            self.db_manager.update_category(
                category.id,
                category_data["name"],
                category_data["description"],
                category_data["display_order"],
            )

            # リストを更新
            self._load_categories()

            logging.info(
                f"カテゴリを更新しました: {category.name} -> {category_data['name']}"
            )

    def _delete_category(self):
        """選択したカテゴリを削除"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(
                self, "選択エラー", "削除するカテゴリを選択してください。"
            )
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # カテゴリのIDを取得
        category = self.categories[row]

        # ビュー数を確認
        views = self.db_manager.get_views_by_category(category.id)
        views_count = len(views)

        # 削除前の確認
        msg = f"カテゴリ「{category.name}」を削除しますか？"
        if views_count > 0:
            msg += f"\n\nこのカテゴリには{views_count}個のビューが含まれています。"
            msg += "\n削除すると、これらのビューも削除されます。"

        reply = QMessageBox.question(
            self,
            "カテゴリの削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # カテゴリを削除
            self.db_manager.delete_category(category.id)

            # リストを更新
            self._load_categories()

            logging.info(f"カテゴリを削除しました: {category.name}")

    def _add_view(self):
        """選択したカテゴリに新しいビューを追加"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "選択エラー", "カテゴリを選択してください。")
            return

        # 選択された行のインデックス
        row = selected_indexes[0].row()

        # カテゴリのIDを取得
        category = self.categories[row]

        # ビュー名を入力
        view_name, ok = QInputDialog.getText(
            self,
            "ビューの追加",
            f"カテゴリ「{category.name}」の新しいビュー名を入力してください:",
            QLineEdit.EchoMode.Normal,
        )

        if ok and view_name.strip():
            # ビューを追加
            view_data = {
                "name": view_name.strip(),
                "category_id": category.id,
                "view_type": "grid",  # デフォルトはグリッド表示
                "sort_field": "title",
                "sort_direction": "asc",
                "filter_query": None,
            }

            # ビューの重複チェック
            existing_views = self.db_manager.get_views_by_category(category.id)
            for view in existing_views:
                if view.name.lower() == view_data["name"].lower():
                    QMessageBox.warning(
                        self,
                        "重複エラー",
                        f"ビュー「{view_data['name']}」は既に存在します。",
                    )
                    return

            # ビューをデータベースに追加
            self.db_manager.create_view(view_data)

            # ビュー一覧を更新
            self._load_views(category)

            logging.info(
                f"ビューを追加しました: {view_data['name']} (カテゴリ: {category.name})"
            )

    def _edit_view(self):
        """選択したビューを編集"""
        selected_items = self.view_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "選択エラー", "編集するビューを選択してください。"
            )
            return

        # 選択されたビューを取得
        view = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # 現在のカテゴリを取得
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            return

        row = selected_indexes[0].row()
        category = self.categories[row]

        # ビュー名を入力
        view_name, ok = QInputDialog.getText(
            self,
            "ビューの編集",
            "ビュー名を入力してください:",
            QLineEdit.EchoMode.Normal,
            view.name,
        )

        if ok and view_name.strip():
            # 重複チェック（自分以外）
            existing_views = self.db_manager.get_views_by_category(category.id)
            for v in existing_views:
                if v.id != view.id and v.name.lower() == view_name.strip().lower():
                    QMessageBox.warning(
                        self,
                        "重複エラー",
                        f"ビュー「{view_name.strip()}」は既に存在します。",
                    )
                    return

            # ビューを更新
            self.db_manager.update_view(view.id, {"name": view_name.strip()})

            # ビュー一覧を更新
            self._load_views(category)

            logging.info(f"ビューを更新しました: {view.name} -> {view_name.strip()}")

    def _delete_view(self):
        """選択したビューを削除"""
        selected_items = self.view_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "選択エラー", "削除するビューを選択してください。"
            )
            return

        # 選択されたビューを取得
        view = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # 現在のカテゴリを取得
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            return

        row = selected_indexes[0].row()
        category = self.categories[row]

        # 削除前の確認
        reply = QMessageBox.question(
            self,
            "ビューの削除",
            f"ビュー「{view.name}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # ビューを削除
            self.db_manager.delete_view(view.id)

            # ビュー一覧を更新
            self._load_views(category)

            logging.info(f"ビューを削除しました: {view.name}")


class CategoryEditDialog(QDialog):
    """カテゴリ編集ダイアログ"""

    def __init__(self, category, parent=None):
        super().__init__(parent)
        self.category = category

        self._init_ui()
        if category:
            self._load_category_data()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("カテゴリの編集" if self.category else "新規カテゴリの追加")
        self.resize(400, 300)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # フォームレイアウト
        form_layout = QFormLayout()

        # カテゴリ名
        self.name_edit = QLineEdit()
        form_layout.addRow("カテゴリ名:", self.name_edit)

        # 表示順
        self.order_spin = QSpinBox()
        self.order_spin.setMinimum(0)
        self.order_spin.setMaximum(999)
        self.order_spin.setValue(0)
        form_layout.addRow("表示順:", self.order_spin)

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

    def _load_category_data(self):
        """カテゴリデータを読み込む"""
        self.name_edit.setText(self.category.name)
        self.order_spin.setValue(self.category.display_order)
        self.description_edit.setText(
            self.category.description if self.category.description else ""
        )

    def get_category_data(self):
        """編集データを取得"""
        return {
            "name": self.name_edit.text().strip(),
            "display_order": self.order_spin.value(),
            "description": self.description_edit.toPlainText().strip(),
        }

    def accept(self):
        """OKボタンが押されたときの処理"""
        # 入力チェック
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "カテゴリ名を入力してください。")
            return

        super().accept()
