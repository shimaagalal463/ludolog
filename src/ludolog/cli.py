"""ludolog CLI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .backup import create_backup
from .catalog import catalog_stats, dedupe_by_title
from .game import Game
from .io_bgg import import_bgg_csv, import_bgg_json
from .io_bgstats import import_bgstats_csv
from .io_csv import export_games_csv, export_plays_csv, import_plays_csv
from .io_excel import export_collection_excel, export_plays_excel
from .io_json import export_library_json, merge_json_into
from .migrate import CURRENT_SCHEMA, migration_plan
from .parser import parse_game_fields, parse_tags, split_names
from .play import Play
from .player import Player
from .recurring import RecurringNight
from .reports import game_night_report, player_report, shelf_report, summary_report
from .search import search_all
from .season import Season
from .shelf import Shelf
from .stats import games_for_slot, update_goal_progress
from .storage import Library, init_library
from .venue import Venue


# TODO: config file for default journal path instead of env var only


def _default_journal() -> Path:
    return Path.home() / "ludolog.json"


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    init_library(path)
    print("initialized %s (schema %d)" % (path, CURRENT_SCHEMA))
    return 0


def cmd_game_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    title, pr, pt, mech = parse_game_fields(args.title, args.players or "", args.minutes or "", args.mechanics or "")
    game = Game(title=title, player_range=pr, playtime=pt, mechanics=mech, designer=args.designer or "")
    if args.bgg:
        game.bgg_id = int(args.bgg)
    lib.add_game(game)
    lib.save()
    print("game #%d %s" % (game.id, game.title))
    return 0


def cmd_play_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    names = split_names(args.players or "")
    pids = []
    for name in names:
        from .player import find_player_by_name

        pl = find_player_by_name(lib.players, name)
        if not pl:
            pl = lib.add_player(Player(name=name))
        pids.append(pl.id)
    wids = []
    if args.winner:
        for w in split_names(args.winner):
            from .player import find_player_by_name

            pl = find_player_by_name(lib.players, w)
            if pl:
                wids.append(pl.id)
    played_at = args.at or (args.date + "T20:00:00" if args.date else "")
    play = Play(
        game_id=int(args.game),
        played_at=played_at,
        player_ids=pids,
        winner_ids=wids,
        duration_minutes=int(args.duration) if args.duration else None,
        notes=args.notes or "",
    )
    if args.scores:
        from .parser import parse_score_pairs

        for k, v in parse_score_pairs(args.scores).items():
            try:
                pid = int(k)
            except ValueError:
                from .player import find_player_by_name

                pl = find_player_by_name(lib.players, k)
                pid = pl.id if pl else 0
            if pid:
                play.set_score(pid, v)
        if not wids:
            play.infer_winners_from_scores()
    lib.add_play(play)
    update_goal_progress(lib)
    lib.save()
    print("play #%d" % play.id)
    return 0


def cmd_player_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    pl = lib.add_player(Player(name=args.name, handle=args.handle or ""))
    lib.save()
    print("player #%d" % pl.id)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    if args.kind == "summary":
        print(summary_report(lib))
    elif args.kind == "game-night":
        print(game_night_report(lib, days=args.days))
    elif args.kind == "player":
        print(player_report(lib, args.id))
    elif args.kind == "shelf":
        print(shelf_report(lib, args.id))
    else:
        print("unknown report kind", file=sys.stderr)
        return 1
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    for hit in search_all(lib, args.query, limit=args.limit):
        print("%.0f\t%s\t%s\t%d" % (hit.score, hit.kind, hit.label, hit.ref_id))
    return 0


def cmd_slot(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    for g in games_for_slot(lib, minutes=args.minutes, players=args.players, slack=args.slack):
        print("%s — %s, %s" % (g.title, g.player_label(), g.playtime_label()))
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    path = Path(args.file)
    fmt = args.format
    if fmt == "csv":
        n = import_plays_csv(lib, path)
    elif fmt == "bgg":
        n = import_bgg_csv(lib, path) if path.suffix.lower() == ".csv" else import_bgg_json(lib, path)
    elif fmt == "bgstats":
        n = import_bgstats_csv(lib, path)
    elif fmt == "json":
        n = merge_json_into(lib, path)
    else:
        print("unknown format", file=sys.stderr)
        return 1
    update_goal_progress(lib)
    lib.save()
    print("imported %d records" % n)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    dest = Path(args.dest)
    if args.format == "csv-plays":
        n = export_plays_csv(lib, dest)
    elif args.format == "csv-games":
        n = export_games_csv(lib, dest)
    elif args.format == "json":
        export_library_json(lib, dest)
        n = len(lib.games)
    elif args.format == "excel-plays":
        n = export_plays_excel(lib, dest)
    elif args.format == "excel-collection":
        n = export_collection_excel(lib, dest)
    else:
        print("unknown format", file=sys.stderr)
        return 1
    print("exported %d rows -> %s" % (n, dest))
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    out = create_backup(args.journal, args.dest, label=args.label or "")
    print("backup -> %s" % out)
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    raw = __import__("json").loads(Path(args.journal).read_text(encoding="utf-8"))
    if args.check:
        print("needs migrations from: %s" % migration_plan(raw))
        return 0
    lib = Library.load(args.journal)
    lib.save()
    print("at schema %d" % lib.schema_version)
    return 0


def cmd_catalog(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    if args.action == "dedupe":
        n = dedupe_by_title(lib)
        lib.save()
        print("merged %d duplicates" % n)
    elif args.action == "stats":
        total, owned, wish = catalog_stats(lib)
        print(f"total={total} owned={owned} wishlist={wish}")
    return 0


def cmd_shelf_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    shelf = lib.add_shelf(Shelf(name=args.name, location=args.location or "", capacity=args.capacity))
    lib.save()
    print("shelf #%d" % shelf.id)
    return 0


def cmd_venue_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    venue = lib.add_venue(Venue(name=args.name, address=args.address or "", default_for_nights=args.default))
    lib.save()
    print("venue #%d" % venue.id)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve_library

    lib = Library.load(args.journal)
    print("serving %s on %s:%d" % (args.journal, args.host, args.port))
    serve_library(lib, host=args.host, port=args.port)
    return 0


def cmd_night_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    night = RecurringNight(name=args.name, weekday=args.weekday or "fri", start_time=args.time or "19:00")
    night.id = max((n.id for n in lib.recurring_nights), default=0) + 1
    lib.recurring_nights.append(night)
    lib.save()
    print("night #%d" % night.id)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .storage import validate_references
    problems = validate_references(lib)
    if problems:
        for msg in problems:
            print(msg, file=sys.stderr)
        return 1
    print("ok")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .stats import (
        average_players_per_session,
        h_index_games,
        leaderboard,
        mechanic_play_counts,
        plays_per_month,
        total_play_minutes,
    )
    if args.kind == "leaderboard":
        for name, wins, played in leaderboard(lib, args.top):
            print("%s\tw%d\tp%d" % (name, wins, played))
    elif args.kind == "months":
        for month, cnt in plays_per_month(lib):
            print("%s\t%d" % (month, cnt))
    elif args.kind == "mechanics":
        for mech, cnt in mechanic_play_counts(lib)[: args.top]:
            print("%s\t%d" % (mech, cnt))
    else:
        print("avg players/session: %.2f" % average_players_per_session(lib))
        print("total minutes logged: %d" % total_play_minutes(lib))
        print("h-index games: %d" % h_index_games(lib.plays))
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .timeline import build_timeline
    for ev in build_timeline(lib, limit=args.limit):
        print("%s\t%s\t%s" % (ev.when, ev.kind, ev.summary))
    return 0


def cmd_goals(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .reports import goals_report
    print(goals_report(lib))
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .storage import compute_library_health
    for k, v in compute_library_health(lib).items():
        print("%s: %s" % (k, v))
    return 0


def cmd_player_merge(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .storage import merge_player_records
    merge_player_records(lib, args.keep, args.drop)
    lib.save()
    print("merged %d into %d" % (args.drop, args.keep))
    return 0


def cmd_collection_add(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .collections import Collection
    coll = lib.add_collection(Collection(name=args.name, description=args.description or ""))
    lib.save()
    print("collection #%d" % coll.id)
    return 0


def cmd_report_extended(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .reports import backlog_report, compare_players_report, full_report, mechanic_report
    if args.kind == "full":
        print(full_report(lib))
    elif args.kind == "backlog":
        print(backlog_report(lib))
    elif args.kind == "mechanic":
        print(mechanic_report(lib, args.query))
    elif args.kind == "compare":
        print(compare_players_report(lib, args.a, args.b))
    else:
        print("unknown", file=sys.stderr)
        return 1
    return 0


def cmd_tag(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .tags_manager import add_global_tag, rename_tag, tag_cloud
    if args.action == "add":
        add_global_tag(lib, args.name)
    elif args.action == "rename":
        rename_tag(lib, args.old, args.new)
    elif args.action == "cloud":
        for tag, cnt in tag_cloud(lib)[: args.top]:
            print("%s\t%d" % (tag, cnt))
    lib.save()
    return 0


def cmd_dormant(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .stats import dormant_games
    for g in dormant_games(lib, days=args.days):
        print(g.title)
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    lib = Library.load(args.journal)
    from .stats import format_dashboard
    print(format_dashboard(lib))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ludolog", description="Board game collection and play tracker")
    p.add_argument("--journal", "-j", default=str(_default_journal()))
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("init", help="create empty journal")
    s.add_argument("path")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("game")
    gsub = s.add_subparsers(dest="game_cmd")
    ga = gsub.add_parser("add")
    ga.add_argument("title")
    ga.add_argument("--players", "-p")
    ga.add_argument("--minutes", "-m")
    ga.add_argument("--mechanics")
    ga.add_argument("--designer")
    ga.add_argument("--bgg", type=int)
    ga.set_defaults(func=cmd_game_add)

    s = sub.add_parser("play")
    psub = s.add_subparsers(dest="play_cmd")
    pa = psub.add_parser("add")
    pa.add_argument("--game", type=int, required=True)
    pa.add_argument("--players")
    pa.add_argument("--winner")
    pa.add_argument("--date")
    pa.add_argument("--at")
    pa.add_argument("--duration", type=int)
    pa.add_argument("--scores")
    pa.add_argument("--notes")
    pa.set_defaults(func=cmd_play_add)

    s = sub.add_parser("player")
    psub = s.add_subparsers(dest="player_cmd")
    pa = psub.add_parser("add")
    pa.add_argument("name")
    pa.add_argument("--handle")
    pa.set_defaults(func=cmd_player_add)

    s = sub.add_parser("report")
    s.add_argument("kind", choices=["summary", "game-night", "player", "shelf"])
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--id", type=int, default=1)
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("slot")
    s.add_argument("--minutes", type=int, required=True)
    s.add_argument("--players", type=int, required=True)
    s.add_argument("--slack", type=int, default=0)
    s.set_defaults(func=cmd_slot)

    s = sub.add_parser("import")
    s.add_argument("format", choices=["csv", "bgg", "bgstats", "json"])
    s.add_argument("file")
    s.set_defaults(func=cmd_import)

    s = sub.add_parser("export")
    s.add_argument("format", choices=["csv-plays", "csv-games", "json", "excel-plays", "excel-collection"])
    s.add_argument("dest")
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("backup")
    s.add_argument("dest")
    s.add_argument("--label")
    s.set_defaults(func=cmd_backup)

    s = sub.add_parser("migrate")
    s.add_argument("--check", action="store_true")
    s.set_defaults(func=cmd_migrate)

    s = sub.add_parser("catalog")
    s.add_argument("action", choices=["dedupe", "stats"])
    s.set_defaults(func=cmd_catalog)

    s = sub.add_parser("shelf")
    ssub = s.add_subparsers(dest="shelf_cmd")
    sa = ssub.add_parser("add")
    sa.add_argument("name")
    sa.add_argument("--location")
    sa.add_argument("--capacity", type=int)
    sa.set_defaults(func=cmd_shelf_add)

    s = sub.add_parser("venue")
    vsub = s.add_subparsers(dest="venue_cmd")
    va = vsub.add_parser("add")
    va.add_argument("name")
    va.add_argument("--address")
    va.add_argument("--default", action="store_true")
    va.set_defaults(func=cmd_venue_add)

    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("night")
    nsub = s.add_subparsers(dest="night_cmd")
    na = nsub.add_parser("add")
    na.add_argument("name")
    na.add_argument("--weekday", default="fri")
    na.add_argument("--time", default="19:00")
    na.set_defaults(func=cmd_night_add)


    s = sub.add_parser("validate")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("stats")
    s.add_argument("kind", choices=["summary", "leaderboard", "months", "mechanics"], default="summary", nargs="?")
    s.add_argument("--top", type=int, default=10)
    s.set_defaults(func=cmd_stats)

    s = sub.add_parser("timeline")
    s.add_argument("--limit", type=int, default=30)
    s.set_defaults(func=cmd_timeline)

    s = sub.add_parser("goals")
    s.set_defaults(func=cmd_goals)

    s = sub.add_parser("health")
    s.set_defaults(func=cmd_health)

    s = sub.add_parser("player-merge")
    s.add_argument("--keep", type=int, required=True)
    s.add_argument("--drop", type=int, required=True)
    s.set_defaults(func=cmd_player_merge)

    s = sub.add_parser("collection")
    csub = s.add_subparsers(dest="collection_cmd")
    ca = csub.add_parser("add")
    ca.add_argument("name")
    ca.add_argument("--description")
    ca.set_defaults(func=cmd_collection_add)

    s = sub.add_parser("dormant")
    s.add_argument("--days", type=int, default=90)
    s.set_defaults(func=cmd_dormant)

    s = sub.add_parser("tag")
    s.add_argument("action", choices=["add", "rename", "cloud"])
    s.add_argument("name", nargs="?")
    s.add_argument("--old")
    s.add_argument("--new")
    s.add_argument("--top", type=int, default=20)
    s.set_defaults(func=cmd_tag)

    s = sub.add_parser("report-ext")
    s.add_argument("kind", choices=["full", "backlog", "mechanic", "compare"])
    s.add_argument("--query", default="")
    s.add_argument("--a", type=int, default=1)
    s.add_argument("--b", type=int, default=2)
    s.set_defaults(func=cmd_report_extended)

    s = sub.add_parser("dashboard")
    s.set_defaults(func=cmd_dashboard)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
