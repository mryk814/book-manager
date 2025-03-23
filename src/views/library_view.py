from PyQt6.QtCore import (
    QByteArray,
    QEvent,
    QPoint,
    QSettings,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QColor, QIcon, QImage, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.book import Book
from views.base.base_grid_view import BaseGridView
from views.base.base_list_view import BaseListView


class BookListItemWidget(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent)

        self.book = book

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(48, 64)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        self.cover_label.setText("...")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        QTimer.singleShot(50, self.load_cover_image)

        layout.addWidget(self.cover_label)

        info_layout = QVBoxLayout()

        self.title_label = QLabel(book.title)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label)

        author_publisher = []
        if book.author:
            author_publisher.append(f"by {book.author}")
        if book.publisher:
            author_publisher.append(f"({book.publisher})")

        if author_publisher:
            self.author_label = QLabel(" ".join(author_publisher))
            info_layout.addWidget(self.author_label)

        if book.series_id:
            series = book.db_manager.get_series(book.series_id)
            if series:
                series_text = f"Series: {series.get('name')}"
                if book.series_order:
                    series_text += f" #{book.series_order}"
                self.series_label = QLabel(series_text)
                info_layout.addWidget(self.series_label)

        if book.category_id:
            self.category_label = QLabel(f"Category: {book.category_name}")
            self.category_label.setStyleSheet("color: green;")
            info_layout.addWidget(self.category_label)
        elif book.series_id and book.db_manager.get_series(book.series_id).get(
            "category_id"
        ):
            series = book.db_manager.get_series(book.series_id)
            if series and series.get("category_id"):
                category = book.db_manager.get_category(series.get("category_id"))
                if category:
                    self.category_label = QLabel(
                        f"Category: {category['name']} (from series)"
                    )
                    info_layout.addWidget(self.category_label)

        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            status_text = f"Reading ({book.current_page + 1}/{book.total_pages})"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )
        info_layout.addWidget(self.status_label)

        layout.addLayout(info_layout)
        layout.setStretch(1, 1)

    def load_cover_image(self):
        try:
            cover_data = self.book.get_cover_image(thumbnail_size=(48, 64))
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(cover_data))
                self.cover_label.setPixmap(pixmap)
            else:
                self.cover_label.setText("No Cover")
                self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            print(f"Error loading cover: {e}")

    def _get_status_color(self, status):
        if status == Book.STATUS_UNREAD:
            return "gray"
        elif status == Book.STATUS_READING:
            return "blue"
        elif status == Book.STATUS_COMPLETED:
            return "green"
        return "black"

    def update_book_info(self, book):
        self.book = book

        self.title_label.setText(book.title)

        if hasattr(self, "author_label"):
            author_publisher = []
            if book.author:
                author_publisher.append(f"by {book.author}")
            if book.publisher:
                author_publisher.append(f"({book.publisher})")

            if author_publisher:
                self.author_label.setText(" ".join(author_publisher))

        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            status_text = f"Reading ({book.current_page + 1}/{book.total_pages})"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )


