import json
import logging
import os
from pathlib import Path


class Config:
    """アプリケーション設定を管理するクラス"""

    # デフォルト設定
    DEFAULT_CONFIG = {
        "app_name": "PDF Library",
        "version": "1.0.0",
        "db_path": "",
        "library_paths": [],
        "thumbnail_dir": "",
        "last_open_book": None,
        "ui": {
            "theme": "light",  # light, dark
            "default_view": "grid",  # grid, list, bookshelf
            "thumbnail_size": "medium",  # small, medium, large
            "sort_field": "title",
            "sort_direction": "asc",
        },
        "viewer": {
            "page_turn_mode": "single",  # single, double
            "zoom_level": 1.0,
            "remember_last_page": True,
            "manga_mode": False,  # 右から左への表示
        },
        "scan_options": {
            "scan_on_startup": True,
            "watch_directories": False,
            "auto_import": True,
        },
    }

    def __init__(self, config_dir=None):
        """
        設定の初期化

        Args:
            config_dir (str): 設定ディレクトリのパス
        """
        # 設定ディレクトリの設定
        if config_dir is None:
            home_dir = str(Path.home())
            self.config_dir = os.path.join(home_dir, ".pdf_library")
        else:
            self.config_dir = config_dir

        # 設定ファイルのパス
        self.config_file = os.path.join(self.config_dir, "config.json")

        # ディレクトリが存在しない場合は作成
        os.makedirs(self.config_dir, exist_ok=True)

        # 設定の読み込み
        self.settings = self.load_config()

        # データベースとサムネイルのパスを設定
        if not self.settings["db_path"]:
            self.settings["db_path"] = os.path.join(self.config_dir, "library.db")

        if not self.settings["thumbnail_dir"]:
            self.settings["thumbnail_dir"] = os.path.join(self.config_dir, "thumbnails")
            os.makedirs(self.settings["thumbnail_dir"], exist_ok=True)

        # 設定を保存
        self.save_config()

    def load_config(self):
        """
        設定ファイルを読み込む

        Returns:
            dict: 設定内容
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                # デフォルト設定とマージ (不足している設定を補完)
                merged_settings = self.DEFAULT_CONFIG.copy()
                self._deep_update(merged_settings, settings)
                return merged_settings
            else:
                logging.info(
                    "設定ファイルが見つからないため、デフォルト設定を使用します"
                )
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"設定ファイルの読み込みエラー: {e}")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """設定をファイルに保存"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            logging.info("設定を保存しました")
        except Exception as e:
            logging.error(f"設定ファイルの保存エラー: {e}")

    def get(self, key, default=None):
        """
        設定値を取得

        Args:
            key (str): 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        # キーが階層化されている場合（"ui.theme"など）
        if "." in key:
            parts = key.split(".")
            value = self.settings
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            return self.settings.get(key, default)

    def set(self, key, value):
        """
        設定値を設定

        Args:
            key (str): 設定キー
            value: 設定値
        """
        # キーが階層化されている場合（"ui.theme"など）
        if "." in key:
            parts = key.split(".")
            target = self.settings
            for part in parts[:-1]:  # 最後の部分以外
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        else:
            self.settings[key] = value

        # 設定を保存
        self.save_config()

    def add_library_path(self, path):
        """
        ライブラリパスを追加

        Args:
            path (str): 追加するパス

        Returns:
            bool: 追加成功の場合True
        """
        if path and os.path.exists(path) and path not in self.settings["library_paths"]:
            self.settings["library_paths"].append(path)
            self.save_config()
            return True
        return False

    def remove_library_path(self, path):
        """
        ライブラリパスを削除

        Args:
            path (str): 削除するパス

        Returns:
            bool: 削除成功の場合True
        """
        if path in self.settings["library_paths"]:
            self.settings["library_paths"].remove(path)
            self.save_config()
            return True
        return False

    def get_all_library_paths(self):
        """
        全てのライブラリパスを取得

        Returns:
            list: ライブラリパスのリスト
        """
        return self.settings["library_paths"]

    def _deep_update(self, target, source):
        """
        辞書を再帰的に更新するヘルパーメソッド

        Args:
            target (dict): 更新対象辞書
            source (dict): 更新元辞書
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(target[key], value)
            else:
                target[key] = value
