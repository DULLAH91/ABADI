"""Backward-compatible entry point for the canonical execution agent."""

from .agent.server import create_app

app = create_app()

__all__ = ["app", "create_app"]
