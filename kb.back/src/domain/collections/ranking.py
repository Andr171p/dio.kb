"""
Дробная индексация (fractional indexing) для порядка элементов коллекции.

Ранги — строки из цифр base62, сравниваемые побайтно (в PostgreSQL колонка с ``COLLATE "C"``).
Между любыми двумя рангами всегда можно вставить новый без перенумерации соседей.
Инвариант: ранг никогда не оканчивается на минимальную цифру ``0``.
"""

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _midpoint(left: str, right: str | None) -> str:
    if right is not None:
        prefix_length = 0
        while (
            prefix_length < len(right)
            and (left[prefix_length : prefix_length + 1] or DIGITS[0]) == right[prefix_length]
        ):
            prefix_length += 1

        if prefix_length > 0:
            return right[:prefix_length] + _midpoint(left[prefix_length:], right[prefix_length:])

    left_digit = DIGITS.index(left[0]) if left else 0
    right_digit = DIGITS.index(right[0]) if right is not None else len(DIGITS)

    if right_digit - left_digit > 1:
        return DIGITS[(left_digit + right_digit) // 2]

    if right is not None and len(right) > 1:
        return right[0]

    return DIGITS[left_digit] + _midpoint(left[1:], None)


def rank_between(before: str | None, after: str | None) -> str:
    """Возвращает ранг строго между ``before`` и ``after`` (``None`` — открытая граница)."""

    if before is not None and after is not None and before >= after:
        raise ValueError(f"Invalid rank bounds: {before!r} >= {after!r}.")

    return _midpoint(before or "", after)


__all__ = ["rank_between"]
