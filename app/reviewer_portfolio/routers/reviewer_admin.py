from fastapi import APIRouter

from app.reviewer_portfolio.schemas.reviewer_admin import (
    ReviewerListResponse,
    ReviewerMutationResponse,
    ReviewerProjectAccessResponse,
    ReviewerProjectAccessUpdateRequest,
    ReviewerStatusUpdateRequest,
)
from app.reviewer_portfolio.services.reviewer_admin_service import (
    delete_reviewer,
    get_reviewer_project_access,
    list_reviewers,
    save_reviewer_project_access,
    update_reviewer_status,
)

router = APIRouter(prefix="/reviewers", tags=["reviewer-admin"])


@router.get("", response_model=ReviewerListResponse, response_model_by_alias=True)
async def get_reviewers() -> ReviewerListResponse:
    return await list_reviewers()


@router.get(
    "/{reviewer_id}/project-access",
    response_model=ReviewerProjectAccessResponse,
    response_model_by_alias=True,
)
async def get_reviewer_access(reviewer_id: str) -> ReviewerProjectAccessResponse:
    return await get_reviewer_project_access(reviewer_id)


@router.put(
    "/{reviewer_id}/project-access",
    response_model=ReviewerMutationResponse,
    response_model_by_alias=True,
)
async def put_reviewer_access(
    reviewer_id: str,
    body: ReviewerProjectAccessUpdateRequest,
) -> ReviewerMutationResponse:
    return await save_reviewer_project_access(reviewer_id, body)


@router.patch(
    "/{reviewer_id}/status",
    response_model=ReviewerMutationResponse,
    response_model_by_alias=True,
)
async def patch_reviewer_status(
    reviewer_id: str,
    body: ReviewerStatusUpdateRequest,
) -> ReviewerMutationResponse:
    return await update_reviewer_status(reviewer_id, body.is_active)


@router.delete(
    "/{reviewer_id}",
    response_model=ReviewerMutationResponse,
    response_model_by_alias=True,
)
async def remove_reviewer(reviewer_id: str) -> ReviewerMutationResponse:
    return await delete_reviewer(reviewer_id)
