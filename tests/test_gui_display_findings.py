"""Display regressions with synthetic metadata; no App startup or host actions."""

import builtins
import io
from unittest.mock import Mock

import pytest

from netmon import app as app_module
from netmon.app import App


class Value:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


def header_app():
    app = App.__new__(App)
    app.get_default_iface = lambda: "enp42s0"
    app.get_active_dns_servers = Mock(return_value=["1.1.1.1", "9.9.9.9"])
    app.nm_dns_header_var = Value()
    return app


def test_dns_header_binds_real_class_method_and_keeps_global_dns_out(monkeypatch):
    app = header_app()
    calls = []

    def fake_command(args, **kwargs):
        calls.append(args)
        assert args == ["nmcli", "-g", "IP4.DNS", "dev", "show", "enp42s0"]
        return 0, "192.0.2.53"

    monkeypatch.setattr(app_module, "run_cmd", fake_command)
    app.update_dns_header()
    assert len(calls) == 1
    assert app.nm_dns_header_var.value.startswith("NM DNS (enp42s0): 192.0.2.53 |")
    assert "1.1.1.1" not in app.nm_dns_header_var.value
    app.get_active_dns_servers.assert_not_called()


@pytest.mark.parametrize("case", ["empty", "unavailable", "no_interface"])
def test_dns_aggregate_fallback_does_not_claim_interface_ownership(case):
    app = header_app()
    getter = Mock(return_value=[])
    if case == "unavailable":
        getter.side_effect = OSError("synthetic unavailable NM")
    if case == "no_interface":
        app.get_default_iface = lambda: ""
    app.nm_get_dns_list = getter
    app.update_dns_header()
    assert app.nm_dns_header_var.value.startswith("Resolver DNS: 1.1.1.1, 9.9.9.9 |")
    assert "enp42s0" not in app.nm_dns_header_var.value
    if case == "no_interface":
        getter.assert_not_called()


def fake_cpuinfo(monkeypatch, text):
    real_open = builtins.open

    def open_file(path, *args, **kwargs):
        if str(path) == "/proc/cpuinfo":
            if text is None:
                raise FileNotFoundError(path)
            return io.StringIO(text)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", open_file)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("processor : 0\nmodel name : Synthetic x86 CPU\n", "Synthetic x86 CPU"),
        ("Hardware : Synthetic board\nmodel name : Synthetic CPU\n", "Synthetic CPU"),
        ("processor : 0\nHardware : Synthetic ARM SoC\n", "Synthetic ARM SoC"),
        ("Processor : Synthetic ARM CPU\n", "Synthetic ARM CPU"),
    ],
)
def test_cpu_model_uses_description_instead_of_processor_index(
    monkeypatch, text, expected
):
    fake_cpuinfo(monkeypatch, text)
    monkeypatch.setattr(
        app_module, "run_cmd", Mock(side_effect=AssertionError("no fallback expected"))
    )
    assert App._read_cpu_model(None) == expected


@pytest.mark.parametrize("text", ["processor : 0\nprocessor : 1\n", "", None])
def test_cpu_model_missing_description_uses_lscpu(monkeypatch, text):
    fake_cpuinfo(monkeypatch, text)
    command = Mock(
        return_value=(0, "Architecture: x86_64\nModel name: Synthetic fallback CPU\n")
    )
    monkeypatch.setattr(app_module, "run_cmd", command)
    assert App._read_cpu_model(None) == "Synthetic fallback CPU"
    command.assert_called_once_with(["lscpu"], timeout=5)


def test_cpu_model_unavailable_never_returns_numeric_index(monkeypatch):
    fake_cpuinfo(monkeypatch, "processor : 0\n")
    monkeypatch.setattr(app_module, "run_cmd", Mock(return_value=(1, "unavailable")))
    assert App._read_cpu_model(None) == "-"


@pytest.mark.parametrize("version", ["1.1.21~v4dnstest20261030.2", "1:2.0.0-1"])
def test_about_displays_installed_package_version_from_fixed_database(
    monkeypatch, version
):
    monkeypatch.setattr(app_module, "__file__", "/usr/lib/netmon/netmon/app.py")
    command = Mock(return_value=(0, f"install ok installed\t{version}"))
    monkeypatch.setattr(app_module, "run_cmd", command)
    app = App.__new__(App)
    assert app._get_about_program_system_info()["netmon"] == version
    command.assert_called_once_with(
        [
            "/usr/bin/dpkg-query",
            "--admindir=/var/lib/dpkg",
            "-W",
            "-f=${Status}\t${Version}\n",
            "netmon",
        ],
        timeout=3,
    )


@pytest.mark.parametrize(
    "status, output",
    [
        (1, "missing"),
        (0, "deinstall ok config-files\t1.1.21~v4dnstest20261030.2"),
        (0, "install ok half-configured\t1.1.21"),
        (0, "install ok installed\tbad version"),
        (0, "install ok installed\t1.1.21\ninjected"),
        (0, "install ok installed\t"),
    ],
)
def test_about_falls_back_when_installed_metadata_is_unusable(
    monkeypatch, status, output
):
    monkeypatch.setattr(app_module, "__file__", "/usr/lib/netmon/netmon/app.py")
    monkeypatch.setattr(app_module, "run_cmd", Mock(return_value=(status, output)))
    app = App.__new__(App)
    assert (
        app._get_about_program_system_info()["netmon"] == app_module.NETMON_APP_VERSION
    )


def test_about_checkout_does_not_borrow_unrelated_installed_version(monkeypatch):
    monkeypatch.setattr(app_module, "__file__", "/synthetic/checkout/netmon/app.py")
    command = Mock(
        side_effect=AssertionError("checkout must not query installed package")
    )
    monkeypatch.setattr(app_module, "run_cmd", command)
    app = App.__new__(App)
    assert (
        app._get_about_program_system_info()["netmon"] == app_module.NETMON_APP_VERSION
    )
    command.assert_not_called()


@pytest.mark.parametrize("kind", ["directory", "broken_link", "file"])
def test_documentation_fallback_only_accepts_existing_regular_files(
    monkeypatch, tmp_path, kind
):
    docs = tmp_path / "dist" / "docs"
    docs.mkdir(parents=True)
    doc = docs / "netmon_dokumentation_other.pdf"
    if kind == "directory":
        doc.mkdir()
    elif kind == "broken_link":
        doc.symlink_to(docs / "missing.pdf")
    else:
        doc.write_bytes(b"synthetic PDF fixture")
    monkeypatch.setattr(app_module, "NETMON_REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(app_module, "__file__", str(tmp_path / "netmon" / "app.py"))
    real_isdir = app_module.os.path.isdir
    monkeypatch.setattr(
        app_module.os.path,
        "isdir",
        lambda p: False if str(p).startswith("/usr/share/") else real_isdir(p),
    )
    app = App.__new__(App)
    app._get_program_documentation_candidates = lambda: []
    assert app._get_available_program_documentation_path() == (
        str(doc) if kind == "file" else ""
    )
