# Architecture

ludolog centers on a **`Library`** dataclass (`storage.py`) — the on-disk JSON journal. Everything else reads or mutates a loaded `Library` and calls `save()` for persistence.

## Layers

1. **Domain models** — `Game`, `Play`, `Player`, `Shelf`, `Venue`, `Goal`, etc. Each exposes `to_dict` / `from_dict`.
2. **Services** — `search`, `stats`, `reports`, `timeline`, `catalog` operate on a library without touching the filesystem.
3. **IO** — `io_csv`, `io_json`, `io_bgg`, `io_bgstats`, `io_excel` import/export external formats.
4. **CLI / server** — `cli.py` wraps argparse commands; `server.py` serves read-only JSON over HTTP.

## Persistence

Writes use temp file + `os.replace` for atomicity. `migrate.py` upgrades schema 0→1→2→3 (players/plays → shelves/venues → recurring nights/goals). On load, migrations run automatically; saving always writes the current schema.

## Extension

`plugins.py` discovers entry points named `ludolog.plugins` for custom report hooks. Validators and parser modules keep CLI input separate from model rules.
