import os

# 作成するディレクトリとファイルの構造定義
structure = {
    "pdf_library_manager": [
        "main.py",
        "requirements.txt",
    ],
    "pdf_library_manager/models": [
        "__init__.py",
        "database.py",
        "book.py",
        "series.py",
        "metadata.py",
    ],
    "pdf_library_manager/views": [
        "__init__.py",
        "main_window.py",
        "library_view.py",
        "reader_view.py",
        "metadata_editor.py",
    ],
    "pdf_library_manager/views/dialogs": [
        "__init__.py",
        "import_dialog.py",
        "settings_dialog.py",
    ],
    "pdf_library_manager/controllers": [
        "__init__.py",
        "library_controller.py",
        "reader_controller.py",
        "search_controller.py",
    ],
    "pdf_library_manager/utils": [
        "__init__.py",
        "file_utils.py",
        "pdf_utils.py",
        "config.py",
    ],
    "pdf_library_manager/resources": [],
    "pdf_library_manager/resources/icons": [],
    "pdf_library_manager/resources/styles": [],
}


def create_structure():
    for folder, files in structure.items():
        # フォルダを作成（既に存在してもOK）
        os.makedirs(folder, exist_ok=True)
        print(f"Created directory: {folder} 😊")
        for file in files:
            file_path = os.path.join(folder, file)
            # ファイルが存在しなかったら新規作成
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("")  # 空ファイルを作成
                print(f"  Created file: {file_path} 💖")
            else:
                print(f"  File already exists: {file_path} ✨")


if __name__ == "__main__":
    create_structure()
    print("全てのディレクトリとファイルが作成されたよ〜！😆👍")
