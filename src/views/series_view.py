import re

from PyQt6.QtCore import QByteArray, QEvent, QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
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


class SeriesGridItemWidget(QWidget):
    """
    グリッドビュー内のシリーズアイテムのカスタムウィジェット。

    Parameters
    ----------
    series : Series
        表示するシリーズオブジェクト
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, series, parent=None):
        """
        Parameters
        ----------
        series : Series
            シリーズ情報
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.series = series
        self.cover_loaded = False

        # レイアウトの設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 表紙画像
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(150, 200)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        # 初期状態ではプレースホルダー表示
        self.cover_label.setText("Series")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #f0f0f0;")

        # 画像の読み込みは遅延させる
        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # シリーズ名
        self.title_label = QLabel(self._truncate_text(series.name, 25))
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setToolTip(series.name)
        layout.addWidget(self.title_label)

        # 書籍数
        book_count = len(series.books)
        self.count_label = QLabel(
            f"{book_count} {'books' if book_count != 1 else 'book'}"
        )
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        # カテゴリ
        if series.category_name:
            self.category_badge = QLabel(self._truncate_text(series.category_name, 20))
            self.category_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.category_badge.setStyleSheet(
                "background-color: #e0e0e0; border-radius: 3px; padding: 2px;"
            )
            self.category_badge.setToolTip(series.category_name)
            layout.addWidget(self.category_badge)

        # 読書進捗
        status_counts = series.get_reading_status()
        total_books = sum(status_counts.values())
        if total_books > 0:
            completed = status_counts.get(Book.STATUS_COMPLETED, 0)
            progress = int(completed / total_books * 100)

            self.progress_label = QLabel(f"Completed: {progress}%")
            self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.progress_label)

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

    def load_cover_image(self):
        """シリーズの表紙画像を非同期で読み込む"""
        if self.cover_loaded:
            return

        try:
            # シリーズの代表的な表紙画像を取得
            cover_data = self.get_series_cover_image(self.series)
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(cover_data))
                self.cover_label.setPixmap(pixmap)
                self.cover_loaded = True
            else:
                # デフォルト表紙
                self.cover_label.setText("Series")
                self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.cover_loaded = True  # 読み込み完了とマーク
        except Exception as e:
            print(f"Error loading series cover: {e}")
            self.cover_label.setText("Series")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cover_loaded = True  # エラーでも読み込み完了とマーク

    def get_series_cover_image(self, series):
        """
        シリーズの表紙画像を取得する。
        シリーズの最初の書籍の表紙を使用する。

        Parameters
        ----------
        series : Series
            シリーズオブジェクト

        Returns
        -------
        bytes または None
            表紙画像のバイナリデータ、もしくはエラー時はNone
        """

        # 自然順でソート
        def natural_sort_key(book):
            """文字列内の数値を数値として扱うキー関数"""
            title = book.title if book.title else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        books = sorted(
            series.books,
            key=lambda b: (b.series_order or float("inf"), natural_sort_key(b)),
        )

        if books:
            first_book = books[0]
            return first_book.get_cover_image(thumbnail_size=(150, 200))
        return None

    def update_series_info(self, series):
        """
        シリーズ情報を更新する。

        Parameters
        ----------
        series : Series
            更新後のシリーズ情報
        """
        self.series = series

        # シリーズ名を更新
        self.title_label.setText(self._truncate_text(series.name, 25))
        self.title_label.setToolTip(series.name)

        # 書籍数を更新
        book_count = len(series.books)
        self.count_label.setText(
            f"{book_count} {'books' if book_count != 1 else 'book'}"
        )

        # 読書進捗を更新
        if hasattr(self, "progress_label"):
            status_counts = series.get_reading_status()
            total_books = sum(status_counts.values())
            if total_books > 0:
                completed = status_counts.get(Book.STATUS_COMPLETED, 0)
                progress = int(completed / total_books * 100)
                self.progress_label.setText(f"Completed: {progress}%")

        # 表紙は再読み込み
        self.cover_loaded = False
        self.cover_label.setText("Series")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        QTimer.singleShot(50, self.load_cover_image)

    def enterEvent(self, event):
        """ウィジェットにマウスが入ったとき、優先的に表紙を読み込む"""
        if not self.cover_loaded:
            QTimer.singleShot(10, self.load_cover_image)
        super().enterEvent(event)


