from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class DatabaseInspector(QDialog):
    """
    データベースの内容を直接確認するためのデバッグツール。
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Database Inspector")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # レイアウトの設定
        self.layout = QVBoxLayout(self)

        # テーブル選択
        self.table_selector = QComboBox()
        self.table_selector.addItems(
            ["books", "categories", "series", "reading_progress", "custom_metadata"]
        )
        self.table_selector.currentTextChanged.connect(self.load_table_data)

        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Select Table:"))
        select_layout.addWidget(self.table_selector)
        select_layout.addStretch()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_table_data)
        select_layout.addWidget(refresh_button)

        self.layout.addLayout(select_layout)

        # データテーブル
        self.data_table = QTableWidget()
        self.layout.addWidget(self.data_table)

        # 初期データのロード
        self.load_table_data()

    def load_table_data(self):
        """選択されたテーブルのデータをロードして表示する。"""
        table_name = self.table_selector.currentText()

        conn = self.db_manager.connect()
        cursor = conn.cursor()

        # テーブルの列情報を取得
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]

        # データを取得
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # テーブルをクリアして設定
        self.data_table.clear()
        self.data_table.setRowCount(len(rows))
        self.data_table.setColumnCount(len(columns))
        self.data_table.setHorizontalHeaderLabels(columns)

        # データを設定
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "NULL")
                item.setFlags(
                    item.flags() & ~Qt.ItemFlag.ItemIsEditable
                )  # 読み取り専用
                self.data_table.setItem(i, j, item)

        # 列の幅を調整
        self.data_table.resizeColumnsToContents()

        # テーブル情報を表示
        self.setWindowTitle(f"Database Inspector - {table_name} ({len(rows)} rows)")
