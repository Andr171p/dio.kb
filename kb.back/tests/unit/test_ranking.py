import random

import pytest

from src.domain.collections.ranking import rank_between


def test_ranks_stay_ordered_under_random_inserts() -> None:
    rng = random.Random(42)
    ranks = [rank_between(None, None)]

    for _ in range(2000):
        index = rng.randint(0, len(ranks))
        before = ranks[index - 1] if index > 0 else None
        after = ranks[index] if index < len(ranks) else None

        rank = rank_between(before, after)

        assert before is None or before < rank
        assert after is None or rank < after
        assert not rank.endswith("0")
        ranks.insert(index, rank)

    assert ranks == sorted(ranks)
    assert len(set(ranks)) == len(ranks)


def test_invalid_bounds_rejected() -> None:
    with pytest.raises(ValueError):
        rank_between("b", "a")
