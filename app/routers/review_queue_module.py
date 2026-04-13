"""
Review Queue (module 5.x) — standalone Reviewer API (no Glimmora monolith).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query

from app.service import mock_store
from app.schema.review_queue_schemas import ReviewQueueSort, ReviewQueueTab
from app.service import review_queue_service

router = APIRouter(prefix="/reviewer", tags=["Review Queue"])


def _envelope(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


@router.get("/review-queue")
def get_review_queue(
    tab: ReviewQueueTab = Query(default=ReviewQueueTab.ALL),
    sort: ReviewQueueSort = Query(default=ReviewQueueSort.SLA_DEADLINE_SOONEST),
    project_id: Optional[str] = Query(default=None, alias="projectId"),
    reviewer_user_id: str = Query(
        default=mock_store.DEMO_REVIEWER_ID,
        alias="reviewerUserId",
        description="Demo store reviewer id; use 'unassigned-reviewer' for empty-state tests.",
    ),
) -> dict[str, Any]:
    payload = review_queue_service.get_review_queue(
        reviewer_user_id,
        tab=tab,
        sort=sort,
        project_id=project_id,
    )
    return _envelope("Review Queue", payload.model_dump(by_alias=True))


@router.get("/review-queue/tab-counts")
def get_review_queue_tab_counts(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    counts = review_queue_service.get_tab_counts(reviewer_user_id)
    return _envelope("Review Queue tab counts", counts.model_dump(by_alias=True))


@router.get("/review-queue/projects")
def get_review_queue_projects(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    data = review_queue_service.list_project_options(reviewer_user_id)
    return _envelope("Assigned projects for Review Queue filter", data.model_dump(by_alias=True))
