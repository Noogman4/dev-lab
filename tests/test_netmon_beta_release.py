"""Public-beta versions: scheme, update channel and the signed release gate.

Name: "NetMon 1.1.22 Public Beta 1", package version ``1.1.22~beta1``.
Sequence under test: 1.1.21 -> 1.1.22~beta1 -> 1.1.22~beta2 -> 1.1.22.
Signed builds use the disposable key of test_netmon_release_security; the
repository trust anchor is never edited. Nothing is installed or published.
"""

import ast
import itertools
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from netmon import app as app_module
from netmon.app import App
from netmon.core import release_version as core_version

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import read_netmon_version as script_version  # noqa: E402
from test_netmon_release_security import (  # noqa: E402
    PIN,
    PROFILES,
    environment,
    gate,
    git,
    isolated_repo,
    run_build,
)

SEQUENCE = ["1.1.21", "1.1.22~beta1", "1.1.22~beta2", "1.1.22~beta10", "1.1.22"]
VALID = SEQUENCE + ["1.1.23", "1.2.0~beta1", "2.0", "0.9.9.1", "1.1.22~beta9999"]
INVALID = [
    "",
    "1",
    "1.1.22~beta",
    "1.1.22~beta0",
    "1.1.22~beta01",
    "1.1.22-beta1",
    "1.1.22beta1",
    "1.1.22~rc1",
    "1.1.22~Beta1",
    "1.1.22~beta1~v4dnstest20261115.1",
    "1.1.22~v4dnstest20261115.1",
    "1.1.22-1",
    "1:1.1.22",
    "01.1.22",
    "1.1.22 ",
    "1.1.22\n",
    "1.1.22~beta1/../x",
    None,
    1122,
]


@pytest.mark.parametrize("module", [core_version, script_version])
def test_scheme_accepts_only_final_releases_and_public_betas(module):
    assert all(module.is_release_version(value) for value in VALID)
    assert not any(module.is_release_version(value) for value in INVALID)
    assert module.is_prerelease("1.1.22~beta1")
    assert not module.is_prerelease("1.1.22")
    assert module.display_version("1.1.22~beta1") == "1.1.22 Public Beta 1"
    assert module.display_version("1.1.22") == "1.1.22"
    assert module.display_version("1.1.21-1") == "1.1.21-1"


def test_app_and_release_tooling_share_one_scheme():
    def scheme_source(path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {
            "_VERSION",
            "parse_release_version",
            "is_release_version",
            "is_prerelease",
            "release_sort_key",
            "compare_release_versions",
            "display_version",
        }
        return {
            ast.unparse(node)
            for node in tree.body
            if (isinstance(node, ast.FunctionDef) and node.name in names)
            or (
                isinstance(node, ast.Assign)
                and any(getattr(t, "id", None) in names for t in node.targets)
            )
        }

    core = scheme_source(ROOT / "netmon/core/release_version.py")
    assert len(core) == 7
    assert core == scheme_source(ROOT / "scripts/read_netmon_version.py")


def test_order_matches_dpkg_for_every_pair():
    dpkg = shutil.which("dpkg")
    if dpkg is None:
        pytest.skip("dpkg unavailable")
    for left, right in itertools.product(VALID, repeat=2):
        expected = core_version.compare_release_versions(left, right)
        operator = {-1: "lt", 0: "eq", 1: "gt"}[expected]
        assert (
            subprocess.run(
                [dpkg, "--compare-versions", left, operator, right]
            ).returncode
            == 0
        ), (left, operator, right)
    assert sorted(SEQUENCE, key=core_version.release_sort_key) == SEQUENCE


# ---------------------------------------------------------------- in-app check


@pytest.fixture
def about(monkeypatch):
    app = App.__new__(App)
    app.tr = lambda _key, fallback: fallback
    app._about_update_redirect_done = False
    app.netmon_roots_latest_version_url = "https://netmonroots.com/latest-version.json"
    app.netmon_roots_downloads_url = "https://netmonroots.com/downloads.html"
    statuses, links = [], []
    app._set_about_version_status = statuses.append
    app.after = lambda _delay, callback: callback()
    app.log_safe = lambda _text: None
    app._open_url_with_xdg_open = lambda url, label: links.append(url) or True

    class Immediate:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module.threading, "Thread", Immediate)

    def check(installed, metadata):
        statuses.clear()
        links.clear()
        app._about_update_redirect_done = False
        monkeypatch.setattr(app_module, "NETMON_APP_VERSION", installed)
        monkeypatch.setattr(app_module, "fetch_release_metadata", lambda _u: metadata)
        app.check_about_latest_version()
        return statuses[-1], links

    return check


