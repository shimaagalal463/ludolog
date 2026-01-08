#!/usr/bin/env python3
"""Print a game-night report from a journal path."""
from __future__ import annotations

import sys
from pathlib import Path

from ludolog.reports import game_night_report
from ludolog.storage import Library


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "ludolog.json"
    if not path.exists():
        print(f"missing journal: {path}", file=sys.stderr)
        raise SystemExit(1)
    lib = Library.load(path)
    print(game_night_report(lib, days=14))


if __name__ == "__main__":
    main()
