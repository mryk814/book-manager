import json
import logging
import os
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from views.main_window import MainWindow


def setup_logging():
    """ロギング設定を初期化する。"""
    log_dir = get_app_data_dir() / "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = log_dir / "pdf_library_manager.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    # サードパーティライブラリのログレベルを調整
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("fitz").setLevel(logging.WARNING)


def get_app_data_dir():
    """
    アプリケーションデータディレクトリのパスを取得する。

    Returns
    -------
    Path
        データディレクトリのパス
    """
    app_name = "PDFLibraryManager"

    if os.name == "nt":  # Windows
        app_data = os.getenv("APPDATA")
        return Path(app_data) / app_name
    elif os.name == "posix":  # macOS / Linux
        if os.path.exists(os.path.expanduser("~/Library/Application Support")):  # macOS
            return Path(os.path.expanduser("~/Library/Application Support")) / app_name
        else:  # Linux
            return Path(os.path.expanduser("~/.config")) / app_name
    else:
        # その他のOSはカレントディレクトリに
        return Path(os.getcwd()) / f".{app_name}"


def load_settings():
    """
    設定ファイルから設定を読み込む。

    Returns
    -------
    dict
        設定の辞書
    """
    default_settings = {
        "general": {"startup_show_last_book": True, "confirm_delete": True},
        "appearance": {
            "grid_columns": 4,
            "grid_cover_size": 150,
            "list_cover_size": 48,
            "default_view": "grid",  # or "list"
        },
        "paths": {
            "default_import_path": "",
            "database_path": str(get_app_data_dir() / "library.db"),
        },
        "reading": {
            "default_zoom": 100,  # パーセント
            "page_turn_mode": "continuous",  # or "single"
        },
    }

    settings_path = get_app_data_dir() / "settings.json"

    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    return default_settings


def main():
    """アプリケーションのエントリーポイント。"""
    # ロギングを設定
    setup_logging()

    # アプリケーションインスタンスを作成
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Library Manager")
    app.setApplicationVersion("1.0.0")

    # アプリケーションアイコンを設定（アイコンファイルがある場合）
    icon_path = os.path.join(
        os.path.dirname(__file__), "resources", "icons", "app_icon.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 設定を読み込む
    settings = load_settings()

    # データベースパスを取得
    db_path = settings["paths"]["database_path"]

    # データベースディレクトリを作成
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # メインウィンドウを作成
    window = MainWindow(db_path)
    window.show()

    # アプリケーションを実行
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