class BookGridItemWidget(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent)

        self.book = book
        self.cover_loaded = False

        from utils.styles import StyleSheets
        from utils.theme import AppTheme

        self.setStyleSheet(StyleSheets.GRID_ITEM_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        cover_width = (
            parent.item_width - 36 if parent and hasattr(parent, "item_width") else 180
        )
        cover_height = int(cover_width * 4 / 3)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(cover_width, cover_height)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        self.cover_label.setText("Loading...")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet(StyleSheets.PLACEHOLDER)

        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(self._truncate_text(book.title, 25))
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setToolTip(book.title)
        layout.addWidget(self.title_label)

        if book.author:
            self.author_label = QLabel(self._truncate_text(book.author, 20))
            self.author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.author_label.setToolTip(book.author)
            layout.addWidget(self.author_label)

        if book.category_id:
            self.category_label = QLabel(f"Category: {book.category_name}")
            layout.addWidget(self.category_label)
        elif book.series_id and book.db_manager.get_series(book.series_id).get(
            "category_id"
        ):
            series = book.db_manager.get_series(book.series_id)
            if series and series.get("category_id"):
                category = book.db_manager.get_category(series.get("category_id"))
                if category:
                    self.category_label = QLabel(
                        f"Category: {category['name']} (from series)"
                    )
                    layout.addWidget(self.category_label)

        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            progress = (
                int((book.current_page + 1) / book.total_pages * 100)
                if book.total_pages > 0
                else 0
            )
            status_text = f"Reading {progress}%"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"
        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(StyleSheets.reading_status_style(book.status))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        if book.series_id:
            series = book.db_manager.get_series(book.series_id)
            if series:
                series_text = series.get("name")
                if book.series_order:
                    series_text += f" #{book.series_order}"
                self.series_badge = QLabel(self._truncate_text(series_text, 20))
                self.series_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.series_badge.setStyleSheet(
                    "background-color: #e0e0e0; border-radius: 3px; padding: 2px;"
                )
                self.series_badge.setToolTip(series_text)
                self.series_badge.setStyleSheet(StyleSheets.SERIES_BADGE)
                layout.addWidget(self.series_badge)

    def _truncate_text(self, text, max_length):
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text

    def _get_status_color(self, status):
        if status == Book.STATUS_UNREAD:
            return "gray"
        elif status == Book.STATUS_READING:
            return "blue"
        elif status == Book.STATUS_COMPLETED:
            return "green"
        return "black"

    def update_book_info(self, book):
        self.book = book

        self.title_label.setText(self._truncate_text(book.title, 25))
        self.title_label.setToolTip(book.title)

        if hasattr(self, "author_label") and book.author:
            self.author_label.setText(self._truncate_text(book.author, 20))
            self.author_label.setToolTip(book.author)

        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            progress = (
                int((book.current_page + 1) / book.total_pages * 100)
                if book.total_pages > 0
                else 0
            )
            status_text = f"Reading {progress}%"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )

    def load_cover_image(self):
        if self.cover_loaded:
            return

        try:
            cover_data = self.book.get_cover_image(thumbnail_size=(150, 200))
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(cover_data))
                self.cover_label.setPixmap(pixmap)
                self.cover_loaded = True
            else:
                self.cover_label.setText("No Cover")
                self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.cover_loaded = True
        except Exception as e:
            print(f"Error loading cover: {e}")
            self.cover_label.setText("Error")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cover_loaded = True  # エラーでも読み込み完了とマーク

    def enterEvent(self, event):
        if not self.cover_loaded:
            QTimer.singleShot(10, self.load_cover_image)
        super().enterEvent(event)


class LibraryGridView(BaseGridView):
    book_selected = pyqtSignal(int)
    books_selected = pyqtSignal(list)

    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)
        self.category_filter = None
        self.status_filter = None

    def _create_item_widget(self, book):
        widget = BookGridItemWidget(book, self)
        widget.setFixedWidth(self.item_width)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        return widget

    def _get_item_id(self, book):
        return book.id

    def _get_filtered_items(self):
        if self.search_query:
            return self.controller.search_books(self.search_query)
        else:
            return self.controller.get_all_books(
                category_id=self.category_filter, status=self.status_filter
            )

    def _optimize_visible_widget(self, book_id, widget):
        if isinstance(widget, BookGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def _style_selected_widget(self, book_id):
        if book_id in self.item_widgets:
            self.item_widgets[book_id].setStyleSheet(
                "background-color: #e0e0ff; border: 1px solid #9090ff;"
            )

    def _style_deselected_widget(self, book_id):
        if book_id in self.item_widgets:
            self.item_widgets[book_id].setStyleSheet("")

    def update_book_item(self, book_id):
        if book_id in self.item_widgets:
            book = self.controller.get_book(book_id)
            if book:
                widget = self.item_widgets[book_id]
                if isinstance(widget, BookGridItemWidget):
                    widget.update_book_info(book)


class LibraryListView(BaseListView):
    book_selected = pyqtSignal(int)
    books_selected = pyqtSignal(list)

    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)
        # 書籍固有の初期化を追加
        self.category_filter = None
        self.status_filter = None

    def _create_item_widget(self, book):
        return BookListItemWidget(book)

    def _get_item_id(self, book):
        return book.id

    def _get_filtered_items(self):
        if self.search_query:
            return self.controller.search_books(self.search_query)
        else:
            return self.controller.get_all_books(
                category_id=self.category_filter, status=self.status_filter
            )

    def _get_item_by_id(self, book_id):
        return self.controller.get_book(book_id)

    def _update_item_widget(self, book, widget):
        if isinstance(widget, BookListItemWidget):
            widget.update_book_info(book)

    def update_book_item(self, book_id):
        if book_id in self.item_widgets:
            book = self.controller.get_book(book_id)
            if book:
                widget_data = self.item_widgets[book_id]
                if isinstance(widget_data, dict) and "widget" in widget_data:
                    widget = widget_data["widget"]
                    if isinstance(widget, BookListItemWidget):
                        widget.update_book_info(book)
