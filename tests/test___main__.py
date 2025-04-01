"""Tests for ludolog.__main__."""
from __future__ import annotations

from unittest.mock import patch

import ludolog.__main__ as main_module
from ludolog.cli import main as cli_main


def test_main_module_imports_cli_main():
    assert main_module.main is cli_main


def test_main_returns_zero_on_help(capsys):
    assert cli_main([]) == 0
    assert "ludolog" in capsys.readouterr().out


def test_main_init_via_module(tmp_path):
    path = tmp_path / "via_main.json"
    assert cli_main(["init", str(path)]) == 0
    assert path.exists()


def test_main_validate_populated(populated_library, capsys):
    journal = str(populated_library.path)
    assert cli_main(["--journal", journal, "validate"]) == 0
    assert capsys.readouterr().out.strip() == "ok"


def test_main_module_name():
    assert main_module.__name__ == "ludolog.__main__"
