from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget


class BaseItemWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cover_loaded = False

    def load_cover_image(self):
        pass

    def update_info(self, item):
        pass

    def _truncate_text(self, text, max_length):
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text

    def enterEvent(self, event):
        if not self.cover_loaded:
            QTimer.singleShot(10, self.load_cover_image)
        super().enterEvent(event)
