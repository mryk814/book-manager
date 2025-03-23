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
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Database Inspector")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.layout = QVBoxLayout(self)

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

        self.data_table = QTableWidget()
        self.layout.addWidget(self.data_table)

        self.load_table_data()

    def load_table_data(self):
        table_name = self.table_selector.currentText()

        conn = self.db_manager.connect()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        self.data_table.clear()
        self.data_table.setRowCount(len(rows))
        self.data_table.setColumnCount(len(columns))
        self.data_table.setHorizontalHeaderLabels(columns)

        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "NULL")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.data_table.setItem(i, j, item)

        self.data_table.resizeColumnsToContents()

        self.setWindowTitle(f"Database Inspector - {table_name} ({len(rows)} rows)")
