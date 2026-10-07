import pytest
from ai_media_hub.agent.security import AgentSecurityPolicy
def p(mode="restricted"): return AgentSecurityPolicy("test-secret",mode)
def test_auth(): assert p().authenticate("test-secret") and not p().authenticate("wrong")
def test_known(): p().validate("nvidia-smi",None,30); p().validate("git status",None,30); p().validate("python --version",None,30)
def test_unknown(): 
    with pytest.raises(PermissionError): p().validate("powershell Get-Process",None,30)
def test_composition():
    with pytest.raises(PermissionError): p().validate("git status & powershell Get-Process",None,30)
def test_trusted(): p("trusted").validate("powershell Get-Process",None,30)
def test_timeout():
    with pytest.raises(PermissionError): p().validate("python --version",None,1801)
def test_interpreter_escape():
    with pytest.raises(PermissionError): p().validate('python -c "print(1)"',None,30)
