"""M-04: production is signed and staged privately; test output cannot publish.

Positive signing tests use a disposable canonical key in an isolated copy of
both the public key and verifier. The repository trust anchor is never edited.
Real NetMon-key fixtures remain covered by test_netmon_signature.py.
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.1.21"
PIN = "RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R"
PROFILES = [
    (
        "build_netmon_site_bundle.sh",
        "site-build",
        "netmonroots_public_html.zip",
        "site",
    ),
    (
        "build_netmon_release_update_bundle.sh",
        "site-release-update",
        "netmonroots_release_update.zip",
        "update",
    ),
]


PINNED_ASSET = b"pinned third-party asset\n" * 64
FIXTURE_DOCS_BUILDER = """
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "dist/docs"
out.mkdir(parents=True, exist_ok=True)
changelog = (root / "docs/CHANGELOG.md").read_text()
for ext in ("pdf", "html"):
    (out / f"netmon_dokumentation_1.1.21.{ext}").write_text(ext + ":" + changelog)
"""
FIXTURE_DEB_BUILDER = """
import json
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
identity = json.loads((root / "scripts/fixture_deb_identity.json").read_text())
staging = root / "deb-staging"
(staging / "DEBIAN").mkdir(parents=True)
(staging / "DEBIAN").chmod(0o755)
(staging / "DEBIAN/control").write_text(
    f"Package: {identity['package']}\\nVersion: {identity['version']}\\n"
    "Architecture: all\\nMaintainer: Release Test <release-test@invalid>\\n"
    "Description: snapshot-built release fixture\\n"
)
docs = staging / "usr/share/doc/netmon"
docs.mkdir(parents=True)
(docs / "copyright").write_text((root / "netmon/config/constants.py").read_text())
for generated in sorted((root / "dist/docs").glob("netmon_dokumentation_*")):
    shutil.copyfile(generated, docs / generated.name)
if identity["test_doc"]:
    (docs / "TEST-BUILD.md").write_text("# TESTBUILD\\n")
