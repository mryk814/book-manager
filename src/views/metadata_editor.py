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


class BatchMetadataEditor(QDialog):
    def __init__(self, library_controller, book_ids, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller
        self.book_ids = book_ids
        self.books = [library_controller.get_book(book_id) for book_id in book_ids]

        self.books = [book for book in self.books if book is not None]
        if not self.books:
            raise ValueError("No valid books found for the provided IDs.")

        self.setWindowTitle(f"Batch Edit Metadata - {len(self.books)} books")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.layout = QVBoxLayout(self)

        self.setup_books_summary()

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

    def setup_books_summary(self):
        summary_group = QGroupBox("Selected Books")
        summary_layout = QVBoxLayout(summary_group)

        self.books_table = QTableWidget()
        self.books_table.setColumnCount(4)
        self.books_table.setHorizontalHeaderLabels(
            ["Title", "Author", "Publisher", "Series"]
        )
        self.books_table.setRowCount(len(self.books))
        self.books_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

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

        for i, book in enumerate(self.books):
            title_item = QTableWidgetItem(book.title or "")
            self.books_table.setItem(i, 0, title_item)

            author_item = QTableWidgetItem(book.author or "")
            self.books_table.setItem(i, 1, author_item)

            publisher_item = QTableWidgetItem(book.publisher or "")
            self.books_table.setItem(i, 2, publisher_item)

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

        self.summary_label = QLabel(
            f"{len(self.books)} books selected. Fields with mixed values will be marked with '*'. "
            "Empty fields will not modify the existing values."
        )
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)

        self.layout.addWidget(summary_group)

    def setup_basic_tab(self):
        layout = QVBoxLayout(self.basic_tab)

        info_group = QGroupBox("Book Information")
        info_layout = QFormLayout(info_group)

        authors = set(book.author for book in self.books if book.author)
        author_value = next(iter(authors)) if len(authors) == 1 else ""
        author_placeholder = (
            "(Multiple values) *" if len(authors) > 1 else "Enter author name"
        )

        self.author_edit = QLineEdit(author_value)
        self.author_edit.setPlaceholderText(author_placeholder)
        info_layout.addRow("Author:", self.author_edit)

        publishers = set(book.publisher for book in self.books if book.publisher)
        publisher_value = next(iter(publishers)) if len(publishers) == 1 else ""
        publisher_placeholder = (
            "(Multiple values) *" if len(publishers) > 1 else "Enter publisher name"
        )

        self.publisher_edit = QLineEdit(publisher_value)
        self.publisher_edit.setPlaceholderText(publisher_placeholder)
        info_layout.addRow("Publisher:", self.publisher_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItem("-- No Change --", None)
        self.status_combo.addItem("Unread", "unread")
        self.status_combo.addItem("Reading", "reading")
        self.status_combo.addItem("Completed", "completed")
        info_layout.addRow("Set Reading Status:", self.status_combo)

        layout.addWidget(info_group)
        layout.addStretch(1)

    def setup_series_tab(self):
        layout = QVBoxLayout(self.series_tab)

        series_group = QGroupBox("Series Information")
        series_layout = QFormLayout(series_group)

        self.series_combo = QComboBox()
        self.series_combo.addItem("-- No Change --", None)
        self.series_combo.addItem("Remove from Series", -1)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        series_layout.addRow("Series:", self.series_combo)

        new_series_layout = QHBoxLayout()

        self.new_series_edit = QLineEdit()
        self.new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(self.new_series_edit)

        self.create_series_button = QPushButton("Create New Series")
        self.create_series_button.clicked.connect(self.create_new_series)
        new_series_layout.addWidget(self.create_series_button)

        series_layout.addRow("New Series:", new_series_layout)

        self.order_method_combo = QComboBox()
        self.order_method_combo.addItem("Do not change order", "no_change")
        self.order_method_combo.addItem("Auto-assign sequential numbers", "sequential")
        self.order_method_combo.addItem("Use specific starting number", "specific")
        series_layout.addRow("Order Method:", self.order_method_combo)

        order_layout = QHBoxLayout()
        self.start_order_spin = QSpinBox()
        self.start_order_spin.setMinimum(1)
        self.start_order_spin.setMaximum(9999)
        self.start_order_spin.setValue(1)
        self.start_order_spin.setEnabled(False)
        order_layout.addWidget(self.start_order_spin)

        self.preserve_current_check = QCheckBox("Keep current order when possible")
        self.preserve_current_check.setChecked(True)
        self.preserve_current_check.setEnabled(False)
        order_layout.addWidget(self.preserve_current_check)

        series_layout.addRow("Starting Number:", order_layout)

        self.order_method_combo.currentIndexChanged.connect(
            self.on_order_method_changed
        )

        layout.addWidget(series_group)
        layout.addStretch(1)

    def on_order_method_changed(self, index):
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
        layout = QVBoxLayout(self.custom_tab)

        custom_group = QGroupBox("Custom Metadata")
        custom_layout = QVBoxLayout(custom_group)

        all_keys = set()
        for book in self.books:
            all_keys.update(book.custom_metadata.keys())

        self.common_metadata = {}
        for key in all_keys:
            values = [
                book.custom_metadata.get(key)
                for book in self.books
                if key in book.custom_metadata
            ]
            if len(set(values)) == 1 and values:
                self.common_metadata[key] = values[0]

        self.custom_form_layout = QFormLayout()
        custom_layout.addLayout(self.custom_form_layout)

        self.custom_editors = {}

        for key in sorted(all_keys):
            if key in self.common_metadata:
                edit = QLineEdit(self.common_metadata[key])
                label_text = f"{key}:"
            else:
                edit = QLineEdit()
                edit.setPlaceholderText("(Multiple values) *")
                label_text = f"{key}: *"

            self.custom_form_layout.addRow(label_text, edit)
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
        author = self.author_edit.text().strip()
        publisher = self.publisher_edit.text().strip()

        status = self.status_combo.currentData()

        series_id = self.series_combo.currentData()

        metadata_updates = {}

        if author:
            metadata_updates["author"] = author
        if publisher:
            metadata_updates["publisher"] = publisher

        if series_id is not None:
            if series_id == -1:
                metadata_updates["series_id"] = None
                metadata_updates["series_order"] = None
            else:
                metadata_updates["series_id"] = series_id

                order_method = self.order_method_combo.currentData()
                if order_method == "sequential" or order_method == "specific":
                    start_order = self.start_order_spin.value()
                    preserve_current = self.preserve_current_check.isChecked()

                    if preserve_current:
                        sorted_books = sorted(
                            self.books,
                            key=lambda b: (
                                b.series_id != series_id,
                                b.series_order or float("inf"),
                            ),
                        )
                    else:
                        sorted_books = sorted(self.books, key=lambda b: b.title)

                    current_order = start_order
                    for book in sorted_books:
                        if book.id in self.book_ids:
                            self.library_controller.update_book_metadata(
                                book.id, series_id=series_id, series_order=current_order
                            )
                            current_order += 1

        for key, edit in self.custom_editors.items():
            value = edit.text().strip()
            if value:
                metadata_updates[key] = value

        if metadata_updates:
            self.library_controller.batch_update_metadata(
                self.book_ids, metadata_updates
            )

        if status is not None:
            for book_id in self.book_ids:
                self.library_controller.update_book_progress(book_id, status=status)


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
