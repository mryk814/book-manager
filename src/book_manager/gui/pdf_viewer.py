import logging
import os

import fitz  # PyMuPDF
from PyQt6.QtCore import QPoint, QRect, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QImage,
    QKeyEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class PDFPageWidget(QLabel):
    """PDFページを表示するウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #444444;")

        # ページ画像
        self.page_pixmap = None
        self.zoom_factor = 1.0
        self.fit_to_window = True  # デフォルトでウィンドウに合わせる

    def set_page_pixmap(self, pixmap, zoom=1.0):
        """ページ画像を設定"""
        self.page_pixmap = pixmap
        self.zoom_factor = zoom

        if pixmap:
            if self.fit_to_window:
                self.fit_pixmap_to_window()
            else:
                # ズーム適用
                scaled_pixmap = pixmap.scaled(
                    int(pixmap.width() * zoom),
                    int(pixmap.height() * zoom),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.setPixmap(scaled_pixmap)
        else:
            self.clear()

    def fit_pixmap_to_window(self):
        """ピクセルマップをウィンドウに合わせる"""
        if not self.page_pixmap:
            return

        # 親のサイズを取得
        parent_size = self.size()

        # 余白を考慮
        available_width = parent_size.width() - 20
        available_height = parent_size.height() - 20

        # ピクセルマップをリサイズ
        scaled_pixmap = self.page_pixmap.scaled(
            available_width,
            available_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setPixmap(scaled_pixmap)

    def set_fit_to_window(self, fit):
        """ウィンドウに合わせるかどうかを設定"""
        self.fit_to_window = fit
        if self.page_pixmap:
            if fit:
                self.fit_pixmap_to_window()
            else:
                # 通常のズーム表示に戻す
                scaled_pixmap = self.page_pixmap.scaled(
                    int(self.page_pixmap.width() * self.zoom_factor),
                    int(self.page_pixmap.height() * self.zoom_factor),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """リサイズイベント"""
        super().resizeEvent(event)
        if self.fit_to_window and self.page_pixmap:
            self.fit_pixmap_to_window()

    def clear_page(self):
        """ページを消去"""
        self.page_pixmap = None
        self.clear()


class PDFViewWidget(QScrollArea):
    """スクロール可能なPDFビューウィジェット"""

    # ページナビゲーションシグナル
    page_changed = pyqtSignal(int)  # 現在のページが変わったとき
    double_clicked = pyqtSignal()  # ダブルクリック

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # コンテンツウィジェット
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        # レイアウト
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ページビューウィジェット
        self.page_view = PDFPageWidget()
        self.layout.addWidget(self.page_view)

        # PDFドキュメント
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        self.rotation = 0
        self.page_pixmaps = {}  # ページのキャッシュ

        # ビューモード
        self.view_mode = "single"  # single, double, continuous
        self.manga_mode = False  # 右から左への表示
        self.fit_to_window = True  # デフォルトでウィンドウに合わせる

    def load_document(self, pdf_path):
        """PDFドキュメントを読み込む"""
        try:
            # 既存のドキュメントを閉じる
            if self.doc:
                self.doc.close()
                self.page_pixmaps.clear()

            # 新しいドキュメントを開く
            self.doc = fitz.open(pdf_path)
            self.total_pages = len(self.doc)
            self.current_page = 0

            if self.total_pages > 0:
                self._render_current_page()
                return True
            else:
                self.doc = None
                return False

        except Exception as e:
            logging.error(f"PDFドキュメント読み込みエラー: {e}")
            self.doc = None
            return False

    def _render_current_page(self):
        """現在のページをレンダリング"""
        if not self.doc or self.current_page >= self.total_pages:
            return

        # キャッシュから取得
        cache_key = f"{self.current_page}_{self.zoom_factor}_{self.rotation}"
        if cache_key in self.page_pixmaps:
            self.page_view.set_page_pixmap(self.page_pixmaps[cache_key], 1.0)
            self.page_changed.emit(self.current_page)
            return

        try:
            # ページを取得
            page = self.doc.load_page(self.current_page)

            # 回転を適用
            rot = self.rotation

            # ズーム適用のためのマトリックス
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor).prerotate(rot)

            # ピクセルマップ作成
            pix = page.get_pixmap(matrix=matrix, alpha=False)

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

            # キャッシュに保存
            self.page_pixmaps[cache_key] = pixmap

            # 表示
            self.page_view.set_page_pixmap(pixmap, 1.0)
            # フィットモード設定を適用
            self.page_view.set_fit_to_window(self.fit_to_window)

            # シグナル発行
            self.page_changed.emit(self.current_page)

        except Exception as e:
            logging.error(f"ページレンダリングエラー (ページ {self.current_page}): {e}")

    def goto_page(self, page_num):
        """指定ページに移動"""
        if not self.doc:
            return

        # ページ番号の有効性チェック
        page_num = max(0, min(page_num, self.total_pages - 1))

        if page_num != self.current_page:
            self.current_page = page_num
            self._render_current_page()

    def next_page(self):
        """次のページへ"""
        if not self.doc:
            return

        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._render_current_page()

    def prev_page(self):
        """前のページへ"""
        if not self.doc:
            return

        if self.current_page > 0:
            self.current_page -= 1
            self._render_current_page()

    def set_zoom(self, zoom_factor):
        """ズーム倍率を設定"""
        self.zoom_factor = zoom_factor
        if self.fit_to_window:
            # フィットモードを解除
            self.set_fit_to_window(False)
        self._render_current_page()

    def zoom_in(self):
        """拡大"""
        if self.fit_to_window:
            # フィットモードを解除
            self.set_fit_to_window(False)
        self.zoom_factor = min(3.0, self.zoom_factor * 1.2)
        self._render_current_page()

    def zoom_out(self):
        """縮小"""
        if self.fit_to_window:
            # フィットモードを解除
            self.set_fit_to_window(False)
        self.zoom_factor = max(0.1, self.zoom_factor / 1.2)
        self._render_current_page()

    def set_fit_to_window(self, fit):
        """ウィンドウに合わせる設定"""
        self.fit_to_window = fit
        if self.doc:
            self.page_view.set_fit_to_window(fit)

    def set_rotation(self, rotation):
        """回転を設定"""
        self.rotation = rotation % 360
        self._render_current_page()

    def rotate_clockwise(self):
        """時計回りに回転"""
        self.rotation = (self.rotation + 90) % 360
        self._render_current_page()

    def rotate_counterclockwise(self):
        """反時計回りに回転"""
        self.rotation = (self.rotation - 90) % 360
        self._render_current_page()

    def set_view_mode(self, mode):
        """表示モードを設定"""
        if mode in ["single", "double", "continuous"]:
            self.view_mode = mode
            self._render_current_page()

    def set_manga_mode(self, manga_mode):
        """マンガモード（右から左）を設定"""
        self.manga_mode = manga_mode
        self._render_current_page()

    def clear(self):
        """表示をクリア"""
        self.page_view.clear_page()
        if self.doc:
            self.doc.close()
            self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.page_pixmaps.clear()

    def resizeEvent(self, event):
        """リサイズイベント"""
        super().resizeEvent(event)
        if self.fit_to_window and self.doc:
            # ページを再レンダリングせずに、既存のピクセルマップを使用してフィット表示を更新
            self.page_view.fit_pixmap_to_window()

    def mousePressEvent(self, event):
        """マウスプレスイベント"""
        # スクロールバーハンドリングを優先
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """ダブルクリックイベント"""
        self.double_clicked.emit()

    def keyPressEvent(self, event):
        """キーイベント"""
        key = event.key()

        if key == Qt.Key.Key_Right or key == Qt.Key.Key_Down or key == Qt.Key.Key_Space:
            if self.manga_mode:
                self.prev_page()
            else:
                self.next_page()
        elif (
            key == Qt.Key.Key_Left
            or key == Qt.Key.Key_Up
            or key == Qt.Key.Key_Backspace
        ):
            if self.manga_mode:
                self.next_page()
            else:
                self.prev_page()
        elif key == Qt.Key.Key_Home:
            self.goto_page(0)
        elif key == Qt.Key.Key_End:
            self.goto_page(self.total_pages - 1)
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            self.zoom_in()
        elif key == Qt.Key.Key_Minus:
            self.zoom_out()
        elif key == Qt.Key.Key_0:
            self.set_zoom(1.0)
        elif key == Qt.Key.Key_R:
            self.rotate_clockwise()
        elif key == Qt.Key.Key_L:
            self.rotate_counterclockwise()
        elif key == Qt.Key.Key_F:
            # Fキーでフィットモード切替
            self.set_fit_to_window(not self.fit_to_window)
        else:
            super().keyPressEvent(event)


class BookmarkDialog(QDialog):
    """ブックマーク追加ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ブックマークの追加")
        self.setMinimumWidth(300)

        # レイアウト
        layout = QVBoxLayout(self)

        # フォーム
        form_layout = QFormLayout()

        # ブックマーク名
        self.name_edit = QLineEdit()
        form_layout.addRow("名前:", self.name_edit)

        layout.addLayout(form_layout)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_bookmark_name(self):
        """ブックマーク名を取得"""
        return self.name_edit.text()


