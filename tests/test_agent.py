from ai_media_hub.execution.agent import ExecutionAgent


def test_agent_requires_token():
    agent = ExecutionAgent()
    assert not agent.authenticate("anything")


def test_agent_rejects_shell_interpreter_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("AMH_AGENT_TOKEN", "test-token")
    monkeypatch.setenv("AMH_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    monkeypatch.delenv("AMH_ALLOW_SHELL", raising=False)
    agent = ExecutionAgent()

    try:
        agent.execute({
            "request_id": "test",
            "operation": "exec",
            "argv": ["powershell.exe", "-NoProfile", "-Command", "Write-Output ok"],
        })
    except PermissionError:
        return
    raise AssertionError("shell interpreter must be disabled by default")


def test_agent_executes_without_shell(monkeypatch, tmp_path):
    monkeypatch.setenv("AMH_AGENT_TOKEN", "test-token")
    monkeypatch.setenv("AMH_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    agent = ExecutionAgent()

    result = agent.execute({
        "request_id": "test",
        "operation": "exec",
        "argv": ["python", "-c", "print('ok')"],
    })

    assert result["exit_code"] == 0
    assert result["stdout"].strip() == "ok"
