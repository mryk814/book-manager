import os
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class ImportWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, db_path, file_paths, metadata):
        super().__init__()
        self.db_path = db_path
        self.file_paths = file_paths
        self.metadata = metadata
        self.abort = False

    def run(self):
        imported_ids = []
        total = len(self.file_paths)

        try:
            from controllers.library_controller import LibraryController
            from models.database import DatabaseManager

            db_manager = DatabaseManager(self.db_path)
            library_controller = LibraryController(db_manager)

            for i, file_path in enumerate(self.file_paths):
                if self.abort:
                    break

                self.progress.emit(i, total)
                book_id = library_controller.import_pdf(
                    file_path=file_path,
                    title=None,
                    author=self.metadata.get("author"),
                    publisher=self.metadata.get("publisher"),
                    series_id=self.metadata.get("series_id"),
                    series_order=None,
                )

                if book_id:
                    imported_ids.append(book_id)

                    custom_metadata = {
                        k: v
                        for k, v in self.metadata.items()
                        if k not in ["author", "publisher", "series_id", "series_order"]
                    }

                    if custom_metadata:
                        library_controller.update_book_metadata(
                            book_id, **custom_metadata
                        )

            self.progress.emit(total, total)
            self.finished.emit(imported_ids)

            db_manager.close()

        except Exception as e:
            self.error.emit(str(e))


class ImportDialog(QDialog):
    def __init__(self, library_controller, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller
        self.selected_files = []
        self.import_worker = None

        self.setWindowTitle("Import PDFs")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.layout = QVBoxLayout(self)

        self.setup_file_selection()

        self.setup_metadata_section()

        self.setup_progress_section()

        self.setup_buttons()

        self.update_ui_state(has_files=False, importing=False)

    def setup_file_selection(self):
        group = QGroupBox("Select PDF Files")
        layout = QVBoxLayout(group)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        layout.addWidget(self.file_list)

        button_layout = QHBoxLayout()

        self.add_files_button = QPushButton("Add Files...")
        self.add_files_button.clicked.connect(self.add_files)
        button_layout.addWidget(self.add_files_button)

        self.add_folder_button = QPushButton("Add Folder...")
        self.add_folder_button.clicked.connect(self.add_folder)
        button_layout.addWidget(self.add_folder_button)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        self.layout.addWidget(group)

    def setup_metadata_section(self):
        group = QGroupBox("Common Metadata")
        layout = QFormLayout(group)

        self.author_edit = QLineEdit()
        layout.addRow("Author:", self.author_edit)

        self.publisher_edit = QLineEdit()
        layout.addRow("Publisher:", self.publisher_edit)

        self.series_combo = QComboBox()
        self.series_combo.addItem("-- None --", None)

        series_list = self.library_controller.get_all_series()
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        layout.addRow("Series:", self.series_combo)

        new_series_layout = QHBoxLayout()

        self.new_series_edit = QLineEdit()
        self.new_series_edit.setPlaceholderText("Enter new series name")
        new_series_layout.addWidget(self.new_series_edit)

        self.create_series_button = QPushButton("Create")
        self.create_series_button.clicked.connect(self.create_new_series)
        new_series_layout.addWidget(self.create_series_button)

        layout.addRow("New Series:", new_series_layout)

        self.layout.addWidget(group)

    def setup_progress_section(self):
        group = QGroupBox("Import Progress")
        layout = QVBoxLayout(group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to import files.")
        layout.addWidget(self.status_label)

        self.layout.addWidget(group)

    def setup_buttons(self):
        self.button_box = QDialogButtonBox()

        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.start_import)
        self.button_box.addButton(
            self.import_button, QDialogButtonBox.ButtonRole.AcceptRole
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addButton(
            self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole
        )

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setVisible(False)
        self.button_box.addButton(
            self.close_button, QDialogButtonBox.ButtonRole.AcceptRole
        )

        self.layout.addWidget(self.button_box)

    def update_ui_state(self, has_files, importing):
        self.add_files_button.setEnabled(not importing)
        self.add_folder_button.setEnabled(not importing)
        self.remove_button.setEnabled(has_files and not importing)
        self.clear_button.setEnabled(has_files and not importing)
        self.file_list.setEnabled(not importing)

        self.author_edit.setEnabled(not importing)
        self.publisher_edit.setEnabled(not importing)
        self.series_combo.setEnabled(not importing)
        self.new_series_edit.setEnabled(not importing)
        self.create_series_button.setEnabled(not importing)

        self.import_button.setEnabled(has_files and not importing)
        self.import_button.setVisible(not importing)

        if importing:
            self.cancel_button.setText("Abort")
            self.cancel_button.clicked.disconnect()
            self.cancel_button.clicked.connect(self.abort_import)
        else:
            self.cancel_button.setText("Cancel")
            try:
                self.cancel_button.clicked.disconnect()
            except:
                pass
            self.cancel_button.clicked.connect(self.reject)

        self.close_button.setVisible(not has_files and not importing)

    def add_files(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("PDF Files (*.pdf)")

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            for file_path in file_paths:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    item = QListWidgetItem(os.path.basename(file_path))
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.file_list.addItem(item)

            self.update_ui_state(
                has_files=len(self.selected_files) > 0, importing=False
            )

    def add_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            # フォルダ内のPDFファイルを検索
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(".pdf"):
                        file_path = os.path.join(root, file)
                        if file_path not in self.selected_files:
                            self.selected_files.append(file_path)
                            item = QListWidgetItem(os.path.basename(file_path))
                            item.setData(Qt.ItemDataRole.UserRole, file_path)
                            self.file_list.addItem(item)

            self.update_ui_state(
                has_files=len(self.selected_files) > 0, importing=False
            )

    def remove_selected(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)

            row = self.file_list.row(item)
            self.file_list.takeItem(row)

        self.update_ui_state(has_files=len(self.selected_files) > 0, importing=False)

    def clear_files(self):
        self.file_list.clear()
        self.selected_files = []
        self.update_ui_state(has_files=False, importing=False)

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

    def get_common_metadata(self):
        metadata = {}

        author = self.author_edit.text().strip()
        if author:
            metadata["author"] = author

        publisher = self.publisher_edit.text().strip()
        if publisher:
            metadata["publisher"] = publisher

        series_id = self.series_combo.currentData()
        if series_id:
            metadata["series_id"] = series_id

        return metadata

    def start_import(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        metadata = self.get_common_metadata()

        self.update_ui_state(has_files=True, importing=True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Importing files...")

        db_path = self.library_controller.db_manager.db_path

        self.import_worker = ImportWorker(db_path, self.selected_files, metadata)

        self.import_worker.progress.connect(self.update_progress)
        self.import_worker.finished.connect(self.import_finished)
        self.import_worker.error.connect(self.import_error)

        self.import_worker.start()

    def abort_import(self):
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.abort = True
            self.status_label.setText("Aborting import...")

    def update_progress(self, current, total):
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            self.status_label.setText(f"Importing file {current} of {total}...")

    def import_finished(self, imported_ids):
        count = len(imported_ids)

        # 完了メッセージを表示
        self.status_label.setText(
            f"Import completed. {count} files imported successfully."
        )

        self.file_list.clear()
        self.selected_files = []

        self.update_ui_state(has_files=False, importing=False)

        self.close_button.setVisible(True)
        self.cancel_button.setVisible(False)

    def import_error(self, error_message):
        QMessageBox.critical(
            self, "Import Error", f"An error occurred during import:\n{error_message}"
        )

        self.update_ui_state(has_files=len(self.selected_files) > 0, importing=False)
