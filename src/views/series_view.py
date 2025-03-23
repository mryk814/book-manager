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


class SeriesGridView(QScrollArea):
    series_selected = pyqtSignal(int)

    def __init__(self, library_controller, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller

        self.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        self.selected_series_id = None

        self.category_filter = None
        self.search_query = None

        self.series_widgets = {}

        self.all_series = []
        self.loaded_count = 0
        self.batch_size = 15
        self.is_loading = False
        self.loading_timer = None
        self.visible_widgets = set()

        self.grid_columns = 3
        self.item_width = 190
        self.last_viewport_width = 0

        self.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

        self.installEventFilter(self)

        self.placeholder = QLabel("Loading series...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        current_width = self.viewport().width()

        if current_width == self.last_viewport_width:
            return

        self.last_viewport_width = current_width

        self.calculate_grid_columns()

        if self.series_widgets:
            self.relayout_grid()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            QTimer.singleShot(100, self.update_visible_widgets)
        return super().eventFilter(obj, event)

    def calculate_grid_columns(self):
        viewport_width = self.viewport().width()

        available_width = max(1, viewport_width - 10)

        new_columns = max(1, int(available_width / self.item_width))

        if new_columns != self.grid_columns:
            self.grid_columns = new_columns
            return True
        return False

    def relayout_grid(self):
        widgets = []
        for series_id, widget in self.series_widgets.items():
            self.grid_layout.removeWidget(widget)
            widgets.append((series_id, widget))

        for i, (series_id, widget) in enumerate(widgets):
            row = i // self.grid_columns
            col = i % self.grid_columns
            self.grid_layout.addWidget(widget, row, col)

        width = min(self.grid_columns * self.item_width, self.viewport().width())

        self.content_widget.updateGeometry()

        QTimer.singleShot(50, self.update_visible_widgets)

    def refresh(self):
        self._clear_grid()

        self.loaded_count = 0

        self.placeholder = QLabel("Loading series...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

        QTimer.singleShot(50, self._load_series_async)

    def _load_series_async(self):
        self.all_series = self._get_filtered_series()

        if self.placeholder.parent() == self.content_widget:
            self.placeholder.setParent(None)
            self.placeholder.deleteLater()

        self.calculate_grid_columns()

        self.load_more_series()

    def load_more_series(self):
        if self.is_loading or self.loaded_count >= len(self.all_series):
            return

        self.is_loading = True

        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_series))

        def natural_sort_key(series):
            name = series.name if series.name else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)
            ]

        sorted_series = sorted(self.all_series, key=natural_sort_key)

        for i in range(start_idx, end_idx):
            if i >= len(sorted_series):
                break

            series = sorted_series[i]
            row = i // self.grid_columns
            col = i % self.grid_columns

            series_widget = SeriesGridItemWidget(series)
            series_widget.setFixedSize(190, 300)
            series_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            series_widget.mousePressEvent = (
                lambda event, s=series.id: self._on_series_clicked(event, s)
            )

            self.grid_layout.addWidget(series_widget, row, col)

            self.series_widgets[series.id] = series_widget

        self.loaded_count = end_idx

        self.is_loading = False

        if self.loaded_count < len(self.all_series):
            try:
                main_window = self.window()
                if main_window and hasattr(main_window, "statusBar"):
                    main_window.statusBar.showMessage(
                        f"Loaded {self.loaded_count} of {len(self.all_series)} series"
                    )
            except Exception as e:
                print(f"Error updating status bar: {e}")

        QTimer.singleShot(50, self.update_visible_widgets)

    def update_visible_widgets(self):
        if not self.series_widgets:
            return

        viewport_rect = self.viewport().rect()
        scrollbar_value = self.verticalScrollBar().value()

        visible_top = scrollbar_value
        visible_bottom = scrollbar_value + viewport_rect.height()

        new_visible_widgets = set()

        for series_id, widget in self.series_widgets.items():
            widget_pos = widget.mapTo(self.content_widget, QPoint(0, 0))
            widget_top = widget_pos.y()
            widget_bottom = widget_top + widget.height()

            if widget_bottom >= visible_top and widget_top <= visible_bottom:
                new_visible_widgets.add(series_id)

                if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
                    QTimer.singleShot(10, widget.load_cover_image)

        self.visible_widgets = new_visible_widgets

    def check_scroll_position(self, value):
        scrollbar = self.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:
            self.load_more_series()

        if self.loading_timer:
            self.loading_timer.stop()

        self.loading_timer = QTimer()
        self.loading_timer.setSingleShot(True)
        self.loading_timer.timeout.connect(self.update_visible_widgets)
        self.loading_timer.start(100)

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.series_widgets = {}
        self.selected_series_id = None
        self.visible_widgets = set()

    def _get_filtered_series(self):
        series_list = self.library_controller.get_all_series(
            category_id=self.category_filter
        )

        if self.search_query:
            query = self.search_query.lower()
            filtered_list = []
            for series in series_list:
                if query in series.name.lower() or (
                    series.category_name and query in series.category_name.lower()
                ):
                    filtered_list.append(series)
                    continue

                for book in series.books:
                    if query in book.title.lower():
                        filtered_list.append(series)
                        break

            return filtered_list

        return series_list

    def _on_series_clicked(self, event, series_id):
        if event.button() == Qt.MouseButton.RightButton:
            global_pos = event.globalPosition().toPoint()
            self._show_context_menu(global_pos, series_id)
            return

        if self.selected_series_id in self.series_widgets:
            self.series_widgets[self.selected_series_id].setStyleSheet("")

        self.selected_series_id = series_id
        self.series_widgets[series_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

        self.series_selected.emit(series_id)

        widget = self.series_widgets[series_id]
        if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def _show_context_menu(self, position, series_id):
        menu = QMenu()

        view_action = QAction("View Series", self)
        view_action.triggered.connect(lambda: self.series_selected.emit(series_id))
        menu.addAction(view_action)

        menu.addSeparator()

        edit_action = QAction("Edit Series", self)
        edit_action.triggered.connect(lambda: self._edit_series(series_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        remove_action = QAction("Remove Series", self)
        remove_action.triggered.connect(lambda: self._remove_series(series_id))
        menu.addAction(remove_action)

        menu.exec(position)

    def _edit_series(self, series_id):
        pass

    def _remove_series(self, series_id):
        pass

    def set_category_filter(self, category_id):
        self.category_filter = category_id
        self.search_query = None
        self.refresh()
        QTimer.singleShot(50, self.ensure_correct_layout)

    def search(self, query):
        self.search_query = query
        self.refresh()
        QTimer.singleShot(50, self.ensure_correct_layout)

    def clear_search(self):
        self.search_query = None
        self.refresh()
        QTimer.singleShot(50, self.ensure_correct_layout)

    def update_series_item(self, series_id):
        if series_id in self.series_widgets:
            series = self.library_controller.get_series(series_id)
            if series:
                widget = self.series_widgets[series_id]
                if isinstance(widget, SeriesGridItemWidget):
                    widget.update_series_info(series)

    def select_series(self, series_id, emit_signal=True):
        if series_id not in self.series_widgets:
            return

        if self.selected_series_id in self.series_widgets:
            self.series_widgets[self.selected_series_id].setStyleSheet("")

        self.selected_series_id = series_id
        self.series_widgets[series_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

        if emit_signal:
            self.series_selected.emit(series_id)

        widget = self.series_widgets[series_id]
        if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def get_selected_series_id(self):
        return self.selected_series_id

    def ensure_correct_layout(self):
        if self.calculate_grid_columns() and self.series_widgets:
            self.relayout_grid()


class SeriesListView(QWidget):
    series_selected = pyqtSignal(int)

    def __init__(self, library_controller, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )
        layout.addWidget(self.list_widget)

        self.category_filter = None
        self.search_query = None

        self.refresh()

    def refresh(self):
        self.list_widget.clear()

        series_list = self._get_filtered_series()

        self._populate_list(series_list)

    def _get_filtered_series(self):
        series_list = self.library_controller.get_all_series(
            category_id=self.category_filter
        )

        if self.search_query:
            query = self.search_query.lower()
            filtered_list = []
            for series in series_list:
                if query in series.name.lower() or (
                    series.category_name and query in series.category_name.lower()
                ):
                    filtered_list.append(series)
                    continue

                for book in series.books:
                    if query in book.title.lower():
                        filtered_list.append(series)
                        break

            return filtered_list

        return series_list

    def _populate_list(self, series_list):
        def natural_sort_key(series):
            name = series.name if series.name else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)
            ]

        sorted_series = sorted(series_list, key=natural_sort_key)

        for series in sorted_series:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, series.id)

            widget = SeriesListItemWidget(series)

            item.setSizeHint(widget.sizeHint())

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _on_item_clicked(self, item):
        series_id = item.data(Qt.ItemDataRole.UserRole)
        self.series_selected.emit(series_id)

    def _on_context_menu_requested(self, position):
        item = self.list_widget.itemAt(position)
        if item:
            series_id = item.data(Qt.ItemDataRole.UserRole)
            global_pos = self.list_widget.mapToGlobal(position)
            self._show_context_menu(global_pos, series_id)

    def _show_context_menu(self, position, series_id):
        menu = QMenu()

        view_action = QAction("View Series", self)
        view_action.triggered.connect(lambda: self.series_selected.emit(series_id))
        menu.addAction(view_action)

        menu.addSeparator()

        edit_action = QAction("Edit Series", self)
        edit_action.triggered.connect(lambda: self._edit_series(series_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        remove_action = QAction("Remove Series", self)
        remove_action.triggered.connect(lambda: self._remove_series(series_id))
        menu.addAction(remove_action)

        menu.exec(position)

    def _edit_series(self, series_id):
        pass

    def _remove_series(self, series_id):
        pass

    def set_category_filter(self, category_id):
        self.category_filter = category_id
        self.search_query = None
        self.refresh()

    def search(self, query):
        self.search_query = query
        self.refresh()

    def clear_search(self):
        self.search_query = None
        self.refresh()

    def update_series_item(self, series_id):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == series_id:
                series = self.library_controller.get_series(series_id)
                if series:
                    widget = self.list_widget.itemWidget(item)
                    if isinstance(widget, SeriesListItemWidget):
                        widget.update_series_info(series)
                break

    def select_series(self, series_id, emit_signal=True):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == series_id:
                self.list_widget.setCurrentItem(item)

                if emit_signal:
                    self.series_selected.emit(series_id)
                break

    def get_selected_series_id(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
