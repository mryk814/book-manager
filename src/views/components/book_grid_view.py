# src/views/components/book_grid_view.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QScrollArea, QSizePolicy, QWidget

from views.components.grid_item_widget import GridItemWidget


class BookGridView(QScrollArea):
    """
    書籍をグリッド形式で表示するビュークラス。

    GridItemWidgetを使用して書籍サムネイルをグリッドレイアウトで表示する。

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

        # グリッドレイアウト
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(10)

        # アイテムとサイズ設定
        self.items = []
        self.columns = 4
        self.item_width = 180
        self.thumbnail_size = (150, 200)

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
        row, col = 0, 0
        for book in books:
            # グリッドアイテムを作成
            item = GridItemWidget()
            item.set_item_data(book, self.thumbnail_size)
            item.setFixedWidth(self.item_width)

            # クリックイベントを接続
            item.clicked.connect(self._on_item_clicked)

            # グリッドに追加
            self.grid_layout.addWidget(item, row, col)
            self.items.append(item)

            # 次の位置へ
            col += 1
            if col >= self.columns:
                col = 0
                row += 1

    def clear_items(self):
        """グリッドアイテムをクリアする"""
        # 既存のアイテムを削除
        for item in self.items:
            self.grid_layout.removeWidget(item)
            item.deleteLater()
        self.items = []

    def set_columns(self, columns):
        """
        グリッドの列数を設定する

        Parameters
        ----------
        columns : int
            設定する列数
        """
        if columns != self.columns:
            self.columns = columns

            # アイテムを再配置
            books = []
            for item in self.items:
                if item.item_data:
                    books.append(item.item_data)

            # 新しい列数で再描画
            self.set_books(books)

    def set_item_width(self, width):
        """
        アイテムの幅を設定する

        Parameters
        ----------
        width : int
            設定する幅（ピクセル）
        """
        if width != self.item_width:
            self.item_width = width

            # アイテムのサイズを更新
            for item in self.items:
                item.setFixedWidth(width)

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
