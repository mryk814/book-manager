from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget


class BaseView(QWidget):
    item_selected = pyqtSignal(int)
    items_selected = pyqtSignal(list)

    def __init__(self, library_controller, parent=None):
        super().__init__(parent)
        self.library_controller = library_controller

        self.selected_item_id = None
        self.selected_item_ids = set()
        self.multi_select_mode = False
        self.item_widgets = {}

        self.category_filter = None
        self.search_query = None

        self.all_items = []
        self.loaded_count = 0
        self.batch_size = 20
        self.is_loading = False

    def refresh(self):
        self._clear_view()
        self.loaded_count = 0

        QTimer.singleShot(50, self._load_items_async)

    def _load_items_async(self):
        self.all_items = self._get_filtered_items()
        self.load_more_items()

    def load_more_items(self):
        if self.is_loading or self.loaded_count >= len(self.all_items):
            return

        self.is_loading = True

        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_items))

        self._process_batch(start_idx, end_idx)

        self.loaded_count = end_idx
        self.is_loading = False

        if self.loaded_count < len(self.all_items):
            self._update_status_message()

    def _get_filtered_items(self):
        return []

    def _clear_view(self):
        pass

    def _process_batch(self, start_idx, end_idx):
        pass

    def _update_status_message(self):
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, "statusBar"):
                main_window.statusBar.showMessage(
                    f"Loaded {self.loaded_count} of {len(self.all_items)} items"
                )
        except Exception as e:
            print(f"Error updating status bar: {e}")

    def select_item(self, item_id, emit_signal=True):
        if item_id not in self.item_widgets:
            return

        self.toggle_multi_select_mode(False)

        self._clear_selection()
        self._select_item(item_id)
        self.selected_item_id = item_id

        if emit_signal:
            self.item_selected.emit(item_id)

    def _select_item(self, item_id, add_to_selection=False):
        pass

    def _clear_selection(self):
        pass

    def toggle_multi_select_mode(self, enabled):
        self.multi_select_mode = enabled
        self._clear_selection()

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

    def get_selected_item_id(self):
        return self.selected_item_id

    def get_selected_item_ids(self):
        return list(self.selected_item_ids)
