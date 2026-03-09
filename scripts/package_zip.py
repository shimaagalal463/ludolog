#!/usr/bin/env python3
"""Package ludolog for submission — keeps .git/ intact (never use Compress-Archive)."""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

PROJECT = "ludolog"
SKIP_DIRS = {
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    ".ruff_cache",
    "build",
    "dist",
    ".history_snapshot",
    ".venv",
}
SKIP_FILES = {".coverage"}


def package(root: Path, out: Path | None = None) -> Path:
    out = out or root.parent / f"{PROJECT}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for r, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info")]
            for f in files:
                if f in SKIP_FILES or f.endswith((".pyc", ".log")):
                    continue
                full = Path(r) / f
                zf.write(full, full.relative_to(root.parent).as_posix())
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = package(root)
    with zipfile.ZipFile(out) as zf:
        ents = zf.namelist()
    for need in (
        f"{PROJECT}/.git/HEAD",
        f"{PROJECT}/.git/refs/heads/main",
        f"{PROJECT}/Dockerfile",
        f"{PROJECT}/README.md",
        f"{PROJECT}/tests/conftest.py",
    ):
        if need not in ents:
            print("MISSING", need, file=sys.stderr)
            return 1
    mb = out.stat().st_size / 1_048_576
    print("OK {} entries, {:.2f} MB -> {}".format(len(ents), mb, out))
    if not 15 <= mb <= 22:
        print("WARN: zip size {:.2f} MB — tune fixture PNG count".format(mb), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
