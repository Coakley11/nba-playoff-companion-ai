"""Portfolio polish — screenshot/demo helpers and demo seed coverage."""

from __future__ import annotations

import portfolio_demo as pdemo
import portfolio_polish as pp
from portfolio_polish import is_capture_mode, show_sidebar_debug, show_trust_strip

_REQUIRED_PORTFOLIO_POLISH_SYMBOLS = frozenset({
    "chart_default_visible",
    "demo_applied",
    "expander_default",
    "feature_expander_default",
    "inject_polish_css",
    "instructional_caption",
    "is_capture_mode",
    "is_demo_mode",
    "is_screenshot_mode",
    "mark_demo_applied",
    "render_executive_summary",
    "render_hero_banner",
    "render_sidebar_toggle",
    "show_sidebar_debug",
    "show_trust_strip",
})


class _FakeSt:
    def __init__(self):
        self.session_state = {}


def test_required_portfolio_polish_symbols_exist():
    missing = [name for name in _REQUIRED_PORTFOLIO_POLISH_SYMBOLS if not hasattr(pp, name)]
    assert not missing, f"portfolio_polish missing: {missing}"
    for name in ("is_capture_mode", "show_trust_strip", "show_sidebar_debug"):
        assert name in pp.__all__


def test_capture_mode_helpers():
    st = _FakeSt()
    st.session_state["portfolio_screenshot_mode"] = True
    assert is_capture_mode(st)
    assert not show_trust_strip(st)
    assert not show_sidebar_debug(st)


def test_demo_mode_is_capture_and_forces_trust_strip_off():
    st = _FakeSt()
    st.session_state["portfolio_demo_mode"] = True
    assert is_capture_mode(st)
    assert not show_trust_strip(st)
    assert show_sidebar_debug(st)


def test_ensure_global_demo_seed():
    st = _FakeSt()
    pdemo.ensure_global_demo_seed(st)
    assert st.session_state["_nba_restore_team"] == pdemo.DEMO_TEAM
    assert st.session_state["legacy_tracker_player"] == pdemo.DEMO_PLAYER
    assert st.session_state["USE_DEMO_BACKUP"] is True
    assert st.session_state["ENABLE_BRACKET_API_REFRESH"] is False
    assert st.session_state["home_dash_live_updates"] is False


def test_load_playoff_demo_marks_home():
    st = _FakeSt()
    pdemo.load_playoff_demo(st)
    assert pp.demo_applied(st, "nba_home")
    assert st.session_state["page_override"] == "🏠 Home Dashboard"


def test_load_legacy_demo_marks_legacy():
    st = _FakeSt()
    st.session_state["portfolio_demo_mode"] = True
    pdemo.load_legacy_demo(st)
    assert pp.demo_applied(st, "nba_legacy")
    assert st.session_state["_nba_restore_team"] == pdemo.DEMO_TEAM
