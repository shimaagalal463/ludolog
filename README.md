# ludolog

I built **ludolog** because my board game shelf outgrew a spreadsheet — I wanted one place to track what I own, who played what, and which games fit a Tuesday evening.

ludolog is a Python library and CLI for managing a personal board game collection and logging play sessions. It stores everything in a single JSON journal with atomic writes and schema migrations. You can import from BoardGameGeek exports and BG Stats, search by mechanic or player count, and print reports for game nights.

## Quick start

```bash
pip install ludolog
ludolog init ~/ludolog.json
ludolog game add "Wingspan" --players 1-5 --minutes 40-70
ludolog play add --game 1 --players "Alex,Sam" --winner Alex
ludolog report summary
```

See `examples/quick_start.py` for a programmatic tour.

## What it doesn't do

ludolog is not a multiplayer platform, not a replacement for BGG's marketplace or forums, and it does not sync live with online APIs (imports are file-based). It won't teach you rules, calculate complex tie-breakers for every title, or manage trading/shipping. I use it for *my* collection and local stats — if you need cloud sync across devices, you'll want something else (or your own backup script — `ludolog backup` helps).

## Author

Shimaa Galal — [shimaagalal463@gmail.com](mailto:shimaagalal463@gmail.com) — [GitHub](https://github.com/shimaagalal463)

MIT License.
