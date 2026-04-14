"""
In-memory Mentoring Log per reviewer (demo). Replace with DB in production.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.mentoring_schemas import (
    MentoringContributorCard,
    MentoringContributorsPayload,
    MentoringNote,
    MentoringNoteCreateRequest,
    MentoringNoteCreatedPayload,
    MentoringNotesPayload,
)

UTC = timezone.utc

# reviewer_user_id -> contributor_id -> { displayLabel, tasksCompletedCount, acceptanceRatePercent }
_contributor_meta: dict[str, dict[str, dict[str, Any]]] = {}
# reviewer_user_id -> contributor_id -> list of note dicts (newest last for append; return reversed)
_notes: dict[str, dict[str, list[dict[str, Any]]]] = {}

_CATEGORY_SUGGESTIONS = [
    "General mentoring",
    "Biometric authentication",
    "Code quality",
    "Documentation",
    "Testing & evidence",
    "Security & compliance",
]


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _ensure_demo_seed(reviewer_user_id: str) -> None:
    if reviewer_user_id in _contributor_meta and _contributor_meta[reviewer_user_id]:
        return
    if reviewer_user_id != mock_store.DEMO_REVIEWER_ID:
        _contributor_meta.setdefault(reviewer_user_id, {})
        _notes.setdefault(reviewer_user_id, {})
        return

    rid = reviewer_user_id
    _contributor_meta[rid] = {
        "e5l": {
            "displayLabel": "Contributor-E5L",
            "tasksCompletedCount": 3,
            "acceptanceRatePercent": 78.0,
        },
        "k7q": {
            "displayLabel": "Contributor-K7Q",
            "tasksCompletedCount": 2,
            "acceptanceRatePercent": 82.0,
        },
    }
    _notes[rid] = {
        "e5l": [
            {
                "noteId": "mn_e5l_1",
                "category": "General mentoring",
                "body": (
                    "Walked through evidence pack expectations and rubric weighting. "
                    "Second submission improved checklist completeness."
                ),
                "createdAt": "2026-04-01T11:00:00+00:00",
            },
            {
                "noteId": "mn_e5l_2",
                "category": "Documentation",
                "body": (
                    "Suggested linking test artifacts directly in the narrative; "
                    "contributor applied feedback on the payroll reconciliation task."
                ),
                "createdAt": "2026-04-03T14:20:00+00:00",
            },
        ],
        "k7q": [
            {
                "noteId": "mn_k7q_1",
                "category": "Biometric authentication",
                "body": (
                    "First submission showed unfamiliarity with native module bridging; "
                    "provided sample pattern for secure credential handoff and retry limits."
                ),
                "createdAt": "2026-04-05T10:15:00+00:00",
            },
        ],
    }


def _note_count(reviewer_user_id: str, contributor_id: str) -> int:
    return len(_notes.get(reviewer_user_id, {}).get(contributor_id, []))


def list_contributors(reviewer_user_id: str) -> MentoringContributorsPayload:
    _ensure_demo_seed(reviewer_user_id)
    meta = _contributor_meta.get(reviewer_user_id, {})
    cards: list[MentoringContributorCard] = []
    for cid in sorted(meta.keys(), key=lambda x: meta[x]["displayLabel"]):
        m = meta[cid]
        cards.append(
            MentoringContributorCard(
                contributor_id=cid,
                display_label=m["displayLabel"],
                is_student=True,
                tasks_completed_count=int(m["tasksCompletedCount"]),
                acceptance_rate_percent=float(m["acceptanceRatePercent"]),
                note_count=_note_count(reviewer_user_id, cid),
            )
        )
    return MentoringContributorsPayload(
        contributors=cards,
        category_suggestions=list(_CATEGORY_SUGGESTIONS),
    )


def _parse_note(n: dict[str, Any]) -> MentoringNote:
    ts = n["createdAt"]
    if isinstance(ts, str):
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        created = datetime.fromisoformat(ts)
    else:
        created = ts
    return MentoringNote(
        note_id=n["noteId"],
        category=n["category"],
        body=n["body"],
        created_at=created,
    )


def list_notes(reviewer_user_id: str, contributor_id: str) -> MentoringNotesPayload:
    _ensure_demo_seed(reviewer_user_id)
    meta = _contributor_meta.get(reviewer_user_id, {})
    if contributor_id not in meta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contributor not found in your mentoring log.")
    raw = list(_notes.get(reviewer_user_id, {}).get(contributor_id, []))
    # Newest first for expanded panel
    raw_sorted = sorted(
        raw,
        key=lambda x: str(x.get("createdAt", "")),
        reverse=True,
    )
    return MentoringNotesPayload(
        contributor_id=contributor_id,
        display_label=meta[contributor_id]["displayLabel"],
        notes=[_parse_note(n) for n in raw_sorted],
    )


def add_note(
    reviewer_user_id: str,
    contributor_id: str,
    body: MentoringNoteCreateRequest,
) -> MentoringNoteCreatedPayload:
    _ensure_demo_seed(reviewer_user_id)
    meta = _contributor_meta.get(reviewer_user_id, {})
    if contributor_id not in meta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contributor not found in your mentoring log.")

    nid = f"mn_{uuid.uuid4().hex[:10]}"
    entry = {
        "noteId": nid,
        "category": body.category.strip(),
        "body": body.body.strip(),
        "createdAt": _now().isoformat(),
    }
    _notes.setdefault(reviewer_user_id, {}).setdefault(contributor_id, []).append(entry)

    return MentoringNoteCreatedPayload(note=_parse_note(entry))


def ensure_contributor_for_reviewer(
    reviewer_user_id: str,
    contributor_id: str,
    *,
    display_label: str,
    tasks_completed_count: int = 0,
    acceptance_rate_percent: float = 0.0,
) -> None:
    """Test hook: register a mentee without going through UI."""
    _contributor_meta.setdefault(reviewer_user_id, {})[contributor_id] = {
        "displayLabel": display_label,
        "tasksCompletedCount": tasks_completed_count,
        "acceptanceRatePercent": acceptance_rate_percent,
    }
    _notes.setdefault(reviewer_user_id, {}).setdefault(contributor_id, [])
