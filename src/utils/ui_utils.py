from typing import Any

from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox


def create_pixmap_from_bytes(data: bytes) -> QPixmap:
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(QByteArray(data))
    return pixmap


def confirm_dialog(
    parent: Any,
    title: str,
    message: str,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.No,
) -> bool:
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button,
    )
    return result == QMessageBox.StandardButton.Yes


def show_error_dialog(parent: Any, title: str, message: str) -> None:
    QMessageBox.critical(parent, title, message)


def show_info_dialog(parent: Any, title: str, message: str) -> None:
    QMessageBox.information(parent, title, message)


def show_warning_dialog(parent: Any, title: str, message: str) -> None:
    QMessageBox.warning(parent, title, message)


def truncate_text(text: str, max_length: int) -> str:
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
