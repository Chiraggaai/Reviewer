"""
In-memory mock data and simple mutations for demo APIs.
Replace with database / service calls in production.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(tz=UTC)


# --- Mutable inbox unread (POST /read updates this) ---
_thread_unread: dict[str, int] = {
    "th_hr_emp": 2,
    "th_appt": 1,
    "th_fin_gl": 0,
}


def reset_demo_state() -> None:
    _thread_unread.clear()
    _thread_unread.update({"th_hr_emp": 2, "th_appt": 1, "th_fin_gl": 0})


def total_unread_messages() -> int:
    return sum(_thread_unread.values())


def get_thread_unread(thread_id: str) -> int:
    return _thread_unread.get(thread_id, 0)


def mark_thread_read(thread_id: str) -> int:
    if thread_id in _thread_unread:
        _thread_unread[thread_id] = 0
    return total_unread_messages()


def get_dashboard_summary() -> dict[str, Any]:
    q = review_queue_items()
    pending = len([x for x in q if x.get("status") == "pending"])
    overdue_ct = len([x for x in q if x.get("isOverdue")])
    overdue_msg = (
        f"You have {overdue_ct} overdue review(s). "
        "Overdue reviews are escalated to GlimmoraTeam Admin."
    )
    alerts: dict[str, Any] | None
    if overdue_ct:
        alerts = {
            "overdueReviewCount": overdue_ct,
            "message": overdue_msg,
            "cta": {"label": "View Overdue", "href": "/reviews?filter=overdue"},
        }
    else:
        alerts = None

    return {
        "pendingReviews": pending,
        "activeTasks": len(active_tasks()),
        "unreadMessages": total_unread_messages(),
        "slaCompliancePercent": 94.0,
        "alerts": alerts,
    }


def action_items() -> dict[str, Any]:
    return {
        "totalRequiringAttention": 5,
        "items": [
            {
                "id": "ai_1",
                "title": "Patient registration and profile",
                "severity": "critical",
                "icon": "sla_breached",
                "statusLabel": "Review SLA breached",
                "deepLink": {"type": "review", "id": "rev_pat_reg", "href": None},
            },
            {
                "id": "ai_2",
                "title": "Finance module — Accounts Payable",
                "severity": "warning",
                "icon": "due_today",
                "statusLabel": "Review due today",
                "deepLink": {"type": "review", "id": "rev_fin_ap", "href": None},
            },
            {
                "id": "ai_3",
                "title": "HR module — Employee records",
                "severity": "warning",
                "icon": "checkpoint",
                "statusLabel": "Midpoint checkpoint pending",
                "deepLink": {"type": "task", "id": "task_hr_emp", "href": None},
            },
            {
                "id": "ai_4",
                "title": "HR module — Employee records",
                "severity": "info",
                "icon": "unread_messages",
                "statusLabel": "2 unread message(s)",
                "deepLink": {"type": "inbox", "id": "th_hr_emp", "href": None},
            },
            {
                "id": "ai_5",
                "title": "Appointment booking system",
                "severity": "info",
                "icon": "unread_messages",
                "statusLabel": "1 unread message(s)",
                "deepLink": {"type": "inbox", "id": "th_appt", "href": None},
            },
        ],
    }


def sla_performance(period: str = "month") -> dict[str, Any]:
    return {
        "slaCompliancePercent": 94.0,
        "slaTargetPercent": 90.0,
        "recAcceptancePercent": 88.0,
        "recAcceptanceTargetPercent": 85.0,
        "avgReviewTimeHours": 18.0,
        "reviewsThisMonth": 12,
        "period": period,
    }


def review_queue_items() -> list[dict[str, Any]]:
    now = _now()
    return [
        {
            "reviewId": "rev_fin_gl",
            "moduleLabel": "Finance module — General Ledger",
            "dueAt": now + timedelta(days=1),
            "dueDisplay": "Due in 1d",
            "isOverdue": False,
            "contributorId": "usr_contrib_01",
            "status": "pending",
        },
        {
            "reviewId": "rev_fin_ap",
            "moduleLabel": "Finance module — Accounts Payable",
            "dueAt": now + timedelta(hours=3),
            "dueDisplay": "Due in 3h",
            "isOverdue": False,
            "contributorId": "usr_contrib_02",
            "status": "pending",
        },
        {
            "reviewId": "rev_pat_reg_r2",
            "moduleLabel": "Patient registration and profile (Round 2)",
            "dueAt": now - timedelta(days=1),
            "dueDisplay": "OVERDUE",
            "isOverdue": True,
            "contributorId": "usr_contrib_03",
            "status": "pending",
        },
    ]


_reviews_detail: dict[str, dict[str, Any]] = {
    "rev_fin_gl": {
        "reviewId": "rev_fin_gl",
        "moduleLabel": "Finance module — General Ledger",
        "status": "pending",
        "dueAt": None,
        "roundLabel": None,
    },
    "rev_fin_ap": {
        "reviewId": "rev_fin_ap",
        "moduleLabel": "Finance module — Accounts Payable",
        "status": "pending",
        "dueAt": None,
        "roundLabel": None,
    },
    "rev_pat_reg": {
        "reviewId": "rev_pat_reg",
        "moduleLabel": "Patient registration and profile",
        "status": "sla_breached",
        "dueAt": None,
        "roundLabel": "Round 1",
    },
    "rev_pat_reg_r2": {
        "reviewId": "rev_pat_reg_r2",
        "moduleLabel": "Patient registration and profile",
        "status": "pending",
        "dueAt": None,
        "roundLabel": "Round 2",
    },
}


def review_detail(review_id: str) -> dict[str, Any] | None:
    item = next((x for x in review_queue_items() if x["reviewId"] == review_id), None)
    base = _reviews_detail.get(review_id)
    if base:
        out = dict(base)
        if item and item.get("dueAt"):
            out["dueAt"] = item["dueAt"]
        return out
    if item:
        return {
            "reviewId": item["reviewId"],
            "moduleLabel": item["moduleLabel"],
            "status": "pending",
            "dueAt": item.get("dueAt"),
            "roundLabel": None,
        }
    return None


def active_tasks() -> list[dict[str, Any]]:
    return [
        {
            "taskId": "task_fin_gl",
            "shortTitle": "Finance module — Gene...",
            "status": "SUBMITTED",
            "statusColorToken": "yellow",
        },
        {
            "taskId": "task_hr_emp",
            "shortTitle": "HR module — Employee ...",
            "status": "IN_PROGRESS",
            "statusColorToken": "blue",
        },
        {
            "taskId": "task_appt",
            "shortTitle": "Appointment booking sy...",
            "status": "IN_PROGRESS",
            "statusColorToken": "blue",
        },
        {
            "taskId": "task_fin_ap",
            "shortTitle": "Finance module — Acco...",
            "status": "REWORK",
            "statusColorToken": "pink",
        },
    ]


def inbox_threads(unread_only: bool = False) -> list[dict[str, Any]]:
    now = _now()
    rows = [
        {
            "threadId": "th_hr_emp",
            "moduleLabel": "HR module — Employee records",
            "linkedReviewId": "rev_pat_reg_r2",
            "unreadCount": _thread_unread.get("th_hr_emp", 0),
            "lastMessagePreview": "Can you confirm the updated policy section?",
            "updatedAt": now - timedelta(hours=2),
        },
        {
            "threadId": "th_appt",
            "moduleLabel": "Appointment booking system",
            "linkedReviewId": None,
            "unreadCount": _thread_unread.get("th_appt", 0),
            "lastMessagePreview": "Slot overlap on peak hours — see screenshot.",
            "updatedAt": now - timedelta(hours=5),
        },
        {
            "threadId": "th_fin_gl",
            "moduleLabel": "Finance module — General Ledger",
            "linkedReviewId": "rev_fin_gl",
            "unreadCount": _thread_unread.get("th_fin_gl", 0),
            "lastMessagePreview": "Thanks, all clear.",
            "updatedAt": now - timedelta(days=1),
        },
    ]
    if unread_only:
        rows = [r for r in rows if r["unreadCount"] > 0]
    return rows


# --- Review Queue module (5.x) — evidence_review assignments + evidence metadata ---

DEMO_REVIEWER_ID = "demo-reviewer"


def review_queue_assigned_projects(reviewer_user_id: str) -> list[dict[str, str]]:
    if reviewer_user_id == "unassigned-reviewer":
        return []
    return [
        {"projectId": "proj_fin", "projectName": "Finance module"},
        {"projectId": "proj_hr", "projectName": "HR module"},
        {"projectId": "proj_health", "projectName": "Patient registration"},
    ]


def review_queue_assigned_project_count(reviewer_user_id: str) -> int:
    return len(review_queue_assigned_projects(reviewer_user_id))


_queue_row_overrides: dict[str, dict[str, Any]] = {}


def _deep_merge_queue_row(base: dict[str, Any]) -> dict[str, Any]:
    import copy

    row = copy.deepcopy(base)
    eid = row["evidence_id"]
    ov = _queue_row_overrides.get(eid)
    if not ov:
        return row
    if "evidence" in ov:
        row["evidence"] = {**row["evidence"], **ov["evidence"]}
    if "assignment" in ov:
        row["assignment"] = {**row["assignment"], **ov["assignment"]}
    return row


def patch_queue_row(
    evidence_id: str,
    *,
    evidence: dict[str, Any] | None = None,
    assignment: dict[str, Any] | None = None,
) -> None:
    cur = _queue_row_overrides.setdefault(
        evidence_id, {"evidence": {}, "assignment": {}}
    )
    if evidence:
        cur["evidence"].update(evidence)
    if assignment:
        cur["assignment"].update(assignment)


def _base_review_queue_rows() -> list[dict[str, Any]]:
    now = _now()
    rid = DEMO_REVIEWER_ID
    return [
        {
            "assignment": {
                "_id": "asg_fin_gl",
                "reviewer_user_id": rid,
                "task_kind": "evidence_review",
                "related_id": "ev_fin_gl",
                "title": "General Ledger reconciliation pack",
                "status": "pending",
                "created_at": now - timedelta(hours=8),
                "updated_at": now - timedelta(hours=2),
            },
            "evidence": {
                "evidence_id": "ev_fin_gl",
                "project_name": "Finance module",
                "project_id": "proj_fin",
                "contributor_anon_id": "C-4K7",
                "submitted_at": now - timedelta(hours=8),
                "rework_round": 1,
                "ai_pre_score_percent": 78,
            },
            "evidence_id": "ev_fin_gl",
        },
        {
            "assignment": {
                "_id": "asg_hr_emp",
                "reviewer_user_id": rid,
                "task_kind": "evidence_review",
                "related_id": "ev_hr_emp",
                "title": "Employee records evidence bundle",
                "status": "in_progress",
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(hours=5),
            },
            "evidence": {
                "evidence_id": "ev_hr_emp",
                "project_name": "HR module",
                "project_id": "proj_hr",
                "submitted_at": now - timedelta(days=2),
                "rework_round": 1,
                "ai_pre_score_percent": 82,
            },
            "evidence_id": "ev_hr_emp",
        },
        {
            "assignment": {
                "_id": "asg_pat_r2",
                "reviewer_user_id": rid,
                "task_kind": "evidence_review",
                "related_id": "ev_pat_r2",
                "title": "Patient registration — policy attachments",
                "status": "pending",
                "created_at": now - timedelta(hours=20),
                "updated_at": now - timedelta(hours=1),
            },
            "evidence": {
                "evidence_id": "ev_pat_r2",
                "project_name": "Patient registration",
                "project_id": "proj_health",
                "contributor_anon_id": "C-9QM",
                "submitted_at": now - timedelta(hours=20),
                "rework_round": 2,
                "ai_pre_score_percent": 71,
            },
            "evidence_id": "ev_pat_r2",
        },
        {
            "assignment": {
                "_id": "asg_completed",
                "reviewer_user_id": rid,
                "task_kind": "evidence_review",
                "related_id": "ev_done_1",
                "title": "Appointment scheduling API — evidence",
                "status": "completed",
                "created_at": now - timedelta(days=10),
                "updated_at": now - timedelta(days=3),
            },
            "evidence": {
                "evidence_id": "ev_done_1",
                "project_name": "Finance module",
                "project_id": "proj_fin",
                "submitted_at": now - timedelta(days=10),
                "rework_round": 1,
                "ai_pre_score_percent": 90,
            },
            "evidence_id": "ev_done_1",
        },
        {
            "assignment": {
                "_id": "asg_breach",
                "reviewer_user_id": rid,
                "task_kind": "evidence_review",
                "related_id": "ev_breach",
                "title": "Accounts Payable — overdue submission",
                "status": "pending",
                "created_at": now - timedelta(hours=60),
                "updated_at": now - timedelta(hours=12),
            },
            "evidence": {
                "evidence_id": "ev_breach",
                "project_name": "Finance module",
                "project_id": "proj_fin",
                "submitted_at": now - timedelta(hours=60),
                "rework_round": 1,
                "ai_pre_score_percent": 65,
            },
            "evidence_id": "ev_breach",
        },
    ]


def review_queue_module_raw_rows() -> list[dict[str, Any]]:
    return [_deep_merge_queue_row(r) for r in _base_review_queue_rows()]


def find_queue_row_by_evidence(evidence_id: str, reviewer_user_id: str) -> dict[str, Any] | None:
    for row in review_queue_module_raw_rows():
        if row["evidence_id"] != evidence_id:
            continue
        if row["assignment"].get("reviewer_user_id") != reviewer_user_id:
            continue
        return row
    return None


def known_evidence_ids() -> set[str]:
    return {str(r["evidence_id"]) for r in review_queue_module_raw_rows()}


def find_any_queue_row_by_evidence(evidence_id: str) -> dict[str, Any] | None:
    """First queue row for an evidence id (contributor / shared context; demo store)."""
    for row in review_queue_module_raw_rows():
        if row["evidence_id"] == evidence_id:
            return row
    return None
