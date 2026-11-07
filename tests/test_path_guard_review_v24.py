"""Review lifecycle and narrow permission fixes, on private synthetic paths."""

import copy
import grp
import os
import stat
from types import SimpleNamespace

import pytest

from netmon.services import path_guard_review as review
from netmon.services.path_guard_service import PathGuardService


@pytest.fixture
def model(tmp_path, monkeypatch):
    # The sandbox NSS intentionally has only a tiny account inventory. Supply
    # explicit empty root/overflow groups for ancestor metadata if absent.
    real_group = grp.getgrgid

    def group(gid):
        try:
            return real_group(gid)
        except KeyError:
            if gid not in {0, 65534}:
                raise
            return SimpleNamespace(gr_name=f"fixture-{gid}", gr_mem=[])

    monkeypatch.setattr(review.grp, "getgrgid", group)
    target = tmp_path / "bin"
    target.mkdir(mode=0o775)
    target.chmod(0o775)
    paths = ["/usr/bin", "/usr/bin", "/usr/bin", str(target)]
    service = PathGuardService(tmp_path / "private" / "reviews.json")
    service.get_current_path_entries = lambda: list(paths)
    service.get_shell_profile_paths = lambda: []
    return SimpleNamespace(service=service, target=target, paths=paths)


def row_for(model, rule="group_write"):
    return next(
        r for r in model.service.run_check()["review_items"] if r["rule"] == rule
    )


def test_confirmation_is_private_persistent_and_raw_risk_stays_visible(model):
    row = row_for(model)
    assert row["can_accept"] and row["can_repair"]
    before = model.target.stat().st_mode
    model.service.accept_finding(row["id"], row["fingerprint"])
    result = model.service.run_check()
    assert result["risk"] == "mittel" and result["counts"]["medium"] == 1
    assert result["review_summary"] == {
        "high": 0,
        "medium": 0,
        "accepted": 1,
        "error": "",
    }
    assert model.target.stat().st_mode == before
    store = model.service.reviews.path
    assert stat.S_IMODE(store.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.parent.stat().st_mode) == 0o700
    fresh = PathGuardService(store)
    fresh.get_current_path_entries = model.service.get_current_path_entries
    fresh.get_shell_profile_paths = lambda: []
    assert fresh.run_check()["review_summary"]["accepted"] == 1
    fresh.revoke_finding(row["id"])
    assert fresh.run_check()["review_summary"]["medium"] == 1


def test_each_issue_requires_its_own_confirmation(model):
    model.paths[:] = [str(model.target)]
    rows = model.service.run_check()["review_items"]
    assert {r["rule"] for r in rows} == {"group_write", "early_path"}
    model.service.accept_finding(rows[0]["id"], rows[0]["fingerprint"])
    assert model.service.run_check()["review_summary"]["medium"] == 1


@pytest.mark.parametrize(
    "change", ["path_order", "mode", "inode", "parent_mode", "group", "acl"]
)
def test_changed_evidence_invalidates_confirmation(model, monkeypatch, change):
    row = row_for(model)
    model.service.accept_finding(row["id"], row["fingerprint"])
    if change == "path_order":
        model.paths[0] = "/bin"
    elif change == "mode":
        model.target.chmod(0o770)
    elif change == "inode":
        model.target.rename(model.target.with_name("old-bin"))
        model.target.mkdir(mode=0o775)
        model.target.chmod(0o775)
    elif change == "parent_mode":
        model.target.parent.chmod(0o750)
    else:
        original = review.permissions_snapshot

        def changed(path):
            snapshot = copy.deepcopy(original(path))
            if change == "group":
                snapshot[-1]["members"].append("new-member")
            else:
                snapshot[-1]["acl"]["system.posix_acl_access"] = "changed"
            return snapshot

        monkeypatch.setattr(review, "permissions_snapshot", changed)
    result = model.service.run_check()
    assert result["review_summary"]["accepted"] == 0
    assert result["review_summary"]["medium"] >= 1
    with pytest.raises(ValueError, match="verändert"):
        model.service.accept_finding(row["id"], row["fingerprint"])


