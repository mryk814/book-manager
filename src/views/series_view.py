import re

from PyQt6.QtCore import QByteArray, QEvent, QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.book import Book
from views.base.base_grid_view import BaseGridView
from views.base.base_list_view import BaseListView


class SeriesGridItemWidget(QWidget):
    def __init__(self, series, parent=None):
        super().__init__(parent)

        self.series = series
        self.cover_loaded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(150, 200)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        self.cover_label.setText("Series")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #f0f0f0;")

        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(self._truncate_text(series.name, 25))
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setToolTip(series.name)
        layout.addWidget(self.title_label)

        book_count = len(series.books)
        self.count_label = QLabel(
            f"{book_count} {'books' if book_count != 1 else 'book'}"
        )
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        if series.category_name:
            self.category_badge = QLabel(self._truncate_text(series.category_name, 20))
            self.category_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.category_badge.setStyleSheet(
                "background-color: #e0e0e0; border-radius: 3px; padding: 2px;"
            )
            self.category_badge.setToolTip(series.category_name)
            layout.addWidget(self.category_badge)

        status_counts = series.get_reading_status()
        total_books = sum(status_counts.values())
        if total_books > 0:
            completed = status_counts.get(Book.STATUS_COMPLETED, 0)
            progress = int(completed / total_books * 100)

            self.progress_label = QLabel(f"Completed: {progress}%")
            self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.progress_label)

    def _truncate_text(self, text, max_length):
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text

    def load_cover_image(self):
        if self.cover_loaded:
            return

        try:
            cover_data = self.get_series_cover_image(self.series)
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(cover_data))
                self.cover_label.setPixmap(pixmap)
                self.cover_loaded = True
            else:
                self.cover_label.setText("Series")
                self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.cover_loaded = True
        except Exception as e:
            print(f"Error loading series cover: {e}")
            self.cover_label.setText("Series")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cover_loaded = True

    def get_series_cover_image(self, series):
        def natural_sort_key(book):
            title = book.title if book.title else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        books = sorted(
            series.books,
            key=lambda b: (b.series_order or float("inf"), natural_sort_key(b)),
        )

        if books:
            first_book = books[0]
            return first_book.get_cover_image(thumbnail_size=(150, 200))
        return None

    def update_series_info(self, series):
        self.series = series

        self.title_label.setText(self._truncate_text(series.name, 25))
        self.title_label.setToolTip(series.name)

        book_count = len(series.books)
        self.count_label.setText(
            f"{book_count} {'books' if book_count != 1 else 'book'}"
        )

        if hasattr(self, "progress_label"):
            status_counts = series.get_reading_status()
            total_books = sum(status_counts.values())
            if total_books > 0:
                completed = status_counts.get(Book.STATUS_COMPLETED, 0)
                progress = int(completed / total_books * 100)
                self.progress_label.setText(f"Completed: {progress}%")

        self.cover_loaded = False
        self.cover_label.setText("Series")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        QTimer.singleShot(50, self.load_cover_image)

    def enterEvent(self, event):
        if not self.cover_loaded:
            QTimer.singleShot(10, self.load_cover_image)
        super().enterEvent(event)


