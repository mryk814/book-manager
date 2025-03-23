# src/views/controllers/reader_view_controller.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class ReaderViewController:
    """
    リーダービューを管理するコントローラクラス。

    PDFの表示、ページナビゲーション、ズーム機能などを提供する。

    Parameters
    ----------
    parent_widget : QWidget
        親ウィジェット
    reader_controller : ReaderController
        リーダーコントローラ
    """

    def __init__(self, parent_widget, reader_controller):
        """
        Parameters
        ----------
        parent_widget : QWidget
            親ウィジェット
        reader_controller : ReaderController
            リーダーコントローラ
        """
        self.parent = parent_widget
        self.reader_controller = reader_controller

        # 現在の状態
        self.current_book = None
        self.current_page = 0
        self.current_zoom = 1.0

        # メインウィジェットの作成
        self.main_widget = QWidget(parent_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # ツールバーの作成
        self._create_toolbar()

        # PDFビューエリアの作成
        self._create_pdf_view()

        # ナビゲーションバーの作成
        self._create_navigation_bar()

        # 初期状態では非表示
        self.main_widget.hide()

    def _create_toolbar(self):
        """リーダーツールバーを作成する"""
        toolbar = QToolBar()

        # 閉じるボタン
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self._on_close_clicked)
        toolbar.addWidget(self.close_button)

        toolbar.addSeparator()

        # ズームコントロール
        toolbar.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        toolbar.addWidget(self.zoom_slider)

        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(50, 200)
        self.zoom_spin.setValue(100)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.valueChanged.connect(self._on_zoom_spin_changed)
        toolbar.addWidget(self.zoom_spin)

        toolbar.addSeparator()

        # ページナビゲーションボタン
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self._on_prev_page_clicked)
        toolbar.addWidget(self.prev_button)

        self.page_label = QLabel("Page 0 / 0")
        toolbar.addWidget(self.page_label)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._on_next_page_clicked)
        toolbar.addWidget(self.next_button)

        self.layout.addWidget(toolbar)

    def _create_pdf_view(self):
        """PDFビューエリアを作成する"""
        self.pdf_view = QLabel()
        self.pdf_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_view.setMinimumSize(600, 800)
        self.pdf_view.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #cccccc;"
        )
        self.layout.addWidget(self.pdf_view)

    def _create_navigation_bar(self):
        """ナビゲーションバーを作成する"""
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        # ページ番号スピンボックス
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self._on_page_spin_changed)

        # 総ページ数ラベル
        self.total_pages_label = QLabel(" / 0")

        # ステータスラベル
        self.status_label = QLabel()

        # レイアウトに追加
        nav_layout.addStretch()
        nav_layout.addWidget(self.page_spin)
        nav_layout.addWidget(self.total_pages_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.status_label)

        self.layout.addWidget(nav_widget)

    def open_book(self, book_id):
        """
        書籍を開く

        Parameters
        ----------
        book_id : int
            開く書籍のID

        Returns
        -------
        bool
            成功したかどうか
        """
        result = self.reader_controller.open_book(book_id)
        if result:
            self.current_book = self.reader_controller.get_current_book()
            self.current_page = self.reader_controller.get_current_page()

            # UIを更新
            self._update_page_display()
            self._update_navigation_controls()

            # ウィジェットを表示
            self.main_widget.show()

            return True

        return False

    def _update_page_display(self):
        """現在のページを表示する"""
        if not self.current_book:
            return

        # ページのPixmapを取得
        pixmap = self.reader_controller.get_page_pixmap(self.current_zoom)
        if pixmap:
            # Pixmapを表示
            qpixmap = QPixmap.fromImage(pixmap.toImage())
            self.pdf_view.setPixmap(qpixmap)

            # ページ情報を更新
            total = self.current_book.total_pages
            current = self.current_page + 1  # 0ベースから1ベースに変換
            self.page_label.setText(f"Page {current} / {total}")

            # 読書進捗を更新
            self.reader_controller.update_reading_progress()

    def _update_navigation_controls(self):
        """ナビゲーションコントロールを更新する"""
        if not self.current_book:
            # コントロールを無効化
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.page_spin.setEnabled(False)
            self.page_spin.setMaximum(1)
            self.total_pages_label.setText(" / 0")
            self.status_label.setText("")
            return

        # 総ページ数
        total_pages = self.current_book.total_pages
        current_page = self.current_page + 1  # 0ベースから1ベースに変換

        # ページスピンの範囲を設定
        self.page_spin.setEnabled(True)
        self.page_spin.setMaximum(total_pages)
        self.page_spin.setValue(current_page)
        self.total_pages_label.setText(f" / {total_pages}")

        # 前後ページボタンの有効/無効設定
        self.prev_button.setEnabled(current_page > 1)
        self.next_button.setEnabled(current_page < total_pages)

        # 読書状態ラベルを更新
        progress = self.reader_controller.get_book_progress()
        if progress:
            status_text = f"{progress['status'].capitalize()} - {progress['progress_percentage']:.1f}%"
            self.status_label.setText(status_text)

    def _on_close_clicked(self):
        """閉じるボタンがクリックされたときのハンドラ"""
        self.close_book()

    def _on_prev_page_clicked(self):
        """前ページボタンがクリックされたときのハンドラ"""
        if self.reader_controller.go_to_previous_page():
            self.current_page = self.reader_controller.get_current_page()
            self._update_page_display()
            self._update_navigation_controls()

    def _on_next_page_clicked(self):
        """次ページボタンがクリックされたときのハンドラ"""
        if self.reader_controller.go_to_next_page():
            self.current_page = self.reader_controller.get_current_page()
            self._update_page_display()
            self._update_navigation_controls()

    def _on_page_spin_changed(self, value):
        """ページスピンボックスの値が変更されたときのハンドラ"""
        # 値が実際に変更された場合のみ処理（プログラムによる変更の場合は無視）
        if not self.current_book or value == self.current_page + 1:
            return

        if self.reader_controller.go_to_page(value - 1):  # 1ベースから0ベースに変換
            self.current_page = self.reader_controller.get_current_page()
            self._update_page_display()
            self._update_navigation_controls()

    def _on_zoom_changed(self, value):
        """ズームスライダーの値が変更されたときのハンドラ"""
        # ズーム値を計算（50%〜200%）
        zoom_factor = value / 100.0
        if zoom_factor != self.current_zoom:
            self.current_zoom = zoom_factor
            self._update_page_display()

            # スピンボックスも連動して更新
            self.zoom_spin.blockSignals(True)
            self.zoom_spin.setValue(value)
            self.zoom_spin.blockSignals(False)

    def _on_zoom_spin_changed(self, value):
        """ズームスピンボックスの値が変更されたときのハンドラ"""
        # スライダーも連動して更新
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(value)
        self.zoom_slider.blockSignals(False)

        # ズーム値を適用
        zoom_factor = value / 100.0
        if zoom_factor != self.current_zoom:
            self.current_zoom = zoom_factor
            self._update_page_display()

    def close_book(self):
        """現在開いている書籍を閉じる"""
        if self.current_book:
            self.reader_controller.close_current_book()
            self.current_book = None
            self.current_page = 0

            # PDFビューをクリア
            self.pdf_view.clear()
            self.pdf_view.setText("No book opened")

            # ナビゲーションコントロールを更新
            self._update_navigation_controls()

            # ウィジェットを非表示
            self.main_widget.hide()

            # 親ウィジェットに通知
            self.parent.on_book_closed()
