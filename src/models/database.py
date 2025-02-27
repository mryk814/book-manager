import os
import sqlite3
from pathlib import Path


class DatabaseManager:
    """
    SQLiteデータベースの管理クラス。

    書籍、シリーズ、メタデータ、読書進捗などの情報を保存・管理する。

    Parameters
    ----------
    db_path : str
        データベースファイルのパス。
    """

    def __init__(self, db_path="library.db"):
        """
        Parameters
        ----------
        db_path : str, optional
            データベースファイルのパス。デフォルトは'library.db'。
        """
        self.db_path = db_path
        self.conn = None
        self._create_tables_if_not_exist()

    def connect(self):
        """
        データベースに接続する。

        Returns
        -------
        sqlite3.Connection
            データベース接続オブジェクト。
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """データベース接続を閉じる。"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables_if_not_exist(self):
        """必要なテーブルが存在しない場合に作成する。"""
        conn = self.connect()
        cursor = conn.cursor()

        # カテゴリテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        )
        """)

        # シリーズテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)

        # 書籍テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            series_id INTEGER,
            series_order INTEGER,
            author TEXT,
            publisher TEXT,
            cover_image BLOB,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series (id)
        )
        """)

        # 読書進捗テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reading_progress (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            current_page INTEGER DEFAULT 0,
            total_pages INTEGER DEFAULT 0,
            status TEXT DEFAULT 'unread',  -- 'unread', 'reading', 'completed'
            last_read_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        """)

        # カスタムメタデータテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_metadata (
            id INTEGER PRIMARY KEY,
            book_id INTEGER,
            series_id INTEGER,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (series_id) REFERENCES series (id)
        )
        """)

        conn.commit()

    def add_book(
        self,
        title,
        file_path,
        series_id=None,
        series_order=None,
        author=None,
        publisher=None,
        cover_image=None,
    ):
        """
        新しい書籍をデータベースに追加する。

        Parameters
        ----------
        title : str
            書籍のタイトル
        file_path : str
            PDFファイルへのパス
        series_id : int, optional
            所属するシリーズのID
        series_order : int, optional
            シリーズ内の順番
        author : str, optional
            著者名
        publisher : str, optional
            出版社名
        cover_image : bytes, optional
            表紙画像のバイナリデータ

        Returns
        -------
        int
            追加された書籍のID
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
            INSERT INTO books (title, file_path, series_id, series_order, author, publisher, cover_image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    title,
                    file_path,
                    series_id,
                    series_order,
                    author,
                    publisher,
                    cover_image,
                ),
            )

            book_id = cursor.lastrowid

            # 読書進捗レコードの初期化
            cursor.execute(
                """
            INSERT INTO reading_progress (book_id)
            VALUES (?)
            """,
                (book_id,),
            )

            conn.commit()
            return book_id
        except sqlite3.IntegrityError:
            conn.rollback()
            raise

    def get_book(self, book_id):
        """
        指定したIDの書籍情報を取得する。

        Parameters
        ----------
        book_id : int
            取得する書籍のID

        Returns
        -------
        dict
            書籍情報の辞書
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT b.*, rp.current_page, rp.total_pages, rp.status, rp.last_read_date
        FROM books b
        LEFT JOIN reading_progress rp ON b.id = rp.book_id
        WHERE b.id = ?
        """,
            (book_id,),
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def update_book(self, book_id, **kwargs):
        """
        書籍情報を更新する。

        Parameters
        ----------
        book_id : int
            更新する書籍のID
        **kwargs
            更新するフィールドと値のペア

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        allowed_fields = {
            "title",
            "series_id",
            "series_order",
            "author",
            "publisher",
            "cover_image",
        }
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return False

        conn = self.connect()
        cursor = conn.cursor()

        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [book_id]

        cursor.execute(
            f"""
        UPDATE books 
        SET {set_clause}
        WHERE id = ?
        """,
            values,
        )

        conn.commit()
        return cursor.rowcount > 0

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
            現在のページ
        total_pages : int, optional
            総ページ数
        status : str, optional
            読書状態 ('unread', 'reading', 'completed')

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        conn = self.connect()
        cursor = conn.cursor()

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

        set_clause = ", ".join(
            [
                f"{field} = {val}" if val == "CURRENT_TIMESTAMP" else f"{field} = ?"
                for field, val in update_dict.items()
            ]
        )

        values = [
            val for field, val in update_dict.items() if val != "CURRENT_TIMESTAMP"
        ]
        values.append(book_id)

        cursor.execute(
            f"""
        UPDATE reading_progress 
        SET {set_clause}
        WHERE book_id = ?
        """,
            values,
        )

        conn.commit()
        return cursor.rowcount > 0

    def add_series(self, name, description=None, category_id=None):
        """
        新しいシリーズをデータベースに追加する。

        Parameters
        ----------
        name : str
            シリーズ名
        description : str, optional
            シリーズの説明
        category_id : int, optional
            所属するカテゴリのID

        Returns
        -------
        int
            追加されたシリーズのID
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO series (name, description, category_id)
        VALUES (?, ?, ?)
        """,
            (name, description, category_id),
        )

        conn.commit()
        return cursor.lastrowid

    def get_series(self, series_id):
        """
        指定したIDのシリーズ情報を取得する。

        Parameters
        ----------
        series_id : int
            取得するシリーズのID

        Returns
        -------
        dict
            シリーズ情報の辞書
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT s.*, c.name as category_name
        FROM series s
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE s.id = ?
        """,
            (series_id,),
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

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
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT b.*, rp.status, rp.current_page, rp.total_pages
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            WHERE b.series_id = ?
            ORDER BY b.series_order, b.title COLLATE NOCASE
            """,
            (series_id,),
        )

        results = [dict(row) for row in cursor.fetchall()]

        # 自然順ソートを実装（数値を考慮したソート）
        import re

        def natural_sort_key(item):
            """
            series_orderを最優先し、次にタイトルの自然順でソート
            """
            # series_orderがNoneの場合は最大値とする（最後に表示）
            order = (
                item["series_order"]
                if item["series_order"] is not None
                else float("inf")
            )
            title = item["title"] if item["title"] else ""
            # 数値部分を抽出して数値として扱う
            title_key = [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]
            return (order, title_key)

        # 結果を自然順でソート
        return sorted(results, key=natural_sort_key)

    def search_books(self, query=None, category_id=None, status=None):
        """
        条件に一致する書籍を検索する。

        Parameters
        ----------
        query : str, optional
            タイトル、著者、出版社などで検索するクエリ文字列
        category_id : int, optional
            カテゴリでフィルタリング
        status : str, optional
            読書状態でフィルタリング ('unread', 'reading', 'completed')

        Returns
        -------
        list
            書籍情報の辞書のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()

        sql = """
        SELECT b.*, rp.status, rp.current_page, s.name as series_name
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

        if category_id:
            sql += " AND c.id = ?"
            params.append(category_id)

        if status:
            sql += " AND rp.status = ?"
            params.append(status)

        # タイトルでソートするが、文字列のまま渡す
        sql += " ORDER BY b.title COLLATE NOCASE"  # COLLATE NOCASEで大文字小文字を区別しない

        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]

        # 自然順ソートを実装（数値を考慮したソート）
        import re

        def natural_sort_key(item):
            """
            文字列内の数値を数値として扱うキー関数
            '作品A（1）'と'作品A（10）'を正しく順序付ける
            """
            title = item["title"] if item["title"] else ""
            # 数値部分を抽出して数値として扱う
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        # 結果を自然順でソート
        return sorted(results, key=natural_sort_key)

    def get_all_categories(self):
        """
        すべてのカテゴリを取得する。

        Returns
        -------
        list
            カテゴリ情報の辞書のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_all_series(self, category_id=None):
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
        conn = self.connect()
        cursor = conn.cursor()

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

        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def set_custom_metadata(self, book_id=None, series_id=None, key=None, value=None):
        """
        書籍またはシリーズにカスタムメタデータを設定する。

        Parameters
        ----------
        book_id : int, optional
            書籍のID（書籍のメタデータを設定する場合）
        series_id : int, optional
            シリーズのID（シリーズのメタデータを設定する場合）
        key : str
            メタデータのキー
        value : str
            メタデータの値

        Returns
        -------
        bool
            設定が成功したかどうか
        """
        if not key or (book_id is None and series_id is None):
            return False

        conn = self.connect()
        cursor = conn.cursor()

        # 既存のエントリを確認
        if book_id:
            cursor.execute(
                """
            SELECT id FROM custom_metadata
            WHERE book_id = ? AND key = ?
            """,
                (book_id, key),
            )
        else:
            cursor.execute(
                """
            SELECT id FROM custom_metadata
            WHERE series_id = ? AND key = ?
            """,
                (series_id, key),
            )

        existing = cursor.fetchone()

        if existing:
            # 更新
            if book_id:
                cursor.execute(
                    """
                UPDATE custom_metadata
                SET value = ?
                WHERE book_id = ? AND key = ?
                """,
                    (value, book_id, key),
                )
            else:
                cursor.execute(
                    """
                UPDATE custom_metadata
                SET value = ?
                WHERE series_id = ? AND key = ?
                """,
                    (value, series_id, key),
                )
        else:
            # 新規追加
            cursor.execute(
                """
            INSERT INTO custom_metadata (book_id, series_id, key, value)
            VALUES (?, ?, ?, ?)
            """,
                (book_id, series_id, key, value),
            )

        conn.commit()
        return True

    def get_custom_metadata(self, book_id=None, series_id=None):
        """
        書籍またはシリーズのカスタムメタデータを取得する。

        Parameters
        ----------
        book_id : int, optional
            書籍のID
        series_id : int, optional
            シリーズのID

        Returns
        -------
        dict
            キーと値のペアとしてのメタデータ
        """
        if book_id is None and series_id is None:
            return {}

        conn = self.connect()
        cursor = conn.cursor()

        if book_id:
            cursor.execute(
                """
            SELECT key, value FROM custom_metadata
            WHERE book_id = ?
            """,
                (book_id,),
            )
        else:
            cursor.execute(
                """
            SELECT key, value FROM custom_metadata
            WHERE series_id = ?
            """,
                (series_id,),
            )

        return {row["key"]: row["value"] for row in cursor.fetchall()}

    def batch_update_metadata(self, book_ids, metadata_updates):
        """
        複数の書籍のメタデータを一括更新する。

        Parameters
        ----------
        book_ids : list
            更新する書籍IDのリスト
        metadata_updates : dict
            更新するメタデータのキーと値

        Returns
        -------
        int
            更新された書籍の数
        """
        if not book_ids or not metadata_updates:
            return 0

        conn = self.connect()
        cursor = conn.cursor()

        # 標準メタデータの更新
        book_fields = {"title", "author", "publisher", "series_id", "series_order"}
        book_updates = {k: v for k, v in metadata_updates.items() if k in book_fields}

        updated_count = 0

        if book_updates:
            set_clause = ", ".join([f"{field} = ?" for field in book_updates.keys()])
            placeholders = ", ".join(["?"] * len(book_ids))

            values = list(book_updates.values()) + book_ids

            cursor.execute(
                f"""
            UPDATE books 
            SET {set_clause}
            WHERE id IN ({placeholders})
            """,
                values,
            )

            updated_count = cursor.rowcount

        # カスタムメタデータの更新
        custom_updates = {
            k: v for k, v in metadata_updates.items() if k not in book_fields
        }

        for book_id in book_ids:
            for key, value in custom_updates.items():
                self.set_custom_metadata(book_id=book_id, key=key, value=value)

        conn.commit()
        return (
            updated_count + len(book_ids) * len(custom_updates)
            if custom_updates
            else updated_count
        )
