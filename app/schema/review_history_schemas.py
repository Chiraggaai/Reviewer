"""
Review History (Records) — immutable submitted reviews + enterprise resolution (demo store).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewHistoryTab(str, Enum):
    ALL = "all"
    RECOMMENDED_ACCEPT = "recommended_accept"
    RECOMMENDED_REWORK = "recommended_rework"
    OVERRIDDEN = "overridden"


class ReviewerRecommendationKind(str, Enum):
    ACCEPT = "ACCEPT"
    REWORK = "REWORK"


class FinalReviewOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    REWORK_REQUIRED = "REWORK_REQUIRED"


class ReviewHistoryAgreementSummary(BaseModel):
    model_config = {"populate_by_name": True}

    agreed_count: int = Field(serialization_alias="agreedCount")
    window_count: int = Field(
        serialization_alias="windowCount",
        description="Size of the rolling window (e.g. last 4 reviews).",
    )
    agreement_percent: Optional[float] = Field(
        default=None,
        serialization_alias="agreementPercent",
        description="Null when window_count is 0.",
    )
    headline: str = Field(
        description="Copy-ready banner, e.g. Enterprise agreed in X of last Y reviews.",
    )


class ReviewHistoryListItem(BaseModel):
    model_config = {"populate_by_name": True}

    review_record_id: str = Field(serialization_alias="reviewRecordId")
    evidence_id: str = Field(serialization_alias="evidenceId")
    task_title: str = Field(serialization_alias="taskTitle")
    project_name: str = Field(serialization_alias="projectName")
    reviewed_at: datetime = Field(serialization_alias="reviewedAt")
    reviewer_recommendation: ReviewerRecommendationKind = Field(
        serialization_alias="reviewerRecommendation"
    )
    final_outcome: FinalReviewOutcome = Field(serialization_alias="finalOutcome")
    overridden: bool
    rework_round: Optional[int] = Field(default=None, serialization_alias="reworkRound")
    enterprise_agreed_with_reviewer: bool = Field(
        serialization_alias="enterpriseAgreedWithReviewer",
        description="True when final enterprise outcome aligns with reviewer recommendation.",
    )


class ReviewHistoryRubricRow(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    criterion_label: str = Field(serialization_alias="criterionLabel")
    score: int = Field(ge=1, le=5)
    max_score: int = Field(default=5, serialization_alias="maxScore")


class ReviewHistoryDetail(BaseModel):
    model_config = {"populate_by_name": True}

    review_record_id: str = Field(serialization_alias="reviewRecordId")
    evidence_id: str = Field(serialization_alias="evidenceId")
    task_title: str = Field(serialization_alias="taskTitle")
    project_name: str = Field(serialization_alias="projectName")
    reviewed_at: datetime = Field(serialization_alias="reviewedAt")
    reviewer_recommendation: ReviewerRecommendationKind = Field(
        serialization_alias="reviewerRecommendation"
    )
    final_outcome: FinalReviewOutcome = Field(serialization_alias="finalOutcome")
    overridden: bool
    rework_round: Optional[int] = Field(default=None, serialization_alias="reworkRound")
    override_justification_excerpt: Optional[str] = Field(
        default=None,
        serialization_alias="overrideJustificationExcerpt",
    )
    rubric_scores: list[ReviewHistoryRubricRow] = Field(serialization_alias="rubricScores")
    overall_assessment: str = Field(serialization_alias="overallAssessment")
    review_record_pdf_api_path: str = Field(
        serialization_alias="reviewRecordPdfApiPath",
        description="GET for PDF stub / metadata (demo).",
    )


class ReviewHistoryListPayload(BaseModel):
    model_config = {"populate_by_name": True}

    agreement: ReviewHistoryAgreementSummary
    items: list[ReviewHistoryListItem]
    total_matching: int = Field(serialization_alias="totalMatching")
    limit: int
    offset: int


class ReviewHistoryPdfMeta(BaseModel):
    model_config = {"populate_by_name": True}

    mode: str = "mock"
    review_record_id: str = Field(serialization_alias="reviewRecordId")
    filename: str
    message: str
