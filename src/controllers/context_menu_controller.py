# src/controllers/context_menu_controller.py (新規ファイル)
class ContextMenuController:
    def __init__(self, library_controller, main_window):
        self.library_controller = library_controller
        self.main_window = main_window

    def edit_metadata(self, book_id):
        from views.metadata_editor import MetadataEditor

        dialog = MetadataEditor(self.library_controller, book_id, self.main_window)
        if dialog.exec():
            self.main_window.grid_view.update_book_item(book_id)
            self.main_window.list_view.update_book_item(book_id)
            book = self.library_controller.get_book(book_id)
            if book and book.series_id:
                self.main_window.series_grid_view.update_series_item(book.series_id)
                self.main_window.series_list_view.update_series_item(book.series_id)
            return True
        return False

    def batch_edit_metadata(self, book_ids):
        from views.batch_metadata_editor import BatchMetadataEditor

        dialog = BatchMetadataEditor(
            self.library_controller, book_ids, self.main_window
        )
        if dialog.exec():
            for book_id in book_ids:
                self.main_window.grid_view.update_book_item(book_id)
                self.main_window.list_view.update_book_item(book_id)
            return True
        return False

    def add_to_series(self, book_id):
        from PyQt6.QtWidgets import (
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QHBoxLayout,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Add to Series")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        series_combo = QComboBox()
        series_combo.addItem("-- Select Series --", None)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            series_combo.addItem(series.name, series.id)
        form_layout.addRow("Series:", series_combo)

        new_series_layout = QHBoxLayout()
        new_series_edit = QLineEdit()
        new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(new_series_edit)

        create_button = QPushButton("Create")
        new_series_layout.addWidget(create_button)
        form_layout.addRow("New Series:", new_series_layout)
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        def create_new_series():
            name = new_series_edit.text().strip()
            if name:
                series_id = self.library_controller.create_series(name=name)
                if series_id:
                    series_combo.addItem(name, series_id)
                    index = series_combo.findData(series_id)
                    if index >= 0:
                        series_combo.setCurrentIndex(index)
                    new_series_edit.clear()

        create_button.clicked.connect(create_new_series)

        if dialog.exec():
            series_id = series_combo.currentData()
            if series_id:
                self.library_controller.update_book_metadata(
                    book_id, series_id=series_id
                )
                self.main_window.grid_view.update_book_item(book_id)
                self.main_window.list_view.update_book_item(book_id)
                return True
        return False

    def batch_add_to_series(self, book_ids):
        from PyQt6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QHBoxLayout,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QSpinBox,
            QVBoxLayout,
        )

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Add to Series")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        series_combo = QComboBox()
        series_combo.addItem("-- Select Series --", None)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            series_combo.addItem(series.name, series.id)
        form_layout.addRow("Series:", series_combo)

        new_series_layout = QHBoxLayout()
        new_series_edit = QLineEdit()
        new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(new_series_edit)

        create_button = QPushButton("Create")
        new_series_layout.addWidget(create_button)
        form_layout.addRow("New Series:", new_series_layout)

        order_method_combo = QComboBox()
        order_method_combo.addItem("Auto-assign sequential numbers", "sequential")
        order_method_combo.addItem("Use specific starting number", "specific")
        order_method_combo.addItem("Do not assign order", "none")
        form_layout.addRow("Order Method:", order_method_combo)

        order_layout = QHBoxLayout()
        start_order_spin = QSpinBox()
        start_order_spin.setMinimum(1)
        start_order_spin.setMaximum(9999)
        start_order_spin.setValue(1)
        order_layout.addWidget(start_order_spin)

        preserve_current_check = QCheckBox("Keep current order when possible")
        preserve_current_check.setChecked(True)
        order_layout.addWidget(preserve_current_check)
        form_layout.addRow("Starting Number:", order_layout)

        def update_order_controls():
            method = order_method_combo.currentData()
            enabled = method != "none"
            start_order_spin.setEnabled(enabled)
            preserve_current_check.setEnabled(enabled)

        order_method_combo.currentIndexChanged.connect(update_order_controls)
        update_order_controls()

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        def create_new_series():
            name = new_series_edit.text().strip()
            if name:
                series_id = self.library_controller.create_series(name=name)
                if series_id:
                    series_combo.addItem(name, series_id)
                    index = series_combo.findData(series_id)
                    if index >= 0:
                        series_combo.setCurrentIndex(index)
                    new_series_edit.clear()

        create_button.clicked.connect(create_new_series)

        if dialog.exec():
            series_id = series_combo.currentData()
            if series_id:
                order_method = order_method_combo.currentData()

                if order_method == "none":
                    for book_id in book_ids:
                        self.library_controller.update_book_metadata(
                            book_id, series_id=series_id
                        )
                else:
                    start_order = start_order_spin.value()
                    preserve_current = preserve_current_check.isChecked()

                    books = [
                        self.library_controller.get_book(book_id)
                        for book_id in book_ids
                    ]
                    books = [book for book in books if book]

                    import re

                    def natural_sort_key(book):
                        title = book.title if book.title else ""
                        return [
                            int(c) if c.isdigit() else c.lower()
                            for c in re.split(r"(\d+)", title)
                        ]

                    if preserve_current:
                        books.sort(
                            key=lambda b: (
                                b.series_id != series_id,
                                b.series_order or float("inf"),
                            )
                        )
                    else:
                        books.sort(key=natural_sort_key)

                    current_order = start_order
                    for book in books:
                        self.library_controller.update_book_metadata(
                            book.id, series_id=series_id, series_order=current_order
                        )
                        current_order += 1

                for book_id in book_ids:
                    self.main_window.grid_view.update_book_item(book_id)
                    self.main_window.list_view.update_book_item(book_id)

                return True
        return False

    def remove_from_series(self, book_id):
        book = self.library_controller.get_book(book_id)
        if book and book.series_id:
            self.library_controller.update_book_metadata(
                book_id, series_id=None, series_order=None
            )
            self.main_window.grid_view.update_book_item(book_id)
            self.main_window.list_view.update_book_item(book_id)
            return True
        return False

    def batch_remove_from_series(self, book_ids):
        from PyQt6.QtWidgets import QMessageBox

        result = QMessageBox.question(
            self.main_window,
            "Confirm Remove from Series",
            f"Are you sure you want to remove {len(book_ids)} books from their series?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return False

        for book_id in book_ids:
            self.library_controller.update_book_metadata(
                book_id, series_id=None, series_order=None
            )
            self.main_window.grid_view.update_book_item(book_id)
            self.main_window.list_view.update_book_item(book_id)

        return True

    def mark_as_status(self, book_id, status):
        self.library_controller.update_book_progress(book_id, status=status)
        self.main_window.grid_view.update_book_item(book_id)
        self.main_window.list_view.update_book_item(book_id)
        return True

    def batch_mark_as_status(self, book_ids, status):
        for book_id in book_ids:
            self.library_controller.update_book_progress(book_id, status=status)
            self.main_window.grid_view.update_book_item(book_id)
            self.main_window.list_view.update_book_item(book_id)
        return True

    def remove_book(self, book_id):
        from PyQt6.QtWidgets import QMessageBox

        book = self.library_controller.get_book(book_id)
        if not book:
            return False

        result = QMessageBox.question(
            self.main_window,
            "Confirm Delete",
            f"Are you sure you want to remove '{book.title}' from the library?\n\n"
            "This will only remove the book from the library, not delete the file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return False

        if self.main_window.reader_view.current_book_id == book_id:
            self.main_window.reader_view.close_current_book()

        success = self.library_controller.remove_book(book_id, delete_file=False)

        if success:
            if book_id in self.main_window.grid_view.book_widgets:
                widget = self.main_window.grid_view.book_widgets[book_id]
                widget.setParent(None)
                widget.deleteLater()
                del self.main_window.grid_view.book_widgets[book_id]

            for i in range(self.main_window.list_view.list_widget.count()):
                item = self.main_window.list_view.list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                    self.main_window.list_view.list_widget.takeItem(i)
                    break

            if self.main_window.grid_view.selected_book_id == book_id:
                self.main_window.grid_view.selected_book_id = None
            if self.main_window.list_view.get_selected_book_id() == book_id:
                self.main_window.list_view.list_widget.clearSelection()

            return True

        return False

    def batch_remove_books(self, book_ids):
        from PyQt6.QtWidgets import QMessageBox

        if not book_ids:
            return False

        result = QMessageBox.question(
            self.main_window,
            "Confirm Delete",
            f"Are you sure you want to remove {len(book_ids)} books from the library?\n\n"
            "This will only remove the books from the library, not delete the files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return False

        if self.main_window.reader_view.current_book_id in book_ids:
            self.main_window.reader_view.close_current_book()

        result = self.library_controller.batch_remove_books(
            book_ids, delete_files=False
        )

        if result["success"]:
            for book_id in result["success"]:
                if book_id in self.main_window.grid_view.book_widgets:
                    widget = self.main_window.grid_view.book_widgets[book_id]
                    widget.setParent(None)
                    widget.deleteLater()
                    del self.main_window.grid_view.book_widgets[book_id]

                for i in range(self.main_window.list_view.list_widget.count()):
                    item = self.main_window.list_view.list_widget.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                        self.main_window.list_view.list_widget.takeItem(i)
                        break

                if self.main_window.grid_view.selected_book_id == book_id:
                    self.main_window.grid_view.selected_book_id = None
                if book_id in self.main_window.grid_view.selected_book_ids:
                    self.main_window.grid_view.selected_book_ids.remove(book_id)

            return True

        if result["failed"]:
            QMessageBox.warning(
                self.main_window,
                "Warning",
                f"Failed to remove {len(result['failed'])} books.",
            )

        return False

    def edit_series(self, series_id):
        from views.series_editor import SeriesEditor

        dialog = SeriesEditor(self.library_controller, series_id, self.main_window)
        if dialog.exec():
            self.main_window.series_grid_view.update_series_item(series_id)
            self.main_window.series_list_view.update_series_item(series_id)
            self.main_window.refresh_library()
            return True
        return False

    def remove_series(self, series_id):
        from PyQt6.QtWidgets import QMessageBox

        series = self.library_controller.get_series(series_id)
        if not series:
            return False

        books_count = len(series.books)
        message = f"Are you sure you want to remove the series '{series.name}'?"

        if books_count > 0:
            message += f"\n\nThis series contains {books_count} books. "
            message += "The books will remain in your library but will no longer be associated with this series."

        result = QMessageBox.question(
            self.main_window,
            "Confirm Delete",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return False

        for book in series.books:
            book.update_metadata(series_id=None, series_order=None)

        conn = self.library_controller.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM custom_metadata WHERE series_id = ?", (series_id,)
            )
            cursor.execute("DELETE FROM series WHERE id = ?", (series_id,))
            conn.commit()

            if series_id in self.main_window.series_books_cache:
                del self.main_window.series_books_cache[series_id]

            self.main_window.series_grid_view.refresh()
            self.main_window.series_list_view.refresh()

            if self.main_window.current_series_id == series_id:
                self.main_window.show_series_view()

            return True

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(
                self.main_window, "Error", f"Failed to remove series: {e}"
            )
            return False
