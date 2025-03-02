from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt6.QtWidgets import QGridLayout, QLabel, QScrollArea, QWidget

from utils.ui_utils import show_error_dialog
from views.base.base_view import BaseView


class BaseGridView(BaseView):
    """
    グリッドビューの基底クラス。
    アイテムをグリッド形式で表示する。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラーのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, library_controller, parent=None):
        super().__init__(library_controller, parent)

        # グリッドビュー固有のプロパティ
        self.grid_columns = 3  # デフォルトの列数
        self.item_width = 190  # アイテムの幅
        self.item_spacing = 10  # アイテム間のスペース
        self.last_viewport_width = 0  # 前回のビューポート幅

        # 表示範囲内のウィジェット追跡
        self.visible_widget_ids = set()
        self.loading_timer = None

        # UI初期化
        self._init_ui()

    def _init_ui(self):
        """UIコンポーネントを初期化する"""
        # スクロール可能なエリアとして設定
        self.setWidgetResizable(True)

        # コンテンツウィジェット
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        # グリッドレイアウト
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(self.item_spacing)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        # ロード中プレースホルダー
        self.placeholder = QLabel("Loading items...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

        # スクロールイベントを監視
        self.verticalScrollBar().valueChanged.connect(self._check_scroll_position)

        # 表示状態も監視
        self.installEventFilter(self)

    def resizeEvent(self, event):
        """ウィジェットのサイズが変わったときに呼ばれる"""
        super().resizeEvent(event)

        # ビューポートの現在の幅を取得
        current_width = self.viewport().width()

        # 前回と同じ幅なら何もしない
        if current_width == self.last_viewport_width:
            return

        self.last_viewport_width = current_width

        # 列数を更新
        self._calculate_grid_columns()

        # アイテムがロードされている場合のみ再レイアウト
        if self.item_widgets:
            self._relayout_grid()

    def eventFilter(self, obj, event):
        """表示イベントをフィルタリング"""
        if event.type() == QEvent.Type.Show:
            # 表示されたときに一度だけスクロール位置をチェック
            QTimer.singleShot(100, self._update_visible_widgets)
        return super().eventFilter(obj, event)

    def _calculate_grid_columns(self):
        """ビューポートの幅に基づいて列数を計算"""
        viewport_width = self.viewport().width()

        # 利用可能な幅を計算（マージンとスペース考慮）
        margins = self.grid_layout.contentsMargins()
        available_width = viewport_width - margins.left() - margins.right()
        spacing = self.grid_layout.spacing()

        # 列数を計算（最低1列）
        estimated_columns = max(
            1, int((available_width + spacing) / (self.item_width + spacing))
        )

        # 最小/最大制限を適用（オプション）
        min_columns = 1
        max_columns = 8
        new_columns = max(min_columns, min(max_columns, estimated_columns))

        # 列数が変わった場合に更新
        if new_columns != self.grid_columns:
            self.grid_columns = new_columns
            return True
        return False

    def _relayout_grid(self):
        """グリッドレイアウトを現在の列数で再レイアウト"""
        # 現在表示されているウィジェットを取得
        widgets = []
        for item_id, widget in self.item_widgets.items():
            # グリッドレイアウトからウィジェットを取り外す
            self.grid_layout.removeWidget(widget)
            widgets.append((item_id, widget))

        # 列数に基づいて再配置
        for i, (item_id, widget) in enumerate(widgets):
            row = i // self.grid_columns
            col = i % self.grid_columns
            self.grid_layout.addWidget(widget, row, col)

        # コンテンツウィジェットの更新を強制
        self.content_widget.updateGeometry()

        # 表示範囲内のウィジェットを更新
        QTimer.singleShot(50, self._update_visible_widgets)

    def _clear_view(self):
        """グリッドレイアウトをクリアする"""
        # すべての子ウィジェットを削除
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.item_widgets.clear()
        self.selected_item_id = None
        self.selected_item_ids.clear()
        self.visible_widget_ids.clear()

        # プレースホルダーを表示
        self.placeholder = QLabel("Loading items...")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 16px;")
        self.grid_layout.addWidget(self.placeholder, 0, 0)

    def _process_batch(self, start_idx, end_idx):
        """アイテムバッチの処理（GridView固有の実装）"""
        try:
            # プレースホルダーを削除
            if (
                hasattr(self, "placeholder")
                and self.placeholder.parent() == self.content_widget
            ):
                self.placeholder.setParent(None)
                self.placeholder.deleteLater()

            # バッチ内のアイテムを処理
            for i in range(start_idx, end_idx):
                if i >= len(self.all_items):
                    break

                item = self.all_items[i]
                row = i // self.grid_columns
                col = i % self.grid_columns

                # サブクラスで実装されるメソッド
                widget = self._create_item_widget(item)

                # グリッドに追加
                self.grid_layout.addWidget(widget, row, col)

                # アイテムIDを取得（サブクラスで実装）
                item_id = self._get_item_id(item)

                # マップに追加
                self.item_widgets[item_id] = widget
        except Exception as e:
            show_error_dialog(self, "Error", f"Error loading items: {str(e)}")
            print(f"Error in _process_batch: {e}")

    def _check_scroll_position(self, value):
        """スクロール位置をチェック"""
        # スクロールが下部に近づいたら追加読み込み
        scrollbar = self.verticalScrollBar()
        if value > scrollbar.maximum() * 0.7:  # 70%以上スクロールしたら
            self.load_more_items()

        # 表示範囲内のウィジェットを更新（連続スクロール時に最適化）
        if self.loading_timer:
            self.loading_timer.stop()

        self.loading_timer = QTimer()
        self.loading_timer.setSingleShot(True)
        self.loading_timer.timeout.connect(self._update_visible_widgets)
        self.loading_timer.start(100)  # 100ms後に実行

    def _update_visible_widgets(self):
        """現在表示範囲内にあるウィジェットを特定し、必要に応じて表示を最適化"""
        if not self.item_widgets:
            return

        # スクロール領域の表示範囲を取得
        viewport_rect = self.viewport().rect()
        scrollbar_value = self.verticalScrollBar().value()

        # 表示範囲を調整（スクロール位置を考慮）
        visible_top = scrollbar_value
        visible_bottom = scrollbar_value + viewport_rect.height()

        # 表示範囲内のウィジェットを特定
        new_visible_widgets = set()

        for item_id, widget in self.item_widgets.items():
            widget_pos = widget.mapTo(self.content_widget, QPoint(0, 0))
            widget_top = widget_pos.y()
            widget_bottom = widget_top + widget.height()

            # ウィジェットが表示範囲内にあるか判定
            if widget_bottom >= visible_top and widget_top <= visible_bottom:
                new_visible_widgets.add(item_id)

                # 必要に応じてウィジェットの表示を最適化（サブクラスで実装）
                self._optimize_visible_widget(item_id, widget)

        # 表示ウィジェットセットを更新
        self.visible_widget_ids = new_visible_widgets

    def _select_item(self, item_id, add_to_selection=False):
        """アイテムを選択状態にする"""
        if item_id not in self.item_widgets:
            return

        if not add_to_selection:
            self._clear_selection()

        # 選択状態を設定
        self.selected_item_ids.add(item_id)
        self._style_selected_widget(item_id)

    def _deselect_item(self, item_id):
        """アイテムの選択を解除する"""
        if item_id not in self.item_widgets:
            return

        if item_id in self.selected_item_ids:
            self.selected_item_ids.remove(item_id)
            self._style_deselected_widget(item_id)

    def _clear_selection(self):
        """すべての選択を解除する"""
        for item_id in list(self.selected_item_ids):
            self._deselect_item(item_id)

    def ensure_correct_layout(self):
        """現在のビューポートサイズに基づいて正しいレイアウトを確保する"""
        if self._calculate_grid_columns() and self.item_widgets:
            self._relayout_grid()

    # サブクラスでオーバーライドすべきメソッド
    def _create_item_widget(self, item):
        """アイテムウィジェットを作成する（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclasses must implement _create_item_widget")

    def _get_item_id(self, item):
        """アイテムからIDを取得する（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclasses must implement _get_item_id")

    def _optimize_visible_widget(self, item_id, widget):
        """表示範囲内のウィジェットを最適化する（サブクラスでオーバーライド）"""
        pass

    def _style_selected_widget(self, item_id):
        """選択されたウィジェットのスタイルを設定する（サブクラスでオーバーライド）"""
        if item_id in self.item_widgets:
            self.item_widgets[item_id].setStyleSheet(
                "background-color: #e0e0ff; border: 1px solid #9090ff;"
            )

    def _style_deselected_widget(self, item_id):
        """選択解除されたウィジェットのスタイルをリセットする（サブクラスでオーバーライド）"""
        if item_id in self.item_widgets:
            self.item_widgets[item_id].setStyleSheet("")
