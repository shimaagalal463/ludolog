"""Tests for ludolog.plugins."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ludolog.errors import PluginError
from ludolog.plugins import (
    _BUILTIN,
    discover_plugins,
    goals_plugin,
    list_plugin_names,
    register_builtin,
    run_builtin_or_plugin,
    run_plugin,
    summary_plugin,
)


def test_list_plugin_names_returns_sorted_discovered():
    names = list_plugin_names()
    assert names == sorted(names)
    assert isinstance(names, list)


def test_builtin_plugins_registered():
    assert "summary" in _BUILTIN
    assert "goals" in _BUILTIN


def test_run_builtin_summary(populated_library):
    text = run_builtin_or_plugin(populated_library, "summary")
    assert "Catan" in text or "game" in text.lower()


def test_run_builtin_goals(populated_library):
    text = run_builtin_or_plugin(populated_library, "goals")
    assert "Play Catan 5x" in text or "goal" in text.lower()


def test_register_builtin_custom(populated_library):
    register_builtin("custom", lambda lib: f"games={len(lib.games)}")
    assert run_builtin_or_plugin(populated_library, "custom") == "games=3"
    del _BUILTIN["custom"]


def test_run_plugin_unknown_raises(populated_library):
    with pytest.raises(PluginError, match="unknown plugin"):
        run_plugin(populated_library, "nonexistent-plugin-xyz")


def test_discover_plugins_returns_dict():
    plugins = discover_plugins()
    assert isinstance(plugins, dict)


def test_summary_plugin_matches_report(populated_library):
    from ludolog.reports import summary_report

    assert summary_plugin(populated_library) == summary_report(populated_library)


def test_goals_plugin_matches_report(populated_library):
    from ludolog.reports import goals_report

    assert goals_plugin(populated_library) == goals_report(populated_library)


def test_discover_plugins_loads_entry_point():
    mock_ep = MagicMock()
    mock_ep.name = "demo"
    mock_ep.load.return_value = lambda lib: "ok"

    mock_eps = MagicMock()
    mock_eps.select.return_value = [mock_ep]

    with patch("ludolog.plugins.importlib.metadata.entry_points", return_value=mock_eps):
        found = discover_plugins()
    assert found["demo"](None) == "ok"


def test_run_plugin_uses_discovered_entry_point(populated_library):
    fn = lambda lib: f"plays={len(lib.plays)}"
    mock_ep = MagicMock()
    mock_ep.name = "counter"
    mock_ep.load.return_value = fn
    mock_eps = MagicMock()
    mock_eps.select.return_value = [mock_ep]

    with patch("ludolog.plugins.importlib.metadata.entry_points", return_value=mock_eps):
        assert run_plugin(populated_library, "counter") == "plays=1"


def test_discover_plugins_load_failure_raises():
    mock_ep = MagicMock()
    mock_ep.name = "broken"
    mock_ep.load.side_effect = RuntimeError("boom")
    mock_eps = MagicMock()
    mock_eps.select.return_value = [mock_ep]

    with patch("ludolog.plugins.importlib.metadata.entry_points", return_value=mock_eps):
        with pytest.raises(PluginError, match="failed to load plugin broken"):
            discover_plugins()


def test_discover_plugins_skips_non_callable():
    mock_ep = MagicMock()
    mock_ep.name = "bad"
    mock_ep.load.return_value = "not-callable"
    mock_eps = MagicMock()
    mock_eps.select.return_value = [mock_ep]

    with patch("ludolog.plugins.importlib.metadata.entry_points", return_value=mock_eps):
        found = discover_plugins()
    assert "bad" not in found
