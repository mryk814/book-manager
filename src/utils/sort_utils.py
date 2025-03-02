import re
from typing import Any, Callable, List, Optional, TypeVar, Union

T = TypeVar("T")


def natural_sort_key(
    text: Union[str, Any], key_func: Optional[Callable[[Any], str]] = None
) -> List[Union[int, str]]:
    """
    テキスト内の数値を数値として扱うソートキー関数を提供する。

    Parameters
    ----------
    text : str または任意のオブジェクト
        ソートキーを生成するオブジェクト
    key_func : callable, optional
        オブジェクトから文字列を抽出する関数

    Returns
    -------
    list
        ソートに使用するキーのリスト（数値部分は整数として扱われる）

    Examples
    --------
    >>> sorted(["item1", "item10", "item2"], key=natural_sort_key)
    ["item1", "item2", "item10"]

    >>> books = [book1, book2, book3]  # book1.title = "Chapter 1", book2.title = "Chapter 10", etc.
    >>> sorted(books, key=lambda b: natural_sort_key(b.title))
    [book1, book3, book2]  # "Chapter 1", "Chapter 2", "Chapter 10" の順
    """
    if key_func:
        text = key_func(text)

    # 入力がNoneまたは空の場合は空リストを返す
    if text is None:
        return []

    # 文字列に変換
    text_str = str(text)

    # 数値部分を抽出して整数として扱い、それ以外を小文字にして返す
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", text_str)]


def sort_items_naturally(
    items: List[T], key_func: Optional[Callable[[T], str]] = None
) -> List[T]:
    """
    アイテムのリストを自然順にソートする。

    Parameters
    ----------
    items : list
        ソートするアイテムのリスト
    key_func : callable, optional
        各アイテムからソートに使用する文字列を抽出する関数

    Returns
    -------
    list
        自然順にソートされたリスト
    """
    if key_func:
        return sorted(items, key=lambda item: natural_sort_key(key_func(item)))
    return sorted(items, key=lambda item: natural_sort_key(str(item)))


def sort_books_by_series_order(books, series_id=None):
    """
    書籍をシリーズ順にソートする。
    シリーズ順が設定されていない書籍は末尾に配置され、タイトルで自然順ソートされる。

    Parameters
    ----------
    books : list
        ソートする書籍のリスト
    series_id : int, optional
        フィルタリングするシリーズID

    Returns
    -------
    list
        ソートされた書籍のリスト
    """

    def sort_key(book):
        # 指定されたシリーズに属していない場合は最後に
        if series_id is not None and book.series_id != series_id:
            return (1, float("inf"), natural_sort_key(book.title))

        # series_orderがNoneの場合は最後に、そうでなければその値を使用
        order = float("inf") if book.series_order is None else book.series_order
        return (0, order, natural_sort_key(book.title))

    return sorted(books, key=sort_key)
