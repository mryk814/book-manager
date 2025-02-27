from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class CategoryManager(QDialog):
    """
    カテゴリを管理するためのダイアログ。

    カテゴリの追加、編集、削除などの機能を提供する。

    Parameters
    ----------
    library_controller : LibraryController
        ライブラリコントローラのインスタンス
    parent : QWidget, optional
        親ウィジェット
    """

    def __init__(self, library_controller, parent=None):
        """
        Parameters
        ----------
        library_controller : LibraryController
            ライブラリコントローラ
        parent : QWidget, optional
            親ウィジェット
        """
        super().__init__(parent)

        self.library_controller = library_controller

        self.setWindowTitle("Category Manager")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # レイアウトの設定
        self.layout = QHBoxLayout(self)

        # カテゴリリスト
        self.setup_category_list()

        # 編集フォーム
        self.setup_edit_form()

        # ボタン
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.button_box.rejected.connect(self.reject)

        # 編集フォームとボタンを垂直に配置
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.edit_group)
        right_layout.addWidget(self.button_box)

        self.layout.addWidget(self.category_list_group, 1)
        self.layout.addLayout(right_layout, 2)

        # カテゴリのロード
        self.load_categories()

    def setup_category_list(self):
        """カテゴリリストを設定する。"""
        self.category_list = QListWidget()
        self.category_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.category_list.currentItemChanged.connect(self.on_category_selected)

        # 操作ボタン
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_category)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_category)
        self.delete_button.setEnabled(False)  # 初期状態では無効
        button_layout.addWidget(self.delete_button)

        # リストと操作ボタンを配置するレイアウト
        list_layout = QVBoxLayout()
        list_layout.addWidget(self.category_list)
        list_layout.addLayout(button_layout)

        # グループボックスとして設定
        list_group = QGroupBox("Categories")
        list_group.setLayout(list_layout)

        self.category_list_group = list_group

    def setup_edit_form(self):
        """編集フォームを設定する。"""
        self.edit_group = QGroupBox("Edit Category")
        form_layout = QFormLayout(self.edit_group)

        # カテゴリ名
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        # 説明
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)

        # シリーズ数（表示のみ）
        self.series_count_label = QLabel("0 series")
        form_layout.addRow("Series Count:", self.series_count_label)

        # 更新ボタン
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_category)
        self.update_button.setEnabled(False)  # 初期状態では無効
        form_layout.addRow("", self.update_button)

        # 初期状態ではフォームを無効化
        self.edit_group.setEnabled(False)

    def load_categories(self):
        """カテゴリをロードしてリストに表示する。"""
        self.category_list.clear()

        categories = self.library_controller.get_all_categories()
        for category in categories:
            item = QListWidgetItem(category["name"])
            item.setData(Qt.ItemDataRole.UserRole, category["id"])
            self.category_list.addItem(item)

    def on_category_selected(self, current, previous):
        """
        カテゴリが選択されたときの処理。

        Parameters
        ----------
        current : QListWidgetItem
            現在選択されたアイテム
        previous : QListWidgetItem
            以前選択されていたアイテム
        """
        if current:
            category_id = current.data(Qt.ItemDataRole.UserRole)
            category = self.library_controller.get_category(category_id)

            if category:
                # 編集フォームを有効化
                self.edit_group.setEnabled(True)
                self.delete_button.setEnabled(True)
                self.update_button.setEnabled(True)

                # フォームに値を設定
                self.name_edit.setText(category["name"])
                self.description_edit.setText(category["description"] or "")

                # シリーズ数を取得して表示
                series_count = self._get_series_count(category_id)
                self.series_count_label.setText(f"{series_count} series")
            else:
                self.edit_group.setEnabled(False)
                self.delete_button.setEnabled(False)
                self.update_button.setEnabled(False)
        else:
            self.edit_group.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.update_button.setEnabled(False)

    def _get_series_count(self, category_id):
        """
        カテゴリに属するシリーズの数を取得する。

        Parameters
        ----------
        category_id : int
            カテゴリID

        Returns
        -------
        int
            シリーズの数
        """
        series_list = self.library_controller.get_all_series(category_id=category_id)
        return len(series_list)

    def add_category(self):
        """新しいカテゴリを追加する。"""
        # 新しいカテゴリをデフォルト名で作成
        category_id = self.library_controller.create_category("New Category")
        if category_id:
            # リストに追加
            item = QListWidgetItem("New Category")
            item.setData(Qt.ItemDataRole.UserRole, category_id)
            self.category_list.addItem(item)

            # 新しいカテゴリを選択
            self.category_list.setCurrentItem(item)

    def update_category(self):
        """選択されているカテゴリを更新する。"""
        current_item = self.category_list.currentItem()
        if not current_item:
            return

        category_id = current_item.data(Qt.ItemDataRole.UserRole)
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Category name cannot be empty.")
            return

        # カテゴリを更新
        success = self.library_controller.update_category(
            category_id, name, description
        )

        if success:
            # リストアイテムの表示を更新
            current_item.setText(name)
            QMessageBox.information(self, "Success", "Category updated successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to update category.")

    def delete_category(self):
        """選択されているカテゴリを削除する。"""
        current_item = self.category_list.currentItem()
        if not current_item:
            return

        category_id = current_item.data(Qt.ItemDataRole.UserRole)

        # カテゴリに所属する書籍とシリーズの数を取得
        series_count = self._get_series_count(category_id)
        book_count = self._get_book_count(category_id)

        if series_count > 0 or book_count > 0:
            message = f"This category is associated with {series_count} series and {book_count} individual books. "
            message += "If deleted, these items will no longer be associated with any category. "
            message += "Do you want to continue?"

            result = QMessageBox.question(
                self,
                "Confirm Delete",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if result != QMessageBox.StandardButton.Yes:
                return

        # カテゴリを削除
        success = self.library_controller.delete_category(category_id)

        if success:
            # リストから削除
            row = self.category_list.row(current_item)
            self.category_list.takeItem(row)

            # 編集フォームをクリア
            self.edit_group.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.update_button.setEnabled(False)

            QMessageBox.information(self, "Success", "Category deleted successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to delete category.")

    def _get_book_count(self, category_id):
        """
        カテゴリに直接属する書籍の数を取得する。

        Parameters
        ----------
        category_id : int
            カテゴリID

        Returns
        -------
        int
            書籍の数
        """
        conn = self.library_controller.db_manager.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) FROM books
            WHERE category_id = ?
            """,
            (category_id,),
        )

        return cursor.fetchone()[0]