class SeriesListItemWidget(QWidget):
    """
    リストビュー内のシリーズアイテムのカスタムウィジェット。

    Parameters
    ----------
    series : Series
        表示するシリーズオブジェクト
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, series, parent=None):
        """
        Parameters
        ----------
        series : Series
            シリーズ情報
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.series = series

        # レイアウトの設定
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # 表紙画像
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(48, 64)
        self.cover_label.setScaledContents(True)
        self.cover_label.setFrameShape(QFrame.Shape.Box)

        # シリーズの代表的な表紙画像を取得または生成
        cover_data = self.get_series_cover_image(series)
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(cover_data))
            self.cover_label.setPixmap(pixmap)
        else:
            # デフォルト表紙
            self.cover_label.setText("Series")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.cover_label)

        # シリーズ情報レイアウト
        info_layout = QVBoxLayout()

        # シリーズ名
        self.title_label = QLabel(series.name)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label)

        # 書籍数と読書状態
        book_count = len(series.books)
        status_counts = series.get_reading_status()
        completed = status_counts.get(Book.STATUS_COMPLETED, 0)
        reading = status_counts.get(Book.STATUS_READING, 0)
        unread = status_counts.get(Book.STATUS_UNREAD, 0)

        self.count_label = QLabel(
            f"{book_count} {'books' if book_count != 1 else 'book'} "
            f"({completed} completed, {reading} reading, {unread} unread)"
        )
        info_layout.addWidget(self.count_label)

        # カテゴリ
        if series.category_name:
            self.category_label = QLabel(f"Category: {series.category_name}")
            info_layout.addWidget(self.category_label)

        layout.addLayout(info_layout)
        layout.setStretch(1, 1)  # 情報部分を伸縮させる

    def get_series_cover_image(self, series):
        """
        シリーズの表紙画像を取得する。
        シリーズの最初の書籍の表紙を使用する。

        Parameters
        ----------
        series : Series
            シリーズオブジェクト

        Returns
        -------
        bytes または None
            表紙画像のバイナリデータ、もしくはエラー時はNone
        """

        # 自然順でソート
        def natural_sort_key(book):
            """文字列内の数値を数値として扱うキー関数"""
            title = book.title if book.title else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        books = sorted(
            series.books,
            key=lambda b: (b.series_order or float("inf"), natural_sort_key(b)),
        )

        if books:
            first_book = books[0]
            return first_book.get_cover_image()
        return None

    def update_series_info(self, series):
        """
        シリーズ情報を更新する。

        Parameters
        ----------
        series : Series
            更新後のシリーズ情報
        """
        self.series = series

        # シリーズ名を更新
        self.title_label.setText(series.name)

        # 書籍数と読書状態を更新
        book_count = len(series.books)
        status_counts = series.get_reading_status()
        completed = status_counts.get(Book.STATUS_COMPLETED, 0)
        reading = status_counts.get(Book.STATUS_READING, 0)
        unread = status_counts.get(Book.STATUS_UNREAD, 0)

        self.count_label.setText(
            f"{book_count} {'books' if book_count != 1 else 'book'} "
            f"({completed} completed, {reading} reading, {unread} unread)"
        )


