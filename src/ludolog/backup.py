"""Backup copies of the JSON journal."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .errors import StorageError
from .storage import Library


def backup_filename(label: str = "") -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = label.replace(" ", "_")[:32] if label else "backup"
    return f"ludolog-{safe}-{stamp}.json"


def create_backup(source: Path | str, dest_dir: Path | str, label: str = "") -> Path:
    src = Path(source)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise StorageError("missing journal: %s" % src)
    out = dest / backup_filename(label)
    shutil.copy2(src, out)
    return out


def export_snapshot(lib: Library, dest: Path | str) -> None:
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(lib.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def restore_backup(backup_path: Path | str, target: Path | str) -> Library:
    bp = Path(backup_path)
    if not bp.exists():
        raise StorageError("backup missing")
    tgt = Path(target)
    shutil.copy2(bp, tgt)
    return Library.load(tgt)


def list_backups(directory: Path | str) -> list[Path]:
    d = Path(directory)
    if not d.is_dir():
        return []
    return sorted(d.glob("ludolog-*.json"), reverse=True)


def rotate_backups(directory: Path | str, keep: int = 5) -> int:
    files = list_backups(directory)
    removed = 0
    for old in files[keep:]:
        old.unlink(missing_ok=True)
        removed += 1
    return removed


def backup_size(path: Path | str) -> int:
    p = Path(path)
    return p.stat().st_size if p.exists() else 0


def verify_backup(backup_path, journal_path) -> bool:
    import json
    try:
        json.loads(Path(backup_path).read_text(encoding="utf-8"))
        json.loads(Path(journal_path).read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def latest_backup(directory) -> Path | None:
    files = list_backups(directory)
    return files[0] if files else None

# TODO: optional gzip compression for backups
