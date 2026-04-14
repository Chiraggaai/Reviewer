"""
Review Queue business logic — backed by ``mock_store`` (standalone Reviewer API).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.review_queue_schemas import (
    QueueStatusBadge,
    ReviewQueueCard,
    ReviewQueueEmptyHint,
    ReviewQueueListData,
    ReviewQueueMeta,
    ReviewQueueProjectOption,
    ReviewQueueProjectsData,
    ReviewQueueReworkRound,
    ReviewQueueSLA,
    ReviewQueueSort,
    ReviewQueueTab,
    ReviewQueueTabCounts,
    SLAVisualStatus,
)

SLA_WINDOW_HOURS = 48
RECENT_COMPLETED_DAYS = 30
MAX_REWORK_ROUNDS = 3


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _contributor_id(evidence_id: str, override: Optional[str]) -> str:
    if override and str(override).strip():
        return str(override).strip()
    h = hashlib.sha256(evidence_id.encode("utf-8")).hexdigest()[:4].upper()
    return f"C-{h}"


def _humanize_hours_ago(hours: float) -> str:
    if hours < 1 / 60:
        return "just now"
    if hours < 1:
        m = max(1, int(hours * 60))
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if hours < 48:
        h = max(1, int(hours))
        return f"{h} hour{'s' if h != 1 else ''} ago"
    d = int(hours // 24)
    return f"{d} day{'s' if d != 1 else ''} ago"


def _format_submitted(submitted_at: datetime, now: datetime) -> str:
    date_part = submitted_at.strftime("%d %b %Y")
    delta = now - submitted_at
    hours = max(0.0, delta.total_seconds() / 3600.0)
    if hours < 48:
        return f"Submitted: {date_part} ({_humanize_hours_ago(hours)})"
    return f"Submitted: {date_part}"


def _deadline_at(submitted_at: datetime, evidence_doc: dict[str, Any]) -> datetime:
    raw = evidence_doc.get("sla_deadline_at")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    return submitted_at + timedelta(hours=SLA_WINDOW_HOURS)


def _build_sla(
    *,
    assignment_status: str,
    submitted_at: datetime,
    now: datetime,
    evidence_doc: dict[str, Any],
) -> tuple[ReviewQueueSLA, bool]:
    if (assignment_status or "").lower() == "completed":
        return (
            ReviewQueueSLA(
                visual_status=SLAVisualStatus.ON_TRACK,
                progress_bar_percent=100.0,
                bar_color_token="green",
                countdown_label="Review completed.",
                emphasize_countdown=False,
                breached=False,
                breached_label=None,
                remaining_seconds=None,
                deadline_at_iso=None,
            ),
            False,
        )

    deadline = _deadline_at(submitted_at, evidence_doc)
    remaining = (deadline - now).total_seconds()
    window_s = SLA_WINDOW_HOURS * 3600
    elapsed = max(0.0, window_s - remaining)
    progress = min(100.0, max(0.0, (elapsed / window_s) * 100.0))

    breached = remaining < 0
    if breached:
        sla = ReviewQueueSLA(
            visual_status=SLAVisualStatus.BREACHED,
            progress_bar_percent=100.0,
            bar_color_token="red",
            countdown_label="SLA BREACHED — complete review as soon as possible.",
            emphasize_countdown=True,
            breached=True,
            breached_label="SLA BREACHED",
            remaining_seconds=int(remaining),
            deadline_at_iso=deadline.isoformat(),
        )
        return sla, True

    hours_left = remaining / 3600.0
    if hours_left < 4:
        visual = SLAVisualStatus.CRITICAL
        emphasize = True
        float_top = True
    elif hours_left <= 24:
        visual = SLAVisualStatus.APPROACHING
        emphasize = False
        float_top = False
    else:
        visual = SLAVisualStatus.ON_TRACK
        emphasize = False
        float_top = False

    if hours_left > 24:
        bar_color = "green"
    elif hours_left >= 12:
        bar_color = "amber"
    else:
        bar_color = "red"

    rh = int(remaining // 3600)
    rm = int((remaining % 3600) // 60)
    countdown = f"Review due in {rh} hours {rm} minutes."

    sla = ReviewQueueSLA(
        visual_status=visual,
        progress_bar_percent=round(progress, 2),
        bar_color_token=bar_color,
        countdown_label=countdown,
        emphasize_countdown=emphasize,
        breached=False,
        breached_label=None,
        remaining_seconds=int(remaining),
        deadline_at_iso=deadline.isoformat(),
    )
    return sla, float_top


def _display_status(assignment_status: str, rework_round: int) -> QueueStatusBadge:
    s = (assignment_status or "").lower()
    if s == "completed":
        return QueueStatusBadge.COMPLETED
    if s == "in_progress":
        return QueueStatusBadge.UNDER_REVIEW
    if rework_round >= 2:
        return QueueStatusBadge.REWORK_RECEIVED
    return QueueStatusBadge.PENDING_REVIEW


def _row_matches_tab(
    badge: QueueStatusBadge,
    assignment_status: str,
    tab: ReviewQueueTab,
    updated_at: datetime,
    now: datetime,
) -> bool:
    if tab == ReviewQueueTab.ALL:
        if (assignment_status or "").lower() == "completed":
            return updated_at >= now - timedelta(days=RECENT_COMPLETED_DAYS)
        return True
    if tab == ReviewQueueTab.COMPLETED:
        return badge == QueueStatusBadge.COMPLETED
    if tab == ReviewQueueTab.PENDING_REVIEW:
        return badge == QueueStatusBadge.PENDING_REVIEW
    if tab == ReviewQueueTab.UNDER_REVIEW:
        return badge == QueueStatusBadge.UNDER_REVIEW
    if tab == ReviewQueueTab.REWORK_RECEIVED:
        return badge == QueueStatusBadge.REWORK_RECEIVED
    return True


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return None


def _assigned_project_count(reviewer_user_id: str) -> int:
    return mock_store.review_queue_assigned_project_count(reviewer_user_id)


def list_project_options(reviewer_user_id: str) -> ReviewQueueProjectsData:
    rows = mock_store.review_queue_assigned_projects(reviewer_user_id)
    projects = [
        ReviewQueueProjectOption(project_id=r["projectId"], project_name=r["projectName"])
        for r in rows
    ]
    return ReviewQueueProjectsData(projects=projects)


def _load_raw_rows(reviewer_user_id: str) -> list[dict[str, Any]]:
    return [
        r
        for r in mock_store.review_queue_module_raw_rows()
        if r["assignment"].get("reviewer_user_id") == reviewer_user_id
    ]


def _build_card(row: dict[str, Any], now: datetime) -> ReviewQueueCard:
    a = row["assignment"]
    ev: dict[str, Any] = row["evidence"]
    eid = row["evidence_id"]
    ast = (a.get("status") or "pending").lower()

    submitted_at = _parse_dt(ev.get("submitted_at")) or _parse_dt(a.get("created_at")) or now
    rework_round = int(ev.get("rework_round") or 1)
    badge = _display_status(ast, rework_round)

    project_name = (ev.get("project_name") or "Project").strip()
    project_id = ev.get("project_id")
    if project_id is not None:
        project_id = str(project_id)

    task_name = (a.get("title") or ev.get("title") or "Evidence review").strip()

    sla, float_default = _build_sla(
        assignment_status=ast,
        submitted_at=submitted_at,
        now=now,
        evidence_doc=ev,
    )
    float_top = float_default or (sla.visual_status == SLAVisualStatus.CRITICAL)

    rework_model: Optional[ReviewQueueReworkRound] = None
    if rework_round > 1:
        rework_model = ReviewQueueReworkRound(
            current=rework_round,
            max_rounds=MAX_REWORK_ROUNDS,
            visible=True,
            is_final_round_warning=rework_round >= MAX_REWORK_ROUNDS,
        )

    ai_score = ev.get("ai_pre_score_percent")
    if ai_score is not None:
        try:
            ai_score = int(ai_score)
        except (TypeError, ValueError):
            ai_score = None

    return ReviewQueueCard(
        assignment_id=str(a["_id"]),
        evidence_id=eid,
        task_name=task_name,
        project_name=project_name,
        project_id=project_id,
        contributor_id=_contributor_id(eid, ev.get("contributor_anon_id")),
        submitted_display=_format_submitted(submitted_at, now),
        rework_round=rework_model,
        sla=sla,
        ai_pre_score_percent=ai_score,
        status_badge=badge,
        float_to_top=float_top,
        open_review_path=f"/reviewer/evidence/{eid}/review",
        evidence_pack_api_path=f"/api/reviewer/evidence/{eid}/pack",
        qa_context_api_path=f"/api/reviewer/evidence/{eid}/qa/context",
    )


def _sort_cards(
    items: list[tuple[datetime, ReviewQueueCard]],
    sort: ReviewQueueSort,
) -> list[ReviewQueueCard]:
    def pin_key(c: ReviewQueueCard) -> int:
        return 0 if c.float_to_top else 1

    if sort == ReviewQueueSort.SLA_DEADLINE_SOONEST:
        ordered = sorted(
            items,
            key=lambda it: (
                pin_key(it[1]),
                it[1].sla.deadline_at_iso or "9999",
            ),
        )
        return [c for _, c in ordered]
    if sort == ReviewQueueSort.SUBMITTED_RECENT:
        ordered = sorted(
            items,
            key=lambda it: (pin_key(it[1]), -it[0].timestamp()),
        )
        return [c for _, c in ordered]
    if sort == ReviewQueueSort.PROJECT_NAME_AZ:
        ordered = sorted(
            items,
            key=lambda it: (pin_key(it[1]), it[1].project_name.lower()),
        )
        return [c for _, c in ordered]
    if sort == ReviewQueueSort.REWORK_ROUND_DESC:
        ordered = sorted(
            items,
            key=lambda it: (
                pin_key(it[1]),
                -(it[1].rework_round.current if it[1].rework_round else 1),
                it[1].task_name.lower(),
            ),
        )
        return [c for _, c in ordered]
    return [c for _, c in items]


def get_tab_counts(reviewer_user_id: str) -> ReviewQueueTabCounts:
    now = _utc_now()
    raw = _load_raw_rows(reviewer_user_id)
    counts = {t: 0 for t in ReviewQueueTab}
    for row in raw:
        a = row["assignment"]
        ev = row["evidence"]
        ast = (a.get("status") or "pending").lower()
        rw = int(ev.get("rework_round") or 1)
        badge = _display_status(ast, rw)
        ua = _parse_dt(a.get("updated_at")) or _parse_dt(a.get("created_at")) or now
        for tab in ReviewQueueTab:
            if _row_matches_tab(badge, ast, tab, ua, now):
                counts[tab] += 1
    return ReviewQueueTabCounts.model_validate(
        {
            "all": counts[ReviewQueueTab.ALL],
            "pendingReview": counts[ReviewQueueTab.PENDING_REVIEW],
            "underReview": counts[ReviewQueueTab.UNDER_REVIEW],
            "reworkReceived": counts[ReviewQueueTab.REWORK_RECEIVED],
            "completed": counts[ReviewQueueTab.COMPLETED],
        }
    )


def get_review_queue(
    reviewer_user_id: str,
    *,
    tab: ReviewQueueTab = ReviewQueueTab.ALL,
    sort: ReviewQueueSort = ReviewQueueSort.SLA_DEADLINE_SOONEST,
    project_id: Optional[str] = None,
) -> ReviewQueueListData:
    now = _utc_now()
    assigned_n = _assigned_project_count(reviewer_user_id)
    proj_opts = list_project_options(reviewer_user_id)
    distinct_from_evidence = len(proj_opts.projects)

    raw = _load_raw_rows(reviewer_user_id)
    assigned_display = max(assigned_n, distinct_from_evidence)
    if assigned_display == 0 and raw:
        assigned_display = 1

    items: list[tuple[datetime, ReviewQueueCard]] = []
    for row in raw:
        a = row["assignment"]
        ev = row["evidence"]
        ast = (a.get("status") or "pending").lower()
        rw = int(ev.get("rework_round") or 1)
        badge = _display_status(ast, rw)
        ua = _parse_dt(a.get("updated_at")) or _parse_dt(a.get("created_at")) or now
        if not _row_matches_tab(badge, ast, tab, ua, now):
            continue
        card = _build_card(row, now)
        if project_id and (card.project_id or "") != project_id:
            continue
        submitted_at = _parse_dt(ev.get("submitted_at")) or _parse_dt(a.get("created_at")) or now
        items.append((submitted_at, card))

    cards = _sort_cards(items, sort)

    empty_hint = ReviewQueueEmptyHint.NONE
    if assigned_display == 0:
        empty_hint = ReviewQueueEmptyHint.NOT_ASSIGNED
    elif not raw:
        empty_hint = ReviewQueueEmptyHint.NO_SUBMISSIONS
    elif not cards:
        empty_hint = ReviewQueueEmptyHint.NO_FILTER_MATCH

    meta = ReviewQueueMeta(
        assigned_project_count=assigned_display,
        empty_hint=empty_hint,
    )
    return ReviewQueueListData(cards=cards, meta=meta)
