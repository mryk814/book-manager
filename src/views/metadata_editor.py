from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
    QPushButton,
    QTabWidget,
    QWidget,
    QMessageBox,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QByteArray


class MetadataEditor(QDialog):
    """
    書籍のメタデータを編集するダイアログ。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    book_id : int
        編集する書籍のID
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, library_controller, book_id, parent=None):
        """
        Parameters
        ----------
        library_controller : LibraryController
            ライブラリコントローラ
        book_id : int
            編集する書籍のID
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.library_controller = library_controller
        self.book_id = book_id
        self.book = library_controller.get_book(book_id)

        if not self.book:
            raise ValueError(f"Book with ID {book_id} not found.")

        self.setWindowTitle(f"Edit Metadata - {self.book.title}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # レイアウトの設定
        self.layout = QVBoxLayout(self)

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

    def setup_basic_tab(self):
        """基本情報タブを設定する。"""
        layout = QVBoxLayout(self.basic_tab)

        # 表紙と基本情報を横に並べる
        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)

        # 表紙画像
        cover_group = QGroupBox("Cover")
        cover_layout = QVBoxLayout(cover_group)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(150, 200)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QLabel.Shape.Box)

        cover_data = self.book.get_cover_image()
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)

        cover_layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.regenerate_cover_button = QPushButton("Regenerate from PDF")
        self.regenerate_cover_button.clicked.connect(self.regenerate_cover)
        cover_layout.addWidget(self.regenerate_cover_button)

        top_layout.addWidget(cover_group)

        # 基本情報フォーム
        info_group = QGroupBox("Book Information")
        info_layout = QFormLayout(info_group)

        # タイトル
        self.title_edit = QLineEdit(self.book.title or "")
        info_layout.addRow("Title:", self.title_edit)

        # 著者
        self.author_edit = QLineEdit(self.book.author or "")
        info_layout.addRow("Author:", self.author_edit)

        # 出版社
        self.publisher_edit = QLineEdit(self.book.publisher or "")
        info_layout.addRow("Publisher:", self.publisher_edit)

        # ファイルパス（読み取り専用）
        self.path_edit = QLineEdit(self.book.file_path)
        self.path_edit.setReadOnly(True)
        info_layout.addRow("File Path:", self.path_edit)

        # 読書状態
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Unread", "Reading", "Completed"])
        current_status = "Unread"
        if self.book.status == self.book.STATUS_READING:
            current_status = "Reading"
        elif self.book.status == self.book.STATUS_COMPLETED:
            current_status = "Completed"
        self.status_combo.setCurrentText(current_status)
        info_layout.addRow("Reading Status:", self.status_combo)

        # 読書進捗情報
        progress_text = f"{self.book.current_page + 1} / {self.book.total_pages}"
        self.progress_label = QLabel(progress_text)
        info_layout.addRow("Current Page:", self.progress_label)

        top_layout.addWidget(info_group)
        top_layout.setStretch(1, 1)  # 情報グループを伸縮させる

    def setup_series_tab(self):
        """シリーズタブを設定する。"""
        layout = QVBoxLayout(self.series_tab)

        # シリーズグループ
        series_group = QGroupBox("Series Information")
        series_layout = QFormLayout(series_group)

        # シリーズ選択
        self.series_combo = QComboBox()
        self.series_combo.addItem("-- None --", None)

        # シリーズの一覧を取得
        series_list = self.library_controller.get_all_series()
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        # 現在のシリーズを選択
        if self.book.series_id:
            index = self.series_combo.findData(self.book.series_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)

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

        # シリーズ内の順番
        self.order_spinbox = QSpinBox()
        self.order_spinbox.setMinimum(0)
        self.order_spinbox.setMaximum(999)
        self.order_spinbox.setValue(self.book.series_order or 0)
        self.order_spinbox.setSpecialValueText("Auto")  # 0は「自動」を意味する
        series_layout.addRow("Order in Series:", self.order_spinbox)

        layout.addWidget(series_group)

        # シリーズの情報表示
        self.series_info_group = QGroupBox("Current Series Books")
        self.series_info_layout = QVBoxLayout(self.series_info_group)

        self.series_info_label = QLabel("Select a series to see other books.")
        self.series_info_layout.addWidget(self.series_info_label)

        layout.addWidget(self.series_info_group)

        # シリーズが変更されたときに情報を更新
        self.series_combo.currentIndexChanged.connect(self.update_series_info)

        # 初期情報を表示
        self.update_series_info()

    def setup_custom_tab(self):
        """カスタムメタデータタブを設定する。"""
        layout = QVBoxLayout(self.custom_tab)

        # カスタムメタデータグループ
        custom_group = QGroupBox("Custom Metadata")
        custom_layout = QVBoxLayout(custom_group)

        # 現在のカスタムメタデータを取得
        self.custom_metadata = self.book.custom_metadata

        # フォームレイアウト（動的に作成）
        self.custom_form_layout = QFormLayout()
        custom_layout.addLayout(self.custom_form_layout)

        # 既存のカスタムメタデータを表示
        self.custom_editors = {}
        for key, value in self.custom_metadata.items():
            edit = QLineEdit(value)
            self.custom_form_layout.addRow(f"{key}:", edit)
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

    def regenerate_cover(self):
        """PDFから表紙を再生成する。"""
        cover_data = self.book.get_cover_image(force_reload=True)
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)

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

    def update_series_info(self):
        """選択されたシリーズの情報を更新する。"""
        # 以前の情報をクリア
        for i in reversed(range(self.series_info_layout.count())):
            widget = self.series_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 選択されたシリーズIDを取得
        series_id = self.series_combo.currentData()

        if not series_id:
            # シリーズが選択されていない場合
            self.series_info_label = QLabel("No series selected.")
            self.series_info_layout.addWidget(self.series_info_label)
            return

        # シリーズの情報を取得
        series = self.library_controller.get_series(series_id)
        if not series:
            self.series_info_label = QLabel("Series not found.")
            self.series_info_layout.addWidget(self.series_info_label)
            return

        # シリーズの書籍リストを表示
        self.series_info_label = QLabel(f"Books in series '{series.name}':")
        self.series_info_layout.addWidget(self.series_info_label)

        books = series.books
        if not books:
            self.series_info_layout.addWidget(QLabel("No books in this series."))
        else:
            for book in sorted(books, key=lambda b: b.series_order or float("inf")):
                if book.id == self.book_id:
                    # 現在編集中の書籍は強調表示
                    book_label = QLabel(
                        f"#{book.series_order or '-'}: {book.title} (current)"
                    )
                    book_label.setStyleSheet("font-weight: bold; color: blue;")
                else:
                    book_label = QLabel(f"#{book.series_order or '-'}: {book.title}")
                self.series_info_layout.addWidget(book_label)

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
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        publisher = self.publisher_edit.text().strip()

        # 読書状態を取得
        status_map = {
            "Unread": self.book.STATUS_UNREAD,
            "Reading": self.book.STATUS_READING,
            "Completed": self.book.STATUS_COMPLETED,
        }
        status = status_map.get(self.status_combo.currentText())

        # シリーズ情報を取得
        series_id = self.series_combo.currentData()
        series_order = self.order_spinbox.value()
        if series_order == 0:  # Auto（自動割り当て）
            series_order = None

        # 更新データを準備
        metadata_updates = {
            "title": title,
            "author": author,
            "publisher": publisher,
            "series_id": series_id,
            "series_order": series_order,
        }

        # カスタムメタデータを追加
        for key, edit in self.custom_editors.items():
            metadata_updates[key] = edit.text().strip()

        # 書籍のメタデータを更新
        self.library_controller.update_book_metadata(self.book_id, **metadata_updates)

        # 読書状態を更新
        self.library_controller.update_book_progress(self.book_id, status=status)
