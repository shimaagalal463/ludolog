# File formats

## ludolog JSON journal

Default filename is `ludolog.json`. Top-level keys:

| Key | Description |
|-----|-------------|
| `schema_version` | Integer, currently `3` |
| `games` | Collection entries with title, BGG id, player range, playtime |
| `plays` | Session logs with date, scores, venue, duration |
| `players` | People you track wins/attendance for |
| `shelves`, `venues`, `goals`, `notes`, `seasons`, `recurring_nights` | Organization and planning |
| `tags`, `collections`, `audit_log` | Tags, curated lists, change history |

Dates are ISO-8601 strings. IDs are integers assigned by the library.

## Imports

- **BGG** — collection CSV or simplified JSON export (`io_bgg`)
- **BG Stats** — plays CSV export (`io_bgstats`)
- **CSV** — ludolog-native play/game rows (`io_csv`)

## Exports

CSV and Excel (`io_excel`) for plays and collection snapshots. `io_json` dumps a portable subset for sharing.
