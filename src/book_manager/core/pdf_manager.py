import hashlib
import io
import logging
import os
import re
from datetime import datetime

import fitz  # PyMuPDF
from PIL import Image


class PDFManager:
    """PDFファイル処理を管理するクラス"""

    def __init__(self, thumbnail_dir):
        """
        PDFマネージャーの初期化

        Args:
            thumbnail_dir (str): サムネイル保存ディレクトリ
        """
        self.thumbnail_dir = thumbnail_dir
        os.makedirs(thumbnail_dir, exist_ok=True)
        logging.info(f"サムネイルディレクトリ: {thumbnail_dir}")

    def extract_metadata(self, pdf_path):
        """
        PDFからメタデータを抽出

        Args:
            pdf_path (str): PDFファイルのパス

        Returns:
            dict: 抽出されたメタデータ
        """
        try:
            print(f"PDFファイルを開こうとしています: {pdf_path}")  # デバッグ情報
            if not os.path.exists(pdf_path):
                logging.error(f"PDFファイルが存在しません: {pdf_path}")
                return None

            doc = fitz.open(pdf_path)
            metadata = {}

            # 基本メタデータの抽出
            pdf_metadata = doc.metadata
            if pdf_metadata:
                metadata["title"] = pdf_metadata.get("title", "")
                metadata["author"] = pdf_metadata.get("author", "")
                # 'subject'フィールドは利用しない（Bookモデルに存在しないため）
                # metadata['subject'] = pdf_metadata.get('subject', '')
                # 'keywords'フィールドは利用しない（Bookモデルに存在しないため）
                # metadata['keywords'] = pdf_metadata.get('keywords', '')

                # キーワードからタグを抽出（あれば）
                keywords = pdf_metadata.get("keywords", "")
                if keywords:
                    metadata["tags"] = [
                        kw.strip() for kw in keywords.split(",") if kw.strip()
                    ]

                # 日付の処理
                if "creationDate" in pdf_metadata and pdf_metadata["creationDate"]:
                    date_str = pdf_metadata["creationDate"]
                    date_match = re.search(r"D:(\d{4})(\d{2})(\d{2})", date_str)
                    if date_match:
                        year, month, day = date_match.groups()
                        metadata["publication_date"] = f"{year}-{month}-{day}"

            # タイトルがない場合はファイル名から取得
            if not metadata.get("title"):
                file_name = os.path.basename(pdf_path)
                base_name = os.path.splitext(file_name)[0]

                # シリーズと巻数を検出する簡易的なパターン
                series_vol_pattern = re.search(r"(.+?)[\s_-]*(\d+)$", base_name)
                if series_vol_pattern:
                    metadata["title"] = base_name
                    metadata["series_name"] = series_vol_pattern.group(1).strip()
                    metadata["volume_number"] = int(series_vol_pattern.group(2))
                else:
                    metadata["title"] = base_name

            # ページ数
            metadata["page_count"] = len(doc)

            # ファイルパス
            metadata["file_path"] = pdf_path

            # サムネイル生成
            thumbnail_path = self.generate_thumbnail(doc, pdf_path)
            if thumbnail_path:
                metadata["thumbnail_path"] = thumbnail_path

            doc.close()
            print(f"メタデータ抽出成功: {metadata.get('title')}")  # デバッグ情報
            return metadata

        except Exception as e:
            logging.error(f"メタデータ抽出エラー ({pdf_path}): {e}")
            print(f"メタデータ抽出エラー: {e}")  # デバッグ情報
            # 最低限の情報を返す
            file_name = os.path.basename(pdf_path)
            base_name = os.path.splitext(file_name)[0]
            return {"title": base_name, "file_path": pdf_path, "page_count": 0}

    def generate_thumbnail(self, doc, pdf_path, page_num=0, width=200, height=300):
        """
        PDFの表紙サムネイルを生成

        Args:
            doc (fitz.Document): PDFドキュメント
            pdf_path (str): PDFファイルのパス
            page_num (int): サムネイルに使用するページ番号
            width (int): サムネイル幅
            height (int): サムネイル高さ

        Returns:
            str: 生成されたサムネイルのパス
        """
        try:
            if page_num >= len(doc):
                page_num = 0

            # ファイル名からハッシュを生成
            file_hash = hashlib.md5(pdf_path.encode()).hexdigest()
            thumbnail_filename = f"{file_hash}.jpg"
            thumbnail_path = os.path.join(self.thumbnail_dir, thumbnail_filename)

            # サムネイルが既に存在する場合はパスを返す
            if os.path.exists(thumbnail_path):
                return thumbnail_path

            # 最初のページをレンダリング
            page = doc.load_page(page_num)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            # PILで画像を処理
            img = Image.open(io.BytesIO(pixmap.tobytes()))
            img.thumbnail((width, height), Image.LANCZOS)
            img.save(thumbnail_path, "JPEG", quality=90)

            return thumbnail_path

        except Exception as e:
            logging.error(f"サムネイル生成エラー ({pdf_path}): {e}")
            return None

    def get_page_image(self, pdf_path, page_num, zoom=1.0):
        """
        指定ページの画像を取得

        Args:
            pdf_path (str): PDFファイルのパス
            page_num (int): ページ番号
            zoom (float): ズーム倍率

        Returns:
            PIL.Image: ページ画像
        """
        try:
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                page_num = 0

            page = doc.load_page(page_num)
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            img = Image.open(io.BytesIO(pixmap.tobytes()))
            doc.close()
            return img

        except Exception as e:
            logging.error(f"ページ画像取得エラー ({pdf_path}, ページ {page_num}): {e}")
            return None

    def get_document(self, pdf_path):
        """
        PDFドキュメントを開く

        Args:
            pdf_path (str): PDFファイルのパス

        Returns:
            fitz.Document: PDFドキュメント
        """
        try:
            return fitz.open(pdf_path)
        except Exception as e:
            logging.error(f"PDFを開けませんでした ({pdf_path}): {e}")
            return None