class SeriesGridView(QScrollArea):
    """
    シリーズをグリッド形式で表示するビュー。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    # カスタムシグナル
    series_selected = pyqtSignal(int)  # series_id

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
        # コンテンツマージンを最小化
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        # 選択中のシリーズID
        self.selected_series_id = None

        # フィルタ設定
        self.category_filter = None
        self.search_query = None

        # シリーズウィジェットのマップ
        self.series_widgets = {}

        # 遅延ロード関連のプロパティ
        self.all_series = []  # 全シリーズデータ
        self.loaded_count = 0  # 読み込み済み件数
        self.batch_size = 15  # 一度に読み込む件数
        self.is_loading = False  # 読み込み中フラグ
        self.loading_timer = None  # 読み込みタイマー
        self.visible_widgets = set()  # 現在表示範囲内にあるウィジェット

        # グリッド列数とアイテムの標準サイズ
        self.grid_columns = 3  # デフォルト値
        # SeriesGridItemWidgetのsetFixedSizに合わせて調整
        self.item_width = 190
        self.last_viewport_width = 0  # 前回のビューポート幅を記録

        # スクロールイベントを監視
        self.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

        # 表示状態も監視（表示されたときに読み込みを最適化するため）
        self.installEventFilter(self)

        # 読み込み中のプレースホルダーを表示
        self.placeholder = QLabel("Loading series...")
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

        # シリーズがロードされている場合のみ再レイアウト
        if self.series_widgets:
            self.relayout_grid()

    def eventFilter(self, obj, event):
        """表示イベントをフィルタリングして、表示されたときに最適化する"""
        if event.type() == QEvent.Type.Show:
            # 表示されたときに一度だけスクロール位置をチェック
            QTimer.singleShot(100, self.update_visible_widgets)
        return super().eventFilter(obj, event)

    def calculate_grid_columns(self):
        """ビューポートの幅に基づいて列数を計算"""
        viewport_width = self.viewport().width()

        # 利用可能な幅に基づいて列数を計算
        # グリッドレイアウトの左右のマージン分を引く
        available_width = max(1, viewport_width - 10)  # 左右マージン各5px

        # 列数を計算（少なくとも1列）
        # 列間のスペース(10px)も考慮
        new_columns = max(1, int(available_width / self.item_width))

        # 列数が変わった場合に更新
        if new_columns != self.grid_columns:
            self.grid_columns = new_columns
            return True
        return False

    def relayout_grid(self):
        """グリッドレイアウトを現在の列数で再レイアウト"""

        # 現在表示されているウィジェットを取得
        widgets = []
        for series_id, widget in self.series_widgets.items():
            # グリッドレイアウトからウィジェットを取り外す
            self.grid_layout.removeWidget(widget)
            widgets.append((series_id, widget))

        # 列数に基づいて再配置
        for i, (series_id, widget) in enumerate(widgets):
            row = i // self.grid_columns
            col = i % self.grid_columns
            self.grid_layout.addWidget(widget, row, col)

        # コンテンツウィジェットのサイズ調整を強制
        width = min(self.grid_columns * self.item_width, self.viewport().width())

        # コンテンツウィジェットの更新を強制
        self.content_widget.updateGeometry()

        # 表示範囲内のウィジェットを更新
        QTimer.singleShot(50, self.update_visible_widgets)

    def refresh(self):
        """シリーズを再読み込みして表示を更新する。"""
        # グリッドをクリア
        self._clear_grid()

        # 遅延ロード用の変数をリセット
        self.loaded_count = 0

        # 読み込み中表示
        self.placeholder = QLabel("Loading series...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

        # 非同期でシリーズデータを取得
        QTimer.singleShot(50, self._load_series_async)

    def _load_series_async(self):
        """シリーズデータを非同期で読み込む"""
        # シリーズを取得
        self.all_series = self._get_filtered_series()

        # プレースホルダーを削除
        if self.placeholder.parent() == self.content_widget:
            self.placeholder.setParent(None)
            self.placeholder.deleteLater()

        # 列数を計算
        self.calculate_grid_columns()

        # 最初のバッチをロード
        self.load_more_series()

    def load_more_series(self):
        """追加のシリーズを読み込む"""
        if self.is_loading or self.loaded_count >= len(self.all_series):
            return

        self.is_loading = True

        # 次のバッチのインデックス範囲を計算
        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_series))

        # 自然順ソート（シリーズ名の中の数字を考慮）
        def natural_sort_key(series):
            name = series.name if series.name else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)
            ]

        sorted_series = sorted(self.all_series, key=natural_sort_key)

        # シリーズをグリッドに配置
        for i in range(start_idx, end_idx):
            if i >= len(sorted_series):
                break

            series = sorted_series[i]
            row = i // self.grid_columns
            col = i % self.grid_columns

            # シリーズウィジェットを作成
            series_widget = SeriesGridItemWidget(series)
            # ここでのサイズがitem_widthと一致することを確認
            series_widget.setFixedSize(190, 300)
            series_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            series_widget.mousePressEvent = (
                lambda event, s=series.id: self._on_series_clicked(event, s)
            )

            # グリッドに追加
            self.grid_layout.addWidget(series_widget, row, col)

            # マップに追加
            self.series_widgets[series.id] = series_widget

        # 読み込み済み件数を更新
        self.loaded_count = end_idx

        # 読み込み中フラグをリセット
        self.is_loading = False

        # すべてのシリーズを読み込んだか確認
        if self.loaded_count < len(self.all_series):
            # まだ未読込のシリーズがあればステータスメッセージを更新
            try:
                main_window = self.window()
                if main_window and hasattr(main_window, "statusBar"):
                    main_window.statusBar.showMessage(
                        f"Loaded {self.loaded_count} of {len(self.all_series)} series"
                    )
            except Exception as e:
                # ステータスバー更新でエラーが発生しても処理を続行
                print(f"Error updating status bar: {e}")

        # 表示範囲内のウィジェットの表紙を読み込む
        QTimer.singleShot(50, self.update_visible_widgets)

    def update_visible_widgets(self):
        """現在表示範囲内にあるウィジェットを特定し、表紙画像を優先的に読み込む"""
        if not self.series_widgets:
            return

        # スクロール領域の表示範囲を取得
        viewport_rect = self.viewport().rect()
        scrollbar_value = self.verticalScrollBar().value()

        # 表示範囲を調整（スクロール位置を考慮）
        visible_top = scrollbar_value
        visible_bottom = scrollbar_value + viewport_rect.height()

        # 表示範囲内のウィジェットを特定
        new_visible_widgets = set()

        for series_id, widget in self.series_widgets.items():
            widget_pos = widget.mapTo(self.content_widget, QPoint(0, 0))
            widget_top = widget_pos.y()
            widget_bottom = widget_top + widget.height()

            # ウィジェットが表示範囲内にあるか判定
            if widget_bottom >= visible_top and widget_top <= visible_bottom:
                new_visible_widgets.add(series_id)

                # まだ表紙が読み込まれていなければ読み込む
                if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
                    # 非同期で表紙を読み込む
                    QTimer.singleShot(10, widget.load_cover_image)

        # 表示ウィジェットセットを更新
        self.visible_widgets = new_visible_widgets

    def check_scroll_position(self, value):
        """スクロール位置をチェックして、必要なら追加のシリーズを読み込む"""
        # スクロールが下部に近づいたら追加読み込み
        scrollbar = self.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:  # 70%以上スクロールしたら
            self.load_more_series()

        # 表示範囲内のウィジェットを更新
        # 連続したスクロールの場合、タイマーをリセットして最後のスクロール後に実行
        if self.loading_timer:
            self.loading_timer.stop()

        self.loading_timer = QTimer()
        self.loading_timer.setSingleShot(True)
        self.loading_timer.timeout.connect(self.update_visible_widgets)
        self.loading_timer.start(100)  # 100ms後に実行（スクロール中は更新しない）

    def _clear_grid(self):
        """グリッドレイアウトをクリアする。"""
        # すべての子ウィジェットを削除
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.series_widgets = {}
        self.selected_series_id = None
        self.visible_widgets = set()

    def _get_filtered_series(self):
        """
        フィルタ条件に基づいてシリーズのリストを取得する。

        Returns
        -------
        list
            Series オブジェクトのリスト
        """
        # カテゴリフィルタがある場合はそれを適用
        series_list = self.library_controller.get_all_series(
            category_id=self.category_filter
        )

        # 検索クエリがある場合はフィルタリング
        if self.search_query:
            query = self.search_query.lower()
            filtered_list = []
            for series in series_list:
                # シリーズ名、カテゴリ名、書籍タイトルで検索
                if query in series.name.lower() or (
                    series.category_name and query in series.category_name.lower()
                ):
                    filtered_list.append(series)
                    continue

                # 書籍タイトルで検索
                for book in series.books:
                    if query in book.title.lower():
                        filtered_list.append(series)
                        break

            return filtered_list

        return series_list

    def _on_series_clicked(self, event, series_id):
        """
        シリーズクリック時の処理。

        Parameters
        ----------
        event : QMouseEvent
            マウスイベント
        series_id : int
            クリックされたシリーズのID
        """
        # 右クリックの場合はコンテキストメニューを表示
        if event.button() == Qt.MouseButton.RightButton:
            # PyQt6では globalPos() が非推奨になり、globalPosition().toPoint() を使用する
            global_pos = event.globalPosition().toPoint()
            self._show_context_menu(global_pos, series_id)
            return

        # 以前の選択をクリア
        if self.selected_series_id in self.series_widgets:
            self.series_widgets[self.selected_series_id].setStyleSheet("")

        # 新しい選択を設定
        self.selected_series_id = series_id
        self.series_widgets[series_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

        # 選択シグナルを発火
        self.series_selected.emit(series_id)

        # 優先的に表紙を読み込む
        widget = self.series_widgets[series_id]
        if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def _show_context_menu(self, position, series_id):
        """
        コンテキストメニューを表示する。

        Parameters
        ----------
        position : QPoint
            表示位置
        series_id : int
            対象のシリーズID
        """
        menu = QMenu()

        # シリーズを表示
        view_action = QAction("View Series", self)
        view_action.triggered.connect(lambda: self.series_selected.emit(series_id))
        menu.addAction(view_action)

        menu.addSeparator()

        # シリーズを編集
        edit_action = QAction("Edit Series", self)
        edit_action.triggered.connect(lambda: self._edit_series(series_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        # シリーズを削除
        remove_action = QAction("Remove Series", self)
        remove_action.triggered.connect(lambda: self._remove_series(series_id))
        menu.addAction(remove_action)

        # メニューを表示
        menu.exec(position)

    def _edit_series(self, series_id):
        """
        シリーズ編集処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        series_id : int
            対象のシリーズID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def _remove_series(self, series_id):
        """
        シリーズ削除処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        series_id : int
            削除するシリーズID
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
        シリーズを検索する。

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
        """検索をクリアしてすべてのシリーズを表示する。"""
        self.search_query = None
        self.refresh()
        # ビュー更新後に列数を再計算
        QTimer.singleShot(50, self.ensure_correct_layout)

    def update_series_item(self, series_id):
        """
        特定のシリーズアイテムを更新する。

        Parameters
        ----------
        series_id : int
            更新するシリーズID
        """
        if series_id in self.series_widgets:
            series = self.library_controller.get_series(series_id)
            if series:
                # シリーズウィジェットを更新
                widget = self.series_widgets[series_id]
                if isinstance(widget, SeriesGridItemWidget):
                    widget.update_series_info(series)

    def select_series(self, series_id, emit_signal=True):
        """
        シリーズを選択状態にする。

        Parameters
        ----------
        series_id : int
            選択するシリーズID
        emit_signal : bool, optional
            選択シグナルを発火するかどうか
        """
        # シリーズが表示されていない場合は何もしない
        if series_id not in self.series_widgets:
            return

        # 以前の選択をクリア
        if self.selected_series_id in self.series_widgets:
            self.series_widgets[self.selected_series_id].setStyleSheet("")

        # 新しい選択を設定
        self.selected_series_id = series_id
        self.series_widgets[series_id].setStyleSheet(
            "background-color: #e0e0ff; border: 1px solid #9090ff;"
        )

        # シグナルを発火（オプション）
        if emit_signal:
            self.series_selected.emit(series_id)

        # 優先的に表紙を読み込む
        widget = self.series_widgets[series_id]
        if isinstance(widget, SeriesGridItemWidget) and not widget.cover_loaded:
            QTimer.singleShot(10, widget.load_cover_image)

    def get_selected_series_id(self):
        """
        現在選択されているシリーズIDを取得する。

        Returns
        -------
        int または None
            選択されているシリーズID、もしくは選択がない場合はNone
        """
        return self.selected_series_id

    def ensure_correct_layout(self):
        """現在のビューポートサイズに基づいて正しいレイアウトを確保する"""
        if self.calculate_grid_columns() and self.series_widgets:
            self.relayout_grid()


class SeriesListView(QWidget):
    """
    シリーズをリスト形式で表示するビュー。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    # カスタムシグナル
    series_selected = pyqtSignal(int)  # series_id

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

        # シリーズを読み込む
        self.refresh()

    def refresh(self):
        """シリーズを再読み込みして表示を更新する。"""
        # リストをクリア
        self.list_widget.clear()

        # シリーズを取得
        series_list = self._get_filtered_series()

        # リストに追加
        self._populate_list(series_list)

    def _get_filtered_series(self):
        """
        フィルタ条件に基づいてシリーズのリストを取得する。

        Returns
        -------
        list
            Series オブジェクトのリスト
        """
        # カテゴリフィルタがある場合はそれを適用
        series_list = self.library_controller.get_all_series(
            category_id=self.category_filter
        )

        # 検索クエリがある場合はフィルタリング
        if self.search_query:
            query = self.search_query.lower()
            filtered_list = []
            for series in series_list:
                # シリーズ名、カテゴリ名、書籍タイトルで検索
                if query in series.name.lower() or (
                    series.category_name and query in series.category_name.lower()
                ):
                    filtered_list.append(series)
                    continue

                # 書籍タイトルで検索
                for book in series.books:
                    if query in book.title.lower():
                        filtered_list.append(series)
                        break

            return filtered_list

        return series_list

    def _populate_list(self, series_list):
        """
        シリーズをリストに追加する。

        Parameters
        ----------
        series_list : list
            Series オブジェクトのリスト
        """

        # 自然順ソート（シリーズ名の中の数字を考慮）
        def natural_sort_key(series):
            name = series.name if series.name else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)
            ]

        sorted_series = sorted(series_list, key=natural_sort_key)

        for series in sorted_series:
            # リストアイテムを作成
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, series.id)  # シリーズIDを保存

            # カスタムウィジェットを作成
            widget = SeriesListItemWidget(series)

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
        series_id = item.data(Qt.ItemDataRole.UserRole)
        self.series_selected.emit(series_id)

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
            series_id = item.data(Qt.ItemDataRole.UserRole)
            global_pos = self.list_widget.mapToGlobal(position)
            self._show_context_menu(global_pos, series_id)

    def _show_context_menu(self, position, series_id):
        """
        コンテキストメニューを表示する。

        Parameters
        ----------
        position : QPoint
            表示位置
        series_id : int
            対象のシリーズID
        """
        menu = QMenu()

        # シリーズを表示
        view_action = QAction("View Series", self)
        view_action.triggered.connect(lambda: self.series_selected.emit(series_id))
        menu.addAction(view_action)

        menu.addSeparator()

        # シリーズを編集
        edit_action = QAction("Edit Series", self)
        edit_action.triggered.connect(lambda: self._edit_series(series_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        # シリーズを削除
        remove_action = QAction("Remove Series", self)
        remove_action.triggered.connect(lambda: self._remove_series(series_id))
        menu.addAction(remove_action)

        # メニューを表示
        menu.exec(position)

    def _edit_series(self, series_id):
        """
        シリーズ編集処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        series_id : int
            対象のシリーズID
        """
        # 実際の処理はメインウィンドウで実装される
        pass

    def _remove_series(self, series_id):
        """
        シリーズ削除処理（シグナル接続先のプレースホルダ）。

        Parameters
        ----------
        series_id : int
            削除するシリーズID
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
        シリーズを検索する。

        Parameters
        ----------
        query : str
            検索クエリ
        """
        self.search_query = query
        self.refresh()

    def clear_search(self):
        """検索をクリアしてすべてのシリーズを表示する。"""
        self.search_query = None
        self.refresh()

    def update_series_item(self, series_id):
        """
        特定のシリーズアイテムを更新する。

        Parameters
        ----------
        series_id : int
            更新するシリーズID
        """
        # series_idに一致するアイテムを検索
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == series_id:
                # シリーズ情報を更新
                series = self.library_controller.get_series(series_id)
                if series:
                    widget = self.list_widget.itemWidget(item)
                    if isinstance(widget, SeriesListItemWidget):
                        widget.update_series_info(series)
                break

    def select_series(self, series_id, emit_signal=True):
        """
        シリーズを選択状態にする。

        Parameters
        ----------
        series_id : int
            選択するシリーズID
        emit_signal : bool, optional
            選択シグナルを発火するかどうか
        """
        # series_idに一致するアイテムを検索
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == series_id:
                # アイテムを選択
                self.list_widget.setCurrentItem(item)

                # シグナルを発火（オプション）
                if emit_signal:
                    self.series_selected.emit(series_id)
                break

    def get_selected_series_id(self):
        """
        現在選択されているシリーズIDを取得する。

        Returns
        -------
        int または None
            選択されているシリーズID、もしくは選択がない場合はNone
        """
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
