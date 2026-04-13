"""
Module 8 — Workroom Q&A (reviewer + legacy §7.3 paths).
Contributor ``/contributor/evidence/.../qa/*`` routes live in the contributor module.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.service import mock_store
from app.schema.qa_schemas import QaReviewerPostRequest
from app.service import qa_service
from app.schema.rework_schemas import WorkroomPostMessageRequest

router = APIRouter(tags=["Module 8 — Workroom Q&A"])


def _ok(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def _parse_opt_date(name: str, raw: Optional[str]) -> Optional[date]:
    if raw is None or not str(raw).strip():
        return None
    try:
        return date.fromisoformat(str(raw).strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{name} must be an ISO date (YYYY-MM-DD).",
        ) from None


# --- Reviewer (assigned only) ---


@router.get("/reviewer/evidence/{evidence_id}/qa/context")
def reviewer_qa_context(
    evidence_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    ctx = qa_service.get_page_context_reviewer(evidence_id, reviewer_user_id)
    return _ok("Workroom Q&A context", ctx.model_dump(by_alias=True))


@router.get("/reviewer/evidence/{evidence_id}/qa/messages")
def reviewer_qa_messages(
    evidence_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
    search: Optional[str] = Query(default=None, description="Applied when length >= 3"),
    from_date: Optional[str] = Query(default=None, alias="fromDate"),
    to_date: Optional[str] = Query(default=None, alias="toDate"),
) -> dict[str, Any]:
    qa_service.assert_reviewer_assigned(evidence_id, reviewer_user_id)
    fd = _parse_opt_date("fromDate", from_date)
    td = _parse_opt_date("toDate", to_date)
    page = qa_service.list_messages_page(evidence_id, search=search, from_date=fd, to_date=td)
    return _ok("Workroom Q&A messages", page.model_dump(by_alias=True))


@router.post("/reviewer/evidence/{evidence_id}/qa/messages")
def reviewer_qa_post(
    body: QaReviewerPostRequest,
    evidence_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    msg = qa_service.post_reviewer_message(evidence_id, reviewer_user_id, body)
    return _ok("Message posted", msg.model_dump(by_alias=True))


@router.get("/reviewer/evidence/{evidence_id}/qa/files/{file_id}/metadata")
def reviewer_qa_file_metadata(
    evidence_id: str = Path(...),
    file_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """Same download contract as the Evidence Pack; use for Workroom file chips."""
    qa_service.assert_reviewer_assigned(evidence_id, reviewer_user_id)
    from app.service import evidence_pack_service

    meta = evidence_pack_service.mock_file_download_info(evidence_id, file_id)
    return _ok("File metadata (mock)", meta)


# --- Legacy §7.3 (same paths as earlier mock) ---


@router.get("/workroom/evidence/{evidence_id}/qanda/messages")
def legacy_list_qanda(evidence_id: str = Path(...)) -> dict[str, Any]:
    qa_service.assert_evidence_known(evidence_id)
    items = qa_service.list_legacy_workroom_messages(evidence_id)
    return _ok("Workroom messages", [m.model_dump(by_alias=True) for m in items])


@router.post("/workroom/evidence/{evidence_id}/qanda/messages")
def legacy_post_qanda(
    body: WorkroomPostMessageRequest,
    evidence_id: str = Path(...),
) -> dict[str, Any]:
    msg = qa_service.post_legacy_workroom_message(evidence_id, body)
    return _ok("Message posted", msg.model_dump(by_alias=True))
