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
    QMenu,
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
        self.views = []  # 現在選択されているカテゴリのビュー
        self.current_category = None  # 現在選択されているカテゴリ

        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("カテゴリの管理")
        self.resize(800, 600)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # ヘルプテキスト
        help_label = QLabel(
            "Ctrlキーを押しながらクリックで複数選択、Shiftキーで範囲選択ができます"
        )
        help_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(help_label)

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

        # 複数選択を可能にする
        self.category_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.category_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )

        self.category_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.category_table.selectionModel().selectionChanged.connect(
            self._on_category_selected
        )

        # コンテキストメニュー
        self.category_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_table.customContextMenuRequested.connect(
            self._show_category_context_menu
        )

        category_layout.addWidget(self.category_table)

        # 選択情報ラベル
        self.category_selection_info_label = QLabel("0 カテゴリ選択中")
        category_layout.addWidget(self.category_selection_info_label)

        # カテゴリ操作ボタン
        category_button_layout = QHBoxLayout()

        add_category_button = QPushButton("追加")
        add_category_button.clicked.connect(self._add_category)
        category_button_layout.addWidget(add_category_button)

        self.edit_category_button = QPushButton("編集")
        self.edit_category_button.clicked.connect(self._edit_category)
        self.edit_category_button.setEnabled(False)
        category_button_layout.addWidget(self.edit_category_button)

        self.delete_category_button = QPushButton("削除")
        self.delete_category_button.clicked.connect(self._delete_category)
        self.delete_category_button.setEnabled(False)
        category_button_layout.addWidget(self.delete_category_button)

        category_layout.addLayout(category_button_layout)

        # 一括操作レイアウト
        batch_category_layout = QHBoxLayout()

        self.batch_update_category_button = QPushButton("選択したカテゴリの一括更新...")
        self.batch_update_category_button.clicked.connect(self._batch_update_categories)
        self.batch_update_category_button.setEnabled(False)
        batch_category_layout.addWidget(self.batch_update_category_button)

        self.batch_delete_category_button = QPushButton("選択したカテゴリを削除")
        self.batch_delete_category_button.clicked.connect(
            self._delete_selected_categories
        )
        self.batch_delete_category_button.setEnabled(False)
        batch_category_layout.addWidget(self.batch_delete_category_button)

        category_layout.addLayout(batch_category_layout)

        # 右側: ビュー一覧
        view_layout = QVBoxLayout()
        self.view_label = QLabel("ビュー一覧: (カテゴリを選択)")
        view_layout.addWidget(self.view_label)

        self.view_list = QListWidget()

        # 複数選択を可能にする
        self.view_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.view_list.itemDoubleClicked.connect(self._edit_view)

        # コンテキストメニュー
        self.view_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view_list.customContextMenuRequested.connect(self._show_view_context_menu)

        view_layout.addWidget(self.view_list)

        # 選択情報ラベル
        self.view_selection_info_label = QLabel("0 ビュー選択中")
        view_layout.addWidget(self.view_selection_info_label)

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

        # ビューの一括操作
        batch_view_layout = QHBoxLayout()

        self.batch_delete_view_button = QPushButton("選択したビューを削除")
        self.batch_delete_view_button.clicked.connect(self._delete_selected_views)
        self.batch_delete_view_button.setEnabled(False)
        batch_view_layout.addWidget(self.batch_delete_view_button)

        view_layout.addLayout(batch_view_layout)

        # ビューリストの選択変更時のシグナル接続
        self.view_list.itemSelectionChanged.connect(self._on_view_selection_changed)

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
        self.batch_delete_view_button.setEnabled(False)

        # 選択情報を更新
        self._update_category_selection_info()
        self._update_view_selection_info()

    def _on_category_selected(self):
        """カテゴリが選択されたときの処理"""
        selected_indexes = self.category_table.selectedIndexes()

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        has_selection = len(selected_rows) > 0
        is_single_selection = len(selected_rows) == 1
        is_multiple_selection = len(selected_rows) > 1

        # 各ボタンの有効/無効を設定
        self.edit_category_button.setEnabled(is_single_selection)
        self.delete_category_button.setEnabled(has_selection)
        self.batch_update_category_button.setEnabled(is_multiple_selection)
        self.batch_delete_category_button.setEnabled(is_multiple_selection)

        if is_single_selection:
            # 単一選択の場合のみビュー一覧を更新
            row = list(selected_rows)[0]
            category = self.categories[row]
            self.current_category = category

            # ビュー一覧を更新
            self._load_views(category)

            # ラベルを更新
            self.view_label.setText(f"ビュー一覧: {category.name}")

            # ビュー追加ボタンを有効化
            self.add_view_button.setEnabled(True)
        else:
            # 複数選択または選択なしの場合
            self.current_category = None
            self.view_list.clear()
            self.views = []

            if not has_selection:
                self.view_label.setText("ビュー一覧: (カテゴリを選択)")
            else:
                self.view_label.setText(
                    f"ビュー一覧: ({len(selected_rows)}個のカテゴリが選択中)"
                )

            # ビュー関連ボタンを無効化
            self.add_view_button.setEnabled(False)
            self.edit_view_button.setEnabled(False)
            self.delete_view_button.setEnabled(False)
            self.batch_delete_view_button.setEnabled(False)

        # 選択情報を更新
        self._update_category_selection_info()
        self._update_view_selection_info()

    def _load_views(self, category):
        """カテゴリに属するビューを読み込む"""
        self.view_list.clear()

        views = self.db_manager.get_views_by_category(category.id)
        self.views = views

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

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 複数選択されている場合
        if len(selected_rows) > 1:
            QMessageBox.warning(
                self, "選択エラー", "編集は一度に1つのカテゴリのみ可能です。"
            )
            return

        # 選択された行のインデックス
        row = list(selected_rows)[0]

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

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 複数選択されている場合
        if len(selected_rows) > 1:
            self._delete_selected_categories()
            return

        # 選択された行のインデックス
        row = list(selected_rows)[0]

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

    def _delete_selected_categories(self):
        """選択した複数のカテゴリを削除"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            return

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 行番号を降順にソート（削除時のインデックスずれを防ぐため）
        selected_rows = sorted(list(selected_rows), reverse=True)

        if not selected_rows:
            return

        # 選択したカテゴリのリスト
        selected_categories = [self.categories[row] for row in selected_rows]

        # 関連するビューの合計数
        total_views_count = 0
        for category in selected_categories:
            views = self.db_manager.get_views_by_category(category.id)
            total_views_count += len(views)

        # 削除前の確認
        if len(selected_categories) == 1:
            msg = f"カテゴリ「{selected_categories[0].name}」を削除しますか？"
        else:
            msg = f"選択した{len(selected_categories)}個のカテゴリを削除しますか？"

            # カテゴリ名を最大5個まで表示
            category_names = [category.name for category in selected_categories[:5]]
            if len(selected_categories) > 5:
                category_names.append(f"...他{len(selected_categories) - 5}個")
            msg += f"\n\n- " + "\n- ".join(category_names)

        if total_views_count > 0:
            msg += f"\n\nこれらのカテゴリには合計{total_views_count}個のビューが含まれています。"
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
            for category in selected_categories:
                self.db_manager.delete_category(category.id)
                logging.info(f"カテゴリを削除しました: {category.name}")

            # リストを更新
            self._load_categories()

            logging.info(f"{len(selected_categories)}個のカテゴリを削除しました")

    def _batch_update_categories(self):
        """選択した複数のカテゴリの一括更新"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            return

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        if not selected_rows:
            return

        # 選択したカテゴリのリスト
        selected_categories = [self.categories[row] for row in selected_rows]

        # バッチ更新ダイアログを表示
        dialog = CategoryBatchUpdateDialog(selected_categories, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新データを取得
            update_data = dialog.get_update_data()

            # 更新するフィールドがあるか確認
            if update_data["display_order"] is None and not update_data["description"]:
                return

            # 各カテゴリを更新
            for category in selected_categories:
                update_dict = {}

                # 表示順の更新
                if update_data["display_order"] is not None:
                    update_dict["display_order"] = update_data["display_order"]

                # 説明の更新（空文字列も更新）
                if update_data["description"] is not None:
                    update_dict["description"] = update_data["description"]

                if update_dict:
                    self.db_manager.update_category(
                        category.id,
                        category.name,  # 名前は変更しない
                        update_dict.get("description", category.description),
                        update_dict.get("display_order", category.display_order),
                    )

            # リストを更新
            self._load_categories()

            count_text = (
                f"{len(selected_categories)}個の"
                if len(selected_categories) > 1
                else ""
            )
            logging.info(f"{count_text}カテゴリを一括更新しました")

    def _show_category_context_menu(self, position):
        """カテゴリのコンテキストメニューを表示"""
        selected_indexes = self.category_table.selectedIndexes()
        if not selected_indexes:
            return

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # メニューの作成
        menu = QMenu(self)

        if len(selected_rows) == 1:
            # 単一選択の場合
            edit_action = menu.addAction("編集")
            edit_action.triggered.connect(self._edit_category)

            menu.addSeparator()

            delete_action = menu.addAction("削除")
            delete_action.triggered.connect(self._delete_category)
        else:
            # 複数選択の場合
            batch_update_action = menu.addAction(
                f"選択した{len(selected_rows)}個のカテゴリを一括更新..."
            )
            batch_update_action.triggered.connect(self._batch_update_categories)

            menu.addSeparator()

            delete_action = menu.addAction(
                f"選択した{len(selected_rows)}個のカテゴリを削除"
            )
            delete_action.triggered.connect(self._delete_selected_categories)

        # メニューを表示
        menu.exec(self.category_table.viewport().mapToGlobal(position))

    def _update_category_selection_info(self):
        """カテゴリ選択情報ラベルの更新"""
        selected_indexes = self.category_table.selectedIndexes()

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 選択情報を表示
        count = len(selected_rows)
        if count == 0:
            self.category_selection_info_label.setText("0 カテゴリ選択中")
        elif count == 1:
            category = self.categories[list(selected_rows)[0]]
            self.category_selection_info_label.setText(
                f"1 カテゴリ選択中: {category.name}"
            )
        else:
            self.category_selection_info_label.setText(f"{count} カテゴリ選択中")

    def _add_view(self):
        """選択したカテゴリに新しいビューを追加"""
        if not self.current_category:
            QMessageBox.warning(self, "選択エラー", "カテゴリを選択してください。")
            return

        # ビュー名を入力
        view_name, ok = QInputDialog.getText(
            self,
            "ビューの追加",
            f"カテゴリ「{self.current_category.name}」の新しいビュー名を入力してください:",
            QLineEdit.EchoMode.Normal,
        )

        if ok and view_name.strip():
            # ビューを追加
            view_data = {
                "name": view_name.strip(),
                "category_id": self.current_category.id,
                "view_type": "grid",  # デフォルトはグリッド表示
                "sort_field": "title",
                "sort_direction": "asc",
                "filter_query": None,
            }

            # ビューの重複チェック
            existing_views = self.db_manager.get_views_by_category(
                self.current_category.id
            )
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
            self._load_views(self.current_category)

            logging.info(
                f"ビューを追加しました: {view_data['name']} (カテゴリ: {self.current_category.name})"
            )

    def _edit_view(self):
        """選択したビューを編集"""
        selected_items = self.view_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "選択エラー", "編集するビューを選択してください。"
            )
            return

        # 複数選択されている場合
        if len(selected_items) > 1:
            QMessageBox.warning(
                self, "選択エラー", "編集は一度に1つのビューのみ可能です。"
            )
            return

        # 選択されたビューを取得
        view = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # 現在のカテゴリを取得
        if not self.current_category:
            return

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
            existing_views = self.db_manager.get_views_by_category(
                self.current_category.id
            )
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
            self._load_views(self.current_category)

            logging.info(f"ビューを更新しました: {view.name} -> {view_name.strip()}")

    def _delete_view(self):
        """選択したビューを削除"""
        selected_items = self.view_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "選択エラー", "削除するビューを選択してください。"
            )
            return

        # 複数選択されている場合
        if len(selected_items) > 1:
            self._delete_selected_views()
            return

        # 選択されたビューを取得
        view = selected_items[0].data(Qt.ItemDataRole.UserRole)

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
            if self.current_category:
                self._load_views(self.current_category)

            logging.info(f"ビューを削除しました: {view.name}")

    def _delete_selected_views(self):
        """選択した複数のビューを削除"""
        selected_items = self.view_list.selectedItems()
        if not selected_items:
            return

        # 選択したビューのリスト
        selected_views = [
            item.data(Qt.ItemDataRole.UserRole) for item in selected_items
        ]

        # 削除前の確認
        if len(selected_views) == 1:
            msg = f"ビュー「{selected_views[0].name}」を削除しますか？"
        else:
            msg = f"選択した{len(selected_views)}個のビューを削除しますか？"

            # ビュー名を最大5個まで表示
            view_names = [view.name for view in selected_views[:5]]
            if len(selected_views) > 5:
                view_names.append(f"...他{len(selected_views) - 5}個")
            msg += f"\n\n- " + "\n- ".join(view_names)

        reply = QMessageBox.question(
            self,
            "ビューの削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # ビューを削除
            for view in selected_views:
                self.db_manager.delete_view(view.id)
                logging.info(f"ビューを削除しました: {view.name}")

            # ビュー一覧を更新
            if self.current_category:
                self._load_views(self.current_category)

            logging.info(f"{len(selected_views)}個のビューを削除しました")

    def _show_view_context_menu(self, position):
        """ビューのコンテキストメニューを表示"""
        selected_items = self.view_list.selectedItems()
        if not selected_items:
            return

        # メニューの作成
        menu = QMenu(self)

        if len(selected_items) == 1:
            # 単一選択の場合
            edit_action = menu.addAction("編集")
            edit_action.triggered.connect(self._edit_view)

            menu.addSeparator()

            delete_action = menu.addAction("削除")
            delete_action.triggered.connect(self._delete_view)
        else:
            # 複数選択の場合
            delete_action = menu.addAction(
                f"選択した{len(selected_items)}個のビューを削除"
            )
            delete_action.triggered.connect(self._delete_selected_views)

        # メニューを表示
        menu.exec(self.view_list.viewport().mapToGlobal(position))

    def _on_view_selection_changed(self):
        """ビュー選択変更時の処理"""
        selected_items = self.view_list.selectedItems()

        has_selection = len(selected_items) > 0
        is_single_selection = len(selected_items) == 1
        is_multiple_selection = len(selected_items) > 1

        # ボタンの有効/無効を設定
        self.edit_view_button.setEnabled(is_single_selection)
        self.delete_view_button.setEnabled(has_selection)
        self.batch_delete_view_button.setEnabled(is_multiple_selection)

        # 選択情報を更新
        self._update_view_selection_info()

    def _update_view_selection_info(self):
        """ビュー選択情報ラベルの更新"""
        selected_items = self.view_list.selectedItems()

        # 選択情報を表示
        count = len(selected_items)
        if count == 0:
            self.view_selection_info_label.setText("0 ビュー選択中")
        elif count == 1:
            view = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.view_selection_info_label.setText(f"1 ビュー選択中: {view.name}")
        else:
            self.view_selection_info_label.setText(f"{count} ビュー選択中")


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


class CategoryBatchUpdateDialog(QDialog):
    """カテゴリ一括更新ダイアログ"""

    def __init__(self, category_list, parent=None):
        super().__init__(parent)
        self.category_list = category_list

        self._init_ui()

    def _init_ui(self):
        """UIの初期化"""
        count = len(self.category_list)
        self.setWindowTitle(f"{count}個のカテゴリを一括更新")
        self.resize(400, 300)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # 説明ラベル
        help_label = QLabel(
            "変更したい項目のみ設定してください。空欄の項目は更新されません。"
        )
        help_label.setStyleSheet("color: #666666;")
        layout.addWidget(help_label)

        # 対象カテゴリ名表示
        if count <= 5:
            # 5個までは全て表示
            category_names = [category.name for category in self.category_list]
            category_text = "対象カテゴリ: " + ", ".join(category_names)
        else:
            # 5個を超える場合は一部表示
            category_names = [category.name for category in self.category_list[:5]]
            category_text = (
                f"対象カテゴリ: {', '.join(category_names)} ... 他 {count - 5} 個"
            )

        category_label = QLabel(category_text)
        category_label.setWordWrap(True)
        layout.addWidget(category_label)

        # 更新フォーム
        form_layout = QFormLayout()

        # 表示順
        self.order_group_layout = QHBoxLayout()
        self.use_order_checkbox = QCheckBox("表示順を一括設定:")
        self.use_order_checkbox.toggled.connect(self._on_use_order_toggled)
        self.order_group_layout.addWidget(self.use_order_checkbox)

        self.order_spin = QSpinBox()
        self.order_spin.setMinimum(0)
        self.order_spin.setMaximum(999)
        self.order_spin.setValue(0)
        self.order_spin.setEnabled(False)  # 初期状態では無効
        self.order_group_layout.addWidget(self.order_spin)

        form_layout.addRow("", self.order_group_layout)

        # 説明
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("変更なし")
        form_layout.addRow("説明:", self.description_edit)

        layout.addLayout(form_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_use_order_toggled(self, checked):
        """表示順チェックボックス切り替え時の処理"""
        self.order_spin.setEnabled(checked)

    def get_update_data(self):
        """更新データを取得"""
        update_data = {}

        # 表示順（チェックボックスがオンの場合のみ更新）
        if self.use_order_checkbox.isChecked():
            update_data["display_order"] = self.order_spin.value()
        else:
            update_data["display_order"] = None

        # 説明（入力があれば更新）
        description = self.description_edit.toPlainText().strip()
        update_data["description"] = description if description else None

        return update_data
