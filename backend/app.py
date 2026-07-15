"""Compatibility entrypoint. Use ``python -m backend.src.server`` for new work."""

from backend.src.app import app

__all__ = ["app"]
