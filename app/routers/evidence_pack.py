"""
Evidence Pack Review (module 6.x) — opened from Review Queue [Open Review].
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path, Query

from app.service import mock_store
from app.schema.evidence_pack_schemas import EvidencePackDraftPayload, SubmitRecommendationRequest
from app.service import evidence_pack_service

router = APIRouter(prefix="/reviewer/evidence", tags=["Evidence Pack Review"])


def _env(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


@router.get("/{evidence_id}/pack")
def get_evidence_pack(
    evidence_id: str = Path(..., description="Evidence ID from queue card"),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """§6.1 Full two-panel layout payload: task context, files tab, rubric + AI reference, draft merge."""
    pack = evidence_pack_service.get_evidence_pack(evidence_id, reviewer_user_id)
    return _env("Evidence pack", pack.model_dump(by_alias=True))


@router.put("/{evidence_id}/draft")
def put_evidence_draft(
    body: EvidencePackDraftPayload,
    evidence_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """§6.7 DRAFT-001: save partial rubric / notes / recommendation — no minimum content."""
    out = evidence_pack_service.save_draft(evidence_id, reviewer_user_id, body)
    return _env("Draft saved", out.model_dump(by_alias=True))


@router.post("/{evidence_id}/recommendation")
def post_recommendation(
    body: SubmitRecommendationRequest,
    evidence_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """§6.6 Submit — RUB-001..004 + conditional REWORK fields. Atomic mock record."""
    out = evidence_pack_service.submit_recommendation(evidence_id, reviewer_user_id, body)
    return _env("Recommendation submitted", out.model_dump(by_alias=True))


@router.get("/{evidence_id}/files/{file_id}/download")
def get_file_download_meta(
    evidence_id: str = Path(...),
    file_id: str = Path(...),
) -> dict[str, Any]:
    """§6.2 Per-file download — demo returns metadata; production streams bytes / signed URL."""
    return evidence_pack_service.mock_file_download_info(evidence_id, file_id)


@router.get("/{evidence_id}/files/download-zip")
def get_zip_download_meta(
    evidence_id: str = Path(...),
    reviewer_user_id: str = Query(default=mock_store.DEMO_REVIEWER_ID, alias="reviewerUserId"),
) -> dict[str, Any]:
    """§6.2 Bulk ZIP — filename pattern ``[TaskID]-submission-v[N].zip``."""
    return evidence_pack_service.mock_zip_download_info(evidence_id, reviewer_user_id)
