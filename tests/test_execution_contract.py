import pytest

from ai_media_hub.runtime.execution import (
    ExecutionCapability,
    ExecutionNode,
    ExecutionPolicyError,
    ExecutionRequest,
    validate_execution_request,
)


def make_node() -> ExecutionNode:
    return ExecutionNode(
        id="windows-rtx6000-01",
        name="Windows RTX 6000",
        platform="windows",
        capabilities=frozenset(
            {ExecutionCapability.SHELL, ExecutionCapability.FILESYSTEM}
        ),
    )


def test_valid_shell_request():
    validate_execution_request(
        ExecutionRequest(
            node_id="windows-rtx6000-01",
            operation="shell",
            command="python --version",
        ),
        make_node(),
    )


def test_rejects_node_mismatch():
    request = ExecutionRequest(
        node_id="wrong-node",
        operation="shell",
        command="python --version",
    )
    with pytest.raises(ExecutionPolicyError, match="does not match"):
        validate_execution_request(request, make_node())


def test_rejects_missing_shell_capability():
    node = ExecutionNode(
        id="gpu-node",
        name="GPU node",
        platform="windows",
        capabilities=frozenset({ExecutionCapability.GPU}),
    )
    request = ExecutionRequest(
        node_id="gpu-node",
        operation="shell",
        command="nvidia-smi",
    )
    with pytest.raises(ExecutionPolicyError, match="shell capability"):
        validate_execution_request(request, node)


def test_rejects_excessive_timeout():
    request = ExecutionRequest(
        node_id="windows-rtx6000-01",
        operation="shell",
        command="python --version",
        timeout_seconds=1801,
    )
    with pytest.raises(ExecutionPolicyError, match="timeout_seconds"):
        validate_execution_request(request, make_node())


def test_rejects_empty_command():
    request = ExecutionRequest(
        node_id="windows-rtx6000-01",
        operation="shell",
    )
    with pytest.raises(ExecutionPolicyError, match="requires a command"):
        validate_execution_request(request, make_node())
