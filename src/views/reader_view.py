import fitz  # PyMuPDF
from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QImage,
    QPainter,
    QPalette,
    QPixmap,
    QTransform,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class PDFReaderView(QWidget):
    progress_updated = pyqtSignal(int, int, str)  # book_id, current_page, status

    def __init__(self, library_controller, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller
        self.current_book_id = None
        self.current_page_num = 0
        self.zoom_factor = 1.0
        self.auto_fit = True

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setup_toolbar()

        self.setup_statusbar()

        self.setup_viewer()

        self.update_ui_state(False)

    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        self.layout.addWidget(self.toolbar)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.toolbar.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_to_next_page)
        self.toolbar.addWidget(self.next_button)

        self.toolbar.addSeparator()
        self.page_label = QLabel("Page:")
        self.toolbar.addWidget(self.page_label)

        self.page_combo = QComboBox()
        self.page_combo.setEditable(True)
        self.page_combo.setMinimumWidth(80)
        self.page_combo.activated.connect(self.on_page_selected)
        self.toolbar.addWidget(self.page_combo)

        self.total_pages_label = QLabel("/ 0")
        self.toolbar.addWidget(self.total_pages_label)

        self.toolbar.addSeparator()
        self.zoom_label = QLabel("Zoom:")
        self.toolbar.addWidget(self.zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setEditable(True)
        self.zoom_combo.activated.connect(self.on_zoom_selected)
        self.toolbar.addWidget(self.zoom_combo)

        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.toolbar.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.toolbar.addWidget(self.zoom_out_button)

    def setup_statusbar(self):
        from utils.styles import StyleSheets

        self.statusbar = QWidget()
        self.statusbar_layout = QHBoxLayout(self.statusbar)
        self.statusbar_layout.setContentsMargins(5, 0, 5, 0)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.progress_slider.valueChanged.connect(self.on_slider_value_changed)
        self.progress_slider.setStyleSheet(StyleSheets.PROGRESS_BAR)
        self.statusbar_layout.addWidget(self.progress_slider)

        self.status_label = QLabel("Not reading")
        self.statusbar_layout.addWidget(self.status_label)

        self.layout.addWidget(self.statusbar)

    def setup_viewer(self):
        from utils.theme import AppTheme

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.graphics_view.setBackgroundBrush(QColor(AppTheme.BACKGROUND_ALT))
        self.graphics_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graphics_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.graphics_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.graphics_view.keyPressEvent = self._handle_key_press

        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        self.placeholder_label = QLabel("No book selected")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.scroll_area.setWidget(self.placeholder_label)

        self.layout.addWidget(self.scroll_area)

    def load_book(self, book_id):
        self.close_current_book()

        book = self.library_controller.get_book(book_id)
        if not book or not book.exists():
            QMessageBox.warning(
                self,
                "Error Loading Book",
                f"The book file could not be found at:\n{book.file_path if book else 'Unknown'}",
            )
            return False

        doc = book.open()
        if not doc:
            QMessageBox.warning(
                self,
                "Error Opening PDF",
                "Failed to open the PDF file. It may be corrupted or password-protected.",
            )
            return False

        self.library_controller.set_current_book(book)
        self.current_book_id = book_id
        self.current_page_num = book.current_page

        self.update_ui_state(True)

        self.scroll_area.takeWidget()
        self.scroll_area.setWidget(self.graphics_view)

        self.show_current_page()

        self.update_progress_slider()

        self.update_page_combo()

        self.fit_to_page()

        return True

    def close_current_book(self):
        if self.current_book_id:
            book = self.library_controller.get_current_book()
            if book:
                book.close()

            self.current_book_id = None
            self.current_page_num = 0
            self.scene.clear()
            self.update_ui_state(False)

            self.scroll_area.takeWidget()
            self.scroll_area.setWidget(self.placeholder_label)

    def update_ui_state(self, has_book):
        self.prev_button.setEnabled(has_book)
        self.next_button.setEnabled(has_book)
        self.page_combo.setEnabled(has_book)
        self.zoom_combo.setEnabled(has_book)
        self.zoom_in_button.setEnabled(has_book)
        self.zoom_out_button.setEnabled(has_book)

        self.progress_slider.setEnabled(has_book)

        if not has_book:
            self.status_label.setText("No book selected")
            self.total_pages_label.setText("/ 0")
            self.progress_slider.setValue(0)

    def update_page_combo(self):
        book = self.library_controller.get_current_book()
        if not book:
            return

        total_pages = book.total_pages

        self.page_combo.clear()
        for i in range(total_pages):
            self.page_combo.addItem(str(i + 1))

        self.page_combo.setCurrentIndex(self.current_page_num)
        self.total_pages_label.setText(f"/ {total_pages}")

    def update_progress_slider(self):
        book = self.library_controller.get_current_book()
        if not book or book.total_pages <= 0:
            return

        progress_pct = int((self.current_page_num + 1) / book.total_pages * 100)
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(progress_pct)
        self.progress_slider.blockSignals(False)

        status_text = "Unread"
        if book.status == book.STATUS_READING:
            status_text = "Reading"
        elif book.status == book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label.setText(
            f"{status_text} - Page {self.current_page_num + 1} of {book.total_pages} ({progress_pct}%)"
        )

    def show_current_page(self):
        book = self.library_controller.get_current_book()
        if not book:
            return

        self.scene.clear()

        try:
            doc = book.open()
            page = doc[self.current_page_num]

            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix)

            img = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888,
            )

            pixmap = QPixmap.fromImage(img)

            self.scene.setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))
            self.scene.addPixmap(pixmap)

            self.update_reading_progress()

        except Exception as e:
            print(f"Error rendering page: {e}")
            self.scene.addText(f"Error displaying page: {str(e)}")

    def update_reading_progress(self):
        """読書進捗を更新する。"""
        if not self.current_book_id:
            return

        book = self.library_controller.get_current_book()
        if not book:
            return

        status = None

        if book.status == book.STATUS_COMPLETED:
            status = book.STATUS_COMPLETED
        elif self.current_page_num == 0 and book.status != book.STATUS_COMPLETED:
            status = book.STATUS_UNREAD
        elif self.current_page_num >= book.total_pages - 1:
            status = book.STATUS_COMPLETED
        else:
            status = book.STATUS_READING

        self.library_controller.update_book_progress(
            book_id=self.current_book_id,
            current_page=self.current_page_num,
            status=status,
        )

        self.update_progress_slider()

        self.progress_updated.emit(self.current_book_id, self.current_page_num, status)

    def go_to_page(self, page_num):
        book = self.library_controller.get_current_book()
        if not book:
            return False

        if page_num < 0:
            page_num = 0
        elif page_num >= book.total_pages:
            page_num = book.total_pages - 1

        if page_num == self.current_page_num:
            return True

        self.current_page_num = page_num
        self.show_current_page()

        self.page_combo.setCurrentIndex(page_num)

        return True

    def go_to_previous_page(self):
        self.go_to_page(self.current_page_num - 1)

    def go_to_next_page(self):
        self.go_to_page(self.current_page_num + 1)

    def on_page_selected(self, index):
        try:
            page_num = int(self.page_combo.currentText()) - 1
            self.go_to_page(page_num)
        except ValueError:
            self.page_combo.setCurrentIndex(self.current_page_num)

    def on_zoom_selected(self, index):
        try:
            zoom_text = self.zoom_combo.currentText().rstrip("%")
            zoom_factor = float(zoom_text) / 100.0
            self.set_zoom(zoom_factor)
        except ValueError:
            self.zoom_combo.setCurrentText(f"{int(self.zoom_factor * 100)}%")

    def set_zoom(self, factor):
        if factor < 0.1:
            factor = 0.1
        elif factor > 5.0:
            factor = 5.0

        if factor != self.zoom_factor:
            self.zoom_factor = factor
            self.zoom_combo.setCurrentText(f"{int(factor * 100)}%")
            self.show_current_page()

    def zoom_in(self):
        self.set_zoom(self.zoom_factor * 1.2)

    def zoom_out(self):
        self.set_zoom(self.zoom_factor / 1.2)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.auto_fit and self.current_book_id:
            self.fit_to_page()

    def fit_to_width(self):
        book = self.library_controller.get_current_book()
        if not book:
            return

        doc = book.open()
        page = doc[self.current_page_num]

        rect = page.rect
        page_width = rect.width

        view_width = self.graphics_view.viewport().width() - 20

        zoom_factor = view_width / page_width

        self.set_zoom(zoom_factor)

    def fit_to_page(self):
        book = self.library_controller.get_current_book()
        if not book:
            return

        doc = book.open()
        page = doc[self.current_page_num]

        rect = page.rect
        page_width = rect.width
        page_height = rect.height

        view_width = self.graphics_view.viewport().width() - 20
        view_height = self.graphics_view.viewport().height() - 20

        zoom_width = view_width / page_width
        zoom_height = view_height / page_height

        zoom_factor = min(zoom_width, zoom_height)

        self.set_zoom(zoom_factor)

    def on_slider_value_changed(self, value):
        book = self.library_controller.get_current_book()
        if not book or book.total_pages <= 0:
            return

        page_num = int(value * book.total_pages / 100) - 1
        if page_num < 0:
            page_num = 0

        self.go_to_page(page_num)

    def _handle_key_press(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.go_to_previous_page()
            event.accept()
        elif event.key() == Qt.Key.Key_Right:
            self.go_to_next_page()
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.go_to_previous_page()
            event.accept()
        elif event.key() == Qt.Key.Key_Right:
            self.go_to_next_page()
            event.accept()
        else:
            super().keyPressEvent(event)
