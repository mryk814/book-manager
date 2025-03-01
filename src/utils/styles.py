from utils.theme import AppTheme


class StyleSheets:
    """
    アプリケーション全体で使用するスタイルシートを集中管理するクラス。
    """

    # メインウィンドウのスタイル
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {AppTheme.BACKGROUND_MAIN};
        }}
    """

    # ツールバーのスタイル
    TOOLBAR = f"""
        QToolBar {{
            background-color: {AppTheme.BACKGROUND_ALT};
            border-bottom: 1px solid {AppTheme.DIVIDER};
            spacing: 5px;
            padding: 2px;
        }}
        
        QToolBar QLabel {{
            margin-left: 5px;
        }}
    """

    # ステータスバーのスタイル
    STATUSBAR = f"""
        QStatusBar {{
            background-color: {AppTheme.BACKGROUND_ALT};
            border-top: 1px solid {AppTheme.DIVIDER};
        }}
    """

    # リストアイテムのスタイル
    LIST_ITEM = f"""
        QListWidget::item {{
            border-bottom: 1px solid {AppTheme.DIVIDER};
            padding: 5px;
        }}
        
        QListWidget::item:selected {{
            background-color: {AppTheme.ITEM_SELECTED};
            border: none;
        }}
        
        QListWidget::item:hover {{
            background-color: {AppTheme.ITEM_HOVER};
        }}
    """

    # グリッドアイテムのスタイル
    GRID_ITEM_BASE = f"""
        background-color: {AppTheme.SURFACE};
        border-radius: 4px;
        padding: 8px;
    """

    GRID_ITEM_SELECTED = f"""
        background-color: {AppTheme.SELECTION_BACKGROUND};
        border: 1px solid {AppTheme.SELECTION_BORDER};
    """

    # プレースホルダーのスタイル
    PLACEHOLDER = f"""
        background-color: {AppTheme.PLACEHOLDER_BACKGROUND};
        border: 1px solid {AppTheme.DIVIDER};
        color: {AppTheme.TEXT_SECONDARY};
        border-radius: 4px;
        font-style: italic;
    """

    # 読書状態のスタイル
    @staticmethod
    def reading_status_style(status):
        color = AppTheme.get_reading_status_color(status)
        return f"color: {color}; font-weight: bold;"

    # カテゴリバッジのスタイル
    CATEGORY_BADGE = f"""
        background-color: {AppTheme.SECONDARY_LIGHT};
        color: white;
        border-radius: 10px;
        padding: 3px 8px;
        font-size: 12px;
    """

    # シリーズバッジのスタイル
    SERIES_BADGE = f"""
        background-color: {AppTheme.PRIMARY_LIGHT};
        color: white;
        border-radius: 10px;
        padding: 3px 8px;
        font-size: 12px;
    """

    # プログレスバーのスタイル
    PROGRESS_BAR = f"""
        QProgressBar {{
            border: 1px solid {AppTheme.DIVIDER};
            border-radius: 5px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {AppTheme.PRIMARY};
            width: 1px;
        }}
    """

    # ボタンのスタイル
    BUTTON = f"""
        QPushButton {{
            background-color: {AppTheme.PRIMARY};
            color: white;
            border-radius: 4px;
            padding: 6px 12px;
            border: none;
        }}
        
        QPushButton:hover {{
            background-color: {AppTheme.PRIMARY_LIGHT};
        }}
        
        QPushButton:pressed {{
            background-color: {AppTheme.PRIMARY_DARK};
        }}
        
        QPushButton:disabled {{
            background-color: {AppTheme.DIVIDER};
            color: {AppTheme.TEXT_SECONDARY};
        }}
    """

    # セカンダリボタンのスタイル
    SECONDARY_BUTTON = f"""
        QPushButton {{
            background-color: white;
            color: {AppTheme.PRIMARY};
            border: 1px solid {AppTheme.PRIMARY};
            border-radius: 4px;
            padding: 6px 12px;
        }}
        
        QPushButton:hover {{
            background-color: {AppTheme.SELECTION_BACKGROUND};
        }}
        
        QPushButton:pressed {{
            background-color: {AppTheme.ITEM_SELECTED};
        }}
        
        QPushButton:disabled {{
            border-color: {AppTheme.DIVIDER};
            color: {AppTheme.TEXT_SECONDARY};
        }}
    """
