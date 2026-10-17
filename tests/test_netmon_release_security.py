"""M-04: production is signed and staged privately; test output cannot publish.

Positive signing tests use a disposable canonical key in an isolated copy of
both the public key and verifier. The repository trust anchor is never edited.
Real NetMon-key fixtures remain covered by test_netmon_signature.py.
"""

from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

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
        "${PKG_VERSION}": VERSION,
        "${DOCS_VERSION}": VERSION,
        "$CURRENT_AUDIT_HTML": "security-audit.html",
        "$CURRENT_AUDIT_VERSIONED_HTML": "security-audit-r12.html",
    }
    paths = set()
    for name, *_ in PROFILES:
        source = (root / "scripts" / name).read_text()
        paths.update(
            re.findall(r'(?:require_file|cp|convert) "(\$ROOT_DIR/[^"\n]+)"', source)
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
        env=environment(root),
        capture_output=True,
        text=True,
        timeout=30,
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
    (root / f"dist/netmon_{VERSION}_all.deb").unlink()
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
    wrapper = root / "test-bin/python3"
    wrapper.unlink()
    wrapper.write_text(
        "#!/bin/sh\n"
        'case "$1:${3:-}" in -c:*/.release-work/*) echo "simulated EXDEV rename failure" >&2; exit 7;; esac\n'
        f'exec "{shutil.which("python3")}" "$@"\n'
    )
    wrapper.chmod(0o700)
    result = run_build(root, profile, NETMON_MINISIGN_SECRET_KEY=str(secret))
    assert result.returncode != 0
    assert "simulated EXDEV" in result.stderr
    assert "Fertig:" not in result.stdout
    no_production_output(root, profile)
