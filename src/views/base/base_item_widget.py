from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QWidget


class BaseItemWidget(QWidget):
    """
    すべてのアイテムウィジェットの基底クラス。

    Parameters
    ----------
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # カバー画像の読み込み状態
        self.cover_loaded = False

    def load_cover_image(self):
        """表紙画像を読み込む（サブクラスでオーバーライド）"""
        pass

    def update_info(self, item):
        """
        アイテム情報を更新する（サブクラスでオーバーライド）。

        Parameters
        ----------
        item : object
            更新するアイテムオブジェクト
        """
        pass

    def _truncate_text(self, text, max_length):
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

    def enterEvent(self, event):
        """ウィジェットにマウスが入ったとき、優先的に表紙を読み込む"""
        if not self.cover_loaded:
            QTimer.singleShot(10, self.load_cover_image)
        super().enterEvent(event)
