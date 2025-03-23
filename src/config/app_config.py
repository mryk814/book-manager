import os
from pathlib import Path

from config.settings_manager import SettingsManager


class AppConfig:
    _instance = None

    def __new__(cls, app_data_dir=None):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, app_data_dir=None):
        if self._initialized:
            return

        # 設定マネージャーを作成
        self.settings_manager = SettingsManager(app_data_dir)
        self.app_data_dir = self.settings_manager.app_data_dir

        # デフォルト設定
        self.default_settings = {
            "general": {
                "startup_show_last_book": True,
                "confirm_delete": True,
            },
            "appearance": {
                "grid_columns": 4,
                "grid_cover_size": 150,
                "list_cover_size": 48,
                "default_view": "grid",
            },
            "paths": {
                "default_import_path": "",
                "database_path": str(self.app_data_dir / "library.db"),
            },
            "reading": {
                "default_zoom": 100,
                "page_turn_mode": "continuous",
            },
        }

        self.settings = self.settings_manager.load_settings(self.default_settings)

        self._initialized = True

    def save_settings(self):
        return self.settings_manager.save_settings(self.settings)

    def get(self, section, key, default=None):
        return self.settings.get(section, {}).get(key, default)

    def set(self, section, key, value):
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value

    def get_database_path(self):
        db_path = self.get("paths", "database_path")

        if not db_path or os.path.dirname(db_path) == "":
            db_path = str(self.app_data_dir / "library.db")
            self.set("paths", "database_path", db_path)
            self.save_settings()

        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        return db_path
