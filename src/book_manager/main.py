import logging
import os
import sys
from pathlib import Path

# ローカルモジュールのインポート
from config import Config
from core.library_manager import LibraryManager
from core.pdf_manager import PDFManager
from database.db_manager import DatabaseManager
from gui.dialogs.metadata_dialog import MetadataDialog
from gui.main_window import MainWindow
from gui.pdf_viewer import PDFViewerWindow
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplashScreen,
    QVBoxLayout,
)


# ロギング設定
def setup_logging(config_dir):
    """ロギングの設定"""
    log_dir = os.path.join(config_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "pdf_library.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def main():
    """アプリケーションのメイン関数"""
    # アプリケーションの作成
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Library")
    app.setOrganizationName("PDF Library")

    # スプラッシュスクリーン（仮実装）
    splash_pixmap = QPixmap(200, 200)
    splash_pixmap.fill(Qt.GlobalColor.darkBlue)
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    app.processEvents()

    # 設定の読み込み
    try:
        config = Config()

        # ロギングの設定
        setup_logging(config.config_dir)

        logging.info("PDF Library アプリケーション起動中...")

        # データベースの初期化
        db_path = config.get("db_path")
        db_manager = DatabaseManager(db_path)

        # サムネイルディレクトリの設定
        thumbnail_dir = config.get("thumbnail_dir")

        # PDFマネージャーの初期化
        pdf_manager = PDFManager(thumbnail_dir)

        # ライブラリマネージャーの初期化
        library_manager = LibraryManager(db_manager, pdf_manager, config)

        # メインウィンドウの作成
        main_window = MainWindow(library_manager, config)

        # PDFビューアウィンドウの作成（非表示）
        pdf_viewer = PDFViewerWindow(library_manager, config)

        # ライブラリビューの初期化と接続
        from gui.library_view import LibraryView

        # ライブラリビュータブの準備
        library_view_tab = main_window.library_view_tab
        library_view_layout = QVBoxLayout(library_view_tab)
        library_view = LibraryView(library_manager, config, main_window)
        library_view_layout.addWidget(library_view)

        # 各種イベントの接続
        # 書籍を開くイベント
        def on_book_open_requested(book):
            if book and os.path.exists(book.file_path):
                if pdf_viewer.load_book(book):
                    pdf_viewer.show()
                    pdf_viewer.raise_()
                else:
                    QMessageBox.warning(
                        main_window, "エラー", f"書籍を開けませんでした: {book.title}"
                    )
            else:
                QMessageBox.warning(
                    main_window,
                    "ファイルが見つかりません",
                    f"ファイルが見つかりません: {book.file_path if book else 'Unknown'}",
                )

        # メタデータ編集イベント
        def on_book_edit_requested(book):
            from gui.dialogs.metadata_dialog import MetadataDialog

            dialog = MetadataDialog(library_manager, book, main_window)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                metadata = dialog.get_metadata()
                if metadata:
                    # メタデータを更新
                    library_manager.update_book_metadata(book.id, metadata)
                    # ビューを更新
                    library_view.refresh()

        # 書籍削除イベント
        def on_book_delete_requested(book):
            reply = QMessageBox.question(
                main_window,
                "書籍の削除",
                f"「{book.title}」を削除しますか？\nこの操作は元に戻せません。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # ファイルも削除するか尋ねる
                delete_file_reply = QMessageBox.question(
                    main_window,
                    "ファイルの削除",
                    "PDFファイルも削除しますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                delete_file = delete_file_reply == QMessageBox.StandardButton.Yes

                # 書籍を削除
                if library_manager.delete_book(book.id, delete_file):
                    QMessageBox.information(
                        main_window, "削除完了", f"書籍「{book.title}」を削除しました。"
                    )
                    # ビューを更新
                    library_view.refresh()
                else:
                    QMessageBox.warning(
                        main_window,
                        "削除エラー",
                        f"書籍「{book.title}」の削除に失敗しました。",
                    )

        # ライブラリビューのシグナルに接続
        library_view.book_open_requested.connect(on_book_open_requested)

        # メインウィンドウのビューモード変更シグナルに接続
        def on_view_mode_changed(index):
            modes = ["grid", "list", "bookshelf"]
            if index < len(modes):
                library_view.change_view_mode(modes[index])

        main_window.view_mode_combo.currentIndexChanged.connect(on_view_mode_changed)

        # メインウィンドウの検索シグナルに接続
        def on_search_requested(search_term):
            if search_term:
                count = library_view.search(search_term)
                main_window.status_bar.showMessage(f"検索結果: {count}件")
            else:
                library_view.refresh()
                main_window.status_bar.showMessage("検索をクリアしました")

        # メインウィンドウの更新メソッドをオーバーライド
        original_update_views = main_window._update_views

        def updated_update_views():
            original_update_views()
            library_view.refresh()

        main_window._update_views = updated_update_views

        # PDFビューアの読書状態変更シグナルに接続
        def on_reading_status_changed(book_id, current_page):
            # ビューを更新
            library_view.refresh()

        pdf_viewer.reading_status_changed.connect(on_reading_status_changed)

        # スプラッシュスクリーンを閉じてメインウィンドウを表示
        splash.finish(main_window)
        main_window.show()

        # アプリケーションの実行
        return app.exec()

    except Exception as e:
        logging.error(f"アプリケーション初期化エラー: {e}")
        splash.close()
        QMessageBox.critical(
            None, "初期化エラー", f"アプリケーションの初期化に失敗しました: {e}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
