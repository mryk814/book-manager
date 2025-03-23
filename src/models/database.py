import os
import sqlite3
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path="library.db"):
        self.db_path = db_path
        self.conn = None
        self._create_tables_if_not_exist()

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables_if_not_exist(self):
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
            FOREIGN KEY (category_id) REFERENCES categories (id)
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

        import re

        def natural_sort_key(item):
            """
            series_orderを最優先し、次にタイトルの自然順でソート
            """
            order = (
                item["series_order"]
                if item["series_order"] is not None
                else float("inf")
            )
            title = item["title"] if item["title"] else ""
            title_key = [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]
            return (order, title_key)

        # 結果を自然順でソート
        return sorted(results, key=natural_sort_key)

    def search_books(self, query=None, category_id=None, status=None):
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

        sql += " ORDER BY b.title COLLATE NOCASE"

        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]

        import re

        def natural_sort_key(item):
            title = item["title"] if item["title"] else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        return sorted(results, key=natural_sort_key)

    def get_category(self, category_id):
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
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_all_series(self, category_id=None):
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

    def get_books_by_category(self, category_id, **kwargs):
        conn = self.connect()
        cursor = conn.cursor()

        # 基本クエリ
        sql = """
        SELECT b.*, rp.status, rp.current_page, s.name as series_name, c.name as category_name
        FROM books b
        LEFT JOIN reading_progress rp ON b.id = rp.book_id
        LEFT JOIN series s ON b.series_id = s.id
        LEFT JOIN categories c ON (b.category_id = c.id OR s.category_id = c.id)
        WHERE (b.category_id = ? OR s.category_id = ?)
        """

        params = [category_id, category_id]

        for key, value in kwargs.items():
            if key == "status" and value:
                sql += " AND rp.status = ?"
                params.append(value)

        sql += " ORDER BY b.title COLLATE NOCASE"

        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]

        import re

        def natural_sort_key(item):
            title = item["title"] if item["title"] else ""
            return [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]

        return sorted(results, key=natural_sort_key)

    def migrate_database(self):
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(books)")
            columns = [col[1] for col in cursor.fetchall()]

            if "category_id" not in columns:
                print("Migrating database: Adding category_id column to books table...")
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
