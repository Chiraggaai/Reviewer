"""
Module 7 — Rework Coordination (mock store + hooks from Evidence Pack submit).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.evidence_pack_schemas import ReworkPhaseUiHints
from app.reviewer_portfolio.schemas.rework_schemas import (
    ContributorResubmitResponse,
    ContributorReworkFeedbackResponse,
    ContributorRubricFeedbackRow,
    EnterpriseReworkConfirmRequest,
    EnterpriseReworkConfirmResponse,
    NotificationPriority,
    NotificationRecipient,
    ReviewerNotificationEventType,
    ReviewerNotificationListPayload,
    ReworkNotification,
)

UTC = timezone.utc

# evidence_id -> state
_rework_by_evidence: dict[str, dict[str, Any]] = {}
_notifications: list[dict[str, Any]] = []
_expand_previous_next_open: dict[str, bool] = {}
_notif_seq = 0


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _next_notif_id() -> str:
    global _notif_seq
    _notif_seq += 1
    return f"n{_notif_seq}"


def _append_notification(
    *,
    recipient: NotificationRecipient,
    priority: NotificationPriority,
    title: str,
    body: str,
    evidence_id: str,
    workroom_href: Optional[str] = None,
    event_type: str = ReviewerNotificationEventType.GENERIC.value,
    deep_link_path: Optional[str] = None,
    cta_label: str = "Open",
) -> None:
    if deep_link_path is None:
        if recipient == NotificationRecipient.CONTRIBUTOR:
            deep_link_path = f"/contributor/evidence/{evidence_id}/workroom"
        else:
            deep_link_path = f"/reviewer/evidence/{evidence_id}/review"
    wh = workroom_href if workroom_href is not None else deep_link_path
    _notifications.append(
        {
            "id": _next_notif_id(),
            "recipient": recipient.value,
            "priority": priority.value,
            "title": title,
            "body": body,
            "workroomHref": wh,
            "evidenceId": evidence_id,
            "createdAt": _now().isoformat(),
            "read": False,
            "eventType": event_type,
            "deepLinkPath": deep_link_path,
            "ctaLabel": cta_label,
        }
    )


def publish_notification(
    *,
    recipient: NotificationRecipient,
    priority: NotificationPriority,
    title: str,
    body: str,
    evidence_id: str,
    workroom_href: Optional[str] = None,
    event_type: str = ReviewerNotificationEventType.GENERIC.value,
    deep_link_path: Optional[str] = None,
    cta_label: str = "Open",
) -> None:
    """Used by the Q&A module so workroom messages and rework alerts share one inbox."""
    _append_notification(
        recipient=recipient,
        priority=priority,
        title=title,
        body=body,
        evidence_id=evidence_id,
        workroom_href=workroom_href,
        event_type=event_type,
        deep_link_path=deep_link_path,
        cta_label=cta_label,
    )


def _parse_notif_created_at(n: dict[str, Any]) -> datetime:
    ts_raw = n["createdAt"].replace("Z", "+00:00") if "Z" in n["createdAt"] else n["createdAt"]
    return datetime.fromisoformat(ts_raw)


def _default_deep_link_and_cta(n: dict[str, Any]) -> tuple[str, str]:
    if n.get("deepLinkPath"):
        return str(n["deepLinkPath"]), str(n.get("ctaLabel") or "Open")
    wh = n.get("workroomHref")
    if wh and wh not in ("", "/workroom"):
        return str(wh), str(n.get("ctaLabel") or "Open")
    eid = n["evidenceId"]
    if n["recipient"] == NotificationRecipient.CONTRIBUTOR.value:
        return f"/contributor/evidence/{eid}/workroom", "Open Workroom"
    return f"/reviewer/evidence/{eid}/review", "Open Review"


def _dict_to_rework_notification(n: dict[str, Any]) -> ReworkNotification:
    deep, cta = _default_deep_link_and_cta(n)
    et = n.get("eventType") or ReviewerNotificationEventType.LEGACY.value
    return ReworkNotification(
        id=n["id"],
        recipient=NotificationRecipient(n["recipient"]),
        priority=NotificationPriority(n["priority"]),
        title=n["title"],
        body=n["body"],
        workroom_href=n.get("workroomHref") or deep,
        evidence_id=n["evidenceId"],
        created_at=_parse_notif_created_at(n),
        read=bool(n.get("read", False)),
        event_type=str(et),
        deep_link_path=deep,
        cta_label=cta,
    )


def _reviewer_notif_matches_filters(
    n: dict[str, Any],
    reviewer_user_id: str,
    event_type: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    if n["recipient"] != NotificationRecipient.REVIEWER.value:
        return False
    if reviewer_user_id != mock_store.DEMO_REVIEWER_ID:
        return False
    et = n.get("eventType") or ReviewerNotificationEventType.LEGACY.value
    if event_type and str(et) != event_type:
        return False
    d = _parse_notif_created_at(n).date()
    if from_date is not None and d < from_date:
        return False
    if to_date is not None and d > to_date:
        return False
    return True


def list_reviewer_notifications_feed(
    reviewer_user_id: str,
    *,
    limit: int = 20,
    offset: int = 0,
    event_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> ReviewerNotificationListPayload:
    """§10.2 — Newest first; default ``limit=20`` matches bell panel."""
    lim = max(1, min(limit, 100))
    off = max(0, offset)
    ordered = [
        n
        for n in reversed(_notifications)
        if _reviewer_notif_matches_filters(n, reviewer_user_id, event_type, from_date, to_date)
    ]
    total = len(ordered)
    page = ordered[off : off + lim]
    return ReviewerNotificationListPayload(
        notifications=[_dict_to_rework_notification(n) for n in page],
        total_matching=total,
        limit=lim,
        offset=off,
    )


def reviewer_notification_unread_count(reviewer_user_id: str) -> int:
    if reviewer_user_id != mock_store.DEMO_REVIEWER_ID:
        return 0
    return sum(
        1
        for n in _notifications
        if n["recipient"] == NotificationRecipient.REVIEWER.value and not n.get("read")
    )


def mark_reviewer_notification_read(notification_id: str, reviewer_user_id: str) -> bool:
    if reviewer_user_id != mock_store.DEMO_REVIEWER_ID:
        return False
    for n in _notifications:
        if n["id"] != notification_id:
            continue
        if n["recipient"] != NotificationRecipient.REVIEWER.value:
            return False
        n["read"] = True
        return True
    return False


def mark_all_reviewer_notifications_read(reviewer_user_id: str) -> int:
    if reviewer_user_id != mock_store.DEMO_REVIEWER_ID:
        return 0
    marked = 0
    for n in _notifications:
        if n["recipient"] != NotificationRecipient.REVIEWER.value:
            continue
        if not n.get("read"):
            n["read"] = True
            marked += 1
    return marked


def on_reviewer_submitted_rework(
    *,
    evidence_id: str,
    review_record_id: str,
    task_name: str,
    payload: dict[str, Any],
    rework_round: int,
) -> None:
    """Called when reviewer POSTs RECOMMEND REWORK (before Enterprise confirms)."""
    if (payload.get("recommendation") or "").upper() != "REWORK":
        return
    dl = payload.get("suggestedRevisedDeadline")
    _rework_by_evidence[evidence_id] = {
        "phase": "PENDING_ENTERPRISE_DECISION",
        "review_record_id": review_record_id,
        "task_name": task_name,
        "reviewer_payload_snapshot": payload,
        "rework_round_at_review": rework_round,
        "resubmission_deadline": dl,
        "admin_internal_notes": None,
    }


def confirm_enterprise_rework(body: EnterpriseReworkConfirmRequest) -> EnterpriseReworkConfirmResponse:
    eid = body.evidence_id
    st = _rework_by_evidence.get(eid)
    if not st:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No pending rework flow for this evidence id.",
        )
    if st.get("phase") != "PENDING_ENTERPRISE_DECISION":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Enterprise decision already recorded for this evidence.",
        )
    if not body.confirm_rework:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="confirmRework must be true for this demo.")

    st["phase"] = "REWORK_REQUIRED"
    st["admin_internal_notes"] = (body.enterprise_admin_internal_notes or "").strip() or None

    task_name = st.get("task_name") or eid
    rnd = int(st.get("rework_round_at_review") or 1)
    dl_raw = st.get("resubmission_deadline") or ""
    try:
        dl = date.fromisoformat(str(dl_raw)) if dl_raw else _now().date()
    except ValueError:
        dl = _now().date()
    dl_disp = dl.strftime("%d %b %Y")

    _append_notification(
        recipient=NotificationRecipient.REVIEWER,
        priority=NotificationPriority.HIGH,
        title="Rework decision confirmed",
        body=(
            f"Rework required for {task_name} — Round {rnd} of 3. "
            f"The Enterprise has confirmed your rework recommendation. "
            f"Resubmission deadline: {dl_disp}."
        ),
        evidence_id=eid,
        event_type=ReviewerNotificationEventType.REWORK_DECISION_CONFIRMED_REVIEWER.value,
        deep_link_path=f"/reviewer/evidence/{eid}/workroom",
        cta_label="Open Workroom",
    )
    _append_notification(
        recipient=NotificationRecipient.CONTRIBUTOR,
        priority=NotificationPriority.HIGH,
        title="Rework decision confirmed",
        body=(
            f"Rework required for {task_name} — Round {rnd} of 3. "
            f"Review the feedback below and resubmit by {dl_disp}."
        ),
        evidence_id=eid,
        event_type=ReviewerNotificationEventType.REWORK_DECISION_CONFIRMED_CONTRIBUTOR.value,
        deep_link_path=f"/contributor/evidence/{eid}/workroom",
        cta_label="Open Workroom",
    )

    return EnterpriseReworkConfirmResponse(
        success=True,
        evidence_id=eid,
        task_status="REWORK_REQUIRED",
        message="Rework confirmed; Reviewer and Contributor notified (HIGH).",
    )


def list_notifications(
    *,
    recipient: NotificationRecipient,
    reviewer_user_id: Optional[str] = None,
) -> list[ReworkNotification]:
    out: list[ReworkNotification] = []
    for n in reversed(_notifications):
        if n["recipient"] != recipient.value:
            continue
        if recipient == NotificationRecipient.REVIEWER and reviewer_user_id:
            if reviewer_user_id != mock_store.DEMO_REVIEWER_ID:
                continue
        out.append(_dict_to_rework_notification(n))
    return out


def get_contributor_rework_feedback(evidence_id: str) -> ContributorReworkFeedbackResponse:
    st = _rework_by_evidence.get(evidence_id)
    if not st or st.get("phase") != "REWORK_REQUIRED":
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Rework feedback not available (Enterprise must confirm REWORK first).",
        )
    payload = st.get("reviewer_payload_snapshot") or {}
    rows_out: list[ContributorRubricFeedbackRow] = []
    for i, row in enumerate(payload.get("rubricScores") or [], start=1):
        rows_out.append(
            ContributorRubricFeedbackRow(
                criterion_id=str(row.get("criterionId", f"crit_{i}")),
                order=i,
                score=int(row["score"]),
                reviewer_notes=str(row.get("notes", "")),
                attribution="Reviewer",
            )
        )
    dl = payload.get("suggestedRevisedDeadline")
    if not dl:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing deadline on snapshot.")
    dl_date = date.fromisoformat(str(dl))

    return ContributorReworkFeedbackResponse(
        evidence_id=evidence_id,
        task_name=str(st.get("task_name") or evidence_id),
        round_number=int(st.get("rework_round_at_review") or 1),
        resubmission_deadline_display=dl_date.strftime("%d %b %Y"),
        rubric_rows=rows_out,
        areas_of_strength=str(payload.get("areasOfStrength", "")),
        areas_for_improvement=str(payload.get("areasForImprovement", "")),
        specific_rework_requirements=str(payload.get("specificReworkRequirements", "")),
        suggested_revised_deadline=dl_date,
    )


def contributor_resubmit(evidence_id: str, reviewer_user_id: str) -> ContributorResubmitResponse:
    st = _rework_by_evidence.get(evidence_id)
    if not st or st.get("phase") != "REWORK_REQUIRED":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Resubmit only after Enterprise-confirmed REWORK_REQUIRED.",
        )

    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown evidence for reviewer.")

    cur_round = int(row["evidence"].get("rework_round") or 1)
    new_round = cur_round + 1

    mock_store.patch_queue_row(
        evidence_id,
        evidence={
            "rework_round": new_round,
            "submitted_at": _now(),
        },
        assignment={"status": "pending", "updated_at": _now()},
    )

    st["phase"] = "SUBMITTED_AFTER_REWORK"
    _expand_previous_next_open[evidence_id] = True

    from app.reviewer_portfolio.services import evidence_pack_service

    evidence_pack_service.clear_submission_lock(reviewer_user_id, evidence_id)

    task_name = st.get("task_name") or evidence_id
    _append_notification(
        recipient=NotificationRecipient.REVIEWER,
        priority=NotificationPriority.HIGH,
        title="Rework resubmission received",
        body=f"Rework resubmission received for {task_name} — Round {new_round} of 3.",
        evidence_id=evidence_id,
        event_type=ReviewerNotificationEventType.REWORK_RESUBMISSION_RECEIVED.value,
        deep_link_path=f"/reviewer/evidence/{evidence_id}/review",
        cta_label="Open Review",
    )

    return ContributorResubmitResponse(
        success=True,
        evidence_id=evidence_id,
        new_round_number=new_round,
        task_status="SUBMITTED",
        message="New submission created; previous version preserved as Version N-1 (mock).",
        previous_version_preserved=True,
    )


def get_pack_rework_ui_hints(
    evidence_id: str,
    current_rework_round: int,
) -> Optional[ReworkPhaseUiHints]:
    st = _rework_by_evidence.get(evidence_id)
    phase = st.get("phase") if st else None

    expand = _expand_previous_next_open.pop(evidence_id, False)

    banner = None
    if current_rework_round >= 3:
        banner = (
            "This is the contributor's final rework round. If the revised work is still not accepted, "
            "the task will be escalated to GlimmoraTeam Admin for resolution."
        )

    status_hint = phase
    if not expand and not banner and not status_hint:
        return None

    return ReworkPhaseUiHints(
        previous_submission_default_expanded=expand,
        final_rework_round_banner=banner,
        task_rework_phase_status=status_hint,
    )
