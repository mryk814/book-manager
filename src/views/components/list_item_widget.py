# src/views/components/list_item_widget.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
)

from utils.styles import StyleSheets
from utils.ui_utils import create_pixmap_from_bytes, truncate_text


class ListItemWidget(QWidget):
    """
    リストレイアウトで使用する書籍アイテムのウィジェットクラス。

    書籍のサムネイル、タイトル、著者、進捗などを表示する。

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
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)

        # 左側のサムネイル部分
        self.image_container = QWidget()
        self.image_layout = QVBoxLayout(self.image_container)
        self.image_layout.setContentsMargins(0, 0, 0, 0)

        # サムネイル画像
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.image_layout.addWidget(self.image_label)

        # 右側のテキスト情報部分
        self.info_container = QWidget()
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(4)

        # タイトルラベル
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold;")
        self.info_layout.addWidget(self.title_label)

        # 著者ラベル
        self.author_label = QLabel()
        self.author_label.setStyleSheet("color: #666666;")
        self.info_layout.addWidget(self.author_label)

        # シリーズ情報
        self.series_label = QLabel()
        self.series_label.setStyleSheet(StyleSheets.SERIES_BADGE)
        self.info_layout.addWidget(self.series_label)

        # 進捗情報コンテナ
        self.progress_container = QWidget()
        self.progress_layout = QHBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)

        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet(StyleSheets.PROGRESS_BAR)
        self.progress_layout.addWidget(self.progress_bar)

        # 進捗テキスト
        self.progress_label = QLabel()
        self.progress_layout.addWidget(self.progress_label)

        self.info_layout.addWidget(self.progress_container)

        # 状態ラベル
        self.status_label = QLabel()
        self.info_layout.addWidget(self.status_label)

        # スペーサーを追加して下部を埋める
        self.info_layout.addStretch()

        # レイアウトにコンテナを追加
        self.layout.addWidget(self.image_container)
        self.layout.addWidget(self.info_container, 1)  # 1は伸縮係数（右側を伸ばす）

        # イベント処理の設定
        self.setMouseTracking(True)
        self.setStyleSheet("QWidget { border-bottom: 1px solid #e0e0e0; }")

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
            thumbnail_size = (48, 64)

        # サムネイルのサイズを設定
        self.image_label.setFixedSize(thumbnail_size[0], thumbnail_size[1])

        # 表紙画像を設定
        cover_data = item_data.get_cover_image(thumbnail_size=thumbnail_size)
        if cover_data:
            pixmap = create_pixmap_from_bytes(cover_data)
            self.image_label.setPixmap(pixmap)
        else:
            # 表紙画像がない場合はプレースホルダーを表示
            self.image_label.setText(truncate_text(item_data.title, 5))
            self.image_label.setStyleSheet(StyleSheets.PLACEHOLDER)

        # テキスト情報を設定
        self.title_label.setText(item_data.title)
        self.author_label.setText(item_data.author)

        # シリーズ情報を設定
        if item_data.series_id:
            self.series_label.setText(item_data.series_info)
            self.series_label.show()
        else:
            self.series_label.hide()

        # 進捗情報を設定
        self.progress_bar.setValue(int(item_data.reading_progress))
        self.progress_label.setText(item_data.progress_text)

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
        base_style = "QWidget { border-bottom: 1px solid #e0e0e0; }"
        if self._selected:
            self.setStyleSheet(base_style + " QWidget { background-color: #e8f0fe; }")
        else:
            self.setStyleSheet(base_style)

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
                "QWidget { border-bottom: 1px solid #e0e0e0; background-color: #f5f5f5; }"
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        """マウスリーブイベントハンドラ"""
        if not self._selected:
            # 通常のスタイルに戻す
            self.setStyleSheet("QWidget { border-bottom: 1px solid #e0e0e0; }")
        super().leaveEvent(event)
