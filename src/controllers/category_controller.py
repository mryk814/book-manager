from repositories.category_repository import CategoryRepository


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
        self.repository = CategoryRepository(db_manager)

    def get_all_categories(self):
        """
        すべてのカテゴリを取得する。

        Returns
        -------
        list
            カテゴリ情報の辞書のリスト
        """
        return self.repository.get_all()

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
        return self.repository.get_by_id(category_id)

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
        return self.repository.create(name, description)

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
        return self.repository.update(category_id, name, description)

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
        return self.repository.delete(category_id)

    def get_categories_with_counts(self):
        """
        各カテゴリに含まれる書籍数とシリーズ数を含めて取得する。

        Returns
        -------
        list
            拡張したカテゴリ情報の辞書のリスト
        """
        return self.repository.get_with_counts()
