"""Smoke tests: NBA widget keys and persistence module imports."""

from __future__ import annotations

import py_compile
from pathlib import Path

import nba_persistent_state as nps


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_nba_persistent_state_exports_widget_keys() -> None:
    assert nps.NBA_TEAM_SELECT_KEY == "favorite_team_sidebar"
    assert nps.NBA_PAGE_RADIO_KEY == "nba_choose_page"


def test_streamlit_app_defines_widget_key_fallbacks() -> None:
    source = (REPO_ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    assert 'NBA_TEAM_SELECT_KEY = "favorite_team_sidebar"' in source
    assert 'NBA_PAGE_RADIO_KEY = "nba_choose_page"' in source
    assert "from nba_persistent_state import NBA_PAGE_RADIO_KEY, NBA_TEAM_SELECT_KEY" not in source


def test_py_compile_nba_entrypoints() -> None:
    py_compile.compile(str(REPO_ROOT / "nba_persistent_state.py"), doraise=True)
    py_compile.compile(str(REPO_ROOT / "streamlit_app.py"), doraise=True)
