from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget


class BaseView(QWidget):
    """
    すべてのビューの基底クラス。
    共通の機能と基本構造を提供する。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラーのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    # 共通シグナル定義
    item_selected = pyqtSignal(int)  # 単一選択時: item_id
    items_selected = pyqtSignal(list)  # 複数選択時: [item_id, ...]

    def __init__(self, library_controller, parent=None):
        super().__init__(parent)
        self.library_controller = library_controller

        # 基本プロパティ
        self.selected_item_id = None  # 単一選択時の選択ID
        self.selected_item_ids = set()  # 複数選択時の選択IDセット
        self.multi_select_mode = False  # 複数選択モードフラグ
        self.item_widgets = {}  # アイテムウィジェットのマップ {id: widget}

        # フィルタリングプロパティ
        self.category_filter = None  # カテゴリフィルタ
        self.search_query = None  # 検索クエリ

        # 遅延ロード関連プロパティ
        self.all_items = []  # すべてのアイテムデータ
        self.loaded_count = 0  # 読み込み済みの件数
        self.batch_size = 20  # 一度に読み込む件数
        self.is_loading = False  # 読み込み中フラグ

    def refresh(self):
        """ビューを再描画する"""
        self._clear_view()
        self.loaded_count = 0

        # 非同期でデータをロード
        QTimer.singleShot(50, self._load_items_async)

    def _load_items_async(self):
        """アイテムデータを非同期でロードする"""
        self.all_items = self._get_filtered_items()
        self.load_more_items()

    def load_more_items(self):
        """追加のアイテムをロードする"""
        if self.is_loading or self.loaded_count >= len(self.all_items):
            return

        self.is_loading = True

        # 次のバッチのインデックス範囲を計算
        start_idx = self.loaded_count
        end_idx = min(start_idx + self.batch_size, len(self.all_items))

        # バッチ処理
        self._process_batch(start_idx, end_idx)

        # 読み込み済み件数を更新
        self.loaded_count = end_idx
        self.is_loading = False

        # すべてのアイテムを読み込んだか確認
        if self.loaded_count < len(self.all_items):
            # ステータスメッセージを表示（オプション）
            self._update_status_message()

    def _get_filtered_items(self):
        """フィルタリングされたアイテムリストを取得する（サブクラスでオーバーライド）"""
        return []

    def _clear_view(self):
        """ビューをクリアする（サブクラスでオーバーライド）"""
        pass

    def _process_batch(self, start_idx, end_idx):
        """アイテムバッチを処理する（サブクラスでオーバーライド）"""
        pass

    def _update_status_message(self):
        """ステータスメッセージを更新する（オプション）"""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, "statusBar"):
                main_window.statusBar.showMessage(
                    f"Loaded {self.loaded_count} of {len(self.all_items)} items"
                )
        except Exception as e:
            print(f"Error updating status bar: {e}")

    def select_item(self, item_id, emit_signal=True):
        """
        アイテムを選択状態にする。

        Parameters
        ----------
        item_id : int
            選択するアイテムID
        emit_signal : bool, optional
            選択シグナルを発火するかどうか
        """
        # アイテムが表示されていない場合は何もしない
        if item_id not in self.item_widgets:
            return

        # 複数選択モードを無効化
        self.toggle_multi_select_mode(False)

        # 選択をクリアして新しい選択を設定
        self._clear_selection()
        self._select_item(item_id)
        self.selected_item_id = item_id

        # シグナルを発火（オプション）
        if emit_signal:
            self.item_selected.emit(item_id)

    def _select_item(self, item_id, add_to_selection=False):
        """
        アイテムを選択状態にする（サブクラスでオーバーライド）。

        Parameters
        ----------
        item_id : int
            選択するアイテムID
        add_to_selection : bool
            既存の選択に追加するかどうか
        """
        pass

    def _clear_selection(self):
        """すべての選択を解除する（サブクラスでオーバーライド）"""
        pass

    def toggle_multi_select_mode(self, enabled):
        """
        複数選択モードを切り替える。

        Parameters
        ----------
        enabled : bool
            複数選択モードを有効にするかどうか
        """
        self.multi_select_mode = enabled
        self._clear_selection()

    def set_category_filter(self, category_id):
        """
        カテゴリフィルタを設定する。

        Parameters
        ----------
        category_id : int または None
            フィルタリングするカテゴリID、またはNone（すべて表示）
        """
        self.category_filter = category_id
        self.search_query = None  # 検索クエリをクリア
        self.refresh()

    def search(self, query):
        """
        検索を実行する。

        Parameters
        ----------
        query : str
            検索クエリ
        """
        self.search_query = query
        self.refresh()

    def clear_search(self):
        """検索をクリアしてすべてのアイテムを表示する。"""
        self.search_query = None
        self.refresh()

    def get_selected_item_id(self):
        """
        現在選択されているアイテムIDを取得する。

        Returns
        -------
        int または None
            選択されているアイテムID、もしくは選択がない場合はNone
        """
        return self.selected_item_id

    def get_selected_item_ids(self):
        """
        現在選択されている複数のアイテムIDリストを取得する。

        Returns
        -------
        list
            選択されているアイテムIDのリスト
        """
        return list(self.selected_item_ids)
