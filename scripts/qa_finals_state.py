"""NBA Finals state audit — active Knicks/Spurs only; bracket agrees. No network.

Note: imports full streamlit_app (slow on cold start). For fast CI use validate_stability_phase.py.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_st = MagicMock()
_st.cache_data = lambda **kwargs: (lambda fn: fn)
_st.session_state = {}
_st.sidebar = MagicMock()
sys.modules["streamlit"] = _st
sys.modules["streamlit_autorefresh"] = MagicMock(st_autorefresh=MagicMock())

import streamlit_app as app  # noqa: E402

ACTIVE = ("New York Knicks", "San Antonio Spurs")
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL: {msg}")


def main() -> int:
    stt = app.get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)
    finals = (stt.get("finals") or {})
    if not finals:
        fail("no finals bracket in playoff state")
    else:
        row = next(iter(finals.values()), {})
        a, b = row.get("a"), row.get("b")
        if set([a, b]) != set(ACTIVE):
            fail(f"finals matchup expected Knicks vs Spurs, got {a} vs {b}")

    for team in app.TEAM_PROFILES:
        pst = app.get_team_playoff_status(team, stt)
        prof = app.TEAM_PROFILES[team]
        status = pst.get("status")
        is_active = team in ACTIVE
        if is_active:
            if status != "active":
                fail(f"{team} should be active, got {status}")
            opp = pst.get("current_opponent")
            if opp not in ACTIVE:
                fail(f"{team} opponent should be Finals rival, got {opp}")
            if app._is_home_eliminated(team):
                fail(f"{team} must not be home-eliminated")
        else:
            if status == "active":
                fail(f"{team} should not be active")
            if not app._is_home_eliminated(team):
                fail(f"{team} should be eliminated on Home")

    for team in ACTIVE:
        dm = app.get_display_matchup(team, stt)
        if "Final" not in str(dm.get("round_short") or dm.get("round") or ""):
            fail(f"{team} display matchup round not Finals: {dm}")
        if dm.get("opponent") not in ACTIVE:
            fail(f"{team} display opponent wrong: {dm.get('opponent')}")

    print("=== Finals bracket ===")
    for k, s in finals.items():
        print(f"  {k}: {s['a']} vs {s['b']} ({s.get('a_wins')}-{s.get('b_wins')})")

    print("\n=== Active teams ===")
    for team in ACTIVE:
        pst = app.get_team_playoff_status(team, stt)
        print(f"  {team}: {pst.get('series_record')} vs {pst.get('current_opponent')}")

    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s)")
        return 1
    print("\nOK — Finals state consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
