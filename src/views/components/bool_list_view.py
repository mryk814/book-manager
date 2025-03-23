# src/views/components/book_list_view.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from views.components.list_item_widget import ListItemWidget


class BookListView(QScrollArea):
    """
    書籍をリスト形式で表示するビュークラス。

    ListItemWidgetを使用して書籍をリストレイアウトで表示する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    """

    # シグナル定義
    book_selected = pyqtSignal(int)  # 書籍選択時
    book_double_clicked = pyqtSignal(int)  # 書籍ダブルクリック時

    def __init__(self, parent=None):
        """
        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        # スクロールエリアの設定
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # スクロール領域の内容
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        # 垂直レイアウト
        self.list_layout = QVBoxLayout(self.content_widget)
        self.list_layout.setSpacing(0)
        self.list_layout.setContentsMargins(0, 0, 0, 0)

        # アイテムとサイズ設定
        self.items = []
        self.thumbnail_size = (48, 64)

        # 選択中のアイテム
        self.selected_item = None

    def set_books(self, books):
        """
        書籍データを設定する

        Parameters
        ----------
        books : list
            表示する書籍のリスト（BookViewModelオブジェクト）
        """
        # 既存のアイテムをクリア
        self.clear_items()

        # 選択状態をリセット
        self.selected_item = None

        # 本がない場合は空の状態を表示
        if not books:
            # TODO: 空状態表示の実装（「書籍がありません」など）
            return

        # 新しいアイテムを追加
        for book in books:
            # リストアイテムを作成
            item = ListItemWidget()
            item.set_item_data(book, self.thumbnail_size)

            # クリックイベントを接続
            item.clicked.connect(self._on_item_clicked)

            # リストに追加
            self.list_layout.addWidget(item)
            self.items.append(item)

        # 最後に伸縮スペースを追加
        self.list_layout.addStretch()

    def clear_items(self):
        """リストアイテムをクリアする"""
        # 既存のアイテムを削除
        for item in self.items:
            self.list_layout.removeWidget(item)
            item.deleteLater()
        self.items = []

        # 伸縮スペースを削除
        if self.list_layout.count() > 0:
            # 最後のアイテムが伸縮スペースかチェック
            item = self.list_layout.itemAt(self.list_layout.count() - 1)
            if item and item.spacerItem():
                self.list_layout.removeItem(item)

    def set_thumbnail_size(self, width, height):
        """
        サムネイルのサイズを設定する

        Parameters
        ----------
        width : int
            サムネイルの幅
        height : int
            サムネイルの高さ
        """
        new_size = (width, height)
        if new_size != self.thumbnail_size:
            self.thumbnail_size = new_size

            # 現在表示している書籍を記憶
            books = []
            for item in self.items:
                if item.item_data:
                    books.append(item.item_data)

            # サムネイルサイズを変更して再表示
            self.set_books(books)

    def _on_item_clicked(self, book_id):
        """
        アイテムクリック時のハンドラ

        Parameters
        ----------
        book_id : int
            クリックされた書籍のID
        """
        # 選択済みのアイテムがあれば選択解除
        if self.selected_item:
            self.selected_item.set_selected(False)

        # クリックされたアイテムを特定
        clicked_item = None
        for item in self.items:
            if item.get_item_id() == book_id:
                clicked_item = item
                break

        # 見つかった場合は選択状態にする
        if clicked_item:
            clicked_item.set_selected(True)
            self.selected_item = clicked_item

            # 選択シグナルを発行
            self.book_selected.emit(book_id)

    def mouseDoubleClickEvent(self, event):
        """マウスダブルクリックイベントハンドラ"""
        if self.selected_item:
            self.book_double_clicked.emit(self.selected_item.get_item_id())
        super().mouseDoubleClickEvent(event)
