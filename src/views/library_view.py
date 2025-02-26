from PyQt6.QtCore import QByteArray, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QImage, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.book import Book


class BookListItemWidget(QWidget):
    """
    リストビュー内の書籍アイテムのカスタムウィジェット。

    Parameters
    ----------
    book : Book
        表示する書籍オブジェクト
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, book, parent=None):
        """
        Parameters
        ----------
        book : Book
            書籍情報
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.book = book

        # レイアウトの設定
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # 表紙画像
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(48, 64)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        cover_data = book.get_cover_image()
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)
        else:
            # デフォルト表紙
            self.cover_label.setText("No Cover")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.cover_label)

        # 書籍情報レイアウト
        info_layout = QVBoxLayout()

        # タイトル
        self.title_label = QLabel(book.title)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label)

        # 著者と出版社
        author_publisher = []
        if book.author:
            author_publisher.append(f"by {book.author}")
        if book.publisher:
            author_publisher.append(f"({book.publisher})")

        if author_publisher:
            self.author_label = QLabel(" ".join(author_publisher))
            info_layout.addWidget(self.author_label)

        # シリーズ情報
        if book.series_id:
            series = book.db_manager.get_series(book.series_id)
            if series:
                series_text = f"Series: {series.get('name')}"
                if book.series_order:
                    series_text += f" #{book.series_order}"
                self.series_label = QLabel(series_text)
                info_layout.addWidget(self.series_label)

        # 読書状態
        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            status_text = f"Reading ({book.current_page + 1}/{book.total_pages})"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )
        info_layout.addWidget(self.status_label)

        layout.addLayout(info_layout)
        layout.setStretch(1, 1)  # 情報部分を伸縮させる

    def _get_status_color(self, status):
        """
        読書状態に応じた色を返す。

        Parameters
        ----------
        status : str
            読書状態

        Returns
        -------
        str
            色のCSSコード
        """
        if status == Book.STATUS_UNREAD:
            return "gray"
        elif status == Book.STATUS_READING:
            return "blue"
        elif status == Book.STATUS_COMPLETED:
            return "green"
        return "black"

    def update_book_info(self, book):
        """
        書籍情報を更新する。

        Parameters
        ----------
        book : Book
            更新後の書籍情報
        """
        self.book = book

        # タイトルを更新
        self.title_label.setText(book.title)

        # 著者と出版社を更新
        if hasattr(self, "author_label"):
            author_publisher = []
            if book.author:
                author_publisher.append(f"by {book.author}")
            if book.publisher:
                author_publisher.append(f"({book.publisher})")

            if author_publisher:
                self.author_label.setText(" ".join(author_publisher))

        # 読書状態を更新
        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            status_text = f"Reading ({book.current_page + 1}/{book.total_pages})"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )


