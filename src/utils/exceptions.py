class ApplicationError(Exception):
    """アプリケーション全般のエラーの基底クラス"""

    pass


class DatabaseError(ApplicationError):
    """データベース関連のエラー"""

    pass


class FileOperationError(ApplicationError):
    """ファイル操作に関するエラー"""

    pass


class UIError(ApplicationError):
    """ユーザーインターフェース関連のエラー"""

    pass
