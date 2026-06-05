"""Portfolio demo state loaders — NBA playoff companion. Presentation only."""

from __future__ import annotations

import portfolio_polish as pp

DEMO_TEAM = "New York Knicks"
DEMO_PLAYER = "Jalen Brunson"

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


def load_playoff_demo(st) -> None:
    """Knicks NBA Finals scenario with demo bracket backup (no QA mode)."""
    st.session_state["_nba_persist_team"] = DEMO_TEAM
    st.session_state["legacy_tracker_player"] = DEMO_PLAYER
    st.session_state["page_override"] = "🏠 Home Dashboard"
    pp.mark_demo_applied(st, "nba_home")


def load_legacy_demo(st) -> None:
    st.session_state["legacy_tracker_player"] = DEMO_PLAYER
    pp.mark_demo_applied(st, "nba_legacy")


def apply_page_demo(st, page: str) -> None:
    if not pp.is_demo_mode(st):
        return
    if page == "Home Dashboard" and not pp.demo_applied(st, "nba_home"):
        load_playoff_demo(st)
    elif page == "Legacy Tracker" and not pp.demo_applied(st, "nba_legacy"):
        load_legacy_demo(st)


def brunson_demo_stats():
    return dict(BRUNSON_DEMO_STATS)
