import fitz  # PyMuPDF
from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPixmap, QTransform
from PyQt6.QtWidgets import (
    QComboBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class PDFReaderView(QWidget):
    """
    PDFファイルを表示するビューコンポーネント。

    ページナビゲーション、ズーム、表示モードなどの
    基本的なPDF閲覧機能を提供する。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    # カスタムシグナル
    progress_updated = pyqtSignal(int, int, str)  # book_id, current_page, status

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
        self.current_book_id = None
        self.current_page_num = 0
        self.zoom_factor = 1.0
        self.auto_fit = True  # 自動フィット機能を有効化

        # レイアウトの設定
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # ツールバーの設定
        self.setup_toolbar()

        # ステータスバーの設定
        self.setup_statusbar()

        # PDF表示領域の設定
        self.setup_viewer()

        # 初期状態（書籍なし）の設定
        self.update_ui_state(False)

    def setup_toolbar(self):
        """ツールバーを設定する。"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        self.layout.addWidget(self.toolbar)

        # 前のページボタン
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.toolbar.addWidget(self.prev_button)

        # 次のページボタン
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_to_next_page)
        self.toolbar.addWidget(self.next_button)

        # ページジャンプコントロール
        self.toolbar.addSeparator()
        self.page_label = QLabel("Page:")
        self.toolbar.addWidget(self.page_label)

        self.page_combo = QComboBox()
        self.page_combo.setEditable(True)
        self.page_combo.setMinimumWidth(80)
        self.page_combo.activated.connect(self.on_page_selected)
        self.toolbar.addWidget(self.page_combo)

        self.total_pages_label = QLabel("/ 0")
        self.toolbar.addWidget(self.total_pages_label)

        # ズームコントロール
        self.toolbar.addSeparator()
        self.zoom_label = QLabel("Zoom:")
        self.toolbar.addWidget(self.zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setEditable(True)
        self.zoom_combo.activated.connect(self.on_zoom_selected)
        self.toolbar.addWidget(self.zoom_combo)

        # ズームインボタン
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.toolbar.addWidget(self.zoom_in_button)

        # ズームアウトボタン
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.toolbar.addWidget(self.zoom_out_button)

    def setup_statusbar(self):
        """ステータスバーを設定する。"""
        self.statusbar = QWidget()
        self.statusbar_layout = QHBoxLayout(self.statusbar)
        self.statusbar_layout.setContentsMargins(5, 0, 5, 0)

        # 読書進捗スライダー
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.progress_slider.valueChanged.connect(self.on_slider_value_changed)
        self.statusbar_layout.addWidget(self.progress_slider)

        # 読書状態ラベル
        self.status_label = QLabel("Not reading")
        self.statusbar_layout.addWidget(self.status_label)

        self.layout.addWidget(self.statusbar)

    def setup_viewer(self):
        """PDF表示領域を設定する。"""
        # スクロール可能なビュー
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # PDFページ用のグラフィックスビュー
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.graphics_view.setBackgroundBrush(Qt.GlobalColor.lightGray)
        self.graphics_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graphics_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # グラフィックスシーン
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        # プレースホルダー
        self.placeholder_label = QLabel("No book selected")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # 初期状態ではプレースホルダーを表示
        self.scroll_area.setWidget(self.placeholder_label)

        self.layout.addWidget(self.scroll_area)

    def load_book(self, book_id):
        """
        書籍をロードする。

        Parameters
        ----------
        book_id : int
            ロードする書籍のID

        Returns
        -------
        bool
            ロードが成功したかどうか
        """
        # 現在の書籍を閉じる
        self.close_current_book()

        # 新しい書籍を取得
        book = self.library_controller.get_book(book_id)
        if not book or not book.exists():
            QMessageBox.warning(
                self,
                "Error Loading Book",
                f"The book file could not be found at:\n{book.file_path if book else 'Unknown'}",
            )
            return False

        # 書籍を開く
        doc = book.open()
        if not doc:
            QMessageBox.warning(
                self,
                "Error Opening PDF",
                "Failed to open the PDF file. It may be corrupted or password-protected.",
            )
            return False

        # 書籍とページ番号を設定
        self.library_controller.set_current_book(book)
        self.current_book_id = book_id
        self.current_page_num = book.current_page

        # UI状態を更新
        self.update_ui_state(True)

        # 表示領域をグラフィックスビューに変更
        self.scroll_area.takeWidget()  # プレースホルダーを取り外す
        self.scroll_area.setWidget(self.graphics_view)

        # 最初のページを表示
        self.show_current_page()

        # 進捗スライダーを更新
        self.update_progress_slider()

        # ページコンボボックスを更新
        self.update_page_combo()

        return True

    def close_current_book(self):
        """現在開いている書籍を閉じる。"""
        if self.current_book_id:
            book = self.library_controller.get_current_book()
            if book:
                book.close()

            self.current_book_id = None
            self.current_page_num = 0
            self.scene.clear()
            self.update_ui_state(False)

            # 表示領域をプレースホルダーに変更
            self.scroll_area.takeWidget()
            self.scroll_area.setWidget(self.placeholder_label)

    def update_ui_state(self, has_book):
        """
        UI状態を更新する。

        Parameters
        ----------
        has_book : bool
            書籍が開かれているかどうか
        """
        # ツールバーの有効/無効を設定
        self.prev_button.setEnabled(has_book)
        self.next_button.setEnabled(has_book)
        self.page_combo.setEnabled(has_book)
        self.zoom_combo.setEnabled(has_book)
        self.zoom_in_button.setEnabled(has_book)
        self.zoom_out_button.setEnabled(has_book)

        # ステータスバーの有効/無効を設定
        self.progress_slider.setEnabled(has_book)

        if not has_book:
            self.status_label.setText("No book selected")
            self.total_pages_label.setText("/ 0")
            self.progress_slider.setValue(0)

    def update_page_combo(self):
        """ページコンボボックスを更新する。"""
        book = self.library_controller.get_current_book()
        if not book:
            return

        total_pages = book.total_pages

        self.page_combo.clear()
        for i in range(total_pages):
            self.page_combo.addItem(str(i + 1))

        self.page_combo.setCurrentIndex(self.current_page_num)
        self.total_pages_label.setText(f"/ {total_pages}")

    def update_progress_slider(self):
        """進捗スライダーを更新する。"""
        book = self.library_controller.get_current_book()
        if not book or book.total_pages <= 0:
            return

        progress_pct = int((self.current_page_num + 1) / book.total_pages * 100)
        self.progress_slider.blockSignals(True)  # 一時的にシグナルをブロック
        self.progress_slider.setValue(progress_pct)
        self.progress_slider.blockSignals(False)

        # ステータスラベルも更新
        status_text = "Unread"
        if book.status == book.STATUS_READING:
            status_text = "Reading"
        elif book.status == book.STATUS_COMPLETED:
            status_text = "Completed"

        self.status_label.setText(
            f"{status_text} - Page {self.current_page_num + 1} of {book.total_pages} ({progress_pct}%)"
        )

    def show_current_page(self):
        """現在のページを表示する。"""
        book = self.library_controller.get_current_book()
        if not book:
            return

        # シーンをクリア
        self.scene.clear()

        # ページを取得してレンダリング
        try:
            # ページをピクセルマップとして取得
            doc = book.open()
            page = doc[self.current_page_num]

            # ズーム係数を適用
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix)

            # QImageに変換
            img = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888,
            )

            # QPixmapに変換
            pixmap = QPixmap.fromImage(img)

            # シーンに追加
            self.scene.setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))
            self.scene.addPixmap(pixmap)

            # 進捗を更新
            self.update_reading_progress()

        except Exception as e:
            print(f"Error rendering page: {e}")
            self.scene.addText(f"Error displaying page: {str(e)}")

    def update_reading_progress(self):
        """読書進捗を更新する。"""
        if not self.current_book_id:
            return

        book = self.library_controller.get_current_book()
        if not book:
            return

        # 状態の自動判定
        status = None

        # すでにCompletedに設定されている場合は、どのページにいても維持する
        if book.status == book.STATUS_COMPLETED:
            status = book.STATUS_COMPLETED
        # それ以外の場合は現在のページに基づいて判定
        elif self.current_page_num == 0 and book.status != book.STATUS_COMPLETED:
            # 最初のページで、かつまだCompletedでない場合のみUnread
            status = book.STATUS_UNREAD
        elif self.current_page_num >= book.total_pages - 1:
            # 最後のページならCompleted
            status = book.STATUS_COMPLETED
        else:
            # それ以外はReading
            status = book.STATUS_READING

        # 進捗を更新
        self.library_controller.update_book_progress(
            book_id=self.current_book_id,
            current_page=self.current_page_num,
            status=status,
        )

        # UIを更新
        self.update_progress_slider()

        # 進捗更新シグナルを発火
        self.progress_updated.emit(self.current_book_id, self.current_page_num, status)

    def go_to_page(self, page_num):
        """
        指定したページに移動する。

        Parameters
        ----------
        page_num : int
            移動先のページ番号（0から始まる）

        Returns
        -------
        bool
            移動が成功したかどうか
        """
        book = self.library_controller.get_current_book()
        if not book:
            return False

        # ページ番号の境界チェック
        if page_num < 0:
            page_num = 0
        elif page_num >= book.total_pages:
            page_num = book.total_pages - 1

        # ページが変わらない場合は何もしない
        if page_num == self.current_page_num:
            return True

        # ページを更新
        self.current_page_num = page_num
        self.show_current_page()

        # コンボボックスも同期
        self.page_combo.setCurrentIndex(page_num)

        return True

    def go_to_previous_page(self):
        """前のページに移動する。"""
        self.go_to_page(self.current_page_num - 1)

    def go_to_next_page(self):
        """次のページに移動する。"""
        self.go_to_page(self.current_page_num + 1)

    def on_page_selected(self, index):
        """
        ページコンボボックスで選択されたとき。

        Parameters
        ----------
        index : int
            選択されたインデックス
        """
        try:
            # テキスト入力の場合
            page_num = int(self.page_combo.currentText()) - 1
            self.go_to_page(page_num)
        except ValueError:
            # 無効な入力の場合は現在のページに戻す
            self.page_combo.setCurrentIndex(self.current_page_num)

    def on_zoom_selected(self, index):
        """
        ズームコンボボックスで選択されたとき。

        Parameters
        ----------
        index : int
            選択されたインデックス
        """
        try:
            zoom_text = self.zoom_combo.currentText().rstrip("%")
            zoom_factor = float(zoom_text) / 100.0
            self.set_zoom(zoom_factor)
        except ValueError:
            # 無効な入力の場合は現在のズームに戻す
            self.zoom_combo.setCurrentText(f"{int(self.zoom_factor * 100)}%")

    def set_zoom(self, factor):
        """
        ズーム係数を設定する。

        Parameters
        ----------
        factor : float
            ズーム係数（1.0 = 100%）
        """
        if factor < 0.1:
            factor = 0.1
        elif factor > 5.0:
            factor = 5.0

        if factor != self.zoom_factor:
            self.zoom_factor = factor
            self.zoom_combo.setCurrentText(f"{int(factor * 100)}%")
            self.show_current_page()  # ページを再表示

    def zoom_in(self):
        """ズームイン（拡大）する。"""
        self.set_zoom(self.zoom_factor * 1.2)

    def zoom_out(self):
        """ズームアウト（縮小）する。"""
        self.set_zoom(self.zoom_factor / 1.2)

    def resizeEvent(self, event):
        """
        ウィジェットのリサイズイベント。

        Parameters
        ----------
        event : QResizeEvent
            リサイズイベント
        """
        super().resizeEvent(event)

        # 自動フィットが有効で、書籍が開かれている場合は自動的にフィット
        if self.auto_fit and self.current_book_id:
            self.fit_to_page()

    def fit_to_width(self):
        """ページを幅に合わせる。"""
        book = self.library_controller.get_current_book()
        if not book:
            return

        doc = book.open()
        page = doc[self.current_page_num]

        # ページの元のサイズを取得
        rect = page.rect
        page_width = rect.width

        # ビューの幅を取得
        view_width = (
            self.graphics_view.viewport().width() - 20
        )  # マージン用に少し小さく

        # ズーム係数を計算
        zoom_factor = view_width / page_width

        self.set_zoom(zoom_factor)

    def fit_to_page(self):
        """ページ全体を表示領域に合わせる。"""
        book = self.library_controller.get_current_book()
        if not book:
            return

        doc = book.open()
        page = doc[self.current_page_num]

        # ページの元のサイズを取得
        rect = page.rect
        page_width = rect.width
        page_height = rect.height

        # ビューのサイズを取得
        view_width = (
            self.graphics_view.viewport().width() - 20
        )  # マージン用に少し小さく
        view_height = self.graphics_view.viewport().height() - 20

        # 幅と高さに基づくズーム係数を計算
        zoom_width = view_width / page_width
        zoom_height = view_height / page_height

        # 小さい方のズーム係数を使用（全体が表示できるように）
        zoom_factor = min(zoom_width, zoom_height)

        self.set_zoom(zoom_factor)

    def on_slider_value_changed(self, value):
        """
        進捗スライダーの値が変更されたとき。

        Parameters
        ----------
        value : int
            新しいスライダーの値（0-100）
        """
        book = self.library_controller.get_current_book()
        if not book or book.total_pages <= 0:
            return

        # 値をページ番号に変換
        page_num = int(value * book.total_pages / 100) - 1
        if page_num < 0:
            page_num = 0

        # ページに移動
        self.go_to_page(page_num)
