class BaseRepository:
    """
    リポジトリの基底クラス。

    データアクセスロジックの共通部分を提供する。

    Parameters
    ----------
    db_manager : DatabaseManager
        データベースマネージャーのインスタンス
    """

    def __init__(self, db_manager):
        """
        Parameters
        ----------
        db_manager : DatabaseManager
            データベース接続マネージャ
        """
        self.db_manager = db_manager

    def connect(self):
        """
        データベース接続を取得する。

        Returns
        -------
        sqlite3.Connection
            データベース接続オブジェクト
        """
        return self.db_manager.connect()

    def execute_query(self, query, params=None):
        """
        SQL文を実行する。

        Parameters
        ----------
        query : str
            実行するSQL文
        params : tuple または list または dict, optional
            SQLパラメータ

        Returns
        -------
        list
            クエリ結果の辞書のリスト
        """
        if params is None:
            params = []

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)

        result = [dict(row) for row in cursor.fetchall()]
        return result

    def execute_update(self, query, params=None):
        """
        データを更新するSQL文を実行する。

        Parameters
        ----------
        query : str
            実行するSQL文
        params : tuple または list または dict, optional
            SQLパラメータ

        Returns
        -------
        int
            更新された行数
        """
        if params is None:
            params = []

        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e

    def execute_insert(self, query, params=None):
        """
        データを挿入するSQL文を実行する。

        Parameters
        ----------
        query : str
            実行するSQL文
        params : tuple または list または dict, optional
            SQLパラメータ

        Returns
        -------
        int
            挿入された行のID
        """
        if params is None:
            params = []

        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
