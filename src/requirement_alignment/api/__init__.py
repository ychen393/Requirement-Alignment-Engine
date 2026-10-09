"""Thin FastAPI boundary for the requirement-alignment application."""

from requirement_alignment.api.main import app, create_app

__all__ = ["app", "create_app"]

