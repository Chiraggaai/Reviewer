from fastapi import APIRouter

from app.reviewer_portfolio.schemas.reviewer_invitation import (
    ReviewerInvitationCreate,
    ReviewerInvitationResponse,
)
from app.reviewer_portfolio.services.reviewer_invitation_service import (
    create_reviewer_invitation,
)

router = APIRouter(prefix="/reviewers", tags=["reviewer-admin"])


@router.post(
    "/invitations",
    response_model=ReviewerInvitationResponse,
    summary="Invite a reviewer",
    description=(
        "Creates a reviewer account in the database with a temporary password and emails "
        "credentials to the invitee."
    ),
)
async def invite_reviewer(
    body: ReviewerInvitationCreate,
) -> ReviewerInvitationResponse:
    return await create_reviewer_invitation(
        body,
        invited_by_user_id="public_api",
    )
