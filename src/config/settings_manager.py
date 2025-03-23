import json
import os
from pathlib import Path


class SettingsManager:
    def __init__(self, app_data_dir=None):
        self.app_data_dir = app_data_dir or self.get_default_app_data_dir()

    @staticmethod
    def get_default_app_data_dir():
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
        return self.app_data_dir / "settings.json"

    def load_settings(self, default_settings):
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
                    merged_settings = default_settings.copy()
                    self.merge_settings(merged_settings, loaded_settings)
                    return merged_settings
            except Exception as e:
                print(f"Error loading settings: {e}")

        return default_settings.copy()

    def save_settings(self, settings):
        settings_path = self.get_settings_path()

        try:
            # 設定ディレクトリを作成
            os.makedirs(os.path.dirname(str(settings_path)), exist_ok=True)

            # 設定を保存
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)

            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def merge_settings(self, target, source):
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
            else:
                # ターゲットに存在しないキーも追加
                target[key] = value
