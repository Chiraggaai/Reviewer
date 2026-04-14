from fastapi import APIRouter

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.schemas import ActionItemsResponse, DashboardAlerts, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    response_model_by_alias=True,
)
def get_summary() -> DashboardSummary:
    """Top four metric cards + optional overdue banner payload."""
    data = mock_store.get_dashboard_summary()
    return DashboardSummary.model_validate(data)


@router.get(
    "/alerts",
    response_model=DashboardAlerts | None,
    response_model_by_alias=True,
)
def get_alerts() -> DashboardAlerts | None:
    """Global notification banner (overdue reviews)."""
    data = mock_store.get_dashboard_summary()
    alerts = data.get("alerts")
    if not alerts:
        return None
    return DashboardAlerts.model_validate(alerts)


@router.get(
    "/action-items",
    response_model=ActionItemsResponse,
    response_model_by_alias=True,
)
def get_action_items() -> ActionItemsResponse:
    """Prioritized list: SLA breach, due today, checkpoints, unread Q&A."""
    data = mock_store.action_items()
    return ActionItemsResponse.model_validate(data)