class SeriesListItemWidget(QWidget):
    def __init__(self, series, parent=None):
        super().__init__(parent)

        self.series = series

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(48, 64)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        cover_data = self.get_series_cover_image(series)
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)
        else:
            self.cover_label.setText("Series")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.cover_label)

        info_layout = QVBoxLayout()

        self.title_label = QLabel(series.name)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label)

        book_count = len(series.books)
        status_counts = series.get_reading_status()
        completed = status_counts.get(Book.STATUS_COMPLETED, 0)
        reading = status_counts.get(Book.STATUS_READING, 0)
        unread = status_counts.get(Book.STATUS_UNREAD, 0)

        self.count_label = QLabel(
            f"{book_count} {'books' if book_count != 1 else 'book'} "
            f"({completed} completed, {reading} reading, {unread} unread)"
        )
        info_layout.addWidget(self.count_label)

        if series.category_name:
            self.category_label = QLabel(f"Category: {series.category_name}")
            info_layout.addWidget(self.category_label)

        layout.addLayout(info_layout)
        layout.setStretch(1, 1)

    def get_series_cover_image(self, series):
        def natural_sort_key(book):
            title = book.title if book.title else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        books = sorted(
            series.books,
            key=lambda b: (b.series_order or float("inf"), natural_sort_key(b)),
        )

        if books:
            first_book = books[0]
            return first_book.get_cover_image()
        return None

    def update_series_info(self, series):
        self.series = series

        self.title_label.setText(series.name)

        book_count = len(series.books)
        status_counts = series.get_reading_status()
        completed = status_counts.get(Book.STATUS_COMPLETED, 0)
        reading = status_counts.get(Book.STATUS_READING, 0)
        unread = status_counts.get(Book.STATUS_UNREAD, 0)

        self.count_label.setText(
            f"{book_count} {'books' if book_count != 1 else 'book'} "
            f"({completed} completed, {reading} reading, {unread} unread)"
        )


class SeriesGridView(BaseGridView):
    series_selected = pyqtSignal(int)

    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)
        # シリーズ固有の初期化を追加
        self.category_filter = None

    def _create_item_widget(self, series):
        widget = SeriesGridItemWidget(series)
        widget.setFixedSize(190, 300)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        return widget

    def _get_item_id(self, series):
        return series.id

    def _get_filtered_items(self):
        series_list = self.controller.get_all_series(category_id=self.category_filter)

        if self.search_query:
            query = self.search_query.lower()
            filtered_list = []
            for series in series_list:
                # シリーズ名、カテゴリ名、書籍タイトルで検索
                if query in series.name.lower() or (
                    series.category_name and query in series.category_name.lower()
                ):
                    filtered_list.append(series)
                    continue

                # 書籍タイトルで検索
                for book in series.books:
                    if query in book.title.lower():
                        filtered_list.append(series)
                        break

            return filtered_list

        return series_list

    def _optimize_visible_widget(self, series_id, widget):
        if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def _style_selected_widget(self, series_id):
        if series_id in self.item_widgets:
            self.item_widgets[series_id].setStyleSheet(
                "background-color: #e0e0ff; border: 1px solid #9090ff;"
            )

    def _style_deselected_widget(self, series_id):
        if series_id in self.item_widgets:
            self.item_widgets[series_id].setStyleSheet("")

    def update_series_item(self, series_id):
        if series_id in self.item_widgets:
            series = self.controller.get_series(series_id)
            if series:
                widget = self.item_widgets[series_id]
                if isinstance(widget, SeriesGridItemWidget):
                    widget.update_series_info(series)


class SeriesListView(BaseListView):
    series_selected = pyqtSignal(int)

    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)
        # シリーズ固有の初期化を追加
        self.category_filter = None

    def _create_item_widget(self, series):
        return SeriesListItemWidget(series)

    def _get_item_id(self, series):
        return series.id

    def _get_filtered_items(self):
        series_list = self.controller.get_all_series(category_id=self.category_filter)

        if self.search_query:
            query = self.search_query.lower()
            filtered_list = []
            for series in series_list:
                # シリーズ名、カテゴリ名、書籍タイトルで検索
                if query in series.name.lower() or (
                    series.category_name and query in series.category_name.lower()
                ):
                    filtered_list.append(series)
                    continue

                # 書籍タイトルで検索
                for book in series.books:
                    if query in book.title.lower():
                        filtered_list.append(series)
                        break

            return filtered_list

        return series_list

    def _get_item_by_id(self, series_id):
        return self.controller.get_series(series_id)

    def _update_item_widget(self, series, widget):
        if isinstance(widget, SeriesListItemWidget):
            widget.update_series_info(series)

    def update_series_item(self, series_id):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == series_id:
                series = self.controller.get_series(series_id)
                if series:
                    widget = self.list_widget.itemWidget(item)
                    if isinstance(widget, SeriesListItemWidget):
                        widget.update_series_info(series)
                break
