import re

from PyQt6.QtCore import QByteArray, QTimer
from PyQt6.QtGui import QPixmap


def natural_sort_key(item, key_func=None):
    if key_func:
        text = key_func(item)
    else:
        text = str(item)

    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", text)]


def truncate_text(text, max_length):
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def load_cover_image_with_timer(widget, delay=10):
    if not widget.cover_loaded:
        QTimer.singleShot(delay, widget.load_cover_image)


def create_pixmap_from_bytes(data):
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(QByteArray(data))
    return pixmap


def update_view_selections(view, selected_ids):
    view.clear_selection()
    for item_id in selected_ids:
        view.select_item(item_id, add_to_selection=True)


def sort_books_by_series_order(books, series_id=None):
    def sort_key(book):
        if series_id is not None and book.series_id != series_id:
            return (1, float("inf"), natural_sort_key(book.title))

        order = float("inf") if book.series_order is None else book.series_order
        return (0, order, natural_sort_key(book.title))

    return sorted(books, key=sort_key)