shutil.copyfile(root / "assets/pinned.bin", docs / "pinned.bin")
out = root / "dist" / f"netmon_{identity['version']}_all.deb"
subprocess.run(
    ["dpkg-deb", "--root-owner-group", "--build", str(staging), str(out)],
    check=True,
    capture_output=True,
)
shutil.rmtree(staging)
print(f"Built: {out}")
"""


def isolated_repo(root, sources=None):
    (root / "scripts").mkdir(parents=True)
    for name in [
        p.name for p in (ROOT / "scripts").glob("*") if p.suffix in {".sh", ".py"}
    ]:
        shutil.copyfile(ROOT / "scripts" / name, root / "scripts" / name)
    for name, source in (sources or {}).items():
        (root / "scripts" / name).write_text(source)
    substitutions = {
        "$ROOT_DIR": str(root),
        "$WORKSPACE_DIR": str(root),
        "${PKG_VERSION}": VERSION,
        "${DOCS_VERSION}": VERSION,
        "$CURRENT_AUDIT_HTML": "security-audit.html",
        "$CURRENT_AUDIT_VERSIONED_HTML": "security-audit-r12.html",
    }
    paths = set()
    for name, *_ in PROFILES:
        source = (root / "scripts" / name).read_text()
        paths.update(
            re.findall(
                r'(?:require_file|copy_release_file|convert) "(\$(?:ROOT|WORKSPACE)_DIR/[^"\n]+)"',
                source,
            )
        )
        paths.update(
            "$ROOT_DIR/site/screenshots/" + value
            for value in re.findall(r"^  (netmon-[\w-]+\.png)", source, re.MULTILINE)
        )
    paths.add("$ROOT_DIR/site/htaccess")
    for name in paths:
        for token, value in substitutions.items():
            name = name.replace(token, value)
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("synthetic input\n")
    (root / "site/latest-version.json").write_text('{"version":"1.1.21"}\n')
    # Locally generated docs for the unsigned test bundle; production builds
    # regenerate them from the commit instead.
    (root / "dist/docs").mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "html"):
        (root / f"dist/docs/netmon_dokumentation_{VERSION}.{ext}").write_text(
            "synthetic input\n"
        )
    (root / "netmon/config").mkdir(parents=True)
    (root / "netmon/config/constants.py").write_text('NETMON_APP_VERSION = "1.1.21"\n')
    # Unrelated website metadata is synthetic; exercise the real release logic.
    (root / "scripts/check_release_consistency.py").write_text(
        'print("synthetic metadata consistent")\n'
    )
    (root / "docs/security").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        ROOT / "docs/security/netmonroots.minisign.pub",
        root / "docs/security/netmonroots.minisign.pub",
    )
    # Committed stand-ins for the documentation and DEB builders. The signed
    # pipeline runs them inside the snapshot, exactly like the real ones.
    (root / "scripts/build_docs_pdf.py").write_text(FIXTURE_DOCS_BUILDER)
    (root / "scripts/build_netmon_deb.sh").write_text(
        '#!/usr/bin/env bash\nexec python3 "$(dirname "$0")/fixture_build_deb.py"\n'
    )
    (root / "scripts/fixture_build_deb.py").write_text(FIXTURE_DEB_BUILDER)
    (root / "scripts/fixture_deb_identity.json").write_text(
        json.dumps({"package": "netmon", "version": VERSION, "test_doc": False})
    )
    # A large git-ignored package asset, admitted only through its pin.
    (root / "assets").mkdir()
    (root / "assets/pinned.bin").write_bytes(PINNED_ASSET)
    (root / "packaging").mkdir(exist_ok=True)
    (root / "packaging/release-assets.sha256").write_text(
        f"{hashlib.sha256(PINNED_ASSET).hexdigest()}  assets/pinned.bin\n"
    )
    tools = root / "test-bin"
    tools.mkdir()
    for tool in (
        "bash",
        "awk",
        "python3",
        "dirname",
        "mkdir",
        "mktemp",
        "mv",
        "rm",
        "flock",
        "cp",
        "cmp",
        "grep",
        "sha256sum",
        "find",
        "chmod",
        "zip",
        "minisign",
        "git",
        "dpkg-deb",
        "tar",
    ):
        actual = shutil.which(tool)
        if actual:
            (tools / tool).symlink_to(actual)
    convert = tools / "convert"
    convert.write_text('#!/bin/sh\ncp "$1" "$4"\n')
    convert.chmod(0o700)
    return root


def environment(root, **values):
    return {"PATH": str(root / "test-bin"), "LC_ALL": "C", "HOME": str(root), **values}


def run_build(root, profile, **values):
    return subprocess.run(
        [shutil.which("bash"), str(root / "scripts" / profile[0])],
        check=False,
        env=environment(root, **values),
        capture_output=True,
        text=True,
        timeout=30,
    )


def gate(root, path, kind):
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts/verify_netmon_release_bundle.py"),
            str(path),
            "--kind",
            kind,
        ],
        check=False,
        env=environment(root),
        capture_output=True,
        text=True,
        timeout=30,
    )


def git(root, *args):
    return subprocess.run(
        [
            shutil.which("git"),
            "-c",
            "user.name=release-test",
            "-c",
            "user.email=release-test@invalid",
            "-C",
            str(root),
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_deb(
    root, version=VERSION, *, test_doc=False, package="netmon", payload="synthetic\n"
):
    """Build a tiny real DEB with the given identity into dist/ (overwrites)."""
    staging = root / "deb-staging"
    shutil.rmtree(staging, ignore_errors=True)
    (staging / "DEBIAN").mkdir(parents=True)
    (staging / "DEBIAN").chmod(0o755)
    (staging / "DEBIAN/control").write_text(
        f"Package: {package}\nVersion: {version}\nArchitecture: all\n"
        "Maintainer: Release Test <release-test@invalid>\n"
        "Description: synthetic release fixture\n"
    )
    docs = staging / "usr/share/doc/netmon"
    docs.mkdir(parents=True)
    (docs / "copyright").write_text(payload)
    # Like build_netmon_deb.sh: ship the generated documentation byte-for-byte.
    for generated in sorted((root / "dist/docs").glob("netmon_dokumentation_*")):
        if generated.is_file() and not generated.is_symlink():
            shutil.copyfile(generated, docs / generated.name)
    if test_doc:
        (docs / "TEST-BUILD.md").write_text("# TESTBUILD\n")
    deb = root / f"dist/netmon_{VERSION}_all.deb"
    deb.parent.mkdir(parents=True, exist_ok=True)
    deb.unlink(missing_ok=True)
    subprocess.run(
        [shutil.which("dpkg-deb"), "--root-owner-group", "--build", staging, deb],
        check=True,
        capture_output=True,
    )
    shutil.rmtree(staging)
    return deb


def write_receipt(root, deb):
    receipt = Path(str(deb) + ".release.json")
    receipt.unlink(missing_ok=True)
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts/netmon_release_deb_receipt.py"),
            "write",
            str(deb),
            "--version",
            VERSION,
            "--commit",
            git(root, "rev-parse", "HEAD"),
        ],
        check=False,
        env=environment(root),
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path):
    assert shutil.which(
        "minisign"
    ), "Install minisign to execute release security regressions"
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
    (root / ".gitignore").write_text("dist/\n*.key\nassets/\ntest-bin/\n")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "release fixture")
    # A locally built DEB in dist/ (used by the unsigned test bundle). Signed
    # production builds never read it; they build their own from the commit.
    build_deb(root)
    return root, secret


def no_production_output(root, profile):
    assert not (root / "dist" / profile[1]).exists()
    work = root / "dist/.release-work"
    assert not work.exists() or not list(work.iterdir())
    assert not list((root / "dist").glob(f"{profile[1]}/**/*.zip"))


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "failure",
    [
        "unsigned-opt-out",
        "missing-minisign",
        "missing-key",
        "nonexistent-key",
        "invalid-key",
        "foreign-key",
        "signer-error",
        "missing-signature",
        "verification-error",
        "zip-error",
        "zip-tamper",
        "directory-tamper",
    ],
)
def test_production_failures_leave_no_ready_artifacts(repo, profile, failure):
    root, secret = repo
    values = {
        "NETMON_MINISIGN_SECRET_KEY": str(secret),
        "NETMON_ALLOW_UNSIGNED_BUILD": "1",
    }
    executable = root / "test-bin/minisign"
    if failure in {"unsigned-opt-out", "missing-key"}:
        values.pop("NETMON_MINISIGN_SECRET_KEY")
    elif failure == "missing-minisign":
        executable.unlink()
    elif failure == "nonexistent-key":
        values["NETMON_MINISIGN_SECRET_KEY"] = str(root / "missing.key")
    elif failure == "invalid-key":
        secret.write_text("invalid private key")
    elif failure == "foreign-key":
        foreign = root / "foreign.key"
        subprocess.run(
            [
                shutil.which("minisign"),
                "-G",
                "-W",
                "-p",
                str(root / "foreign.pub"),
                "-s",
                str(foreign),
            ],
            check=True,
            capture_output=True,
        )
        values["NETMON_MINISIGN_SECRET_KEY"] = str(foreign)
        values["NETMON_EXPECTED_MINISIGN_PUBKEY"] = (
            (root / "foreign.pub").read_text().splitlines()[1]
        )
    elif failure in {"signer-error", "missing-signature", "verification-error"}:
        executable.unlink()
        actual = shutil.which("minisign")
        body = {
            "signer-error": "exit 2",
            "missing-signature": "exit 0",
            "verification-error": f'if [ "$1" = "-V" ]; then exit 3; fi\nexec "{actual}" "$@"',
        }[failure]
        executable.write_text("#!/bin/sh\n" + body + "\n")
        executable.chmod(0o700)
    else:
        zipper = root / "test-bin/zip"
        zipper.unlink()
        if failure == "zip-error":
            body = 'printf partial > "$2"\nexit 2'
        elif failure == "directory-tamper":
            body = f'"{shutil.which("zip")}" "$@"\nprintf changed > "public_html/dist/netmon_{VERSION}_all.deb"'
        else:
            body = f'"{shutil.which("zip")}" "$@"\nprintf corrupt > "$2"'
        zipper.write_text("#!/bin/sh\n" + body + "\n")
        zipper.chmod(0o700)
    result = run_build(root, profile, **values)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Fertig:" not in result.stdout
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_valid_signature_succeeds_and_old_environment_cannot_disable_verification(
    repo, profile
):
    root, secret = repo
    result = run_build(
        root,
        profile,
        NETMON_MINISIGN_SECRET_KEY=str(secret),
        NETMON_ALLOW_UNSIGNED_BUILD="1",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    path = root / "dist" / profile[1] / profile[2]
    verified = gate(root, path, profile[3])
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "Production bundle verified" in result.stdout
    with zipfile.ZipFile(path) as archive:
        assert "public_html/dist/SHA256SUMS.minisig" in archive.namelist()
        assert (
            archive.read("public_html/verify/verify_netmon_signature.sh")
            == (root / "scripts/verify_netmon_signature.sh").read_bytes()
        )


@pytest.mark.parametrize("profile", PROFILES)
def test_failed_build_quarantines_old_artifacts_without_claiming_success(repo, profile):
    root, _ = repo
    prior = root / "dist" / profile[1]
    prior.mkdir()
    (prior / profile[2]).write_bytes(b"old zip must be retained")
    result = run_build(root, profile, NETMON_ALLOW_UNSIGNED_BUILD="1")
    assert result.returncode != 0
    no_production_output(root, profile)
    previous = list(
        (root / "dist/.release-history").glob(
            f"{profile[1]}.previous.*/previous-output/{profile[2]}"
        )
    )
    assert (
        len(previous) == 1 and previous[0].read_bytes() == b"old zip must be retained"
    )
    assert "kein Ergebnis dieses Laufs" in result.stderr


@pytest.mark.parametrize("profile", PROFILES)
def test_foreign_public_key_override_is_rejected(repo, profile):
    root, secret = repo
    other = root / "other.pub"
    other.write_text("untrusted comment: foreign\nRWforeign\n")
    result = run_build(
        root,
        profile,
        NETMON_MINISIGN_SECRET_KEY=str(secret),
        NETMON_MINISIGN_PUBKEY=str(other),
    )
    assert result.returncode != 0
    no_production_output(root, profile)


def test_unsigned_test_bundle_is_separate_and_never_modifies_production(repo):
    root, _ = repo
    existing = {}
    for _, label, filename, _ in PROFILES:
        path = root / "dist" / label / filename
        path.parent.mkdir()
        path.write_bytes(b"production untouched")
        existing[path] = path.read_bytes()
    result = subprocess.run(
        [sys.executable, str(root / "scripts/build_netmon_unsigned_test_bundle.py")],
        env=environment(root),
        capture_output=True,
        text=True,
        check=True,
    )
    artifact = Path(result.stdout.splitlines()[-1])
    assert artifact.is_relative_to(root / "unsigned-test-builds")
    assert "UNSIGNED-TEST-ONLY" in artifact.name
    with zipfile.ZipFile(artifact) as archive:
        assert all(
            name.startswith("UNSIGNED-TEST-ONLY/") for name in archive.namelist()
        )
        assert b"DO NOT PUBLISH" in archive.read(
            "UNSIGNED-TEST-ONLY/UNSIGNED-TEST-ONLY"
        )
        assert not any(
            name.endswith(".minisig") or "public_html" in name
            for name in archive.namelist()
        )
    assert {path: path.read_bytes() for path in existing} == existing
    for _, label, filename, kind in PROFILES:
        copied = root / "dist" / label / filename
        shutil.copyfile(artifact, copied)
        assert gate(root, copied, kind).returncode != 0


def rewrite_zip(path, replacements=None, extras=None):
    with zipfile.ZipFile(path) as archive:
        files = {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }
    for name, content in (replacements or {}).items():
        if content is None:
            files.pop(name)
        else:
            files[name] = content
    files.update(extras or {})
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "failure",
    [
        "signature-missing",
        "signature-corrupt",
        "verifier-modified",
        "hash-verifier-modified",
        "key-foreign",
        "payload-tampered",
        "manifest-tampered",
        "missing-file",
        "test-path",
        "test-content",
        "test-boundary",
        "version",
        "unexpected-payload",
        "traversal",
        "duplicate",
        "symlink",
    ],
)
def test_publication_gate_rejects_bad_or_relabelled_bundles(repo, profile, failure):
    root, secret = repo
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode == 0, result.stdout + result.stderr
    path = root / "dist" / profile[1] / profile[2]
    changes = {
        "verifier-modified": {
            "public_html/verify/verify_netmon_signature.sh": b"#!/bin/sh\nexit 0\n"
        },
        "hash-verifier-modified": {
            "public_html/verify/verify_netmon_download.sh": b"#!/bin/sh\nexit 0\n"
        },
        "signature-missing": {"public_html/dist/SHA256SUMS.minisig": None},
        "signature-corrupt": {"public_html/dist/SHA256SUMS.minisig": b"invalid"},
        "key-foreign": {
            "public_html/verify/netmonroots.minisign.pub": b"untrusted comment: foreign\nRWforeign\n"
        },
        "payload-tampered": {f"public_html/dist/netmon_{VERSION}_all.deb": b"modified"},
        "manifest-tampered": {"public_html/dist/SHA256SUMS": b"modified"},
        "missing-file": {"public_html/downloads.html": None},
        "test-content": {"public_html/downloads.html": b"UNSIGNED-TEST-ONLY"},
        "test-boundary": {
            "public_html/downloads.html": b"x" * (65536 - 4) + b"UNSIGNED-TEST-ONLY"
        },
        "version": {"public_html/latest-version.json": b'{"version":"0"}'},
    }
    extras = {
        "test-path": {"public_html/UNSIGNED-TEST-ONLY": b"test"},
        "unexpected-payload": {"public_html/dist/netmon-test.deb": b"test"},
        "traversal": {"public_html/../outside": b"test"},
    }
    rewrite_zip(path, changes.get(failure), extras.get(failure))
    if failure in {"duplicate", "symlink"}:
        with zipfile.ZipFile(path, "a") as archive:
            if failure == "duplicate":
                with pytest.warns(UserWarning, match="Duplicate"):
                    archive.writestr("public_html/downloads.html", b"duplicate")
            else:
                info = zipfile.ZipInfo("public_html/link")
                info.external_attr = 0o120777 << 16
                archive.writestr(info, b"/etc/passwd")
    rejected = gate(root, path, profile[3])
    assert rejected.returncode != 0, rejected.stdout + rejected.stderr


def test_test_build_failure_cleans_only_its_own_output(repo):
    root, _ = repo
    (root / f"dist/netmon_{VERSION}_all.deb").unlink()
    result = subprocess.run(
        [sys.executable, str(root / "scripts/build_netmon_unsigned_test_bundle.py")],
        check=False,
        env=environment(root),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not list((root / "unsigned-test-builds").iterdir())


@pytest.mark.parametrize("profile", PROFILES)
def test_production_lock_prevents_parallel_output_changes(repo, profile):
    root, secret = repo
    lock = root / "dist" / f".{profile[1]}.lock"
    import fcntl

    with lock.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0
    assert "laeuft bereits" in result.stderr
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_initial_input_failure_cleans_work_and_quarantines_old_release(repo, profile):
    root, secret = repo
    old = root / "dist" / profile[1]
    old.mkdir()
    (old / profile[2]).write_bytes(b"old output")
    # A required input is missing from the commit the release is built from.
    (root / "site/latest-version.json").unlink()
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "drop a required release input")
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0
    no_production_output(root, profile)


@pytest.mark.parametrize("location", ["dist", "work", "history", "output", "lock"])
def test_symlink_output_paths_are_rejected(repo, tmp_path, location):
    root, secret = repo
    target = tmp_path / "outside"
    target.mkdir()
    profile = PROFILES[0]
    paths = {
        "dist": root / "dist",
        "work": root / "dist/.release-work",
        "history": root / "dist/.release-history",
        "output": root / "dist/site-build",
        "lock": root / "dist/.site-build.lock",
    }
    path = paths[location]
    if location == "dist":
        path.rename(root / "original-dist")
    path.symlink_to(target, target_is_directory=True)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0
    assert not list(target.iterdir())


@pytest.mark.parametrize("late_swap", [False, True])
@pytest.mark.parametrize(
    "profile,source",
    [
        (profile, source)
        for profile in PROFILES
        for source in [
            "site/downloads.html",
            "site/download-config.php",
            "site/en",
            "docs/security/netmonroots.minisign.pub",
            "scripts/verify_netmon_download.sh",
        ]
        + (
            ["tools/Favicon.png", "site/robots.txt", "site/screenshots"]
            if profile[3] == "site"
            else []
        )
    ],
)
def test_workspace_symlink_inputs_are_not_signed(
    repo, tmp_path, profile, source, late_swap
):
    root, secret = repo
    path = root / source
    target = tmp_path / "external-input"
    if late_swap:
        # Runs after require_file preflight, before the first staging copy.
        (root / "scripts/check_release_consistency.py").write_text(
            "from pathlib import Path\n"
            f"source, target = Path({str(path)!r}), Path({str(target)!r})\n"
            "source.rename(target)\n"
            "source.symlink_to(target, target_is_directory=target.is_dir())\n"
        )
    else:
        path.rename(target)
        path.symlink_to(target, target_is_directory=target.is_dir())
    marker = root / "signer-called"
    signer = root / "test-bin/minisign"
    signer.unlink()
    signer.write_text(
        '#!/bin/sh\nif [ "$1" = -S ]; then\n'
        f'  printf called >> "{marker}"\nfi\n'
        f'exec "{shutil.which("minisign")}" "$@"\n'
    )
    signer.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Fertig:" not in result.stdout
    assert not marker.exists(), "Symlink input reached production signing"
    no_production_output(root, profile)


@pytest.mark.parametrize(
    "damage", ["eocd-count", "directory-size", "zip64-locator", "comment", "truncated"]
)
def test_metadata_preflight_rejects_ambiguous_archives_before_zip_parser(
    repo, monkeypatch, damage
):
    import importlib.util
    import struct

    root, _ = repo
    path = root / "netmonroots_public_html.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("public_html/file", b"content")
    payload = bytearray(path.read_bytes())
    if damage == "eocd-count":
        struct.pack_into("<H", payload, len(payload) - 12, 2)
    elif damage == "directory-size":
        struct.pack_into("<L", payload, len(payload) - 10, 0x1000000)
    elif damage == "zip64-locator":
        payload[-42:-38] = b"PK\x06\x07"
    elif damage == "comment":
        struct.pack_into("<H", payload, len(payload) - 2, 4)
        payload.extend(b"test")
    else:
        payload = payload[:-1]
    path.write_bytes(payload)
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "m04_gate", ROOT / "scripts/verify_netmon_release_bundle.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def forbidden(*args, **kwargs):
        pytest.fail("Untrusted ZIP directory reached ZipFile")

    monkeypatch.setattr(module.zipfile, "ZipFile", forbidden)
    with pytest.raises(ValueError):
        module.verify_bundle(path, "site")


@pytest.mark.parametrize("profile", PROFILES)
def test_failed_atomic_promotion_leaves_no_production_copy(repo, profile):
    root, secret = repo
    launcher = root / "fail-promotion.py"
    launcher.write_text(
        "import os, runpy, sys\n"
        "def fail(*args, **kwargs):\n"
        "    raise OSError(18, 'simulated EXDEV rename failure')\n"
        "os.rename = fail\n"
        "sys.argv = sys.argv[1:]\n"
        "sys.path.insert(0, os.path.dirname(sys.argv[0]))\n"
        "runpy.run_path(sys.argv[0], run_name='__main__')\n"
    )
    wrapper = root / "test-bin/python3"
    wrapper.unlink()
    wrapper.write_text(
        "#!/bin/sh\n"
        'case "$1" in */verify_netmon_release_bundle.py)\n'
        f'  exec "{shutil.which("python3")}" "{launcher}" "$@";; esac\n'
        f'exec "{shutil.which("python3")}" "$@"\n'
    )
    wrapper.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0
    assert "simulated EXDEV" in result.stderr
    assert "Fertig:" not in result.stdout
    no_production_output(root, profile)


@pytest.mark.parametrize(
    "profile,member",
    [
        (profile, member)
        for profile in PROFILES
        for member in (
            ["download-config.php", "downloads.html", "app.js", ".htaccess"]
            if profile[3] == "site"
            else ["download-config.php", "downloads.html"]
        )
    ],
)
def test_gate_authenticates_deployable_web_content(repo, profile, member):
    root, secret = repo
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode == 0, result.stdout + result.stderr
    path = root / "dist" / profile[1] / profile[2]
    rewrite_zip(path, {f"public_html/{member}": b"modified deployable content\n"})
    rejected = gate(root, path, profile[3])
    assert rejected.returncode != 0, rejected.stdout + rejected.stderr
    assert "Release checksums or member set mismatch" in rejected.stderr


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "failure",
    [
        "missing",
        "missing-signature",
        "corrupt-signature",
        "rehashed",
        "omitted",
        "extra",
        "duplicate",
        "self-reference",
    ],
)
def test_full_member_manifest_requires_signature_and_exact_coverage(
    repo, profile, failure
):
    import hashlib

    root, secret = repo
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode == 0, result.stdout + result.stderr
    path = root / "dist" / profile[1] / profile[2]
    manifest = "public_html/verify/RELEASE-SHA256SUMS"
    signature = manifest + ".minisig"
    with zipfile.ZipFile(path) as archive:
        message = archive.read(manifest)
    changes = {}
    if failure == "missing":
        changes[manifest] = None
    elif failure == "missing-signature":
        changes[signature] = None
    elif failure == "corrupt-signature":
        changes[signature] = b"invalid"
    else:
        lines = message.splitlines(keepends=True)
        selected = next(line for line in lines if line.endswith(b"  downloads.html\n"))
        if failure == "rehashed":
            replacement = b"modified HTML with updated unsigned checksum\n"
            changes["public_html/downloads.html"] = replacement
            message = message.replace(
                selected,
                hashlib.sha256(replacement).hexdigest().encode()
                + b"  downloads.html\n",
            )
        elif failure == "omitted":
            message = message.replace(selected, b"")
        elif failure == "extra":
            message += b"0" * 64 + b"  unexpected.php\n"
        elif failure == "duplicate":
            message += selected
        else:
            message += b"0" * 64 + b"  verify/RELEASE-SHA256SUMS\n"
        changes[manifest] = message
        if failure != "rehashed":
            # Even a valid signature must not authorize partial/ambiguous coverage.
            local = root / "coverage-manifest"
            local.write_bytes(message)
            subprocess.run(
                [
                    shutil.which("minisign"),
                    "-S",
                    "-s",
                    str(secret),
                    "-m",
                    str(local),
                    "-x",
                    str(local) + ".minisig",
                ],
                check=True,
                capture_output=True,
            )
            changes[signature] = Path(str(local) + ".minisig").read_bytes()
    rewrite_zip(path, changes)
    rejected = gate(root, path, profile[3])
    assert rejected.returncode != 0, rejected.stdout + rejected.stderr


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("damage", ["php", "html", "extra", "symlink", "missing"])
def test_post_packaging_web_directory_changes_block_promotion(repo, profile, damage):
    root, secret = repo
    zipper = root / "test-bin/zip"
    zipper.unlink()
    action = {
        "php": "printf changed > public_html/download-config.php",
        "html": "printf changed > public_html/downloads.html",
        "extra": "printf extra > public_html/extra.php",
        "symlink": f'"{sys.executable}" -c \'from pathlib import Path; p=Path("public_html/downloads.html"); p.unlink(); p.symlink_to("docs.html")\'',
        "missing": "rm public_html/downloads.html",
    }[damage]
    zipper.write_text(f'#!/bin/sh\n"{shutil.which("zip")}" "$@"\n{action}\n')
    zipper.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Fertig:" not in result.stdout
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "damage", ["php", "html", "extra", "symlink", "missing", "zip"]
)
def test_late_staging_changes_cannot_diverge_promoted_upload_from_zip(
    repo, profile, damage
):
    root, secret = repo
    action = {
        "php": "(public / 'download-config.php').write_bytes(b'changed PHP')",
        "html": "(public / 'downloads.html').write_bytes(b'changed HTML')",
        "extra": "(public / 'extra.php').write_bytes(b'extra PHP')",
        "symlink": "p = public / 'downloads.html'; p.unlink(); p.symlink_to('docs.html')",
        "missing": "(public / 'downloads.html').unlink()",
        "zip": "Path(sys.argv[1]).write_bytes(b'changed original ZIP')",
    }[damage]
    attack = root / "late-staging-change.py"
    marker = root / "late-staging-change-ran"
    attack.write_text(
        "from pathlib import Path\nimport sys\n"
        "public = Path(sys.argv[1]).parent / 'public_html'\n"
        + action
        + f"\nPath({str(marker)!r}).write_text('changed after verification')\n"
    )
    wrapper = root / "test-bin/python3"
    wrapper.unlink()
    wrapper.write_text(
        "#!/bin/sh\n"
        f'"{shutil.which("python3")}" "$@"\nstatus=$?\n'
        'case "$1:$2" in */verify_netmon_release_bundle.py:*.zip)\n'
        f'  if [ "$status" = 0 ]; then "{shutil.which("python3")}" "{attack}" "$2"; fi;;\n'
        "esac\nexit $status\n"
    )
    wrapper.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert marker.exists(), "The post-verification attack did not run"
    assert result.returncode == 0, result.stdout + result.stderr
    output = root / "dist" / profile[1]
    with zipfile.ZipFile(output / profile[2]) as archive:
        expected = {
            member.filename.removeprefix("public_html/"): archive.read(member)
            for member in archive.infolist()
            if not member.is_dir()
        }
    public = output / "public_html"
    actual = {}
    for path in public.rglob("*"):
        assert not path.is_symlink(), path
        if path.is_file():
            actual[path.relative_to(public).as_posix()] = path.read_bytes()
    assert actual == expected, "Promoted upload differs from authenticated ZIP"


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("failure", ["error", "missing"])
def test_full_manifest_signing_failure_blocks_production(repo, profile, failure):
    root, secret = repo
    signer = root / "test-bin/minisign"
    signer.unlink()
    status = 2 if failure == "error" else 0
    signer.write_text(
        '#!/bin/sh\ncase "$*" in *RELEASE-SHA256SUMS*) '
        f'exit {status};; esac\nexec "{shutil.which("minisign")}" "$@"\n'
    )
    signer.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("failure", ["occupied-target", "invalid-signature"])
def test_snapshot_promotion_failure_preserves_existing_output_and_cleans_work(
    repo, profile, failure
):
    root, secret = repo
    built = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert built.returncode == 0, built.stdout + built.stderr
    archive = root / "dist" / profile[1] / profile[2]
    output = root / "independent-promotion"
    if failure == "occupied-target":
        output.mkdir()
        (output / "keep").write_bytes(b"existing output")
    else:
        rewrite_zip(
            archive, {"public_html/verify/RELEASE-SHA256SUMS.minisig": b"invalid"}
        )
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/verify_netmon_release_bundle.py"),
            str(archive),
            "--kind",
            profile[3],
            "--promote-to",
            str(output),
        ],
        env=environment(root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "unrecognized arguments" not in result.stderr
    if failure == "occupied-target":
        assert (output / "keep").read_bytes() == b"existing output"
    else:
        assert not output.exists()
    assert not list(archive.parent.glob(".verified-release-*"))


def _bundle_member(root, profile, name):
    with zipfile.ZipFile(root / "dist" / profile[1] / profile[2]) as archive:
        return archive.read(f"public_html/{name}")


def _deb_member(deb_bytes, tmp_path, member):
    deb = tmp_path / "inspect.deb"
    deb.write_bytes(deb_bytes)
    out = tmp_path / "inspect"
    shutil.rmtree(out, ignore_errors=True)
    subprocess.run([shutil.which("dpkg-deb"), "-x", deb, out], check=True)
    return (out / member).read_bytes()


@pytest.mark.parametrize("profile", PROFILES)
def test_workspace_deb_and_forged_receipt_are_ignored(repo, tmp_path, profile):
    """Finding: a writer of dist/ planted a DEB and a matching receipt."""
    root, secret = repo
    attacker = build_deb(root, payload="attacker payload\n")
    receipt = Path(str(attacker) + ".release.json")
    receipt.write_text(
        json.dumps(
            {
                "schema": "netmon-release-deb/1",
                "kind": "release",
                "package": "netmon",
                "version": VERSION,
                "filename": attacker.name,
                "sha256": hashlib.sha256(attacker.read_bytes()).hexdigest(),
                "commit": git(root, "rev-parse", "HEAD"),
            }
        )
    )
    docs = root / "dist/docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / f"netmon_dokumentation_{VERSION}.pdf").write_text("attacker docs\n")

    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))

    assert result.returncode == 0, result.stdout + result.stderr
    published = _bundle_member(root, profile, f"dist/netmon_{VERSION}_all.deb")
    assert published != attacker.read_bytes()
    constants = (root / "netmon/config/constants.py").read_bytes()
    assert (
        _deb_member(published, tmp_path, "usr/share/doc/netmon/copyright") == constants
    )
    assert (
        _deb_member(published, tmp_path, "usr/share/doc/netmon/pinned.bin")
        == PINNED_ASSET
    )
    pdf = _bundle_member(root, profile, f"dist/docs/netmon_dokumentation_{VERSION}.pdf")
    assert pdf != b"attacker docs\n"
    assert pdf == _deb_member(
        published, tmp_path, f"usr/share/doc/netmon/netmon_dokumentation_{VERSION}.pdf"
    )


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "identity",
    [
        {"version": f"{VERSION}~v4dnstest20261111.1"},
        {"test_doc": True},
        {"package": "netmon-test"},
    ],
    ids=["test-version", "test-build-doc", "foreign-package"],
)
def test_snapshot_built_deb_without_release_identity_is_never_signed(
    repo, profile, identity
):
    root, secret = repo
    path = root / "scripts/fixture_deb_identity.json"
    path.write_text(json.dumps({**json.loads(path.read_text()), **identity}))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "non-release package identity")
    marker = _signing_marker(root)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Release-Abbruch" in result.stderr
    assert not marker.exists()
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("fault", ["mismatch", "missing", "symlink", "tracked"])
def test_pinned_package_assets_must_match_their_committed_hash(
    repo, tmp_path, profile, fault
):
    root, secret = repo
    asset = root / "assets/pinned.bin"
    if fault == "mismatch":
        asset.write_bytes(b"swapped third-party asset\n")
    elif fault == "missing":
        asset.unlink()
    elif fault == "symlink":
        outside = tmp_path / "outside.bin"
        outside.write_bytes(PINNED_ASSET)
        asset.unlink()
        asset.symlink_to(outside)
    else:
        (root / ".gitignore").write_text("dist/\n*.key\ntest-bin/\n")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "track the pinned asset")
    marker = _signing_marker(root)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Gepinnte" in result.stderr
    assert not marker.exists()
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("boundary", ["identity", "manifest"])
def test_deb_replaced_after_identity_check_is_not_published(repo, profile, boundary):
    root, secret = repo
    # A different, valid DEB with the same release identity replaces the
    # snapshot-built bytes after their digest was approved.
    deb = root / f"dist/netmon_{VERSION}_all.deb"
    replacement = root / "replacement.deb"
    shutil.copyfile(build_deb(root, payload="unapproved payload\n"), replacement)
    if boundary == "identity":
        action = (
            'case "$1:${2:-}" in */netmon_release_deb_receipt.py:identity)\n'
            f'  cp "{replacement}" "$3";;\n'
            "esac\n"
        )
    else:
        action = (
            'case "$1:$*" in */verify_netmon_release_bundle.py:*--write-manifest*)\n'
            f'  cp "{replacement}" "$2/dist/{deb.name}";;\n'
            "esac\n"
        )
    wrapper = root / "test-bin/python3"
    wrapper.unlink()
    wrapper.write_text(
        "#!/bin/sh\n"
        f'"{shutil.which("python3")}" "$@"\n'
        "status=$?\n" + action + "exit $status\n"
    )
    wrapper.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "DEB differs from receipt-approved SHA-256" in result.stderr
    assert "Fertig:" not in result.stdout
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_valid_signatures_do_not_override_expected_receipt_digest(repo, profile):
    root, secret = repo
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode == 0, result.stdout + result.stderr
    path = root / "dist" / profile[1] / profile[2]
    command = [
        sys.executable,
        str(root / "scripts/verify_netmon_release_bundle.py"),
        str(path),
        "--kind",
        profile[3],
        "--release-deb-sha256",
    ]
    approved = hashlib.sha256(
        _bundle_member(root, profile, f"dist/netmon_{VERSION}_all.deb")
    ).hexdigest()
    for digest in (approved, "0" * 64):
        checked = subprocess.run(
            [*command, digest],
            env=environment(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if digest == approved:
            assert checked.returncode == 0, checked.stdout + checked.stderr
        else:
            assert checked.returncode != 0
            assert "DEB differs from receipt-approved SHA-256" in checked.stderr


def test_receipt_is_only_written_for_clean_committed_release_sources(repo):
    root, _ = repo
    deb = build_deb(root)
    (root / "netmon/config/constants.py").write_text(
        'NETMON_APP_VERSION = "1.1.21"\n# local edit\n'
    )
    dirty = write_receipt(root, deb)
    assert dirty.returncode != 0 and "committetem Stand" in dirty.stderr
    git(root, "checkout", "--", "netmon/config/constants.py")
    (root / "netmon/untracked_module.py").write_text("UNREVIEWED = True\n")
    untracked = write_receipt(root, deb)
    assert untracked.returncode != 0 and "untracked_module.py" in untracked.stderr
    (root / "netmon/untracked_module.py").unlink()
    build_deb(root, f"{VERSION}~v4dnstest20261111.1")
    test_version = write_receipt(root, deb)
    assert test_version.returncode != 0 and "kein Release" in test_version.stderr
    assert not Path(str(deb) + ".release.json").exists()


def test_deb_builder_release_mode_is_exclusive_and_explicit():
    source = (ROOT / "scripts/build_netmon_deb.sh").read_text()
    assert '[[ $# == 1 && "$1" == "--release" ]]' in source
    assert 'netmon_release_deb_receipt.py" preflight' in source
    result = subprocess.run(
        [
            shutil.which("bash"),
            str(ROOT / "scripts/build_netmon_deb.sh"),
            "--release",
            "--test-version",
            f"{VERSION}~v4dnstest20261111.1",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert not (
        ROOT / "dist" / f"netmon_{VERSION}~v4dnstest20261111.1_all.deb"
    ).exists()


# --- Production bundles sign only committed content and tooling ----------


def _signing_marker(root):
    marker = root / "signer-called"
    signer = root / "test-bin/minisign"
    signer.unlink()
    signer.write_text(
        '#!/bin/sh\nif [ "$1" = -S ]; then\n'
        f'  printf called >> "{marker}"\nfi\n'
        f'exec "{shutil.which("minisign")}" "$@"\n'
    )
    signer.chmod(0o700)
    return marker


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "change",
    [
        "modified-page",
        "untracked-page",
        "staged-page",
        "modified-tool",
        "modified-launcher",
        "modified-common",
        "modified-pubkey",
        "untracked-package-module",
        "modified-deb-builder",
        "modified-asset-pins",
    ],
)
def test_uncommitted_inputs_or_tooling_are_never_signed(repo, profile, change):
    root, secret = repo
    if change == "modified-page":
        (root / "site/downloads.html").write_text("<p>unreviewed</p>\n")
    elif change == "untracked-page":
        (root / "site/en/unreviewed.html").write_text("<p>unreviewed</p>\n")
    elif change == "staged-page":
        (root / "site/docs.html").write_text("<p>staged only</p>\n")
        git(root, "add", "site/docs.html")
    elif change == "modified-tool":
        path = root / "scripts/verify_netmon_release_bundle.py"
        path.write_text(path.read_text() + "\n# local tooling edit\n")
    elif change == "modified-launcher":
        path = root / "scripts/netmon_release_source.py"
        path.write_text(path.read_text() + "\n# local launcher edit\n")
    elif change == "modified-common":
        path = root / "scripts/netmon_release_common.sh"
        path.write_text(path.read_text() + "\n# local edit\n")
    elif change == "untracked-package-module":
        (root / "netmon/unreviewed.py").write_text("UNREVIEWED = True\n")
    elif change == "modified-deb-builder":
        path = root / "scripts/build_netmon_deb.sh"
        path.write_text(path.read_text() + "# local edit\n")
    elif change == "modified-asset-pins":
        (root / "packaging/release-assets.sha256").write_text(
            f"{'0' * 64}  assets/pinned.bin\n"
        )
    else:
        path = root / "docs/security/netmonroots.minisign.pub"
        path.write_text(path.read_text() + "\n")
    marker = _signing_marker(root)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "committetem Stand" in result.stderr
    assert not marker.exists(), "uncommitted release input reached signing"
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_build_signs_the_commit_even_if_workspace_changes_mid_build(repo, profile):
    root, secret = repo
    committed = (root / "site/docs.html").read_bytes()
    # Unrelated dirty files elsewhere do not block an official build.
    (root / "unrelated-notes.md").write_text("local notes\n")
    # After the clean check and snapshot, edit a signed input and a tool in
    # the workspace while the build runs: neither may reach the bundle.
    wrapper = root / "test-bin/python3"
    wrapper.unlink()
    wrapper.write_text(
        "#!/bin/sh\n"
        'case "$1" in */check_release_consistency.py)\n'
        f'  printf "<p>late edit</p>" > "{root}/site/docs.html"\n'
        f'  printf "raise SystemExit(9)\\n" >> "{root}/scripts/verify_netmon_release_bundle.py"\n'
        "esac\n"
        f'exec "{shutil.which("python3")}" "$@"\n'
    )
    wrapper.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Release-Quelle: Commit " + git(root, "rev-parse", "HEAD") in result.stderr
    bundle = root / "dist" / profile[1] / profile[2]
    with zipfile.ZipFile(bundle) as archive:
        assert archive.read("public_html/docs.html") == committed


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("document", ["pdf", "html"])
def test_published_docs_must_match_the_snapshot_built_deb(repo, profile, document):
    root, secret = repo
    wrapper = root / "test-bin/python3"
    wrapper.unlink()
    wrapper.write_text(
        "#!/bin/sh\n"
        f'"{shutil.which("python3")}" "$@"\n'
        "status=$?\n"
        'case "$1:${2:-}" in */netmon_release_deb_receipt.py:identity)\n'
        '  printf changed > "$(dirname "$3")/docs/'
        f'netmon_dokumentation_{VERSION}.{document}";;\n'
        "esac\n"
        "exit $status\n"
    )
    wrapper.chmod(0o700)
    marker = _signing_marker(root)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "belegten Release-DEB" in result.stderr
    assert not marker.exists()
    no_production_output(root, profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_workspace_script_cannot_skip_the_snapshot(repo, profile):
    root, secret = repo
    marker = _signing_marker(root)
    result = run_build(
        root,
        profile,
        NETMON_MINISIGN_SECRET_KEY=str(secret),
        NETMON_RELEASE_SOURCE_DIR=str(root),
        NETMON_RELEASE_WORKSPACE=str(root),
        NETMON_RELEASE_COMMIT=git(root, "rev-parse", "HEAD"),
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Commit-Snapshot" in result.stderr
    assert not marker.exists()
    no_production_output(root, profile)
