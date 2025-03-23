from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt6.QtWidgets import QGridLayout, QLabel, QWidget

from utils.ui_utils import show_error_dialog
from views.base.base_view import BaseView


class BaseGridView(BaseView):
    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)

        self.grid_columns = 3
        self.item_width = 190
        self.item_spacing = 10
        self.last_viewport_width = 0

        self.visible_widget_ids = set()
        self.loading_timer = None

        self._init_ui()

    def _init_ui(self):
        self.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(self.item_spacing)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        self.placeholder = QLabel("Loading items...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

        self.verticalScrollBar().valueChanged.connect(self._check_scroll_position)

        self.installEventFilter(self)

    def resizeEvent(self, event):
        """ウィジェットのサイズが変わったときに呼ばれる"""
        super().resizeEvent(event)

        current_width = self.viewport().width()

        if current_width == self.last_viewport_width:
            return

        self.last_viewport_width = current_width

        self._calculate_grid_columns()

        if self.item_widgets:
            self._relayout_grid()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            QTimer.singleShot(100, self._update_visible_widgets)
        return super().eventFilter(obj, event)

    def _calculate_grid_columns(self):
        viewport_width = self.viewport().width()

        margins = self.grid_layout.contentsMargins()
        available_width = viewport_width - margins.left() - margins.right()
        spacing = self.grid_layout.spacing()

        estimated_columns = max(
            1, int((available_width + spacing) / (self.item_width + spacing))
        )

        min_columns = 1
        max_columns = 8
        new_columns = max(min_columns, min(max_columns, estimated_columns))

        if new_columns != self.grid_columns:
            self.grid_columns = new_columns
            return True
        return False

    def _relayout_grid(self):
        widgets = []
        for item_id, widget in self.item_widgets.items():
            self.grid_layout.removeWidget(widget)
            widgets.append((item_id, widget))

        for i, (item_id, widget) in enumerate(widgets):
            row = i // self.grid_columns
            col = i % self.grid_columns
            self.grid_layout.addWidget(widget, row, col)

        self.content_widget.updateGeometry()

        QTimer.singleShot(50, self._update_visible_widgets)

    def _clear_view(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.item_widgets.clear()
        self.selected_item_id = None
        self.selected_item_ids.clear()
        self.visible_widget_ids.clear()

        self.placeholder = QLabel("Loading items...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

    def _process_batch(self, start_idx, end_idx):
        try:
            if (
                hasattr(self, "placeholder")
                and self.placeholder.parent() == self.content_widget
            ):
                self.placeholder.setParent(None)
                self.placeholder.deleteLater()

            for i in range(start_idx, end_idx):
                if i >= len(self.all_items):
                    break

                item = self.all_items[i]
                row = i // self.grid_columns
                col = i % self.grid_columns

                widget = self._create_item_widget(item)

                self.grid_layout.addWidget(widget, row, col)

                item_id = self._get_item_id(item)

                self.item_widgets[item_id] = widget
        except Exception as e:
            show_error_dialog(self, "Error", f"Error loading items: {str(e)}")
            print(f"Error in _process_batch: {e}")

    def _check_scroll_position(self, value):
        scrollbar = self.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:
            self.load_more_items()

        if self.loading_timer:
            self.loading_timer.stop()

        self.loading_timer = QTimer()
        self.loading_timer.setSingleShot(True)
        self.loading_timer.timeout.connect(self._update_visible_widgets)
        self.loading_timer.start(100)

    def _update_visible_widgets(self):
        if not self.item_widgets:
            return

        viewport_rect = self.viewport().rect()
        scrollbar_value = self.verticalScrollBar().value()

        visible_top = scrollbar_value
        visible_bottom = scrollbar_value + viewport_rect.height()

        new_visible_widgets = set()

        for item_id, widget in self.item_widgets.items():
            widget_pos = widget.mapTo(self.content_widget, QPoint(0, 0))
            widget_top = widget_pos.y()
            widget_bottom = widget_top + widget.height()

            if widget_bottom >= visible_top and widget_top <= visible_bottom:
                new_visible_widgets.add(item_id)

                self._optimize_visible_widget(item_id, widget)

        self.visible_widget_ids = new_visible_widgets

    def _select_item(self, item_id, add_to_selection=False):
        if item_id not in self.item_widgets:
            return

        if not add_to_selection:
            self._clear_selection()

        self.selected_item_ids.add(item_id)
        self._style_selected_widget(item_id)

    def _deselect_item(self, item_id):
        if item_id not in self.item_widgets:
            return

        if item_id in self.selected_item_ids:
            self.selected_item_ids.remove(item_id)
            self._style_deselected_widget(item_id)

    def _clear_selection(self):
        for item_id in list(self.selected_item_ids):
            self._deselect_item(item_id)

    def ensure_correct_layout(self):
        if self._calculate_grid_columns() and self.item_widgets:
            self._relayout_grid()

    def _create_item_widget(self, item):
        raise NotImplementedError("Subclasses must implement _create_item_widget")

    def _get_item_id(self, item):
        raise NotImplementedError("Subclasses must implement _get_item_id")

    def _style_selected_widget(self, item_id):
        if item_id in self.item_widgets:
            self.item_widgets[item_id].setStyleSheet(
                "background-color: #e0e0ff; border: 1px solid #9090ff;"
            )

    def _style_deselected_widget(self, item_id):
        if item_id in self.item_widgets:
            self.item_widgets[item_id].setStyleSheet("")
