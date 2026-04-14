from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import close_db, connect_db
from app.reviewer_portfolio import router as reviewer_portfolio_router
from app.reviewer_portfolio.routers import reviewer_invitations


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="Glimmora Reviewer API",
    version="1.0.0",
    description=(
        "Reviewer dashboard, Review Queue (5), Evidence Pack (6), Rework Coordination (7), "
        "Workroom Q&A (8), Reviewer notifications (10), Review History, Mentoring Log, tasks, inbox, SLA metrics."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviewer_portfolio_router, prefix="/api")
app.include_router(reviewer_invitations.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