class PDFViewerWindow(QMainWindow):
    """PDFビューアウィンドウ"""

    # 読書状態が変更されたときのシグナル
    reading_status_changed = pyqtSignal(int, int)  # book_id, current_page

    def __init__(self, library_manager, config, parent=None):
        super().__init__(parent)
        self.library_manager = library_manager
        self.config = config
        self.db_manager = library_manager.db

        # 現在の書籍
        self.current_book = None

        # ブックマークの自動保存タイマー
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave_progress)
        self.autosave_timer.setInterval(30000)  # 30秒

        # UIの初期化
        self._init_ui()

    def _init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("PDFビューア")
        self.resize(1000, 800)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # PDFビューウィジェット - この行を_create_toolbarの前に移動
        self.pdf_view = PDFViewWidget()
        self.pdf_view.page_changed.connect(self._on_page_changed)
        self.pdf_view.double_clicked.connect(self._toggle_fullscreen)

        # ツールバー
        self._create_toolbar()

        # PDFビューを追加
        main_layout.addWidget(self.pdf_view)

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # ページ情報ラベル
        self.page_info_label = QLabel()
        self.status_bar.addPermanentWidget(self.page_info_label)

        # ビューモード設定
        view_mode = self.config.get("viewer.page_turn_mode", "single")
        self.pdf_view.set_view_mode(view_mode)

        # マンガモード設定
        manga_mode = self.config.get("viewer.manga_mode", False)
        self.pdf_view.set_manga_mode(manga_mode)

    def _create_toolbar(self):
        """ツールバーを作成"""
        toolbar = QToolBar("PDF表示ツールバー")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # ナビゲーションアクション
        self.prev_action = QAction("前へ", self)
        self.prev_action.triggered.connect(lambda: self.pdf_view.prev_page())
        toolbar.addAction(self.prev_action)

        self.next_action = QAction("次へ", self)
        self.next_action.triggered.connect(lambda: self.pdf_view.next_page())
        toolbar.addAction(self.next_action)

        # ページ選択
        toolbar.addSeparator()

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self._on_page_spin_changed)
        toolbar.addWidget(self.page_spin)

        self.total_pages_label = QLabel("/ 1")
        toolbar.addWidget(self.total_pages_label)

        # ズームコントロール
        toolbar.addSeparator()

        self.zoom_out_action = QAction("縮小", self)
        self.zoom_out_action.triggered.connect(lambda: self.pdf_view.zoom_out())
        toolbar.addAction(self.zoom_out_action)

        self.zoom_combo = QComboBox()
        zoom_levels = [
            "ウィンドウに合わせる",
            "50%",
            "75%",
            "100%",
            "125%",
            "150%",
            "200%",
            "300%",
        ]
        self.zoom_combo.addItems(zoom_levels)
        self.zoom_combo.setCurrentIndex(0)  # デフォルトで「ウィンドウに合わせる」
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_combo_changed)
        toolbar.addWidget(self.zoom_combo)

        self.zoom_in_action = QAction("拡大", self)
        self.zoom_in_action.triggered.connect(lambda: self.pdf_view.zoom_in())
        toolbar.addAction(self.zoom_in_action)

        # ウィンドウに合わせるアクション
        self.fit_window_action = QAction("ウィンドウに合わせる", self)
        self.fit_window_action.setCheckable(True)
        self.fit_window_action.setChecked(True)  # デフォルトで有効
        self.fit_window_action.triggered.connect(self._toggle_fit_window)
        toolbar.addAction(self.fit_window_action)

        # 回転
        toolbar.addSeparator()

        self.rotate_ccw_action = QAction("左回転", self)
        self.rotate_ccw_action.triggered.connect(
            lambda: self.pdf_view.rotate_counterclockwise()
        )
        toolbar.addAction(self.rotate_ccw_action)

        self.rotate_cw_action = QAction("右回転", self)
        self.rotate_cw_action.triggered.connect(
            lambda: self.pdf_view.rotate_clockwise()
        )
        toolbar.addAction(self.rotate_cw_action)

        # 表示モード
        toolbar.addSeparator()

        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["単一ページ", "見開き", "連続"])

        # 初期モードを設定
        view_mode = self.config.get("viewer.page_turn_mode", "single")
        if view_mode == "single":
            self.view_mode_combo.setCurrentIndex(0)
        elif view_mode == "double":
            self.view_mode_combo.setCurrentIndex(1)
        elif view_mode == "continuous":
            self.view_mode_combo.setCurrentIndex(2)

        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        toolbar.addWidget(self.view_mode_combo)

        # マンガモード
        self.manga_mode_action = QAction("マンガモード", self)
        self.manga_mode_action.setCheckable(True)
        self.manga_mode_action.setChecked(self.config.get("viewer.manga_mode", False))
        self.manga_mode_action.triggered.connect(self._toggle_manga_mode)
        toolbar.addAction(self.manga_mode_action)

        # ブックマーク
        toolbar.addSeparator()

        self.add_bookmark_action = QAction("ブックマーク追加", self)
        self.add_bookmark_action.triggered.connect(self._add_bookmark)
        toolbar.addAction(self.add_bookmark_action)

        self.show_bookmarks_action = QAction("ブックマーク一覧", self)
        self.show_bookmarks_action.triggered.connect(self._show_bookmarks)
        toolbar.addAction(self.show_bookmarks_action)

        # 全画面表示
        toolbar.addSeparator()

        self.fullscreen_action = QAction("全画面", self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.triggered.connect(self._toggle_fullscreen)
        toolbar.addAction(self.fullscreen_action)

    def load_book(self, book):
        """書籍を読み込む"""
        if not book or not book.file_path or not os.path.exists(book.file_path):
            self.status_bar.showMessage("ファイルが見つかりません")
            return False

        self.current_book = book
        self.setWindowTitle(f"PDFビューア - {book.title}")

        # PDFを読み込む
        success = self.pdf_view.load_document(book.file_path)
        if not success:
            self.status_bar.showMessage("PDFの読み込みに失敗しました")
            return False

        # ページ選択のUI更新
        self.page_spin.setMaximum(self.pdf_view.total_pages)
        self.total_pages_label.setText(f"/ {self.pdf_view.total_pages}")

        # 前回のページ位置を復元
        if (
            self.config.get("viewer.remember_last_page", True)
            and book.current_page is not None
        ):
            self.pdf_view.goto_page(book.current_page)
        else:
            self.pdf_view.goto_page(0)

        # 自動保存タイマー開始
        self.autosave_timer.start()

        return True

    def _on_page_changed(self, page_num):
        """ページ変更時の処理"""
        # Spinボックス更新（シグナルループを防ぐため一時的にブロック）
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(page_num + 1)  # 表示上は1から始まる
        self.page_spin.blockSignals(False)

        # ステータスバー更新
        self.page_info_label.setText(
            f"ページ: {page_num + 1} / {self.pdf_view.total_pages}"
        )

        # 読書状態の更新
        if self.current_book:
            # 最後のページに達したら読了としてマーク
            if page_num >= self.pdf_view.total_pages - 1:
                self.current_book.reading_status = "読了"
            # 最初のページより先に進んだら読書中としてマーク
            elif page_num > 0:
                self.current_book.reading_status = "読書中"

    def _on_page_spin_changed(self, value):
        """ページスピン変更時の処理"""
        # 0ベースに変換
        self.pdf_view.goto_page(value - 1)

    def _on_zoom_changed(self, zoom_text):
        """ズーム変更時の処理"""
        # パーセント表示から浮動小数点に変換
        zoom_value = float(zoom_text.rstrip("%")) / 100.0
        self.pdf_view.set_zoom(zoom_value)

    def _on_zoom_combo_changed(self, index):
        """ズームコンボボックス変更時の処理"""
        text = self.zoom_combo.currentText()

        if text == "ウィンドウに合わせる":
            # ウィンドウに合わせるモードを有効化
            self.pdf_view.set_fit_to_window(True)
            self.fit_window_action.setChecked(True)
        else:
            # パーセント表示から浮動小数点に変換
            zoom_value = float(text.rstrip("%")) / 100.0
            self.pdf_view.set_fit_to_window(False)
            self.fit_window_action.setChecked(False)
            self.pdf_view.set_zoom(zoom_value)

    def _toggle_fit_window(self, checked):
        """ウィンドウに合わせるモードの切り替え"""
        self.pdf_view.set_fit_to_window(checked)

        # コンボボックスも連動して更新
        if checked:
            self.zoom_combo.setCurrentIndex(0)  # 「ウィンドウに合わせる」を選択
        else:
            # 現在のズーム率に近い項目を選択
            current_zoom = self.pdf_view.zoom_factor
            zoom_text = f"{int(current_zoom * 100)}%"
            index = self.zoom_combo.findText(zoom_text)
            if index >= 0:
                self.zoom_combo.setCurrentIndex(index)
            else:
                # 該当するズーム率がない場合は100%を選択
                index = self.zoom_combo.findText("100%")
                if index >= 0:
                    self.zoom_combo.setCurrentIndex(index)

    def _on_view_mode_changed(self, index):
        """表示モード変更時の処理"""
        modes = ["single", "double", "continuous"]
        if index < len(modes):
            mode = modes[index]
            self.pdf_view.set_view_mode(mode)
            self.config.set("viewer.page_turn_mode", mode)

    def _toggle_manga_mode(self, checked):
        """マンガモード切替"""
        self.pdf_view.set_manga_mode(checked)
        self.config.set("viewer.manga_mode", checked)

    def _toggle_fullscreen(self):
        """全画面表示切替"""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setChecked(False)
        else:
            self.showFullScreen()
            self.fullscreen_action.setChecked(True)

    def _add_bookmark(self):
        """ブックマークを追加"""
        if not self.current_book or not self.pdf_view.doc:
            return

        # ブックマーク追加ダイアログ
        dialog = BookmarkDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_bookmark_name()
            page = self.pdf_view.current_page

            # ブックマークを追加
            self.db_manager.add_bookmark(self.current_book.id, page, name)
            self.status_bar.showMessage(
                f"ブックマーク '{name}' をページ {page + 1} に追加しました", 3000
            )

    def _show_bookmarks(self):
        """ブックマーク一覧を表示"""
        if not self.current_book or not self.pdf_view.doc:
            return

        # ブックマーク取得
        bookmarks = self.db_manager.get_bookmarks_by_book(self.current_book.id)
        if not bookmarks:
            self.status_bar.showMessage("ブックマークはありません", 3000)
            return

        # ブックマークメニュー
        menu = QMenu(self)

        for bookmark in bookmarks:
            name = bookmark.name if bookmark.name else f"ページ {bookmark.page + 1}"
            action = QAction(name, self)
            action.triggered.connect(
                lambda checked, p=bookmark.page: self.pdf_view.goto_page(p)
            )
            menu.addAction(action)

        # メニュー表示
        menu.exec(self.mapToGlobal(self.show_bookmarks_action.parentWidget().pos()))

    def _autosave_progress(self):
        """読書進捗の自動保存"""
        if self.current_book and self.pdf_view.doc:
            page = self.pdf_view.current_page

            # 進捗を更新
            self.library_manager.update_reading_progress(self.current_book.id, page)

            # シグナル発行
            self.reading_status_changed.emit(self.current_book.id, page)

    def closeEvent(self, event):
        """ウィンドウを閉じるときの処理"""
        # 自動保存タイマーを停止
        self.autosave_timer.stop()

        # 最終進捗を保存
        if self.current_book and self.pdf_view.doc:
            page = self.pdf_view.current_page
            self.library_manager.update_reading_progress(self.current_book.id, page)

            # シグナル発行
            self.reading_status_changed.emit(self.current_book.id, page)

        # PDFを閉じる
        self.pdf_view.clear()

        event.accept()
