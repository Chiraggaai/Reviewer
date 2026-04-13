from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# --- Dashboard ---


class DashboardAlertCTA(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    href: str


class DashboardAlerts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    overdue_review_count: int = Field(validation_alias="overdueReviewCount", alias="overdueReviewCount")
    message: str
    cta: DashboardAlertCTA | None = None


class DashboardSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pending_reviews: int = Field(validation_alias="pendingReviews", alias="pendingReviews")
    active_tasks: int = Field(validation_alias="activeTasks", alias="activeTasks")
    unread_messages: int = Field(validation_alias="unreadMessages", alias="unreadMessages")
    sla_compliance_percent: float = Field(
        validation_alias="slaCompliancePercent", alias="slaCompliancePercent"
    )
    alerts: DashboardAlerts | None = None


class ActionItemDeepLink(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["review", "task", "inbox", "metrics"]
    id: str | None = None
    href: str | None = None


class ActionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    severity: Literal["critical", "warning", "info"]
    icon: str
    status_label: str = Field(validation_alias="statusLabel", alias="statusLabel")
    deep_link: ActionItemDeepLink = Field(validation_alias="deepLink", alias="deepLink")


class ActionItemsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_requiring_attention: int = Field(
        validation_alias="totalRequiringAttention", alias="totalRequiringAttention"
    )
    items: list[ActionItem]


# --- Metrics ---


class SLAPerformanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sla_compliance_percent: float = Field(
        validation_alias="slaCompliancePercent", alias="slaCompliancePercent"
    )
    sla_target_percent: float = Field(
        validation_alias="slaTargetPercent", alias="slaTargetPercent"
    )
    rec_acceptance_percent: float = Field(
        validation_alias="recAcceptancePercent", alias="recAcceptancePercent"
    )
    rec_acceptance_target_percent: float = Field(
        validation_alias="recAcceptanceTargetPercent", alias="recAcceptanceTargetPercent"
    )
    avg_review_time_hours: float = Field(
        validation_alias="avgReviewTimeHours", alias="avgReviewTimeHours"
    )
    reviews_this_month: int = Field(
        validation_alias="reviewsThisMonth", alias="reviewsThisMonth"
    )
    period: str


# --- Reviews ---


class ReviewQueueStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ReviewQueueItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    review_id: str = Field(validation_alias="reviewId", alias="reviewId")
    module_label: str = Field(validation_alias="moduleLabel", alias="moduleLabel")
    due_at: datetime | None = Field(validation_alias="dueAt", alias="dueAt")
    due_display: str = Field(validation_alias="dueDisplay", alias="dueDisplay")
    is_overdue: bool = Field(validation_alias="isOverdue", alias="isOverdue")
    contributor_id: str | None = Field(
        default=None, validation_alias="contributorId", alias="contributorId"
    )


class ReviewQueueResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ReviewQueueItem]
    total: int


class ReviewDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    review_id: str = Field(validation_alias="reviewId", alias="reviewId")
    module_label: str = Field(validation_alias="moduleLabel", alias="moduleLabel")
    status: str
    due_at: datetime | None = Field(validation_alias="dueAt", alias="dueAt")
    round_label: str | None = Field(
        default=None, validation_alias="roundLabel", alias="roundLabel"
    )


# --- Tasks ---


class TaskStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    REWORK = "REWORK"


class ActiveTaskItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str = Field(validation_alias="taskId", alias="taskId")
    short_title: str = Field(validation_alias="shortTitle", alias="shortTitle")
    status: TaskStatus
    status_color_token: str = Field(
        validation_alias="statusColorToken", alias="statusColorToken"
    )


class ActiveTasksResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ActiveTaskItem]
    total: int


# --- Inbox ---


class InboxThread(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    thread_id: str = Field(validation_alias="threadId", alias="threadId")
    module_label: str = Field(validation_alias="moduleLabel", alias="moduleLabel")
    linked_review_id: str | None = Field(
        default=None, validation_alias="linkedReviewId", alias="linkedReviewId"
    )
    unread_count: int = Field(validation_alias="unreadCount", alias="unreadCount")
    last_message_preview: str = Field(
        validation_alias="lastMessagePreview", alias="lastMessagePreview"
    )
    updated_at: datetime = Field(validation_alias="updatedAt", alias="updatedAt")


class InboxThreadsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[InboxThread]
    total: int


class UnreadCountResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    unread_messages: int = Field(validation_alias="unreadMessages", alias="unreadMessages")


class MarkReadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    thread_id: str = Field(validation_alias="threadId", alias="threadId")
    unread_messages: int = Field(validation_alias="unreadMessages", alias="unreadMessages")
