"""
Workroom Q&A — in-memory thread per evidence id (demo).
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from app.service import mock_store
from app.schema.qa_schemas import (
    QaAttachmentMeta,
    QaContributorPostRequest,
    QaReviewerPostRequest,
    QandaAuthorRole,
    WorkroomMessagesPage,
    WorkroomPageContext,
    WorkroomQandaMessage,
    qanda_display_label,
)
from app.schema.rework_schemas import (
    NotificationPriority,
    NotificationRecipient,
    ReviewerNotificationEventType,
    WorkroomAuthorRole,
    WorkroomMessage,
    WorkroomPostMessageRequest,
)
from app.service import rework_coordination_service

UTC = timezone.utc

_threads: dict[str, list[dict[str, Any]]] = {}

CHANGE_REQUEST_PREFIX = re.compile(r"^\s*\[CHANGE\s+REQUEST\]\s*", re.IGNORECASE)


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _parse_dt(s: str) -> datetime:
    if "Z" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


def _strip_change_request_prefix(body: str) -> tuple[str, bool]:
    raw = body.strip()
    if CHANGE_REQUEST_PREFIX.match(raw):
        return CHANGE_REQUEST_PREFIX.sub("", raw).strip() or raw, True
    return raw, False


def assert_evidence_known(evidence_id: str) -> None:
    if evidence_id not in mock_store.known_evidence_ids():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown evidence id.")


def assert_reviewer_assigned(evidence_id: str, reviewer_user_id: str) -> dict[str, Any]:
    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    if row is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this evidence.",
        )
    return row


def _row_for_contributor(evidence_id: str) -> dict[str, Any]:
    row = mock_store.find_any_queue_row_by_evidence(evidence_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown evidence id.")
    return row


def get_page_context_reviewer(evidence_id: str, reviewer_user_id: str) -> WorkroomPageContext:
    row = assert_reviewer_assigned(evidence_id, reviewer_user_id)
    a = row["assignment"]
    ev: dict[str, Any] = row["evidence"]
    task_name = (a.get("title") or ev.get("title") or "Evidence review").strip()
    project_name = (ev.get("project_name") or "Project").strip()
    return WorkroomPageContext(
        evidence_id=evidence_id,
        task_name=task_name,
        project_name=project_name,
        evidence_pack_api_path=f"/api/reviewer/evidence/{evidence_id}/pack",
        qa_messages_api_path=f"/api/reviewer/evidence/{evidence_id}/qa/messages",
    )


def get_page_context_contributor(evidence_id: str) -> WorkroomPageContext:
    assert_evidence_known(evidence_id)
    row = _row_for_contributor(evidence_id)
    a = row["assignment"]
    ev: dict[str, Any] = row["evidence"]
    task_name = (a.get("title") or ev.get("title") or "Evidence review").strip()
    project_name = (ev.get("project_name") or "Project").strip()
    return WorkroomPageContext(
        evidence_id=evidence_id,
        task_name=task_name,
        project_name=project_name,
        evidence_pack_api_path=f"/api/reviewer/evidence/{evidence_id}/pack",
        qa_messages_api_path=f"/api/contributor/evidence/{evidence_id}/qa/messages",
    )


def _entry_to_qanda(m: dict[str, Any]) -> WorkroomQandaMessage:
    role = QandaAuthorRole(m["authorRole"])
    atts = m.get("attachments") or []
    attachments = [QaAttachmentMeta.model_validate(a) for a in atts]
    return WorkroomQandaMessage(
        message_id=m["messageId"],
        evidence_id=m["evidenceId"],
        author_role=role,
        display_label=m.get("displayLabel") or qanda_display_label(role),
        body=m["body"],
        flagged_about_feedback=bool(m.get("flaggedAboutFeedback", False)),
        is_change_request=bool(m.get("isChangeRequest", False)),
        created_at=_parse_dt(m["createdAt"]),
        attachments=attachments,
    )


def _filter_messages(
    evidence_id: str,
    *,
    search: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[list[WorkroomQandaMessage], bool]:
    raw = _threads.get(evidence_id, [])
    out: list[WorkroomQandaMessage] = []
    q = (search or "").strip()
    search_applied = len(q) >= 3
    q_low = q.lower() if search_applied else ""

    for m in raw:
        msg = _entry_to_qanda(m)
        if search_applied and q_low not in msg.body.lower():
            continue
        d = msg.created_at.date()
        if from_date is not None and d < from_date:
            continue
        if to_date is not None and d > to_date:
            continue
        out.append(msg)

    out.sort(key=lambda x: x.created_at)
    return out, search_applied


def list_messages_page(
    evidence_id: str,
    *,
    search: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> WorkroomMessagesPage:
    messages, search_applied = _filter_messages(
        evidence_id, search=search, from_date=from_date, to_date=to_date
    )
    return WorkroomMessagesPage(messages=messages, search_applied=search_applied)


def _append_message(
    evidence_id: str,
    *,
    role: QandaAuthorRole,
    body: str,
    flagged_about_feedback: bool,
    attachments: list[QaAttachmentMeta],
    is_change_request: bool,
) -> WorkroomQandaMessage:
    mid = str(uuid.uuid4())[:12]
    ts = _now()
    text, cr = _strip_change_request_prefix(body)
    if cr:
        is_change_request = True
    entry = {
        "messageId": mid,
        "evidenceId": evidence_id,
        "authorRole": role.value,
        "displayLabel": qanda_display_label(role),
        "body": text,
        "flaggedAboutFeedback": flagged_about_feedback,
        "isChangeRequest": is_change_request,
        "createdAt": ts.isoformat(),
        "attachments": [a.model_dump(by_alias=True) for a in attachments],
    }
    _threads.setdefault(evidence_id, []).append(entry)
    return _entry_to_qanda(entry)


def post_reviewer_message(
    evidence_id: str,
    reviewer_user_id: str,
    req: QaReviewerPostRequest,
) -> WorkroomQandaMessage:
    assert_reviewer_assigned(evidence_id, reviewer_user_id)
    msg = _append_message(
        evidence_id,
        role=QandaAuthorRole.REVIEWER,
        body=req.body,
        flagged_about_feedback=req.flag_question_about_feedback,
        attachments=req.attachments,
        is_change_request=False,
    )
    rework_coordination_service.publish_notification(
        recipient=NotificationRecipient.CONTRIBUTOR,
        priority=NotificationPriority.MEDIUM,
        title="New message from Reviewer",
        body=f"A reviewer posted in the workroom Q&A for evidence {evidence_id}.",
        evidence_id=evidence_id,
        event_type=ReviewerNotificationEventType.REVIEWER_QA_MESSAGE.value,
        deep_link_path=f"/contributor/evidence/{evidence_id}/workroom",
        cta_label="Open Workroom",
    )
    return msg


def post_contributor_message(evidence_id: str, req: QaContributorPostRequest) -> WorkroomQandaMessage:
    assert_evidence_known(evidence_id)
    row = _row_for_contributor(evidence_id)
    a: dict[str, Any] = row["assignment"]
    ev: dict[str, Any] = row["evidence"]
    task_name = (a.get("title") or ev.get("title") or "Task").strip()
    project_name = (ev.get("project_name") or "Project").strip()
    msg = _append_message(
        evidence_id,
        role=QandaAuthorRole.CONTRIBUTOR,
        body=req.body,
        flagged_about_feedback=req.flag_question_about_feedback,
        attachments=req.attachments,
        is_change_request=False,
    )
    title = (
        "[CHANGE REQUEST] Contributor update"
        if msg.is_change_request
        else "New message from Contributor"
    )
    body = (
        f"The contributor posted a change request for {task_name} in {project_name}."
        if msg.is_change_request
        else f"New message from Contributor on {task_name} in {project_name}."
    )
    rework_coordination_service.publish_notification(
        recipient=NotificationRecipient.REVIEWER,
        priority=NotificationPriority.HIGH,
        title=title,
        body=body,
        evidence_id=evidence_id,
        event_type=ReviewerNotificationEventType.CONTRIBUTOR_QA_MESSAGE.value,
        deep_link_path=f"/reviewer/evidence/{evidence_id}/workroom",
        cta_label="Open Workroom",
    )
    return msg


def _qanda_role_to_legacy(m: dict[str, Any]) -> tuple[WorkroomAuthorRole, str]:
    role = QandaAuthorRole(m["authorRole"])
    label = m.get("displayLabel") or qanda_display_label(role)
    if role == QandaAuthorRole.REVIEWER:
        return WorkroomAuthorRole.REVIEWER, label
    return WorkroomAuthorRole.CONTRIBUTOR, label


def list_legacy_workroom_messages(evidence_id: str) -> list[WorkroomMessage]:
    """Backward-compatible §7.3 shape (reviewer vs contributor only)."""
    raw = _threads.get(evidence_id, [])
    out: list[WorkroomMessage] = []
    for m in sorted(raw, key=lambda x: x["createdAt"]):
        w_role, label = _qanda_role_to_legacy(m)
        out.append(
            WorkroomMessage(
                message_id=m["messageId"],
                evidence_id=m["evidenceId"],
                author_role=w_role,
                display_label=label,
                body=m["body"],
                flagged_about_feedback=m.get("flaggedAboutFeedback", False),
                created_at=_parse_dt(m["createdAt"]),
            )
        )
    return out


def post_legacy_workroom_message(evidence_id: str, req: WorkroomPostMessageRequest) -> WorkroomMessage:
    """Maps legacy POST to the shared Q&A thread (no rework-phase gate)."""
    assert_evidence_known(evidence_id)
    if req.author_role == WorkroomAuthorRole.REVIEWER:
        q_req = QaReviewerPostRequest(
            body=req.body,
            flag_question_about_feedback=req.flag_question_about_feedback,
            attachments=[],
        )
        post_reviewer_message(evidence_id, mock_store.DEMO_REVIEWER_ID, q_req)
    else:
        q_req = QaContributorPostRequest(
            body=req.body,
            flag_question_about_feedback=req.flag_question_about_feedback,
            attachments=[],
        )
        post_contributor_message(evidence_id, q_req)
    thread = _threads.get(evidence_id, [])
    if not thread:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Message not stored.")
    last = thread[-1]
    w_role, label = _qanda_role_to_legacy(last)
    return WorkroomMessage(
        message_id=last["messageId"],
        evidence_id=evidence_id,
        author_role=w_role,
        display_label=label,
        body=last["body"],
        flagged_about_feedback=last.get("flaggedAboutFeedback", False),
        created_at=_parse_dt(last["createdAt"]),
    )
