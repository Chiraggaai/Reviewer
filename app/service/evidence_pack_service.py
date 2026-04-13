"""
Evidence Pack Review — mock-backed pack assembly, drafts (DRAFT-001/002), submit validation (RUB-*).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from app.service import mock_store
from app.schema.evidence_pack_schemas import (
    AcceptanceCriterion,
    ContributorChecklistItem,
    EvidencePackDraftPayload,
    EvidencePackDraftResponse,
    EvidencePackResponse,
    OverallQuality,
    ReworkPhaseUiHints,
    PreviousChecklistState,
    PreviousSubmission,
    PreviousSubmissionFile,
    RecommendationState,
    RecommendationType,
    ReferenceFile,
    RubricRowState,
    RubricScoringTab,
    SubmitRecommendationRequest,
    SubmitRecommendationResponse,
    SubmittedFile,
    SubmittedFilesTab,
    TaskContextPanel,
)

UTC = timezone.utc

_drafts: dict[str, dict[str, Any]] = {}
_submitted_keys: set[str] = set()
_review_records: dict[str, dict[str, Any]] = {}


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _draft_key(reviewer_user_id: str, evidence_id: str) -> str:
    return f"{reviewer_user_id}:{evidence_id}"


def get_latest_review_record(evidence_id: str) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_ts = ""
    for r in _review_records.values():
        if r.get("evidence_id") != evidence_id:
            continue
        ts = str(r.get("created_at") or "")
        if ts >= best_ts:
            best_ts = ts
            best = r
    return best


def get_review_record(record_id: str) -> dict[str, Any] | None:
    """Immutable submit snapshot for Review History detail."""
    return _review_records.get(record_id)


def list_review_records_for_reviewer(reviewer_user_id: str) -> list[tuple[str, dict[str, Any]]]:
    """(record_id, record) pairs for the given reviewer, arbitrary order."""
    return [
        (rid, rec)
        for rid, rec in _review_records.items()
        if rec.get("reviewer_user_id") == reviewer_user_id
    ]


def criterion_labels_for_evidence(evidence_id: str) -> dict[str, str]:
    """Map criterionId -> display text for history / read-only views."""
    return {c["criterionId"]: c["text"] for c in _criterion_template(evidence_id)}


def clear_submission_lock(reviewer_user_id: str, evidence_id: str) -> None:
    _submitted_keys.discard(_draft_key(reviewer_user_id, evidence_id))


def _add_business_days(start: date, business_days: int) -> date:
    d = start
    added = 0
    while added < business_days:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


def _pass_fail(score: int) -> str:
    return "FAIL" if score <= 2 else "PASS"


def _criterion_template(evidence_id: str) -> list[dict[str, Any]]:
    """Shared 3 criteria; AI hints vary slightly by pack."""
    base_ai = {
        "ev_fin_gl": [(4, "Strong reconciliation coverage; minor gap on FX."), (3, "Adequate tie-out steps."), (4, "Good narrative.")],
        "ev_hr_emp": [(4, "Employee records mostly complete."), (3, "Some ID redaction inconsistent."), (4, "Retention policy cited.")],
        "ev_pat_r2": [(3, "Policy refs improved vs v1."), (2, "HIPAA checklist still partial."), (3, "Screenshots clearer.")],
        "ev_done_1": [(5, "Excellent API evidence."), (5, "Thorough test matrix."), (4, "Minor doc typo.")],
        "ev_breach": [(2, "Timeout handling missing."), (3, "Partial error model."), (2, "Logs incomplete.")],
    }
    ai = base_ai.get(
        evidence_id,
        [(3, "Generic adequate."), (3, "Generic adequate."), (3, "Generic adequate.")],
    )
    texts = [
        "Deliverable implements the agreed data model and passes schema validation.",
        "Error handling covers API timeout and 5xx paths with user-safe messaging.",
        "Documentation lists test evidence and links to automated run artifacts.",
    ]
    rows = []
    for i, (t, (s, r)) in enumerate(zip(texts, ai, strict=False), start=1):
        rows.append(
            {
                "criterionId": f"crit_{i}",
                "order": i,
                "text": t,
                "aiSuggestedScore": s,
                "aiRationale": r,
            }
        )
    return rows


def _files_for(evidence_id: str, when: datetime) -> list[dict[str, Any]]:
    return [
        {
            "fileId": f"{evidence_id}_f1",
            "filename": "evidence-summary.pdf",
            "fileTypeBadge": "PDF",
            "sizeBytes": 482_000,
            "uploadedAt": when - timedelta(hours=2),
            "previewSupported": True,
        },
        {
            "fileId": f"{evidence_id}_f2",
            "filename": "screenshots.zip",
            "fileTypeBadge": "ZIP",
            "sizeBytes": 1_024_000,
            "uploadedAt": when - timedelta(hours=2),
            "previewSupported": False,
        },
    ]


def get_evidence_pack(evidence_id: str, reviewer_user_id: str) -> EvidencePackResponse:
    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Evidence pack not found for this reviewer.")

    a = row["assignment"]
    ev = row["evidence"]
    ast = (a.get("status") or "pending").lower()
    rework_round = int(ev.get("rework_round") or 1)
    now = _utc_now()
    submitted_at = ev.get("submitted_at") or a.get("created_at") or now
    if isinstance(submitted_at, datetime) and submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=UTC)

    task_deadline = submitted_at + timedelta(days=14)
    assignment_id = str(a["_id"])

    criteria = _criterion_template(evidence_id)

    status_badge = {
        "pending": "PENDING_REVIEW",
        "in_progress": "UNDER_REVIEW",
        "completed": "COMPLETED",
    }.get(ast, "PENDING_REVIEW")

    submission_notes = (
        "Uploaded revised policy PDF per last round feedback."
        if rework_round >= 2
        else None
    )

    ref_files = [
        ReferenceFile(
            file_id="ref_sow_excerpt",
            filename="SOW_Decomposition_Excerpt.pdf",
            file_type_badge="PDF",
            size_bytes=120_000,
            uploaded_at=now - timedelta(days=30),
            download_path=f"/api/reviewer/evidence/{evidence_id}/files/ref_sow_excerpt/download",
            preview_supported=True,
        )
    ]

    task_ctx = TaskContextPanel(
        task_name=a.get("title") or "Evidence review",
        status_badge=status_badge,
        task_instructions_html=(
            "<p>Verify the submission against the acceptance criteria below. "
            "Use the rubric tab to score each criterion independently.</p>"
        ),
        acceptance_criteria=[
            AcceptanceCriterion(criterion_id=c["criterionId"], order=c["order"], text=c["text"])
            for c in criteria
        ],
        task_deadline=task_deadline,
        reference_materials=ref_files,
        submission_notes_contributor=submission_notes,
    )

    file_rows = _files_for(evidence_id, submitted_at if isinstance(submitted_at, datetime) else now)
    sfiles = [
        SubmittedFile(
            file_id=f["fileId"],
            filename=f["filename"],
            file_type_badge=f["fileTypeBadge"],
            size_bytes=f["sizeBytes"],
            uploaded_at=f["uploadedAt"],
            download_path=f"/api/reviewer/evidence/{evidence_id}/files/{f['fileId']}/download",
            preview_supported=f["previewSupported"],
        )
        for f in file_rows
    ]

    checklist = [
        ContributorChecklistItem(
            criterion_id=c["criterionId"],
            order=c["order"],
            criterion_text=c["text"],
            checked_by_contributor=True if c["order"] <= 2 else False,
            contributor_notes="See section 2 in PDF." if c["order"] == 1 else None,
        )
        for c in criteria
    ]

    prev_sub: Optional[PreviousSubmission] = None
    if rework_round >= 2:
        prev_sub = PreviousSubmission(
            version_label="Previous Submission (Version 1)",
            round_number=rework_round - 1,
            files=[
                PreviousSubmissionFile(file_id=f"{evidence_id}_v1_a", filename="old-pack.pdf"),
            ],
            checklist_state=[
                PreviousChecklistState(criterion_id="crit_1", checked=True),
                PreviousChecklistState(
                    criterion_id="crit_2", checked=False, contributor_notes="Pending"
                ),
                PreviousChecklistState(criterion_id="crit_3", checked=True),
            ],
        )

    zip_name = f"{assignment_id}-submission-v{rework_round}.zip"
    files_tab = SubmittedFilesTab(
        files=sfiles,
        bulk_zip_download_path=f"/api/reviewer/evidence/{evidence_id}/files/download-zip",
        bulk_zip_filename_hint=zip_name,
        submission_notes=submission_notes,
        contributor_checklist=checklist,
        previous_submission=prev_sub,
    )

    dk = _draft_key(reviewer_user_id, evidence_id)
    draft = _drafts.get(dk, {})

    rubric_rows: list[RubricRowState] = []
    draft_rubric = {r["criterionId"]: r for r in draft.get("rubric", []) if isinstance(r, dict)}

    for c in criteria:
        cid = c["criterionId"]
        dr = draft_rubric.get(cid, {})
        sc = dr.get("score")
        notes = dr.get("notes")
        badge = _pass_fail(int(sc)) if sc is not None else None
        rubric_rows.append(
            RubricRowState(
                criterion_id=cid,
                order=c["order"],
                criterion_text=c["text"],
                score=sc,
                reviewer_notes=notes,
                pass_fail_badge=badge,
                ai_suggested_score=c["aiSuggestedScore"],
                ai_rationale=c["aiRationale"],
            )
        )

    rubric_tab = RubricScoringTab(rows=rubric_rows)

    oq = OverallQuality(
        areas_of_strength=draft.get("areas_of_strength"),
        areas_for_improvement=draft.get("areas_for_improvement"),
    )

    rec_sel = draft.get("recommendation")
    rec_enum = RecommendationType(rec_sel) if rec_sel in ("ACCEPT", "REWORK") else None
    next_round = rework_round + 1 if rec_enum == RecommendationType.REWORK else None
    rework_disp = (
        f"This will be Round {next_round} of 3."
        if rec_enum == RecommendationType.REWORK and next_round
        else None
    )

    rec_state = RecommendationState(
        selected=rec_enum,
        rework_round_display=rework_disp,
        specific_rework_requirements=draft.get("specific_rework_requirements"),
        suggested_revised_deadline=(
            date.fromisoformat(draft["suggested_revised_deadline"])
            if draft.get("suggested_revised_deadline")
            else None
        ),
    )

    key = _draft_key(reviewer_user_id, evidence_id)
    submitted = key in _submitted_keys or ast == "completed"

    rework_hints: ReworkPhaseUiHints | None = None
    from app.service.rework_coordination_service import get_pack_rework_ui_hints

    rework_hints = get_pack_rework_ui_hints(evidence_id, rework_round)

    return EvidencePackResponse(
        evidence_id=evidence_id,
        assignment_id=assignment_id,
        task_context=task_ctx,
        submitted_files_tab=files_tab,
        rubric_scoring_tab=rubric_tab,
        overall_quality=oq,
        recommendation=rec_state,
        review_submitted=submitted,
        read_only=submitted,
        rework_phase_hints=rework_hints,
    )


def save_draft(
    evidence_id: str,
    reviewer_user_id: str,
    payload: EvidencePackDraftPayload,
) -> EvidencePackDraftResponse:
    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Evidence pack not found.")
    key = _draft_key(reviewer_user_id, evidence_id)
    if key in _submitted_keys or (row["assignment"].get("status") or "").lower() == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Review already submitted; draft cannot be saved.")

    rubric_dump = [r.model_dump(by_alias=True) for r in payload.rubric]
    body: dict[str, Any] = {
        "rubric": rubric_dump,
        "areas_of_strength": payload.areas_of_strength,
        "areas_for_improvement": payload.areas_for_improvement,
        "recommendation": payload.recommendation.value if payload.recommendation else None,
        "specific_rework_requirements": payload.specific_rework_requirements,
        "suggested_revised_deadline": (
            payload.suggested_revised_deadline.isoformat()
            if payload.suggested_revised_deadline
            else None
        ),
        "saved_at": _utc_now().isoformat(),
    }
    _drafts[key] = body
    return EvidencePackDraftResponse(
        saved=True, saved_at=_utc_now(), message="Draft saved (private to reviewer until submit)."
    )


def submit_recommendation(
    evidence_id: str,
    reviewer_user_id: str,
    body: SubmitRecommendationRequest,
) -> SubmitRecommendationResponse:
    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Evidence pack not found.")
    key = _draft_key(reviewer_user_id, evidence_id)
    if key in _submitted_keys or (row["assignment"].get("status") or "").lower() == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Review already submitted (immutable per RUB-003).")

    criteria = _criterion_template(evidence_id)
    expected_ids = {c["criterionId"] for c in criteria}
    got = {r.criterion_id for r in body.rubric_scores}
    if expected_ids != got:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "RUB-001: Every acceptance criterion must have exactly one score.",
                "expectedCriterionIds": sorted(expected_ids),
                "receivedCriterionIds": sorted(got),
            },
        )

    a = row["assignment"]
    ev = row["evidence"]
    submitted_at = ev.get("submitted_at") or a.get("created_at") or _utc_now()
    if isinstance(submitted_at, datetime) and submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=UTC)
    task_deadline = (submitted_at + timedelta(days=14)).date()

    if body.recommendation == RecommendationType.REWORK:
        assert body.suggested_revised_deadline is not None
        dl = body.suggested_revised_deadline
        today = _utc_now().date()
        if dl < today:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Suggested revised deadline cannot be in the past.",
            )
        max_date = _add_business_days(task_deadline, 3)
        if dl > max_date:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Deadline cannot exceed task deadline plus 3 business days "
                    f"(max {max_date.isoformat()})."
                ),
            )

    record_id = str(uuid.uuid4())
    _review_records[record_id] = {
        "evidence_id": evidence_id,
        "reviewer_user_id": reviewer_user_id,
        "payload": body.model_dump(by_alias=True),
        "created_at": _utc_now().isoformat(),
    }
    _submitted_keys.add(key)
    _drafts.pop(key, None)

    if body.recommendation == RecommendationType.REWORK:
        from app.service import rework_coordination_service as rcs

        rcs.on_reviewer_submitted_rework(
            evidence_id=evidence_id,
            review_record_id=record_id,
            task_name=str(a.get("title") or evidence_id),
            payload=body.model_dump(by_alias=True),
            rework_round=int(ev.get("rework_round") or 1),
        )

    msg = (
        f"Reviewer recommendation received: {body.recommendation.value} for "
        f"{(a.get('title') or evidence_id)!s}."
    )
    return SubmitRecommendationResponse(
        review_record_id=record_id,
        message=msg,
        queue_status="COMPLETED",
        enterprise_task_hint="PENDING_ENTERPRISE_DECISION",
    )


def mock_file_download_info(evidence_id: str, file_id: str) -> dict[str, Any]:
    return {
        "mode": "mock",
        "evidenceId": evidence_id,
        "fileId": file_id,
        "message": "Demo API: no binary payload; integrate blob storage in production.",
    }


def mock_zip_download_info(evidence_id: str, reviewer_user_id: str) -> dict[str, Any]:
    row = mock_store.find_queue_row_by_evidence(evidence_id, reviewer_user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found.")
    a = row["assignment"]
    ev = row["evidence"]
    rw = int(ev.get("rework_round") or 1)
    zip_name = f"{a['_id']}-submission-v{rw}.zip"
    return {
        "mode": "mock",
        "filename": zip_name,
        "message": "Demo API: generate ZIP from storage in production.",
        "path": f"/api/reviewer/evidence/{evidence_id}/files/download-zip",
    }
