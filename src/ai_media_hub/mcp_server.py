from __future__ import annotations

import json
from typing import Annotated, Literal

from mcp.server import MCPServer
from pydantic import Field

from ai_media_hub.control import ControlPlane, ControlPlaneError


mcp = MCPServer(
    "AI Media Hub",
    instructions=(
        "You are connected to the AI Media Hub control plane. "
        "Use the provided narrow tools to inspect the execution node and run "
        "approved production probes. Never assume a job succeeded without "
        "reading its returned status, telemetry, and artifact metadata."
    ),
)
control = ControlPlane()


def _result(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def node_status() -> str:
    """Inspect the registered execution node, GPU identity, driver and capabilities."""
    try:
        return _result(control.node_status())
    except ControlPlaneError as exc:
        return _result({"status": "error", "error": str(exc)})


@mcp.tool()
def run_probe(
    kind: Annotated[
        Literal["gpu", "git", "docker", "ffmpeg"],
        Field(description="Approved diagnostic probe to execute on the node."),
    ],
) -> str:
    """Run one approved diagnostic job and return its measured execution result."""
    try:
        return _result(control.run_probe(kind))
    except ControlPlaneError as exc:
        return _result({"status": "error", "error": str(exc)})


@mcp.tool()
def produce_test_media(
    duration_seconds: Annotated[
        int,
        Field(ge=1, le=10, description="Synthetic test-video duration in seconds."),
    ] = 3,
) -> str:
    """Produce a real MP4 artifact through FFmpeg on the execution node.

    This is the first end-to-end production proof: execution, artifact,
    SHA-256 provenance, duration telemetry and estimated local cost.
    """
    try:
        return _result(control.produce_test_media(duration_seconds))
    except ControlPlaneError as exc:
        return _result({"status": "error", "error": str(exc)})


if __name__ == "__main__":
    mcp.run()
