class AppTheme:
    """
    アプリケーションのカラーテーマを管理するクラス。
    色は全てここで一元管理し、名前付き定数としてアクセスできるようにする。
    """

    # 基本カラー
    PRIMARY = "#4a6ea9"  # 濃い青色（メインカラー）
    PRIMARY_LIGHT = "#6d8fc6"  # 明るい青色
    PRIMARY_DARK = "#2c4d7c"  # 暗い青色

    SECONDARY = "#5b9e7a"  # 緑色（アクセントカラー）
    SECONDARY_LIGHT = "#7db598"  # 明るい緑色
    SECONDARY_DARK = "#3d7c5c"  # 暗い緑色

    # ステータスカラー
    SUCCESS = "#4caf50"  # 緑色（成功）
    WARNING = "#ff9800"  # オレンジ色（警告）
    ERROR = "#f44336"  # 赤色（エラー）
    INFO = "#2196f3"  # 青色（情報）

    # 読書状態カラー
    STATUS_UNREAD = "#9e9e9e"  # グレー
    STATUS_READING = "#1976d2"  # 青色
    STATUS_COMPLETED = "#43a047"  # 緑色

    # テキストカラー
    TEXT_PRIMARY = "#212121"  # 黒に近いグレー
    TEXT_SECONDARY = "#757575"  # 薄めのグレー

    # 背景カラー
    BACKGROUND_MAIN = "#ffffff"  # 白
    BACKGROUND_ALT = "#f5f5f5"  # 薄いグレー

    # UI要素カラー
    SURFACE = "#ffffff"  # 白（カード、ダイアログなど）
    DIVIDER = "#e0e0e0"  # 薄いグレー（区切り線）

    # 選択状態カラー
    SELECTION_BACKGROUND = "#e3f2fd"  # 淡い青色の背景
    SELECTION_BORDER = "#2196f3"  # 青色のボーダー

    # 項目カラー
    ITEM_HOVER = "#f5f5f5"  # 薄いグレー（ホバー時）
    ITEM_SELECTED = "#e8f0fe"  # 薄い青色（選択時）

    # プレースホルダーカラー
    PLACEHOLDER_BACKGROUND = "#f0f0f0"  # 薄いグレー

    @classmethod
    def get_reading_status_color(cls, status):
        """
        読書状態に応じた色を返す。

        Parameters
        ----------
        status : str
            読書状態 ('unread', 'reading', 'completed')

        Returns
        -------
        str
            色のCSSコード
        """
        if status == "unread":
            return cls.STATUS_UNREAD
        elif status == "reading":
            return cls.STATUS_READING
        elif status == "completed":
            return cls.STATUS_COMPLETED
        return cls.TEXT_PRIMARY
