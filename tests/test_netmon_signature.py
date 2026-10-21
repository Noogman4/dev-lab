"""H-01 regressions: immutable release trust anchor and real offline signatures."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify_netmon_signature.sh"
PUBLIC_KEY = ROOT / "docs" / "security" / "netmonroots.minisign.pub"
FIXTURES = ROOT / "tests" / "fixtures" / "minisign"
MESSAGE = FIXTURES / "netmon-1.1.21.SHA256SUMS"
SIGNATURE = FIXTURES / "netmon-1.1.21.SHA256SUMS.minisig"
PIN = "RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R"
BASH = shutil.which("bash")


def verify(key=PUBLIC_KEY, signature=SIGNATURE, message=MESSAGE, *, env=None):
    return subprocess.run(
        [BASH, str(VERIFIER), str(key), str(signature), str(message)],
        env={"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C", **(env or {})},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


@pytest.fixture
def minisign():
    executable = shutil.which("minisign")
    if executable is None:
        pytest.skip("minisign is required for real signature integration tests")
    return executable


@pytest.fixture
def minisign_spy(tmp_path):
    """A successful stub makes both premature invocation and acceptance observable."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "minisign-called"
    executable = bin_dir / "minisign"
    executable.write_text(
        '#!/bin/sh\nprintf "called\\n" > "$MINISIGN_MARKER"\n', encoding="utf-8"
    )
    executable.chmod(0o755)
    return marker, {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "MINISIGN_MARKER": str(marker),
    }


@pytest.fixture
def foreign_release(tmp_path, minisign):
    """Disposable attacker keys; never access the production secret key."""
    key = tmp_path / "attacker.pub"
    secret = tmp_path / "attacker.key"
    message = tmp_path / "SHA256SUMS"
    signature = tmp_path / "SHA256SUMS.minisig"
    message.write_text(f"{'0' * 64}  attacker.deb\n", encoding="utf-8")
    for args in (
        ["-G", "-W", "-p", str(key), "-s", str(secret)],
        ["-S", "-s", str(secret), "-m", str(message), "-x", str(signature)],
        ["-V", "-p", str(key), "-m", str(message), "-x", str(signature)],
    ):
        subprocess.run(
            [minisign, *args], capture_output=True, text=True, check=True, timeout=10
        )
    return key, signature, message


