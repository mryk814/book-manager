# src/views/base/item_view.py (新規ファイル)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget


class ItemView(QWidget):
    item_selected = pyqtSignal(int)
    items_selected = pyqtSignal(list)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.selected_item_id = None
        self.selected_item_ids = set()
        self.multi_select_mode = False
        self.category_filter = None
        self.status_filter = None
        self.search_query = None
        self.item_widgets = {}

    def refresh(self):
        self._clear_view()
        self._load_items()

    def set_category_filter(self, category_id):
        self.category_filter = category_id
        self.search_query = None
        self.refresh()

    def set_status_filter(self, status):
        self.status_filter = status
        self.refresh()

    def search(self, query):
        self.search_query = query
        self.refresh()

    def clear_search(self):
        self.search_query = None
        self.refresh()

    def toggle_multi_select_mode(self, enabled):
        self.multi_select_mode = enabled
        self._clear_selection()

    def select_all(self):
        pass

    def update_item(self, item_id):
        pass

    def select_item(self, item_id, emit_signal=True):
        pass

    def get_selected_item_id(self):
        return self.selected_item_id

    def get_selected_item_ids(self):
        return list(self.selected_item_ids)

    def _clear_view(self):
        pass

    def _load_items(self):
        pass

    def _get_filtered_items(self):
        pass

    def _clear_selection(self):
        pass