@pytest.mark.parametrize(
    "kind", ["high", "missing", "symlink", "foreign_owner", "unreadable_acl"]
)
def test_unacceptable_evidence_cannot_be_confirmed_or_repaired(
    model, monkeypatch, kind
):
    if kind == "high":
        model.target.chmod(0o777)
    elif kind == "missing":
        model.paths[3] = str(model.target / "missing")
    elif kind == "symlink":
        link = model.target.with_name("linked-bin")
        link.symlink_to(model.target, target_is_directory=True)
        model.paths[3] = str(link)
    elif kind == "foreign_owner":
        original = review.os.fstat
        ino = model.target.stat().st_ino

        def foreign(fd):
            result = original(fd)
            if result.st_ino == ino:
                values = list(result)
                values[4] = os.geteuid() + 1
                return os.stat_result(values)
            return result

        monkeypatch.setattr(review.os, "fstat", foreign)
    else:
        monkeypatch.setattr(
            review,
            "acl_snapshot",
            lambda _: (_ for _ in ()).throw(PermissionError("ACL unreadable")),
        )
    rows = model.service.run_check()["review_items"]
    assert rows and not any(r["can_accept"] or r["can_repair"] for r in rows)
    for row in rows:
        with pytest.raises(ValueError):
            model.service.accept_finding(row["id"], row["fingerprint"])
    assert not model.service.reviews.path.exists()


def test_repair_removes_only_group_write_from_selected_directory(model):
    nested = model.target / "nested"
    nested.mkdir(mode=0o775)
    nested.chmod(0o775)
    child = model.target / "program"
    child.write_text("synthetic executable")
    child.chmod(0o775)
    parent_mode = model.target.parent.stat().st_mode
    row = row_for(model)
    model.service.repair_finding(row["id"], row["fingerprint"])
    assert stat.S_IMODE(model.target.stat().st_mode) == 0o755
    assert stat.S_IMODE(child.stat().st_mode) == 0o775
    assert stat.S_IMODE(nested.stat().st_mode) == 0o775
    assert model.target.parent.stat().st_mode == parent_mode
    assert model.service.run_check()["review_summary"]["medium"] == 0


def test_acl_prevents_automatic_chmod(model, monkeypatch):
    original = review.acl_snapshot

    def extended(fd):
        value = original(fd)
        if os.fstat(fd).st_ino == model.target.stat().st_ino:
            value["system.posix_acl_access"] = "0102"
        return value

    monkeypatch.setattr(review, "acl_snapshot", extended)
    row = row_for(model)
    assert not row["can_repair"]
    with pytest.raises(ValueError, match="keine sichere"):
        model.service.repair_finding(row["id"], row["fingerprint"])


def test_special_permission_bits_prevent_automatic_chmod(model):
    model.target.chmod(0o2775)
    before = stat.S_IMODE(model.target.stat().st_mode)
    assert before == 0o2775
    row = row_for(model)
    assert not row["can_repair"]
    with pytest.raises(ValueError, match="keine sichere"):
        model.service.repair_finding(row["id"], row["fingerprint"])
    assert stat.S_IMODE(model.target.stat().st_mode) == before


def test_stale_repair_proposal_does_not_change_permissions(model):
    row = row_for(model)
    model.target.chmod(0o770)
    with pytest.raises(ValueError, match="verändert"):
        model.service.repair_finding(row["id"], row["fingerprint"])
    assert stat.S_IMODE(model.target.stat().st_mode) == 0o770


def test_descriptor_repair_does_not_follow_swapped_path(model, monkeypatch):
    row = row_for(model)
    outside = model.target.with_name("outside")
    outside.mkdir(mode=0o775)
    outside.chmod(0o775)
    moved = model.target.with_name("moved")
    real_chmod = os.fchmod

    def swap(fd, mode):
        model.target.rename(moved)
        model.target.symlink_to(outside, target_is_directory=True)
        real_chmod(fd, mode)

    monkeypatch.setattr(review.os, "fchmod", swap)
    model.service.repair_finding(row["id"], row["fingerprint"])
    assert stat.S_IMODE(moved.stat().st_mode) == 0o755
    assert stat.S_IMODE(outside.stat().st_mode) == 0o775


@pytest.mark.parametrize("damage", ["json", "mode", "link", "hardlink", "parent_link"])
def test_invalid_store_never_silently_suppresses_warnings(model, damage):
    row = row_for(model)
    model.service.accept_finding(row["id"], row["fingerprint"])
    path = model.service.reviews.path
    if damage == "json":
        path.write_text("{broken")
    elif damage == "mode":
        path.chmod(0o644)
    elif damage == "link":
        actual = path.with_name("actual")
        path.rename(actual)
        path.symlink_to(actual)
    elif damage == "hardlink":
        os.link(path, path.with_name("second"))
    else:
        actual = path.parent.with_name("actual-directory")
        path.parent.rename(actual)
        path.parent.symlink_to(actual, target_is_directory=True)
    result = model.service.run_check()
    assert result["review_summary"]["error"]
    assert result["review_summary"]["accepted"] == 0
    assert result["review_summary"]["medium"] == 1
    assert not row_for(model)["can_accept"]


