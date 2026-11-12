"""NVIDIA package probe: one batched, locale-independent apt-cache policy call."""

from types import SimpleNamespace

from netmon import app as app_module

SEARCH = (
    "nvidia-utils-570 - NVIDIA driver support binaries\n"
    "nvidia-utils-580 - NVIDIA driver support binaries\n"
    "nvidia-utils-580-server - not matched\n"
)
POLICY = """nvidia-utils-580:
  Installed: (none)
  Candidate: 580.1-0ubuntu1
  Version table:
     580.1-0ubuntu1 500
nvidia-utils-570:
  Installed: (none)
  Candidate: (none)
  Version table:
"""


def test_probe_uses_one_c_locale_policy_call(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        output = SEARCH if command[1] == "search" else POLICY
        return SimpleNamespace(stdout=output, returncode=0)

    monkeypatch.setattr(app_module, "has_cmd", lambda name: True)
    monkeypatch.setattr(app_module.subprocess, "run", fake_run)
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    monkeypatch.setenv("LANGUAGE", "de")

    result = app_module.probe_nvidia_smi_package_candidates()

    assert result == {
        "installable": True,
        "preferred_package": "nvidia-utils-580",
        "available_packages": ["nvidia-utils-580"],
    }
    assert [command[1] for command, _ in calls] == ["search", "policy"]
    assert calls[1][0][2:] == ["--", "nvidia-utils-580", "nvidia-utils-570"]
    for _command, kwargs in calls:
        assert kwargs["env"]["LC_ALL"] == "C"
        assert "LANGUAGE" not in kwargs["env"]


def test_probe_without_candidates_skips_policy(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(app_module, "has_cmd", lambda name: True)
    monkeypatch.setattr(app_module.subprocess, "run", fake_run)
    assert app_module.probe_nvidia_smi_package_candidates()["installable"] is False
    assert len(calls) == 1
