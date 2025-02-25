import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class BatchBookUpdateDialog(QDialog):
    """書籍の一括更新ダイアログ"""

    def __init__(self, library_manager, books, parent=None):
        super().__init__(parent)
        self.library_manager = library_manager
        self.db_manager = library_manager.db
        self.books = books

        self._init_ui()

    def _init_ui(self):
        """UIの初期化"""
        count = len(self.books)
        self.setWindowTitle(f"{count}冊の書籍を一括更新")
        self.resize(600, 500)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # 説明ラベル
        help_label = QLabel(
            "変更したい項目のみ設定してください。空欄の項目は更新されません。"
        )
        help_label.setStyleSheet("color: #666666;")
        layout.addWidget(help_label)

        # 対象書籍の表示
        if count <= 5:
            # 5冊までは全て表示
            book_titles = [book.title for book in self.books]
            book_text = "対象書籍: " + ", ".join(book_titles)
        else:
            # 5冊を超える場合は一部表示
            book_titles = [book.title for book in self.books[:5]]
            book_text = f"対象書籍: {', '.join(book_titles)} ... 他 {count - 5} 冊"

        book_label = QLabel(book_text)
        book_label.setWordWrap(True)
        layout.addWidget(book_label)

        # タブウィジェット
        tab_widget = QTabWidget()

        # 基本情報タブ
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "基本情報")

        # タグ・シリーズタブ
        tag_series_tab = self._create_tag_series_tab()
        tab_widget.addTab(tag_series_tab, "タグ・シリーズ")

        # 読書状態タブ
        reading_tab = self._create_reading_tab()
        tab_widget.addTab(reading_tab, "読書状態")

        layout.addWidget(tab_widget)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_basic_tab(self):
        """基本情報タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form_layout = QFormLayout()

        # 著者
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("変更なし")
        form_layout.addRow("著者:", self.author_edit)

        # 出版社
        self.publisher_edit = QLineEdit()
        self.publisher_edit.setPlaceholderText("変更なし")
        form_layout.addRow("出版社:", self.publisher_edit)

        # 出版日
        self.publication_date_edit = QLineEdit()
        self.publication_date_edit.setPlaceholderText("変更なし (YYYY-MM-DD形式)")
        form_layout.addRow("出版日:", self.publication_date_edit)

        # 評価
        self.use_rating_check = QCheckBox("評価を設定")
        self.use_rating_check.toggled.connect(
            lambda checked: self.rating_spin.setEnabled(checked)
        )

        rating_layout = QHBoxLayout()
        rating_layout.addWidget(self.use_rating_check)

        self.rating_spin = QSpinBox()
        self.rating_spin.setMinimum(0)
        self.rating_spin.setMaximum(5)
        self.rating_spin.setSingleStep(1)
        self.rating_spin.setEnabled(False)
        rating_layout.addWidget(self.rating_spin)

        form_layout.addRow("評価:", rating_layout)

        # お気に入り
        self.use_favorite_check = QCheckBox("お気に入り設定を変更")
        self.use_favorite_check.toggled.connect(
            lambda checked: self.favorite_combo.setEnabled(checked)
        )

        favorite_layout = QHBoxLayout()
        favorite_layout.addWidget(self.use_favorite_check)

        self.favorite_combo = QComboBox()
        self.favorite_combo.addItems(["お気に入りに追加", "お気に入りから削除"])
        self.favorite_combo.setEnabled(False)
        favorite_layout.addWidget(self.favorite_combo)

        form_layout.addRow("お気に入り:", favorite_layout)

        layout.addLayout(form_layout)

        # 余白を追加
        layout.addStretch()

        return tab

    def _create_tag_series_tab(self):
        """タグ・シリーズタブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # タグ操作エリア
        tag_group_layout = QVBoxLayout()
        tag_label = QLabel("タグ操作:")
        tag_group_layout.addWidget(tag_label)

        # タグの追加
        add_tag_label = QLabel("追加するタグ:")
        tag_group_layout.addWidget(add_tag_label)

        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        tag_group_layout.addWidget(self.tag_list)

        # タグの削除
        remove_tag_label = QLabel("削除するタグ:")
        tag_group_layout.addWidget(remove_tag_label)

        self.remove_tag_list = QListWidget()
        self.remove_tag_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        tag_group_layout.addWidget(self.remove_tag_list)

        layout.addLayout(tag_group_layout)

        # シリーズ操作エリア
        series_group_layout = QVBoxLayout()
        series_label = QLabel("シリーズ操作:")
        series_group_layout.addWidget(series_label)

        # シリーズ設定
        self.use_series_check = QCheckBox("シリーズを設定")
        self.use_series_check.toggled.connect(
            lambda checked: self.series_combo.setEnabled(checked)
        )

        series_combo_layout = QHBoxLayout()
        series_combo_layout.addWidget(self.use_series_check)

        self.series_combo = QComboBox()
        self.series_combo.setEnabled(False)
        self.series_combo.setEditable(True)
        series_combo_layout.addWidget(self.series_combo)

        series_group_layout.addLayout(series_combo_layout)

        # 巻数設定
        self.use_volume_check = QCheckBox("巻数を設定")
        self.use_volume_check.toggled.connect(
            lambda checked: self.volume_spin.setEnabled(checked)
        )

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.use_volume_check)

        self.volume_spin = QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(9999)
        self.volume_spin.setSpecialValueText("巻数なし")  # 0の場合は「巻数なし」
        self.volume_spin.setEnabled(False)
        volume_layout.addWidget(self.volume_spin)

        series_group_layout.addLayout(volume_layout)

        layout.addLayout(series_group_layout)

        # タグとシリーズデータの読み込み
        self._load_tags_and_series()

        return tab

    def _create_reading_tab(self):
        """読書状態タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form_layout = QFormLayout()

        # 読書状態
        self.use_reading_status_check = QCheckBox("読書状態を設定")
        self.use_reading_status_check.toggled.connect(
            lambda checked: self.reading_status_combo.setEnabled(checked)
        )

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.use_reading_status_check)

        self.reading_status_combo = QComboBox()
        self.reading_status_combo.addItems(["未読", "読書中", "読了"])
        self.reading_status_combo.setEnabled(False)
        status_layout.addWidget(self.reading_status_combo)

        form_layout.addRow("読書状態:", status_layout)

        # 現在のページ
        self.use_current_page_check = QCheckBox("現在のページを設定")
        self.use_current_page_check.toggled.connect(
            lambda checked: self.current_page_spin.setEnabled(checked)
        )

        page_layout = QHBoxLayout()
        page_layout.addWidget(self.use_current_page_check)

        self.current_page_spin = QSpinBox()
        self.current_page_spin.setMinimum(0)
        self.current_page_spin.setMaximum(9999)
        self.current_page_spin.setEnabled(False)
        page_layout.addWidget(self.current_page_spin)

        form_layout.addRow("現在のページ:", page_layout)

        # コメント
        self.comments_edit = QTextEdit()
        self.comments_edit.setPlaceholderText("変更なし")
        form_layout.addRow("コメント:", self.comments_edit)

        layout.addLayout(form_layout)

        # 余白を追加
        layout.addStretch()

        return tab

    def _load_tags_and_series(self):
        """タグとシリーズデータの読み込み"""
        # タグの読み込み
        all_tags = self.db_manager.get_all_tags()

        for tag in all_tags:
            self.tag_list.addItem(tag.name)
            self.remove_tag_list.addItem(tag.name)

        # シリーズの読み込み
        all_series = self.db_manager.get_all_series()

        # 「なし」の選択肢を追加
        self.series_combo.addItem("なし")

        for series in all_series:
            self.series_combo.addItem(series.name)

    def get_update_data(self):
        """更新データを取得"""
        update_data = {}

        # 基本情報
        author = self.author_edit.text().strip()
        if author:
            update_data["author"] = author

        publisher = self.publisher_edit.text().strip()
        if publisher:
            update_data["publisher"] = publisher

        publication_date = self.publication_date_edit.text().strip()
        if publication_date:
            update_data["publication_date"] = publication_date

        if self.use_rating_check.isChecked():
            update_data["rating"] = self.rating_spin.value()

        if self.use_favorite_check.isChecked():
            update_data["is_favorite"] = (
                self.favorite_combo.currentIndex() == 0
            )  # 0はお気に入りに追加

        # タグ操作
        add_tags = []
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item.isSelected():
                add_tags.append(item.text())

        remove_tags = []
        for i in range(self.remove_tag_list.count()):
            item = self.remove_tag_list.item(i)
            if item.isSelected():
                remove_tags.append(item.text())

        if add_tags:
            update_data["add_tags"] = add_tags

        if remove_tags:
            update_data["remove_tags"] = remove_tags

        # シリーズ操作
        if self.use_series_check.isChecked():
            series_name = self.series_combo.currentText()
            if series_name == "なし":
                update_data["series_name"] = ""  # 空文字で削除
            else:
                update_data["series_name"] = series_name

        if self.use_volume_check.isChecked():
            volume = self.volume_spin.value()
            update_data["volume_number"] = None if volume == 0 else volume

        # 読書状態
        if self.use_reading_status_check.isChecked():
            update_data["reading_status"] = self.reading_status_combo.currentText()

        if self.use_current_page_check.isChecked():
            update_data["current_page"] = self.current_page_spin.value()

        comments = self.comments_edit.toPlainText().strip()
        if comments:
            update_data["comments"] = comments

        return update_data

    def accept(self):
        """OKボタンが押されたときの処理"""
        update_data = self.get_update_data()

        # 更新するデータがあるか確認
        if not update_data:
            QMessageBox.warning(self, "入力エラー", "更新するデータがありません。")
            return

        super().accept()


def apply_batch_update(library_manager, books, update_data):
    """複数の書籍に一括更新を適用する"""
    # 実際に更新するデータを作成（一括処理用の特殊フィールドを考慮）
    special_fields = ["add_tags", "remove_tags"]

    for book in books:
        # 通常の更新データ
        book_update = {}
        for key, value in update_data.items():
            if key not in special_fields:
                book_update[key] = value

        # タグの追加・削除処理
        if book_update or "add_tags" in update_data or "remove_tags" in update_data:
            # まず通常のフィールド値を更新
            if book_update:
                library_manager.update_book_metadata(book.id, book_update)

            # 次にタグの追加・削除処理
            if "add_tags" in update_data or "remove_tags" in update_data:
                # 現在のタグを取得
                current_book = library_manager.db.get_book(book.id)
                current_tags = [tag.name for tag in current_book.tags]

                # タグを追加
                if "add_tags" in update_data:
                    for tag_name in update_data["add_tags"]:
                        if tag_name not in current_tags:
                            current_tags.append(tag_name)

                # タグを削除
                if "remove_tags" in update_data:
                    current_tags = [
                        tag
                        for tag in current_tags
                        if tag not in update_data["remove_tags"]
                    ]

                # タグを更新
                library_manager.update_book_metadata(book.id, {"tags": current_tags})

    # 変更が適用された書籍数を返す
    return len(books)
