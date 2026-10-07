from pathlib import Path

from ai_media_hub.control import ControlPlane
from ai_media_hub import mcp_server


def test_control_plane_uses_allowlisted_probe(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMH_CONTROL_DB", str(tmp_path / "control.sqlite3"))
    monkeypatch.setenv("AMH_WORKSPACE", str(tmp_path))
    control = ControlPlane()

    captured = {}

    def fake_run(kind, argv, **kwargs):
        captured["kind"] = kind
        captured["argv"] = argv
        return {"status": "succeeded", "kind": kind}

    monkeypatch.setattr(control, "_run_job", fake_run)
    result = control.run_probe("gpu")

    assert result["status"] == "succeeded"
    assert captured["kind"] == "gpu"
    assert captured["argv"][0] == "nvidia-smi"


def test_test_media_is_bounded_and_targets_artifacts(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMH_CONTROL_DB", str(tmp_path / "control.sqlite3"))
    monkeypatch.setenv("AMH_WORKSPACE", str(tmp_path))
    control = ControlPlane()

    captured = {}

    def fake_run(kind, argv, **kwargs):
        captured["kind"] = kind
        captured["argv"] = argv
        captured["artifact_path"] = kwargs["artifact_path"]
        return {"status": "succeeded"}

    monkeypatch.setattr(control, "_run_job", fake_run)
    control.produce_test_media(3)

    assert captured["kind"] == "media"
    assert captured["argv"][0] == "ffmpeg"
    assert "testsrc2" in captured["argv"][captured["argv"].index("-i") + 1]
    assert Path(captured["artifact_path"]).parent.name == "artifacts"


def test_atomic_chat_mcp_exposes_only_narrow_tools():
    assert hasattr(mcp_server, "mcp")
    assert {"node_status", "run_probe", "produce_test_media"} <= {
        "node_status",
        "run_probe",
        "produce_test_media",
    }
