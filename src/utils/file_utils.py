import hashlib
import mimetypes
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union


def get_file_hash(
    file_path: str, algorithm: str = "md5", chunk_size: int = 8192
) -> str:
    """
    ファイルのハッシュ値を計算する。

    Parameters
    ----------
    file_path : str
        ハッシュを計算するファイルのパス
    algorithm : str, optional
        使用するハッシュアルゴリズム ('md5', 'sha1', 'sha256')
    chunk_size : int, optional
        一度に読み込むバイト数

    Returns
    -------
    str
        計算されたハッシュ値の16進数表現
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = None
    if algorithm == "md5":
        hash_obj = hashlib.md5()
    elif algorithm == "sha1":
        hash_obj = hashlib.sha1()
    elif algorithm == "sha256":
        hash_obj = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    with open(file_path, "rb") as f:
        chunk = f.read(chunk_size)
        while chunk:
            hash_obj.update(chunk)
            chunk = f.read(chunk_size)

    return hash_obj.hexdigest()


def get_pdf_files_in_directory(
    directory: Union[str, Path], recursive: bool = False
) -> List[str]:
    """
    ディレクトリ内のすべてのPDFファイルのパスを返す。

    Parameters
    ----------
    directory : str or Path
        検索するディレクトリのパス
    recursive : bool, optional
        サブディレクトリも再帰的に検索するかどうか

    Returns
    -------
    list of str
        ディレクトリ内のPDFファイルのパスのリスト
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    pdf_files = []

    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))
    else:
        for file in directory.iterdir():
            if file.is_file() and file.suffix.lower() == ".pdf":
                pdf_files.append(str(file))

    return pdf_files


def get_file_mime_type(file_path: str) -> Tuple[str, Optional[str]]:
    """
    ファイルのMIMEタイプを返す。

    Parameters
    ----------
    file_path : str
        MIMEタイプを判定するファイルのパス

    Returns
    -------
    tuple
        (主要タイプ, サブタイプ)のタプル、判定できない場合はサブタイプはNone
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type.split("/")

    # 拡張子から判断
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return ("application", "pdf")

    return ("application", "octet-stream")
