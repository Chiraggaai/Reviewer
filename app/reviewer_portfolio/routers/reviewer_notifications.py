"""
Module 10 — Reviewer notification bell: list (deep links), unread count, mark read (§10.2).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.services import rework_coordination_service
from app.reviewer_portfolio.schemas.rework_schemas import (
    ReviewerNotificationEventType,
    ReviewerNotificationListPayload,
    ReviewerNotificationMarkAllReadPayload,
    ReviewerNotificationMarkReadPayload,
    ReviewerNotificationUnreadPayload,
)

router = APIRouter(prefix="/reviewer/notifications", tags=["Module 10 — Reviewer notifications"])


def _env(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def _parse_opt_date(name: str, raw: Optional[str]) -> Optional[date]:
    if raw is None or not str(raw).strip():
        return None
    try:
        return date.fromisoformat(str(raw).strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{name} must be an ISO date (YYYY-MM-DD).",
        ) from None


@router.get("")
def get_reviewer_notifications(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
    limit: int = Query(default=20, ge=1, le=100, description="§10.2 panel default 20"),
    offset: int = Query(default=0, ge=0),
    event_type: Optional[ReviewerNotificationEventType] = Query(
        default=None,
        alias="eventType",
        description="Filter by §10.1 event type (optional).",
    ),
    from_date: Optional[str] = Query(default=None, alias="fromDate"),
    to_date: Optional[str] = Query(default=None, alias="toDate"),
) -> dict[str, Any]:
    """Bell panel and full history: each item includes ``deepLinkPath`` + ``ctaLabel`` for SPA routing."""
    fd = _parse_opt_date("fromDate", from_date)
    td = _parse_opt_date("toDate", to_date)
    et = event_type.value if event_type is not None else None
    payload = rework_coordination_service.list_reviewer_notifications_feed(
        reviewer_user_id,
        limit=limit,
        offset=offset,
        event_type=et,
        from_date=fd,
        to_date=td,
    )
    return _env("Reviewer notifications", payload.model_dump(by_alias=True))


@router.get("/unread-count")
def get_reviewer_unread_count(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    n = rework_coordination_service.reviewer_notification_unread_count(reviewer_user_id)
    body = ReviewerNotificationUnreadPayload(unread_count=n)
    return _env("Unread count", body.model_dump(by_alias=True))


@router.post("/mark-all-read")
def post_mark_all_notifications_read(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    marked = rework_coordination_service.mark_all_reviewer_notifications_read(reviewer_user_id)
    body = ReviewerNotificationMarkAllReadPayload(marked_count=marked)
    return _env("Marked all read", body.model_dump(by_alias=True))


@router.post("/{notification_id}/read")
def post_mark_notification_read(
    notification_id: str = Path(..., description="Notification id from the list payload"),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    ok = rework_coordination_service.mark_reviewer_notification_read(notification_id, reviewer_user_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    body = ReviewerNotificationMarkReadPayload(updated=True)
    return _env("Notification marked read", body.model_dump(by_alias=True))


@router.get("/event-types")
def list_notification_event_types() -> dict[str, Any]:
    """Values for ``eventType`` filter (§10.1 matrix + shared enums)."""
    return _env(
        "Event types",
        {"eventTypes": [e.value for e in ReviewerNotificationEventType]},
    )
