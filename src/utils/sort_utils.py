import re
from typing import Any, Callable, List, Optional, TypeVar, Union

T = TypeVar("T")


def natural_sort_key(
    text: Union[str, Any], key_func: Optional[Callable[[Any], str]] = None
) -> List[Union[int, str]]:
    if key_func:
        text = key_func(text)

    if text is None:
        return []

    text_str = str(text)

    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", text_str)]


def sort_items_naturally(
    items: List[T], key_func: Optional[Callable[[T], str]] = None
) -> List[T]:
    if key_func:
        return sorted(items, key=lambda item: natural_sort_key(key_func(item)))
    return sorted(items, key=lambda item: natural_sort_key(str(item)))


def sort_books_by_series_order(books, series_id=None):
    def sort_key(book):
        if series_id is not None and book.series_id != series_id:
            return (1, float("inf"), natural_sort_key(book.title))

        order = float("inf") if book.series_order is None else book.series_order
        return (0, order, natural_sort_key(book.title))

    return sorted(books, key=sort_key)
