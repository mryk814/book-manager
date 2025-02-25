import logging
import os

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TagSelector(QWidget):
    """タグ選択ウィジェット"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_tags = []

        # レイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # タグリスト
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.tag_list)

        # 新規タグ追加
        add_layout = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("新しいタグ...")
        add_layout.addWidget(self.new_tag_edit)

        add_button = QPushButton("追加")
        add_button.clicked.connect(self._add_new_tag)
        add_layout.addWidget(add_button)

        layout.addLayout(add_layout)

        # タグの読み込み
        self._load_tags()

    def _load_tags(self):
        """タグを読み込む"""
        self.tag_list.clear()

        # 全タグを取得
        all_tags = self.db_manager.get_all_tags()

        for tag in all_tags:
            item = QListWidgetItem(tag.name)
            # 選択済みタグにチェック
            if tag.name in self.selected_tags:
                item.setSelected(True)
            self.tag_list.addItem(item)

    def _add_new_tag(self):
        """新しいタグを追加"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return

        # タグを追加または取得
        tag = self.db_manager.get_or_create_tag(tag_name)

        # リストを更新
        self._load_tags()

        # 新しいタグを選択
        self.selected_tags.append(tag_name)

        # 選択状態を反映
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item.text() == tag_name:
                item.setSelected(True)

        # 入力欄をクリア
        self.new_tag_edit.clear()

    def set_selected_tags(self, tags):
        """選択中のタグを設定"""
        self.selected_tags = tags.copy() if tags else []
        self._load_tags()

    def get_selected_tags(self):
        """選択されたタグを取得"""
        selected_tags = []
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item.isSelected():
                selected_tags.append(item.text())
        return selected_tags


