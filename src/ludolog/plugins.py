"""Plugin hooks for custom report formatters."""
from __future__ import annotations

import importlib.metadata
from typing import Callable, Dict, List, TYPE_CHECKING

from .errors import PluginError

if TYPE_CHECKING:
    from .storage import Library

ReportFn = Callable[["Library"], str]


def discover_plugins() -> Dict[str, ReportFn]:
    found: Dict[str, ReportFn] = {}
    try:
        eps = importlib.metadata.entry_points()
        group = eps.select(group="ludolog.plugins") if hasattr(eps, "select") else eps.get("ludolog.plugins", [])
    except Exception:
        group = []
    for ep in group:
        try:
            fn = ep.load()
            if callable(fn):
                found[ep.name] = fn
        except Exception as exc:
            raise PluginError("failed to load plugin %s" % ep.name) from exc
    return found


def run_plugin(lib: "Library", name: str) -> str:
    plugins = discover_plugins()
    if name not in plugins:
        raise PluginError("unknown plugin: %s" % name)
    return plugins[name](lib)


def list_plugin_names() -> List[str]:
    return sorted(discover_plugins().keys())


def register_builtin(name: str, fn: ReportFn) -> None:
    _BUILTIN[name] = fn


_BUILTIN: Dict[str, ReportFn] = {}


def run_builtin_or_plugin(lib: "Library", name: str) -> str:
    if name in _BUILTIN:
        return _BUILTIN[name](lib)
    return run_plugin(lib, name)

# TODO: plugin config in journal metadata


def summary_plugin(lib) -> str:
    from .reports import summary_report
    return summary_report(lib)


register_builtin("summary", summary_plugin)


def goals_plugin(lib) -> str:
    from .reports import goals_report
    return goals_report(lib)


register_builtin("goals", goals_plugin)