BETA_PAGE = "https://netmonroots.com/beta.html"


def latest(stable, beta=None):
    data = {"version": stable, "download_url": "https://netmonroots.com/downloads.html"}
    if beta:
        data["beta"] = {"version": beta, "download_url": BETA_PAGE}
    return data


@pytest.mark.parametrize(
    "installed, metadata, expected_status, expected_link",
    [
        # Stable users are not pointed at a beta through the beta channel.
        ("1.1.21", latest("1.1.21", "1.1.22~beta1"), "NetMon ist aktuell", None),
        # ... but are, if the site deliberately publishes it as "version".
        (
            "1.1.21",
            latest("1.1.22~beta1"),
            "Neue Version gefunden: 1.1.22 Public Beta 1 (installiert: 1.1.21)",
            "https://netmonroots.com/downloads.html",
        ),
        (
            "1.1.22~beta1",
            latest("1.1.21", "1.1.22~beta1"),
            "NetMon ist aktuell. Installiert und online: 1.1.22 Public Beta 1.",
            None,
        ),
        (
            "1.1.22~beta1",
            latest("1.1.21", "1.1.22~beta2"),
            "Neue Version gefunden: 1.1.22 Public Beta 2 "
            "(installiert: 1.1.22 Public Beta 1)",
            BETA_PAGE,
        ),
        (
            "1.1.22~beta2",
            latest("1.1.22"),
            "Neue Version gefunden: 1.1.22 (installiert: 1.1.22 Public Beta 2)",
            "https://netmonroots.com/downloads.html",
        ),
        # A stale beta entry never outranks the final release.
        (
            "1.1.22~beta2",
            latest("1.1.22", "1.1.22~beta2"),
            "Neue Version gefunden: 1.1.22 (installiert: 1.1.22 Public Beta 2)",
            "https://netmonroots.com/downloads.html",
        ),
        ("1.1.22", latest("1.1.22", "1.1.22~beta2"), "NetMon ist aktuell", None),
        ("1.1.22", latest("1.1.22~beta2"), "Lokale Version ist neuer", None),
        # Next cycle: the final 1.1.22 user stays stable, a beta user moves on.
        ("1.1.22", latest("1.1.22", "1.1.23~beta1"), "NetMon ist aktuell", None),
        (
            "1.1.22~beta2",
            latest("1.1.22", "1.1.23~beta1"),
            "Neue Version gefunden: 1.1.23 Public Beta 1",
            BETA_PAGE,
        ),
    ],
)
def test_update_hint_follows_beta_sequence(
    about, installed, metadata, expected_status, expected_link
):
    status, links = about(installed, metadata)
    assert status.startswith(expected_status)
    assert links == ([expected_link] if expected_link else [])


def test_old_client_comparison_would_have_hidden_the_final_release():
    # Regression: the former digits-only comparison ranked 1.1.22~beta1 as
    # (1, 1, 22, 1) above 1.1.22, so no beta tester would see the final.
    assert App._normalize_version_tuple(None, "1.1.22~beta1") > (1, 1, 22)
    assert (
        App._compare_version_strings(App.__new__(App), "1.1.22~beta1", "1.1.22") == -1
    )


def test_beta_channel_link_keeps_the_pinned_origin(about):
    metadata = latest("1.1.21")
    metadata["beta"] = {
        "version": "1.1.22~beta2",
        "download_url": "https://evil.invalid/",
    }
    status, links = about("1.1.22~beta1", metadata)
    assert status.startswith("Neue Version gefunden: 1.1.22 Public Beta 2")
    assert links == ["https://netmonroots.com/downloads.html"]


