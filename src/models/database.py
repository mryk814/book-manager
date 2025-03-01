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
            category_id INTEGER,
            author TEXT,
            publisher TEXT,
            cover_image BLOB,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)  -- 追加: 外部キー
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

        # テーブルのマイグレーションを呼び出す
        self.migrate_database()

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
            "category_id",  # 追加: category_id を許可フィールドに追加
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

    def get_books_in_series(self, series_id, sort_by=None, sort_order="asc"):
        """
        指定したシリーズに属する書籍のリストを取得する。

        Parameters
        ----------
        series_id : int
            シリーズのID
        sort_by : str, optional
            ソート基準 ('title', 'author', 'publisher', 'added_date', 'status', 'last_read', 'series_order')
        sort_order : str, optional
            ソート順序 ('asc' または 'desc')

        Returns
        -------
        list
            書籍情報の辞書のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()

        sql = """
        SELECT b.*, rp.status, rp.current_page, rp.total_pages, rp.last_read_date
        FROM books b
        LEFT JOIN reading_progress rp ON b.id = rp.book_id
        WHERE b.series_id = ?
        """

        params = [series_id]

        # ソート条件の設定
        if sort_by:
            sort_column = "b.title"

            if sort_by == "author":
                sort_column = "b.author"
            elif sort_by == "publisher":
                sort_column = "b.publisher"
            elif sort_by == "added_date":
                sort_column = "b.added_date"
            elif sort_by == "status":
                sort_column = "rp.status"
            elif sort_by == "last_read":
                sort_column = "rp.last_read_date"
            elif sort_by == "series_order":
                # series_orderが存在すればそれを、なければ最大値を使用
                sort_column = "COALESCE(b.series_order, 999999)"

            # NULLは最後に来るようにCASE文を使用
            sql += f" ORDER BY CASE WHEN {sort_column} IS NULL THEN 1 ELSE 0 END, {sort_column} COLLATE NOCASE"

            # ソート順の指定
            if sort_order.lower() == "desc":
                sql += " DESC"
        else:
            # デフォルトはシリーズ順、次にタイトルでソート
            sql += " ORDER BY COALESCE(b.series_order, 999999), b.title COLLATE NOCASE"

        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def search_books(
        self, query=None, category_id=None, status=None, sort_by=None, sort_order="asc"
    ):
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
        sort_by : str, optional
            ソート基準 ('title', 'author', 'publisher', 'added_date', 'status', 'last_read')
        sort_order : str, optional
            ソート順序 ('asc' または 'desc')

        Returns
        -------
        list
            書籍情報の辞書のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()

        sql = """
        SELECT b.*, rp.status, rp.current_page, rp.last_read_date, s.name as series_name
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
            sql += " AND (b.category_id = ? OR s.category_id = ?)"
            params.extend([category_id, category_id])

        if status:
            sql += " AND rp.status = ?"
            params.append(status)

        # ソート条件の設定
        if sort_by:
            # デフォルトのソート順はタイトル
            sort_column = "b.title"

            if sort_by == "author":
                sort_column = "b.author"
            elif sort_by == "publisher":
                sort_column = "b.publisher"
            elif sort_by == "added_date":
                sort_column = "b.added_date"
            elif sort_by == "status":
                sort_column = "rp.status"
            elif sort_by == "last_read":
                sort_column = "rp.last_read_date"

            # 数値の場合でもCOLLATE NOCASEを適用（テキスト部分のソート用）
            # NULLは最後に来るようにCASE文を使用
            sql += f" ORDER BY CASE WHEN {sort_column} IS NULL THEN 1 ELSE 0 END, {sort_column} COLLATE NOCASE"

            # ソート順の指定
            if sort_order.lower() == "desc":
                sql += " DESC"
        else:
            # デフォルトはタイトルでソート
            sql += " ORDER BY b.title COLLATE NOCASE"

        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

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
        if not category_id:
            return None

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM categories
            WHERE id = ?
            """,
            (category_id,),
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

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

    def get_books_by_category(
        self, category_id, sort_by=None, sort_order="asc", **kwargs
    ):
        """
        特定のカテゴリに関連する書籍を取得する。

        Parameters
        ----------
        category_id : int
            カテゴリID
        sort_by : str, optional
            ソート基準 ('title', 'author', 'publisher', 'added_date', 'status', 'last_read')
        sort_order : str, optional
            ソート順序 ('asc' または 'desc')
        **kwargs
            その他の検索条件

        Returns
        -------
        list
            書籍情報の辞書のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()

        # 基本クエリ
        sql = """
        SELECT b.*, rp.status, rp.current_page, rp.last_read_date, s.name as series_name, c.name as category_name
        FROM books b
        LEFT JOIN reading_progress rp ON b.id = rp.book_id
        LEFT JOIN series s ON b.series_id = s.id
        LEFT JOIN categories c ON (b.category_id = c.id OR s.category_id = c.id)
        WHERE (b.category_id = ? OR s.category_id = ?)
        """

        params = [category_id, category_id]

        # 追加の検索条件
        for key, value in kwargs.items():
            if key == "status" and value:
                sql += " AND rp.status = ?"
                params.append(value)

        # ソート条件の設定
        if sort_by:
            # デフォルトのソート順はタイトル
            sort_column = "b.title"

            if sort_by == "author":
                sort_column = "b.author"
            elif sort_by == "publisher":
                sort_column = "b.publisher"
            elif sort_by == "added_date":
                sort_column = "b.added_date"
            elif sort_by == "status":
                sort_column = "rp.status"
            elif sort_by == "last_read":
                sort_column = "rp.last_read_date"

            # NULLは最後に来るようにCASE文を使用
            sql += f" ORDER BY CASE WHEN {sort_column} IS NULL THEN 1 ELSE 0 END, {sort_column} COLLATE NOCASE"

            # ソート順の指定
            if sort_order.lower() == "desc":
                sql += " DESC"
        else:
            # デフォルトはタイトルでソート
            sql += " ORDER BY b.title COLLATE NOCASE"

        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def migrate_database(self):
        """
        データベーススキーマの移行を行う。
        新しいバージョンのアプリケーションで必要なスキーマ変更を適用する。
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            # books テーブルに category_id カラムが存在するか確認
            cursor.execute("PRAGMA table_info(books)")
            columns = [col[1] for col in cursor.fetchall()]

            if "category_id" not in columns:
                print("Migrating database: Adding category_id column to books table...")
                # category_id カラムを追加
                cursor.execute("""
                ALTER TABLE books ADD COLUMN category_id INTEGER 
                REFERENCES categories(id)
                """)
                conn.commit()
                print("Migration successful: Added category_id column to books table")
            else:
                print(
                    "Migration not needed: category_id column already exists in books table"
                )

        except Exception as e:
            print(f"Migration error: {e}")
            conn.rollback()
            raise
