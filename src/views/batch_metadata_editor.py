from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.book import Book


class BatchMetadataEditor(QDialog):
    """
    複数の書籍のメタデータを一括編集するダイアログ。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    book_ids : list
        編集する書籍IDのリスト
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, library_controller, book_ids, parent=None):
        """
        Parameters
        ----------
        library_controller : LibraryController
            ライブラリコントローラ
        book_ids : list
            編集する書籍IDのリスト
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.library_controller = library_controller
        self.book_ids = book_ids
        self.books = [library_controller.get_book(book_id) for book_id in book_ids]

        # 無効なIDは除外
        self.books = [book for book in self.books if book is not None]
        if not self.books:
            raise ValueError("No valid books found for the provided IDs.")

        self.setWindowTitle(f"Batch Edit Metadata - {len(self.books)} books")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # レイアウトの設定
        self.layout = QVBoxLayout(self)

        # 書籍の概要を表示
        self.setup_books_summary()

        # タブウィジェットの作成
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # 基本情報タブ
        self.basic_tab = QWidget()
        self.tab_widget.addTab(self.basic_tab, "Basic Info")
        self.setup_basic_tab()

        # シリーズタブ
        self.series_tab = QWidget()
        self.tab_widget.addTab(self.series_tab, "Series")
        self.setup_series_tab()

        # カスタムメタデータタブ
        self.custom_tab = QWidget()
        self.tab_widget.addTab(self.custom_tab, "Custom Metadata")
        self.setup_custom_tab()

        # ボタン
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # OKボタンを押したときの処理
        self.accepted.connect(self.save_metadata)

    def setup_books_summary(self):
        """選択された書籍の概要を表示する。"""
        summary_group = QGroupBox("Selected Books")
        summary_layout = QVBoxLayout(summary_group)

        # 書籍の一覧をテーブルで表示
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(4)
        self.books_table.setHorizontalHeaderLabels(
            ["Title", "Author", "Publisher", "Series"]
        )
        self.books_table.setRowCount(len(self.books))
        self.books_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # 列の幅を調整
        self.books_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.books_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.books_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.books_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        # 書籍データをテーブルに設定
        for i, book in enumerate(self.books):
            # タイトル
            title_item = QTableWidgetItem(book.title or "")
            self.books_table.setItem(i, 0, title_item)

            # 著者
            author_item = QTableWidgetItem(book.author or "")
            self.books_table.setItem(i, 1, author_item)

            # 出版社
            publisher_item = QTableWidgetItem(book.publisher or "")
            self.books_table.setItem(i, 2, publisher_item)

            # シリーズ
            series_text = ""
            if book.series_id:
                series = self.library_controller.get_series(book.series_id)
                if series:
                    series_text = series.name
                    if book.series_order:
                        series_text += f" #{book.series_order}"
            series_item = QTableWidgetItem(series_text)
            self.books_table.setItem(i, 3, series_item)

        summary_layout.addWidget(self.books_table)

        # 説明ラベル
        self.summary_label = QLabel(
            f"{len(self.books)} books selected. Fields with mixed values will be marked with '*'. "
            "Empty fields will not modify the existing values."
        )
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)

        self.layout.addWidget(summary_group)

    def setup_basic_tab(self):
        """基本情報タブを設定する。"""
        layout = QVBoxLayout(self.basic_tab)

        # 基本情報フォーム
        info_group = QGroupBox("Book Information")
        info_layout = QFormLayout(info_group)

        # 著者（共通値があれば表示、なければ空）
        authors = set(book.author for book in self.books if book.author)
        author_value = next(iter(authors)) if len(authors) == 1 else ""
        author_placeholder = (
            "(Multiple values) *" if len(authors) > 1 else "Enter author name"
        )

        self.author_edit = QLineEdit(author_value)
        self.author_edit.setPlaceholderText(author_placeholder)
        info_layout.addRow("Author:", self.author_edit)

        # 出版社
        publishers = set(book.publisher for book in self.books if book.publisher)
        publisher_value = next(iter(publishers)) if len(publishers) == 1 else ""
        publisher_placeholder = (
            "(Multiple values) *" if len(publishers) > 1 else "Enter publisher name"
        )

        self.publisher_edit = QLineEdit(publisher_value)
        self.publisher_edit.setPlaceholderText(publisher_placeholder)
        info_layout.addRow("Publisher:", self.publisher_edit)

        # 読書状態
        self.status_combo = QComboBox()
        self.status_combo.addItem("-- No Change --", None)
        self.status_combo.addItem("Unread", "unread")
        self.status_combo.addItem("Reading", "reading")
        self.status_combo.addItem("Completed", "completed")
        info_layout.addRow("Set Reading Status:", self.status_combo)

        layout.addWidget(info_group)
        layout.addStretch(1)

    def setup_series_tab(self):
        """シリーズタブを設定する。"""
        layout = QVBoxLayout(self.series_tab)

        # シリーズグループ
        series_group = QGroupBox("Series Information")
        series_layout = QFormLayout(series_group)

        # シリーズ選択
        self.series_combo = QComboBox()
        self.series_combo.addItem("-- No Change --", None)
        self.series_combo.addItem("Remove from Series", -1)  # 特殊な値としての -1

        # シリーズの一覧を取得
        series_list = self.library_controller.get_all_series()
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        series_layout.addRow("Series:", self.series_combo)

        # 新しいシリーズの作成
        new_series_layout = QHBoxLayout()

        self.new_series_edit = QLineEdit()
        self.new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(self.new_series_edit)

        self.create_series_button = QPushButton("Create New Series")
        self.create_series_button.clicked.connect(self.create_new_series)
        new_series_layout.addWidget(self.create_series_button)

        series_layout.addRow("New Series:", new_series_layout)

        # シリーズ内の順番設定
        self.order_method_combo = QComboBox()
        self.order_method_combo.addItem("Do not change order", "no_change")
        self.order_method_combo.addItem("Auto-assign sequential numbers", "sequential")
        self.order_method_combo.addItem("Use specific starting number", "specific")
        series_layout.addRow("Order Method:", self.order_method_combo)

        # 開始番号の入力欄
        order_layout = QHBoxLayout()
        self.start_order_spin = QSpinBox()
        self.start_order_spin.setMinimum(1)
        self.start_order_spin.setMaximum(9999)
        self.start_order_spin.setValue(1)
        self.start_order_spin.setEnabled(False)  # 初期状態では無効
        order_layout.addWidget(self.start_order_spin)

        self.preserve_current_check = QCheckBox("Keep current order when possible")
        self.preserve_current_check.setChecked(True)
        self.preserve_current_check.setEnabled(False)  # 初期状態では無効
        order_layout.addWidget(self.preserve_current_check)

        series_layout.addRow("Starting Number:", order_layout)

        # オーダーメソッドが変更されたときのハンドラ
        self.order_method_combo.currentIndexChanged.connect(
            self.on_order_method_changed
        )

        layout.addWidget(series_group)
        layout.addStretch(1)

    def on_order_method_changed(self, index):
        """
        オーダーメソッドが変更されたときの処理。

        Parameters
        ----------
        index : int
            選択されたインデックス
        """
        method = self.order_method_combo.currentData()

        if method == "specific":
            self.start_order_spin.setEnabled(True)
            self.preserve_current_check.setEnabled(True)
        elif method == "sequential":
            self.start_order_spin.setEnabled(True)
            self.preserve_current_check.setEnabled(True)
        else:
            self.start_order_spin.setEnabled(False)
            self.preserve_current_check.setEnabled(False)

    def setup_custom_tab(self):
        """カスタムメタデータタブを設定する。"""
        layout = QVBoxLayout(self.custom_tab)

        # カスタムメタデータグループ
        custom_group = QGroupBox("Custom Metadata")
        custom_layout = QVBoxLayout(custom_group)

        # 共通のカスタムメタデータキーを取得
        all_keys = set()
        for book in self.books:
            all_keys.update(book.custom_metadata.keys())

        # キーごとの共通値を見つける
        self.common_metadata = {}
        for key in all_keys:
            values = [
                book.custom_metadata.get(key)
                for book in self.books
                if key in book.custom_metadata
            ]
            if len(set(values)) == 1 and values:
                self.common_metadata[key] = values[0]

        # フォームレイアウト
        self.custom_form_layout = QFormLayout()
        custom_layout.addLayout(self.custom_form_layout)

        # 既存のカスタムメタデータを表示
        self.custom_editors = {}

        for key in sorted(all_keys):
            if key in self.common_metadata:
                # 共通値がある場合
                edit = QLineEdit(self.common_metadata[key])
                label_text = f"{key}:"
            else:
                # 複数の値がある場合
                edit = QLineEdit()
                edit.setPlaceholderText("(Multiple values) *")
                label_text = f"{key}: *"

            self.custom_form_layout.addRow(label_text, edit)
            self.custom_editors[key] = edit

        # 新しいメタデータの追加
        add_layout = QHBoxLayout()

        self.new_key_edit = QLineEdit()
        self.new_key_edit.setPlaceholderText("New Field Name")
        add_layout.addWidget(self.new_key_edit)

        self.new_value_edit = QLineEdit()
        self.new_value_edit.setPlaceholderText("Value")
        add_layout.addWidget(self.new_value_edit)

        self.add_metadata_button = QPushButton("Add")
        self.add_metadata_button.clicked.connect(self.add_custom_metadata)
        add_layout.addWidget(self.add_metadata_button)

        custom_layout.addLayout(add_layout)

        layout.addWidget(custom_group)
        layout.addStretch(1)

    def create_new_series(self):
        """新しいシリーズを作成する。"""
        name = self.new_series_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a series name.")
            return

        # シリーズを作成
        series_id = self.library_controller.create_series(name=name)
        if series_id:
            # コンボボックスに追加
            self.series_combo.addItem(name, series_id)

            # 新しいシリーズを選択
            index = self.series_combo.findData(series_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)

            # 入力フィールドをクリア
            self.new_series_edit.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to create series.")

    def add_custom_metadata(self):
        """新しいカスタムメタデータを追加する。"""
        key = self.new_key_edit.text().strip()
        value = self.new_value_edit.text().strip()

        if not key:
            QMessageBox.warning(self, "Error", "Please enter a field name.")
            return

        if key in self.custom_editors:
            # 既に存在する場合は上書きするか確認
            result = QMessageBox.question(
                self,
                "Confirm Overwrite",
                f"Field '{key}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if result == QMessageBox.StandardButton.No:
                return

            # 既存の入力フィールドの値を更新
            self.custom_editors[key].setText(value)
        else:
            # 新しいフィールドを追加
            edit = QLineEdit(value)
            self.custom_form_layout.addRow(f"{key}:", edit)
            self.custom_editors[key] = edit

        # 入力フィールドをクリア
        self.new_key_edit.clear()
        self.new_value_edit.clear()

    def save_metadata(self):
        """メタデータの変更を保存する。"""
        # 基本情報を取得
        author = self.author_edit.text().strip()
        publisher = self.publisher_edit.text().strip()

        # 読書状態を取得
        status = self.status_combo.currentData()

        # シリーズ情報を取得
        series_id = self.series_combo.currentData()

        # 更新データを準備
        metadata_updates = {}

        # 空でないフィールドのみ追加
        if author:
            metadata_updates["author"] = author
        if publisher:
            metadata_updates["publisher"] = publisher

        # シリーズ処理
        if series_id is not None:
            if series_id == -1:  # シリーズから削除
                metadata_updates["series_id"] = None
                metadata_updates["series_order"] = None
            else:
                metadata_updates["series_id"] = series_id

                # シリーズの順番処理
                order_method = self.order_method_combo.currentData()
                if order_method == "sequential" or order_method == "specific":
                    start_order = self.start_order_spin.value()
                    preserve_current = self.preserve_current_check.isChecked()

                    # 自然順ソートを実装（数値を考慮したソート）
                    import re

                    def natural_sort_key(book):
                        """
                        series_orderを最優先し、次にタイトルの自然順でソート
                        """
                        # series_orderがNoneの場合は最大値とする（最後に表示）
                        order = (
                            book.series_order
                            if book.series_order is not None
                            else float("inf")
                        )
                        title = book.title if book.title else ""
                        # 数値部分を抽出して数値として扱う
                        title_key = [
                            int(c) if c.isdigit() else c.lower()
                            for c in re.split(r"(\d+)", title)
                        ]
                        return (order, title_key)

                    if preserve_current:
                        # 現在の順番を維持しつつソート
                        sorted_books = sorted(
                            self.books,
                            key=lambda b: (
                                b.series_id != series_id,
                                natural_sort_key(b),
                            ),
                        )
                    else:
                        # タイトルでソート（自然順）
                        sorted_books = sorted(self.books, key=natural_sort_key)

                    # 各本に順番を割り当て
                    current_order = start_order
                    for book in sorted_books:
                        if book.id in self.book_ids:
                            # このバッチ処理でのみ順番を設定
                            self.library_controller.update_book_metadata(
                                book.id, series_id=series_id, series_order=current_order
                            )
                            current_order += 1

        # カスタムメタデータを追加
        for key, edit in self.custom_editors.items():
            value = edit.text().strip()
            if value:  # 空でない場合のみ更新
                metadata_updates[key] = value

        # 複数書籍のメタデータを一括更新
        if metadata_updates:
            self.library_controller.batch_update_metadata(
                self.book_ids, metadata_updates
            )

        # 読書状態を更新（もし指定されていれば）
        if status is not None:
            for book_id in self.book_ids:
                self.library_controller.update_book_progress(book_id, status=status)
