from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout

from utils.ui_utils import show_error_dialog
from views.base.item_view import ItemView


class BaseListView(ItemView):
    def __init__(self, controller, parent=None):
        super().__init__(controller, parent)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )

        self.list_widget.verticalScrollBar().valueChanged.connect(
            self._check_scroll_position
        )

        layout.addWidget(self.list_widget)

    def _clear_view(self):
        self.list_widget.clear()
        self.item_widgets.clear()
        self.selected_item_id = None
        self.selected_item_ids.clear()

    def _process_batch(self, start_idx, end_idx):
        try:
            for i in range(start_idx, end_idx):
                if i >= len(self.all_items):
                    break

                item = self.all_items[i]

                list_item = QListWidgetItem()
                item_id = self._get_item_id(item)
                list_item.setData(Qt.ItemDataRole.UserRole, item_id)

                widget = self._create_item_widget(item)

                list_item.setSizeHint(widget.sizeHint())

                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, widget)

                self.item_widgets[item_id] = {"list_item": list_item, "widget": widget}
        except Exception as e:
            show_error_dialog(self, "Error", f"Error loading items: {str(e)}")
            print(f"Error in _process_batch: {e}")

    def _on_item_clicked(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole)

        if self.multi_select_mode:
            selected_items = self.list_widget.selectedItems()
            selected_ids = [
                item.data(Qt.ItemDataRole.UserRole) for item in selected_items
            ]
            self.selected_item_ids = set(selected_ids)
            self.items_selected.emit(selected_ids)
        else:
            self.selected_item_id = item_id
            self.item_selected.emit(item_id)

    def _on_context_menu_requested(self, position):
        item = self.list_widget.itemAt(position)
        if item:
            item_id = item.data(Qt.ItemDataRole.UserRole)

            selected_items = self.list_widget.selectedItems()
            if len(selected_items) > 1 and item in selected_items:
                selected_ids = [
                    item.data(Qt.ItemDataRole.UserRole) for item in selected_items
                ]
                self._show_batch_context_menu(
                    self.list_widget.mapToGlobal(position), selected_ids
                )
            else:
                self._show_context_menu(self.list_widget.mapToGlobal(position), item_id)

    def _check_scroll_position(self, value):
        scrollbar = self.list_widget.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:
            self.load_more_items()

    def toggle_multi_select_mode(self, enabled):
        super().toggle_multi_select_mode(enabled)

        if enabled:
            self.list_widget.setSelectionMode(
                QListWidget.SelectionMode.ExtendedSelection
            )
        else:
            self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        self.list_widget.clearSelection()

    def select_item(self, item_id, emit_signal=True):
        self.toggle_multi_select_mode(False)

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == item_id:
                self.list_widget.setCurrentItem(item)

                self.selected_item_id = item_id

                if emit_signal:
                    self.item_selected.emit(item_id)
                break

    def get_selected_item_id(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def get_selected_item_ids(self):
        selected_items = self.list_widget.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

    def select_all(self):
        self.toggle_multi_select_mode(True)

        self.list_widget.selectAll()

        selected_ids = self.get_selected_item_ids()
        self.selected_item_ids = set(selected_ids)

        if selected_ids:
            self.items_selected.emit(selected_ids)

    def update_item(self, item_id):
        if item_id in self.item_widgets:
            item = self._get_item_by_id(item_id)

            if item:
                widget_data = self.item_widgets[item_id]
                self._update_item_widget(item, widget_data["widget"])

    def _create_item_widget(self, item):
        raise NotImplementedError("Subclasses must implement _create_item_widget")

    def _get_item_id(self, item):
        raise NotImplementedError("Subclasses must implement _get_item_id")

    def _get_item_by_id(self, item_id):
        raise NotImplementedError("Subclasses must implement _get_item_by_id")

    def _update_item_widget(self, item, widget):
        raise NotImplementedError("Subclasses must implement _update_item_widget")

    def _show_context_menu(self, position, item_id):
        pass

    def _show_batch_context_menu(self, position, item_ids):
        pass
