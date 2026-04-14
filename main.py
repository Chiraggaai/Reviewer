"""ASGI entry for ``uvicorn main:app`` (or ``uvicorn app.main:app``).

Python must see the **Reviewer** repo root on ``sys.path`` (so the ``app`` package resolves).

- From another directory: ``uvicorn app.main:app --app-dir <path-to-Reviewer>``
- Or: ``$env:PYTHONPATH = '<path-to-Reviewer>'`` then ``uvicorn app.main:app``
- Or: ``python serve.py`` / ``.\\run.ps1`` (both set path for you)
"""
from app.main import app

__all__ = ["app"]
