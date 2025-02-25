import logging
import os

from sqlalchemy import and_, asc, create_engine, desc, or_
from sqlalchemy.orm import sessionmaker

from .models import Base, Book, Bookmark, Category, CustomMetadata, Series, Tag, View


class DatabaseManager:
    """データベース操作を管理するクラス"""

    def __init__(self, db_path):
        """
        データベースマネージャーの初期化

        Args:
            db_path (str): データベースファイルのパス
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        logging.info(f"データベース接続完了: {db_path}")

    def close(self):
        """セッションを閉じる"""
        self.session.close()

    def commit(self):
        """変更をコミット"""
        self.session.commit()

    # ==== 書籍管理 ====
    def add_book(self, book_data):
        """
        新しい書籍を追加

        Args:
            book_data (dict): 書籍データ

        Returns:
            Book: 追加された書籍オブジェクト
        """
        try:
            print(
                f"書籍の追加を試みています: {book_data.get('title', 'Unknown')}"
            )  # デバッグ情報

            # 必要なフィールドが存在するか確認
            if "file_path" not in book_data or not book_data["file_path"]:
                logging.error("ファイルパスが指定されていません")
                print("ファイルパスが指定されていません")  # デバッグ情報
                return None

            if "title" not in book_data or not book_data["title"]:
                file_name = os.path.basename(book_data["file_path"])
                book_data["title"] = os.path.splitext(file_name)[0]
                print(
                    f"タイトルがないためファイル名を使用: {book_data['title']}"
                )  # デバッグ情報

            # ファイルパスが既に存在するか確認
            existing_book = (
                self.session.query(Book)
                .filter_by(file_path=book_data["file_path"])
                .first()
            )
            if existing_book:
                logging.warning(f"既存の書籍です: {book_data['file_path']}")
                print(f"既存の書籍です: {book_data['file_path']}")  # デバッグ情報
                return existing_book

            # モデルに存在するフィールドのみを抽出
            valid_fields = {}
            book_model_attrs = [attr.key for attr in Book.__table__.columns]

            for key, value in book_data.items():
                if key in book_model_attrs:
                    valid_fields[key] = value
                elif key != "tags" and key != "series_name":
                    print(f"警告: '{key}'はBookモデルの有効なフィールドではありません")

            # タグとシリーズを一時的に取り除く
            tags_data = book_data.get("tags", [])
            series_name = book_data.get("series_name")

            # 新しい書籍オブジェクトを作成
            new_book = Book(**valid_fields)

            # タグの処理
            for tag_name in tags_data:
                tag = self.get_or_create_tag(tag_name)
                new_book.tags.append(tag)

            # シリーズの処理
            if series_name:
                series = self.get_or_create_series(series_name)
                new_book.series.append(series)

            self.session.add(new_book)
            self.session.commit()
            logging.info(f"書籍を追加しました: {new_book.title}")
            print(f"書籍を追加しました: {new_book.title}")  # デバッグ情報
            return new_book

        except Exception as e:
            self.session.rollback()
            logging.error(f"書籍追加エラー: {e}")
            print(f"書籍追加エラー: {e}")  # デバッグ情報
            import traceback

            traceback.print_exc()  # スタックトレースを出力
            return None

    def update_book(self, book_id, book_data):
        """
        書籍情報を更新

        Args:
            book_id (int): 書籍ID
            book_data (dict): 更新データ

        Returns:
            Book: 更新された書籍オブジェクト
        """
        book = self.session.query(Book).get(book_id)
        if not book:
            logging.error(f"書籍が見つかりません: ID {book_id}")
            return None

        # タグとシリーズの特別処理
        if "tags" in book_data:
            # タグを全てクリアして新しいタグを設定
            book.tags.clear()
            for tag_name in book_data["tags"]:
                tag = self.get_or_create_tag(tag_name)
                book.tags.append(tag)
            del book_data["tags"]

        if "series_name" in book_data:
            book.series.clear()
            if book_data["series_name"]:
                series = self.get_or_create_series(book_data["series_name"])
                book.series.append(series)
            del book_data["series_name"]

        # その他の属性を更新
        for key, value in book_data.items():
            setattr(book, key, value)

        self.session.commit()
        logging.info(f"書籍を更新しました: ID {book_id}")
        return book

    def delete_book(self, book_id):
        """
        書籍を削除

        Args:
            book_id (int): 書籍ID

        Returns:
            bool: 削除成功の場合True
        """
        book = self.session.query(Book).get(book_id)
        if not book:
            logging.error(f"書籍が見つかりません: ID {book_id}")
            return False

        self.session.delete(book)
        self.session.commit()
        logging.info(f"書籍を削除しました: ID {book_id}")
        return True

    def get_book(self, book_id):
        """
        書籍IDから書籍を取得

        Args:
            book_id (int): 書籍ID

        Returns:
            Book: 書籍オブジェクト
        """
        return self.session.query(Book).get(book_id)

    def get_book_by_path(self, file_path):
        """
        ファイルパスから書籍を取得

        Args:
            file_path (str): ファイルパス

        Returns:
            Book: 書籍オブジェクト
        """
        return self.session.query(Book).filter_by(file_path=file_path).first()

    def get_all_books(self, sort_by="title", sort_dir="asc"):
        """
        全ての書籍を取得

        Args:
            sort_by (str): ソートフィールド
            sort_dir (str): ソート方向 ('asc' or 'desc')

        Returns:
            list: 書籍オブジェクトのリスト
        """
        query = self.session.query(Book)

        # ソート順を設定
        if hasattr(Book, sort_by):
            order_column = getattr(Book, sort_by)
            if sort_dir.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

        return query.all()

    def search_books(self, search_term, fields=None):
        """
        書籍を検索

        Args:
            search_term (str): 検索キーワード
            fields (list): 検索対象フィールド (Noneの場合はデフォルトフィールド)

        Returns:
            list: 検索結果の書籍リスト
        """
        if not fields:
            fields = ["title", "author", "publisher"]

        search_term = f"%{search_term}%"
        filters = []

        for field in fields:
            if hasattr(Book, field):
                filters.append(getattr(Book, field).ilike(search_term))

        # カスタムメタデータも検索
        subquery = (
            self.session.query(CustomMetadata.book_id)
            .filter(CustomMetadata.value.ilike(search_term))
            .distinct()
        )

        filters.append(Book.id.in_(subquery))

        return self.session.query(Book).filter(or_(*filters)).all()

    def filter_books(self, filters):
        """
        書籍をフィルタリング

        Args:
            filters (dict): フィルタ条件

        Returns:
            list: フィルタリングされた書籍リスト
        """
        query = self.session.query(Book)

        # 標準フィールドのフィルタリング
        for field, value in filters.items():
            if field == "tags":
                # タグによるフィルタリング
                for tag_id in value:
                    query = query.filter(Book.tags.any(Tag.id == tag_id))
            elif field == "series":
                # シリーズによるフィルタリング
                query = query.filter(Book.series.any(Series.id == value))
            elif field == "reading_status":
                # 読書状態によるフィルタリング
                query = query.filter(Book.reading_status == value)
            elif hasattr(Book, field):
                # その他の標準フィールド
                query = query.filter(getattr(Book, field) == value)

        return query.all()

    # ==== タグ管理 ====
    def get_or_create_tag(self, tag_name):
        """
        タグを取得または作成

        Args:
            tag_name (str): タグ名

        Returns:
            Tag: タグオブジェクト
        """
        tag = self.session.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            self.session.add(tag)
            self.session.commit()
            logging.info(f"タグを作成しました: {tag_name}")
        return tag

    def get_all_tags(self):
        """
        全てのタグを取得

        Returns:
            list: タグオブジェクトのリスト
        """
        return self.session.query(Tag).order_by(Tag.name).all()

    def update_tag(self, tag_id, tag_data):
        """
        タグを更新

        Args:
            tag_id (int): タグID
            tag_data (dict): 更新データ

        Returns:
            Tag: 更新されたタグオブジェクト
        """
        tag = self.session.query(Tag).get(tag_id)
        if not tag:
            logging.error(f"タグが見つかりません: ID {tag_id}")
            return None

        for key, value in tag_data.items():
            setattr(tag, key, value)

        self.session.commit()
        return tag

    def delete_tag(self, tag_id):
        """
        タグを削除

        Args:
            tag_id (int): タグID

        Returns:
            bool: 削除成功の場合True
        """
        tag = self.session.query(Tag).get(tag_id)
        if not tag:
            logging.error(f"タグが見つかりません: ID {tag_id}")
            return False

        self.session.delete(tag)
        self.session.commit()
        logging.info(f"タグを削除しました: ID {tag_id}")
        return True

    # ==== シリーズ管理 ====
    def get_or_create_series(self, series_name):
        """
        シリーズを取得または作成

        Args:
            series_name (str): シリーズ名

        Returns:
            Series: シリーズオブジェクト
        """
        series = self.session.query(Series).filter_by(name=series_name).first()
        if not series:
            series = Series(name=series_name)
            self.session.add(series)
            self.session.commit()
            logging.info(f"シリーズを作成しました: {series_name}")
        return series

    def get_all_series(self):
        """
        全てのシリーズを取得

        Returns:
            list: シリーズオブジェクトのリスト
        """
        return self.session.query(Series).order_by(Series.name).all()

    def update_series(self, series_id, series_data):
        """
        シリーズを更新

        Args:
            series_id (int): シリーズID
            series_data (dict): 更新データ

        Returns:
            Series: 更新されたシリーズオブジェクト
        """
        series = self.session.query(Series).get(series_id)
        if not series:
            logging.error(f"シリーズが見つかりません: ID {series_id}")
            return None

        for key, value in series_data.items():
            setattr(series, key, value)

        self.session.commit()
        return series

    def delete_series(self, series_id):
        """
        シリーズを削除

        Args:
            series_id (int): シリーズID

        Returns:
            bool: 削除成功の場合True
        """
        series = self.session.query(Series).get(series_id)
        if not series:
            logging.error(f"シリーズが見つかりません: ID {series_id}")
            return False

        # 削除前に関連付けを解除
        for book in series.books:
            book.series.remove(series)

        self.session.delete(series)
        self.session.commit()
        logging.info(f"シリーズを削除しました: ID {series_id}")
        return True

    def get_books_by_series(self, series_id, sort_by="volume_number"):
        """
        シリーズに属する書籍を取得

        Args:
            series_id (int): シリーズID
            sort_by (str): ソートフィールド

        Returns:
            list: 書籍オブジェクトのリスト
        """
        series = self.session.query(Series).get(series_id)
        if not series:
            return []

        # ソート順を設定
        if sort_by == "volume_number":
            return sorted(
                series.books, key=lambda book: book.volume_number or float("inf")
            )
        else:
            return series.books

    # ==== カテゴリ管理 ====
    def get_or_create_category(self, category_name, description=None):
        """
        カテゴリを取得または作成

        Args:
            category_name (str): カテゴリ名
            description (str): 説明

        Returns:
            Category: カテゴリオブジェクト
        """
        category = self.session.query(Category).filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name, description=description)
            self.session.add(category)
            self.session.commit()
            logging.info(f"カテゴリを作成しました: {category_name}")
        return category

    def get_all_categories(self):
        """
        全てのカテゴリを取得

        Returns:
            list: カテゴリオブジェクトのリスト
        """
        return (
            self.session.query(Category)
            .order_by(Category.display_order, Category.name)
            .all()
        )

    # ==== ビュー管理 ====
    def create_view(self, view_data):
        """
        ビューを作成

        Args:
            view_data (dict): ビューデータ

        Returns:
            View: 作成されたビューオブジェクト
        """
        new_view = View(**view_data)
        self.session.add(new_view)
        self.session.commit()
        return new_view

    def get_views_by_category(self, category_id):
        """
        カテゴリに属するビューを取得

        Args:
            category_id (int): カテゴリID

        Returns:
            list: ビューオブジェクトのリスト
        """
        return self.session.query(View).filter_by(category_id=category_id).all()

    # ==== ブックマーク管理 ====
    def add_bookmark(self, book_id, page, name=None):
        """
        ブックマークを追加

        Args:
            book_id (int): 書籍ID
            page (int): ページ番号
            name (str): ブックマーク名

        Returns:
            Bookmark: 作成されたブックマークオブジェクト
        """
        bookmark = Bookmark(book_id=book_id, page=page, name=name)
        self.session.add(bookmark)
        self.session.commit()
        return bookmark

    def get_bookmarks_by_book(self, book_id):
        """
        書籍のブックマークを取得

        Args:
            book_id (int): 書籍ID

        Returns:
            list: ブックマークオブジェクトのリスト
        """
        return (
            self.session.query(Bookmark)
            .filter_by(book_id=book_id)
            .order_by(Bookmark.page)
            .all()
        )

    def update_category(self, category_id, name, description=None, display_order=0):
        """
        カテゴリを更新

        Args:
            category_id (int): カテゴリID
            name (str): カテゴリ名
            description (str): 説明
            display_order (int): 表示順

        Returns:
            Category: 更新されたカテゴリオブジェクト
        """
        category = self.session.query(Category).get(category_id)
        if not category:
            logging.error(f"カテゴリが見つかりません: ID {category_id}")
            return None

        category.name = name
        if description is not None:
            category.description = description
        category.display_order = display_order

        self.session.commit()
        return category

    def update_category_display_order(self, category_id, display_order):
        """
        カテゴリの表示順を更新

        Args:
            category_id (int): カテゴリID
            display_order (int): 表示順

        Returns:
            Category: 更新されたカテゴリオブジェクト
        """
        category = self.session.query(Category).get(category_id)
        if not category:
            logging.error(f"カテゴリが見つかりません: ID {category_id}")
            return None

        category.display_order = display_order
        self.session.commit()
        return category

    def delete_category(self, category_id):
        """
        カテゴリを削除（関連するビューも削除）

        Args:
            category_id (int): カテゴリID

        Returns:
            bool: 削除成功の場合True
        """
        category = self.session.query(Category).get(category_id)
        if not category:
            logging.error(f"カテゴリが見つかりません: ID {category_id}")
            return False

        # 関連するビューを削除
        views = self.session.query(View).filter_by(category_id=category_id).all()
        for view in views:
            self.session.delete(view)

        # カテゴリを削除
        self.session.delete(category)
        self.session.commit()
        logging.info(f"カテゴリを削除しました: ID {category_id}")
        return True

    def create_view(self, view_data):
        """
        ビューを作成

        Args:
            view_data (dict): ビューデータ

        Returns:
            View: 作成されたビューオブジェクト
        """
        new_view = View(**view_data)
        self.session.add(new_view)
        self.session.commit()
        logging.info(f"ビューを作成しました: {new_view.name}")
        return new_view

    def update_view(self, view_id, view_data):
        """
        ビューを更新

        Args:
            view_id (int): ビューID
            view_data (dict): 更新データ

        Returns:
            View: 更新されたビューオブジェクト
        """
        view = self.session.query(View).get(view_id)
        if not view:
            logging.error(f"ビューが見つかりません: ID {view_id}")
            return None

        for key, value in view_data.items():
            setattr(view, key, value)

        self.session.commit()
        logging.info(f"ビューを更新しました: ID {view_id}")
        return view

    def delete_view(self, view_id):
        """
        ビューを削除

        Args:
            view_id (int): ビューID

        Returns:
            bool: 削除成功の場合True
        """
        view = self.session.query(View).get(view_id)
        if not view:
            logging.error(f"ビューが見つかりません: ID {view_id}")
            return False

        self.session.delete(view)
        self.session.commit()
        logging.info(f"ビューを削除しました: ID {view_id}")
        return True
