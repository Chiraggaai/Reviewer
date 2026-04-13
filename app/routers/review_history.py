"""
Review History (Records) — list, agreement summary, detail, PDF stub.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.service import mock_store
from app.service import review_history_service
from app.schema.review_history_schemas import ReviewHistoryTab

router = APIRouter(prefix="/reviewer/history", tags=["Review History"])


def _env(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


@router.get("")
def get_review_history(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
    tab: ReviewHistoryTab = Query(
        default=ReviewHistoryTab.ALL,
        description="All | recommended_accept | recommended_rework | overridden",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """
    Immutable submitted reviews: agreement banner (last up to 4) + filterable list.
    List is chronological (oldest first). Use ``offset``/``limit`` for pagination.
    """
    payload = review_history_service.list_history(
        reviewer_user_id,
        tab=tab,
        limit=limit,
        offset=offset,
    )
    return _env("Review history", payload.model_dump(by_alias=True))


@router.get("/{record_id}")
def get_review_history_detail(
    record_id: str,
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """Expanded card: rubric scores, overall assessment, PDF path."""
    detail = review_history_service.get_history_detail(reviewer_user_id, record_id)
    return _env("Review history detail", detail.model_dump(by_alias=True))


@router.get("/{record_id}/review-record-pdf")
def get_review_record_pdf_metadata(
    record_id: str,
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """Demo: returns filename + message; production would stream PDF or signed URL."""
    meta = review_history_service.get_review_record_pdf_meta(reviewer_user_id, record_id)
    return _env("Review record PDF (mock)", meta.model_dump(by_alias=True))
