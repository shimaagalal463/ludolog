"""Tests for ludolog.backup."""
import json

import pytest

from ludolog.backup import (
    backup_filename,
    backup_size,
    create_backup,
    export_snapshot,
    latest_backup,
    list_backups,
    restore_backup,
    rotate_backups,
    verify_backup,
)
from ludolog.errors import StorageError
from ludolog.storage import Library


def test_backup_filename_includes_label_and_timestamp():
    name = backup_filename("manual save")
    assert name.startswith("ludolog-manual_save-")
    assert name.endswith(".json")


def test_backup_filename_default_label():
    name = backup_filename()
    assert name.startswith("ludolog-backup-")


def test_create_backup_copies_journal(tmp_journal, tmp_path):
    tmp_journal.save()
    backup_dir = tmp_path / "backups"
    out = create_backup(tmp_journal.path, backup_dir, label="daily")
    assert out.exists()
    assert out.read_text(encoding="utf-8") == tmp_journal.path.read_text(encoding="utf-8")


def test_create_backup_missing_source_raises(tmp_path):
    with pytest.raises(StorageError, match="missing journal"):
        create_backup(tmp_path / "missing.json", tmp_path)


def test_export_snapshot_writes_library_dict(populated_library, tmp_path):
    dest = tmp_path / "snap" / "export.json"
    export_snapshot(populated_library, dest)
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["schema_version"] == populated_library.to_dict()["schema_version"]
    assert len(data["games"]) == 3


def test_restore_backup_replaces_target_and_loads(populated_library, tmp_path):
    populated_library.save()
    backup = create_backup(populated_library.path, tmp_path, label="restore")
    target = tmp_path / "restored.json"
    lib = restore_backup(backup, target)
    assert target.exists()
    assert len(lib.games) == 3


def test_restore_backup_missing_raises(tmp_path):
    with pytest.raises(StorageError, match="backup missing"):
        restore_backup(tmp_path / "nope.json", tmp_path / "out.json")


def test_list_backups_sorted_newest_first(tmp_path):
    older = tmp_path / "ludolog-a-20250101-100000.json"
    newer = tmp_path / "ludolog-b-20250201-100000.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")
    backups = list_backups(tmp_path)
    assert backups[0] == newer
    assert backups[1] == older


def test_list_backups_empty_for_missing_dir(tmp_path):
    assert list_backups(tmp_path / "not-a-dir") == []


def test_rotate_backups_removes_oldest(tmp_path):
    files = []
    for i in range(7):
        p = tmp_path / f"ludolog-x-2025010{i}-120000.json"
        p.write_text("{}", encoding="utf-8")
        files.append(p)
    removed = rotate_backups(tmp_path, keep=3)
    assert removed == 4
    remaining = list_backups(tmp_path)
    assert len(remaining) == 3


def test_backup_size_bytes(tmp_path):
    p = tmp_path / "ludolog-test.json"
    p.write_text('{"ok": true}', encoding="utf-8")
    assert backup_size(p) > 0


def test_backup_size_missing_is_zero(tmp_path):
    assert backup_size(tmp_path / "missing.json") == 0


def test_verify_backup_valid_json(tmp_journal, tmp_path):
    tmp_journal.save()
    backup = create_backup(tmp_journal.path, tmp_path)
    assert verify_backup(backup, tmp_journal.path) is True


def test_verify_backup_invalid_json(tmp_journal, tmp_path):
    tmp_journal.save()
    bad = tmp_path / "ludolog-bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert verify_backup(bad, tmp_journal.path) is False


def test_latest_backup_returns_newest(tmp_path):
    older = tmp_path / "ludolog-x-20250101-100000.json"
    newer = tmp_path / "ludolog-x-20250201-100000.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")
    assert latest_backup(tmp_path) == newer


def test_latest_backup_none_when_empty(tmp_path):
    assert latest_backup(tmp_path) is None


def test_create_backup_creates_dest_directory(tmp_journal, tmp_path):
    tmp_journal.save()
    dest_dir = tmp_path / "nested" / "backups"
    out = create_backup(tmp_journal.path, dest_dir)
    assert dest_dir.is_dir()
    assert out.parent == dest_dir


def test_export_snapshot_creates_parent_dirs(populated_library, tmp_path):
    dest = tmp_path / "deep" / "snap.json"
    export_snapshot(populated_library, dest)
    assert dest.exists()
