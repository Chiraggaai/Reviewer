from fastapi import APIRouter, HTTPException, Query

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.schemas import ReviewDetail, ReviewQueueItem, ReviewQueueResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get(
    "/queue",
    response_model=ReviewQueueResponse,
    response_model_by_alias=True,
)
def get_review_queue(
    status: str | None = Query(
        default="pending",
        description="Filter by review status",
    ),
    overdue_only: bool = Query(default=False, alias="overdueOnly"),
) -> ReviewQueueResponse:
    """Review Queue section: pending items with due labels."""
    items = mock_store.review_queue_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if overdue_only:
        items = [x for x in items if x.get("isOverdue")]
    # Strip internal status from response
    out = []
    for x in items:
        row = {k: v for k, v in x.items() if k != "status"}
        out.append(ReviewQueueItem.model_validate(row))
    return ReviewQueueResponse(items=out, total=len(out))


@router.get(
    "/{review_id}",
    response_model=ReviewDetail,
    response_model_by_alias=True,
)
def get_review(review_id: str) -> ReviewDetail:
    """Single review for Open Review / deep links."""
    detail = mock_store.review_detail(review_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewDetail.model_validate(detail)
