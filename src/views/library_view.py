from PyQt6.QtCore import QByteArray, QEvent, QSize, Qt, QTimer, pyqtSignal
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

        # 初期状態ではプレースホルダー表示
        self.cover_label.setText("...")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 画像読み込みを遅延実行
        QTimer.singleShot(50, self.load_cover_image)

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
        # カテゴリ情報
        if book.category_id:
            self.category_label = QLabel(f"Category: {book.category_name}")
            self.category_label.setStyleSheet("color: green;")
            info_layout.addWidget(self.category_label)
        elif book.series_id and book.db_manager.get_series(book.series_id).get(
            "category_id"
        ):
            # シリーズのカテゴリを表示
            series = book.db_manager.get_series(book.series_id)
            if series and series.get("category_id"):
                category = book.db_manager.get_category(series.get("category_id"))
                if category:
                    self.category_label = QLabel(
                        f"Category: {category['name']} (from series)"
                    )
                    info_layout.addWidget(self.category_label)
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

    def load_cover_image(self):
        """表紙画像を非同期で読み込む"""
        try:
            # より小さいサムネイルサイズで取得
            cover_data = self.book.get_cover_image(thumbnail_size=(48, 64))
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(cover_data))
                self.cover_label.setPixmap(pixmap)
            else:
                # デフォルト表紙
                self.cover_label.setText("No Cover")
                self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            print(f"Error loading cover: {e}")
            # エラー時も表示を変えない（目立たせない）

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
        self.cover_label.setFixedSize(150, 200)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        # 初期状態ではプレースホルダー表示
        self.cover_label.setText("Loading...")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 画像読み込みを遅延実行
        QTimer.singleShot(50, self.load_cover_image)

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

        # シリーズ情報の後にカテゴリ情報を追加
        if book.category_id:
            self.category_label = QLabel(f"Category: {book.category_name}")
            layout.addWidget(self.category_label)
        elif book.series_id and book.db_manager.get_series(book.series_id).get(
            "category_id"
        ):
            # シリーズのカテゴリを表示
            series = book.db_manager.get_series(book.series_id)
            if series and series.get("category_id"):
                category = book.db_manager.get_category(series.get("category_id"))
                if category:
                    self.category_label = QLabel(
                        f"Category: {category['name']} (from series)"
                    )
                    layout.addWidget(self.category_label)

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

    def load_cover_image(self):
        """表紙画像を非同期で読み込む"""
        try:
            # 小さいサムネイルサイズで取得
            cover_data = self.book.get_cover_image(thumbnail_size=(150, 200))
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(cover_data))
                self.cover_label.setPixmap(pixmap)
            else:
                # デフォルト表紙
                self.cover_label.setText("No Cover")
                self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            print(f"Error loading cover: {e}")
            self.cover_label.setText("Error")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


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
    books_selected = pyqtSignal(list)  # 選択された複数の book_id のリスト

    def __init__(self, library_controller, parent=None):
        """コンストラクタ"""
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

        # 選択中の書籍ID（単一選択時）
        self.selected_book_id = None

        # 選択中の書籍IDのリスト（複数選択時）
        self.selected_book_ids = set()

        # 複数選択モードかどうか
        self.multi_select_mode = False

        # フィルタ設定
        self.category_filter = None
        self.search_query = None

        # 書籍ウィジェットのマップ
        self.book_widgets = {}

        # 遅延ロード関連のプロパティ
        self.all_books = []  # 全書籍データ
        self.loaded_count = 0  # 読み込み済み件数
        self.batch_size = 20  # 一度に読み込む件数
        self.is_loading = False  # 読み込み中フラグ

        # グリッド列数とアイテムの標準サイズ
        self.grid_columns = 4  # デフォルト値
        self.item_width = 150  # 書籍アイテムの幅（ウィジェット幅+マージン）
        self.last_viewport_width = 0  # 前回のビューポート幅を記録

        # スクロールイベントを監視
        self.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

        # 空のプレースホルダーを配置
        self.placeholder = QLabel("Loading books...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

    def resizeEvent(self, event):
        """ウィジェットのサイズが変わったときに呼ばれる"""
        super().resizeEvent(event)

        # ビューポートの現在の幅を取得
        current_width = self.viewport().width()

        # 前回と同じ幅なら何もしない
        if current_width == self.last_viewport_width:
            return

        self.last_viewport_width = current_width

        # 列数を更新して再レイアウト
        self.calculate_grid_columns()

        # 書籍がロードされている場合のみ再レイアウト
        if self.book_widgets:
            self.relayout_grid()

    def calculate_grid_columns(self):
        """ビューポートの幅に基づいて列数を計算"""
        viewport_width = self.viewport().width()

        # 利用可能な幅に基づいて列数を計算
        # 20pxはスクロールバーやマージン用の余白
        available_width = max(1, viewport_width - 20)

        # 列数を計算（少なくとも1列）
        new_columns = max(1, available_width // self.item_width)

        # 列数が変わった場合に更新
        if new_columns != self.grid_columns:
            print(
                f"Changing grid columns from {self.grid_columns} to {new_columns} (viewport width: {viewport_width}px)"
            )
            self.grid_columns = new_columns
            return True
        return False

    def relayout_grid(self):
        """グリッドレイアウトを現在の列数で再レイアウト"""

        # 現在表示されているウィジェットを取得
        widgets = []
        for book_id, widget in self.book_widgets.items():
            # グリッドレイアウトからウィジェットを取り外す
            self.grid_layout.removeWidget(widget)
            widgets.append((book_id, widget))

        # 列数に基づいて再配置
        for i, (book_id, widget) in enumerate(widgets):
            row = i // self.grid_columns
            col = i % self.grid_columns
            self.grid_layout.addWidget(widget, row, col)

        # コンテンツウィジェットの更新を強制
        self.content_widget.updateGeometry()

    def refresh(self):
        """ライブラリを再読み込みして表示を更新する。（遅延ロード対応版）"""
        # グリッドをクリア
        self._clear_grid()

        # 遅延ロード用の変数をリセット
        self.loaded_count = 0

        # プレースホルダーを表示
        self.placeholder = QLabel("Loading books...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

        # 非同期で書籍データを取得
        QTimer.singleShot(50, self._load_books_async)

    def _load_books_async(self):
        """書籍データを非同期で読み込む"""
        # 書籍を取得
        self.all_books = self._get_filtered_books()

        # プレースホルダーを削除
        if self.placeholder.parent() == self.content_widget:
            self.placeholder.setParent(None)
            self.placeholder.deleteLater()

        # 列数を計算
        self.calculate_grid_columns()

        # 最初のバッチをロード
        self.load_more_books()

    def load_more_books(self):
        """追加の書籍を読み込む"""
        if self.is_loading or self.loaded_count >= len(self.all_books):
            return

        self.is_loading = True

        # 次のバッチのインデックス範囲を計算
        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_books))

        # 書籍をグリッドに配置
        for i in range(start_idx, end_idx):
            book = self.all_books[i]
            row = i // self.grid_columns
            col = i % self.grid_columns

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

        # 読み込み済み件数を更新
        self.loaded_count = end_idx

        # 読み込み中フラグをリセット
        self.is_loading = False

        # すべての書籍を読み込んだか確認
        if self.loaded_count < len(self.all_books):
            # まだ未読込の書籍があればステータスメッセージを更新
            try:
                main_window = self.window()
                if main_window and hasattr(main_window, "statusBar"):
                    main_window.statusBar.showMessage(
                        f"Loaded {self.loaded_count} of {len(self.all_books)} books"
                    )
            except Exception as e:
                # ステータスバー更新でエラーが発生しても処理を続行
                print(f"Error updating status bar: {e}")

    def _load_books_async(self):
        """書籍データを非同期で読み込む"""
        # 書籍を取得
        self.all_books = self._get_filtered_books()

        # プレースホルダーを削除
        if self.placeholder.parent() == self.content_widget:
            self.placeholder.setParent(None)
            self.placeholder.deleteLater()

        # 最初のバッチをロード
        self.load_more_books()

    def check_scroll_position(self, value):
        """スクロール位置をチェックして、必要なら追加の書籍を読み込む"""
        # スクロールが下部に近づいたら追加読み込み
        scrollbar = self.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:  # 70%以上スクロールしたら
            self.load_more_books()

    def _populate_grid(self, books):
        """
        書籍をグリッドに配置する。（遅延ロード対応版）

        Parameters
        ----------
        books : list
            Book オブジェクトのリスト
        """
        # 書籍データを保存
        self.all_books = books

        # 列数を更新
        self.update_grid_columns()

        # 最初のバッチだけ即時表示
        self.loaded_count = 0
        self.load_more_books()

    def _clear_grid(self):
        """グリッドレイアウトをクリアする。"""
        # すべての子ウィジェットを削除
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.book_widgets = {}
        self.selected_book_ids = set()
        self.selected_book_id = None

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

        # 複数選択モードの場合
        if self.multi_select_mode:
            ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            shift_pressed = event.modifiers() & Qt.KeyboardModifier.ShiftModifier

            if shift_pressed and self.selected_book_ids:
                # シフトキーが押されている場合、最後に選択したアイテムから連続選択
                last_id = (
                    list(self.selected_book_ids)[-1]
                    if self.selected_book_ids
                    else book_id
                )
                all_ids = list(self.book_widgets.keys())
                try:
                    start_idx = all_ids.index(last_id)
                    end_idx = all_ids.index(book_id)
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                    for idx in range(start_idx, end_idx + 1):
                        self._select_book(all_ids[idx], add_to_selection=True)
                except ValueError:
                    # インデックスが見つからない場合は単一選択として扱う
                    if not ctrl_pressed:
                        self._clear_selection()
                    self._select_book(book_id, add_to_selection=True)
            else:
                # Ctrlキーが押されていない場合は選択をクリア
                if not ctrl_pressed:
                    self._clear_selection()

                # 選択状態を切り替える
                if book_id in self.selected_book_ids:
                    self._deselect_book(book_id)
                else:
                    self._select_book(book_id, add_to_selection=True)

            # 複数選択シグナルを発火
            self.books_selected.emit(list(self.selected_book_ids))
        else:
            # 単一選択モード
            self._clear_selection()
            self._select_book(book_id)
            self.selected_book_id = book_id
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

        # 複数選択されているかどうかで表示内容を変更
        is_multiple_selected = len(self.selected_book_ids) > 1

        if is_multiple_selected and book_id in self.selected_book_ids:
            # 複数選択のコンテキストメニュー
            selection_count = len(self.selected_book_ids)
            menu.addAction(f"{selection_count} books selected")
            menu.addSeparator()

            # 一括編集
            edit_action = QAction("Edit Selected Books", self)
            edit_action.triggered.connect(
                lambda: self._batch_edit_metadata(list(self.selected_book_ids))
            )
            menu.addAction(edit_action)

            # 一括シリーズ追加
            add_to_series_action = QAction("Add Selected to Series", self)
            add_to_series_action.triggered.connect(
                lambda: self._batch_add_to_series(list(self.selected_book_ids))
            )
            menu.addAction(add_to_series_action)

            # 一括シリーズ削除
            remove_from_series_action = QAction("Remove Selected from Series", self)
            remove_from_series_action.triggered.connect(
                lambda: self._batch_remove_from_series(list(self.selected_book_ids))
            )
            menu.addAction(remove_from_series_action)

            menu.addSeparator()

            # 一括ステータス変更
            mark_action = QMenu("Mark Selected as", menu)

            unread_action = QAction("Unread", self)
            unread_action.triggered.connect(
                lambda: self._batch_mark_as_status(
                    list(self.selected_book_ids), Book.STATUS_UNREAD
                )
            )
            mark_action.addAction(unread_action)

            reading_action = QAction("Reading", self)
            reading_action.triggered.connect(
                lambda: self._batch_mark_as_status(
                    list(self.selected_book_ids), Book.STATUS_READING
                )
            )
            mark_action.addAction(reading_action)

            completed_action = QAction("Completed", self)
            completed_action.triggered.connect(
                lambda: self._batch_mark_as_status(
                    list(self.selected_book_ids), Book.STATUS_COMPLETED
                )
            )
            mark_action.addAction(completed_action)

            menu.addMenu(mark_action)

            menu.addSeparator()

            # 一括削除
            remove_action = QAction("Remove Selected from Library", self)
            remove_action.triggered.connect(
                lambda: self._batch_remove_books(list(self.selected_book_ids))
            )
            menu.addAction(remove_action)
        else:
            # 単一選択のコンテキストメニュー
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.book_selected.emit(book_id))
            menu.addAction(open_action)

            menu.addSeparator()

            edit_action = QAction("Edit Metadata", self)
            edit_action.triggered.connect(lambda: self._edit_metadata(book_id))
            menu.addAction(edit_action)

            if self.library_controller.get_book(book_id).series_id is None:
                add_to_series_action = QAction("Add to Series", self)
                add_to_series_action.triggered.connect(
                    lambda: self._add_to_series(book_id)
                )
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

            # 選択に追加/削除（複数選択モードの場合）
            if self.multi_select_mode:
                if book_id in self.selected_book_ids:
                    select_action = QAction("Remove from Selection", self)
                    select_action.triggered.connect(
                        lambda: self._deselect_book(book_id)
                    )
                else:
                    select_action = QAction("Add to Selection", self)
                    select_action.triggered.connect(
                        lambda: self._select_book(book_id, add_to_selection=True)
                    )
                menu.addAction(select_action)

                menu.addSeparator()

            remove_action = QAction("Remove from Library", self)
            remove_action.triggered.connect(lambda: self._remove_book(book_id))
            menu.addAction(remove_action)

        # メニューを表示
        menu.exec(position)

    def _select_book(self, book_id, add_to_selection=False):
        """
        書籍を選択状態にする。

        Parameters
        ----------
        book_id : int
            選択する書籍ID
        add_to_selection : bool
            既存の選択に追加するかどうか
        """
        if book_id not in self.book_widgets:
            return

        if not add_to_selection:
            self._clear_selection()

        # 選択状態を設定
        self.selected_book_ids.add(book_id)
        self.book_widgets[book_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

    def _deselect_book(self, book_id):
        """
        書籍の選択を解除する。

        Parameters
        ----------
        book_id : int
            選択解除する書籍ID
        """
        if book_id not in self.book_widgets:
            return

        if book_id in self.selected_book_ids:
            self.selected_book_ids.remove(book_id)
            self.book_widgets[book_id].setStyleSheet("")

    def _clear_selection(self):
        """すべての選択を解除する。"""
        for book_id in list(self.selected_book_ids):
            if book_id in self.book_widgets:
                self.book_widgets[book_id].setStyleSheet("")

        self.selected_book_ids.clear()
        self.selected_book_id = None

    def toggle_multi_select_mode(self, enabled):
        """
        複数選択モードを切り替える。

        Parameters
        ----------
        enabled : bool
            複数選択モードを有効にするかどうか
        """
        self.multi_select_mode = enabled

        # モード切替時に選択をクリア
        self._clear_selection()

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

    def _batch_edit_metadata(self, book_ids):
        """
        複数書籍のメタデータ一括編集処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
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

    def _batch_add_to_series(self, book_ids):
        """
        複数書籍を一括でシリーズに追加する処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
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

    def _batch_remove_from_series(self, book_ids):
        """
        複数書籍を一括でシリーズから削除する処理。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
        """
        for book_id in book_ids:
            book = self.library_controller.get_book(book_id)
            if book and book.series_id:
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

    def _batch_mark_as_status(self, book_ids, status):
        """
        複数書籍の読書状態を一括で設定する。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
        status : str
            設定する状態
        """
        for book_id in book_ids:
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

    def _batch_remove_books(self, book_ids):
        """
        複数書籍を一括で削除する処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_ids : list
            削除する書籍IDリスト
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
        # ビューが表示された時に列数を再計算
        QTimer.singleShot(50, self.ensure_correct_layout)

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
        # 検索結果表示後に列数を再計算
        QTimer.singleShot(50, self.ensure_correct_layout)

    def clear_search(self):
        """検索をクリアしてすべての書籍を表示する。"""
        self.search_query = None
        self.refresh()
        # ビュー更新後に列数を再計算
        QTimer.singleShot(50, self.ensure_correct_layout)

    def update_book_item(self, book_id):
        """
        特定の書籍アイテムを更新する。

        Parameters
        ----------
        book_id : int
            更新する書籍ID
        """
        if book_id in self.book_widgets:
            # ローカルキャッシュをクリアせずにデータベースから最新の情報を取得
            self.library_controller.db_manager.close()  # 念のため接続を閉じて再接続
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

        # 単一選択モードに切り替え
        self.multi_select_mode = False

        # 選択をクリアして新しい選択を設定
        self._clear_selection()
        self._select_book(book_id)
        self.selected_book_id = book_id

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

    def get_selected_book_ids(self):
        """
        現在選択されている複数の書籍IDリストを取得する。

        Returns
        -------
        list
            選択されている書籍IDのリスト
        """
        return list(self.selected_book_ids)

    def select_all(self):
        """すべての表示されている書籍を選択する。"""
        self._clear_selection()

        for book_id in self.book_widgets:
            self._select_book(book_id, add_to_selection=True)

        if self.selected_book_ids:
            self.books_selected.emit(list(self.selected_book_ids))

    def eventFilter(self, obj, event):
        """イベントフィルタでリサイズイベントを検知"""
        if obj == self.viewport() and event.type() == QEvent.Type.Resize:
            # ビューポートのリサイズ時に列数を再計算して更新
            self.update_grid_columns()
        return super().eventFilter(obj, event)

    def update_grid_columns(self):
        """ビューポートの幅に基づいて列数を計算"""
        viewport_width = self.viewport().width()

        # 書籍アイテムの幅 (固定幅 + マージン)
        item_width = 180  # BookGridItemWidgetのfixedWidth(150) + マージン

        # 利用可能な幅に基づいて列数を計算
        available_width = viewport_width - 20  # スクロールバーや余白のための調整
        new_columns = max(1, available_width // item_width)

        # 列数が変わった場合のみ更新
        if new_columns != self.grid_columns:
            self.grid_columns = new_columns

            # 表示中の場合、レイアウトを更新
            if not self.is_loading and self.loaded_count > 0:
                self.relayout_grid()

    def ensure_correct_layout(self):
        """現在のビューポートサイズに基づいて正しいレイアウトを確保する"""
        if self.calculate_grid_columns() and self.book_widgets:
            self.relayout_grid()


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
    books_selected = pyqtSignal(list)  # 選択された複数の book_id のリスト

    def __init__(self, library_controller, parent=None):
        """コンストラクタ"""
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

        # 複数選択モードかどうか
        self.multi_select_mode = False

        # フィルタ設定
        self.category_filter = None
        self.search_query = None

        # 遅延ロード関連のプロパティ
        self.all_books = []  # 全書籍データ
        self.loaded_count = 0  # 読み込み済み件数
        self.batch_size = 30  # 一度に読み込む件数
        self.is_loading = False  # 読み込み中フラグ

        # スクロールイベントを監視
        self.list_widget.verticalScrollBar().valueChanged.connect(
            self.check_scroll_position
        )

        # Loading表示用のアイテム
        self.loading_item = QListWidgetItem("Loading more books...")
        self.loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # ライブラリを読み込む
        self.refresh()

    def refresh(self):
        """ライブラリを再読み込みして表示を更新する。（遅延ロード対応版）"""
        # リストをクリア
        self.list_widget.clear()

        # 遅延ロード用の変数をリセット
        self.loaded_count = 0

        # 一時的にローディングアイテムを表示
        self.list_widget.addItem("Loading books...")

        # 非同期で書籍データを取得
        QTimer.singleShot(50, self._load_books_async)

    def _load_books_async(self):
        """書籍データを非同期で読み込む"""
        # 書籍を取得
        self.all_books = self._get_filtered_books()

        # リストをクリア
        self.list_widget.clear()

        # 最初のバッチをロード
        self.load_more_books()

    def load_more_books(self):
        """追加の書籍を読み込む"""
        if self.is_loading or self.loaded_count >= len(self.all_books):
            return

        self.is_loading = True

        # ローディングアイテムを一時的に削除
        try:
            self.list_widget.takeItem(self.list_widget.count() - 1)
        except:
            pass

        # 次のバッチのインデックス範囲を計算
        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_books))

        # 書籍をリストに追加
        for i in range(start_idx, end_idx):
            book = self.all_books[i]

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

        # まだロードする書籍が残っていれば、ローディングアイテムを追加
        if end_idx < len(self.all_books):
            self.list_widget.addItem("Loading more books...")

        # 読み込み済み件数を更新
        self.loaded_count = end_idx

        # 読み込み中フラグをリセット
        self.is_loading = False

        # すべての書籍を読み込んだか確認
        if self.loaded_count < len(self.all_books):
            # まだ未読込の書籍があればステータスメッセージを更新
            try:
                if self.window() and hasattr(self.window(), "statusBar"):
                    self.window().statusBar.showMessage(
                        f"Loaded {self.loaded_count} of {len(self.all_books)} books"
                    )
            except Exception as e:
                # ステータスバー更新でエラーが発生しても処理を続行
                print(f"Error updating status bar: {e}")

    def check_scroll_position(self, value):
        """スクロール位置をチェックして、必要なら追加の書籍を読み込む"""
        # スクロールが下部に近づいたら追加読み込み
        scrollbar = self.list_widget.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:  # 70%以上スクロールしたら
            self.load_more_books()

    def _populate_list(self, books):
        """
        書籍をリストに追加する。（遅延ロード対応版）

        Parameters
        ----------
        books : list
            Book オブジェクトのリスト
        """
        # 書籍データを保存
        self.all_books = books

        # リストをクリア
        self.list_widget.clear()

        # 最初のバッチをロード
        self.loaded_count = 0
        self.load_more_books()

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

    def toggle_multi_select_mode(self, enabled):
        """
        複数選択モードを切り替える。

        Parameters
        ----------
        enabled : bool
            複数選択モードを有効にするかどうか
        """
        self.multi_select_mode = enabled

        # 選択モードを変更
        if enabled:
            self.list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )
        else:
            self.list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.SingleSelection
            )

        # 現在の選択をクリア
        self.list_widget.clearSelection()

    def _on_item_clicked(self, item):
        """
        リストアイテムがクリックされたときの処理。

        Parameters
        ----------
        item : QListWidgetItem
            クリックされたアイテム
        """
        book_id = item.data(Qt.ItemDataRole.UserRole)

        # 複数選択モードの場合
        if self.multi_select_mode:
            selected_items = self.list_widget.selectedItems()
            selected_ids = [
                item.data(Qt.ItemDataRole.UserRole) for item in selected_items
            ]
            self.books_selected.emit(selected_ids)
        else:
            # 単一選択モード
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

            # 複数選択されているか確認
            selected_items = self.list_widget.selectedItems()
            if len(selected_items) > 1 and item in selected_items:
                # 複数選択のコンテキストメニュー
                selected_ids = [
                    item.data(Qt.ItemDataRole.UserRole) for item in selected_items
                ]
                self._show_batch_context_menu(global_pos, selected_ids)
            else:
                # 単一選択のコンテキストメニュー
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

    def _show_batch_context_menu(self, position, book_ids):
        """
        複数選択時のコンテキストメニューを表示する。

        Parameters
        ----------
        position : QPoint
            表示位置
        book_ids : list
            選択された書籍IDのリスト
        """
        menu = QMenu()

        # 選択数を表示
        selection_count = len(book_ids)
        menu.addAction(f"{selection_count} books selected")
        menu.addSeparator()

        # 一括編集
        edit_action = QAction("Edit Selected Books", self)
        edit_action.triggered.connect(lambda: self._batch_edit_metadata(book_ids))
        menu.addAction(edit_action)

        # 一括シリーズ追加
        add_to_series_action = QAction("Add Selected to Series", self)
        add_to_series_action.triggered.connect(
            lambda: self._batch_add_to_series(book_ids)
        )
        menu.addAction(add_to_series_action)

        # 一括シリーズ削除
        remove_from_series_action = QAction("Remove Selected from Series", self)
        remove_from_series_action.triggered.connect(
            lambda: self._batch_remove_from_series(book_ids)
        )
        menu.addAction(remove_from_series_action)

        menu.addSeparator()

        # 一括ステータス変更
        mark_action = QMenu("Mark Selected as", menu)

        unread_action = QAction("Unread", self)
        unread_action.triggered.connect(
            lambda: self._batch_mark_as_status(book_ids, Book.STATUS_UNREAD)
        )
        mark_action.addAction(unread_action)

        reading_action = QAction("Reading", self)
        reading_action.triggered.connect(
            lambda: self._batch_mark_as_status(book_ids, Book.STATUS_READING)
        )
        mark_action.addAction(reading_action)

        completed_action = QAction("Completed", self)
        completed_action.triggered.connect(
            lambda: self._batch_mark_as_status(book_ids, Book.STATUS_COMPLETED)
        )
        mark_action.addAction(completed_action)

        menu.addMenu(mark_action)

        menu.addSeparator()

        # 一括削除
        remove_action = QAction("Remove Selected from Library", self)
        remove_action.triggered.connect(lambda: self._batch_remove_books(book_ids))
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

    def _batch_edit_metadata(self, book_ids):
        """
        複数書籍のメタデータ一括編集処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
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

    def _batch_add_to_series(self, book_ids):
        """
        複数書籍を一括でシリーズに追加する処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
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

    def _batch_remove_from_series(self, book_ids):
        """
        複数書籍を一括でシリーズから削除する処理。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
        """
        for book_id in book_ids:
            book = self.library_controller.get_book(book_id)
            if book and book.series_id:
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

    def _batch_mark_as_status(self, book_ids, status):
        """
        複数書籍の読書状態を一括で設定する。

        Parameters
        ----------
        book_ids : list
            対象の書籍IDリスト
        status : str
            設定する状態
        """
        for book_id in book_ids:
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

    def _batch_remove_books(self, book_ids):
        """
        複数書籍を一括で削除する処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        book_ids : list
            削除する書籍IDリスト
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
        # 単一選択モードに戻す
        self.toggle_multi_select_mode(False)

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
        現在選択されている書籍IDを取得する（単一選択モード）。

        Returns
        -------
        int または None
            選択されている書籍ID、もしくは選択がない場合はNone
        """
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def get_selected_book_ids(self):
        """
        現在選択されている複数の書籍IDリストを取得する。

        Returns
        -------
        list
            選択されている書籍IDのリスト
        """
        selected_items = self.list_widget.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

    def select_all(self):
        """すべての表示されている書籍を選択する。"""
        # 複数選択モードを有効化
        self.toggle_multi_select_mode(True)

        # すべてのアイテムを選択
        self.list_widget.selectAll()

        # シグナルを発火
        selected_ids = self.get_selected_book_ids()
        if selected_ids:
            self.books_selected.emit(selected_ids)
