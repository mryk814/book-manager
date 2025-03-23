class AppTheme:
    """
    アプリケーションのカラーテーマを管理するクラス。
    色は全てここで一元管理し、名前付き定数としてアクセスできるようにする。
    """

    PRIMARY = "#4a6ea9"
    PRIMARY_LIGHT = "#6d8fc6"
    PRIMARY_DARK = "#2c4d7c"

    SECONDARY = "#5b9e7a"
    SECONDARY_LIGHT = "#7db598"
    SECONDARY_DARK = "#3d7c5c"

    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    INFO = "#2196f3"

    STATUS_UNREAD = "#9e9e9e"
    STATUS_READING = "#1976d2"
    STATUS_COMPLETED = "#43a047"

    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"

    BACKGROUND_MAIN = "#ffffff"
    BACKGROUND_ALT = "#f5f5f5"

    SURFACE = "#ffffff"
    DIVIDER = "#e0e0e0"

    SELECTION_BACKGROUND = "#e3f2fd"
    SELECTION_BORDER = "#2196f3"

    ITEM_HOVER = "#f5f5f5"
    ITEM_SELECTED = "#e8f0fe"

    PLACEHOLDER_BACKGROUND = "#f0f0f0"

    @classmethod
    def get_reading_status_color(cls, status):
        if status == "unread":
            return cls.STATUS_UNREAD
        elif status == "reading":
            return cls.STATUS_READING
        elif status == "completed":
            return cls.STATUS_COMPLETED
        return cls.TEXT_PRIMARY
