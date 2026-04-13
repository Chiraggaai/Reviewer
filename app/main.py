from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    dashboard,
    evidence_pack,
    inbox,
    mentoring_log,
    metrics,
    qa,
    reviewers,
    reviewer_notifications,
    review_history,
    reviews,
    review_queue_module,
    rework_coordination,
    tasks,
)

app = FastAPI(
    title="Glimmora Reviewer API",
    version="1.0.0",
    description=(
        "Reviewer dashboard, Review Queue (5), Evidence Pack (6), Rework Coordination (7), "
        "Workroom Q&A (8), Reviewer notifications (10), Review History, Mentoring Log, tasks, inbox, SLA metrics."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(inbox.router, prefix="/api")
app.include_router(reviewers.router, prefix="/api")
app.include_router(reviewer_notifications.router, prefix="/api")
app.include_router(review_history.router, prefix="/api")
app.include_router(mentoring_log.router, prefix="/api")
app.include_router(review_queue_module.router, prefix="/api")
app.include_router(evidence_pack.router, prefix="/api")
app.include_router(rework_coordination.router, prefix="/api")
app.include_router(qa.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
