import asyncio
from uuid import uuid4

import pytest

from ai_media_hub.runtime.execution import ExecutionCapability, ExecutionNode, ExecutionRequest
from ai_media_hub.runtime.windows_agent import WindowsExecutionAgent


def make_node() -> ExecutionNode:
    return ExecutionNode(
        id="test-node",
        name="Test",
        platform="windows",
        capabilities=frozenset({ExecutionCapability.SHELL}),
    )


@pytest.mark.asyncio
async def test_agent_executes_allowlisted_command_and_preserves_request_id():
    agent = WindowsExecutionAgent(
        make_node(),
        token="secret",
        allowed_command_patterns=(r"python --version",),
    )
    request_id = uuid4()
    result = await agent.execute(
        ExecutionRequest(
            node_id="test-node",
            operation="shell",
            command="python --version",
            request_id=request_id,
        )
    )
    assert result.request_id == request_id
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_agent_rejects_unallowlisted_command():
    agent = WindowsExecutionAgent(
        make_node(),
        token="secret",
        allowed_command_patterns=(r"python --version",),
    )
    with pytest.raises(RuntimeError, match="rejected"):
        await agent.execute(
            ExecutionRequest(
                node_id="test-node",
                operation="shell",
                command="whoami",
            )
        )


@pytest.mark.asyncio
async def test_agent_rejects_node_mismatch():
    agent = WindowsExecutionAgent(
        make_node(),
        token="secret",
        allowed_command_patterns=(r"python --version",),
    )
    with pytest.raises(RuntimeError, match="identity"):
        await agent.execute(
            ExecutionRequest(
                node_id="other-node",
                operation="shell",
                command="python --version",
            )
        )


@pytest.mark.asyncio
async def test_audit_records_rejection(tmp_path):
    audit = tmp_path / "audit.jsonl"
    agent = WindowsExecutionAgent(
        make_node(),
        token="secret",
        allowed_command_patterns=(r"python --version",),
        audit_log=str(audit),
    )
    with pytest.raises(RuntimeError):
        await agent.execute(
            ExecutionRequest(
                node_id="test-node",
                operation="shell",
                command="whoami",
            )
        )
    await asyncio.sleep(0)
    assert "command_policy" in audit.read_text(encoding="utf-8")
