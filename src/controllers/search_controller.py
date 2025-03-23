from models.book import Book
from models.series import Series
from repositories.book_repository import BookRepository


class SearchController:
    """
    検索機能を管理するコントローラクラス。

    ライブラリ内の書籍、シリーズ、カテゴリの検索機能を提供する。

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
        self.book_repository = BookRepository(db_manager)

    def search_books(self, query, filters=None):
        """
        書籍を検索する。

        Parameters
        ----------
        query : str
            検索クエリ
        filters : dict, optional
            検索フィルタ（カテゴリ、状態など）

        Returns
        -------
        list
            検索結果の書籍リスト
        """
        if filters is None:
            filters = {}

        book_data_list = self.book_repository.search(query, **filters)
        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def search_series(self, query, category_id=None):
        """
        シリーズを検索する。

        Parameters
        ----------
        query : str
            検索クエリ
        category_id : int, optional
            カテゴリによるフィルタ

        Returns
        -------
        list
            検索結果のシリーズリスト
        """
        # シリーズを取得
        from controllers.series_controller import SeriesController

        series_controller = SeriesController(self.db_manager)
        series_list = series_controller.get_all_series(category_id)

        if not query:
            return series_list

        # クエリで絞り込み
        query = query.lower()
        filtered_list = []

        for series in series_list:
            # シリーズ名で検索
            if query in series.name.lower():
                filtered_list.append(series)
                continue

            # カテゴリ名で検索
            if series.category_name and query in series.category_name.lower():
                filtered_list.append(series)
                continue

            # 書籍のタイトルで検索
            for book in series.books:
                if query in book.title.lower():
                    filtered_list.append(series)
                    break

        return filtered_list

    def search_categories(self, query):
        """
        カテゴリを検索する。

        Parameters
        ----------
        query : str
            検索クエリ

        Returns
        -------
        list
            検索結果のカテゴリリスト
        """
        from controllers.category_controller import CategoryController

        category_controller = CategoryController(self.db_manager)
        all_categories = category_controller.get_all_categories()

        if not query:
            return all_categories

        # クエリで絞り込み
        query = query.lower()
        return [
            category
            for category in all_categories
            if query in category["name"].lower()
            or (category["description"] and query in category["description"].lower())
        ]

    def advanced_search(self, criteria):
        """
        複雑な条件による高度な検索を行う。

        Parameters
        ----------
        criteria : dict
            検索条件の辞書

        Returns
        -------
        list
            検索結果の書籍リスト
        """
        sql_parts = [
            """
            SELECT b.*, rp.status, rp.current_page, s.name as series_name, c.name as category_name
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            LEFT JOIN series s ON b.series_id = s.id
            LEFT JOIN categories c ON b.category_id = c.id OR s.category_id = c.id
            WHERE 1=1
            """
        ]
        params = []

        # 各検索条件を追加
        if "title" in criteria and criteria["title"]:
            sql_parts.append("AND b.title LIKE ?")
            params.append(f"%{criteria['title']}%")

        if "author" in criteria and criteria["author"]:
            sql_parts.append("AND b.author LIKE ?")
            params.append(f"%{criteria['author']}%")

        if "publisher" in criteria and criteria["publisher"]:
            sql_parts.append("AND b.publisher LIKE ?")
            params.append(f"%{criteria['publisher']}%")

        if "status" in criteria and criteria["status"]:
            sql_parts.append("AND rp.status = ?")
            params.append(criteria["status"])

        if "series_id" in criteria and criteria["series_id"]:
            sql_parts.append("AND b.series_id = ?")
            params.append(criteria["series_id"])

        if "category_id" in criteria and criteria["category_id"]:
            sql_parts.append("AND (b.category_id = ? OR s.category_id = ?)")
            params.append(criteria["category_id"])
            params.append(criteria["category_id"])

        if "custom_metadata" in criteria and criteria["custom_metadata"]:
            for key, value in criteria["custom_metadata"].items():
                sql_parts.append("""
                    AND EXISTS (
                        SELECT 1 FROM custom_metadata cm 
                        WHERE cm.book_id = b.id 
                        AND cm.key = ? AND cm.value LIKE ?
                    )
                """)
                params.append(key)
                params.append(f"%{value}%")

        # ソートの設定
        sort_field = criteria.get("sort_field", "title")
        sort_order = criteria.get("sort_order", "ASC")

        valid_sort_fields = {"title", "author", "publisher", "added_date"}
        valid_sort_orders = {"ASC", "DESC"}

        if sort_field not in valid_sort_fields:
            sort_field = "title"
        if sort_order not in valid_sort_orders:
            sort_order = "ASC"

        sql_parts.append(f" ORDER BY b.{sort_field} COLLATE NOCASE {sort_order}")

        # クエリを実行
        sql = " ".join(sql_parts)
        book_data_list = self.db_manager.connect().execute(sql, params).fetchall()
        book_data_list = [dict(row) for row in book_data_list]

        return [Book(book_data, self.db_manager) for book_data in book_data_list]

    def search_in_content(self, query, book_ids=None):
        """
        書籍の内容を検索する（フルテキスト検索）。
        注意: 実装されているPDFの場合のみ可能。

        Parameters
        ----------
        query : str
            検索クエリ
        book_ids : list, optional
            検索対象の書籍IDリスト（指定しない場合はすべての書籍）

        Returns
        -------
        dict
            書籍IDをキー、検索結果リストを値とする辞書
        """
        if not query:
            return {}

        # 検索対象の書籍を取得
        from controllers.book_controller import BookController

        book_controller = BookController(self.db_manager)

        if book_ids:
            books = [book_controller.get_book(book_id) for book_id in book_ids]
            books = [book for book in books if book]
        else:
            books = self.search_books("")

        results = {}

        # 各書籍を検索
        for book in books:
            if not book.exists():
                continue

            try:
                doc = book.open()
                book_results = []

                for _, page_idx in enumerate(doc):
                    page = doc[page_idx]
                    text = page.get_text()

                    if query.lower() in text.lower():
                        # 検索クエリを含む行を抽出
                        lines = text.split("\n")
                        matching_lines = []

                        for line in lines:
                            if query.lower() in line.lower():
                                matching_lines.append(line.strip())

                        if matching_lines:
                            book_results.append(
                                {"page": page_idx, "lines": matching_lines}
                            )

                if book_results:
                    results[book.id] = {"book": book, "matches": book_results}

                doc.close()

            except Exception as e:
                print(f"Error searching in book {book.id}: {e}")

        return results
