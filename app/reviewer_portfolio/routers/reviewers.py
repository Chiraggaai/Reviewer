from fastapi import APIRouter

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.schemas import DashboardAlerts

router = APIRouter(prefix="/reviewers", tags=["reviewers"])


@router.get(
    "/me/notifications",
    response_model=DashboardAlerts | None,
    response_model_by_alias=True,
)
def get_my_notifications() -> DashboardAlerts | None:
    """Banner-only payload (same source as /dashboard/alerts)."""
    data = mock_store.get_dashboard_summary()
    alerts = data.get("alerts")
    if not alerts:
        return None
    return DashboardAlerts.model_validate(alerts)
