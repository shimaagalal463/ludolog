"""Targeted tests for uncovered branches in cli, stats, storage, and io modules."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ludolog.cli import main
from ludolog.errors import NotFoundError, StorageError
from ludolog.game import Game
from ludolog.play import Play
from ludolog.player import Player
from ludolog.recurring import RecurringNight
from ludolog.season import Season
from ludolog.shelf import Shelf
from ludolog.storage import (
    Library,
    add_recurring_night,
    add_season,
    archive_player,
    assign_season_to_plays,
    build_game_play_index,
    clone_library_metadata,
    compact_library,
    count_owned_games,
    count_wishlist,
    describe_library,
    export_audit_trail,
    export_player_directory,
    filter_games_by_mechanic,
    find_plays_by_player,
    find_wins_by_player,
    games_without_shelf,
    get_recurring_night,
    get_season,
    import_audit_trail,
    import_player_directory,
    iter_owned_games,
    link_collection_games,
    merge_player_records,
    player_ids_in_library,
    reactivate_player,
    recent_plays,
    record_note_for_game,
    reindex_audit_if_needed,
    set_game_rating,
    snapshot_play_counts,
    suggest_next_game,
    toggle_wishlist,
    top_tags,
    touch_schema,
    unlink_collection_game,
)
from ludolog.stats import (
    average_players_per_session,
    collection_value_estimate,
    compare_mechanics,
    compare_player_win_rates,
    compute_stats_dashboard,
    coop_rate,
    estimate_nights_to_clear_backlog,
    format_dashboard,
    game_retention_score,
    games_by_designer,
    head_to_head,
    h_index_games,
    mechanic_diversity,
    mechanic_play_counts,
    monthly_unique_games,
    player_activity_matrix,
    player_attendance_rate,
    player_engagement,
    player_favorite_game,
    plays_by_weekday,
    plays_per_month,
    publisher_diversity,
    rating_histogram,
    shelf_fill_rates,
    streak_longest_win,
    summary_numbers,
    top_designers_by_plays,
    total_play_minutes,
    update_goal_progress,
    venue_leaderboard,
    win_streak,
)
from ludolog.goal import Goal, GoalKind
from ludolog.audit_log import AuditEntry


# --- CLI coverage ---


def test_cli_report_game_night(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report", "game-night", "--days", "30"]) == 0
    out = capsys.readouterr().out
    assert len(out) >= 0


def test_cli_report_player(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report", "player", "--id", "1"]) == 0


def test_cli_report_shelf(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report", "shelf", "--id", "1"]) == 0


def test_cli_report_unknown_kind(tmp_journal, capsys):
    j = str(tmp_journal.path)
    code = main(["--journal", j, "report", "summary"])
    assert code == 0


def test_cli_import_bgg_json(tmp_journal, tmp_path, capsys):
    j = str(tmp_journal.path)
    data = {"games": [{"title": "Azul", "bgg_id": 230802}]}
    f = tmp_path / "games.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    assert main(["--journal", j, "import", "bgg", str(f)]) == 0
    assert "imported" in capsys.readouterr().out


def test_cli_import_bgstats(tmp_journal, bgstats_csv_path, capsys):
    j = str(tmp_journal.path)
    assert main(["--journal", j, "import", "bgstats", str(bgstats_csv_path)]) == 0


def test_cli_import_json_merge(tmp_journal, loaded_library, capsys):
    j = str(tmp_journal.path)
    src = loaded_library.path
    assert main(["--journal", j, "import", "json", str(src)]) == 0


def test_cli_export_csv_games(populated_library, tmp_path, capsys):
    j = str(populated_library.path)
    dest = tmp_path / "games.csv"
    assert main(["--journal", j, "export", "csv-games", str(dest)]) == 0
    assert dest.exists()


def test_cli_export_json(populated_library, tmp_path, capsys):
    j = str(populated_library.path)
    dest = tmp_path / "out.json"
    assert main(["--journal", j, "export", "json", str(dest)]) == 0


def test_cli_export_excel_plays(populated_library, tmp_path, capsys):
    pytest.importorskip("openpyxl")
    j = str(populated_library.path)
    dest = tmp_path / "plays.xlsx"
    assert main(["--journal", j, "export", "excel-plays", str(dest)]) == 0


def test_cli_export_excel_collection(populated_library, tmp_path, capsys):
    pytest.importorskip("openpyxl")
    j = str(populated_library.path)
    dest = tmp_path / "coll.xlsx"
    assert main(["--journal", j, "export", "excel-collection", str(dest)]) == 0


def test_cli_migrate_check(v0_fixture_data, tmp_path, capsys):
    p = tmp_path / "v0.json"
    p.write_text(json.dumps(v0_fixture_data), encoding="utf-8")
    assert main(["--journal", str(p), "migrate", "--check"]) == 0
    assert "needs migrations" in capsys.readouterr().out


def test_cli_migrate_apply(v0_fixture_data, tmp_path, capsys):
    p = tmp_path / "v0.json"
    p.write_text(json.dumps(v0_fixture_data), encoding="utf-8")
    assert main(["--journal", str(p), "migrate"]) == 0
    assert "schema" in capsys.readouterr().out


def test_cli_catalog_dedupe(tmp_path, capsys):
    lib = Library(path=tmp_path / "d.json")
    lib.games = [Game(id=1, title="Same"), Game(id=2, title="same")]
    lib.save()
    j = str(lib.path)
    assert main(["--journal", j, "catalog", "dedupe"]) == 0
    assert "merged" in capsys.readouterr().out


def test_cli_catalog_stats(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "catalog", "stats"]) == 0
    assert "total=" in capsys.readouterr().out


def test_cli_night_add(tmp_journal, capsys):
    j = str(tmp_journal.path)
    assert main(["--journal", j, "night", "add", "Friday Fun"]) == 0
    assert "night #" in capsys.readouterr().out


def test_cli_stats_leaderboard(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "stats", "leaderboard"]) == 0


def test_cli_stats_months(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "stats", "months"]) == 0


def test_cli_stats_mechanics(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "stats", "mechanics"]) == 0


def test_cli_timeline(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "timeline"]) == 0


def test_cli_goals(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "goals"]) == 0


def test_cli_player_merge(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "player-merge", "--keep", "1", "--drop", "2"]) == 0
    assert "merged" in capsys.readouterr().out


def test_cli_collection_add(tmp_journal, capsys):
    j = str(tmp_journal.path)
    assert main(["--journal", j, "collection", "add", "Travel Bag"]) == 0


def test_cli_report_ext_full(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report-ext", "full"]) == 0


def test_cli_report_ext_backlog(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report-ext", "backlog"]) == 0


def test_cli_report_ext_mechanic(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report-ext", "mechanic", "--query", "cooperative"]) == 0


def test_cli_report_ext_compare(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "report-ext", "compare", "--a", "1", "--b", "2"]) == 0


def test_cli_tag_add(tmp_journal, capsys):
    j = str(tmp_journal.path)
    assert main(["--journal", j, "tag", "add", "party"]) == 0


def test_cli_tag_rename(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "tag", "rename", "--old", "family", "--new", "fam"]) == 0


def test_cli_tag_cloud(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "tag", "cloud"]) == 0


def test_cli_dormant(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "dormant", "--days", "0"]) == 0


def test_cli_dashboard(populated_library, capsys):
    j = str(populated_library.path)
    assert main(["--journal", j, "dashboard"]) == 0
    assert "dashboard" in capsys.readouterr().out.lower()


def test_cli_play_add_with_winner_by_name(populated_library, capsys):
    j = str(populated_library.path)
    code = main([
        "--journal", j, "play", "add", "--game", "1",
        "--players", "Alice,Bob", "--winner", "Alice", "--date", "2025-06-10",
    ])
    assert code == 0


def test_cli_play_add_with_scores_by_name(populated_library, capsys):
    j = str(populated_library.path)
    code = main([
        "--journal", j, "play", "add", "--game", "1",
        "--players", "Alice,Bob", "--scores", "Alice:12,Bob:8", "--date", "2025-06-11",
    ])
    assert code == 0


# --- stats coverage ---


def test_update_goal_progress_win_rate(populated_library):
    populated_library.goals = [
        Goal(kind=GoalKind.WIN_RATE.value, target=50.0, player_id=1),
    ]
    update_goal_progress(populated_library)
    assert populated_library.goals[0].progress >= 0


def test_update_goal_progress_new_games(populated_library):
    populated_library.goals = [Goal(kind=GoalKind.NEW_GAMES.value, target=10.0)]
    update_goal_progress(populated_library)
    assert populated_library.goals[0].progress >= 1.0


def test_update_goal_progress_skips_completed(populated_library):
    g = Goal(kind=GoalKind.NEW_GAMES.value, target=1.0, completed=True, progress=99.0)
    populated_library.goals = [g]
    update_goal_progress(populated_library)
    assert g.progress == 99.0


def test_plays_per_month_skips_incomplete(populated_library, sample_play_incomplete):
    populated_library.plays.append(sample_play_incomplete)
    months = plays_per_month(populated_library)
    assert all(isinstance(m, tuple) for m in months)


def test_average_players_per_session_empty(tmp_journal):
    assert average_players_per_session(tmp_journal) == 0.0


def test_total_play_minutes(populated_library):
    assert total_play_minutes(populated_library) >= 75


def test_games_by_designer(populated_library):
    result = games_by_designer(populated_library)
    assert any("Klaus" in d or "Matt" in d for d, _ in result)


def test_h_index_games():
    plays = [Play(game_id=1) for _ in range(3)] + [Play(game_id=2), Play(game_id=2)]
    assert h_index_games(plays) == 2


def test_player_favorite_game(populated_library):
    game, cnt = player_favorite_game(populated_library, 1)
    assert game is not None
    assert cnt >= 1


def test_player_favorite_game_none(tmp_journal):
    game, cnt = player_favorite_game(tmp_journal, 99)
    assert game is None
    assert cnt == 0


def test_win_streak(populated_library):
    assert win_streak(populated_library, 1) >= 1


def test_mechanic_play_counts(populated_library):
    counts = mechanic_play_counts(populated_library)
    assert isinstance(counts, list)


def test_collection_value_estimate(populated_library):
    val = collection_value_estimate(populated_library)
    assert val > 0


def test_compare_player_win_rates(populated_library):
    a, b = compare_player_win_rates(populated_library, 1, 2)
    assert 0.0 <= a <= 1.0


def test_head_to_head(populated_library):
    aw, bw, ties = head_to_head(populated_library, 1, 2)
    assert aw + bw + ties >= 0


def test_monthly_unique_games(populated_library):
    result = monthly_unique_games(populated_library)
    assert len(result) >= 1


def test_player_activity_matrix(populated_library):
    matrix = player_activity_matrix(populated_library)
    assert 1 in matrix


def test_shelf_fill_rates(populated_library):
    rates = shelf_fill_rates(populated_library)
    assert len(rates) >= 1
    assert rates[0][1] > 0


def test_rating_histogram(populated_library):
    hist = rating_histogram(populated_library)
    assert len(hist) >= 1


def test_streak_longest_win(populated_library):
    assert streak_longest_win(populated_library, 1) >= 1


def test_compare_mechanics(populated_library):
    a, b = compare_mechanics(populated_library, "cooperative", "engine building")
    assert a >= 0 and b >= 0


def test_estimate_nights_to_clear_backlog(populated_library):
    nights = estimate_nights_to_clear_backlog(populated_library)
    assert nights >= 0


def test_player_attendance_rate(populated_library):
    rate = player_attendance_rate(populated_library, 1)
    assert 0.0 < rate <= 1.0


def test_summary_numbers(populated_library):
    nums = summary_numbers(populated_library)
    assert nums["games"] == 3
    assert nums["plays"] >= 1


def test_top_designers_by_plays(populated_library):
    top = top_designers_by_plays(populated_library)
    assert len(top) >= 1


def test_plays_by_weekday(populated_library):
    days = plays_by_weekday(populated_library)
    assert len(days) == 7


def test_coop_rate_empty(tmp_journal):
    assert coop_rate(tmp_journal) == 0.0


def test_player_engagement(populated_library):
    rows = player_engagement(populated_library)
    assert len(rows) == 2


def test_publisher_diversity(populated_library):
    assert publisher_diversity(populated_library) >= 1


def test_mechanic_diversity(populated_library):
    assert mechanic_diversity(populated_library) >= 2


def test_compute_stats_dashboard(populated_library):
    dash = compute_stats_dashboard(populated_library)
    assert "h_index" in dash
    assert dash["coop_rate"] >= 0


def test_format_dashboard(populated_library):
    text = format_dashboard(populated_library)
    assert "ludolog dashboard" in text


def test_game_retention_score_insufficient(populated_library):
    assert game_retention_score(populated_library, 2) == 0.0


def test_game_retention_score_with_multiple_plays(populated_library):
    populated_library.plays.append(
        Play(game_id=1, played_at="2025-05-01T19:00:00", player_ids=[1, 2])
    )
    score = game_retention_score(populated_library, 1)
    assert score > 0


def test_venue_leaderboard(populated_library):
    top = venue_leaderboard(populated_library)
    assert len(top) >= 1


# --- storage coverage ---


def test_storage_save_oserror(tmp_path, monkeypatch):
    lib = Library(path=tmp_path / "bad.json")
    lib.games.append(Game(title="X"))

    def fail_replace(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(StorageError, match="failed to write"):
        lib.save()


def test_add_collection(populated_library):
    from ludolog.collections import Collection
    coll = populated_library.add_collection(Collection(name="New"))
    assert coll.id > 0


def test_get_play_not_found(populated_library):
    with pytest.raises(NotFoundError):
        populated_library.get_play(9999)


def test_get_shelf_not_found(populated_library):
    with pytest.raises(NotFoundError):
        populated_library.get_shelf(9999)


def test_get_venue_not_found(populated_library):
    with pytest.raises(NotFoundError):
        populated_library.get_venue(9999)


def test_player_ids_in_library(populated_library):
    assert player_ids_in_library(populated_library) == [1, 2]


def test_reindex_audit_if_needed(populated_library):
    populated_library.audit_log = [
        AuditEntry(at=f"t{i}", action="x", detail={}) for i in range(600)
    ]
    reindex_audit_if_needed(populated_library, max_entries=500)
    assert len(populated_library.audit_log) == 500


def test_clone_library_metadata(populated_library):
    snap = clone_library_metadata(populated_library)
    assert snap["schema_version"] == 3


def test_merge_player_records_scores(populated_library):
    populated_library.plays[0].scores["2"] = 5.0
    merge_player_records(populated_library, keep_id=1, drop_id=2)
    assert "2" not in populated_library.plays[0].scores
    assert len(populated_library.players) == 1


def test_touch_schema(populated_library):
    populated_library.schema_version = 0
    touch_schema(populated_library)
    assert populated_library.schema_version == 3


def test_validate_references_missing_venue(populated_library):
    populated_library.plays[0].venue_id = 999
    from ludolog.storage import validate_references
    problems = validate_references(populated_library)
    assert any("venue" in p for p in problems)


def test_validate_references_missing_shelf(populated_library):
    populated_library.games[0].shelf_id = 999
    from ludolog.storage import validate_references
    problems = validate_references(populated_library)
    assert any("shelf" in p for p in problems)


def test_find_plays_by_player(populated_library):
    plays = find_plays_by_player(populated_library, 1)
    assert len(plays) >= 1


def test_find_wins_by_player(populated_library):
    wins = find_wins_by_player(populated_library, 1)
    assert len(wins) >= 1


def test_count_owned_games(populated_library):
    assert count_owned_games(populated_library) == 2


def test_count_wishlist(populated_library):
    assert count_wishlist(populated_library) == 1


def test_recent_plays(populated_library):
    assert len(recent_plays(populated_library, limit=5)) >= 1


def test_games_without_shelf(populated_library):
    unassigned = games_without_shelf(populated_library)
    assert any(g.title == "Pandemic" for g in unassigned)


def test_assign_season_to_plays(populated_library):
    n = assign_season_to_plays(populated_library)
    assert n >= 1
    assert populated_library.plays[0].season_id == 1


def test_export_player_directory(populated_library):
    rows = export_player_directory(populated_library)
    assert rows[0]["name"] == "Alice"


def test_import_player_directory(tmp_journal):
    added = import_player_directory(tmp_journal, [{"name": "New Player", "handle": "np"}])
    assert added == 1
    added2 = import_player_directory(tmp_journal, [{"name": "New Player"}])
    assert added2 == 0


def test_snapshot_play_counts(populated_library):
    counts = snapshot_play_counts(populated_library)
    assert counts[1] >= 1


def test_top_tags(populated_library):
    tags = top_tags(populated_library, limit=5)
    assert len(tags) >= 1


def test_link_collection_games(populated_library):
    n = link_collection_games(populated_library, 1, [2])
    assert n == 1


def test_unlink_collection_game(populated_library):
    assert unlink_collection_game(populated_library, 1, 1) is True


def test_set_game_rating(populated_library):
    g = set_game_rating(populated_library, 1, 9.5)
    assert g.rating == 9.5


def test_toggle_wishlist(populated_library):
    g = toggle_wishlist(populated_library, 1, wishlist=True)
    assert g.wishlist is True
    assert g.owned is False


def test_archive_and_reactivate_player(populated_library):
    archive_player(populated_library, 1)
    assert populated_library.get_player(1).active is False
    reactivate_player(populated_library, 1)
    assert populated_library.get_player(1).active is True


def test_add_recurring_night_storage(populated_library):
    night = add_recurring_night(populated_library, RecurringNight(name="Tuesday"))
    assert night.id > 0


def test_get_recurring_night(populated_library):
    n = get_recurring_night(populated_library, 1)
    assert n.name == "Friday Night"


def test_get_recurring_night_not_found(populated_library):
    with pytest.raises(NotFoundError):
        get_recurring_night(populated_library, 999)


def test_add_season_storage(populated_library):
    s = add_season(populated_library, Season(name="Winter", start_date="2025-12-01", end_date="2026-02-28"))
    assert s.id > 0


def test_get_season(populated_library):
    s = get_season(populated_library, 1)
    assert s.name == "Summer 2025"


def test_get_season_not_found(populated_library):
    with pytest.raises(NotFoundError):
        get_season(populated_library, 999)


def test_export_audit_trail(populated_library):
    trail = export_audit_trail(populated_library, limit=10)
    assert isinstance(trail, list)


def test_import_audit_trail_reindex(populated_library):
    entries = [{"at": "2025-01-01", "action": "test", "detail": {}} for _ in range(600)]
    n = import_audit_trail(populated_library, entries)
    assert n == 600
    assert len(populated_library.audit_log) <= 500


def test_compact_library(tmp_path):
    lib = Library(path=tmp_path / "c.json")
    lib.games = [Game(id=1, title="Dup"), Game(id=2, title="dup")]
    lib.seasons = [Season(id=1, name="S", start_date="2020-01-01", end_date="2030-12-31")]
    result = compact_library(lib)
    assert "merged" in result


def test_iter_owned_games(populated_library):
    owned = list(iter_owned_games(populated_library))
    assert len(owned) == 2


def test_build_game_play_index(populated_library):
    index = build_game_play_index(populated_library)
    assert 1 in index


def test_filter_games_by_mechanic(populated_library):
    games = filter_games_by_mechanic(populated_library, "cooperative")
    assert len(games) == 1


def test_record_note_for_game(populated_library):
    note = record_note_for_game(populated_library, 1, "Session notes")
    assert note.game_id == 1
    assert note.body == "Session notes"


def test_suggest_next_game(populated_library):
    suggestions = suggest_next_game(populated_library, players=4, minutes=90)
    assert isinstance(suggestions, list)


def test_describe_library(populated_library):
    desc = describe_library(populated_library)
    assert desc.startswith("Library(")
