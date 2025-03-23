from models.series import Series


class SeriesController:
    """
    シリーズに関連する操作を管理するコントローラクラス。

    シリーズの取得、作成、更新などの機能を提供する。

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

    def get_all_series(self, category_id=None):
        """
        シリーズのリストを取得する。

        Parameters
        ----------
        category_id : int, optional
            特定のカテゴリに属するシリーズのみを取得

        Returns
        -------
        list
            Series オブジェクトのリスト
        """
        series_data_list = self.db_manager.get_all_series(category_id)
        return [
            Series(series_data, self.db_manager) for series_data in series_data_list
        ]

    def get_series(self, series_id):
        """
        指定したIDのシリーズを取得する。

        Parameters
        ----------
        series_id : int
            シリーズのID

        Returns
        -------
        Series または None
            指定IDのシリーズ、もしくは見つからない場合はNone
        """
        series_data = self.db_manager.get_series(series_id)
        if series_data:
            return Series(series_data, self.db_manager)
        return None

    def create_series(self, name, description=None, category_id=None):
        """
        新しいシリーズを作成する。

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
        int または None
            追加されたシリーズのID、もしくは失敗した場合はNone
        """
        try:
            series_id = self.db_manager.add_series(
                name=name, description=description, category_id=category_id
            )
            return series_id
        except Exception as e:
            print(f"Error creating series: {e}")
            return None

    def update_series(self, series_id, name=None, description=None, category_id=None):
        """
        シリーズの情報を更新する。

        Parameters
        ----------
        series_id : int
            更新するシリーズのID
        name : str, optional
            新しいシリーズ名
        description : str, optional
            新しいシリーズの説明
        category_id : int, optional
            新しいカテゴリID

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        series = self.get_series(series_id)
        if not series:
            return False

        # 更新するフィールドを準備
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if category_id is not None:
            update_data["category_id"] = category_id

        if not update_data:
            return True  # 更新するデータがない場合は成功とみなす

        # 更新を実行
        return series.update_metadata(**update_data)

    def delete_series(self, series_id):
        """
        シリーズを削除する。所属する書籍はシリーズから解除する。

        Parameters
        ----------
        series_id : int
            削除するシリーズのID

        Returns
        -------
        bool
            削除が成功したかどうか
        """
        series = self.get_series(series_id)
        if not series:
            return False

        # シリーズ内の全書籍のシリーズIDをNULLに設定
        for book in series.books:
            book.update_metadata(series_id=None, series_order=None)

        # シリーズを削除
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        try:
            # カスタムメタデータを削除
            cursor.execute(
                "DELETE FROM custom_metadata WHERE series_id = ?", (series_id,)
            )

            # シリーズを削除
            cursor.execute("DELETE FROM series WHERE id = ?", (series_id,))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting series: {e}")
            conn.rollback()
            return False

    def add_book_to_series(self, book_id, series_id, order=None):
        """
        書籍をシリーズに追加する。

        Parameters
        ----------
        book_id : int
            追加する書籍のID
        series_id : int
            追加先のシリーズID
        order : int, optional
            シリーズ内の順番

        Returns
        -------
        bool
            追加が成功したかどうか
        """
        series = self.get_series(series_id)
        if not series:
            return False

        return series.add_book(book_id, order)

    def remove_book_from_series(self, book_id, series_id):
        """
        書籍をシリーズから削除する。

        Parameters
        ----------
        book_id : int
            削除する書籍のID
        series_id : int
            シリーズID

        Returns
        -------
        bool
            削除が成功したかどうか
        """
        series = self.get_series(series_id)
        if not series:
            return False

        return series.remove_book(book_id)

    def reorder_books(self, series_id, order_mapping):
        """
        シリーズ内の書籍の順序を変更する。

        Parameters
        ----------
        series_id : int
            シリーズID
        order_mapping : dict
            book_id: new_order の形式の辞書

        Returns
        -------
        bool
            更新が成功したかどうか
        """
        series = self.get_series(series_id)
        if not series:
            return False

        return series.reorder_books(order_mapping)