class BookGridItemWidget(QWidget):
    """
    グリッドビュー内の書籍アイテムのカスタムウィジェット。

    Parameters
    ----------
    book : Book
        表示する書籍オブジェクト
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, book, parent=None):
        """
        Parameters
        ----------
        book : Book
            書籍情報
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.book = book

        # レイアウトの設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 表紙画像
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(128, 192)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        cover_data = book.get_cover_image()
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)
        else:
            # デフォルト表紙
            self.cover_label.setText("No Cover")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # タイトル
        self.title_label = QLabel(self._truncate_text(book.title, 25))
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setToolTip(book.title)
        layout.addWidget(self.title_label)

        # 著者
        if book.author:
            self.author_label = QLabel(self._truncate_text(book.author, 20))
            self.author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.author_label.setToolTip(book.author)
            layout.addWidget(self.author_label)

        # 読書状態（アイコンまたはテキスト）
        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            progress = (
                int((book.current_page + 1) / book.total_pages * 100)
                if book.total_pages > 0
                else 0
            )
            status_text = f"Reading {progress}%"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # シリーズバッジ
        if book.series_id:
            series = book.db_manager.get_series(book.series_id)
            if series:
                series_text = series.get("name")
                if book.series_order:
                    series_text += f" #{book.series_order}"
                self.series_badge = QLabel(self._truncate_text(series_text, 20))
                self.series_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.series_badge.setStyleSheet(
                    "background-color: #e0e0e0; border-radius: 3px; padding: 2px;"
                )
                self.series_badge.setToolTip(series_text)
                layout.addWidget(self.series_badge)

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

    def _get_status_color(self, status):
        """
        読書状態に応じた色を返す。

        Parameters
        ----------
        status : str
            読書状態

        Returns
        -------
        str
            色のCSSコード
        """
        if status == Book.STATUS_UNREAD:
            return "gray"
        elif status == Book.STATUS_READING:
            return "blue"
        elif status == Book.STATUS_COMPLETED:
            return "green"
        return "black"

    def update_book_info(self, book):
        """
        書籍情報を更新する。

        Parameters
        ----------
        book : Book
            更新後の書籍情報
        """
        self.book = book

        # タイトルを更新
        self.title_label.setText(self._truncate_text(book.title, 25))
        self.title_label.setToolTip(book.title)

        # 著者を更新
        if hasattr(self, "author_label") and book.author:
            self.author_label.setText(self._truncate_text(book.author, 20))
            self.author_label.setToolTip(book.author)

        # 読書状態を更新
        status_text = "Unread"
        if book.status == Book.STATUS_READING:
            progress = (
                int((book.current_page + 1) / book.total_pages * 100)
                if book.total_pages > 0
                else 0
            )
            status_text = f"Reading {progress}%"
        elif book.status == Book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"color: {self._get_status_color(book.status)};"
        )


