"""
Review Queue page (module 5.x) — response shapes (standalone Reviewer API).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewQueueTab(str, Enum):
    ALL = "ALL"
    PENDING_REVIEW = "PENDING_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    REWORK_RECEIVED = "REWORK_RECEIVED"
    COMPLETED = "COMPLETED"


class ReviewQueueSort(str, Enum):
    SLA_DEADLINE_SOONEST = "sla_deadline_soonest"
    SUBMITTED_RECENT = "submitted_recent"
    PROJECT_NAME_AZ = "project_name_az"
    REWORK_ROUND_DESC = "rework_round_desc"


class SLAVisualStatus(str, Enum):
    ON_TRACK = "on_track"
    APPROACHING = "approaching"
    CRITICAL = "critical"
    BREACHED = "breached"


class QueueStatusBadge(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    REWORK_RECEIVED = "REWORK_RECEIVED"
    COMPLETED = "COMPLETED"


class ReviewQueueReworkRound(BaseModel):
    model_config = {"populate_by_name": True}

    current: int
    max_rounds: int = Field(default=3, serialization_alias="maxRounds")
    visible: bool
    is_final_round_warning: bool = Field(serialization_alias="isFinalRoundWarning")


class ReviewQueueSLA(BaseModel):
    model_config = {"populate_by_name": True}

    visual_status: SLAVisualStatus = Field(serialization_alias="visualStatus")
    progress_bar_percent: float = Field(serialization_alias="progressBarPercent")
    bar_color_token: str = Field(serialization_alias="barColorToken")
    countdown_label: str = Field(serialization_alias="countdownLabel")
    emphasize_countdown: bool = Field(serialization_alias="emphasizeCountdown")
    breached: bool
    breached_label: Optional[str] = Field(default=None, serialization_alias="breachedLabel")
    remaining_seconds: Optional[int] = Field(default=None, serialization_alias="remainingSeconds")
    deadline_at_iso: Optional[str] = Field(default=None, serialization_alias="deadlineAtIso")


class ReviewQueueCard(BaseModel):
    model_config = {"populate_by_name": True}

    assignment_id: str = Field(serialization_alias="assignmentId")
    evidence_id: str = Field(serialization_alias="evidenceId")
    task_name: str = Field(serialization_alias="taskName")
    project_name: str = Field(serialization_alias="projectName")
    project_id: Optional[str] = Field(default=None, serialization_alias="projectId")
    contributor_id: str = Field(serialization_alias="contributorId")
    contributor_tooltip: str = Field(
        default="Contributor identity is protected.",
        serialization_alias="contributorTooltip",
    )
    submitted_display: str = Field(serialization_alias="submittedDisplay")
    rework_round: Optional[ReviewQueueReworkRound] = Field(
        default=None, serialization_alias="reworkRound"
    )
    sla: ReviewQueueSLA
    ai_pre_score_percent: Optional[int] = Field(
        default=None, serialization_alias="aiPreScorePercent"
    )
    ai_score_tooltip: str = Field(
        default="AI-generated reference score. Your independent assessment takes priority.",
        serialization_alias="aiScoreTooltip",
    )
    status_badge: QueueStatusBadge = Field(serialization_alias="statusBadge")
    float_to_top: bool = Field(serialization_alias="floatToTop")
    open_review_path: str = Field(serialization_alias="openReviewPath")
    evidence_pack_api_path: str = Field(
        serialization_alias="evidencePackApiPath",
        description="GET this URL (with reviewerUserId) to load module 6 Evidence Pack Review payload.",
    )
    qa_context_api_path: str = Field(
        serialization_alias="qaContextApiPath",
        description="GET this URL (with reviewerUserId) for module 8 Workroom Q&A page context.",
    )


class ReviewQueueTabCounts(BaseModel):
    model_config = {"populate_by_name": True}

    all_count: int = Field(validation_alias="all", alias="all")
    pending_review: int = Field(validation_alias="pendingReview", alias="pendingReview")
    under_review: int = Field(validation_alias="underReview", alias="underReview")
    rework_received: int = Field(validation_alias="reworkReceived", alias="reworkReceived")
    completed: int = Field(validation_alias="completed", alias="completed")


class ReviewQueueEmptyHint(str, Enum):
    NONE = "none"
    NO_SUBMISSIONS = "no_submissions"
    NO_FILTER_MATCH = "no_filter_match"
    NOT_ASSIGNED = "not_assigned"


class ReviewQueueMeta(BaseModel):
    model_config = {"populate_by_name": True}

    page_title: str = Field(default="Review Queue", serialization_alias="pageTitle")
    page_sub_label: str = Field(
        default="Submissions assigned to you across all your projects.",
        serialization_alias="pageSubLabel",
    )
    assigned_project_count: int = Field(serialization_alias="assignedProjectCount")
    refresh_interval_seconds: int = Field(default=60, serialization_alias="refreshIntervalSeconds")
    empty_hint: ReviewQueueEmptyHint = Field(
        default=ReviewQueueEmptyHint.NONE, serialization_alias="emptyHint"
    )


class ReviewQueueListData(BaseModel):
    model_config = {"populate_by_name": True}

    cards: list[ReviewQueueCard]
    meta: ReviewQueueMeta


class ReviewQueueProjectOption(BaseModel):
    model_config = {"populate_by_name": True}

    project_id: str = Field(serialization_alias="projectId")
    project_name: str = Field(serialization_alias="projectName")


class ReviewQueueProjectsData(BaseModel):
    model_config = {"populate_by_name": True}

    projects: list[ReviewQueueProjectOption]
