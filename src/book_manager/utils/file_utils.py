import logging
import os
import shutil


def ensure_dir(directory):
    """ディレクトリが存在することを確認し、存在しない場合は作成"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"ディレクトリを作成しました: {directory}")
    return directory


def copy_file(src, dst, overwrite=False):
    """ファイルをコピー"""
    if not os.path.exists(src):
        logging.error(f"コピー元ファイルが見つかりません: {src}")
        return False

    if os.path.exists(dst) and not overwrite:
        logging.warning(f"コピー先ファイルが既に存在します: {dst}")
        return False

    try:
        shutil.copy2(src, dst)
        logging.info(f"ファイルをコピーしました: {src} -> {dst}")
        return True
    except Exception as e:
        logging.error(f"ファイルコピーエラー: {e}")
        return False


def move_file(src, dst, overwrite=False):
    """ファイルを移動"""
    if not os.path.exists(src):
        logging.error(f"移動元ファイルが見つかりません: {src}")
        return False

    if os.path.exists(dst) and not overwrite:
        logging.warning(f"移動先ファイルが既に存在します: {dst}")
        return False

    try:
        shutil.move(src, dst)
        logging.info(f"ファイルを移動しました: {src} -> {dst}")
        return True
    except Exception as e:
        logging.error(f"ファイル移動エラー: {e}")
        return False


def delete_file(path):
    """ファイルを削除"""
    if not os.path.exists(path):
        logging.warning(f"削除するファイルが見つかりません: {path}")
        return False

    try:
        os.remove(path)
        logging.info(f"ファイルを削除しました: {path}")
        return True
    except Exception as e:
        logging.error(f"ファイル削除エラー: {e}")
        return False
