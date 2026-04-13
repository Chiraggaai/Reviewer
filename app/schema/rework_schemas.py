"""
Module 7 — Rework Coordination (API contracts).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NotificationPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class NotificationRecipient(str, Enum):
    REVIEWER = "reviewer"
    CONTRIBUTOR = "contributor"


class ReviewerNotificationEventType(str, Enum):
    """§10.1 matrix (+ shared contributor events). Use string values in filters."""

    NEW_SUBMISSION_ASSIGNED = "NEW_SUBMISSION_ASSIGNED"
    REVIEW_SLA_APPROACHING_T24H = "REVIEW_SLA_APPROACHING_T24H"
    REVIEW_SLA_APPROACHING_T4H = "REVIEW_SLA_APPROACHING_T4H"
    REVIEW_SLA_BREACHED = "REVIEW_SLA_BREACHED"
    REWORK_RESUBMISSION_RECEIVED = "REWORK_RESUBMISSION_RECEIVED"
    CONTRIBUTOR_QA_MESSAGE = "CONTRIBUTOR_QA_MESSAGE"
    REVIEWER_QA_MESSAGE = "REVIEWER_QA_MESSAGE"
    ENTERPRISE_OVERRIDE_REWORK_TO_ACCEPT = "ENTERPRISE_OVERRIDE_REWORK_TO_ACCEPT"
    ENTERPRISE_OVERRIDE_ACCEPT_TO_REWORK = "ENTERPRISE_OVERRIDE_ACCEPT_TO_REWORK"
    TASK_ESCALATED_ROUND3 = "TASK_ESCALATED_ROUND3"
    PROJECT_BLUEPRINT_PUBLISHED = "PROJECT_BLUEPRINT_PUBLISHED"
    REWORK_DECISION_CONFIRMED_REVIEWER = "REWORK_DECISION_CONFIRMED_REVIEWER"
    REWORK_DECISION_CONFIRMED_CONTRIBUTOR = "REWORK_DECISION_CONFIRMED_CONTRIBUTOR"
    REVIEWER_DEACTIVATED = "REVIEWER_DEACTIVATED"
    GENERIC = "GENERIC"
    LEGACY = "LEGACY"


class ReworkNotification(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    recipient: NotificationRecipient
    priority: NotificationPriority
    title: str
    body: str
    workroom_href: str = Field(default="/workroom", serialization_alias="workroomHref")
    evidence_id: str = Field(serialization_alias="evidenceId")
    created_at: datetime = Field(serialization_alias="createdAt")
    read: bool = False
    event_type: str = Field(
        default=ReviewerNotificationEventType.LEGACY.value,
        serialization_alias="eventType",
        description="Filter key for full notification history (§10.1).",
    )
    deep_link_path: str = Field(
        serialization_alias="deepLinkPath",
        description="SPA route when the user opens this notification (not the REST API path).",
    )
    cta_label: str = Field(
        default="Open",
        serialization_alias="ctaLabel",
        description="Short CTA label for the deep link (e.g. Open Review, Open Workroom).",
    )


class EnterpriseReworkConfirmRequest(BaseModel):
    model_config = {"populate_by_name": True}

    evidence_id: str = Field(validation_alias="evidenceId", serialization_alias="evidenceId")
    confirm_rework: bool = Field(default=True, validation_alias="confirmRework", serialization_alias="confirmRework")
    enterprise_admin_internal_notes: str = Field(
        default="",
        validation_alias="enterpriseAdminInternalNotes",
        serialization_alias="enterpriseAdminInternalNotes",
        description="Stored server-side only — never returned on contributor endpoints (WRK-005).",
    )


class EnterpriseReworkConfirmResponse(BaseModel):
    model_config = {"populate_by_name": True}

    success: bool = True
    evidence_id: str = Field(serialization_alias="evidenceId")
    task_status: str = Field(default="REWORK_REQUIRED", serialization_alias="taskStatus")
    message: str


class ContributorRubricFeedbackRow(BaseModel):
    model_config = {"populate_by_name": True}

    criterion_id: str = Field(serialization_alias="criterionId")
    order: int
    score: int = Field(ge=1, le=5)
    reviewer_notes: str = Field(serialization_alias="reviewerNotes")
    attribution: str = Field(default="Reviewer", description="Never a personal name (WRK-005).")


class ContributorReworkFeedbackResponse(BaseModel):
    """§7.2 — Reviewer structured feedback only (WRK-005)."""

    model_config = {"populate_by_name": True}

    evidence_id: str = Field(serialization_alias="evidenceId")
    task_name: str = Field(serialization_alias="taskName")
    round_number: int = Field(serialization_alias="roundNumber")
    resubmission_deadline_display: str = Field(serialization_alias="resubmissionDeadlineDisplay")
    rubric_rows: list[ContributorRubricFeedbackRow] = Field(serialization_alias="rubricRows")
    areas_of_strength: str = Field(serialization_alias="areasOfStrength")
    areas_for_improvement: str = Field(serialization_alias="areasForImprovement")
    specific_rework_requirements: str = Field(serialization_alias="specificReworkRequirements")
    suggested_revised_deadline: date = Field(serialization_alias="suggestedRevisedDeadline")
    visibility_rule: str = Field(
        default="WRK-005: Enterprise Admin internal notes are never included in this payload.",
        serialization_alias="visibilityRule",
    )


class WorkroomAuthorRole(str, Enum):
    REVIEWER = "reviewer"
    CONTRIBUTOR = "contributor"


class WorkroomMessage(BaseModel):
    model_config = {"populate_by_name": True}

    message_id: str = Field(serialization_alias="messageId")
    evidence_id: str = Field(serialization_alias="evidenceId")
    author_role: WorkroomAuthorRole = Field(serialization_alias="authorRole")
    display_label: str = Field(
        default="Reviewer",
        serialization_alias="displayLabel",
        description="§7.3 — Reviewer messages labelled generically, never by name.",
    )
    body: str
    flagged_about_feedback: bool = Field(
        default=False, serialization_alias="flaggedAboutFeedback"
    )
    created_at: datetime = Field(serialization_alias="createdAt")


class WorkroomPostMessageRequest(BaseModel):
    model_config = {"populate_by_name": True}

    author_role: WorkroomAuthorRole = Field(validation_alias="authorRole", serialization_alias="authorRole")
    body: str = Field(min_length=1)
    flag_question_about_feedback: bool = Field(
        default=False,
        validation_alias="flagQuestionAboutFeedback",
        serialization_alias="flagQuestionAboutFeedback",
    )


class ContributorResubmitRequest(BaseModel):
    model_config = {"populate_by_name": True}

    summary: Optional[str] = Field(
        default=None,
        description="Optional contributor note for audit log (demo).",
    )


class ContributorResubmitResponse(BaseModel):
    model_config = {"populate_by_name": True}

    success: bool = True
    evidence_id: str = Field(serialization_alias="evidenceId")
    new_round_number: int = Field(serialization_alias="newRoundNumber")
    task_status: str = Field(default="SUBMITTED", serialization_alias="taskStatus")
    message: str
    previous_version_preserved: bool = Field(
        default=True, serialization_alias="previousVersionPreserved"
    )


class ReviewerNotificationListPayload(BaseModel):
    """§10.2 — Bell panel (default limit 20) and full history with filters."""

    model_config = {"populate_by_name": True}

    notifications: list[ReworkNotification]
    total_matching: int = Field(serialization_alias="totalMatching")
    limit: int
    offset: int


class ReviewerNotificationUnreadPayload(BaseModel):
    model_config = {"populate_by_name": True}

    unread_count: int = Field(serialization_alias="unreadCount")


class ReviewerNotificationMarkReadPayload(BaseModel):
    model_config = {"populate_by_name": True}

    updated: bool


class ReviewerNotificationMarkAllReadPayload(BaseModel):
    model_config = {"populate_by_name": True}

    marked_count: int = Field(serialization_alias="markedCount")
