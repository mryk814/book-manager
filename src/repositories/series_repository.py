from repositories.base_repository import BaseRepository


class SeriesRepository(BaseRepository):
    """
    シリーズのデータアクセスを管理するリポジトリクラス。

    Parameters
    ----------
    db_manager : DatabaseManager
        データベースマネージャーのインスタンス
    """

    def get_all(self, category_id=None):
        """
        すべてのシリーズを取得する。オプションでカテゴリでフィルタリング。

        Parameters
        ----------
        category_id : int, optional
            特定のカテゴリに属するシリーズのみを取得する場合のID

        Returns
        -------
        list
            シリーズ情報の辞書のリスト
        """
        sql = """
        SELECT s.*, c.name as category_name
        FROM series s
        LEFT JOIN categories c ON s.category_id = c.id
        """

        params = []
        if category_id:
            sql += " WHERE s.category_id = ?"
            params.append(category_id)

        sql += " ORDER BY s.name"

        return self.execute_query(sql, params)

    def get_by_id(self, series_id):
        """
        指定IDのシリーズを取得する。

        Parameters
        ----------
        series_id : int
            取得するシリーズのID

        Returns
        -------
        dict または None
            シリーズデータの辞書、もしくは見つからない場合はNone
        """
        sql = """
        SELECT s.*, c.name as category_name
        FROM series s
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE s.id = ?
        """

        results = self.execute_query(sql, (series_id,))
        return results[0] if results else None

    def create(self, data):
        """
        新しいシリーズを作成する。

        Parameters
        ----------
        data : dict
            シリーズデータ

        Returns
        -------
        int または None
            作成されたシリーズのID、もしくは失敗した場合はNone
        """
        sql = """
        INSERT INTO series (name, description, category_id)
        VALUES (?, ?, ?)
        """

        params = (data.get("name"), data.get("description"), data.get("category_id"))

        try:
            return self.execute_insert(sql, params)
        except Exception as e:
            print(f"Error creating series: {e}")
            return None

    def update(self, series_id, data):
        """
        シリーズを更新する。

        Parameters
        ----------
        series_id : int
            更新するシリーズのID
        data : dict
            更新するデータ

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        allowed_fields = {"name", "description", "category_id"}
        update_fields = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_fields:
            return False

        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [series_id]

        sql = f"""
        UPDATE series 
        SET {set_clause}
        WHERE id = ?
        """

        try:
            rows_affected = self.execute_update(sql, values)
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating series: {e}")
            return False

    def delete(self, series_id):
        """
        シリーズを削除する。

        Parameters
        ----------
        series_id : int
            削除するシリーズのID

        Returns
        -------
        bool
            削除が成功したかどうか
        """
        try:
            # カスタムメタデータを削除
            self.execute_update(
                "DELETE FROM custom_metadata WHERE series_id = ?", (series_id,)
            )

            # シリーズを削除
            rows_affected = self.execute_update(
                "DELETE FROM series WHERE id = ?", (series_id,)
            )

            return rows_affected > 0
        except Exception as e:
            print(f"Error deleting series: {e}")
            return False

    def get_books_in_series(self, series_id):
        """
        指定したシリーズに属する書籍のリストを取得する。

        Parameters
        ----------
        series_id : int
            シリーズのID

        Returns
        -------
        list
            書籍情報の辞書のリスト
        """
        sql = """
        SELECT b.*, rp.status, rp.current_page, rp.total_pages
        FROM books b
        LEFT JOIN reading_progress rp ON b.id = rp.book_id
        WHERE b.series_id = ?
        ORDER BY b.series_order, b.title COLLATE NOCASE
        """

        return self.execute_query(sql, (series_id,))

    def get_custom_metadata(self, series_id):
        """
        シリーズのカスタムメタデータを取得する。

        Parameters
        ----------
        series_id : int
            シリーズのID

        Returns
        -------
        dict
            キーと値のペアとしてのメタデータ
        """
        sql = """
        SELECT key, value FROM custom_metadata
        WHERE series_id = ?
        """

        result = self.execute_query(sql, (series_id,))
        return {row["key"]: row["value"] for row in result}

    def set_custom_metadata(self, series_id, key, value):
        """
        シリーズのカスタムメタデータを設定する。

        Parameters
        ----------
        series_id : int
            シリーズのID
        key : str
            メタデータのキー
        value : str
            メタデータの値

        Returns
        -------
        bool
            設定が成功したかどうか
        """
        # 既存のエントリを確認
        sql = """
        SELECT id FROM custom_metadata
        WHERE series_id = ? AND key = ?
        """

        result = self.execute_query(sql, (series_id, key))

        try:
            if result:
                # 更新
                update_sql = """
                UPDATE custom_metadata
                SET value = ?
                WHERE series_id = ? AND key = ?
                """
                self.execute_update(update_sql, (value, series_id, key))
            else:
                # 新規追加
                insert_sql = """
                INSERT INTO custom_metadata (series_id, key, value)
                VALUES (?, ?, ?)
                """
                self.execute_insert(insert_sql, (series_id, key, value))

            return True
        except Exception as e:
            print(f"Error setting custom metadata: {e}")
            return False

    def reorder_books(self, order_mapping):
        """
        シリーズ内の書籍の順序を変更する。

        Parameters
        ----------
        order_mapping : dict
            book_id: new_order の形式の辞書

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        success = True

        for book_id, new_order in order_mapping.items():
            sql = """
            UPDATE books
            SET series_order = ?
            WHERE id = ?
            """
            try:
                self.execute_update(sql, (new_order, book_id))
            except Exception as e:
                print(f"Error updating book order: {e}")
                success = False

        return success
