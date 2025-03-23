import os
from pathlib import Path

import fitz  # PyMuPDF


class ImportController:
    """
    PDFファイルのインポートを管理するコントローラクラス。

    PDFファイルのインポート、バッチインポートなどの機能を提供する。

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

    def import_pdf(
        self,
        file_path,
        title=None,
        author=None,
        publisher=None,
        series_id=None,
        series_order=None,
        category_id=None,
    ):
        """
        PDFをライブラリにインポートする。

        Parameters
        ----------
        file_path : str
            PDFファイルへのパス
        title : str, optional
            書籍のタイトル（指定しない場合はファイル名から自動生成）
        author : str, optional
            著者名
        publisher : str, optional
            出版社名
        series_id : int, optional
            所属するシリーズのID
        series_order : int, optional
            シリーズ内の順番
        category_id : int, optional
            書籍のカテゴリID

        Returns
        -------
        int または None
            追加された書籍のID、もしくは失敗した場合はNone
        """
        if not os.path.isfile(file_path) or not file_path.lower().endswith(".pdf"):
            return None

        # タイトルが指定されていない場合はファイル名から生成
        if not title:
            title = Path(file_path).stem

        try:
            # ファイルを開いてメタデータを取得
            doc = fitz.open(file_path)

            # 著者が指定されていない場合はPDFから取得
            if not author and "author" in doc.metadata:
                author = doc.metadata["author"]

            # 総ページ数を取得
            total_pages = len(doc)

            # 表紙画像を取得
            cover_image = None
            if total_pages > 0:
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))  # 縮小して取得
                cover_image = pix.tobytes()

            doc.close()

            # データベースに書籍を追加
            book_id = self.db_manager.add_book(
                title=title,
                file_path=file_path,
                series_id=series_id,
                series_order=series_order,
                author=author,
                publisher=publisher,
                cover_image=cover_image,
                category_id=category_id,
            )

            # 総ページ数を更新
            self.db_manager.update_reading_progress(book_id, total_pages=total_pages)

            return book_id
        except Exception as e:
            print(f"Error importing PDF: {e}")
            return None

    def batch_import_pdfs(self, file_paths, common_metadata=None):
        """
        複数のPDFを一括インポートする。

        Parameters
        ----------
        file_paths : list
            PDFファイルへのパスのリスト
        common_metadata : dict, optional
            すべての書籍に適用する共通メタデータ

        Returns
        -------
        list
            インポートに成功した書籍IDのリスト
        """
        if common_metadata is None:
            common_metadata = {}

        imported_ids = []

        for file_path in file_paths:
            book_id = self.import_pdf(
                file_path=file_path,
                title=None,  # ファイル名から自動生成
                author=common_metadata.get("author"),
                publisher=common_metadata.get("publisher"),
                series_id=common_metadata.get("series_id"),
                series_order=None,  # 自動的に最後に追加
                category_id=common_metadata.get("category_id"),
            )

            if book_id:
                imported_ids.append(book_id)

                # カスタムメタデータがあれば設定
                custom_metadata = {
                    k: v
                    for k, v in common_metadata.items()
                    if k
                    not in [
                        "author",
                        "publisher",
                        "series_id",
                        "series_order",
                        "category_id",
                    ]
                }

                if custom_metadata:
                    for key, value in custom_metadata.items():
                        self.db_manager.set_custom_metadata(
                            book_id=book_id, key=key, value=value
                        )

        return imported_ids

    def validate_pdf(self, file_path):
        """
        PDFファイルが有効かどうかを検証する。

        Parameters
        ----------
        file_path : str
            検証するPDFファイルのパス

        Returns
        -------
        dict
            検証結果の辞書（成功かどうか、メッセージ、ページ数など）
        """
        result = {"valid": False, "message": "", "page_count": 0, "metadata": {}}

        if not os.path.isfile(file_path):
            result["message"] = "File does not exist"
            return result

        if not file_path.lower().endswith(".pdf"):
            result["message"] = "Not a PDF file"
            return result

        try:
            # PDFファイルを開いて検証
            doc = fitz.open(file_path)

            # 基本情報を取得
            result["valid"] = True
            result["page_count"] = len(doc)

            # メタデータを取得
            meta = doc.metadata
            if meta:
                if "title" in meta and meta["title"]:
                    result["metadata"]["title"] = meta["title"]
                if "author" in meta and meta["author"]:
                    result["metadata"]["author"] = meta["author"]
                if "subject" in meta and meta["subject"]:
                    result["metadata"]["subject"] = meta["subject"]
                if "keywords" in meta and meta["keywords"]:
                    result["metadata"]["keywords"] = meta["keywords"]
                if "creator" in meta and meta["creator"]:
                    result["metadata"]["creator"] = meta["creator"]
                if "producer" in meta and meta["producer"]:
                    result["metadata"]["producer"] = meta["producer"]

            doc.close()
        except Exception as e:
            result["message"] = f"Error validating PDF: {str(e)}"

        return result
