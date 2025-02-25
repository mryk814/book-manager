import logging
import os

from PyQt6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class BookItemModel(QAbstractListModel):
    """書籍アイテムのモデルクラス"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.books = []
        self.filter_query = None
        self.sort_field = "title"
        self.sort_direction = "asc"

        # ソート対象フィールドの表示名マッピング
        self.field_display_names = {
            "title": "タイトル",
            "author": "著者",
            "date_added": "追加日",
            "rating": "評価",
            "last_read": "最終閲覧日",
        }

    def rowCount(self, parent=QModelIndex()):
        """行数を返す"""
        return len(self.books)

    def data(self, index, role):
        """データを返す"""
        if not index.isValid() or index.row() >= len(self.books):
            return None

        book = self.books[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return book.title
        elif role == Qt.ItemDataRole.ToolTipRole:
            # ツールチップ表示
            tooltip = f"タイトル: {book.title}\n"
            if book.author:
                tooltip += f"著者: {book.author}\n"
            if book.publisher:
                tooltip += f"出版社: {book.publisher}\n"
            if book.page_count:
                tooltip += f"ページ数: {book.page_count}\n"
            return tooltip
        elif role == Qt.ItemDataRole.UserRole:
            # カスタムデータ（書籍オブジェクト）
            return book

        return None

    def load_books(self, filter_query=None, sort_field=None, sort_direction=None):
        """書籍データを読み込む"""
        # ソート設定を適用
        if sort_field:
            self.sort_field = sort_field
        if sort_direction:
            self.sort_direction = sort_direction

        self.filter_query = filter_query

        # データ取得前に通知
        self.beginResetModel()

        # フィルタクエリがある場合はフィルタリング
        if filter_query:
            # フィルタリング条件に応じて書籍を取得
            if isinstance(filter_query, dict):
                # 辞書形式のフィルタ条件
                self.books = self.db_manager.filter_books(filter_query)
            elif isinstance(filter_query, str):
                # 文字列検索
                self.books = self.db_manager.search_books(filter_query)
            else:
                # その他の場合は全ての書籍
                self.books = self.db_manager.get_all_books(
                    self.sort_field, self.sort_direction
                )
        else:
            # フィルタなしの場合は全ての書籍
            self.books = self.db_manager.get_all_books(
                self.sort_field, self.sort_direction
            )

        # データ変更の通知
        self.endResetModel()
        return len(self.books)

    def get_sort_info(self):
        """現在のソート情報を取得"""
        field_name = self.field_display_names.get(self.sort_field, self.sort_field)
        direction = "▲" if self.sort_direction == "asc" else "▼"
        return f"{field_name} {direction}"

    def get_book(self, index):
        """指定インデックスの書籍を取得"""
        if 0 <= index.row() < len(self.books):
            return self.books[index.row()]
        return None


class GridBookView(QScrollArea):
    """グリッド形式の書籍表示ビュー"""

    book_selected = pyqtSignal(object)  # 書籍選択シグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        # 内部ウィジェット
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        # グリッドレイアウト
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)

        # アイテムのサイズ
        self.item_width = 150
        self.item_height = 220

        # 一行あたりのアイテム数
        self.items_per_row = 5

        # 表示される書籍
        self.books = []

        # 選択されたアイテムのインデックス
        self.selected_index = -1

        # 遅延ロード用の設定
        self.visible_rows = {}  # 表示中の行：{行番号: Widgetのリスト}
        self.loaded_ranges = []  # ロード済みの範囲：[(開始行, 終了行), ...]
        self.row_heights = {}  # 各行の高さ：{行番号: 高さ}

        # スクロールイベントの接続
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def set_books(self, books):
        """書籍リストを設定"""
        self.books = books
        self.loaded_ranges = []
        self.visible_rows = {}
        self.row_heights = {}
        self._update_view()

    def set_item_size(self, width, height):
        """アイテムサイズを設定"""
        self.item_width = width
        self.item_height = height
        self.loaded_ranges = []
        self.visible_rows = {}
        self.row_heights = {}
        self._update_view()

    def set_columns(self, columns):
        """カラム数を設定"""
        self.items_per_row = max(1, columns)
        self.loaded_ranges = []
        self.visible_rows = {}
        self.row_heights = {}
        self._update_view()

    def _update_view(self):
        """ビューを更新"""
        # 既存のアイテムをクリア
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 書籍がない場合は終了
        if not self.books:
            return

        # 全体の行数を計算
        total_rows = (len(self.books) + self.items_per_row - 1) // self.items_per_row

        # プレースホルダーとなる行を作成
        for row in range(total_rows):
            for col in range(self.items_per_row):
                index = row * self.items_per_row + col
                if index < len(self.books):
                    # プレースホルダーウィジェット
                    placeholder = QWidget()
                    placeholder.setFixedSize(self.item_width, self.item_height)
                    placeholder.setObjectName(f"placeholder_{row}_{col}")

                    # データ属性
                    placeholder.setProperty("row", row)
                    placeholder.setProperty("col", col)
                    placeholder.setProperty("index", index)
                    placeholder.setProperty("is_loaded", False)

                    # 最小限のスタイル
                    placeholder.setStyleSheet(
                        f"QWidget#placeholder_{row}_{col} {{ "
                        "    background-color: #f0f0f0; "
                        "    border-radius: 5px; "
                        "    border: 1px solid #cccccc; "
                        "}"
                    )

                    # 行に追加
                    self.grid_layout.addWidget(placeholder, row, col)

                    # 行の追跡
                    if row not in self.visible_rows:
                        self.visible_rows[row] = []
                    self.visible_rows[row].append(placeholder)

                    # 行の高さを記録
                    self.row_heights[row] = self.item_height

        # 初期表示範囲をロード
        QTimer.singleShot(100, self._load_visible_rows)

    def _load_visible_rows(self):
        """現在表示されている行にアイテムをロード"""
        if not self.visible_rows:
            return

        # スクロール位置を取得
        scroll_pos = self.verticalScrollBar().value()
        viewport_height = self.viewport().height()

        # 表示されている行を特定
        visible_row_indices = []
        for row_idx, widgets in self.visible_rows.items():
            if widgets:
                # 行の位置を確認（最初のウィジェットの位置を使用）
                row_pos = widgets[0].mapTo(self.content_widget, QPoint(0, 0)).y()
                row_height = self.row_heights.get(row_idx, self.item_height)

                # 行が表示範囲内にあるか確認
                if -row_height <= row_pos - scroll_pos <= viewport_height:
                    visible_row_indices.append(row_idx)

        if not visible_row_indices:
            return

        # 表示範囲の前後も含めてロード対象とする
        buffer = 2  # 前後2行ずつバッファ
        visible_min = min(visible_row_indices)
        visible_max = max(visible_row_indices)

        load_min = max(0, visible_min - buffer)
        load_max = min(max(self.visible_rows.keys()), visible_max + buffer)

        # すでにロード済みの範囲を確認
        should_load = True
        for start, end in self.loaded_ranges:
            if start <= load_min and end >= load_max:
                should_load = False
                break

        if should_load:
            # 表示範囲内の行にアイテムをロード
            for row_idx in range(load_min, load_max + 1):
                if row_idx in self.visible_rows:
                    for widget in self.visible_rows[row_idx]:
                        if not widget.property("is_loaded"):
                            index = widget.property("index")
                            if 0 <= index < len(self.books):
                                self._load_book_item(widget, self.books[index], index)
                                widget.setProperty("is_loaded", True)

            # ロード済み範囲を更新
            self.loaded_ranges.append((load_min, load_max))

            # 範囲が多すぎる場合は古い範囲を削除
            if len(self.loaded_ranges) > 3:
                old_min, old_max = self.loaded_ranges.pop(0)
                # 現在の範囲とオーバーラップしない場合のみアンロード
                overlap = False
                for start, end in self.loaded_ranges:
                    if not (old_max < start or old_min > end):
                        overlap = True
                        break

                if not overlap:
                    for row_idx in range(old_min, old_max + 1):
                        if row_idx < load_min or row_idx > load_max:
                            if row_idx in self.visible_rows:
                                # 表示範囲外なのでアンロード
                                for widget in self.visible_rows[row_idx]:
                                    self._unload_book_item(widget)

    def _load_book_item(self, placeholder, book, index):
        """プレースホルダーに書籍アイテムの内容をロード"""
        row = placeholder.property("row")
        col = placeholder.property("col")

        # 既存のレイアウトとウィジェットを取得（なければ新規作成）
        layout = placeholder.layout()
        if not layout:
            layout = QVBoxLayout(placeholder)
            layout.setContentsMargins(5, 5, 5, 5)

        # 既存の子ウィジェットをクリア
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # スタイルシート更新
        placeholder.setStyleSheet(
            f"QWidget#placeholder_{row}_{col} {{ "
            "    background-color: #f0f0f0; "
            "    border-radius: 5px; "
            "    border: 1px solid #cccccc; "
            "}"
            f"QWidget#placeholder_{row}_{col}:hover {{ "
            "    background-color: #e0e0e0; "
            "    border: 1px solid #aaaaaa; "
            "}"
        )

        # サムネイル画像
        thumbnail = QLabel()
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if book.thumbnail_path and os.path.exists(book.thumbnail_path):
            pixmap = QPixmap(book.thumbnail_path)
            pixmap = pixmap.scaled(
                self.item_width - 20,
                self.item_height - 60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            thumbnail.setPixmap(pixmap)
        else:
            # デフォルト画像
            thumbnail.setText("No Cover")
            thumbnail.setStyleSheet(
                "background-color: #dddddd; border: 1px solid #cccccc;"
            )
            thumbnail.setFixedHeight(self.item_height - 60)

        layout.addWidget(thumbnail)

        # タイトル
        title = QLabel(book.title)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        # テキストが長い場合は省略
        if len(book.title) > 30:
            title.setText(book.title[:27] + "...")
        title.setToolTip(book.title)
        layout.addWidget(title)

        # 著者（あれば）
        if book.author:
            author = QLabel(book.author)
            author.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # テキストが長い場合は省略
            if len(book.author) > 30:
                author.setText(book.author[:27] + "...")
            author.setToolTip(book.author)
            author.setStyleSheet("color: #666666; font-size: 9pt;")
            layout.addWidget(author)

        # クリックイベント
        placeholder.mousePressEvent = lambda event, idx=index: self._on_item_clicked(
            idx
        )

    def _unload_book_item(self, placeholder):
        """プレースホルダーをリセット"""
        if not placeholder.property("is_loaded"):
            return

        row = placeholder.property("row")
        col = placeholder.property("col")

        # 既存のレイアウトとウィジェットを取得
        layout = placeholder.layout()
        if layout:
            # 既存の子ウィジェットをクリア
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # スタイルシートをリセット
        placeholder.setStyleSheet(
            f"QWidget#placeholder_{row}_{col} {{ "
            "    background-color: #f0f0f0; "
            "    border-radius: 5px; "
            "    border: 1px solid #cccccc; "
            "}"
        )

        placeholder.setProperty("is_loaded", False)

    def _on_scroll(self, value):
        """スクロール時の処理"""
        # スクロール位置が変わったら表示行を更新
        QTimer.singleShot(100, self._load_visible_rows)

    def _on_item_clicked(self, index):
        """アイテムクリック時の処理"""
        # 既存の選択状態をリセット
        if 0 <= self.selected_index < len(self.books):
            for row_idx, widgets in self.visible_rows.items():
                for widget in widgets:
                    if widget.property(
                        "index"
                    ) == self.selected_index and widget.property("is_loaded"):
                        row = widget.property("row")
                        col = widget.property("col")
                        widget.setStyleSheet(
                            f"QWidget#placeholder_{row}_{col} {{ "
                            "    background-color: #f0f0f0; "
                            "    border-radius: 5px; "
                            "    border: 1px solid #cccccc; "
                            "}"
                            f"QWidget#placeholder_{row}_{col}:hover {{ "
                            "    background-color: #e0e0e0; "
                            "    border: 1px solid #aaaaaa; "
                            "}"
                        )

        # 新しい選択状態
        self.selected_index = index
        for row_idx, widgets in self.visible_rows.items():
            for widget in widgets:
                if widget.property("index") == index and widget.property("is_loaded"):
                    row = widget.property("row")
                    col = widget.property("col")
                    widget.setStyleSheet(
                        f"QWidget#placeholder_{row}_{col} {{ "
                        "    background-color: #d0d0ff; "
                        "    border-radius: 5px; "
                        "    border: 2px solid #6666cc; "
                        "}"
                    )

        # 選択シグナルを発行
        if 0 <= index < len(self.books):
            self.book_selected.emit(self.books[index])

    def contextMenuEvent(self, event):
        """コンテキストメニューイベント"""
        # 複数選択モードがオンの場合
        if hasattr(self, "multi_select_mode") and self.multi_select_mode:
            # クリックされた位置のアイテムを特定
            for row_idx, widgets in self.visible_rows.items():
                for widget in widgets:
                    if widget.geometry().contains(
                        event.pos() - self.content_widget.pos()
                    ):
                        index = widget.property("index")
                        if index is not None:
                            # 選択されていない場合は選択
                            if index not in self.selected_indices:
                                self._on_item_clicked(index)

                            # 選択されているアイテムの数を確認
                            selected_count = len(self.selected_indices)

                            # コンテキストメニューを作成
                            menu = QMenu(self)

                            if selected_count == 1:
                                # 単一選択の場合
                                open_action = QAction("開く", self)
                                open_action.triggered.connect(
                                    lambda checked=False, idx=index: self._open_book(
                                        idx
                                    )
                                )
                                menu.addAction(open_action)

                                edit_action = QAction("編集", self)
                                edit_action.triggered.connect(
                                    lambda checked=False, idx=index: self._edit_book(
                                        idx
                                    )
                                )
                                menu.addAction(edit_action)

                                menu.addSeparator()

                                delete_action = QAction("削除", self)
                                delete_action.triggered.connect(
                                    lambda checked=False, idx=index: self._delete_book(
                                        idx
                                    )
                                )
                                menu.addAction(delete_action)
                            else:
                                # 複数選択の場合
                                books = self.get_selected_books()

                                # 一括更新アクション
                                update_action = QAction(
                                    f"選択した{selected_count}冊を一括更新...", self
                                )
                                update_action.triggered.connect(
                                    lambda: self._batch_update_books(books)
                                )
                                menu.addAction(update_action)

                                menu.addSeparator()

                                # お気に入り追加/削除
                                add_favorite_action = QAction("お気に入りに追加", self)
                                add_favorite_action.triggered.connect(
                                    lambda: self._batch_set_favorite(books, True)
                                )
                                menu.addAction(add_favorite_action)

                                remove_favorite_action = QAction(
                                    "お気に入りから削除", self
                                )
                                remove_favorite_action.triggered.connect(
                                    lambda: self._batch_set_favorite(books, False)
                                )
                                menu.addAction(remove_favorite_action)

                                menu.addSeparator()

                                # 読書状態変更
                                reading_menu = menu.addMenu("読書状態を変更")

                                unread_action = reading_menu.addAction("未読に設定")
                                unread_action.triggered.connect(
                                    lambda: self._batch_set_reading_status(
                                        books, "未読"
                                    )
                                )

                                reading_action = reading_menu.addAction("読書中に設定")
                                reading_action.triggered.connect(
                                    lambda: self._batch_set_reading_status(
                                        books, "読書中"
                                    )
                                )

                                completed_action = reading_menu.addAction("読了に設定")
                                completed_action.triggered.connect(
                                    lambda: self._batch_set_reading_status(
                                        books, "読了"
                                    )
                                )

                                menu.addSeparator()

                                # 削除
                                delete_action = QAction(
                                    f"選択した{selected_count}冊を削除...", self
                                )
                                delete_action.triggered.connect(
                                    lambda: self._batch_delete_books(books)
                                )
                                menu.addAction(delete_action)

                            menu.exec(event.globalPos())
                            return

        # 複数選択モードでない場合の以前の処理
        # クリックされた位置のアイテムを特定
        for i in range(len(self.books)):
            spine = self.findChild(QFrame, f"book_spine_{i}")
            if spine and spine.geometry().contains(
                event.pos() - self.content_widget.pos()
            ):
                self._on_spine_clicked(i)

                # コンテキストメニューを作成
                menu = QMenu(self)

                open_action = QAction("開く", self)
                open_action.triggered.connect(
                    lambda checked=False, idx=i: self._open_book(idx)
                )
                menu.addAction(open_action)

                edit_action = QAction("編集", self)
                edit_action.triggered.connect(
                    lambda checked=False, idx=i: self._edit_book(idx)
                )
                menu.addAction(edit_action)

                menu.addSeparator()

                delete_action = QAction("削除", self)
                delete_action.triggered.connect(
                    lambda checked=False, idx=i: self._delete_book(idx)
                )
                menu.addAction(delete_action)

                menu.exec(event.globalPos())
                break

    def _open_book(self, index):
        """書籍を開く"""
        if 0 <= index < len(self.books):
            book = self.books[index]
            # 書籍を開くシグナルを発行（実装は親ウィジェットで行う）
            self.book_selected.emit(book)

    def _edit_book(self, index):
        """書籍を編集"""
        if 0 <= index < len(self.books):
            book = self.books[index]
            # 編集ダイアログを表示（実際の実装は親ウィジェットで行う）
            # ここではシグナルのみ発行
            self.book_selected.emit(book)

    def _delete_book(self, index):
        """書籍を削除"""
        if 0 <= index < len(self.books):
            book = self.books[index]

            # 確認ダイアログ
            reply = QMessageBox.question(
                self,
                "書籍の削除",
                f"「{book.title}」を削除しますか？\nこの操作は元に戻せません。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 削除処理（実際の実装は親ウィジェットで行う）
                # ここではシグナルのみ発行
                self.book_selected.emit(book)

    def setSelectionMode(self, multi_select):
        """選択モードを設定"""
        self.multi_select_mode = multi_select
        self.selected_indices = (
            set()
            if multi_select
            else {self.selected_index}
            if self.selected_index >= 0
            else set()
        )

    def get_selected_books(self):
        """選択されている書籍のリストを取得"""
        selected_books = []

        for index in self.selected_indices:
            if 0 <= index < len(self.books):
                selected_books.append(self.books[index])

        return selected_books

    def _on_item_clicked(self, index):
        """アイテムクリック時の処理"""
        # 既存の選択状態をリセット
        if not self.multi_select_mode:
            # 単一選択モードの場合
            if self.selected_index >= 0:
                placeholder = self._find_placeholder_for_index(self.selected_index)
                if placeholder:
                    self._reset_placeholder_style(placeholder)

            self.selected_index = index
            self.selected_indices = {index}
        else:
            # 複数選択モードの場合
            modifiers = QApplication.keyboardModifiers()

            if modifiers & Qt.KeyboardModifier.ControlModifier:
                # Controlキーが押されている場合、トグル
                if index in self.selected_indices:
                    self.selected_indices.remove(index)
                    placeholder = self._find_placeholder_for_index(index)
                    if placeholder:
                        self._reset_placeholder_style(placeholder)
                else:
                    self.selected_indices.add(index)
            elif (
                modifiers & Qt.KeyboardModifier.ShiftModifier
                and self.selected_index >= 0
            ):
                # Shiftキーが押されている場合、範囲選択
                start = min(self.selected_index, index)
                end = max(self.selected_index, index) + 1

                # 既存の選択に追加
                for i in range(start, end):
                    self.selected_indices.add(i)
            else:
                # 通常のクリック、既存の選択をクリア
                for old_index in self.selected_indices:
                    if old_index != index:
                        placeholder = self._find_placeholder_for_index(old_index)
                        if placeholder:
                            self._reset_placeholder_style(placeholder)

                self.selected_indices = {index}

            # 最後にクリックしたインデックスを保存
            self.selected_index = index

        # 選択したアイテムのスタイルを更新
        placeholder = self._find_placeholder_for_index(index)
        if placeholder:
            row = placeholder.property("row")
            col = placeholder.property("col")
            placeholder.setStyleSheet(
                f"QWidget#placeholder_{row}_{col} {{ "
                "    background-color: #d0d0ff; "
                "    border-radius: 5px; "
                "    border: 2px solid #6666cc; "
                "}"
            )

        # 選択シグナルを発行（単一選択互換）
        if 0 <= index < len(self.books):
            self.book_selected.emit(self.books[index])

    def _find_placeholder_for_index(self, index):
        """インデックスに対応するプレースホルダーを探す"""
        for row_idx, widgets in self.visible_rows.items():
            for widget in widgets:
                if widget.property("index") == index:
                    return widget
        return None

    def _reset_placeholder_style(self, placeholder):
        """プレースホルダーのスタイルをリセット"""
        row = placeholder.property("row")
        col = placeholder.property("col")
        placeholder.setStyleSheet(
            f"QWidget#placeholder_{row}_{col} {{ "
            "    background-color: #f0f0f0; "
            "    border-radius: 5px; "
            "    border: 1px solid #cccccc; "
            "}"
            f"QWidget#placeholder_{row}_{col}:hover {{ "
            "    background-color: #e0e0e0; "
            "    border: 1px solid #aaaaaa; "
            "}"
        )

    def _batch_update_books(self, books):
        """複数の書籍を一括更新"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, LibraryView):
            parent = parent.parent()

        if parent and isinstance(parent, LibraryView):
            parent.batch_update_selected_books()

    def _batch_set_favorite(self, books, is_favorite):
        """複数の書籍のお気に入り状態を一括設定"""
        if not books:
            return

        action_text = "お気に入りに追加" if is_favorite else "お気に入りから削除"

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 確認ダイアログ
        reply = QMessageBox.question(
            parent,
            f"{len(books)}冊を{action_text}",
            f"選択した{len(books)}冊の書籍を{action_text}しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # お気に入り状態を更新
                for book in books:
                    library_manager.update_book_metadata(
                        book.id, {"is_favorite": is_favorite}
                    )

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent, "更新完了", f"{len(books)}冊の書籍を{action_text}しました。"
                )

    def _batch_set_reading_status(self, books, status):
        """複数の書籍の読書状態を一括設定"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 確認ダイアログ
        reply = QMessageBox.question(
            parent,
            f"{len(books)}冊の読書状態を変更",
            f"選択した{len(books)}冊の書籍の読書状態を「{status}」に設定しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # 読書状態を更新
                for book in books:
                    library_manager.update_book_metadata(
                        book.id, {"reading_status": status}
                    )

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent,
                    "更新完了",
                    f"{len(books)}冊の書籍の読書状態を「{status}」に設定しました。",
                )

    def _batch_delete_books(self, books):
        """複数の書籍を一括削除"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 削除前の確認
        msg = (
            f"選択した{len(books)}冊の書籍を削除しますか？\nこの操作は元に戻せません。"
        )

        # 書籍名を最大5冊まで表示
        book_titles = [book.title for book in books[:5]]
        if len(books) > 5:
            book_titles.append(f"...他{len(books) - 5}冊")
        msg += f"\n\n- " + "\n- ".join(book_titles)

        reply = QMessageBox.question(
            parent,
            "書籍の一括削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # ファイルも削除するか尋ねる
            delete_file_reply = QMessageBox.question(
                parent,
                "ファイルの削除",
                "PDFファイルも削除しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            delete_file = delete_file_reply == QMessageBox.StandardButton.Yes

            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # 書籍を削除
                deleted_count = 0
                for book in books:
                    if library_manager.delete_book(book.id, delete_file):
                        deleted_count += 1

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent, "削除完了", f"{deleted_count}冊の書籍を削除しました。"
                )


class ListBookView(QTableView):
    """リスト形式の書籍表示ビュー"""

    book_selected = pyqtSignal(object)  # 書籍選択シグナル

    def __init__(self, parent=None):
        super().__init__(parent)

        # モデルの設定
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            ["タイトル", "著者", "シリーズ", "追加日", "状態"]
        )
        self.setModel(self.model)

        # 表示設定
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.verticalHeader().hide()  # 行番号を非表示
        self.setAlternatingRowColors(True)  # 交互に行の色を変える

        # ダブルクリックシグナルの接続
        self.doubleClicked.connect(self._on_double_clicked)

        # 書籍リスト
        self.books = []

    def set_books(self, books):
        """書籍リストを設定"""
        self.books = books
        self._update_view()

    def _update_view(self):
        """ビューを更新"""
        # 既存のデータをクリア
        self.model.setRowCount(0)

        # 書籍データを追加
        for book in self.books:
            # 各カラムのアイテム
            title_item = QStandardItem(book.title)
            title_item.setData(book, Qt.ItemDataRole.UserRole)  # 書籍オブジェクトを保存

            author_item = QStandardItem(book.author if book.author else "")

            # シリーズ名を取得（シリーズが存在する場合）
            series_name = ""
            if book.series and len(book.series) > 0:
                series_name = book.series[0].name
                if book.volume_number:
                    series_name += f" ({book.volume_number})"
            series_item = QStandardItem(series_name)

            # 追加日
            date_added = ""
            if book.date_added:
                date_added = book.date_added.strftime("%Y-%m-%d")
            date_item = QStandardItem(date_added)

            # 読書状態
            status_item = QStandardItem(book.reading_status)

            # 行を追加
            self.model.appendRow(
                [title_item, author_item, series_item, date_item, status_item]
            )

        # カラム幅の調整
        self.resizeColumnsToContents()

    def _on_double_clicked(self, index):
        """アイテムダブルクリック時の処理"""
        # 選択された行から書籍オブジェクトを取得
        row_index = index.row()
        title_item = self.model.item(row_index, 0)
        book = title_item.data(Qt.ItemDataRole.UserRole)

        # 書籍選択シグナルを発行
        self.book_selected.emit(book)

    def contextMenuEvent(self, event):
        """コンテキストメニューイベント"""
        # 選択された行のインデックスを取得
        index = self.indexAt(event.pos())
        if index.isValid():
            # 選択された行から書籍オブジェクトを取得
            row_index = index.row()
            title_item = self.model.item(row_index, 0)
            book = title_item.data(Qt.ItemDataRole.UserRole)

            # コンテキストメニューを作成
            menu = QMenu(self)

            open_action = QAction("開く", self)
            open_action.triggered.connect(lambda: self._open_book(book))
            menu.addAction(open_action)

            edit_action = QAction("編集", self)
            edit_action.triggered.connect(lambda: self._edit_book(book))
            menu.addAction(edit_action)

            menu.addSeparator()

            delete_action = QAction("削除", self)
            delete_action.triggered.connect(lambda: self._delete_book(book))
            menu.addAction(delete_action)

            menu.exec(event.globalPos())

    def _open_book(self, book):
        """書籍を開く"""
        self.book_selected.emit(book)

    def _edit_book(self, book):
        """書籍を編集"""
        # 編集ダイアログを表示（実際の実装は親ウィジェットで行う）
        # ここではシグナルのみ発行
        self.book_selected.emit(book)

    def _delete_book(self, book):
        """書籍を削除"""
        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "書籍の削除",
            f"「{book.title}」を削除しますか？\nこの操作は元に戻せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 削除処理（実際の実装は親ウィジェットで行う）
            # ここではシグナルのみ発行
            self.book_selected.emit(book)

    def get_selected_books(self):
        """選択されている書籍のリストを取得"""
        selected_books = []

        # 選択されている行のインデックスを取得
        selected_indexes = self.selectedIndexes()

        # 選択行の重複を排除して取得（行単位の選択）
        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        # 各行の書籍を取得
        for row in selected_rows:
            title_item = self.model.item(row, 0)
            book = title_item.data(Qt.ItemDataRole.UserRole)
            selected_books.append(book)

        return selected_books

    def _batch_update_books(self, books):
        """複数の書籍を一括更新"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, LibraryView):
            parent = parent.parent()

        if parent and isinstance(parent, LibraryView):
            parent.batch_update_selected_books()

    def _batch_set_favorite(self, books, is_favorite):
        """複数の書籍のお気に入り状態を一括設定"""
        if not books:
            return

        action_text = "お気に入りに追加" if is_favorite else "お気に入りから削除"

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 確認ダイアログ
        reply = QMessageBox.question(
            parent,
            f"{len(books)}冊を{action_text}",
            f"選択した{len(books)}冊の書籍を{action_text}しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # お気に入り状態を更新
                for book in books:
                    library_manager.update_book_metadata(
                        book.id, {"is_favorite": is_favorite}
                    )

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent, "更新完了", f"{len(books)}冊の書籍を{action_text}しました。"
                )

    def _batch_set_reading_status(self, books, status):
        """複数の書籍の読書状態を一括設定"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 確認ダイアログ
        reply = QMessageBox.question(
            parent,
            f"{len(books)}冊の読書状態を変更",
            f"選択した{len(books)}冊の書籍の読書状態を「{status}」に設定しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # 読書状態を更新
                for book in books:
                    library_manager.update_book_metadata(
                        book.id, {"reading_status": status}
                    )

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent,
                    "更新完了",
                    f"{len(books)}冊の書籍の読書状態を「{status}」に設定しました。",
                )

    def _batch_delete_books(self, books):
        """複数の書籍を一括削除"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 削除前の確認
        msg = (
            f"選択した{len(books)}冊の書籍を削除しますか？\nこの操作は元に戻せません。"
        )

        # 書籍名を最大5冊まで表示
        book_titles = [book.title for book in books[:5]]
        if len(books) > 5:
            book_titles.append(f"...他{len(books) - 5}冊")
        msg += f"\n\n- " + "\n- ".join(book_titles)

        reply = QMessageBox.question(
            parent,
            "書籍の一括削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # ファイルも削除するか尋ねる
            delete_file_reply = QMessageBox.question(
                parent,
                "ファイルの削除",
                "PDFファイルも削除しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            delete_file = delete_file_reply == QMessageBox.StandardButton.Yes

            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # 書籍を削除
                deleted_count = 0
                for book in books:
                    if library_manager.delete_book(book.id, delete_file):
                        deleted_count += 1

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent, "削除完了", f"{deleted_count}冊の書籍を削除しました。"
                )


class BookshelfView(QScrollArea):
    """本棚形式の書籍表示ビュー"""

    book_selected = pyqtSignal(object)  # 書籍選択シグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        # 内部ウィジェット
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        # 縦のレイアウト（棚ごと）
        self.shelves_layout = QVBoxLayout(self.content_widget)
        self.shelves_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.shelves_layout.setContentsMargins(10, 10, 10, 10)
        self.shelves_layout.setSpacing(30)  # 棚の間隔

        # 表示する書籍
        self.books = []

        # 一棚あたりのアイテム数
        self.items_per_shelf = 15

        # 選択されたアイテムのインデックス
        self.selected_index = -1

        # 遅延ロード用の設定
        self.visible_shelves = []  # 表示中の棚
        self.loaded_ranges = []  # ロード済みの範囲
        self.max_visible_shelves = 8  # 一度に表示する最大棚数

        # スクロールイベントの接続
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def set_books(self, books):
        """書籍リストを設定"""
        self.books = books
        self.loaded_ranges = []
        self._update_view()

    def set_items_per_shelf(self, count):
        """一棚あたりのアイテム数を設定"""
        self.items_per_shelf = max(1, count)
        self.loaded_ranges = []
        self._update_view()

    def _update_view(self):
        """ビューを更新"""
        # 既存のアイテムをクリア
        while self.shelves_layout.count():
            item = self.shelves_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.visible_shelves = []

        # 書籍がない場合は終了
        if not self.books:
            return

        # 何棚必要かを計算
        shelf_count = (
            len(self.books) + self.items_per_shelf - 1
        ) // self.items_per_shelf

        # シェルフのプレースホルダーを作成
        for shelf_index in range(shelf_count):
            # 棚のウィジェット（QFrameを使用）
            shelf = QFrame()
            shelf.setObjectName(f"shelf_{shelf_index}")

            # 棚の色と境界線を設定
            shelf.setAutoFillBackground(True)
            palette = shelf.palette()
            palette.setColor(shelf.backgroundRole(), QColor("#8B4513"))  # 茶色
            shelf.setPalette(palette)

            shelf.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
            shelf.setLineWidth(2)
            shelf.setMinimumHeight(30)

            shelf_layout = QHBoxLayout(shelf)
            shelf_layout.setContentsMargins(5, 5, 5, 5)
            shelf_layout.setSpacing(0)  # 本の間隔を狭く

            # 空のラベルを追加（サイズ確保のため）
            placeholder = QLabel(f"棚 {shelf_index + 1}")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setMinimumHeight(150)
            shelf_layout.addWidget(placeholder)

            # データ属性を設定
            shelf.setProperty("shelf_index", shelf_index)
            shelf.setProperty("is_loaded", False)

            # 棚を追加
            self.shelves_layout.addWidget(shelf)
            self.visible_shelves.append(shelf)

        # 初期表示範囲をロード
        QTimer.singleShot(100, self._load_visible_shelves)

    def _load_visible_shelves(self):
        """現在表示されている棚にアイテムをロード"""
        if not self.visible_shelves:
            return

        # スクロール位置を取得
        scroll_pos = self.verticalScrollBar().value()
        viewport_height = self.viewport().height()

        # 表示範囲内の棚を特定
        visible_indices = []
        for shelf in self.visible_shelves:
            shelf_idx = shelf.property("shelf_index")
            shelf_pos = shelf.mapTo(self.content_widget, QPoint(0, 0)).y()

            # 棚が表示範囲内にあるか確認
            if -150 <= shelf_pos - scroll_pos <= viewport_height:
                visible_indices.append(shelf_idx)

        # 表示範囲の前後も含めてロード対象とする
        buffer = 2  # 前後2棚ずつバッファ
        visible_min = min(visible_indices) if visible_indices else 0
        visible_max = max(visible_indices) if visible_indices else 0

        load_min = max(0, visible_min - buffer)
        load_max = min(len(self.visible_shelves) - 1, visible_max + buffer)

        # すでにロード済みの範囲を確認
        should_load = True
        for start, end in self.loaded_ranges:
            if start <= load_min and end >= load_max:
                should_load = False
                break

        if should_load:
            # 表示範囲内の棚にアイテムをロード
            for shelf_idx in range(load_min, load_max + 1):
                shelf = self.visible_shelves[shelf_idx]
                if not shelf.property("is_loaded"):
                    self._load_shelf_items(shelf)
                    shelf.setProperty("is_loaded", True)

            # ロード済み範囲を更新
            self.loaded_ranges.append((load_min, load_max))

            # 範囲が多すぎる場合は古い範囲を削除
            if len(self.loaded_ranges) > 3:
                old_min, old_max = self.loaded_ranges.pop(0)
                # 現在の範囲とオーバーラップしない場合のみアンロード
                overlap = False
                for start, end in self.loaded_ranges:
                    if not (old_max < start or old_min > end):
                        overlap = True
                        break

                if not overlap:
                    for shelf_idx in range(old_min, old_max + 1):
                        if shelf_idx < load_min or shelf_idx > load_max:
                            # 表示範囲外なのでアンロード
                            self._unload_shelf_items(self.visible_shelves[shelf_idx])

    def _load_shelf_items(self, shelf):
        """棚にアイテムをロード"""
        # 既存のアイテムをクリア
        while shelf.layout().count():
            item = shelf.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        shelf_idx = shelf.property("shelf_index")

        # 棚に本を配置
        start_idx = shelf_idx * self.items_per_shelf
        end_idx = min(start_idx + self.items_per_shelf, len(self.books))

        for i in range(start_idx, end_idx):
            book = self.books[i]
            book_widget = self._create_book_spine(book, i)
            shelf.layout().addWidget(book_widget)

    def _unload_shelf_items(self, shelf):
        """棚のアイテムをアンロード"""
        if not shelf.property("is_loaded"):
            return

        # 既存のアイテムをクリア
        while shelf.layout().count():
            item = shelf.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # プレースホルダーを追加
        shelf_idx = shelf.property("shelf_index")
        placeholder = QLabel(f"棚 {shelf_idx + 1}")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumHeight(150)
        shelf.layout().addWidget(placeholder)

        shelf.setProperty("is_loaded", False)

    def _on_scroll(self, value):
        """スクロール時の処理"""
        # スクロール位置が変わったら表示棚を更新
        QTimer.singleShot(100, self._load_visible_shelves)

    def _create_book_spine(self, book, index):
        """本の背表紙ウィジェットを作成"""
        # 本の背表紙（QFrameを使用）
        spine = QFrame()
        spine.setObjectName(f"book_spine_{index}")
        spine.setFixedWidth(30)  # 背表紙の幅
        spine.setMinimumHeight(150)  # 背表紙の高さ

        # タイトルに基づいて色を決定（より単純な実装）
        title_hash = sum(ord(c) for c in book.title)
        r = (title_hash % 150) + 100  # 100-250の範囲
        g = ((title_hash * 3) % 150) + 100
        b = ((title_hash * 7) % 150) + 100

        # QPaletteを使用して背景色を設定
        palette = spine.palette()
        palette.setColor(spine.backgroundRole(), QColor(r, g, b))
        spine.setAutoFillBackground(True)
        spine.setPalette(palette)

        # 境界線はフレームで設定（QFrameのメソッド）
        spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        spine.setLineWidth(1)

        # レイアウト
        layout = QVBoxLayout(spine)
        layout.setContentsMargins(2, 2, 2, 2)

        # 縦書きのタイトル（簡易的な実装）
        label = QLabel()
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # タイトルの短縮化
        if len(book.title) > 15:
            display_title = book.title[:12] + "..."
        else:
            display_title = book.title

        label.setText(display_title)
        label.setStyleSheet("color: black; font-size: 8pt;")
        label.setToolTip(book.title)
        layout.addWidget(label)

        # データ属性として保存（選択状態の維持用）
        spine.setProperty("book_index", index)
        spine.setProperty("book_color", QColor(r, g, b))
        spine.setProperty("selected", False)

        # クリックイベント
        spine.mousePressEvent = lambda event, idx=index: self._on_spine_clicked(idx)

        return spine

    def _on_spine_clicked(self, index):
        """背表紙クリック時の処理"""
        # 既存の選択状態をリセット
        if 0 <= self.selected_index < len(self.books):
            spine = self.findChild(QFrame, f"book_spine_{self.selected_index}")
            if spine:
                # もとの色に戻す
                original_color = spine.property("book_color")
                palette = spine.palette()
                palette.setColor(spine.backgroundRole(), original_color)
                spine.setPalette(palette)

                # 線の色を戻す
                spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
                spine.setLineWidth(1)

                spine.setProperty("selected", False)

        # 新しい選択状態
        self.selected_index = index
        spine = self.findChild(QFrame, f"book_spine_{index}")
        if spine:
            # 選択色に変更
            palette = spine.palette()
            palette.setColor(spine.backgroundRole(), QColor(255, 255, 0))  # 黄色
            spine.setPalette(palette)

            # 枠線を強調
            spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            spine.setLineWidth(2)

            spine.setProperty("selected", True)

        # 選択シグナルを発行
        self.book_selected.emit(self.books[index])

    def setSelectionMode(self, multi_select):
        """選択モードを設定"""
        self.multi_select_mode = multi_select
        self.selected_indices = (
            set()
            if multi_select
            else {self.selected_index}
            if self.selected_index >= 0
            else set()
        )

    def get_selected_books(self):
        """選択されている書籍のリストを取得"""
        selected_books = []

        for index in self.selected_indices:
            if 0 <= index < len(self.books):
                selected_books.append(self.books[index])

        return selected_books

    def _on_spine_clicked(self, index):
        """背表紙クリック時の処理"""
        # 既存の選択状態をリセット
        if not self.multi_select_mode:
            # 単一選択モードの場合
            if 0 <= self.selected_index < len(self.books):
                spine = self.findChild(QFrame, f"book_spine_{self.selected_index}")
                if spine:
                    # もとの色に戻す
                    original_color = spine.property("book_color")
                    palette = spine.palette()
                    palette.setColor(spine.backgroundRole(), original_color)
                    spine.setPalette(palette)

                    # 線の色を戻す
                    spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
                    spine.setLineWidth(1)

                    spine.setProperty("selected", False)

            self.selected_index = index
            self.selected_indices = {index}
        else:
            # 複数選択モードの場合
            modifiers = QApplication.keyboardModifiers()

            if modifiers & Qt.KeyboardModifier.ControlModifier:
                # Controlキーが押されている場合、トグル
                if index in self.selected_indices:
                    self.selected_indices.remove(index)
                    spine = self.findChild(QFrame, f"book_spine_{index}")
                    if spine:
                        # もとの色に戻す
                        original_color = spine.property("book_color")
                        palette = spine.palette()
                        palette.setColor(spine.backgroundRole(), original_color)
                        spine.setPalette(palette)

                        # 線の色を戻す
                        spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
                        spine.setLineWidth(1)

                        spine.setProperty("selected", False)
                else:
                    self.selected_indices.add(index)
            elif (
                modifiers & Qt.KeyboardModifier.ShiftModifier
                and self.selected_index >= 0
            ):
                # Shiftキーが押されている場合、範囲選択
                start = min(self.selected_index, index)
                end = max(self.selected_index, index) + 1

                # 既存の選択に追加
                for i in range(start, end):
                    self.selected_indices.add(i)
            else:
                # 通常のクリック、既存の選択をクリア
                for old_index in self.selected_indices:
                    if old_index != index:
                        spine = self.findChild(QFrame, f"book_spine_{old_index}")
                        if spine:
                            # もとの色に戻す
                            original_color = spine.property("book_color")
                            palette = spine.palette()
                            palette.setColor(spine.backgroundRole(), original_color)
                            spine.setPalette(palette)

                            # 線の色を戻す
                            spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
                            spine.setLineWidth(1)

                            spine.setProperty("selected", False)

                self.selected_indices = {index}

            # 最後にクリックしたインデックスを保存
            self.selected_index = index

        # 選択したアイテムのスタイルを更新
        spine = self.findChild(QFrame, f"book_spine_{index}")
        if spine:
            # 選択色に変更
            palette = spine.palette()
            palette.setColor(spine.backgroundRole(), QColor(255, 255, 0))  # 黄色
            spine.setPalette(palette)

            # 枠線を強調
            spine.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            spine.setLineWidth(2)

            spine.setProperty("selected", True)

        # 選択シグナルを発行（単一選択互換）
        if 0 <= index < len(self.books):
            self.book_selected.emit(self.books[index])

    def _batch_update_books(self, books):
        """複数の書籍を一括更新"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, LibraryView):
            parent = parent.parent()

        if parent and isinstance(parent, LibraryView):
            parent.batch_update_selected_books()

    def _batch_set_favorite(self, books, is_favorite):
        """複数の書籍のお気に入り状態を一括設定"""
        if not books:
            return

        action_text = "お気に入りに追加" if is_favorite else "お気に入りから削除"

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 確認ダイアログ
        reply = QMessageBox.question(
            parent,
            f"{len(books)}冊を{action_text}",
            f"選択した{len(books)}冊の書籍を{action_text}しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # お気に入り状態を更新
                for book in books:
                    library_manager.update_book_metadata(
                        book.id, {"is_favorite": is_favorite}
                    )

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent, "更新完了", f"{len(books)}冊の書籍を{action_text}しました。"
                )

    def _batch_set_reading_status(self, books, status):
        """複数の書籍の読書状態を一括設定"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 確認ダイアログ
        reply = QMessageBox.question(
            parent,
            f"{len(books)}冊の読書状態を変更",
            f"選択した{len(books)}冊の書籍の読書状態を「{status}」に設定しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # 読書状態を更新
                for book in books:
                    library_manager.update_book_metadata(
                        book.id, {"reading_status": status}
                    )

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent,
                    "更新完了",
                    f"{len(books)}冊の書籍の読書状態を「{status}」に設定しました。",
                )

    def _batch_delete_books(self, books):
        """複数の書籍を一括削除"""
        if not books:
            return

        # 親ウィジェットを探す
        parent = self
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()

        # 削除前の確認
        msg = (
            f"選択した{len(books)}冊の書籍を削除しますか？\nこの操作は元に戻せません。"
        )

        # 書籍名を最大5冊まで表示
        book_titles = [book.title for book in books[:5]]
        if len(books) > 5:
            book_titles.append(f"...他{len(books) - 5}冊")
        msg += f"\n\n- " + "\n- ".join(book_titles)

        reply = QMessageBox.question(
            parent,
            "書籍の一括削除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # ファイルも削除するか尋ねる
            delete_file_reply = QMessageBox.question(
                parent,
                "ファイルの削除",
                "PDFファイルも削除しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            delete_file = delete_file_reply == QMessageBox.StandardButton.Yes

            # 親ウィジェットのライブラリマネージャーを探す
            library_manager = None
            temp_parent = parent
            while temp_parent:
                if hasattr(temp_parent, "library_manager"):
                    library_manager = temp_parent.library_manager
                    break
                temp_parent = temp_parent.parent()

            if library_manager:
                # 書籍を削除
                deleted_count = 0
                for book in books:
                    if library_manager.delete_book(book.id, delete_file):
                        deleted_count += 1

                # 親ウィジェットを更新
                library_view = self.parent()
                while library_view and not isinstance(library_view, LibraryView):
                    library_view = library_view.parent()

                if library_view:
                    library_view.refresh()

                QMessageBox.information(
                    parent, "削除完了", f"{deleted_count}冊の書籍を削除しました。"
                )


class LibraryView(QWidget):
    """ライブラリビューのメインクラス"""

    book_open_requested = pyqtSignal(object)  # 書籍を開くリクエスト

    def __init__(self, library_manager, config, parent=None):
        super().__init__(parent)
        self.library_manager = library_manager
        self.config = config
        self.db_manager = library_manager.db

        # UI設定の読み込み
        self.ui_settings = config.get("ui", {})

        # データモデル
        self.book_model = BookItemModel(self.db_manager)

        # UIの初期化
        self._init_ui()

        # 初期データの読み込み
        self._load_books()

    def _init_ui(self):
        """UIの初期化"""
        main_layout = QVBoxLayout(self)

        # 上部のコントロールエリア
        control_layout = QHBoxLayout()

        # 表示モードラベル
        view_info_label = QLabel("表示:")
        control_layout.addWidget(view_info_label)

        # 表示モード表示
        self.view_mode_label = QLabel()
        control_layout.addWidget(self.view_mode_label)

        # スペーサー
        control_layout.addStretch()

        # ソート情報
        sort_info_label = QLabel("ソート:")
        control_layout.addWidget(sort_info_label)

        # ソート表示
        self.sort_info_label = QLabel()
        control_layout.addWidget(self.sort_info_label)

        # スペーサー
        control_layout.addStretch()

        # 書籍数表示
        self.book_count_label = QLabel()
        control_layout.addWidget(self.book_count_label)

        main_layout.addLayout(control_layout)

        # 書籍表示領域
        self.grid_view = GridBookView()
        self.list_view = ListBookView()
        self.bookshelf_view = BookshelfView()

        # シグナルの接続
        self.grid_view.book_selected.connect(self._on_book_selected)
        self.list_view.book_selected.connect(self._on_book_selected)
        self.bookshelf_view.book_selected.connect(self._on_book_selected)

        # 初期表示モードの設定
        self.current_view = None
        view_mode = self.ui_settings.get("default_view", "grid")
        self._set_view_mode(view_mode)

        main_layout.addWidget(self.grid_view)
        main_layout.addWidget(self.list_view)
        main_layout.addWidget(self.bookshelf_view)

    def _set_view_mode(self, mode):
        """表示モードを設定"""
        # 前のビューを非表示
        if self.current_view:
            self.current_view.hide()

        # 新しいビューを表示
        if mode == "grid":
            self.current_view = self.grid_view
            self.view_mode_label.setText("グリッド表示")
        elif mode == "list":
            self.current_view = self.list_view
            self.view_mode_label.setText("リスト表示")
        elif mode == "bookshelf":
            self.current_view = self.bookshelf_view
            self.view_mode_label.setText("本棚表示")
        else:
            self.current_view = self.grid_view
            self.view_mode_label.setText("グリッド表示")

        self.current_view.show()

        # 設定を保存
        self.config.set("ui.default_view", mode)

    def change_view_mode(self, mode):
        """外部から表示モードを変更"""
        self._set_view_mode(mode)
        self._update_views()

    def _load_books(self, filter_query=None):
        """書籍データを読み込む"""
        # UIからソート設定を取得
        sort_field = self.config.get("ui.sort_field", "title")
        sort_direction = self.config.get("ui.sort_direction", "asc")

        # データを読み込む
        count = self.book_model.load_books(filter_query, sort_field, sort_direction)

        # ビューを更新
        self._update_views()

        # 情報表示を更新
        self.book_count_label.setText(f"全 {count} 書籍")
        self.sort_info_label.setText(self.book_model.get_sort_info())

        return count

    def _update_views(self):
        """すべてのビューを更新"""
        books = self.book_model.books

        # 各ビューに書籍リストを設定
        self.grid_view.set_books(books)
        self.list_view.set_books(books)
        self.bookshelf_view.set_books(books)

    def refresh(self, filter_query=None):
        """ビューを更新（外部から呼び出し用）"""
        self._load_books(filter_query)

    def search(self, search_term):
        """検索を実行"""
        return self._load_books(search_term)

    def filter(self, filter_dict):
        """フィルタリングを実行"""
        return self._load_books(filter_dict)

    def _on_book_selected(self, book):
        """書籍が選択されたときの処理"""
        # 書籍を開くリクエストを発行
        self.book_open_requested.emit(book)

    def _enable_multiple_selection(self):
        """ライブラリビューで複数選択を有効にする"""
        # グリッドビューの複数選択を有効にする
        self.grid_view.setSelectionMode(True)

        # リストビューは既に複数選択をサポートしているので処理不要

        # 本棚ビューの複数選択を有効にする
        self.bookshelf_view.setSelectionMode(True)

    def get_selected_books(self):
        """現在の表示モードで選択されている書籍のリストを取得"""
        selected_books = []

        if self.current_view == self.grid_view:
            selected_books = self.grid_view.get_selected_books()
        elif self.current_view == self.list_view:
            selected_books = self.list_view.get_selected_books()
        elif self.current_view == self.bookshelf_view:
            selected_books = self.bookshelf_view.get_selected_books()

        return selected_books

    def batch_update_selected_books(self):
        """選択した書籍を一括更新"""
        selected_books = self.get_selected_books()

        if not selected_books:
            QMessageBox.warning(self, "選択エラー", "更新する書籍を選択してください。")
            return

        # 一括更新ダイアログを表示
        from book_manager.gui.dialogs.batch_book_dialog import BatchBookUpdateDialog

        dialog = BatchBookUpdateDialog(self.library_manager, selected_books, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新データを取得
            update_data = dialog.get_update_data()

            # 一括更新を適用
            from book_manager.gui.dialogs.batch_book_dialog import apply_batch_update

            count = apply_batch_update(
                self.library_manager, selected_books, update_data
            )

            if count > 0:
                QMessageBox.information(
                    self, "一括更新完了", f"{count}冊の書籍を更新しました。"
                )

                # ビューを更新
                self.refresh()
