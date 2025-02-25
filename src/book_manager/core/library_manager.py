import concurrent.futures
import logging
import os
import time
from datetime import datetime
from pathlib import Path


class LibraryManager:
    """ライブラリを管理するクラス"""

    def __init__(self, db_manager, pdf_manager, config):
        """
        ライブラリマネージャーの初期化

        Args:
            db_manager: データベースマネージャー
            pdf_manager: PDFマネージャー
            config: 設定マネージャー
        """
        self.db = db_manager
        self.pdf = pdf_manager
        self.config = config
        self.is_scanning = False
        logging.info("ライブラリマネージャーを初期化")

    def scan_directory(self, directory_path, callback=None):
        """
        ディレクトリをスキャンしてPDFファイルをインポート

        Args:
            directory_path (str): スキャンするディレクトリパス
            callback (function): 進捗報告用コールバック関数

        Returns:
            dict: インポート結果 {'added': 数, 'skipped': 数, 'failed': 数}
        """
        if self.is_scanning:
            logging.warning("既にスキャン中です")
            return {"added": 0, "skipped": 0, "failed": 0}

        self.is_scanning = True
        result = {"added": 0, "skipped": 0, "failed": 0}

        try:
            # PDFファイルを再帰的に検索
            pdf_files = []
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, file))

            total_files = len(pdf_files)
            if total_files == 0:
                logging.info(f"PDFファイルが見つかりませんでした: {directory_path}")
                return result

            logging.info(
                f"{total_files}件のPDFファイルをスキャンします: {directory_path}"
            )

            # 各ファイルを処理
            for i, pdf_path in enumerate(pdf_files):
                progress = (i + 1) / total_files * 100
                try:
                    # 既存の書籍をチェック
                    existing_book = self.db.get_book_by_path(pdf_path)
                    if existing_book:
                        result["skipped"] += 1
                        if callback:
                            callback(
                                progress,
                                f"スキップ: {os.path.basename(pdf_path)}",
                                total_files,
                                i + 1,
                            )
                        continue

                    # メタデータを抽出してインポート
                    metadata = self.pdf.extract_metadata(pdf_path)
                    if not metadata:
                        result["failed"] += 1
                        logging.warning(f"メタデータの抽出に失敗: {pdf_path}")
                        continue

                    # 書籍を追加
                    self.db.add_book(metadata)
                    result["added"] += 1

                    if callback:
                        callback(
                            progress,
                            f"インポート: {metadata.get('title')}",
                            total_files,
                            i + 1,
                        )

                except Exception as e:
                    result["failed"] += 1
                    logging.error(f"PDFのインポートエラー ({pdf_path}): {e}")
                    if callback:
                        callback(
                            progress,
                            f"エラー: {os.path.basename(pdf_path)}",
                            total_files,
                            i + 1,
                        )

            logging.info(
                f"スキャン完了: 追加={result['added']}, スキップ={result['skipped']}, 失敗={result['failed']}"
            )
            return result

        except Exception as e:
            logging.error(f"ディレクトリスキャンエラー: {e}")
            return result

        finally:
            self.is_scanning = False

    def scan_all_libraries(self, callback=None):
        """
        全てのライブラリディレクトリをスキャン

        Args:
            callback (function): 進捗報告用コールバック関数

        Returns:
            dict: インポート結果 {'added': 数, 'skipped': 数, 'failed': 数}
        """
        library_paths = self.config.get_all_library_paths()
        total_result = {"added": 0, "skipped": 0, "failed": 0}

        for path in library_paths:
            if os.path.exists(path):
                result = self.scan_directory(path, callback)
                total_result["added"] += result["added"]
                total_result["skipped"] += result["skipped"]
                total_result["failed"] += result["failed"]
            else:
                logging.warning(f"ライブラリパスが存在しません: {path}")

        return total_result

    def import_file(self, file_path):
        """
        単一のPDFファイルをインポート

        Args:
            file_path (str): PDFファイルのパス

        Returns:
            Book: インポートされた書籍オブジェクト、失敗時はNone
        """
        try:
            print(f"ファイルのインポートを試みています: {file_path}")  # デバッグ情報
            if not os.path.exists(file_path):
                logging.error(f"ファイルが存在しません: {file_path}")
                print(f"ファイルが存在しません: {file_path}")  # デバッグ情報
                return None

            if not file_path.lower().endswith(".pdf"):
                logging.error(f"PDFファイルではありません: {file_path}")
                print(f"PDFファイルではありません: {file_path}")  # デバッグ情報
                return None

            # 既存の書籍をチェック
            existing_book = self.db.get_book_by_path(file_path)
            if existing_book:
                logging.info(f"既存の書籍をスキップ: {file_path}")
                print(f"既存の書籍をスキップ: {file_path}")  # デバッグ情報
                return existing_book

            # メタデータを抽出してインポート
            metadata = self.pdf.extract_metadata(file_path)
            if not metadata:
                logging.warning(f"メタデータの抽出に失敗: {file_path}")
                print(f"メタデータの抽出に失敗: {file_path}")  # デバッグ情報
                return None

            # 書籍を追加
            book = self.db.add_book(metadata)
            logging.info(f"PDFをインポートしました: {metadata.get('title')}")
            print(f"PDFをインポートしました: {metadata.get('title')}")  # デバッグ情報
            return book

        except Exception as e:
            logging.error(f"PDFのインポートエラー ({file_path}): {e}")
            print(f"PDFのインポートエラー: {e}")  # デバッグ情報
            import traceback

            traceback.print_exc()  # スタックトレースを出力
            return None

    def update_book_metadata(self, book_id, metadata):
        """
        書籍のメタデータを更新

        Args:
            book_id (int): 書籍ID
            metadata (dict): 更新するメタデータ

        Returns:
            Book: 更新された書籍オブジェクト
        """
        return self.db.update_book(book_id, metadata)

    def delete_book(self, book_id, delete_file=False):
        """
        書籍を削除

        Args:
            book_id (int): 書籍ID
            delete_file (bool): ファイルも削除するか

        Returns:
            bool: 削除成功の場合True
        """
        book = self.db.get_book(book_id)
        if not book:
            return False

        file_path = book.file_path

        # データベースからの削除
        if not self.db.delete_book(book_id):
            return False

        # ファイルの削除（オプション）
        if delete_file and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"ファイルを削除しました: {file_path}")
            except Exception as e:
                logging.error(f"ファイル削除エラー ({file_path}): {e}")
                return False

        return True

    def check_missing_files(self):
        """
        不明なファイルをチェック

        Returns:
            list: 存在しないファイルパスを持つ書籍のリスト
        """
        all_books = self.db.get_all_books()
        missing_books = []

        for book in all_books:
            if not os.path.exists(book.file_path):
                missing_books.append(book)

        return missing_books

    def update_file_path(self, book_id, new_path):
        """
        書籍のファイルパスを更新

        Args:
            book_id (int): 書籍ID
            new_path (str): 新しいファイルパス

        Returns:
            Book: 更新された書籍オブジェクト
        """
        if not os.path.exists(new_path) or not new_path.lower().endswith(".pdf"):
            logging.error(f"無効なPDFファイル: {new_path}")
            return None

        return self.db.update_book(book_id, {"file_path": new_path})

    def update_reading_progress(self, book_id, current_page):
        """
        読書進捗を更新

        Args:
            book_id (int): 書籍ID
            current_page (int): 現在のページ

        Returns:
            Book: 更新された書籍オブジェクト
        """
        book = self.db.get_book(book_id)
        if not book:
            return None

        # ページ範囲をチェック
        current_page = max(0, min(current_page, book.page_count - 1))

        # 読書状態の更新
        reading_status = book.reading_status
        if current_page > 0:
            reading_status = "読書中"
            if current_page >= book.page_count - 1:
                reading_status = "読了"

        return self.db.update_book(
            book_id,
            {
                "current_page": current_page,
                "reading_status": reading_status,
                "last_read": datetime.now(),
            },
        )

    def get_book_statistics(self):
        """
        ライブラリの統計情報を取得

        Returns:
            dict: 統計情報
        """
        all_books = self.db.get_all_books()

        # 基本統計
        total_books = len(all_books)
        total_series = len(self.db.get_all_series())
        total_tags = len(self.db.get_all_tags())

        # 読書状態
        unread_count = sum(1 for book in all_books if book.reading_status == "未読")
        reading_count = sum(1 for book in all_books if book.reading_status == "読書中")
        completed_count = sum(1 for book in all_books if book.reading_status == "読了")

        # お気に入り
        favorites_count = sum(1 for book in all_books if book.is_favorite)

        # 合計ページ数
        total_pages = sum(book.page_count for book in all_books if book.page_count)

        return {
            "total_books": total_books,
            "total_series": total_series,
            "total_tags": total_tags,
            "unread": unread_count,
            "reading": reading_count,
            "completed": completed_count,
            "favorites": favorites_count,
            "total_pages": total_pages,
        }