@pytest.mark.parametrize(
    "beta", ["1.1.22~rc1", "1.1.22", None, 5, ["1.1.22~beta2"], "1.1.22~beta2 "]
)
def test_malformed_beta_entry_is_ignored(about, beta):
    status, links = about(
        "1.1.22~beta1", {"version": "1.1.21", "beta": {"version": beta}}
    )
    assert status.startswith("Lokale Version ist neuer")
    assert links == []


# ---------------------------------------------------- latest-version contract


@pytest.mark.parametrize(
    "version, metadata, ok",
    [
        ("1.1.22", {"version": "1.1.22"}, True),
        ("1.1.22", {"version": "1.1.22", "beta": {"version": "1.1.23~beta1"}}, True),
        ("1.1.22", {"version": "1.1.22", "beta": {"version": "1.1.23"}}, False),
        ("1.1.22", {"version": "1.1.22~beta1"}, False),
        ("1.1.22", {"version": "1.1.21", "beta": {"version": "1.1.22"}}, False),
        ("1.1.22~beta1", {"version": "1.1.22~beta1"}, True),
        (
            "1.1.22~beta1",
            {"version": "1.1.21", "beta": {"version": "1.1.22~beta1"}},
            True,
        ),
        (
            "1.1.22~beta1",
            {"version": "1.1.21", "beta": {"version": "1.1.22~beta2"}},
            False,
        ),
        (
            "1.1.22~beta1",
            {"version": "1.1.22", "beta": {"version": "1.1.22~beta1"}},
            False,
        ),
        (
            "1.1.22~beta2",
            {"version": "1.1.22~beta1", "beta": {"version": "1.1.22~beta2"}},
            False,
        ),
        ("1.1.22~beta1", {"version": "1.1.21"}, False),
        ("1.1.22~beta1", {"version": "x", "beta": {"version": "1.1.22~beta1"}}, False),
        ("1.1.22~beta1", ["1.1.22~beta1"], False),
    ],
)
def test_latest_version_contract(version, metadata, ok):
    assert (script_version.latest_metadata_error(metadata, version) is None) is ok


# -------------------------------------------------------------- DEB identity


def _deb(root, version, *, test_doc=False):
    staging = root / f"stage-{version}"
    (staging / "DEBIAN").mkdir(parents=True)
    (staging / "DEBIAN").chmod(0o755)
    (staging / "DEBIAN/control").write_text(
        f"Package: netmon\nVersion: {version}\nArchitecture: all\n"
        "Maintainer: Release Test <release-test@invalid>\n"
        "Description: beta fixture\n"
    )
    docs = staging / "usr/share/doc/netmon"
    docs.mkdir(parents=True)
    (docs / "copyright").write_text(version)
    if test_doc:
        (docs / "TEST-BUILD.md").write_text("# TESTBUILD\n")
    deb = root / f"netmon_{version}_all.deb"
    subprocess.run(
        [shutil.which("dpkg-deb"), "--root-owner-group", "--build", staging, deb],
        check=True,
        capture_output=True,
    )
    return deb


def _identity(deb, version):
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/netmon_release_deb_receipt.py"),
            "identity",
            str(deb),
            "--version",
            version,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "version, test_doc, ok",
    [
        ("1.1.22~beta1", False, True),
        ("1.1.22~beta2", False, True),
        ("1.1.22", False, True),
        ("1.1.22~beta1", True, False),
        ("1.1.22~beta1~v4dnstest20261115.1", False, False),
        ("1.1.22~v4dnstest20261115.1", False, False),
        ("1.1.22~rc1", False, False),
    ],
)
def test_release_identity_accepts_betas_but_never_test_builds(
    tmp_path, version, test_doc, ok
):
    if shutil.which("dpkg-deb") is None:
        pytest.skip("dpkg-deb unavailable")
    result = _identity(_deb(tmp_path, version, test_doc=test_doc), version)
    assert (result.returncode == 0) is ok, result.stdout + result.stderr


