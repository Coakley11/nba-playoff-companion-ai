"""Portfolio demo state loaders — NBA playoff companion. Presentation only."""

from __future__ import annotations

import portfolio_polish as pp

DEMO_TEAM = "New York Knicks"
DEMO_PLAYER = "Jalen Brunson"
HOME_DASH_LIVE_KEY = "home_dash_live_updates"

BRUNSON_DEMO_STATS = {
    "GP": 18,
    "PTS": 28.4,
    "REB": 3.2,
    "AST": 6.1,
    "STL": 0.9,
    "BLK": 0.2,
    "TOV": 2.1,
    "FG_PCT": 0.472,
    "FG3_PCT": 0.381,
    "PLUS_MINUS": 4.6,
}


def ensure_global_demo_seed(st) -> None:
    """Stable Knicks Finals scenario — safe before sidebar widgets render."""
    st.session_state["_nba_restore_team"] = DEMO_TEAM
    st.session_state["_nba_persist_team"] = DEMO_TEAM
    st.session_state.setdefault("legacy_tracker_player", DEMO_PLAYER)
    st.session_state["USE_DEMO_BACKUP"] = True
    st.session_state["ENABLE_BRACKET_API_REFRESH"] = False
    st.session_state[HOME_DASH_LIVE_KEY] = False


def load_playoff_demo(st) -> None:
    """Knicks NBA Finals scenario with demo bracket backup (no QA mode)."""
    ensure_global_demo_seed(st)
    st.session_state["page_override"] = "🏠 Home Dashboard"
    pp.mark_demo_applied(st, "nba_home")


def load_legacy_demo(st) -> None:
    ensure_global_demo_seed(st)
    pp.mark_demo_applied(st, "nba_legacy")


def apply_page_demo(st, page: str) -> None:
    if not pp.is_demo_mode(st):
        return
    ensure_global_demo_seed(st)
    if page == "Home Dashboard" and not pp.demo_applied(st, "nba_home"):
        load_playoff_demo(st)
    elif page == "Legacy Tracker" and not pp.demo_applied(st, "nba_legacy"):
        load_legacy_demo(st)


def brunson_demo_stats():
    return dict(BRUNSON_DEMO_STATS)
