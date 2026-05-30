"""Lightweight bracket QA — mocks Streamlit so the full app UI does not boot."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Mock Streamlit before importing streamlit_app (sidebar code runs at import time).
_st = MagicMock()
_st.cache_data = lambda **kwargs: (lambda fn: fn)
_st.session_state = {}
_st.sidebar = MagicMock()
_st_autorefresh = MagicMock()
sys.modules["streamlit"] = _st
sys.modules["streamlit_autorefresh"] = MagicMock(st_autorefresh=_st_autorefresh)

import streamlit_app as app  # noqa: E402

stt = app.get_playoff_state_cached(use_demo_backup=True, api_refresh=False)
print("=== Second round ===")
for k, s in stt["second"].items():
    print(f"  {k}: {s['a_wins']}-{s['b_wins']} winner={s.get('winner')}")

print("\n=== Conference finals ===")
for k, s in (stt.get("cf") or {}).items():
    print(f"  {k}: {s['a_wins']}-{s['b_wins']} {s['a']} vs {s['b']} winner={s.get('winner')}")

print("\n=== Team status (all) ===")
for team in sorted(app.TEAM_PROFILES.keys()):
    pst = app.get_team_playoff_status(team, stt)
    eff = app.get_effective_team_profile(team, stt)
    label = app._sidebar_team_label(team)
    print(
        f"  {team}: status={pst.get('status')} round={pst.get('current_round')} "
        f"opp={pst.get('current_opponent')} rec={pst.get('series_record')} "
        f"sidebar={label!r} eff_round={eff.get('round')}"
    )

print("\n=== Active teams only ===")
for team, p in app.TEAM_PROFILES.items():
    if p.get("status") == "Active":
        dm = app.get_display_matchup(team, stt)
        print(f"  {team}: {dm.get('round_short')} vs {dm.get('opponent_nick')} ({dm.get('series_record')})")
