class BaseRepository:
    """
    リポジトリの基底クラス。

    データアクセスロジックの共通部分を提供する。
    すべてのリポジトリクラスはこのクラスを継承する。

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

    def execute_delete(self, query, params=None):
        """
        データを削除するSQL文を実行する。

        Parameters
        ----------
        query : str
            実行するSQL文
        params : tuple または list または dict, optional
            SQLパラメータ

        Returns
        -------
        int
            削除された行数
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

    def execute_transaction(self, operations):
        """
        複数のSQL操作をトランザクションとして実行する。

        Parameters
        ----------
        operations : list of tuples
            (query, params) のタプルのリスト

        Returns
        -------
        bool
            すべての操作が成功したかどうか
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            for query, params in operations:
                cursor.execute(query, params or [])

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e

    def get_by_id(self, table, id_field, id_value):
        """
        特定のIDのレコードを取得する汎用メソッド。

        Parameters
        ----------
        table : str
            テーブル名
        id_field : str
            ID列の名前
        id_value : int
            検索するID値

        Returns
        -------
        dict または None
            レコードデータの辞書、もしくは見つからない場合はNone
        """
        query = f"SELECT * FROM {table} WHERE {id_field} = ?"
        results = self.execute_query(query, (id_value,))
        return results[0] if results else None

    def get_all(self, table, where_clause=None, params=None, order_by=None):
        """
        条件に一致するすべてのレコードを取得する汎用メソッド。

        Parameters
        ----------
        table : str
            テーブル名
        where_clause : str, optional
            WHERE句（"WHERE"キーワードは除く）
        params : tuple または list, optional
            SQLパラメータ
        order_by : str, optional
            ORDER BY句（"ORDER BY"キーワードは除く）

        Returns
        -------
        list
            レコードデータの辞書のリスト
        """
        query = f"SELECT * FROM {table}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        return self.execute_query(query, params)
