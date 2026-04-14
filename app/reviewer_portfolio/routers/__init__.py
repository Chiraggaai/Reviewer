"""Reviewer API routers — composed like ``app.project_portfolio.routers``."""

from fastapi import APIRouter

from . import (
    dashboard,
    evidence_pack,
    inbox,
    mentoring_log,
    metrics,
    qa,
    reviewer_admin,
    reviewers,
    reviewer_notifications,
    review_history,
    reviews,
    review_queue_module,
    rework_coordination,
    tasks,
)

router = APIRouter()
router.include_router(dashboard.router)
router.include_router(metrics.router)
router.include_router(reviews.router)
router.include_router(tasks.router)
router.include_router(inbox.router)
router.include_router(reviewer_admin.router)
router.include_router(reviewers.router)
router.include_router(reviewer_notifications.router)
router.include_router(review_history.router)
router.include_router(mentoring_log.router)
router.include_router(review_queue_module.router)
router.include_router(evidence_pack.router)
router.include_router(rework_coordination.router)
router.include_router(qa.router)

__all__ = ["router"]
