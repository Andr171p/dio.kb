"""
Генерация лексикографических рангов (Fractional Indexing) для сортировки коллекций.

Модуль предназначен для реализации пользовательского порядка элементов (например,
drag-and-drop в UI) без необходимости пересчитывать позиции соседних записей в БД.

Требования к хранению:
    Ранги представляют собой строки в алфавите Base62 (``0-9``, ``A-Z``, ``a-z``).
    Сравнение строк должно выполняться строго побайтно (по кодам ASCII).
    В PostgreSQL для колонки ранга обязательно указывать ``COLLATE "C"`` (или ``bytea``),
    иначе сортировка будет зависеть от локали ОС и нарушит порядок.

Инварианты:
    1. Для любых валидных строк ``a < b`` выполняется ``a < rank_between(a, b) < b``.
    2. Валидный ранг никогда не бывает пустой строкой и не оканчивается на ``'0'``.
"""

from typing import Literal

import string
from itertools import takewhile, zip_longest

_DIGITS = string.digits + string.ascii_uppercase + string.ascii_lowercase

_ZERO = _DIGITS[0]
_BASE = len(_DIGITS)
_DIGIT_INDEX = {char: idx for idx, char in enumerate(_DIGITS)}


def _validate_rank(rank: str | None, bound_name: Literal["after", "before"]) -> None:
    """Проверяет, что ранг состоит из символов Base62 и не оканчивается на '0'."""

    if rank is None:
        return

    if not rank.strip():
        raise ValueError(f"Parameter {bound_name!r} cannot be an empty string.")

    if rank.endswith(_ZERO):
        raise ValueError(f"Invariant violated in  {bound_name!r}: rank {rank!r} cannot end with {_ZERO!r}.")

    if not all(char in _DIGIT_INDEX for char in rank):
        raise ValueError(f"Parameter {bound_name!r} contains invalid characters: {rank!r}.")


def _midpoint(left: str, right: str | None) -> str:
    if right is not None:
        prefix_length = sum(
            1 for _ in takewhile(lambda pair: pair[0] == pair[1], zip_longest(left, right, fillvalue=_ZERO))
        )

        if prefix_length > 0:
            return right[:prefix_length] + _midpoint(left[prefix_length:], right[prefix_length:])

    left_digit = _DIGIT_INDEX[left[0]] if left else 0
    right_digit = _DIGIT_INDEX[right[0]] if right is not None else _BASE

    # Если между цифрами есть зазор хотя бы в 2 единицы - берем середину
    if right_digit - left_digit > 1:
        return _DIGITS[(left_digit + right_digit) // 2]

    # Если зазора нет, но у правой границы есть хвост - спускаемся на разряд глубже
    if right is not None and len(right) > 1:
        return right[0]

    # Иначе фиксируем левую цифру и ищем середину в следующем разряде
    return _DIGITS[left_digit] + _midpoint(left[1:], None)


def rank_between(before: str | None, after: str | None) -> str:
    """Вычисляет новый ранг, находящийся строго между ``before`` и ``after``.

    Args:
        before: Ранг предыдущего элемента или ``None``, если вставка идет в начало списка.
        after: Ранг следующего элемента или ``None``, если вставка идет в конец списка.

    Returns:
        Новая строка ранга, для которой гарантируется ``before < result < after``.

    Raises:
        ValueError: Если ``before >= after``, передана пустая строка или нарушен
            формат Base62 / инвариант отсутствия ``'0'`` на конце.

    Examples:
        >>> rank_between(None, None)  # Первый элемент в пустом списке
        'V'
        >>> rank_between(None, "V")  # Вставка в начало
        'F'
        >>> rank_between("V", None)  # Вставка в конец
        'l'
        >>> rank_between("F", "V")  # Вставка между двумя элементами
        'N'
    """

    _validate_rank(before, "before")
    _validate_rank(after, "after")

    if before is not None and after is not None and before >= after:
        raise ValueError(f"Invalid rank bounds: {before!r} >= {after!r}.")

    return _midpoint(before or "", after)


__all__ = ["rank_between"]
