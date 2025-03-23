# src/views/components/filter_panel.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget


class FilterPanel(QWidget):
    """
    フィルタ操作用のパネルウィジェット。

    カテゴリ、シリーズ、読書状態などによるフィルタリング機能を提供する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    library_controller : LibraryController
        ライブラリコントローラ
    """

    # フィルタ変更時に発するシグナル
    filter_changed = pyqtSignal(dict)

    def __init__(self, parent=None, library_controller=None):
        """
        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェット
        library_controller : LibraryController, optional
            ライブラリコントローラ
        """
        super().__init__(parent)

        self.library_controller = library_controller

        # 現在のフィルタ状態
        self.current_filters = {"category_id": None, "series_id": None, "status": None}

        # レイアウトの初期化
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # カテゴリフィルター
        self.layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        self.layout.addWidget(self.category_combo)

        # シリーズフィルター
        self.layout.addWidget(QLabel("Series:"))
        self.series_combo = QComboBox()
        self.series_combo.addItem("All Series", None)
        self.layout.addWidget(self.series_combo)

        # 読書状態フィルター
        self.layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("All Status", None)
        self.status_combo.addItem("Unread", "unread")
        self.status_combo.addItem("Reading", "reading")
        self.status_combo.addItem("Completed", "completed")
        self.layout.addWidget(self.status_combo)

        # 右側に余白を追加
        self.layout.addStretch(1)

        # シグナル接続
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self.series_combo.currentIndexChanged.connect(self._on_series_changed)
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)

        # データロード
        if self.library_controller:
            self._load_categories()
            self._load_series()

    def _load_categories(self):
        """カテゴリデータをロードしてコンボボックスに設定する"""
        if not self.library_controller:
            return

        # 現在選択されているカテゴリIDを保存
        current_id = self.category_combo.currentData()

        # コンボボックスをクリア
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)

        # カテゴリデータをロード
        categories = self.library_controller.category_controller.get_all_categories()
        for category in categories:
            self.category_combo.addItem(category["name"], category["id"])

        # 以前選択していたカテゴリを再選択
        if current_id is not None:
            index = self.category_combo.findData(current_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def _load_series(self, category_id=None):
        """
        シリーズデータをロードしてコンボボックスに設定する

        Parameters
        ----------
        category_id : int, optional
            カテゴリID（指定した場合はそのカテゴリに属するシリーズのみ表示）
        """
        if not self.library_controller:
            return

        # 現在選択されているシリーズIDを保存
        current_id = self.series_combo.currentData()

        # コンボボックスをクリア
        self.series_combo.clear()
        self.series_combo.addItem("All Series", None)

        # シリーズデータをロード
        series_list = self.library_controller.series_controller.get_all_series(
            category_id
        )
        for series in series_list:
            self.series_combo.addItem(series.name, series.id)

        # 以前選択していたシリーズを再選択
        if current_id is not None:
            index = self.series_combo.findData(current_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)

    def _on_category_changed(self, index):
        """
        カテゴリ選択変更時のハンドラ

        Parameters
        ----------
        index : int
            選択されたインデックス
        """
        category_id = self.category_combo.itemData(index)
        self.current_filters["category_id"] = category_id

        # カテゴリが変更されたらシリーズリストを更新
        self._load_series(category_id)

        # フィルタ変更を通知
        self.filter_changed.emit(self.current_filters)

    def _on_series_changed(self, index):
        """
        シリーズ選択変更時のハンドラ

        Parameters
        ----------
        index : int
            選択されたインデックス
        """
        series_id = self.series_combo.itemData(index)
        self.current_filters["series_id"] = series_id

        # フィルタ変更を通知
        self.filter_changed.emit(self.current_filters)

    def _on_status_changed(self, index):
        """
        読書状態選択変更時のハンドラ

        Parameters
        ----------
        index : int
            選択されたインデックス
        """
        status = self.status_combo.itemData(index)
        self.current_filters["status"] = status

        # フィルタ変更を通知
        self.filter_changed.emit(self.current_filters)

    def set_filter(self, category_id=None, series_id=None, status=None):
        """
        フィルタを設定する

        Parameters
        ----------
        category_id : int, optional
            カテゴリID
        series_id : int, optional
            シリーズID
        status : str, optional
            読書状態
        """
        # カテゴリを設定
        if category_id is not None:
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        # シリーズを設定
        if series_id is not None:
            index = self.series_combo.findData(series_id)
            if index >= 0:
                self.series_combo.setCurrentIndex(index)

        # 読書状態を設定
        if status is not None:
            index = self.status_combo.findData(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
