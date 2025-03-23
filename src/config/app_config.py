import json
import os
from pathlib import Path


class AppConfig:
    """
    アプリケーション設定を管理するクラス。

    設定の読み込み、保存、アクセスなどの機能を提供する。
    シングルトンパターンを使用して、アプリケーション全体で一貫した設定管理を行う。
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

        # アプリデータディレクトリ
        self.app_data_dir = app_data_dir or self.get_default_app_data_dir()

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
        self.settings = self.load_settings()

        # 初期化完了フラグ
        self._initialized = True

    @staticmethod
    def get_default_app_data_dir():
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
            if os.path.exists(
                os.path.expanduser("~/Library/Application Support")
            ):  # macOS
                return (
                    Path(os.path.expanduser("~/Library/Application Support")) / app_name
                )
            else:  # Linux
                return Path(os.path.expanduser("~/.config")) / app_name
        else:
            # その他のOSはカレントディレクトリに
            return Path(os.getcwd()) / f".{app_name}"

    def get_settings_path(self):
        """
        設定ファイルのパスを取得する。

        Returns
        -------
        Path
            設定ファイルのパス
        """
        return self.app_data_dir / "settings.json"

    def load_settings(self):
        """
        設定ファイルから設定を読み込む。

        Returns
        -------
        dict
            設定の辞書
        """
        settings_path = self.get_settings_path()

        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)

                    # データベースパスの検証
                    db_path = loaded_settings.get("paths", {}).get("database_path", "")
                    if not db_path or not os.path.dirname(db_path):
                        loaded_settings.setdefault("paths", {})["database_path"] = str(
                            self.app_data_dir / "library.db"
                        )
                        print(f"Invalid database path in settings, using default")

                    # デフォルト設定と結合（欠けている設定をデフォルトで補完）
                    merged_settings = self.default_settings.copy()
                    self.merge_settings(merged_settings, loaded_settings)
                    return merged_settings
            except Exception as e:
                print(f"Error loading settings: {e}")

        return self.default_settings.copy()

    def save_settings(self):
        """設定をファイルに保存する。"""
        settings_path = self.get_settings_path()

        try:
            # 設定ディレクトリを作成
            os.makedirs(os.path.dirname(str(settings_path)), exist_ok=True)

            # 設定を保存
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)

            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def merge_settings(self, target, source):
        """
        設定を再帰的にマージする。

        Parameters
        ----------
        target : dict
            ターゲット辞書（更新される）
        source : dict
            ソース辞書（更新内容）
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                # 両方辞書の場合は再帰的にマージ
                self.merge_settings(target[key], value)
            elif key in target:
                # その他の場合は上書き
                target[key] = value

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
