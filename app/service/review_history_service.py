"""
Review History — merges demo seed rows with immutable Evidence Pack submit records.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from app.service import evidence_pack_service
from app.service import mock_store
from app.schema.review_history_schemas import (
    FinalReviewOutcome,
    ReviewHistoryAgreementSummary,
    ReviewHistoryDetail,
    ReviewHistoryListItem,
    ReviewHistoryListPayload,
    ReviewHistoryPdfMeta,
    ReviewHistoryRubricRow,
    ReviewHistoryTab,
    ReviewerRecommendationKind,
)

UTC = timezone.utc

# record_id -> { final: ACCEPTED|REWORK_REQUIRED, overridden: bool, justification: str }
_enterprise_outcomes: dict[str, dict[str, Any]] = {}


def _parse_ts(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    s = str(raw)
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def _aligned(reviewer_rec: str, final: str) -> bool:
    return (reviewer_rec == "ACCEPT" and final == "ACCEPTED") or (
        reviewer_rec == "REWORK" and final == "REWORK_REQUIRED"
    )


def _ensure_outcome(record_id: str, reviewer_rec: str) -> dict[str, Any]:
    if record_id not in _enterprise_outcomes:
        h = int(hashlib.sha256(record_id.encode()).hexdigest(), 16) % 100
        if h < 22:
            overridden = True
            final = "REWORK_REQUIRED" if reviewer_rec == "ACCEPT" else "ACCEPTED"
        else:
            overridden = False
            final = "ACCEPTED" if reviewer_rec == "ACCEPT" else "REWORK_REQUIRED"
        excerpts = (
            "Client Team cited delivery risk; accepted despite your REWORK recommendation.",
            "Compliance required additional controls; rework mandated after your ACCEPT.",
        )
        _enterprise_outcomes[record_id] = {
            "final": final,
            "overridden": overridden,
            "justification": excerpts[h % 2],
        }
    return _enterprise_outcomes[record_id]


def _seed_rows() -> list[dict[str, Any]]:
    """Static demo rows matching Review History UI (75% agreement on last 4)."""
    rid = mock_store.DEMO_REVIEWER_ID
    return [
        {
            "review_record_id": "hist_seed_mono",
            "evidence_id": "ev_hist_mono",
            "reviewer_user_id": rid,
            "task_title": "Setup monorepo infrastructure",
            "project_name": "ERP Platform Decomposition",
            "reviewed_at": _parse_ts("2026-03-31T14:00:00+00:00"),
            "reviewer_recommendation": "ACCEPT",
            "final_outcome": "ACCEPTED",
            "overridden": False,
            "rework_round": None,
            "enterprise_agreed_with_reviewer": True,
            "payload": {
                "rubricScores": [
                    {"criterionId": "crit_1", "score": 5, "notes": "Strong CI/CD coverage across repos."},
                    {"criterionId": "crit_2", "score": 5, "notes": "Branch protection and checks documented."},
                    {"criterionId": "crit_3", "score": 4, "notes": "Minor gap on artifact retention policy."},
                    {"criterionId": "crit_4", "score": 5, "notes": "Clear runbook for releases."},
                ],
                "areasOfStrength": (
                    "Excellent infrastructure setup with comprehensive CI/CD pipeline. "
                    "All acceptance criteria met and exceeded."
                ),
                "areasForImprovement": "",
                "recommendation": "ACCEPT",
            },
            "criterion_labels": {
                "crit_1": "Criterion 1",
                "crit_2": "Criterion 2",
                "crit_3": "Criterion 3",
                "crit_4": "Criterion 4",
            },
        },
        {
            "review_record_id": "hist_seed_auth_v1",
            "evidence_id": "ev_hist_auth",
            "reviewer_user_id": rid,
            "task_title": "Auth service with Keycloak",
            "project_name": "ERP Platform Decomposition",
            "reviewed_at": _parse_ts("2026-03-31T16:30:00+00:00"),
            "reviewer_recommendation": "REWORK",
            "final_outcome": "REWORK_REQUIRED",
            "overridden": False,
            "rework_round": 1,
            "enterprise_agreed_with_reviewer": True,
            "payload": {
                "rubricScores": [
                    {"criterionId": "crit_1", "score": 3, "notes": "Integration present but error paths thin."},
                    {"criterionId": "crit_2", "score": 2, "notes": "Token refresh flow not demonstrated."},
                    {"criterionId": "crit_3", "score": 3, "notes": "Docs list endpoints but not failure modes."},
                ],
                "areasOfStrength": "Core Keycloak realm configuration is plausible and builds cleanly.",
                "areasForImprovement": "Need stronger coverage of session expiry and forced logout paths per checklist.",
                "recommendation": "REWORK",
                "specificReworkRequirements": "Provide test evidence for refresh token rotation and 401 handling.",
            },
            "criterion_labels": {
                "crit_1": "Criterion 1",
                "crit_2": "Criterion 2",
                "crit_3": "Criterion 3",
            },
        },
        {
            "review_record_id": "hist_seed_auth_v2",
            "evidence_id": "ev_hist_auth",
            "reviewer_user_id": rid,
            "task_title": "Auth service with Keycloak",
            "project_name": "ERP Platform Decomposition",
            "reviewed_at": _parse_ts("2026-04-01T10:00:00+00:00"),
            "reviewer_recommendation": "ACCEPT",
            "final_outcome": "ACCEPTED",
            "overridden": False,
            "rework_round": 2,
            "enterprise_agreed_with_reviewer": True,
            "payload": {
                "rubricScores": [
                    {"criterionId": "crit_1", "score": 5, "notes": "Error paths now exercised in tests."},
                    {"criterionId": "crit_2", "score": 5, "notes": "Refresh flow documented with screenshots."},
                    {"criterionId": "crit_3", "score": 4, "notes": "Minor wording gaps in ops runbook."},
                ],
                "areasOfStrength": "Rework addressed prior gaps; evidence is clear and traceable.",
                "areasForImprovement": "",
                "recommendation": "ACCEPT",
            },
            "criterion_labels": {
                "crit_1": "Criterion 1",
                "crit_2": "Criterion 2",
                "crit_3": "Criterion 3",
            },
        },
        {
            "review_record_id": "hist_seed_frontend",
            "evidence_id": "ev_hist_ui",
            "reviewer_user_id": rid,
            "task_title": "Frontend design system",
            "project_name": "ERP Platform Decomposition",
            "reviewed_at": _parse_ts("2026-04-02T09:00:00+00:00"),
            "reviewer_recommendation": "ACCEPT",
            "final_outcome": "REWORK_REQUIRED",
            "overridden": True,
            "rework_round": None,
            "enterprise_agreed_with_reviewer": False,
            "payload": {
                "rubricScores": [
                    {"criterionId": "crit_1", "score": 4, "notes": "Components documented."},
                    {"criterionId": "crit_2", "score": 4, "notes": "Storybook mostly complete."},
                    {"criterionId": "crit_3", "score": 4, "notes": "Accessibility checklist partial."},
                ],
                "areasOfStrength": "Cohesive tokens and sensible component boundaries.",
                "areasForImprovement": "A11y sign-off still pending for two critical widgets.",
                "recommendation": "ACCEPT",
            },
            "criterion_labels": {
                "crit_1": "Criterion 1",
                "crit_2": "Criterion 2",
                "crit_3": "Criterion 3",
            },
            "override_justification_excerpt": (
                "Enterprise prioritized UX consistency; additional a11y work required before release train."
            ),
        },
    ]


def _row_from_submitted_record(record_id: str, rec: dict[str, Any]) -> dict[str, Any]:
    evidence_id = str(rec.get("evidence_id") or "")
    reviewer_user_id = str(rec.get("reviewer_user_id") or "")
    payload = rec.get("payload") or {}
    rec_str = str(payload.get("recommendation") or "ACCEPT").upper()

    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    task_title = "Evidence review"
    project_name = "Project"
    rework_round: Optional[int] = None
    if row:
        a = row["assignment"]
        ev = row["evidence"]
        task_title = (a.get("title") or ev.get("title") or task_title).strip()
        project_name = (ev.get("project_name") or project_name).strip()
        rework_round = int(ev.get("rework_round") or 1)

    reviewed_at = _parse_ts(rec.get("created_at"))

    eo = _ensure_outcome(record_id, rec_str)
    final = str(eo["final"])
    overridden = bool(eo["overridden"])
    agreed = _aligned(rec_str, final)

    labels = evidence_pack_service.criterion_labels_for_evidence(evidence_id)

    return {
        "review_record_id": record_id,
        "evidence_id": evidence_id,
        "reviewer_user_id": reviewer_user_id,
        "task_title": task_title,
        "project_name": project_name,
        "reviewed_at": reviewed_at,
        "reviewer_recommendation": rec_str,
        "final_outcome": final,
        "overridden": overridden,
        "rework_round": rework_round,
        "enterprise_agreed_with_reviewer": agreed,
        "payload": payload,
        "criterion_labels": labels,
        "override_justification_excerpt": eo.get("justification") if overridden else None,
    }


def _collect_rows(reviewer_user_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if reviewer_user_id == mock_store.DEMO_REVIEWER_ID:
        rows.extend(_seed_rows())
    for record_id, rec in evidence_pack_service.list_review_records_for_reviewer(reviewer_user_id):
        rows.append(_row_from_submitted_record(record_id, rec))
    return rows


def _match_tab(row: dict[str, Any], tab: ReviewHistoryTab) -> bool:
    if tab == ReviewHistoryTab.ALL:
        return True
    rec = row["reviewer_recommendation"]
    if tab == ReviewHistoryTab.RECOMMENDED_ACCEPT:
        return rec == "ACCEPT"
    if tab == ReviewHistoryTab.RECOMMENDED_REWORK:
        return rec == "REWORK"
    if tab == ReviewHistoryTab.OVERRIDDEN:
        return bool(row["overridden"])
    return True


def _agreement_window(rows_chrono: list[dict[str, Any]]) -> ReviewHistoryAgreementSummary:
    window = rows_chrono[-4:] if len(rows_chrono) > 4 else rows_chrono
    n = len(window)
    if n == 0:
        return ReviewHistoryAgreementSummary(
            agreed_count=0,
            window_count=0,
            agreement_percent=None,
            headline="No submitted reviews yet. Complete a review from the queue to build history.",
        )
    agreed = sum(1 for r in window if r["enterprise_agreed_with_reviewer"])
    pct = round(100.0 * agreed / n, 0)
    headline = (
        f"Enterprise Admin agreed with your recommendation in {agreed} of your last {n} reviews."
    )
    return ReviewHistoryAgreementSummary(
        agreed_count=agreed,
        window_count=n,
        agreement_percent=pct,
        headline=headline,
    )


def _to_list_item(row: dict[str, Any]) -> ReviewHistoryListItem:
    return ReviewHistoryListItem(
        review_record_id=row["review_record_id"],
        evidence_id=row["evidence_id"],
        task_title=row["task_title"],
        project_name=row["project_name"],
        reviewed_at=row["reviewed_at"],
        reviewer_recommendation=ReviewerRecommendationKind(row["reviewer_recommendation"]),
        final_outcome=FinalReviewOutcome(row["final_outcome"]),
        overridden=row["overridden"],
        rework_round=row.get("rework_round"),
        enterprise_agreed_with_reviewer=row["enterprise_agreed_with_reviewer"],
    )


def list_history(
    reviewer_user_id: str,
    *,
    tab: ReviewHistoryTab = ReviewHistoryTab.ALL,
    limit: int = 20,
    offset: int = 0,
) -> ReviewHistoryListPayload:
    all_rows = _collect_rows(reviewer_user_id)
    chrono = sorted(all_rows, key=lambda r: r["reviewed_at"])
    agreement = _agreement_window(chrono)
    filtered = [r for r in chrono if _match_tab(r, tab)]
    total = len(filtered)
    lim = max(1, min(limit, 100))
    off = max(0, offset)
    page = filtered[off : off + lim]
    return ReviewHistoryListPayload(
        agreement=agreement,
        items=[_to_list_item(r) for r in page],
        total_matching=total,
        limit=lim,
        offset=off,
    )


def _find_row(reviewer_user_id: str, record_id: str) -> Optional[dict[str, Any]]:
    for r in _collect_rows(reviewer_user_id):
        if r["review_record_id"] == record_id:
            return r
    return None


def get_history_detail(reviewer_user_id: str, record_id: str) -> ReviewHistoryDetail:
    row = _find_row(reviewer_user_id, record_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review record not found.")

    payload = row.get("payload") or {}
    labels: dict[str, str] = row.get("criterion_labels") or {}
    rubric_out: list[ReviewHistoryRubricRow] = []
    for rs in payload.get("rubricScores") or []:
        cid = str(rs.get("criterionId") or "")
        rubric_out.append(
            ReviewHistoryRubricRow(
                criterion_id=cid,
                criterion_label=labels.get(cid, cid),
                score=int(rs["score"]),
                max_score=5,
            )
        )

    strength = (payload.get("areasOfStrength") or "").strip()
    improve = (payload.get("areasForImprovement") or "").strip()
    overall = strength
    if improve:
        overall = f"{strength}\n\nAreas for improvement: {improve}" if strength else improve

    pdf_path = f"/api/reviewer/history/{record_id}/review-record-pdf"

    return ReviewHistoryDetail(
        review_record_id=row["review_record_id"],
        evidence_id=row["evidence_id"],
        task_title=row["task_title"],
        project_name=row["project_name"],
        reviewed_at=row["reviewed_at"],
        reviewer_recommendation=ReviewerRecommendationKind(row["reviewer_recommendation"]),
        final_outcome=FinalReviewOutcome(row["final_outcome"]),
        overridden=row["overridden"],
        rework_round=row.get("rework_round"),
        override_justification_excerpt=row.get("override_justification_excerpt"),
        rubric_scores=rubric_out,
        overall_assessment=overall or "No narrative was stored for this record.",
        review_record_pdf_api_path=pdf_path,
    )


def get_review_record_pdf_meta(reviewer_user_id: str, record_id: str) -> ReviewHistoryPdfMeta:
    row = _find_row(reviewer_user_id, record_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review record not found.")
    safe_task = "".join(c if c.isalnum() else "_" for c in row["task_title"])[:40]
    fname = f"review-record-{record_id}-{safe_task}.pdf"
    return ReviewHistoryPdfMeta(
        review_record_id=record_id,
        filename=fname,
        message="Demo API: generate PDF from stored review snapshot in production.",
    )