class SeriesSelector(QWidget):
    """シリーズ選択ウィジェット"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        # レイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # シリーズの選択
        form_layout = QFormLayout()

        # シリーズコンボボックス
        self.series_combo = QComboBox()
        self.series_combo.setEditable(True)
        self.series_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        form_layout.addRow("シリーズ:", self.series_combo)

        # 巻数スピンボックス
        self.volume_spin = QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(9999)
        self.volume_spin.setSpecialValueText("巻数なし")  # 0の場合は「巻数なし」
        form_layout.addRow("巻数:", self.volume_spin)

        layout.addLayout(form_layout)

        # シリーズの読み込み
        self._load_series()

    def _load_series(self):
        """シリーズを読み込む"""
        self.series_combo.clear()

        # 「なし」の選択肢を追加
        self.series_combo.addItem("なし")

        # 全シリーズを取得
        all_series = self.db_manager.get_all_series()

        for series in all_series:
            self.series_combo.addItem(series.name)

    def set_series(self, series_name, volume_number=None):
        """シリーズと巻数を設定"""
        # シリーズ設定
        if series_name:
            index = self.series_combo.findText(series_name)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)
            else:
                # リストにない場合は追加
                self.series_combo.addItem(series_name)
                self.series_combo.setCurrentText(series_name)
        else:
            self.series_combo.setCurrentIndex(0)  # 「なし」を選択

        # 巻数設定
        if volume_number is not None:
            self.volume_spin.setValue(volume_number)
        else:
            self.volume_spin.setValue(0)

    def get_series(self):
        """シリーズ名と巻数を取得"""
        series_name = self.series_combo.currentText()
        if series_name == "なし":
            series_name = ""

        volume_number = self.volume_spin.value()
        if volume_number == 0:
            volume_number = None

        return series_name, volume_number


class MetadataDialog(QDialog):
    """書籍メタデータ編集ダイアログ"""

    def __init__(self, library_manager, book=None, parent=None):
        super().__init__(parent)
        self.library_manager = library_manager
        self.db_manager = library_manager.db
        self.book = book

        # UIの初期化
        self._init_ui()

        # 書籍データの読み込み
        if book:
            self._load_book_data()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("書籍メタデータ編集")
        self.resize(500, 600)

        # メインレイアウト
        layout = QVBoxLayout(self)

        # タブウィジェット
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 基本情報タブ
        basic_tab = QWidget()
        self.tab_widget.addTab(basic_tab, "基本情報")
        self._create_basic_tab(basic_tab)

        # タグとシリーズタブ
        categories_tab = QWidget()
        self.tab_widget.addTab(categories_tab, "分類")
        self._create_categories_tab(categories_tab)

        # コメントタブ
        comments_tab = QWidget()
        self.tab_widget.addTab(comments_tab, "コメント")
        self._create_comments_tab(comments_tab)

        # ファイル情報タブ
        file_tab = QWidget()
        self.tab_widget.addTab(file_tab, "ファイル")
        self._create_file_tab(file_tab)

        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_basic_tab(self, tab):
        """基本情報タブの作成"""
        layout = QVBoxLayout(tab)

        # フォームレイアウト
        form_layout = QFormLayout()

        # タイトル
        self.title_edit = QLineEdit()
        form_layout.addRow("タイトル:", self.title_edit)

        # 著者
        self.author_edit = QLineEdit()
        form_layout.addRow("著者:", self.author_edit)

        # 出版社
        self.publisher_edit = QLineEdit()
        form_layout.addRow("出版社:", self.publisher_edit)

        # 出版日
        self.publication_date_edit = QLineEdit()
        form_layout.addRow("出版日:", self.publication_date_edit)

        # ページ数
        self.page_count_spin = QSpinBox()
        self.page_count_spin.setMinimum(0)
        self.page_count_spin.setMaximum(9999)
        form_layout.addRow("ページ数:", self.page_count_spin)

        # 評価
        self.rating_spin = QDoubleSpinBox()
        self.rating_spin.setMinimum(0.0)
        self.rating_spin.setMaximum(5.0)
        self.rating_spin.setSingleStep(0.5)
        form_layout.addRow("評価:", self.rating_spin)

        # 読書状態
        self.reading_status_combo = QComboBox()
        self.reading_status_combo.addItems(["未読", "読書中", "読了"])
        form_layout.addRow("読書状態:", self.reading_status_combo)

        # お気に入り
        self.is_favorite_check = QCheckBox("お気に入り")
        form_layout.addRow("", self.is_favorite_check)

        layout.addLayout(form_layout)

    def _create_categories_tab(self, tab):
        """分類タブの作成"""
        layout = QVBoxLayout(tab)

        # タグセクション
        tag_group = QGroupBox("タグ")
        tag_layout = QVBoxLayout(tag_group)

        # タグセレクタ
        self.tag_selector = TagSelector(self.db_manager)
        tag_layout.addWidget(self.tag_selector)

        layout.addWidget(tag_group)

        # シリーズセクション
        series_group = QGroupBox("シリーズ")
        series_layout = QVBoxLayout(series_group)

        # シリーズセレクタ
        self.series_selector = SeriesSelector(self.db_manager)
        series_layout.addWidget(self.series_selector)

        layout.addWidget(series_group)

    def _create_comments_tab(self, tab):
        """コメントタブの作成"""
        layout = QVBoxLayout(tab)

        # コメントテキストエリア
        self.comments_edit = QTextEdit()
        layout.addWidget(self.comments_edit)

    def _create_file_tab(self, tab):
        """ファイル情報タブの作成"""
        layout = QVBoxLayout(tab)

        # ファイル情報フォーム
        form_layout = QFormLayout()

        # ファイルパス
        file_path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_path_layout.addWidget(self.file_path_edit)

        browse_button = QPushButton("参照...")
        browse_button.clicked.connect(self._browse_file)
        file_path_layout.addWidget(browse_button)

        form_layout.addRow("ファイルパス:", file_path_layout)

        # サムネイル
        thumbnail_layout = QHBoxLayout()
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(150, 200)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #cccccc;"
        )
        thumbnail_layout.addWidget(self.thumbnail_label)

        thumbnail_buttons_layout = QVBoxLayout()

        update_thumbnail_button = QPushButton("表紙を更新")
        update_thumbnail_button.clicked.connect(self._update_thumbnail)
        thumbnail_buttons_layout.addWidget(update_thumbnail_button)

        thumbnail_buttons_layout.addStretch()
        thumbnail_layout.addLayout(thumbnail_buttons_layout)

        form_layout.addRow("表紙:", thumbnail_layout)

        layout.addLayout(form_layout)

        # スペーサー
        layout.addStretch()

    def _load_book_data(self):
        """書籍データの読み込み"""
        if not self.book:
            return

        # 基本情報の設定
        self.title_edit.setText(self.book.title or "")
        self.author_edit.setText(self.book.author or "")
        self.publisher_edit.setText(self.book.publisher or "")
        self.publication_date_edit.setText(self.book.publication_date or "")

        if self.book.page_count is not None:
            self.page_count_spin.setValue(self.book.page_count)

        if self.book.rating is not None:
            self.rating_spin.setValue(self.book.rating)

        # 読書状態の設定
        if self.book.reading_status:
            index = self.reading_status_combo.findText(self.book.reading_status)
            if index >= 0:
                self.reading_status_combo.setCurrentIndex(index)

        # お気に入りの設定
        self.is_favorite_check.setChecked(self.book.is_favorite)

        # タグの設定
        tags = [tag.name for tag in self.book.tags]
        self.tag_selector.set_selected_tags(tags)

        # シリーズの設定
        series_name = None
        if self.book.series and len(self.book.series) > 0:
            series_name = self.book.series[0].name
        self.series_selector.set_series(series_name, self.book.volume_number)

        # コメントの設定
        self.comments_edit.setText(self.book.comments or "")

        # ファイル情報の設定
        self.file_path_edit.setText(self.book.file_path or "")

        # サムネイルの設定
        if self.book.thumbnail_path and os.path.exists(self.book.thumbnail_path):
            pixmap = QPixmap(self.book.thumbnail_path)
            pixmap = pixmap.scaled(
                150,
                200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setText("No Cover")

    def _browse_file(self):
        """ファイル参照ダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "PDFファイルの選択", "", "PDFファイル (*.pdf)"
        )

        if file_path:
            self.file_path_edit.setText(file_path)

            # PDFからメタデータを抽出して自動入力
            metadata = self.library_manager.pdf.extract_metadata(file_path)
            if metadata:
                if (
                    "title" in metadata
                    and metadata["title"]
                    and not self.title_edit.text()
                ):
                    self.title_edit.setText(metadata["title"])

                if (
                    "author" in metadata
                    and metadata["author"]
                    and not self.author_edit.text()
                ):
                    self.author_edit.setText(metadata["author"])

                if "page_count" in metadata and metadata["page_count"]:
                    self.page_count_spin.setValue(metadata["page_count"])

                if "thumbnail_path" in metadata and metadata["thumbnail_path"]:
                    pixmap = QPixmap(metadata["thumbnail_path"])
                    pixmap = pixmap.scaled(
                        150,
                        200,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.thumbnail_label.setPixmap(pixmap)

    def _update_thumbnail(self):
        """サムネイルを更新"""
        file_path = self.file_path_edit.text()
        if not file_path or not os.path.exists(file_path):
            return

        # PDFからサムネイルを生成
        pdf_doc = self.library_manager.pdf.get_document(file_path)
        if pdf_doc:
            thumbnail_path = self.library_manager.pdf.generate_thumbnail(
                pdf_doc, file_path
            )
            if thumbnail_path:
                pixmap = QPixmap(thumbnail_path)
                pixmap = pixmap.scaled(
                    150,
                    200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.thumbnail_label.setPixmap(pixmap)
            pdf_doc.close()

    def get_metadata(self):
        """編集されたメタデータを取得"""
        metadata = {}

        # 基本情報
        metadata["title"] = self.title_edit.text()
        metadata["author"] = self.author_edit.text()
        metadata["publisher"] = self.publisher_edit.text()
        metadata["publication_date"] = self.publication_date_edit.text()
        metadata["page_count"] = self.page_count_spin.value()
        metadata["rating"] = self.rating_spin.value()
        metadata["reading_status"] = self.reading_status_combo.currentText()
        metadata["is_favorite"] = self.is_favorite_check.isChecked()

        # タグとシリーズ
        metadata["tags"] = self.tag_selector.get_selected_tags()
        series_name, volume_number = self.series_selector.get_series()
        metadata["series_name"] = series_name
        metadata["volume_number"] = volume_number

        # コメント
        metadata["comments"] = self.comments_edit.toPlainText()

        # ファイル情報
        file_path = self.file_path_edit.text()
        if file_path and file_path != self.book.file_path:
            metadata["file_path"] = file_path

        return metadata
