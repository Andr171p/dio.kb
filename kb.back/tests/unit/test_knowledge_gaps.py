from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.knowledge_gaps.config import KnowledgeGapsConfig
from src.application.knowledge_gaps.detection import build_candidate, detect_gaps
from src.application.knowledge_gaps.dtos import GapCandidate
from src.application.knowledge_gaps.grouping import group_signals, grouping_key_for, normalize_topic_hint
from src.application.knowledge_gaps.signals import GapSignal, GapSignalKind, GapSignalSourceType
from src.domain.knowledge_gaps.models import KnowledgeGap
from src.domain.knowledge_gaps.types import GapKind, GapStatus


def _signal(*, kind=GapSignalKind.ANSWER_INSUFFICIENT, hint="http 401 auth", org=None):
    return GapSignal(
        id=uuid4(),
        organization_id=org or uuid4(),
        kind=kind,
        source_type=GapSignalSourceType.ANSWER_RUN,
        source_id=uuid4(),
        occurred_at=datetime.now(UTC),
        answer_id=uuid4(),
        topic_hint=hint,
    )


def test_normalize_topic_hint():
    assert normalize_topic_hint("  HTTP  401!!! ") == "http 401"
    assert normalize_topic_hint("   ") is None


def test_grouping_same_hint_same_key():
    org = uuid4()
    a = _signal(org=org, hint="VPN не подключается")
    b = _signal(org=org, hint="vpn не подключается")
    assert grouping_key_for(a) == grouping_key_for(b)


def test_group_signals_splits_different_kinds():
    org = uuid4()
    signals = [
        _signal(org=org, kind=GapSignalKind.ANSWER_INSUFFICIENT, hint="printer"),
        _signal(org=org, kind=GapSignalKind.SOURCES_CONFLICT, hint="printer"),
    ]
    groups = group_signals(signals)
    assert len(groups) == 2


def test_build_candidate_needs_triage_for_insufficient():
    org = uuid4()
    group = [_signal(org=org, kind=GapSignalKind.ANSWER_INSUFFICIENT, hint="нет инструкции")]
    candidate = build_candidate(group, config=KnowledgeGapsConfig())
    assert candidate is not None
    assert candidate.suggested_kind is GapKind.NEEDS_TRIAGE
    assert candidate.organization_id == org


def test_build_candidate_conflict():
    org = uuid4()
    group = [_signal(org=org, kind=GapSignalKind.SOURCES_CONFLICT, hint="auth")]
    candidate = build_candidate(group, config=KnowledgeGapsConfig())
    assert candidate is not None
    assert candidate.suggested_kind is GapKind.CONFLICTING_CONTENT


def test_build_candidate_respects_min_signals():
    group = [_signal()]
    assert build_candidate(group, config=KnowledgeGapsConfig(min_signals=2)) is None


@pytest.mark.asyncio
async def test_detect_gaps_saves_candidates():
    org = uuid4()
    groups = [[_signal(org=org, hint="a")], [_signal(org=org, hint="b")]]
    saved: list[GapCandidate] = []

    async def assess(group):
        return build_candidate(group, config=KnowledgeGapsConfig())

    async def save(candidate: GapCandidate):
        saved.append(candidate)
        return uuid4()

    ids = await detect_gaps(groups, assess=assess, save=save)
    assert len(ids) == 2
    assert len(saved) == 2


def test_knowledge_gap_state_machine():
    gap = KnowledgeGap(
        organization_id=uuid4(),
        grouping_key="k",
        title="t",
    )
    gap.triage(GapKind.MISSING_CONTENT)
    gap.assign(uuid4())
    gap.start()
    assert gap.status is GapStatus.IN_PROGRESS
    gap.resolve("done")
    assert gap.status is GapStatus.RESOLVED
    gap.reopen()
    assert gap.status is GapStatus.OPEN
