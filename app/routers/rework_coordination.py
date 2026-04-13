"""
Module 7 — Rework Coordination (reviewer notifications).
Enterprise confirm, contributor rework notifications / feedback / resubmit live in other modules.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.service import mock_store
from app.schema.rework_schemas import NotificationRecipient
from app.service import rework_coordination_service

router = APIRouter(tags=["Module 7 — Rework Coordination"])


def _ok(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


@router.get("/reviewer/rework/notifications")
def reviewer_rework_notifications(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """§7.1 / §7.4 — HIGH priority in-app notification list (demo store)."""
    items = rework_coordination_service.list_notifications(
        recipient=NotificationRecipient.REVIEWER,
        reviewer_user_id=reviewer_user_id,
    )
    return _ok(
        "Reviewer notifications",
        [n.model_dump(by_alias=True) for n in items],
    )
