import hashlib
import mimetypes
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union


def get_pdf_files_in_directory(
    directory: Union[str, Path], recursive: bool = False
) -> List[str]:
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
