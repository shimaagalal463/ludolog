# Recipes

## Weekly game night report

```bash
ludolog report game-night --days 7 --journal ~/ludolog.json
```

Or run `examples/game_night_report.py` after seeding demo data.

## Find a game for 45 minutes and 4 players

```python
from ludolog.storage import Library
from ludolog.stats import games_for_slot

lib = Library.load("ludolog.json")
candidates = games_for_slot(lib, minutes=45, players=4, slack=15)
for g in candidates[:5]:
    print(g.title, g.playtime_label())
```

## Import BGG then merge duplicates

```bash
ludolog import bgg ~/Downloads/collection.csv
ludolog catalog dedupe --journal ludolog.json
```

## Backup before schema migration

```bash
ludolog backup ~/ludolog.json ~/backups/ --label pre-migrate
ludolog migrate --journal ~/ludolog.json
```

## Serve collection on LAN

```bash
ludolog serve --port 8765 --journal ludolog.json
```

Read-only JSON at `/games`, `/plays`, `/stats/summary`.
