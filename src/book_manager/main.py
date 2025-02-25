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
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen


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

        # ライブラリビューのシグナルに接続
        # 具体的な接続はライブラリビューの実装後に追加

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
