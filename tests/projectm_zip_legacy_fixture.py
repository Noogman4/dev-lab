"""Explicit in-process worker stub for the existing import/rollback regressions.

These tests retain their original injected parser/read failures. Real process
isolation and the unmodified ZIP functions are exercised by separate probes.
"""

from contextlib import contextmanager
from types import SimpleNamespace
import zipfile

from netmon.core import projectm_archive, projectm_zip


def use_legacy_zip_worker(monkeypatch):
    @contextmanager
    def prepared(path):
        with open(path, "rb") as handle:
            size, count = projectm_archive.check_zip_envelope(handle)
            with zipfile.ZipFile(handle, "r") as archive:
                members = projectm_archive.validate_members(archive, size, count)
                yield SimpleNamespace(
                    members=members,
                    copy_member=lambda member, dest, budget: projectm_archive.copy_member(
                        archive, member, dest, budget
                    ),
                )

    monkeypatch.setattr(projectm_zip, "prepared_archive", prepared)
