from models.book import Book


class Series:
    def __init__(self, series_data, db_manager):
        self.data = series_data
        self.db_manager = db_manager
        self._books = None
        self._custom_metadata = None

    @property
    def id(self):
        return self.data.get("id")

    @property
    def name(self):
        return self.data.get("name")

    @property
    def description(self):
        return self.data.get("description")

    @property
    def category_id(self):
        return self.data.get("category_id")

    @property
    def category_name(self):
        return self.data.get("category_name")

    @property
    def custom_metadata(self):
        if self._custom_metadata is None:
            self._custom_metadata = self.db_manager.get_custom_metadata(
                series_id=self.id
            )
        return self._custom_metadata

    @property
    def books(self):
        if self._books is None:
            book_data_list = self.db_manager.get_books_in_series(self.id)
            self._books = [
                Book(book_data, self.db_manager) for book_data in book_data_list
            ]
        return self._books

    def get_book_count(self):
        return len(self.books)

    def get_reading_status(self):
        status_counts = {
            Book.STATUS_UNREAD: 0,
            Book.STATUS_READING: 0,
            Book.STATUS_COMPLETED: 0,
        }

        for book in self.books:
            status = book.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts

    def update_metadata(self, **kwargs):
        standard_fields = {"name", "description", "category_id"}
        standard_updates = {k: v for k, v in kwargs.items() if k in standard_fields}
        custom_updates = {k: v for k, v in kwargs.items() if k not in standard_fields}

        success = True

        if standard_updates:
            conn = self.db_manager.connect()
            cursor = conn.cursor()

            set_clause = ", ".join(
                [f"{field} = ?" for field in standard_updates.keys()]
            )
            values = list(standard_updates.values()) + [self.id]

            cursor.execute(
                f"""
            UPDATE series 
            SET {set_clause}
            WHERE id = ?
            """,
                values,
            )

            conn.commit()
            db_success = cursor.rowcount > 0

            if db_success:
                for k, v in standard_updates.items():
                    self.data[k] = v

            success = success and db_success

        for key, value in custom_updates.items():
            meta_success = self.db_manager.set_custom_metadata(
                series_id=self.id, key=key, value=value
            )
            if meta_success and self._custom_metadata is not None:
                self._custom_metadata[key] = value
            success = success and meta_success

        return success

    def add_book(self, book_id, order=None):
        if order is None and self._books is not None:
            order = len(self._books) + 1

        success = self.db_manager.update_book(
            book_id, series_id=self.id, series_order=order
        )

        if success:
            self._books = None

        return success

    def remove_book(self, book_id):
        success = self.db_manager.update_book(
            book_id, series_id=None, series_order=None
        )

        # 書籍リストをリフレッシュ
        if success:
            self._books = None

        return success

    def reorder_books(self, order_mapping):
        success = True

        for book_id, new_order in order_mapping.items():
            book_success = self.db_manager.update_book(book_id, series_order=new_order)
            success = success and book_success

        # 書籍リストをリフレッシュ
        if success:
            self._books = None

        return success

    def get_first_book(self):
        books = self.books
        if not books:
            return None

        import re

        def natural_sort_key(book):
            order = book.series_order if book.series_order is not None else float("inf")
            title = book.title if book.title else ""
            title_key = [
                int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", title)
            ]
            return (order, title_key)

        sorted_books = sorted(books, key=natural_sort_key)
        return sorted_books[0] if sorted_books else None

    def get_book_by_order(self, order):
        """
        指定した順番の書籍を取得。

        Parameters
        ----------
        order : int
            書籍の順番

        Returns
        -------
        Book または None
            指定順番の書籍、もしくは見つからない場合はNone
        """
        for book in self.books:
            if book.series_order == order:
                return book
        return None
