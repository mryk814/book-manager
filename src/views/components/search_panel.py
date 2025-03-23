# src/views/components/search_panel.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QToolButton, QWidget


class SearchPanel(QWidget):
    """
    検索用のパネルウィジェット。

    検索ボックスとボタンを提供する。

    Parameters
    ----------
    parent : QWidget
        親ウィジェット
    """

    # 検索実行時に発するシグナル
    search_triggered = pyqtSignal(str)

    # クリアボタンクリック時に発するシグナル
    search_cleared = pyqtSignal()

    def __init__(self, parent=None):
        """
        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        # レイアウトの初期化
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        # 検索ボックス
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.returnPressed.connect(self._on_search)
        self.layout.addWidget(self.search_box)

        # クリアボタン
        self.clear_button = QToolButton()
        self.clear_button.setText("×")
        self.clear_button.setToolTip("Clear search")
        self.clear_button.clicked.connect(self._on_clear)
        self.layout.addWidget(self.clear_button)

        # 検索ボタン
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search)
        self.layout.addWidget(self.search_button)

        # 詳細検索ボタン
        self.advanced_button = QPushButton("Advanced...")
        self.advanced_button.clicked.connect(self._on_advanced_search)
        self.layout.addWidget(self.advanced_button)

        # 初期状態ではクリアボタンを非表示
        self.clear_button.setVisible(False)

        # 検索ボックスの内容が変更されたときのイベント接続
        self.search_box.textChanged.connect(self._on_text_changed)

    def _on_search(self):
        """検索ボタンクリック時またはEnterキー押下時のハンドラ"""
        query = self.search_box.text().strip()
        if query:
            self.search_triggered.emit(query)

    def _on_clear(self):
        """クリアボタンクリック時のハンドラ"""
        self.search_box.clear()
        self.search_cleared.emit()

    def _on_text_changed(self, text):
        """検索ボックスのテキスト変更時のハンドラ"""
        # テキストがある場合のみクリアボタンを表示
        self.clear_button.setVisible(bool(text))

    def _on_advanced_search(self):
        """詳細検索ボタンクリック時のハンドラ"""
        # 詳細検索ダイアログを表示（実装は別途必要）
        # self.parent().on_advanced_search()
        pass

    def set_search_text(self, text):
        """
        検索ボックスのテキストを設定する

        Parameters
        ----------
        text : str
            設定するテキスト
        """
        self.search_box.setText(text)

    def get_search_text(self):
        """
        検索ボックスのテキストを取得する

        Returns
        -------
        str
            検索ボックスのテキスト
        """
        return self.search_box.text()
