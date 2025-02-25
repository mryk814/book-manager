import logging
import os
import re

import fitz  # PyMuPDF


def get_pdf_info(pdf_path):
    """PDFの基本情報を取得"""
    if not os.path.exists(pdf_path):
        logging.error(f"PDFファイルが見つかりません: {pdf_path}")
        return None

    try:
        doc = fitz.open(pdf_path)
        info = {
            "page_count": len(doc),
            "metadata": doc.metadata,
            "file_size": os.path.getsize(pdf_path),
        }
        doc.close()
        return info
    except Exception as e:
        logging.error(f"PDF情報取得エラー: {e}")
        return None


def extract_text(pdf_path, page_range=None):
    """PDFからテキストを抽出"""
    if not os.path.exists(pdf_path):
        logging.error(f"PDFファイルが見つかりません: {pdf_path}")
        return None

    try:
        doc = fitz.open(pdf_path)
        text = ""

        if page_range is None:
            # 全ページ
            for page in doc:
                text += page.get_text()
        else:
            # 指定ページ
            start, end = page_range
            start = max(0, start)
            end = min(len(doc) - 1, end)

            for i in range(start, end + 1):
                page = doc.load_page(i)
                text += page.get_text()

        doc.close()
        return text
    except Exception as e:
        logging.error(f"PDFテキスト抽出エラー: {e}")
        return None


def search_text(pdf_path, search_term, case_sensitive=False):
    """PDFからテキストを検索し、ヒットしたページを返す"""
    if not os.path.exists(pdf_path):
        logging.error(f"PDFファイルが見つかりません: {pdf_path}")
        return []

    try:
        doc = fitz.open(pdf_path)
        hits = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()

            if case_sensitive:
                if search_term in text:
                    hits.append(page_num)
            else:
                if search_term.lower() in text.lower():
                    hits.append(page_num)

        doc.close()
        return hits
    except Exception as e:
        logging.error(f"PDF検索エラー: {e}")
        return []
