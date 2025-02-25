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
    QMenu,
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
        self.resize(700, 500)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # ヘルプテキスト
        help_label = QLabel(
            "Ctrlキーを押しながらクリックで複数選択、Shiftキーで範囲選択ができます"
        )
        help_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(help_label)

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

        # 複数選択を可能にする
        self.series_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.series_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self.series_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.series_table.doubleClicked.connect(self._edit_series)

        # コンテキストメニュー
        self.series_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.series_table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.series_table)

        # 選択情報ラベル
        self.selection_info_label = QLabel("0 シリーズ選択中")
        layout.addWidget(self.selection_info_label)

        # シリーズテーブルの選択変更時のシグナル接続
        self.series_table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        # 操作ボタンのレイアウト
        button_layout = QHBoxLayout()

        # 新規シリーズ追加ボタン
        add_button = QPushButton("新規シリーズ")
        add_button.clicked.connect(self._add_series)
        button_layout.addWidget(add_button)

        button_layout.addStretch()

        # 編集・削除ボタン
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self._edit_series)
        self.edit_button.setEnabled(False)  # 初期状態では無効
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self._delete_series)
        self.delete_button.setEnabled(False)  # 初期状態では無効
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        # 一括操作レイアウト
        batch_layout = QHBoxLayout()

        # 一括操作ボタン - バッチ更新ボタン
        self.batch_update_button = QPushButton("選択したシリーズの一括更新...")
        self.batch_update_button.clicked.connect(self._batch_update_series)
        self.batch_update_button.setEnabled(False)  # 初期状態では無効
        batch_layout.addWidget(self.batch_update_button)

        # 一括削除ボタン
        self.batch_delete_button = QPushButton("選択したシリーズを削除")
        self.batch_delete_button.clicked.connect(self._delete_selected_series)
        self.batch_delete_button.setEnabled(False)  # 初期状態では無効
        batch_layout.addWidget(self.batch_delete_button)

        layout.addLayout(batch_layout)

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

        # 選択情報を更新
        self._update_selection_info()

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

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 複数選択されている場合
        if len(selected_rows) > 1:
            QMessageBox.warning(
                self, "選択エラー", "編集は一度に1つのシリーズのみ可能です。"
            )
            return

        # 選択された行のインデックス
        row = list(selected_rows)[0]

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

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 複数選択されている場合
        if len(selected_rows) > 1:
            self._delete_selected_series()
            return

        # 選択された行のインデックス
        row = list(selected_rows)[0]

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

    def _delete_selected_series(self):
        """選択した複数のシリーズを削除"""
        selected_indexes = self.series_table.selectedIndexes()
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

        # 選択したシリーズのリスト
        selected_series = [self.series_list[row] for row in selected_rows]

        # 使用数を合計
        total_books_count = sum(len(series.books) for series in selected_series)

        # 削除前の確認
        if len(selected_series) == 1:
            msg = f"シリーズ「{selected_series[0].name}」を削除しますか？"
        else:
            msg = f"選択した{len(selected_series)}個のシリーズを削除しますか？"

            # シリーズ名を最大5個まで表示
            series_names = [series.name for series in selected_series[:5]]
            if len(selected_series) > 5:
                series_names.append(f"...他{len(selected_series) - 5}個")
            msg += f"\n\n- " + "\n- ".join(series_names)

        if total_books_count > 0:
            msg += f"\n\nこれらのシリーズは合計{total_books_count}冊の書籍に使用されています。"
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
            for series in selected_series:
                self.db_manager.delete_series(series.id)
                logging.info(f"シリーズを削除しました: {series.name}")

            # リストを更新
            self._load_series()

            logging.info(f"{len(selected_series)}個のシリーズを削除しました")

    def _batch_update_series(self):
        """選択した複数のシリーズの一括更新"""
        selected_indexes = self.series_table.selectedIndexes()
        if not selected_indexes:
            return

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        if not selected_rows:
            return

        # 選択したシリーズのリスト
        selected_series = [self.series_list[row] for row in selected_rows]

        # バッチ更新ダイアログを表示
        dialog = SeriesBatchUpdateDialog(selected_series, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新データを取得
            update_data = dialog.get_update_data()

            # 更新するフィールドがあるか確認
            if not any(update_data.values()):
                return

            # 各シリーズを更新
            for series in selected_series:
                # 実際に更新するデータを作成（空でないフィールドのみ）
                series_update = {}
                for key, value in update_data.items():
                    if value is not None:  # Noneでない値のみ更新
                        series_update[key] = value

                if series_update:
                    self.db_manager.update_series(series.id, series_update)

            # リストを更新
            self._load_series()

            count_text = (
                f"{len(selected_series)}個の" if len(selected_series) > 1 else ""
            )
            logging.info(f"{count_text}シリーズを一括更新しました")

    def _show_context_menu(self, position):
        """コンテキストメニューを表示"""
        selected_indexes = self.series_table.selectedIndexes()
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
            edit_action.triggered.connect(self._edit_series)

            menu.addSeparator()

            delete_action = menu.addAction("削除")
            delete_action.triggered.connect(self._delete_series)
        else:
            # 複数選択の場合
            batch_update_action = menu.addAction(
                f"選択した{len(selected_rows)}個のシリーズを一括更新..."
            )
            batch_update_action.triggered.connect(self._batch_update_series)

            menu.addSeparator()

            delete_action = menu.addAction(
                f"選択した{len(selected_rows)}個のシリーズを削除"
            )
            delete_action.triggered.connect(self._delete_selected_series)

        # メニューを表示
        menu.exec(self.series_table.viewport().mapToGlobal(position))

    def _on_selection_changed(self):
        """選択変更時の処理"""
        selected_indexes = self.series_table.selectedIndexes()

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # ボタンの有効/無効を設定
        has_selection = len(selected_rows) > 0
        is_single_selection = len(selected_rows) == 1
        is_multiple_selection = len(selected_rows) > 1

        self.edit_button.setEnabled(is_single_selection)
        self.delete_button.setEnabled(has_selection)
        self.batch_update_button.setEnabled(is_multiple_selection)
        self.batch_delete_button.setEnabled(is_multiple_selection)

        # 選択情報を更新
        self._update_selection_info()

    def _update_selection_info(self):
        """選択情報ラベルの更新"""
        selected_indexes = self.series_table.selectedIndexes()

        # 選択行の重複を排除して取得
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 選択情報を表示
        count = len(selected_rows)
        if count == 0:
            self.selection_info_label.setText("0 シリーズ選択中")
        elif count == 1:
            series = self.series_list[list(selected_rows)[0]]
            self.selection_info_label.setText(f"1 シリーズ選択中: {series.name}")
        else:
            self.selection_info_label.setText(f"{count} シリーズ選択中")


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


class SeriesBatchUpdateDialog(QDialog):
    """シリーズ一括更新ダイアログ"""

    # シリーズのカテゴリオプション
    CATEGORY_OPTIONS = [
        "変更なし",
        "",
        "漫画",
        "小説",
        "技術書",
        "雑誌",
        "ビジネス",
        "その他",
    ]

    def __init__(self, series_list, parent=None):
        super().__init__(parent)
        self.series_list = series_list

        self._init_ui()

    def _init_ui(self):
        """UIの初期化"""
        count = len(self.series_list)
        self.setWindowTitle(f"{count}個のシリーズを一括更新")
        self.resize(400, 300)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # 説明ラベル
        help_label = QLabel(
            "変更したい項目のみ設定してください。空欄の項目は更新されません。"
        )
        help_label.setStyleSheet("color: #666666;")
        layout.addWidget(help_label)

        # 対象シリーズ名表示
        if count <= 5:
            # 5個までは全て表示
            series_names = [series.name for series in self.series_list]
            series_text = "対象シリーズ: " + ", ".join(series_names)
        else:
            # 5個を超える場合は一部表示
            series_names = [series.name for series in self.series_list[:5]]
            series_text = (
                f"対象シリーズ: {', '.join(series_names)} ... 他 {count - 5} 個"
            )

        series_label = QLabel(series_text)
        series_label.setWordWrap(True)
        layout.addWidget(series_label)

        # 更新フォーム
        form_layout = QFormLayout()

        # 著者
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("変更なし")
        form_layout.addRow("著者:", self.author_edit)

        # 出版社
        self.publisher_edit = QLineEdit()
        self.publisher_edit.setPlaceholderText("変更なし")
        form_layout.addRow("出版社:", self.publisher_edit)

        # カテゴリ
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.CATEGORY_OPTIONS)
        form_layout.addRow("カテゴリ:", self.category_combo)

        layout.addLayout(form_layout)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_update_data(self):
        """更新データを取得"""
        update_data = {}

        # 著者（入力があれば更新）
        author = self.author_edit.text().strip()
        update_data["author"] = author if author else None

        # 出版社（入力があれば更新）
        publisher = self.publisher_edit.text().strip()
        update_data["publisher"] = publisher if publisher else None

        # カテゴリ（「変更なし」以外を選択した場合に更新）
        category_index = self.category_combo.currentIndex()
        if category_index > 0:  # 0は「変更なし」
            update_data["category"] = self.category_combo.currentText()
        else:
            update_data["category"] = None

        return update_data
