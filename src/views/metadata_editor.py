from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QPixmap
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
    QVBoxLayout,
    QWidget,
)


class MetadataEditor(QDialog):
    def __init__(self, library_controller, book_id, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller
        self.book_id = book_id
        self.book = library_controller.get_book(book_id)

        if not self.book:
            raise ValueError(f"Book with ID {book_id} not found.")

        self.setWindowTitle(f"Edit Metadata - {self.book.title}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.basic_tab = QWidget()
        self.tab_widget.addTab(self.basic_tab, "Basic Info")
        self.setup_basic_tab()

        self.series_tab = QWidget()
        self.tab_widget.addTab(self.series_tab, "Series")
        self.setup_series_tab()

        self.custom_tab = QWidget()
        self.tab_widget.addTab(self.custom_tab, "Custom Metadata")
        self.setup_custom_tab()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.accepted.connect(self.save_metadata)

    def setup_basic_tab(self):
        layout = QVBoxLayout(self.basic_tab)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)

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

        info_group = QGroupBox("Book Information")
        info_layout = QFormLayout(info_group)

        self.title_edit = QLineEdit(self.book.title or "")
        info_layout.addRow("Title:", self.title_edit)

        self.author_edit = QLineEdit(self.book.author or "")
        info_layout.addRow("Author:", self.author_edit)

        self.publisher_edit = QLineEdit(self.book.publisher or "")
        info_layout.addRow("Publisher:", self.publisher_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItem("-- None --", None)

        categories = self.library_controller.get_all_categories()
        for category in categories:
            self.category_combo.addItem(category["name"], category["id"])

        if self.book.category_id:
            index = self.category_combo.findData(self.book.category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        info_layout.addRow("Category:", self.category_combo)

        self.path_edit = QLineEdit(self.book.file_path)
        self.path_edit.setReadOnly(True)
        info_layout.addRow("File Path:", self.path_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Unread", "Reading", "Completed"])
        current_status = "Unread"
        if self.book.status == self.book.STATUS_READING:
            current_status = "Reading"
        elif self.book.status == self.book.STATUS_COMPLETED:
            current_status = "Completed"
        self.status_combo.setCurrentText(current_status)
        info_layout.addRow("Reading Status:", self.status_combo)

        progress_text = f"{self.book.current_page + 1} / {self.book.total_pages}"
        self.progress_label = QLabel(progress_text)
        info_layout.addRow("Current Page:", self.progress_label)

        top_layout.addWidget(info_group)
        top_layout.setStretch(1, 1)

    def setup_series_tab(self):
        layout = QVBoxLayout(self.series_tab)

        series_group = QGroupBox("Series Information")
        series_layout = QFormLayout(series_group)

        self.series_combo = QComboBox()
        self.series_combo.addItem("-- None --", None)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        if self.book.series_id:
            index = self.series_combo.findData(self.book.series_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)

        series_layout.addRow("Series:", self.series_combo)

        new_series_layout = QHBoxLayout()

        self.new_series_edit = QLineEdit()
        self.new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(self.new_series_edit)

        self.create_series_button = QPushButton("Create New Series")
        self.create_series_button.clicked.connect(self.create_new_series)
        new_series_layout.addWidget(self.create_series_button)

        series_layout.addRow("New Series:", new_series_layout)

        self.order_spinbox = QSpinBox()
        self.order_spinbox.setMinimum(0)
        self.order_spinbox.setMaximum(999)
        self.order_spinbox.setValue(self.book.series_order or 0)
        self.order_spinbox.setSpecialValueText("Auto")
        series_layout.addRow("Order in Series:", self.order_spinbox)

        layout.addWidget(series_group)

        self.series_info_group = QGroupBox("Current Series Books")
        self.series_info_layout = QVBoxLayout(self.series_info_group)

        self.series_info_label = QLabel("Select a series to see other books.")
        self.series_info_layout.addWidget(self.series_info_label)

        layout.addWidget(self.series_info_group)

        self.series_combo.currentIndexChanged.connect(self.update_series_info)

        self.update_series_info()

    def setup_custom_tab(self):
        layout = QVBoxLayout(self.custom_tab)

        custom_group = QGroupBox("Custom Metadata")
        custom_layout = QVBoxLayout(custom_group)

        self.custom_metadata = self.book.custom_metadata

        self.custom_form_layout = QFormLayout()
        custom_layout.addLayout(self.custom_form_layout)

        self.custom_editors = {}
        for key, value in self.custom_metadata.items():
            edit = QLineEdit(value)
            self.custom_form_layout.addRow(f"{key}:", edit)
            self.custom_editors[key] = edit

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
        cover_data = self.book.get_cover_image(force_reload=True)
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)

    def create_new_series(self):
        name = self.new_series_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a series name.")
            return

        series_id = self.library_controller.create_series(name=name)
        if series_id:
            self.series_combo.addItem(name, series_id)

            index = self.series_combo.findData(series_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)

            self.new_series_edit.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to create series.")

    def update_series_info(self):
        for i in reversed(range(self.series_info_layout.count())):
            widget = self.series_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        series_id = self.series_combo.currentData()

        if not series_id:
            self.series_info_label = QLabel("No series selected.")
            self.series_info_layout.addWidget(self.series_info_label)
            return

        series = self.library_controller.get_series(series_id)
        if not series:
            self.series_info_label = QLabel("Series not found.")
            self.series_info_layout.addWidget(self.series_info_label)
            return

        self.series_info_label = QLabel(f"Books in series '{series.name}':")
        self.series_info_layout.addWidget(self.series_info_label)

        books = series.books
        if not books:
            self.series_info_layout.addWidget(QLabel("No books in this series."))
        else:
            for book in sorted(books, key=lambda b: b.series_order or float("inf")):
                if book.id == self.book_id:
                    book_label = QLabel(
                        f"#{book.series_order or '-'}: {book.title} (current)"
                    )
                    book_label.setStyleSheet("font-weight: bold; color: blue;")
                else:
                    book_label = QLabel(f"#{book.series_order or '-'}: {book.title}")
                self.series_info_layout.addWidget(book_label)

    def add_custom_metadata(self):
        key = self.new_key_edit.text().strip()
        value = self.new_value_edit.text().strip()

        if not key:
            QMessageBox.warning(self, "Error", "Please enter a field name.")
            return

        if key in self.custom_editors:
            result = QMessageBox.question(
                self,
                "Confirm Overwrite",
                f"Field '{key}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if result == QMessageBox.StandardButton.No:
                return

            self.custom_editors[key].setText(value)
        else:
            edit = QLineEdit(value)
            self.custom_form_layout.addRow(f"{key}:", edit)
            self.custom_editors[key] = edit

        self.new_key_edit.clear()
        self.new_value_edit.clear()

    def save_metadata(self):
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        publisher = self.publisher_edit.text().strip()

        category_id = self.category_combo.currentData()

        status_map = {
            "Unread": self.book.STATUS_UNREAD,
            "Reading": self.book.STATUS_READING,
            "Completed": self.book.STATUS_COMPLETED,
        }
        status = status_map.get(self.status_combo.currentText())

        series_id = self.series_combo.currentData()
        series_order = self.order_spinbox.value()
        if series_order == 0:
            series_order = None

        metadata_updates = {
            "title": title,
            "author": author,
            "publisher": publisher,
            "series_id": series_id,
            "series_order": series_order,
            "category_id": category_id,
        }

        for key, edit in self.custom_editors.items():
            metadata_updates[key] = edit.text().strip()

        success = self.library_controller.update_book_metadata(
            self.book_id, **metadata_updates
        )

        if success:
            print(
                f"Successfully updated book {self.book_id} with category_id: {category_id}"
            )
        else:
            print(f"Failed to update book {self.book_id}")

        self.library_controller.update_book_progress(self.book_id, status=status)
