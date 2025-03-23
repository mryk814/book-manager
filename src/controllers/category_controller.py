class CategoryController:
    """
    カテゴリに関連する操作を管理するコントローラクラス。

    カテゴリの取得、作成、更新、削除などの機能を提供する。

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

    def get_all_categories(self):
        """
        すべてのカテゴリを取得する。

        Returns
        -------
        list
            カテゴリ情報の辞書のリスト
        """
        return self.db_manager.get_all_categories()

    def get_category(self, category_id):
        """
        指定したIDのカテゴリ情報を取得する。

        Parameters
        ----------
        category_id : int
            取得するカテゴリのID

        Returns
        -------
        dict または None
            カテゴリ情報の辞書、もしくは見つからない場合はNone
        """
        return self.db_manager.get_category(category_id)

    def create_category(self, name, description=None):
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
            追加されたカテゴリのID、もしくは失敗した場合はNone
        """
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO categories (name, description)
                VALUES (?, ?)
                """,
                (name, description),
            )

            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating category: {e}")
            conn.rollback()
            return None

    def update_category(self, category_id, name, description=None):
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
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE categories
                SET name = ?, description = ?
                WHERE id = ?
                """,
                (name, description, category_id),
            )

            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating category: {e}")
            conn.rollback()
            return False

    def delete_category(self, category_id):
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
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            # カテゴリに所属するシリーズのカテゴリIDをNULLに設定
            cursor.execute(
                """
                UPDATE series
                SET category_id = NULL
                WHERE category_id = ?
                """,
                (category_id,),
            )

            # カテゴリに所属する書籍のカテゴリIDをNULLに設定
            cursor.execute(
                """
                UPDATE books
                SET category_id = NULL
                WHERE category_id = ?
                """,
                (category_id,),
            )

            # カテゴリを削除
            cursor.execute(
                """
                DELETE FROM categories
                WHERE id = ?
                """,
                (category_id,),
            )

            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            conn.rollback()
            return False

    def get_categories_with_counts(self):
        """
        各カテゴリに含まれる書籍数とシリーズ数を含めて取得する。

        Returns
        -------
        list
            拡張したカテゴリ情報の辞書のリスト
        """
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        # カテゴリごとの書籍数を取得
        cursor.execute("""
            SELECT c.id, c.name, c.description,
                   COUNT(DISTINCT b.id) as book_count,
                   COUNT(DISTINCT s.id) as series_count
            FROM categories c
            LEFT JOIN books b ON b.category_id = c.id
            LEFT JOIN series s ON s.category_id = c.id
            GROUP BY c.id
            ORDER BY c.name
        """)

        categories = []
        for row in cursor.fetchall():
            categories.append(dict(row))

        return categories
