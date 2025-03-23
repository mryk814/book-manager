# src/views/components/grid_item_widget.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QProgressBar, QSizePolicy, QVBoxLayout, QWidget

from utils.styles import StyleSheets
from utils.ui_utils import create_pixmap_from_bytes, truncate_text


class GridItemWidget(QWidget):
    """
    グリッドレイアウトで使用する書籍アイテムのウィジェットクラス。

    書籍のサムネイル、タイトル、進捗バーなどを表示する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    """

    clicked = pyqtSignal(object)  # クリック時に発するシグナル

    def __init__(self, parent=None):
        """
        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        # アイテムデータ
        self.item_data = None

        # 選択状態
        self._selected = False

        # レイアウトの初期化
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        # サムネイル画像
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.layout.addWidget(self.image_label)

        # タイトルラベル
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.title_label)

        # 著者ラベル
        self.author_label = QLabel()
        self.author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.author_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.layout.addWidget(self.author_label)

        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(StyleSheets.PROGRESS_BAR)
        self.layout.addWidget(self.progress_bar)

        # 状態ラベル
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        # イベント処理の設定
        self.setMouseTracking(True)
        self.setStyleSheet(StyleSheets.GRID_ITEM_BASE)

    def set_item_data(self, item_data, thumbnail_size=None):
        """
        アイテムデータを設定する

        Parameters
        ----------
        item_data : BookViewModel
            書籍のビューモデル
        thumbnail_size : tuple, optional
            サムネイルサイズ（幅, 高さ）
        """
        self.item_data = item_data

        # サムネイルサイズが指定されていない場合はデフォルト値を使用
        if thumbnail_size is None:
            thumbnail_size = (150, 200)

        # 表紙画像を設定
        cover_data = item_data.get_cover_image(thumbnail_size=thumbnail_size)
        if cover_data:
            pixmap = create_pixmap_from_bytes(cover_data)
            self.image_label.setPixmap(pixmap)
        else:
            # 表紙画像がない場合はプレースホルダーを表示
            self.image_label.setText(truncate_text(item_data.title, 15))
            self.image_label.setStyleSheet(StyleSheets.PLACEHOLDER)

        # テキスト情報を設定
        self.title_label.setText(truncate_text(item_data.title, 25))
        self.author_label.setText(truncate_text(item_data.author, 25))

        # 進捗情報を設定
        self.progress_bar.setValue(int(item_data.reading_progress))

        # 読書状態を設定
        status_text = item_data.reading_status
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"color: {item_data.status_color}; font-weight: bold;"
        )

    def get_item_id(self):
        """
        アイテムのIDを取得する

        Returns
        -------
        int or None
            アイテムのID
        """
        if self.item_data:
            return self.item_data.id
        return None

    def set_selected(self, selected):
        """
        選択状態を設定する

        Parameters
        ----------
        selected : bool
            選択状態
        """
        if self._selected != selected:
            self._selected = selected
            self.update_style()

    def is_selected(self):
        """
        選択状態を取得する

        Returns
        -------
        bool
            選択状態
        """
        return self._selected

    def update_style(self):
        """スタイルを更新する"""
        if self._selected:
            self.setStyleSheet(
                StyleSheets.GRID_ITEM_BASE + StyleSheets.GRID_ITEM_SELECTED
            )
        else:
            self.setStyleSheet(StyleSheets.GRID_ITEM_BASE)

    def mousePressEvent(self, event):
        """マウスプレスイベントハンドラ"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.get_item_id())
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """マウスエンターイベントハンドラ"""
        if not self._selected:
            # ホバー時のスタイルを設定
            self.setStyleSheet(
                StyleSheets.GRID_ITEM_BASE
                + "background-color: #f0f0f0; border: 1px solid #cccccc;"
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        """マウスリーブイベントハンドラ"""
        if not self._selected:
            # 通常のスタイルに戻す
            self.setStyleSheet(StyleSheets.GRID_ITEM_BASE)
        super().leaveEvent(event)
