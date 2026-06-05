"""Verify every pdemo.<name> used in streamlit_app.py exists on portfolio_demo."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import portfolio_demo as pdemo

_REPO_ROOT = Path(__file__).resolve().parents[1]
_STREAMLIT_APP = _REPO_ROOT / "streamlit_app.py"


def _pdemo_refs_in_streamlit_app() -> set[str]:
    text = _STREAMLIT_APP.read_text(encoding="utf-8")
    return set(re.findall(r"\bpdemo\.(\w+)", text))


def test_streamlit_app_pdemo_refs_resolve():
    refs = _pdemo_refs_in_streamlit_app()
    assert refs, "expected at least one pdemo.<name> reference in streamlit_app.py"
    missing = sorted(name for name in refs if not hasattr(pdemo, name))
    assert not missing, f"portfolio_demo missing symbols referenced by streamlit_app.py: {missing}"


def test_pdemo_exports_in_all():
    refs = _pdemo_refs_in_streamlit_app()
    public = {name for name in refs if not name.startswith("_")}
    not_exported = sorted(name for name in public if name not in pdemo.__all__)
    assert not not_exported, f"portfolio_demo.__all__ missing: {not_exported}"


def test_portfolio_demo_reload_keeps_symbols():
    reloaded = importlib.reload(pdemo)
    for name in _pdemo_refs_in_streamlit_app():
        assert hasattr(reloaded, name), f"reload lost portfolio_demo.{name}"


def test_demo_and_screenshot_startup_seed():
    """Simulate main() demo path: both toggles on, seed + page loaders run."""
    class _FakeSt:
        def __init__(self):
            self.session_state = {
                "portfolio_demo_mode": True,
                "portfolio_screenshot_mode": True,
            }

    st = _FakeSt()
    pdemo.ensure_global_demo_seed(st)
    pdemo.apply_page_demo(st, "Home Dashboard")
    pdemo.apply_page_demo(st, "Legacy Tracker")
    assert st.session_state["_nba_restore_team"] == pdemo.DEMO_TEAM
    assert st.session_state["legacy_tracker_player"] == pdemo.DEMO_PLAYER
    assert st.session_state["USE_DEMO_BACKUP"] is True