def test_download_verifier_accepts_beta_filenames_only_as_plain_names(tmp_path):
    deb = tmp_path / "netmon_1.1.22~beta1_all.deb"
    deb.write_bytes(b"beta payload\n")
    digest = subprocess.run(
        ["sha256sum", deb.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    (tmp_path / "SHA256SUMS").write_text(digest)
    script = ROOT / "scripts/verify_netmon_download.sh"
    ok = subprocess.run(
        ["bash", str(script), "SHA256SUMS", deb.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    (tmp_path / "~home").write_bytes(b"x")
    (tmp_path / "SHA256SUMS").write_text(
        digest
        + subprocess.run(
            ["sha256sum", "~home"], cwd=tmp_path, capture_output=True, text=True
        ).stdout
    )
    bad = subprocess.run(
        ["bash", str(script), "SHA256SUMS", "~home"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert bad.returncode != 0


# ---------------------------------------------- signed pipeline, full sequence

DOCS_BUILDER = """
from pathlib import Path
from read_netmon_version import read_netmon_version

root = Path(__file__).resolve().parent.parent
version = read_netmon_version()
out = root / "dist/docs"
out.mkdir(parents=True, exist_ok=True)
for ext in ("pdf", "html"):
    (out / f"netmon_dokumentation_{version}.{ext}").write_text(ext + ":" + version)
"""


def set_release(root, version, metadata):
    (root / "netmon/config/constants.py").write_text(
        f'NETMON_APP_VERSION = "{version}"\n'
    )
    (root / "site/latest-version.json").write_text(json.dumps(metadata) + "\n")
    (root / "scripts/fixture_deb_identity.json").write_text(
        json.dumps({"package": "netmon", "version": version, "test_doc": False})
    )
    for ext in ("pdf", "html"):
        local = root / f"dist/docs/netmon_dokumentation_{version}.{ext}"
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text("local unsigned test input\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", f"release {version}")


@pytest.fixture
def beta_repo(tmp_path):
    if not shutil.which("minisign") or not shutil.which("dpkg-deb"):
        pytest.skip("minisign and dpkg-deb are required for signed builds")
    root = isolated_repo(tmp_path / "repo")
    secret, public = root / "trusted-test.key", root / "trusted-test.pub"
    subprocess.run(
        [shutil.which("minisign"), "-G", "-W", "-p", str(public), "-s", str(secret)],
        check=True,
        capture_output=True,
    )
    key = public.read_text().splitlines()[1]
    shutil.copyfile(public, root / "docs/security/netmonroots.minisign.pub")
    verifier = root / "scripts/verify_netmon_signature.sh"
    verifier.write_text(verifier.read_text().replace(PIN, key))
    (root / "scripts/build_docs_pdf.py").write_text(DOCS_BUILDER)
    (root / ".gitignore").write_text(
        "dist/\n*.key\nassets/\ntest-bin/\nunsigned-test-builds/\nkept/\n"
    )
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "release fixture 1.1.21")
    return root, secret


def build_and_keep(root, secret, profile, version):
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode == 0, result.stdout + result.stderr
    kept = root / "kept" / version / profile[2]
    kept.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / "dist" / profile[1] / profile[2], kept)
    return kept


def deb_version(bundle, version):
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        deb = f"public_html/dist/netmon_{version}_all.deb"
        assert deb in names, names
        latest = json.loads(archive.read("public_html/latest-version.json"))
        target = bundle.parent / "payload.deb"
        target.write_bytes(archive.read(deb))
    control = subprocess.run(
        [shutil.which("dpkg-deb"), "-f", str(target), "Version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return control, latest


@pytest.mark.parametrize("profile", PROFILES, ids=[p[3] for p in PROFILES])
@pytest.mark.parametrize("channel", ["beta-entry", "top-level"])
def test_signed_sequence_beta_to_next_beta_to_final(beta_repo, profile, channel):
    root, secret = beta_repo
    steps = [
        ("1.1.22~beta1", "1.1.21"),
        ("1.1.22~beta2", "1.1.21"),
        ("1.1.22", None),
    ]
    bundles, debs = {}, []
    for version, stable in steps:
        if stable is None:
            metadata = {"version": version}
        elif channel == "beta-entry":
            metadata = {"version": stable, "beta": {"version": version}}
        else:
            metadata = {"version": version}
        set_release(root, version, metadata)
        bundle = build_and_keep(root, secret, profile, version)
        verified = gate(root, bundle, profile[3])
        assert verified.returncode == 0, verified.stdout + verified.stderr
        control, published = deb_version(bundle, version)
        assert control == version and published == metadata
        debs.append(control)
        # Every older signed bundle is stale for the new checkout.
        for older in bundles.values():
            assert gate(root, older, profile[3]).returncode != 0
        bundles[version] = bundle
    for older, newer in zip(debs, debs[1:]):
        assert (
            subprocess.run(
                ["dpkg", "--compare-versions", older, "lt", newer]
            ).returncode
            == 0
        )


def test_beta_signature_checks_stay_mandatory(beta_repo):
    root, secret = beta_repo
    profile = PROFILES[1]
    set_release(
        root, "1.1.22~beta1", {"version": "1.1.21", "beta": {"version": "1.1.22~beta1"}}
    )
    unsigned = run_build(root, profile, NETMON_ALLOW_UNSIGNED_BUILD="1")
    assert unsigned.returncode != 0
    bundle = build_and_keep(root, secret, profile, "1.1.22~beta1")
    assert gate(root, bundle, profile[3]).returncode == 0
    for replacement in (
        # Re-labelling the beta as final, or dropping it from the channel.
        {"version": "1.1.22"},
        {"version": "1.1.21"},
        {"version": "1.1.21", "beta": {"version": "1.1.22~beta2"}},
    ):
        tampered = bundle.parent / "tampered" / bundle.name
        tampered.parent.mkdir(exist_ok=True)
        with (
            zipfile.ZipFile(bundle) as source,
            zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as target,
        ):
            for info in source.infolist():
                data = source.read(info)
                if info.filename == "public_html/latest-version.json":
                    data = json.dumps(replacement).encode() + b"\n"
                target.writestr(info, data)
        assert gate(root, tampered, profile[3]).returncode != 0
        tampered.unlink()


def test_beta_deb_receipt_lane_still_requires_a_clean_commit(beta_repo):
    root, _ = beta_repo
    set_release(
        root, "1.1.22~beta1", {"version": "1.1.21", "beta": {"version": "1.1.22~beta1"}}
    )
    (root / "netmon/config/constants.py").write_text(
        'NETMON_APP_VERSION = "1.1.22~beta1"\n# local edit\n'
    )
    deb = _deb(root / "dist", "1.1.22~beta1")
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/netmon_release_deb_receipt.py"),
            "write",
            str(deb),
            "--version",
            "1.1.22~beta1",
            "--commit",
            git(root, "rev-parse", "HEAD"),
        ],
        env=environment(root),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "committetem Stand" in result.stderr + result.stdout


def test_unsigned_beta_test_bundle_is_never_accepted(beta_repo):
    root, _ = beta_repo
    set_release(
        root, "1.1.22~beta1", {"version": "1.1.21", "beta": {"version": "1.1.22~beta1"}}
    )
    _deb(root / "dist", "1.1.22~beta1")
    result = subprocess.run(
        [sys.executable, str(root / "scripts/build_netmon_unsigned_test_bundle.py")],
        env=environment(root),
        capture_output=True,
        text=True,
        check=True,
    )
    artifact = Path(result.stdout.splitlines()[-1])
    with zipfile.ZipFile(artifact) as archive:
        info = json.loads(archive.read("UNSIGNED-TEST-ONLY/test-build.json"))
    assert info == {
        "identity": "UNSIGNED-TEST-ONLY",
        "production_release": False,
        "source_version": "1.1.22~beta1",
    }
    for _, label, filename, kind in PROFILES:
        copied = root / "dist" / label / filename
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(artifact, copied)
        assert gate(root, copied, kind).returncode != 0
