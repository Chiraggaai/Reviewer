"""
Evidence Pack Review (module 6.x) — request/response models.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class RecommendationType(str, Enum):
    ACCEPT = "ACCEPT"
    REWORK = "REWORK"


class ReferenceFile(BaseModel):
    model_config = {"populate_by_name": True}

    file_id: str = Field(serialization_alias="fileId")
    filename: str
    file_type_badge: str = Field(serialization_alias="fileTypeBadge")
    size_bytes: int = Field(serialization_alias="sizeBytes")
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    download_path: str = Field(serialization_alias="downloadPath")
    preview_supported: bool = Field(default=False, serialization_alias="previewSupported")


class SubmittedFile(BaseModel):
    model_config = {"populate_by_name": True}

    file_id: str = Field(serialization_alias="fileId")
    filename: str
    file_type_badge: str = Field(serialization_alias="fileTypeBadge")
    size_bytes: int = Field(serialization_alias="sizeBytes")
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    download_path: str = Field(serialization_alias="downloadPath")
    preview_supported: bool = Field(serialization_alias="previewSupported")


class PreviousSubmissionFile(BaseModel):
    model_config = {"populate_by_name": True}

    file_id: str = Field(serialization_alias="fileId")
    filename: str


class PreviousChecklistState(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    checked: bool
    contributor_notes: Optional[str] = Field(default=None, serialization_alias="contributorNotes")


class PreviousSubmission(BaseModel):
    model_config = {"populate_by_name": True}

    version_label: str = Field(serialization_alias="versionLabel")
    round_number: int = Field(serialization_alias="roundNumber")
    files: list[PreviousSubmissionFile]
    checklist_state: list[PreviousChecklistState] = Field(
        serialization_alias="checklistState"
    )


class ContributorChecklistItem(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    order: int
    criterion_text: str = Field(serialization_alias="criterionText")
    checked_by_contributor: bool = Field(serialization_alias="checkedByContributor")
    contributor_notes: Optional[str] = Field(default=None, serialization_alias="contributorNotes")


class AcceptanceCriterion(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    order: int
    text: str


class RubricAIRow(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    suggested_score: int = Field(ge=1, le=5, serialization_alias="suggestedScore")
    rationale: str


class RubricRowState(BaseModel):
    """Single rubric row for GET pack (merged with draft if present)."""

    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    order: int
    criterion_text: str = Field(serialization_alias="criterionText")
    score: Optional[int] = Field(default=None, ge=1, le=5)
    reviewer_notes: Optional[str] = Field(default=None, serialization_alias="reviewerNotes")
    pass_fail_badge: Optional[str] = Field(
        default=None,
        serialization_alias="passFailBadge",
        description="PASS | FAIL — derived when score set",
    )
    ai_suggested_score: int = Field(serialization_alias="aiSuggestedScore")
    ai_rationale: str = Field(serialization_alias="aiRationale")


class TaskContextPanel(BaseModel):
    model_config = {"populate_by_name": True}

    task_name: str = Field(serialization_alias="taskName")
    status_badge: str = Field(serialization_alias="statusBadge")
    task_instructions_html: str = Field(serialization_alias="taskInstructionsHtml")
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        serialization_alias="acceptanceCriteria"
    )
    task_deadline: datetime = Field(serialization_alias="taskDeadline")
    reference_materials: list[ReferenceFile] = Field(
        default_factory=list, serialization_alias="referenceMaterials"
    )
    submission_notes_contributor: Optional[str] = Field(
        default=None,
        max_length=500,
        serialization_alias="submissionNotesContributor",
    )


class SubmittedFilesTab(BaseModel):
    model_config = {"populate_by_name": True}

    files: list[SubmittedFile]
    bulk_zip_download_path: str = Field(serialization_alias="bulkZipDownloadPath")
    bulk_zip_filename_hint: str = Field(serialization_alias="bulkZipFilenameHint")
    submission_notes: Optional[str] = Field(
        default=None, serialization_alias="submissionNotes"
    )
    contributor_checklist: list[ContributorChecklistItem] = Field(
        serialization_alias="contributorChecklist"
    )
    previous_submission: Optional[PreviousSubmission] = Field(
        default=None, serialization_alias="previousSubmission"
    )


class RubricScoringTab(BaseModel):
    model_config = {"populate_by_name": True}

    rubric_intro: str = Field(
        default=(
            "Score each criterion 1–5 with mandatory notes (min 20 characters). "
            "AI pre-score is reference only."
        ),
        serialization_alias="rubricIntro",
    )
    score_labels: dict[str, str] = Field(
        default_factory=lambda: {
            "1": "Does not meet",
            "2": "Partially meets",
            "3": "Meets",
            "4": "Exceeds",
            "5": "Exceptional",
        },
        serialization_alias="scoreLabels",
    )
    ai_panel_header: str = Field(
        default="AI Pre-Score — Reference Only",
        serialization_alias="aiPanelHeader",
    )
    ai_panel_tooltip: str = Field(
        default="AI scores are suggestions only. Your assessment is authoritative.",
        serialization_alias="aiPanelTooltip",
    )
    rows: list[RubricRowState]


class OverallQuality(BaseModel):
    model_config = {"populate_by_name": True}

    areas_of_strength: Optional[str] = Field(default=None, serialization_alias="areasOfStrength")
    areas_for_improvement: Optional[str] = Field(
        default=None, serialization_alias="areasForImprovement"
    )


class RecommendationState(BaseModel):
    model_config = {"populate_by_name": True}

    selected: Optional[RecommendationType] = None
    rework_round_display: Optional[str] = Field(
        default=None, serialization_alias="reworkRoundDisplay",
        description='e.g. "This will be Round 2 of 3."',
    )
    specific_rework_requirements: Optional[str] = Field(
        default=None, serialization_alias="specificReworkRequirements"
    )
    suggested_revised_deadline: Optional[date] = Field(
        default=None, serialization_alias="suggestedRevisedDeadline"
    )
    rework_extension_business_days_max: int = Field(
        default=3, serialization_alias="reworkExtensionBusinessDaysMax"
    )


class ReworkPhaseUiHints(BaseModel):
    """§7.4 — previous submission expanded on resubmission open; Round 3 warning."""

    model_config = {"populate_by_name": True}

    previous_submission_default_expanded: bool = Field(
        default=False, serialization_alias="previousSubmissionDefaultExpanded"
    )
    final_rework_round_banner: Optional[str] = Field(
        default=None, serialization_alias="finalReworkRoundBanner"
    )
    task_rework_phase_status: Optional[str] = Field(
        default=None,
        serialization_alias="taskReworkPhaseStatus",
        description="e.g. REWORK_REQUIRED, SUBMITTED_AFTER_REWORK",
    )


class EvidencePackResponse(BaseModel):
    model_config = {"populate_by_name": True}

    evidence_id: str = Field(serialization_alias="evidenceId")
    assignment_id: str = Field(serialization_alias="assignmentId")
    task_context: TaskContextPanel = Field(serialization_alias="taskContext")
    submitted_files_tab: SubmittedFilesTab = Field(serialization_alias="submittedFilesTab")
    rubric_scoring_tab: RubricScoringTab = Field(serialization_alias="rubricScoringTab")
    overall_quality: OverallQuality = Field(serialization_alias="overallQuality")
    recommendation: RecommendationState
    rework_phase_hints: Optional[ReworkPhaseUiHints] = Field(
        default=None, serialization_alias="reworkPhaseHints"
    )
    layout: dict[str, str] = Field(
        default_factory=lambda: {
            "desktop": "two_panel",
            "mobile": "single_column",
        }
    )
    draft_auto_save_interval_seconds: int = Field(
        default=60, serialization_alias="draftAutoSaveIntervalSeconds"
    )
    submit_enabled_rules: dict[str, str] = Field(
        default_factory=lambda: {
            "RUB-001": "All criteria scored 1–5 before submit.",
            "RUB-002": "Min 20 characters notes per criterion.",
            "RUB-003": "Submission is immutable after success.",
            "RUB-004": "Atomic server write — no partial records.",
        },
        serialization_alias="submitEnabledRules",
    )
    review_submitted: bool = Field(default=False, serialization_alias="reviewSubmitted")
    read_only: bool = Field(default=False, serialization_alias="readOnly")


# --- Draft (DRAFT-001: no minimum) ---


class DraftRubricRow(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(
        validation_alias="criterionId",
        serialization_alias="criterionId",
    )
    score: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = None


class EvidencePackDraftPayload(BaseModel):
    model_config = {"populate_by_name": True}

    rubric: list[DraftRubricRow] = Field(default_factory=list)
    areas_of_strength: Optional[str] = Field(
        default=None,
        validation_alias="areasOfStrength",
        serialization_alias="areasOfStrength",
    )
    areas_for_improvement: Optional[str] = Field(
        default=None,
        validation_alias="areasForImprovement",
        serialization_alias="areasForImprovement",
    )
    recommendation: Optional[RecommendationType] = None
    specific_rework_requirements: Optional[str] = Field(
        default=None,
        validation_alias="specificReworkRequirements",
        serialization_alias="specificReworkRequirements",
    )
    suggested_revised_deadline: Optional[date] = Field(
        default=None,
        validation_alias="suggestedRevisedDeadline",
        serialization_alias="suggestedRevisedDeadline",
    )


class EvidencePackDraftResponse(BaseModel):
    model_config = {"populate_by_name": True}

    saved: bool = True
    saved_at: datetime = Field(
        validation_alias="savedAt",
        serialization_alias="savedAt",
    )
    message: str = "Draft saved (private to reviewer until submit)."


# --- Submit ---


class SubmitRubricRow(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(
        validation_alias="criterionId",
        serialization_alias="criterionId",
    )
    score: int = Field(ge=1, le=5)
    notes: str

    @field_validator("notes")
    @classmethod
    def notes_trim(cls, v: str) -> str:
        t = (v or "").strip()
        if len(t) < 20:
            raise ValueError(
                "Please add at least 20 characters of feedback for this criterion."
            )
        return t


class SubmitRecommendationRequest(BaseModel):
    model_config = {"populate_by_name": True}

    rubric_scores: list[SubmitRubricRow] = Field(
        validation_alias="rubricScores",
        serialization_alias="rubricScores",
    )
    areas_of_strength: str = Field(
        validation_alias="areasOfStrength",
        serialization_alias="areasOfStrength",
    )
    areas_for_improvement: str = Field(
        default="",
        validation_alias="areasForImprovement",
        serialization_alias="areasForImprovement",
    )
    recommendation: RecommendationType
    specific_rework_requirements: Optional[str] = Field(
        default=None,
        validation_alias="specificReworkRequirements",
        serialization_alias="specificReworkRequirements",
    )
    suggested_revised_deadline: Optional[date] = Field(
        default=None,
        validation_alias="suggestedRevisedDeadline",
        serialization_alias="suggestedRevisedDeadline",
    )

    @field_validator("areas_of_strength")
    @classmethod
    def strength_trim(cls, v: str) -> str:
        t = v.strip()
        if len(t) < 30:
            raise ValueError("Areas of Strength must be at least 30 characters.")
        return t

    @model_validator(mode="after")
    def rework_rules(self) -> SubmitRecommendationRequest:
        if self.recommendation == RecommendationType.REWORK:
            imp = self.areas_for_improvement.strip()
            if len(imp) < 50:
                raise ValueError(
                    "Areas for Improvement must be at least 50 characters when recommending REWORK."
                )
            req = (self.specific_rework_requirements or "").strip()
            if len(req) < 50:
                raise ValueError(
                    "Specific rework requirements must be at least 50 characters for REWORK."
                )
            if self.suggested_revised_deadline is None:
                raise ValueError("Suggested revised deadline is required for REWORK.")
        return self


class SubmitRecommendationResponse(BaseModel):
    model_config = {"populate_by_name": True}

    success: bool = True
    review_record_id: str = Field(serialization_alias="reviewRecordId")
    message: str
    queue_status: str = Field(
        default="COMPLETED",
        serialization_alias="queueStatus",
    )
    enterprise_task_hint: str = Field(
        default="PENDING_ENTERPRISE_DECISION",
        serialization_alias="enterpriseTaskHint",
    )


class ValidationErrorItem(BaseModel):
    model_config = {"populate_by_name": True}

    field: str
    message: str


class SubmitRecommendationErrorResponse(BaseModel):
    model_config = {"populate_by_name": True}

    success: bool = False
    errors: list[ValidationErrorItem]
