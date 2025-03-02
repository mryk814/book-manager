from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout

from utils.ui_utils import show_error_dialog
from views.base.base_view import BaseView


class BaseListView(BaseView):
    """
    リストビューの基底クラス。
    アイテムをリスト形式で表示する。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラーのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)

        # UI初期化
        self._init_ui()

    def _init_ui(self):
        """UIコンポーネントを初期化する"""
        # レイアウトの設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # リストウィジェット
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )

        # スクロールイベントを監視
        self.list_widget.verticalScrollBar().valueChanged.connect(
            self._check_scroll_position
        )

        layout.addWidget(self.list_widget)

    def _clear_view(self):
        """リストをクリアする"""
        self.list_widget.clear()
        self.item_widgets.clear()
        self.selected_item_id = None
        self.selected_item_ids.clear()

    def _process_batch(self, start_idx, end_idx):
        """アイテムバッチの処理（ListView固有の実装）"""
        try:
            # バッチ内のアイテムを処理
            for i in range(start_idx, end_idx):
                if i >= len(self.all_items):
                    break

                item = self.all_items[i]

                # リストアイテムを作成
                list_item = QListWidgetItem()
                item_id = self._get_item_id(item)
                list_item.setData(Qt.ItemDataRole.UserRole, item_id)  # アイテムIDを保存

                # カスタムウィジェットを作成
                widget = self._create_item_widget(item)

                # アイテムのサイズを設定
                list_item.setSizeHint(widget.sizeHint())

                # リストに追加
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, widget)

                # マップに追加（リストアイテムとカスタムウィジェットの両方を保存）
                self.item_widgets[item_id] = {"list_item": list_item, "widget": widget}
        except Exception as e:
            show_error_dialog(self, "Error", f"Error loading items: {str(e)}")
            print(f"Error in _process_batch: {e}")

    def _on_item_clicked(self, item):
        """
        リストアイテムがクリックされたときの処理。

        Parameters
        ----------
        item : QListWidgetItem
            クリックされたアイテム
        """
        item_id = item.data(Qt.ItemDataRole.UserRole)

        if self.multi_select_mode:
            # 複数選択モードの場合
            selected_items = self.list_widget.selectedItems()
            selected_ids = [
                item.data(Qt.ItemDataRole.UserRole) for item in selected_items
            ]
            # 選択IDセットを更新
            self.selected_item_ids = set(selected_ids)
            # 複数選択シグナルを発火
            self.items_selected.emit(selected_ids)
        else:
            # 単一選択モードの場合
            self.selected_item_id = item_id
            self.item_selected.emit(item_id)

    def _on_context_menu_requested(self, position):
        """
        コンテキストメニューが要求されたときの処理。

        Parameters
        ----------
        position : QPoint
            要求位置
        """
        item = self.list_widget.itemAt(position)
        if item:
            item_id = item.data(Qt.ItemDataRole.UserRole)

            # 複数選択されているか確認
            selected_items = self.list_widget.selectedItems()
            if len(selected_items) > 1 and item in selected_items:
                # 複数選択のコンテキストメニュー
                selected_ids = [
                    item.data(Qt.ItemDataRole.UserRole) for item in selected_items
                ]
                self._show_batch_context_menu(
                    self.list_widget.mapToGlobal(position), selected_ids
                )
            else:
                # 単一選択のコンテキストメニュー
                self._show_context_menu(self.list_widget.mapToGlobal(position), item_id)

    def _check_scroll_position(self, value):
        """スクロール位置をチェック"""
        # スクロールが下部に近づいたら追加読み込み
        scrollbar = self.list_widget.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:  # 70%以上スクロールしたら
            self.load_more_items()

    def toggle_multi_select_mode(self, enabled):
        """
        複数選択モードを切り替える。

        Parameters
        ----------
        enabled : bool
            複数選択モードを有効にするかどうか
        """
        super().toggle_multi_select_mode(enabled)

        # 選択モードを変更
        if enabled:
            self.list_widget.setSelectionMode(
                QListWidget.SelectionMode.ExtendedSelection
            )
        else:
            self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # 現在の選択をクリア
        self.list_widget.clearSelection()

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
        # 単一選択モードに戻す
        self.toggle_multi_select_mode(False)

        # item_idに一致するアイテムを検索
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == item_id:
                # アイテムを選択
                self.list_widget.setCurrentItem(item)

                # 選択状態を更新
                self.selected_item_id = item_id

                # シグナルを発火（オプション）
                if emit_signal:
                    self.item_selected.emit(item_id)
                break

    def get_selected_item_id(self):
        """
        現在選択されているアイテムIDを取得する。

        Returns
        -------
        int または None
            選択されているアイテムID、もしくは選択がない場合はNone
        """
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def get_selected_item_ids(self):
        """
        現在選択されている複数のアイテムIDリストを取得する。

        Returns
        -------
        list
            選択されているアイテムIDのリスト
        """
        selected_items = self.list_widget.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

    def select_all(self):
        """すべての表示されているアイテムを選択する。"""
        # 複数選択モードを有効化
        self.toggle_multi_select_mode(True)

        # すべてのアイテムを選択
        self.list_widget.selectAll()

        # 選択状態を更新
        selected_ids = self.get_selected_item_ids()
        self.selected_item_ids = set(selected_ids)

        # シグナルを発火
        if selected_ids:
            self.items_selected.emit(selected_ids)

    def update_item(self, item_id):
        """
        特定のアイテムを更新する。

        Parameters
        ----------
        item_id : int
            更新するアイテムID
        """
        if item_id in self.item_widgets:
            # アイテムを取得（サブクラスで実装）
            item = self._get_item_by_id(item_id)

            if item:
                # ウィジェットを更新（サブクラスで実装）
                widget_data = self.item_widgets[item_id]
                self._update_item_widget(item, widget_data["widget"])

    # サブクラスでオーバーライドすべきメソッド
    def _create_item_widget(self, item):
        """アイテムウィジェットを作成する（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclasses must implement _create_item_widget")

    def _get_item_id(self, item):
        """アイテムからIDを取得する（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclasses must implement _get_item_id")

    def _get_item_by_id(self, item_id):
        """IDからアイテムを取得する（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclasses must implement _get_item_by_id")

    def _update_item_widget(self, item, widget):
        """ウィジェットを更新する（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclasses must implement _update_item_widget")

    def _show_context_menu(self, position, item_id):
        """単一アイテムのコンテキストメニューを表示する（サブクラスでオーバーライド）"""
        pass

    def _show_batch_context_menu(self, position, item_ids):
        """複数アイテムのコンテキストメニューを表示する（サブクラスでオーバーライド）"""
        pass