class LibraryGridView(QScrollArea):
    """
    書籍をグリッド形式で表示するビュー。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    # カスタムシグナル
    book_selected = pyqtSignal(int)  # book_id

    def __init__(self, library_controller, parent=None):
        """
        Parameters
        ----------
        library_controller : LibraryController
            ライブラリコントローラ
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.library_controller = library_controller

        # ウィジェットの設定
        self.setWidgetResizable(True)

        # コンテンツウィジェット
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        # グリッドレイアウト
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(10)

        # 選択中の書籍ID
        self.selected_book_id = None

        # フィルタ設定
        self.category_filter = None
        self.search_query = None

        # 書籍ウィジェットのマップ
        self.book_widgets = {}

        # ライブラリを読み込む
        self.refresh()

    def refresh(self):
        """ライブラリを再読み込みして表示を更新する。"""
        # グリッドをクリア
        self._clear_grid()

        # 書籍を取得
        books = self._get_filtered_books()

        # グリッドに配置
        self._populate_grid(books)

    def _clear_grid(self):
        """グリッドレイアウトをクリアする。"""
        # すべての子ウィジェットを削除
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.book_widgets = {}

    def _get_filtered_books(self):
        """
        フィルタ条件に基づいて書籍のリストを取得する。

        Returns
        -------
        list
            Book オブジェクトのリスト
        """
        if self.search_query:
            # 検索クエリがある場合は検索結果を返す
            return self.library_controller.search_books(self.search_query)
        else:
            # カテゴリフィルタがある場合はそれを適用
            return self.library_controller.get_all_books(
                category_id=self.category_filter
            )

    def _populate_grid(self, books):
        """
        書籍をグリッドに配置する。

        Parameters
        ----------
        books : list
            Book オブジェクトのリスト
        """
        # グリッドのカラム数
        columns = 4

        # 書籍をグリッドに配置
        for i, book in enumerate(books):
            row = i // columns
            col = i % columns

            # 書籍ウィジェットを作成
            book_widget = BookGridItemWidget(book)
            book_widget.setFixedSize(150, 280)
            book_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            book_widget.mousePressEvent = (
                lambda event, b=book.id: self._on_book_clicked(event, b)
            )

            # グリッドに追加
            self.grid_layout.addWidget(book_widget, row, col)

            # マップに追加
            self.book_widgets[book.id] = book_widget

    def _on_book_clicked(self, event, book_id):
        """
        書籍クリック時の処理。

        Parameters
        ----------
        event : QMouseEvent
            マウスイベント
        book_id : int
            クリックされた書籍のID
        """
        # 右クリックの場合はコンテキストメニューを表示
        if event.button() == Qt.MouseButton.RightButton:
            # PyQt6では globalPos() が非推奨になり、globalPosition().toPoint() を使用する
            global_pos = event.globalPosition().toPoint()
            self._show_context_menu(global_pos, book_id)
            return

        # 以前の選択をクリア
        if self.selected_book_id in self.book_widgets:
            self.book_widgets[self.selected_book_id].setStyleSheet("")

        # 新しい選択を設定
        self.selected_book_id = book_id
        self.book_widgets[book_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

        # 選択シグナルを発火
        self.book_selected.emit(book_id)

    def _show_context_menu(self, position, book_id):
        """
        コンテキストメニューを表示する。

        Parameters
        ----------
        position : QPoint
            表示位置
        book_id : int
            対象の書籍ID
        """
        menu = QMenu()

        # メニューアクションを追加
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.book_selected.emit(book_id))
        menu.addAction(open_action)

        menu.addSeparator()

        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(lambda: self._edit_metadata(book_id))
        menu.addAction(edit_action)

        if self.library_controller.get_book(book_id).series_id is None:
            add_to_series_action = QAction("Add to Series", self)
            add_to_series_action.triggered.connect(lambda: self._add_to_series(book_id))
            menu.addAction(add_to_series_action)
        else:
            remove_from_series_action = QAction("Remove from Series", self)
            remove_from_series_action.triggered.connect(
                lambda: self._remove_from_series(book_id)
            )
            menu.addAction(remove_from_series_action)

        menu.addSeparator()

        mark_action = QMenu("Mark as", menu)

        unread_action = QAction("Unread", self)
        unread_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_UNREAD)
        )
        mark_action.addAction(unread_action)

        reading_action = QAction("Reading", self)
        reading_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_READING)
        )
        mark_action.addAction(reading_action)

        completed_action = QAction("Completed", self)
        completed_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_COMPLETED)
        )
        mark_action.addAction(completed_action)

        menu.addMenu(mark_action)

        menu.addSeparator()

        remove_action = QAction("Remove from Library", self)
        remove_action.triggered.connect(lambda: self._remove_book(book_id))
        menu.addAction(remove_action)

        # メニューを表示
        menu.exec(position)

    def _edit_metadata(self, book_id):
        """
        メタデータ編集処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def _add_to_series(self, book_id):
        """
        シリーズに追加処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def _remove_from_series(self, book_id):
        """
        シリーズから削除処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        """
        book = self.library_controller.get_book(book_id)
        if book and book.series_id:
            # シリーズIDをNULLに更新
            self.library_controller.update_book_metadata(
                book_id, series_id=None, series_order=None
            )
            # ビューを更新
            self.update_book_item(book_id)

    def _mark_as_status(self, book_id, status):
        """
        読書状態を設定する。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        status : str
            設定する状態
        """
        self.library_controller.update_book_progress(book_id, status=status)
        self.update_book_item(book_id)

    def _remove_book(self, book_id):
        """
        書籍を削除する。

        Parameters
        ----------
        book_id : int
            削除する書籍ID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def set_category_filter(self, category_id):
        """
        カテゴリフィルタを設定する。

        Parameters
        ----------
        category_id : int または None
            フィルタリングするカテゴリID、またはNone（すべて表示）
        """
        self.category_filter = category_id
        self.search_query = None  # 検索クエリをクリア
        self.refresh()

    def search(self, query):
        """
        書籍を検索する。

        Parameters
        ----------
        query : str
            検索クエリ
        """
        self.search_query = query
        self.refresh()

    def clear_search(self):
        """検索をクリアしてすべての書籍を表示する。"""
        self.search_query = None
        self.refresh()

    def update_book_item(self, book_id):
        """
        特定の書籍アイテムを更新する。

        Parameters
        ----------
        book_id : int
            更新する書籍ID
        """
        if book_id in self.book_widgets:
            book = self.library_controller.get_book(book_id)
            if book:
                # 書籍ウィジェットを更新
                self.book_widgets[book_id].update_book_info(book)

    def select_book(self, book_id, emit_signal=True):
        """
        書籍を選択状態にする。

        Parameters
        ----------
        book_id : int
            選択する書籍ID
        emit_signal : bool, optional
            選択シグナルを発火するかどうか
        """
        # 書籍が表示されていない場合は何もしない
        if book_id not in self.book_widgets:
            return

        # 以前の選択をクリア
        if self.selected_book_id in self.book_widgets:
            self.book_widgets[self.selected_book_id].setStyleSheet("")

        # 新しい選択を設定
        self.selected_book_id = book_id
        self.book_widgets[book_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

        # シグナルを発火（オプション）
        if emit_signal:
            self.book_selected.emit(book_id)

    def get_selected_book_id(self):
        """
        現在選択されている書籍IDを取得する。

        Returns
        -------
        int または None
            選択されている書籍ID、もしくは選択がない場合はNone
        """
        return self.selected_book_id


class LibraryListView(QWidget):
    """
    書籍をリスト形式で表示するビュー。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    # カスタムシグナル
    book_selected = pyqtSignal(int)  # book_id

    def __init__(self, library_controller, parent=None):
        """
        Parameters
        ----------
        library_controller : LibraryController
            ライブラリコントローラ
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.library_controller = library_controller

        # レイアウトの設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # リストウィジェット
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )
        layout.addWidget(self.list_widget)

        # フィルタ設定
        self.category_filter = None
        self.search_query = None

        # ライブラリを読み込む
        self.refresh()

    def refresh(self):
        """ライブラリを再読み込みして表示を更新する。"""
        # リストをクリア
        self.list_widget.clear()

        # 書籍を取得
        books = self._get_filtered_books()

        # リストに追加
        self._populate_list(books)

    def _get_filtered_books(self):
        """
        フィルタ条件に基づいて書籍のリストを取得する。

        Returns
        -------
        list
            Book オブジェクトのリスト
        """
        if self.search_query:
            # 検索クエリがある場合は検索結果を返す
            return self.library_controller.search_books(self.search_query)
        else:
            # カテゴリフィルタがある場合はそれを適用
            return self.library_controller.get_all_books(
                category_id=self.category_filter
            )

    def _populate_list(self, books):
        """
        書籍をリストに追加する。

        Parameters
        ----------
        books : list
            Book オブジェクトのリスト
        """
        for book in books:
            # リストアイテムを作成
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, book.id)  # 書籍IDを保存

            # カスタムウィジェットを作成
            widget = BookListItemWidget(book)

            # アイテムのサイズを設定
            item.setSizeHint(widget.sizeHint())

            # リストに追加
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _on_item_clicked(self, item):
        """
        リストアイテムがクリックされたときの処理。

        Parameters
        ----------
        item : QListWidgetItem
            クリックされたアイテム
        """
        book_id = item.data(Qt.ItemDataRole.UserRole)
        self.book_selected.emit(book_id)

    def _on_context_menu_requested(self, position):
        """
        コンテキストメニューが要求されたときの処理。

        Parameters
        ----------
        position : QPoint
            要求位置
        """
        item = self.list_widget.itemAt(position)
        if item:
            book_id = item.data(Qt.ItemDataRole.UserRole)
            global_pos = self.list_widget.mapToGlobal(position)
            self._show_context_menu(global_pos, book_id)

    def _show_context_menu(self, position, book_id):
        """
        コンテキストメニューを表示する。

        Parameters
        ----------
        position : QPoint
            表示位置
        book_id : int
            対象の書籍ID
        """
        menu = QMenu()

        # メニューアクションを追加
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.book_selected.emit(book_id))
        menu.addAction(open_action)

        menu.addSeparator()

        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(lambda: self._edit_metadata(book_id))
        menu.addAction(edit_action)

        book = self.library_controller.get_book(book_id)
        if book and book.series_id is None:
            add_to_series_action = QAction("Add to Series", self)
            add_to_series_action.triggered.connect(lambda: self._add_to_series(book_id))
            menu.addAction(add_to_series_action)
        else:
            remove_from_series_action = QAction("Remove from Series", self)
            remove_from_series_action.triggered.connect(
                lambda: self._remove_from_series(book_id)
            )
            menu.addAction(remove_from_series_action)

        menu.addSeparator()

        mark_action = QMenu("Mark as", menu)

        unread_action = QAction("Unread", self)
        unread_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_UNREAD)
        )
        mark_action.addAction(unread_action)

        reading_action = QAction("Reading", self)
        reading_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_READING)
        )
        mark_action.addAction(reading_action)

        completed_action = QAction("Completed", self)
        completed_action.triggered.connect(
            lambda: self._mark_as_status(book_id, Book.STATUS_COMPLETED)
        )
        mark_action.addAction(completed_action)

        menu.addMenu(mark_action)

        menu.addSeparator()

        remove_action = QAction("Remove from Library", self)
        remove_action.triggered.connect(lambda: self._remove_book(book_id))
        menu.addAction(remove_action)

        # メニューを表示
        menu.exec(position)

    def _edit_metadata(self, book_id):
        """
        メタデータ編集処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def _add_to_series(self, book_id):
        """
        シリーズに追加処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def _remove_from_series(self, book_id):
        """
        シリーズから削除処理。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        """
        self.library_controller.update_book_metadata(
            book_id, series_id=None, series_order=None
        )
        self.update_book_item(book_id)

    def _mark_as_status(self, book_id, status):
        """
        読書状態を設定する。

        Parameters
        ----------
        book_id : int
            対象の書籍ID
        status : str
            設定する状態
        """
        self.library_controller.update_book_progress(book_id, status=status)
        self.update_book_item(book_id)

    def _remove_book(self, book_id):
        """
        書籍を削除する（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_id : int
            削除する書籍ID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def set_category_filter(self, category_id):
        """
        カテゴリフィルタを設定する。

        Parameters
        ----------
        category_id : int または None
            フィルタリングするカテゴリID、またはNone（すべて表示）
        """
        self.category_filter = category_id
        self.search_query = None  # 検索クエリをクリア
        self.refresh()

    def search(self, query):
        """
        書籍を検索する。

        Parameters
        ----------
        query : str
            検索クエリ
        """
        self.search_query = query
        self.refresh()

    def clear_search(self):
        """検索をクリアしてすべての書籍を表示する。"""
        self.search_query = None
        self.refresh()

    def update_book_item(self, book_id):
        """
        特定の書籍アイテムを更新する。

        Parameters
        ----------
        book_id : int
            更新する書籍ID
        """
        # book_idに一致するアイテムを検索
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == book_id:
                # 書籍情報を更新
                book = self.library_controller.get_book(book_id)
                if book:
                    widget = self.list_widget.itemWidget(item)
                    if isinstance(widget, BookListItemWidget):
                        widget.update_book_info(book)
                break

    def select_book(self, book_id, emit_signal=True):
        """
        書籍を選択状態にする。

        Parameters
        ----------
        book_id : int
            選択する書籍ID
        emit_signal : bool, optional
            選択シグナルを発火するかどうか
        """
        # book_idに一致するアイテムを検索
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == book_id:
                # アイテムを選択
                self.list_widget.setCurrentItem(item)

                # シグナルを発火（オプション）
                if emit_signal:
                    self.book_selected.emit(book_id)
                break

    def get_selected_book_id(self):
        """
        現在選択されている書籍IDを取得する。

        Returns
        -------
        int または None
            選択されている書籍ID、もしくは選択がない場合はNone
        """
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
