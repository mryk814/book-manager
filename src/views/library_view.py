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


class LibraryGridView(QScrollArea):
    book_selected = pyqtSignal(int)
    books_selected = pyqtSignal(list)

    def __init__(self, library_controller, parent=None):
        super().__init__(parent)

        self.library_controller = library_controller

        self.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)

        self.min_columns = 2
        self.max_columns = 8
        self.ideal_columns = 5
        self.min_item_width = 160
        self.preferred_item_width = 200
        self.max_item_width = 260

        self.grid_columns = self.ideal_columns
        self.item_width = self.preferred_item_width

        self.selected_book_id = None

        self.selected_book_ids = set()

        self.multi_select_mode = False

        self.category_filter = None
        self.status_filter = None
        self.search_query = None

        self.book_widgets = {}

        self.all_books = []
        self.loaded_count = 0
        self.batch_size = 20
        self.is_loading = False
        self.loading_timer = None
        self.visible_widgets = set()

        self.grid_columns = 3
        self.item_width = 190
        self.last_viewport_width = 0

        self.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

        self.installEventFilter(self)

        self.placeholder = QLabel("Loading books...")
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

        if self.book_widgets:
            self.relayout_grid()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            QTimer.singleShot(100, self.update_visible_widgets)
        return super().eventFilter(obj, event)

    def calculate_grid_columns(self):
        viewport_width = self.viewport().width()

        margins = self.grid_layout.contentsMargins()
        available_width = viewport_width - margins.left() - margins.right() - 20

        spacing = self.grid_layout.spacing()

        columns = max(
            self.min_columns,
            min(
                self.max_columns,
                (available_width + spacing) // (self.preferred_item_width + spacing),
            ),
        )

        item_width = max(
            self.min_item_width,
            min(
                self.max_item_width,
                (available_width - (columns - 1) * spacing) // columns,
            ),
        )

        layout_changed = False
        if columns != self.grid_columns:
            self.grid_columns = columns
            layout_changed = True

        if abs(item_width - self.item_width) > 5:
            self.item_width = item_width
            layout_changed = True

        return layout_changed

    def calculate_ideal_item_width(self):
        viewport_width = self.viewport().width()
        spacing = 10

        target_columns = 4

        ideal_width = (
            viewport_width - 20 - (target_columns - 1) * spacing
        ) // target_columns

        min_width = 150
        max_width = 250
        return max(min_width, min(max_width, ideal_width))

    def relayout_grid(self):
        widgets = []
        for book_id, widget in self.book_widgets.items():
            self.grid_layout.removeWidget(widget)
            widgets.append((book_id, widget))

        for i, (book_id, widget) in enumerate(widgets):
            row = i // self.grid_columns
            col = i % self.grid_columns
            self.grid_layout.addWidget(widget, row, col)

        self.content_widget.updateGeometry()

        QTimer.singleShot(50, self.update_visible_widgets)

    def refresh(self):
        self._clear_grid()

        self.loaded_count = 0

        self.placeholder = QLabel("Loading books...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

        QTimer.singleShot(50, self._load_books_async)

    def _load_books_async(self):
        self.all_books = self._get_filtered_books()

        if self.placeholder.parent() == self.content_widget:
            self.placeholder.setParent(None)
            self.placeholder.deleteLater()

        self.calculate_grid_columns()

        self.load_more_books()

    def load_more_books(self):
        if self.is_loading or self.loaded_count >= len(self.all_books):
            return

        self.is_loading = True

        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_books))

        for i in range(start_idx, end_idx):
            book = self.all_books[i]
            row = i // self.grid_columns
            col = i % self.grid_columns

            book_widget = BookGridItemWidget(book, self)
            book_widget.setFixedWidth(self.item_width)
            book_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            book_widget.mousePressEvent = (
                lambda event, b=book.id: self._on_book_clicked(event, b)
            )

            self.grid_layout.addWidget(book_widget, row, col)

            self.book_widgets[book.id] = book_widget

        self.loaded_count = end_idx

        self.is_loading = False

        if self.loaded_count < len(self.all_books):
            try:
                main_window = self.window()
                if main_window and hasattr(main_window, "statusBar"):
                    main_window.statusBar.showMessage(
                        f"Loaded {self.loaded_count} of {len(self.all_books)} books"
                    )
            except Exception as e:
                print(f"Error updating status bar: {e}")

        QTimer.singleShot(50, self.update_visible_widgets)

    def update_visible_widgets(self):
        if not self.book_widgets:
            return

        viewport_rect = self.viewport().rect()
        scrollbar_value = self.verticalScrollBar().value()

        visible_top = scrollbar_value
        visible_bottom = scrollbar_value + viewport_rect.height()

        new_visible_widgets = set()

        for book_id, widget in self.book_widgets.items():
            widget_pos = widget.mapTo(self.content_widget, QPoint(0, 0))
            widget_top = widget_pos.y()
            widget_bottom = widget_top + widget.height()

            if widget_bottom >= visible_top and widget_top <= visible_bottom:
                new_visible_widgets.add(book_id)

                if isinstance(widget, BookGridItemWidget) and not widget.cover_loaded:
                    QTimer.singleShot(10, widget.load_cover_image)

        self.visible_widgets = new_visible_widgets

    def check_scroll_position(self, value):
        scrollbar = self.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:
            self.load_more_books()

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

        self.book_widgets = {}
        self.selected_book_ids = set()
        self.selected_book_id = None
        self.visible_widgets = set()

    def _get_filtered_books(self):
        if self.search_query:
            base_books = self.library_controller.search_books(self.search_query)
        else:
            base_books = self.library_controller.get_all_books(
                category_id=self.category_filter, status=self.status_filter
            )

        return base_books

    def _on_book_clicked(self, event, book_id):
        if event.button() == Qt.MouseButton.RightButton:
            global_pos = event.globalPosition().toPoint()
            self._show_context_menu(global_pos, book_id)
            return

        if self.multi_select_mode:
            ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            shift_pressed = event.modifiers() & Qt.KeyboardModifier.ShiftModifier

            if shift_pressed and self.selected_book_ids:
                last_id = (
                    list(self.selected_book_ids)[-1]
                    if self.selected_book_ids
                    else book_id
                )
                all_ids = list(self.book_widgets.keys())
                try:
                    start_idx = all_ids.index(last_id)
                    end_idx = all_ids.index(book_id)
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                    for idx in range(start_idx, end_idx + 1):
                        self._select_book(all_ids[idx], add_to_selection=True)
                except ValueError:
                    if not ctrl_pressed:
                        self._clear_selection()
                    self._select_book(book_id, add_to_selection=True)
            else:
                if not ctrl_pressed:
                    self._clear_selection()

                if book_id in self.selected_book_ids:
                    self._deselect_book(book_id)
                else:
                    self._select_book(book_id, add_to_selection=True)

            self.books_selected.emit(list(self.selected_book_ids))
        else:
            self._clear_selection()
            self._select_book(book_id)
            self.selected_book_id = book_id
            self.book_selected.emit(book_id)

    def set_status_filter(self, status):
        self.status_filter = status
        self.search_query = None  # 検索クエリをクリア
        self.refresh()

    def _show_context_menu(self, position, book_id):
        menu = QMenu()

        is_multiple_selected = len(self.selected_book_ids) > 1

        if is_multiple_selected and book_id in self.selected_book_ids:
            selection_count = len(self.selected_book_ids)
            menu.addAction(f"{selection_count} books selected")
            menu.addSeparator()

            edit_action = QAction("Edit Selected Books", self)
            edit_action.triggered.connect(
                lambda: self._batch_edit_metadata(list(self.selected_book_ids))
            )
            menu.addAction(edit_action)

            add_to_series_action = QAction("Add Selected to Series", self)
            add_to_series_action.triggered.connect(
                lambda: self._batch_add_to_series(list(self.selected_book_ids))
            )
            menu.addAction(add_to_series_action)

            remove_from_series_action = QAction("Remove Selected from Series", self)
            remove_from_series_action.triggered.connect(
                lambda: self._batch_remove_from_series(list(self.selected_book_ids))
            )
            menu.addAction(remove_from_series_action)

            menu.addSeparator()

            mark_action = QMenu("Mark Selected as", menu)

            unread_action = QAction("Unread", self)
            unread_action.triggered.connect(
                lambda: self._batch_mark_as_status(
                    list(self.selected_book_ids), Book.STATUS_UNREAD
                )
            )
            mark_action.addAction(unread_action)

            reading_action = QAction("Reading", self)
            reading_action.triggered.connect(
                lambda: self._batch_mark_as_status(
                    list(self.selected_book_ids), Book.STATUS_READING
                )
            )
            mark_action.addAction(reading_action)

            completed_action = QAction("Completed", self)
            completed_action.triggered.connect(
                lambda: self._batch_mark_as_status(
                    list(self.selected_book_ids), Book.STATUS_COMPLETED
                )
            )
            mark_action.addAction(completed_action)

            menu.addMenu(mark_action)

            menu.addSeparator()

            remove_action = QAction("Remove Selected from Library", self)
            remove_action.triggered.connect(
                lambda: self._batch_remove_books(list(self.selected_book_ids))
            )
            menu.addAction(remove_action)
        else:
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.book_selected.emit(book_id))
            menu.addAction(open_action)

            menu.addSeparator()

            edit_action = QAction("Edit Metadata", self)
            edit_action.triggered.connect(lambda: self._edit_metadata(book_id))
            menu.addAction(edit_action)

            if self.library_controller.get_book(book_id).series_id is None:
                add_to_series_action = QAction("Add to Series", self)
                add_to_series_action.triggered.connect(
                    lambda: self._add_to_series(book_id)
                )
                menu.addAction(add_to_series_action)
            else:
                remove_from_series_action = QAction("Remove from Series", self)
                remove_from_series_action.triggered.connect(
                    lambda: self._remove_from_series(book_id)
                )
                menu.addAction(remove_from_series_action)

            menu.addSeparator()

            mark_action = QMenu("Mark as", menu)

            unread_action = QAction("Unread", self)
            unread_action.triggered.connect(
                lambda: self._mark_as_status(book_id, Book.STATUS_UNREAD)
            )
            mark_action.addAction(unread_action)

            reading_action = QAction("Reading", self)
            reading_action.triggered.connect(
                lambda: self._mark_as_status(book_id, Book.STATUS_READING)
            )
            mark_action.addAction(reading_action)

            completed_action = QAction("Completed", self)
            completed_action.triggered.connect(
                lambda: self._mark_as_status(book_id, Book.STATUS_COMPLETED)
            )
            mark_action.addAction(completed_action)

            menu.addMenu(mark_action)

            menu.addSeparator()

            if self.multi_select_mode:
                if book_id in self.selected_book_ids:
                    select_action = QAction("Remove from Selection", self)
                    select_action.triggered.connect(
                        lambda: self._deselect_book(book_id)
                    )
                else:
                    select_action = QAction("Add to Selection", self)
                    select_action.triggered.connect(
                        lambda: self._select_book(book_id, add_to_selection=True)
                    )
                menu.addAction(select_action)

                menu.addSeparator()

            remove_action = QAction("Remove from Library", self)
            remove_action.triggered.connect(lambda: self._remove_book(book_id))
            menu.addAction(remove_action)

        menu.exec(position)

    def _populate_grid(self, books):
        self.all_books = books

        self.calculate_grid_columns()

        self.loaded_count = 0
        self.load_more_books()

    def _select_book(self, book_id, add_to_selection=False):
        from utils.styles import StyleSheets

        if book_id not in self.book_widgets:
            return

        if not add_to_selection:
            self._clear_selection()

        self.selected_book_ids.add(book_id)
        self.book_widgets[book_id].setStyleSheet(StyleSheets.GRID_ITEM_SELECTED)

        widget = self.book_widgets[book_id]
        if isinstance(widget, BookGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def _deselect_book(self, book_id):
        if book_id not in self.book_widgets:
            return

        if book_id in self.selected_book_ids:
            self.selected_book_ids.remove(book_id)
            self.book_widgets[book_id].setStyleSheet("")

    def _clear_selection(self):
        for book_id in list(self.selected_book_ids):
            if book_id in self.book_widgets:
                self.book_widgets[book_id].setStyleSheet("")

        self.selected_book_ids.clear()
        self.selected_book_id = None

    def toggle_multi_select_mode(self, enabled):
        self.multi_select_mode = enabled

        self._clear_selection()

    def _edit_metadata(self, book_id):
        pass

    def _batch_edit_metadata(self, book_ids):
        pass

    def _add_to_series(self, book_id):
        pass

    def _batch_add_to_series(self, book_ids):
        pass

    def _remove_from_series(self, book_id):
        book = self.library_controller.get_book(book_id)
        if book and book.series_id:
            self.library_controller.update_book_metadata(
                book_id, series_id=None, series_order=None
            )
            self.update_book_item(book_id)

    def _batch_remove_from_series(self, book_ids):
        for book_id in book_ids:
            book = self.library_controller.get_book(book_id)
            if book and book.series_id:
                self.library_controller.update_book_metadata(
                    book_id, series_id=None, series_order=None
                )
                self.update_book_item(book_id)

    def _mark_as_status(self, book_id, status):
        self.library_controller.update_book_progress(book_id, status=status)
        self.update_book_item(book_id)

    def _batch_mark_as_status(self, book_ids, status):
        for book_id in book_ids:
            self.library_controller.update_book_progress(book_id, status=status)
            self.update_book_item(book_id)

    def _remove_book(self, book_id):
        pass

    def _batch_remove_books(self, book_ids):
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

    def update_book_item(self, book_id):
        if book_id in self.book_widgets:
            book = self.library_controller.get_book(book_id)

            if book:
                widget = self.book_widgets[book_id]
                if isinstance(widget, BookGridItemWidget):
                    widget.update_book_info(book)

    def select_book(self, book_id, emit_signal=True):
        if book_id not in self.book_widgets:
            return

        self.multi_select_mode = False

        self._clear_selection()
        self._select_book(book_id)
        self.selected_book_id = book_id

        if emit_signal:
            self.book_selected.emit(book_id)

    def get_selected_book_id(self):
        return self.selected_book_id

    def get_selected_book_ids(self):
        return list(self.selected_book_ids)

    def select_all(self):
        self._clear_selection()

        for book_id in self.book_widgets:
            self._select_book(book_id, add_to_selection=True)

        if self.selected_book_ids:
            self.books_selected.emit(list(self.selected_book_ids))

    def ensure_correct_layout(self):
        layout_changed = self.calculate_grid_columns()

        if layout_changed and self.book_widgets:
            settings = QSettings("YourOrg", "PDFLibraryManager")
            settings.setValue("grid_view/preferred_columns", self.grid_columns)

            for book_id, widget in self.book_widgets.items():
                if hasattr(widget, "update_size"):
                    widget.update_size(self.item_width)

            self.relayout_grid()

            QTimer.singleShot(10, self.update_visible_widgets)


class LibraryListView(QWidget):
    book_selected = pyqtSignal(int)
    books_selected = pyqtSignal(list)

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

        self.multi_select_mode = False

        self.category_filter = None
        self.status_filter = None
        self.search_query = None

        self.all_books = []
        self.loaded_count = 0
        self.batch_size = 30
        self.is_loading = False

        self.list_widget.verticalScrollBar().valueChanged.connect(
            self.check_scroll_position
        )

        self.loading_item = QListWidgetItem("Loading more books...")
        self.loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh()

    def refresh(self):
        self.list_widget.clear()

        self.loaded_count = 0

        self.list_widget.addItem("Loading books...")

        QTimer.singleShot(50, self._load_books_async)

    def _load_books_async(self):
        self.all_books = self._get_filtered_books()

        self.list_widget.clear()

        self.load_more_books()

    def load_more_books(self):
        if self.is_loading or self.loaded_count >= len(self.all_books):
            return

        self.is_loading = True
        try:
            self.list_widget.takeItem(self.list_widget.count() - 1)
        except:
            pass

        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_books))

        for i in range(start_idx, end_idx):
            book = self.all_books[i]

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, book.id)

            widget = BookListItemWidget(book)

            item.setSizeHint(widget.sizeHint())

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        if end_idx < len(self.all_books):
            self.list_widget.addItem("Loading more books...")

        self.loaded_count = end_idx

        self.is_loading = False

        if self.loaded_count < len(self.all_books):
            try:
                if self.window() and hasattr(self.window(), "statusBar"):
                    self.window().statusBar.showMessage(
                        f"Loaded {self.loaded_count} of {len(self.all_books)} books"
                    )
            except Exception as e:
                print(f"Error updating status bar: {e}")

    def check_scroll_position(self, value):
        scrollbar = self.list_widget.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:
            self.load_more_books()

    def _populate_list(self, books):
        self.all_books = books

        self.list_widget.clear()

        self.loaded_count = 0
        self.load_more_books()

    def _get_filtered_books(self):
        if self.search_query:
            return self.library_controller.search_books(self.search_query)
        else:
            return self.library_controller.get_all_books(
                category_id=self.category_filter
            )

    def _populate_list(self, books):
        for book in books:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, book.id)

            widget = BookListItemWidget(book)

            item.setSizeHint(widget.sizeHint())

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def toggle_multi_select_mode(self, enabled):
        self.multi_select_mode = enabled

        if enabled:
            self.list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )
        else:
            self.list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.SingleSelection
            )

        self.list_widget.clearSelection()

    def _on_item_clicked(self, item):
        book_id = item.data(Qt.ItemDataRole.UserRole)

        if self.multi_select_mode:
            selected_items = self.list_widget.selectedItems()
            selected_ids = [
                item.data(Qt.ItemDataRole.UserRole) for item in selected_items
            ]
            self.books_selected.emit(selected_ids)
        else:
            self.book_selected.emit(book_id)

    def _on_context_menu_requested(self, position):
        item = self.list_widget.itemAt(position)
        if item:
            book_id = item.data(Qt.ItemDataRole.UserRole)
            global_pos = self.list_widget.mapToGlobal(position)

            selected_items = self.list_widget.selectedItems()
            if len(selected_items) > 1 and item in selected_items:
                selected_ids = [
                    item.data(Qt.ItemDataRole.UserRole) for item in selected_items
                ]
                self._show_batch_context_menu(global_pos, selected_ids)
            else:
                self._show_context_menu(global_pos, book_id)

    def _show_context_menu(self, position, book_id):
        menu = QMenu()

        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.book_selected.emit(book_id))
        menu.addAction(open_action)

        menu.addSeparator()

        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(lambda: self._edit_metadata(book_id))
        menu.addAction(edit_action)

        book = self.library_controller.get_book(book_id)
        if book and book.series_id is None:
            add_to_series_action = QAction("Add to Series", self)
            add_to_series_action.triggered.connect(lambda: self._add_to_series(book_id))
            menu.addAction(add_to_series_action)
        else:
            remove_from_series_action = QAction("Remove from Series", self)
            remove_from_series_action.triggered.connect(
                lambda: self._remove_from_series(book_id)
            )
            menu.addAction(remove_from_series_action)

        menu.addSeparator()

        mark_action = QMenu("Mark as", menu)

        unread_action = QAction("Unread", self)
        unread_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_UNREAD)
        )
        mark_action.addAction(unread_action)

        reading_action = QAction("Reading", self)
        reading_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_READING)
        )
        mark_action.addAction(reading_action)

        completed_action = QAction("Completed", self)
        completed_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_COMPLETED)
        )
        mark_action.addAction(completed_action)

        menu.addMenu(mark_action)

        menu.addSeparator()

        remove_action = QAction("Remove from Library", self)
        remove_action.triggered.connect(lambda: self._remove_book(book_id))
        menu.addAction(remove_action)

        menu.exec(position)

    def _show_batch_context_menu(self, position, book_ids):
        menu = QMenu()

        selection_count = len(book_ids)
        menu.addAction(f"{selection_count} books selected")
        menu.addSeparator()

        edit_action = QAction("Edit Selected Books", self)
        edit_action.triggered.connect(lambda: self._batch_edit_metadata(book_ids))
        menu.addAction(edit_action)

        add_to_series_action = QAction("Add Selected to Series", self)
        add_to_series_action.triggered.connect(
            lambda: self._batch_add_to_series(book_ids)
        )
        menu.addAction(add_to_series_action)

        remove_from_series_action = QAction("Remove Selected from Series", self)
        remove_from_series_action.triggered.connect(
            lambda: self._batch_remove_from_series(book_ids)
        )
        menu.addAction(remove_from_series_action)

        menu.addSeparator()

        mark_action = QMenu("Mark Selected as", menu)

        unread_action = QAction("Unread", self)
        unread_action.triggered.connect(
            lambda: self._batch_mark_as_status(book_ids, Book.STATUS_UNREAD)
        )
        mark_action.addAction(unread_action)

        reading_action = QAction("Reading", self)
        reading_action.triggered.connect(
            lambda: self._batch_mark_as_status(book_ids, Book.STATUS_READING)
        )
        mark_action.addAction(reading_action)

        completed_action = QAction("Completed", self)
        completed_action.triggered.connect(
            lambda: self._batch_mark_as_status(book_ids, Book.STATUS_COMPLETED)
        )
        mark_action.addAction(completed_action)

        menu.addMenu(mark_action)

        menu.addSeparator()

        remove_action = QAction("Remove Selected from Library", self)
        remove_action.triggered.connect(lambda: self._batch_remove_books(book_ids))
        menu.addAction(remove_action)

        menu.exec(position)

    def _edit_metadata(self, book_id):
        pass

    def _batch_edit_metadata(self, book_ids):
        pass

    def _add_to_series(self, book_id):
        pass

    def _batch_add_to_series(self, book_ids):
        pass

    def _remove_from_series(self, book_id):
        self.library_controller.update_book_metadata(
            book_id, series_id=None, series_order=None
        )
        self.update_book_item(book_id)

    def _batch_remove_from_series(self, book_ids):
        for book_id in book_ids:
            book = self.library_controller.get_book(book_id)
            if book and book.series_id:
                self.library_controller.update_book_metadata(
                    book_id, series_id=None, series_order=None
                )
                self.update_book_item(book_id)

    def _mark_as_status(self, book_id, status):
        self.library_controller.update_book_progress(book_id, status=status)
        self.update_book_item(book_id)

    def _batch_mark_as_status(self, book_ids, status):
        for book_id in book_ids:
            self.library_controller.update_book_progress(book_id, status=status)
            self.update_book_item(book_id)

    def _remove_book(self, book_id):
        pass

    def _batch_remove_books(self, book_ids):
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

    def update_book_item(self, book_id):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == book_id:
                book = self.library_controller.get_book(book_id)
                if book:
                    widget = self.list_widget.itemWidget(item)
                    if isinstance(widget, BookListItemWidget):
                        widget.update_book_info(book)
                break

    def select_book(self, book_id, emit_signal=True):
        self.toggle_multi_select_mode(False)

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == book_id:
                self.list_widget.setCurrentItem(item)

                if emit_signal:
                    self.book_selected.emit(book_id)
                break

    def get_selected_book_id(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def get_selected_book_ids(self):
        selected_items = self.list_widget.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

    def select_all(self):
        self.toggle_multi_select_mode(True)

        self.list_widget.selectAll()

        selected_ids = self.get_selected_book_ids()
        if selected_ids:
            self.books_selected.emit(selected_ids)

    def _get_filtered_books(self):
        if self.search_query:
            base_books = self.library_controller.search_books(self.search_query)
        else:
            base_books = self.library_controller.get_all_books(
                category_id=self.category_filter, status=self.status_filter
            )

        return base_books

    def set_status_filter(self, status):
        self.status_filter = status
        self.search_query = None  # 検索クエリをクリア
        self.refresh()
