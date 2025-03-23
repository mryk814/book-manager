import os
from pathlib import Path

from config.settings_manager import SettingsManager


class AppConfig:
    """
    アプリケーション設定を管理するクラス。

    設定の読み込み、保存、アクセスなどの機能を提供する。
    シングルトンパターンを使用して、アプリケーション全体で一貫した設定管理を行う。
    内部的には SettingsManager クラスを利用して設定の保存・読み込みを行う。

    Parameters
    ----------
    app_data_dir : str, optional
        設定ファイルを保存するディレクトリ
        指定しない場合はデフォルトのアプリデータディレクトリを使用
    """

    # シングルトンインスタンス
    _instance = None

    def __new__(cls, app_data_dir=None):
        """シングルトンパターンでインスタンスを生成"""
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, app_data_dir=None):
        """
        Parameters
        ----------
        app_data_dir : str, optional
            設定ファイルを保存するディレクトリ
            指定しない場合はデフォルトのアプリデータディレクトリを使用
        """
        # 初期化済みの場合は何もしない（シングルトン用）
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
                "default_view": "grid",  # or "list"
            },
            "paths": {
                "default_import_path": "",
                "database_path": str(self.app_data_dir / "library.db"),
            },
            "reading": {
                "default_zoom": 100,  # パーセント
                "page_turn_mode": "continuous",  # or "single"
            },
        }

        # 設定を読み込む
        self.settings = self.settings_manager.load_settings(self.default_settings)

        # 初期化完了フラグ
        self._initialized = True

    def save_settings(self):
        """設定をファイルに保存する。"""
        return self.settings_manager.save_settings(self.settings)

    def get(self, section, key, default=None):
        """
        設定値を取得する。

        Parameters
        ----------
        section : str
            設定セクション名
        key : str
            設定キー名
        default : any, optional
            設定が存在しない場合のデフォルト値

        Returns
        -------
        any
            設定値
        """
        return self.settings.get(section, {}).get(key, default)

    def set(self, section, key, value):
        """
        設定値を設定する。

        Parameters
        ----------
        section : str
            設定セクション名
        key : str
            設定キー名
        value : any
            設定値
        """
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value

    def get_database_path(self):
        """
        データベースファイルのパスを取得する。

        Returns
        -------
        str
            データベースファイルのパス
        """
        db_path = self.get("paths", "database_path")

        # パスが空か無効な場合はデフォルトのパスを設定
        if not db_path or os.path.dirname(db_path) == "":
            db_path = str(self.app_data_dir / "library.db")
            self.set("paths", "database_path", db_path)
            self.save_settings()

        # データベースディレクトリを作成
        db_dir = os.path.dirname(db_path)
        if db_dir:  # ディレクトリパスが空でない場合のみ作成
            os.makedirs(db_dir, exist_ok=True)

        return db_path
