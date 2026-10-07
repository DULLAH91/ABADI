import pytest
from ai_media_hub.agent.security import AgentSecurityPolicy

def make_policy(mode="restricted"):
    return AgentSecurityPolicy(token="test-secret", mode=mode)

def test_authentication():
    policy = make_policy()
    assert policy.authenticate("test-secret")
    assert not policy.authenticate("wrong")

def test_restricted_mode_allows_known_tools():
    policy = make_policy()
    policy.validate("nvidia-smi", None, 30)
    policy.validate("git status", None, 30)
    policy.validate("python --version", None, 30)

def test_restricted_mode_denies_unknown_executable():
    with pytest.raises(PermissionError):
        make_policy().validate("powershell Get-Process", None, 30)

def test_trusted_mode_requires_explicit_operator_choice():
    make_policy("trusted").validate("powershell Get-Process", None, 30)

def test_timeout_is_bounded():
    with pytest.raises(PermissionError):
        make_policy().validate("python --version", None, 1801)
