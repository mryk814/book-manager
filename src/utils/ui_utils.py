from typing import Any, Dict, List, Optional, Tuple, Union

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox


def create_pixmap_from_bytes(data: bytes) -> QPixmap:
    """
    バイトデータからQPixmapを作成する。

    Parameters
    ----------
    data : bytes
        画像データのバイト列

    Returns
    -------
    QPixmap
        作成されたピクスマップ、失敗した場合は空のピクスマップ
    """
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
    """
    確認ダイアログを表示する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    title : str
        ダイアログのタイトル
    message : str
        表示するメッセージ
    default_button : QMessageBox.StandardButton, optional
        デフォルトで選択されるボタン

    Returns
    -------
    bool
        ユーザーが「はい」を選択した場合はTrue、それ以外はFalse
    """
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button,
    )
    return result == QMessageBox.StandardButton.Yes


def show_error_dialog(parent: Any, title: str, message: str) -> None:
    """
    エラーダイアログを表示する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    title : str
        ダイアログのタイトル
    message : str
        表示するエラーメッセージ
    """
    QMessageBox.critical(parent, title, message)


def show_info_dialog(parent: Any, title: str, message: str) -> None:
    """
    情報ダイアログを表示する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    title : str
        ダイアログのタイトル
    message : str
        表示する情報メッセージ
    """
    QMessageBox.information(parent, title, message)


def show_warning_dialog(parent: Any, title: str, message: str) -> None:
    """
    警告ダイアログを表示する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    title : str
        ダイアログのタイトル
    message : str
        表示する警告メッセージ
    """
    QMessageBox.warning(parent, title, message)


def truncate_text(text: str, max_length: int) -> str:
    """
    テキストを指定した長さに切り詰める。

    Parameters
    ----------
    text : str
        元のテキスト
    max_length : int
        最大長

    Returns
    -------
    str
        切り詰められたテキスト
    """
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