def test_retired_finding_can_be_revoked_without_claiming_repair(model):
    row = row_for(model)
    model.service.accept_finding(row["id"], row["fingerprint"])
    model.paths.pop()
    result = model.service.run_check()
    assert result["review_items"][0]["state"] == "nicht mehr gemeldet"
    assert result["review_summary"]["accepted"] == 0
    model.service.revoke_finding(row["id"])
    assert not model.service.reviews.load()


def test_high_finding_cannot_be_suppressed_by_crafted_record(model):
    model.target.chmod(0o777)
    row = model.service.run_check()["review_items"][0]
    model.service.reviews.save(
        {
            row["id"]: {
                "fingerprint": "a" * 64,
                "target": str(model.target),
                "rule": "group_write",
                "time": "fixture",
                "active": True,
            }
        }
    )
    result = model.service.run_check()
    assert result["review_summary"]["high"] > 0
    assert result["review_summary"]["accepted"] == 0


def test_failed_state_save_does_not_report_confirmation(model, monkeypatch):
    row = row_for(model)
    monkeypatch.setattr(
        review.os,
        "replace",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            OSError("synthetic save failure")
        ),
    )
    with pytest.raises(OSError):
        model.service.accept_finding(row["id"], row["fingerprint"])
    assert not model.service.reviews.path.exists()
    assert not list(model.service.reviews.path.parent.glob(".review-*"))
    assert model.service.run_check()["review_summary"]["accepted"] == 0


def test_concurrent_review_writer_is_refused_without_losing_revocations(model):
    row = row_for(model)
    with model.service.reviews.locked():
        with pytest.raises(ValueError, match="andere Bearbeitung"):
            model.service.accept_finding(row["id"], row["fingerprint"])
    assert not model.service.reviews.load()
    model.service.accept_finding(row["id"], row["fingerprint"])
    model.service.revoke_finding(row["id"])
    assert not model.service.reviews.load()


def test_observed_change_does_not_reactivate_old_confirmation_when_restored(model):
    row = row_for(model)
    model.service.accept_finding(row["id"], row["fingerprint"])
    model.target.chmod(0o770)
    assert model.service.run_check()["review_summary"]["accepted"] == 0
    model.target.chmod(0o775)
    assert model.service.run_check()["review_summary"]["accepted"] == 0
    fresh = row_for(model)
    model.service.accept_finding(fresh["id"], fresh["fingerprint"])
    assert model.service.run_check()["review_summary"]["accepted"] == 1


def test_high_shell_profile_risk_stays_open_after_directory_confirmation(model):
    profile = model.target.parent / "bashrc"
    profile.write_text('export PATH="/tmp:$PATH"\n')
    model.service.get_shell_profile_paths = lambda: [str(profile)]
    row = row_for(model)
    model.service.accept_finding(row["id"], row["fingerprint"])
    result = model.service.run_check()
    assert result["review_summary"]["accepted"] == 1
    assert result["review_summary"]["high"] == 1
    profile_row = next(r for r in result["review_items"] if r["target"] == str(profile))
    assert not profile_row["can_accept"] and not profile_row["can_repair"]


def test_failed_repair_readback_reports_partial_change_without_regrant(
    model, monkeypatch
):
    row = row_for(model)
    original_chmod = os.fchmod
    original_stat = os.fstat
    changed_fd = []

    def chmod(fd, mode):
        original_chmod(fd, mode)
        changed_fd.append(fd)

    def fail_after_write(fd):
        if changed_fd and fd == changed_fd[-1]:
            raise OSError("synthetic readback failure after chmod")
        return original_stat(fd)

    monkeypatch.setattr(review.os, "fchmod", chmod)
    monkeypatch.setattr(review.os, "fstat", fail_after_write)
    with pytest.raises(OSError, match="readback failure"):
        model.service.repair_finding(row["id"], row["fingerprint"])
    assert stat.S_IMODE(model.target.stat().st_mode) == 0o755
