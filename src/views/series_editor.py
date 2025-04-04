import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
    QTextEdit,
    QVBoxLayout,
)


class SeriesEditor(QDialog):
    def __init__(self, library_controller, series_id, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller
        self.series_id = series_id
        self.series = library_controller.get_series(series_id)

        if not self.series:
            raise ValueError(f"Series with ID {series_id} not found.")

        self.setWindowTitle(f"Edit Series - {self.series.name}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.layout = QVBoxLayout(self)

        self.setup_basic_info()

        self.setup_books_list()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.accepted.connect(self.save_series)

    def setup_basic_info(self):
        group = QGroupBox("Series Information")
        form_layout = QFormLayout(group)

        self.name_edit = QLineEdit(self.series.name)
        form_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        if self.series.description:
            self.description_edit.setText(self.series.description)
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItem("-- None --", None)

        categories = self.library_controller.get_all_categories()
        for category in categories:
            self.category_combo.addItem(category["name"], category["id"])

        if self.series.category_id:
            index = self.category_combo.findData(self.series.category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        form_layout.addRow("Category:", self.category_combo)

        new_category_layout = QHBoxLayout()

        self.new_category_edit = QLineEdit()
        self.new_category_edit.setPlaceholderText("Enter new category name")
        new_category_layout.addWidget(self.new_category_edit)

        self.create_category_button = QPushButton("Create")
        self.create_category_button.clicked.connect(self.create_new_category)
        new_category_layout.addWidget(self.create_category_button)

        form_layout.addRow("New Category:", new_category_layout)

        self.layout.addWidget(group)

    def setup_books_list(self):
        group = QGroupBox("Books in Series")
        layout = QVBoxLayout(group)

        self.books_table = QTableWidget()
        self.books_table.setColumnCount(4)
        self.books_table.setHorizontalHeaderLabels(
            ["Title", "Author", "Order", "Status"]
        )

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

        def natural_sort_key(book):
            order = book.series_order if book.series_order is not None else float("inf")
            title = book.title if book.title else ""
            title_key = [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]
            return (order, title_key)

        books = sorted(self.series.books, key=natural_sort_key)
        self.books_table.setRowCount(len(books))

        for i, book in enumerate(books):
            title_item = QTableWidgetItem(book.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            title_item.setData(Qt.ItemDataRole.UserRole, book.id)
            self.books_table.setItem(i, 0, title_item)

            author_item = QTableWidgetItem(book.author or "")
            author_item.setFlags(author_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.books_table.setItem(i, 1, author_item)

            order_spin = QSpinBox()
            order_spin.setMinimum(0)
            order_spin.setMaximum(9999)
            order_spin.setSpecialValueText("Auto")

            if book.series_order is not None:
                order_spin.setValue(book.series_order)
            self.books_table.setCellWidget(i, 2, order_spin)

            status_text = "Unread"
            if book.status == book.STATUS_READING:
                status_text = "Reading"
            elif book.status == book.STATUS_COMPLETED:
                status_text = "Completed"

            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.books_table.setItem(i, 3, status_item)

        layout.addWidget(self.books_table)

        buttons_layout = QHBoxLayout()

        self.reorder_auto_button = QPushButton("Auto Sort by Title")
        self.reorder_auto_button.clicked.connect(self.auto_reorder_books)
        buttons_layout.addWidget(self.reorder_auto_button)

        self.reorder_numeric_button = QPushButton("Extract Numbers from Titles")
        self.reorder_numeric_button.clicked.connect(self.numeric_reorder_books)
        buttons_layout.addWidget(self.reorder_numeric_button)

        layout.addLayout(buttons_layout)

        self.layout.addWidget(group)

    def create_new_category(self):
        name = self.new_category_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a category name.")
            return

        category_id = self.library_controller.create_category(name=name)
        if category_id:
            self.category_combo.addItem(name, category_id)

            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

            self.new_category_edit.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to create category.")

    def auto_reorder_books(self):
        books = self._get_current_books()

        def natural_sort_key(book):
            title = book["title"] if book["title"] else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        sorted_books = sorted(books, key=natural_sort_key)

        for i, book in enumerate(sorted_books):
            row = book["row"]
            order_spin = self.books_table.cellWidget(row, 2)
            order_spin.setValue(i + 1)

    def numeric_reorder_books(self):
        books = self._get_current_books()

        for book in books:
            title = book["title"]
            numbers = re.findall(r"\d+", title)

            if numbers:
                try:
                    order = int(numbers[0])
                    row = book["row"]
                    order_spin = self.books_table.cellWidget(row, 2)
                    order_spin.setValue(order)
                except (ValueError, IndexError):
                    pass

    def _get_current_books(self):
        books = []
        for row in range(self.books_table.rowCount()):
            title_item = self.books_table.item(row, 0)
            book_id = title_item.data(Qt.ItemDataRole.UserRole)
            title = title_item.text()

            order_spin = self.books_table.cellWidget(row, 2)
            order = order_spin.value()
            if order == 0:
                order = None

            books.append(
                {
                    "id": book_id,
                    "title": title,
                    "order": order,
                    "row": row,
                }
            )

        return books

    def save_series(self):
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        category_id = self.category_combo.currentData()

        if not name:
            QMessageBox.warning(self, "Error", "Series name cannot be empty.")
            return

        self.series.update_metadata(
            name=name, description=description, category_id=category_id
        )

        order_updates = {}
        for row in range(self.books_table.rowCount()):
            title_item = self.books_table.item(row, 0)
            book_id = title_item.data(Qt.ItemDataRole.UserRole)

            order_spin = self.books_table.cellWidget(row, 2)
            order = order_spin.value()
            if order == 0:
                order = None

            order_updates[book_id] = order

        self.series.reorder_books(order_updates)
