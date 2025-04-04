import json
import logging
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from models.database import DatabaseManager
from views.main_window import MainWindow


def setup_logging():
    log_dir = get_app_data_dir() / "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = log_dir / "pdf_library_manager.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("fitz").setLevel(logging.WARNING)


def get_app_data_dir():
    app_name = "PDFLibraryManager"

    if os.name == "nt":
        app_data = os.getenv("APPDATA")
        return Path(app_data) / app_name
    elif os.name == "posix":
        if os.path.exists(os.path.expanduser("~/Library/Application Support")):  # macOS
            return Path(os.path.expanduser("~/Library/Application Support")) / app_name
        else:
            return Path(os.path.expanduser("~/.config")) / app_name
    else:
        return Path(os.getcwd()) / f".{app_name}"


def load_settings():
    default_settings = {
        "general": {"startup_show_last_book": True, "confirm_delete": True},
        "appearance": {
            "grid_columns": 4,
            "grid_cover_size": 150,
            "list_cover_size": 48,
            "default_view": "grid",
        },
        "paths": {
            "default_import_path": "",
            "database_path": str(get_app_data_dir() / "library.db"),
        },
        "reading": {
            "default_zoom": 100,
            "page_turn_mode": "continuous",
        },
    }

    settings_path = get_app_data_dir() / "settings.json"

    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)

                db_path = loaded_settings.get("paths", {}).get("database_path", "")
                if not db_path or not os.path.dirname(db_path):
                    loaded_settings.setdefault("paths", {})["database_path"] = str(
                        get_app_data_dir() / "library.db"
                    )
                    logging.warning(f"Invalid database path in settings, using default")

                return loaded_settings
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    return default_settings


def perform_db_migration(db_path, splash=None):
    if splash:
        splash.showMessage(
            "データベースマイグレーションを実行中...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        )

    try:
        temp_db_manager = DatabaseManager(db_path)
        temp_db_manager.migrate_database()
        temp_db_manager.close()
        logging.info("Database migration completed successfully")
    except Exception as e:
        logging.error(f"Database migration failed: {e}")


def main():
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("PDF Library Manager")
    app.setApplicationVersion("1.0.0")

    splash_pixmap = QPixmap(300, 200)
    splash_pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(splash_pixmap)
    splash.showMessage(
        "起動中...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
    )
    splash.show()

    app.processEvents()

    icon_path = os.path.join(
        os.path.dirname(__file__), "resources", "icons", "app_icon.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash.showMessage(
        "設定を読み込み中...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
    )
    app.processEvents()

    settings = load_settings()

    db_path = settings["paths"]["database_path"]

    if not db_path or os.path.dirname(db_path) == "":
        db_path = str(get_app_data_dir() / "library.db")
        settings["paths"]["database_path"] = db_path
        logging.warning(f"Invalid database path detected, using default: {db_path}")

        try:
            settings_path = get_app_data_dir() / "settings.json"
            os.makedirs(os.path.dirname(str(settings_path)), exist_ok=True)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    perform_db_migration(db_path, splash)

    splash.showMessage(
        "ライブラリインターフェースを初期化中...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
    )
    app.processEvents()

    window = MainWindow(db_path, splash)

    QTimer.singleShot(1500, lambda: window.show())

    QTimer.singleShot(1500, lambda: splash.finish(window))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
