"""ASGI entry for ``uvicorn main:app`` from this workspace root (standalone Reviewer API)."""
from app.main import app

__all__ = ["app"]
