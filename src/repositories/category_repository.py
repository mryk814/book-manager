from repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):
    """
    カテゴリのデータアクセスを管理するリポジトリクラス。

    Parameters
    ----------
    db_manager : DatabaseManager
        データベースマネージャーのインスタンス
    """

    def get_all(self):
        """
        すべてのカテゴリを取得する。

        Returns
        -------
        list
            カテゴリ情報の辞書のリスト
        """
        sql = "SELECT * FROM categories ORDER BY name"
        return self.execute_query(sql)

    def get_by_id(self, category_id):
        """
        指定IDのカテゴリを取得する。

        Parameters
        ----------
        category_id : int
            取得するカテゴリのID

        Returns
        -------
        dict または None
            カテゴリデータの辞書、もしくは見つからない場合はNone
        """
        if not category_id:
            return None

        sql = "SELECT * FROM categories WHERE id = ?"
        results = self.execute_query(sql, (category_id,))
        return results[0] if results else None

    def create(self, name, description=None):
        """
        新しいカテゴリを作成する。

        Parameters
        ----------
        name : str
            カテゴリ名
        description : str, optional
            カテゴリの説明

        Returns
        -------
        int または None
            作成されたカテゴリのID、もしくは失敗した場合はNone
        """
        sql = """
        INSERT INTO categories (name, description)
        VALUES (?, ?)
        """

        try:
            return self.execute_insert(sql, (name, description))
        except Exception as e:
            print(f"Error creating category: {e}")
            return None

    def update(self, category_id, name, description=None):
        """
        カテゴリを更新する。

        Parameters
        ----------
        category_id : int
            更新するカテゴリのID
        name : str
            カテゴリ名
        description : str, optional
            カテゴリの説明

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        sql = """
        UPDATE categories
        SET name = ?, description = ?
        WHERE id = ?
        """

        try:
            rows_affected = self.execute_update(sql, (name, description, category_id))
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating category: {e}")
            return False

    def delete(self, category_id):
        """
        カテゴリを削除する。

        Parameters
        ----------
        category_id : int
            削除するカテゴリのID

        Returns
        -------
        bool
            削除が成功したかどうか
        """
        try:
            # トランザクション開始
            conn = self.connect()
            conn.begin()

            # カテゴリに所属するシリーズのカテゴリIDをNULLに設定
            self.execute_update(
                """
                UPDATE series
                SET category_id = NULL
                WHERE category_id = ?
                """,
                (category_id,),
            )

            # カテゴリに所属する書籍のカテゴリIDをNULLに設定
            self.execute_update(
                """
                UPDATE books
                SET category_id = NULL
                WHERE category_id = ?
                """,
                (category_id,),
            )

            # カテゴリを削除
            rows_affected = self.execute_update(
                "DELETE FROM categories WHERE id = ?", (category_id,)
            )

            # トランザクション確定
            conn.commit()
            return rows_affected > 0

        except Exception as e:
            # エラー時はロールバック
            conn.rollback()
            print(f"Error deleting category: {e}")
            return False

    def get_with_counts(self):
        """
        各カテゴリに含まれる書籍数とシリーズ数を含めて取得する。

        Returns
        -------
        list
            拡張したカテゴリ情報の辞書のリスト
        """
        sql = """
            SELECT c.id, c.name, c.description,
                   COUNT(DISTINCT b.id) as book_count,
                   COUNT(DISTINCT s.id) as series_count
            FROM categories c
            LEFT JOIN books b ON b.category_id = c.id
            LEFT JOIN series s ON s.category_id = c.id
            GROUP BY c.id
            ORDER BY c.name
        """

        return self.execute_query(sql)