@pytest.mark.parametrize("expected", [None, "", "RWATTACKER", PIN])
def test_real_netmon_release_is_accepted_with_immutable_pin(minisign, expected):
    env = {} if expected is None else {"NETMON_EXPECTED_MINISIGN_PUBKEY": expected}
    result = verify(env=env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Signature and comment signature verified" in result.stdout


@pytest.mark.parametrize(
    "expected", [None, "", "foreign", "canonical", "other-settings"]
)
def test_correctly_signed_foreign_release_is_rejected_before_minisign(
    foreign_release, minisign_spy, expected
):
    key, signature, message = foreign_release
    marker, env = minisign_spy
    if expected == "other-settings":
        # Similarly named and build-only settings must not bypass the pin either.
        env["PINNED_MINISIGN_PUBKEY"] = key.read_text(encoding="utf-8").splitlines()[1]
        env["NETMON_MINISIGN_PUBKEY"] = str(key)
        env["NETMON_ALLOW_UNSIGNED_BUILD"] = "1"
    elif expected is not None:
        env["NETMON_EXPECTED_MINISIGN_PUBKEY"] = {
            "foreign": key.read_text(encoding="utf-8").splitlines()[1],
            "canonical": PIN,
            "": "",
        }[expected]
    result = verify(key, signature, message, env=env)

    assert result.returncode == 1
    assert "NetMon-Pin" in result.stderr
    assert not marker.exists()


@pytest.mark.parametrize(
    "contents",
    [
        b"",
        b"untrusted comment: missing key\n",
        b"untrusted comment: empty key\n\n",
        b"untrusted comment: broken key\nRWbroken\n",
        PIN.encode() + b"\n",
        b"wrong comment\n" + PIN.encode() + b"\n",
        b"untrusted comment: extra key\n" + PIN.encode() + b"\nRWforeign\n",
        b"untrusted comment: extra blank\n" + PIN.encode() + b"\n\n",
        b"untrusted comment: whitespace\n " + PIN.encode() + b"\n",
        b"untrusted comment: whitespace\n" + PIN.encode() + b" \n",
        b"untrusted comment: NUL\n" + PIN[:20].encode() + b"\0" + PIN[20:].encode(),
        b"untrusted comment: binary\n\xff\xfe\n",
    ],
    ids=[
        "empty",
        "comment-only",
        "empty-key",
        "broken-key",
        "missing-comment",
        "invalid-comment",
        "multiple-keys",
        "trailing-blank-line",
        "leading-whitespace",
        "trailing-whitespace",
        "embedded-NUL",
        "binary-key",
    ],
)
def test_corrupted_key_files_are_rejected_before_minisign(
    tmp_path, minisign_spy, contents
):
    key = tmp_path / "damaged.pub"
    key.write_bytes(contents)
    marker, env = minisign_spy
    result = verify(key, env=env)

    assert result.returncode == 1
    assert "Public-Key-Datei" in result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("missing", ["key", "signature", "message"])
def test_missing_inputs_are_rejected_before_minisign(tmp_path, minisign_spy, missing):
    args = {"key": PUBLIC_KEY, "signature": SIGNATURE, "message": MESSAGE}
    args[missing] = tmp_path / "missing"
    marker, env = minisign_spy
    result = verify(**args, env=env)

    assert result.returncode == 1
    assert "Datei nicht gefunden" in result.stderr
    assert not marker.exists()


def test_directory_instead_of_key_is_rejected_before_minisign(tmp_path, minisign_spy):
    marker, env = minisign_spy
    result = verify(tmp_path, env=env)

    assert result.returncode == 1
    assert not marker.exists()


def test_unreadable_key_is_rejected_before_minisign(tmp_path, minisign_spy):
    key = tmp_path / "unreadable.pub"
    key.write_bytes(PUBLIC_KEY.read_bytes())
    marker, env = minisign_spy
    key.chmod(0)
    try:
        if os.access(key, os.R_OK):
            pytest.skip("current user can read files without read permission")
        result = verify(key, env=env)
    finally:
        key.chmod(0o600)

    assert result.returncode == 1
    assert "nicht lesbar" in result.stderr
    assert not marker.exists()


def test_canonical_key_id_in_comment_cannot_authorize_foreign_key(
    foreign_release, minisign_spy
):
    key, signature, message = foreign_release
    foreign_key = key.read_text(encoding="utf-8").splitlines()[1]
    canonical_comment = PUBLIC_KEY.read_text(encoding="utf-8").splitlines()[0]
    key.write_text(f"{canonical_comment}\n{foreign_key}\n", encoding="utf-8")
    marker, env = minisign_spy
    result = verify(key, signature, message, env=env)

    assert result.returncode == 1
    assert not marker.exists()


@pytest.mark.parametrize("damaged", ["message", "signature"])
def test_canonical_key_does_not_accept_tampered_release(tmp_path, minisign, damaged):
    args = {}
    path = tmp_path / damaged
    original = MESSAGE if damaged == "message" else SIGNATURE
    path.write_bytes(
        original.read_bytes() + b"tampered\n" if damaged == "message" else b""
    )
    args[damaged] = path
    result = verify(**args)

    assert result.returncode != 0


def test_foreign_signature_is_rejected_with_canonical_key(foreign_release, minisign):
    _, signature, message = foreign_release
    result = verify(signature=signature, message=message)

    assert result.returncode != 0


def test_distributed_verifier_works_standalone_with_only_offline_tools(
    tmp_path, minisign
):
    """No repo files, HOME, network helpers, or inherited configuration are required."""
    standalone = tmp_path / "standalone release"
    standalone.mkdir()
    for source in (VERIFIER, PUBLIC_KEY, MESSAGE, SIGNATURE):
        shutil.copyfile(source, standalone / source.name)
    bin_dir = tmp_path / "offline-bin"
    bin_dir.mkdir()
    for name, executable in (("awk", shutil.which("awk")), ("minisign", minisign)):
        (bin_dir / name).symlink_to(executable)
    result = subprocess.run(
        [BASH, VERIFIER.name, PUBLIC_KEY.name, SIGNATURE.name, MESSAGE.name],
        cwd=standalone,
        env={"PATH": str(bin_dir), "LC_ALL": "C"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_valid_key_without_minisign_fails_closed(tmp_path):
    bin_dir = tmp_path / "no-minisign"
    bin_dir.mkdir()
    (bin_dir / "awk").symlink_to(shutil.which("awk"))
    result = verify(env={"PATH": str(bin_dir)})

    assert result.returncode == 1
    assert "minisign ist nicht installiert" in result.stderr
