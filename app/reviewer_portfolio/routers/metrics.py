from fastapi import APIRouter, Query

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.schemas import SLAPerformanceResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/me/sla-performance",
    response_model=SLAPerformanceResponse,
    response_model_by_alias=True,
)
def get_my_sla_performance(
    period: str = Query(
        default="month",
        description="Aggregation window, e.g. month, week, quarter",
    ),
) -> SLAPerformanceResponse:
    """SLA sidebar: compliance, acceptance, avg time, volume."""
    data = mock_store.sla_performance(period=period)
    return SLAPerformanceResponse.model_validate(data)
