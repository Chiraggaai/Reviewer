from fastapi import APIRouter

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.schemas.schemas import ActiveTaskItem, ActiveTasksResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/active",
    response_model=ActiveTasksResponse,
    response_model_by_alias=True,
)
def get_active_tasks() -> ActiveTasksResponse:
    """Active Task Signal strip (submitted / in progress / rework)."""
    raw = mock_store.active_tasks()
    items = [ActiveTaskItem.model_validate(x) for x in raw]
    return ActiveTasksResponse(items=items, total=len(items))
