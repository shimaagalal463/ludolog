# FAQ

**Why JSON instead of SQLite?**  
I wanted something I could diff in git, hand-edit in a pinch, and copy to a USB stick. Atomic writes keep it safe enough for a personal journal.

**Can two people edit the same file at once?**  
No — last write wins. Use backups or split collections if you share a household shelf.

**Does ludolog download from BGG automatically?**  
No. Export your collection from BGG or use a CSV you already have; `ludolog import bgg` parses local files only.

**How are wins counted?**  
Each `Play` may set `winner_ids` (list). Co-op wins can mark all seated players or none — your choice at log time. Stats use explicit winner IDs.

**What if my playtime varies?**  
Games store min/max minutes. Slot matching uses the max by default; pass `slack` in `games_for_slot` to allow overrun.

**Python version?**  
3.9+. Tested on 3.12 in CI.

**Where do cover images go?**  
Optional `cover_path` on `Game` — not managed by ludolog beyond storing the path string.
