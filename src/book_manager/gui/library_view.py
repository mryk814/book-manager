import logging
import os

from PyQt6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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

    def set_books(self, books):
        """書籍リストを設定"""
        self.books = books
        self._update_view()

    def set_item_size(self, width, height):
        """アイテムサイズを設定"""
        self.item_width = width
        self.item_height = height
        self._update_view()

    def set_columns(self, columns):
        """カラム数を設定"""
        self.items_per_row = max(1, columns)
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

        # グリッドにアイテムを追加
        for i, book in enumerate(self.books):
            row = i // self.items_per_row
            col = i % self.items_per_row

            # 書籍アイテムウィジェットを作成
            item = self._create_book_item(book, i)
            self.grid_layout.addWidget(item, row, col)

    def _create_book_item(self, book, index):
        """書籍アイテムウィジェットを作成"""
        item = QWidget()
        item.setFixedSize(self.item_width, self.item_height)
        item.setObjectName(f"book_item_{index}")

        # スタイルシート
        item.setStyleSheet(
            "QWidget#book_item_" + str(index) + " { "
            "    background-color: #f0f0f0; "
            "    border-radius: 5px; "
            "    border: 1px solid #cccccc; "
            "}"
            "QWidget#book_item_" + str(index) + ":hover { "
            "    background-color: #e0e0e0; "
            "    border: 1px solid #aaaaaa; "
            "}"
        )

        layout = QVBoxLayout(item)
        layout.setContentsMargins(5, 5, 5, 5)

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
        item.mousePressEvent = lambda event, idx=index: self._on_item_clicked(idx)

        return item

    def _on_item_clicked(self, index):
        """アイテムクリック時の処理"""
        # 既存の選択状態をリセット
        if 0 <= self.selected_index < len(self.books):
            old_item = self.content_widget.findChild(
                QWidget, f"book_item_{self.selected_index}"
            )
            if old_item:
                old_item.setStyleSheet(
                    "QWidget#book_item_" + str(self.selected_index) + " { "
                    "    background-color: #f0f0f0; "
                    "    border-radius: 5px; "
                    "    border: 1px solid #cccccc; "
                    "}"
                    "QWidget#book_item_" + str(self.selected_index) + ":hover { "
                    "    background-color: #e0e0e0; "
                    "    border: 1px solid #aaaaaa; "
                    "}"
                )

        # 新しい選択状態
        self.selected_index = index
        item = self.content_widget.findChild(QWidget, f"book_item_{index}")
        if item:
            item.setStyleSheet(
                "QWidget#book_item_" + str(index) + " { "
                "    background-color: #d0d0ff; "
                "    border-radius: 5px; "
                "    border: 2px solid #6666cc; "
                "}"
            )

        # 選択シグナルを発行
        self.book_selected.emit(self.books[index])

    def contextMenuEvent(self, event):
        """コンテキストメニューイベント"""
        # クリックされた位置のアイテムを特定
        for i in range(len(self.books)):
            item = self.content_widget.findChild(QWidget, f"book_item_{i}")
            if item and item.geometry().contains(
                event.pos() - self.content_widget.pos()
            ):
                self._on_item_clicked(i)

                # コンテキストメニューを作成
                menu = QMenu(self)

                open_action = QAction("開く", self)
                open_action.triggered.connect(lambda: self._open_book(i))
                menu.addAction(open_action)

                edit_action = QAction("編集", self)
                edit_action.triggered.connect(lambda: self._edit_book(i))
                menu.addAction(edit_action)

                menu.addSeparator()

                delete_action = QAction("削除", self)
                delete_action.triggered.connect(lambda: self._delete_book(i))
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

    def set_books(self, books):
        """書籍リストを設定"""
        self.books = books
        self._update_view()

    def set_items_per_shelf(self, count):
        """一棚あたりのアイテム数を設定"""
        self.items_per_shelf = max(1, count)
        self._update_view()

    def _update_view(self):
        """ビューを更新"""
        # 既存のアイテムをクリア
        while self.shelves_layout.count():
            item = self.shelves_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 書籍がない場合は終了
        if not self.books:
            return

        # 何棚必要かを計算
        shelf_count = (
            len(self.books) + self.items_per_shelf - 1
        ) // self.items_per_shelf

        # 棚ごとに書籍を配置
        for shelf_index in range(shelf_count):
            # 棚のウィジェット
            shelf = QWidget()
            shelf.setObjectName(f"shelf_{shelf_index}")
            shelf.setStyleSheet(
                f"QWidget#shelf_{shelf_index} {{ "
                "    background-color: #8B4513; "  # 棚の茶色
                "    border-radius: 3px; "
                "    min-height: 30px; "
                "}}"
            )
            shelf_layout = QHBoxLayout(shelf)
            shelf_layout.setContentsMargins(5, 5, 5, 5)
            shelf_layout.setSpacing(0)  # 本の間隔を狭く

            # 棚に本を配置
            start_idx = shelf_index * self.items_per_shelf
            end_idx = min(start_idx + self.items_per_shelf, len(self.books))

            for i in range(start_idx, end_idx):
                book = self.books[i]
                book_widget = self._create_book_spine(book, i)
                shelf_layout.addWidget(book_widget)

            # 棚を追加
            self.shelves_layout.addWidget(shelf)

    def _create_book_spine(self, book, index):
        """本の背表紙ウィジェットを作成"""
        # 本の背表紙
        spine = QWidget()
        spine.setObjectName(f"book_spine_{index}")
        spine.setFixedWidth(30)  # 背表紙の幅
        spine.setMinimumHeight(150)  # 背表紙の高さ

        # タイトルから背景色を生成
        hue = sum(ord(c) for c in book.title) % 360
        spine.setStyleSheet(
            f"QWidget#book_spine_{index} {{ "
            f"    background-color: hsv({hue}, 200, 220); "
            "    border: 1px solid #555555; "
            "    border-radius: 2px; "
            "}}"
        )

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

        # クリックイベント
        spine.mousePressEvent = lambda event, idx=index: self._on_spine_clicked(idx)

        return spine

    def _on_spine_clicked(self, index):
        """背表紙クリック時の処理"""
        # 既存の選択状態をリセット
        if 0 <= self.selected_index < len(self.books):
            spine = self.findChild(QWidget, f"book_spine_{self.selected_index}")
            if spine:
                # もとのスタイルに戻す
                book = self.books[self.selected_index]
                hue = sum(ord(c) for c in book.title) % 360
                spine.setStyleSheet(
                    f"QWidget#book_spine_{self.selected_index} {{ "
                    f"    background-color: hsv({hue}, 200, 220); "
                    "    border: 1px solid #555555; "
                    "    border-radius: 2px; "
                    "}}"
                )

        # 新しい選択状態
        self.selected_index = index
        spine = self.findChild(QWidget, f"book_spine_{index}")
        if spine:
            spine.setStyleSheet(
                f"QWidget#book_spine_{index} {{ "
                "    background-color: #ffff00; "  # 黄色でハイライト
                "    border: 2px solid #ff0000; "
                "    border-radius: 2px; "
                "}}"
            )

        # 選択シグナルを発行
        self.book_selected.emit(self.books[index])

    def contextMenuEvent(self, event):
        """コンテキストメニューイベント"""
        # クリックされた位置のアイテムを特定
        for i in range(len(self.books)):
            spine = self.findChild(QWidget, f"book_spine_{i}")
            pos = spine.mapFrom(self, event.pos())
            if spine and spine.rect().contains(pos):
                self._on_spine_clicked(i)

                # コンテキストメニューを作成
                menu = QMenu(self)

                open_action = QAction("開く", self)
                open_action.triggered.connect(lambda: self._open_book(i))
                menu.addAction(open_action)

                edit_action = QAction("編集", self)
                edit_action.triggered.connect(lambda: self._edit_book(i))
                menu.addAction(edit_action)

                menu.addSeparator()

                delete_action = QAction("削除", self)
                delete_action.triggered.connect(lambda: self._delete_book(i))
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
