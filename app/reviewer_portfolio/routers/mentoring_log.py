"""
Mentoring Log — student contributors, notes list, add note.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path, Query

from app.reviewer_portfolio.services import mock_store
from app.reviewer_portfolio.services import mentoring_service
from app.reviewer_portfolio.schemas.mentoring_schemas import MentoringNoteCreateRequest

router = APIRouter(prefix="/reviewer/mentoring", tags=["Mentoring Log"])


def _env(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


@router.get("/contributors")
def get_mentoring_contributors(
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """Cards: display id, student badge (always true in demo), tasks, acceptance %, note count."""
    payload = mentoring_service.list_contributors(reviewer_user_id)
    return _env("Mentoring contributors", payload.model_dump(by_alias=True))


@router.get("/contributors/{contributor_id}/notes")
def get_mentoring_notes(
    contributor_id: str = Path(..., description="contributorId from the list payload"),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """Expanded card: full note history, newest first."""
    payload = mentoring_service.list_notes(reviewer_user_id, contributor_id)
    return _env("Mentoring notes", payload.model_dump(by_alias=True))


@router.post("/contributors/{contributor_id}/notes")
def post_mentoring_note(
    body: MentoringNoteCreateRequest,
    contributor_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """Add note (category + body, min 20 chars)."""
    out = mentoring_service.add_note(reviewer_user_id, contributor_id, body)
    return _env("Note saved", out.model_dump(by_alias=True))
