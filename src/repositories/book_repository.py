import re

from repositories.base_repository import BaseRepository


class BookRepository(BaseRepository):
    """
    書籍のデータアクセスを管理するリポジトリクラス。

    Parameters
    ----------
    db_manager : DatabaseManager
        データベースマネージャーのインスタンス
    """

    def get_all(self, category_id=None, series_id=None, status=None):
        """
        条件に合う書籍リストを取得する。

        Parameters
        ----------
        category_id : int, optional
            特定のカテゴリに属する書籍のみを取得
        series_id : int, optional
            特定のシリーズに属する書籍のみを取得
        status : str, optional
            特定の読書状態の書籍のみを取得

        Returns
        -------
        list
            書籍データの辞書のリスト
        """
        query_params = {}
        params = []

        sql = """
            SELECT b.*, rp.current_page, rp.total_pages, rp.status, rp.last_read_date,
                   s.name as series_name, c.name as category_name
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            LEFT JOIN series s ON b.series_id = s.id
            LEFT JOIN categories c ON (b.category_id = c.id OR s.category_id = c.id)
            WHERE 1=1
        """

        if status:
            sql += " AND rp.status = ?"
            params.append(status)

        if series_id:
            sql += " AND b.series_id = ?"
            params.append(series_id)

        if category_id:
            sql += " AND (b.category_id = ? OR s.category_id = ?)"
            params.append(category_id)
            params.append(category_id)

        # タイトルでソート（自然順）
        sql += " ORDER BY b.title COLLATE NOCASE"

        return self.execute_query(sql, params)

    def get_by_id(self, book_id):
        """
        指定IDの書籍を取得する。

        Parameters
        ----------
        book_id : int
            取得する書籍のID

        Returns
        -------
        dict または None
            書籍データの辞書、もしくは見つからない場合はNone
        """
        sql = """
            SELECT b.*, rp.current_page, rp.total_pages, rp.status, rp.last_read_date
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            WHERE b.id = ?
        """

        results = self.execute_query(sql, (book_id,))
        return results[0] if results else None

    def search(self, query=None, **kwargs):
        """
        書籍を検索する。

        Parameters
        ----------
        query : str, optional
            検索クエリ
        **kwargs
            追加の検索条件

        Returns
        -------
        list
            書籍データの辞書のリスト
        """
        sql = """
            SELECT b.*, rp.status, rp.current_page, rp.total_pages, s.name as series_name
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            LEFT JOIN series s ON b.series_id = s.id
            LEFT JOIN categories c ON s.category_id = c.id
            WHERE 1=1
        """

        params = []

        if query:
            sql += """
            AND (b.title LIKE ? OR b.author LIKE ? OR b.publisher LIKE ?)
            """
            query_param = f"%{query}%"
            params.extend([query_param, query_param, query_param])

        # 追加の検索条件を適用
        for key, value in kwargs.items():
            if key == "category_id" and value:
                sql += " AND c.id = ?"
                params.append(value)
            elif key == "status" and value:
                sql += " AND rp.status = ?"
                params.append(value)

        # タイトルで自然順ソート
        sql += " ORDER BY b.title COLLATE NOCASE"

        return self.execute_query(sql, params)

    def create(self, data):
        """
        新しい書籍を作成する。

        Parameters
        ----------
        data : dict
            書籍データ

        Returns
        -------
        int または None
            作成された書籍のID、もしくは失敗した場合はNone
        """
        sql = """
            INSERT INTO books (
                title, file_path, series_id, series_order, category_id, author, publisher, cover_image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            data.get("title"),
            data.get("file_path"),
            data.get("series_id"),
            data.get("series_order"),
            data.get("category_id"),
            data.get("author"),
            data.get("publisher"),
            data.get("cover_image"),
        )

        try:
            book_id = self.execute_insert(sql, params)

            # 読書進捗レコードの初期化
            progress_sql = "INSERT INTO reading_progress (book_id) VALUES (?)"
            self.execute_insert(progress_sql, (book_id,))

            return book_id
        except Exception as e:
            print(f"Error creating book: {e}")
            return None

    def update(self, book_id, data):
        """
        書籍を更新する。

        Parameters
        ----------
        book_id : int
            更新する書籍のID
        data : dict
            更新するデータ

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        allowed_fields = {
            "title",
            "series_id",
            "series_order",
            "category_id",
            "author",
            "publisher",
            "cover_image",
        }

        update_fields = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_fields:
            return False

        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [book_id]

        sql = f"""
            UPDATE books 
            SET {set_clause}
            WHERE id = ?
        """

        try:
            rows_affected = self.execute_update(sql, values)
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating book: {e}")
            return False

    def delete(self, book_id):
        """
        書籍を削除する。

        Parameters
        ----------
        book_id : int
            削除する書籍のID

        Returns
        -------
        bool
            削除が成功したかどうか
        """
        try:
            # 読書進捗を削除
            self.execute_update(
                "DELETE FROM reading_progress WHERE book_id = ?", (book_id,)
            )

            # カスタムメタデータを削除
            self.execute_update(
                "DELETE FROM custom_metadata WHERE book_id = ?", (book_id,)
            )

            # 書籍を削除
            rows_affected = self.execute_update(
                "DELETE FROM books WHERE id = ?", (book_id,)
            )

            return rows_affected > 0
        except Exception as e:
            print(f"Error deleting book: {e}")
            return False

    def update_reading_progress(
        self, book_id, current_page=None, total_pages=None, status=None
    ):
        """
        読書進捗を更新する。

        Parameters
        ----------
        book_id : int
            書籍のID
        current_page : int, optional
            現在のページ番号
        total_pages : int, optional
            総ページ数
        status : str, optional
            読書状態

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        update_dict = {}
        if current_page is not None:
            update_dict["current_page"] = current_page
        if total_pages is not None:
            update_dict["total_pages"] = total_pages
        if status is not None:
            update_dict["status"] = status

        if status == "reading" or (current_page is not None and current_page > 0):
            update_dict["last_read_date"] = "CURRENT_TIMESTAMP"

        if not update_dict:
            return False

        # SQLのSET句を構築
        set_parts = []
        params = []

        for field, value in update_dict.items():
            if value == "CURRENT_TIMESTAMP":
                set_parts.append(f"{field} = CURRENT_TIMESTAMP")
            else:
                set_parts.append(f"{field} = ?")
                params.append(value)

        set_clause = ", ".join(set_parts)
        params.append(book_id)

        sql = f"""
            UPDATE reading_progress 
            SET {set_clause}
            WHERE book_id = ?
        """

        try:
            rows_affected = self.execute_update(sql, params)
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating reading progress: {e}")
            return False

    def get_by_category(self, category_id, **kwargs):
        """
        カテゴリに属する書籍を取得する。

        Parameters
        ----------
        category_id : int
            カテゴリID
        **kwargs
            追加の検索条件

        Returns
        -------
        list
            書籍データの辞書のリスト
        """
        sql = """
            SELECT b.*, rp.status, rp.current_page, s.name as series_name, c.name as category_name
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            LEFT JOIN series s ON b.series_id = s.id
            LEFT JOIN categories c ON (b.category_id = c.id OR s.category_id = c.id)
            WHERE (b.category_id = ? OR s.category_id = ?)
        """

        params = [category_id, category_id]

        # 追加の検索条件を適用
        for key, value in kwargs.items():
            if key == "status" and value:
                sql += " AND rp.status = ?"
                params.append(value)

        # タイトルでソート
        sql += " ORDER BY b.title COLLATE NOCASE"

        return self.execute_query(sql, params)

    def get_custom_metadata(self, book_id):
        """
        書籍のカスタムメタデータを取得する。

        Parameters
        ----------
        book_id : int
            書籍のID

        Returns
        -------
        dict
            キーと値のペアとしてのメタデータ
        """
        sql = """
            SELECT key, value FROM custom_metadata
            WHERE book_id = ?
        """

        result = self.execute_query(sql, (book_id,))
        return {row["key"]: row["value"] for row in result}

    def set_custom_metadata(self, book_id, key, value):
        """
        書籍のカスタムメタデータを設定する。

        Parameters
        ----------
        book_id : int
            書籍のID
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
            WHERE book_id = ? AND key = ?
        """

        result = self.execute_query(sql, (book_id, key))

        try:
            if result:
                # 更新
                update_sql = """
                    UPDATE custom_metadata
                    SET value = ?
                    WHERE book_id = ? AND key = ?
                """
                self.execute_update(update_sql, (value, book_id, key))
            else:
                # 新規追加
                insert_sql = """
                    INSERT INTO custom_metadata (book_id, key, value)
                    VALUES (?, ?, ?)
                """
                self.execute_insert(insert_sql, (book_id, key, value))

            return True
        except Exception as e:
            print(f"Error setting custom metadata: {e}")
            return False

    def batch_update_metadata(self, book_ids, metadata):
        """
        複数書籍のメタデータを一括更新する。

        Parameters
        ----------
        book_ids : list
            更新する書籍IDのリスト
        metadata : dict
            更新するメタデータ

        Returns
        -------
        int
            更新された書籍の数
        """
        if not book_ids or not metadata:
            return 0

        # 標準メタデータの更新
        book_fields = {
            "title",
            "author",
            "publisher",
            "series_id",
            "series_order",
            "category_id",
        }
        book_updates = {k: v for k, v in metadata.items() if k in book_fields}

        updated_count = 0

        if book_updates:
            set_clause = ", ".join([f"{field} = ?" for field in book_updates.keys()])
            placeholders = ", ".join(["?"] * len(book_ids))

            values = list(book_updates.values()) + book_ids

            sql = f"""
                UPDATE books 
                SET {set_clause}
                WHERE id IN ({placeholders})
            """

            try:
                updated_count = self.execute_update(sql, values)
            except Exception as e:
                print(f"Error in batch update: {e}")
                return 0

        # カスタムメタデータの更新
        custom_updates = {k: v for k, v in metadata.items() if k not in book_fields}

        if custom_updates:
            for book_id in book_ids:
                for key, value in custom_updates.items():
                    self.set_custom_metadata(book_id, key, value)

            updated_count += len(book_ids) * len(custom_updates)

        return updated_count
