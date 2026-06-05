"""Factual accuracy audit — playoff scores, standouts, Finals state (no Streamlit UI).

Run from repo root:
  python scripts/audit_factual_accuracy.py
"""
from __future__ import annotations

import re
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

FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def main() -> int:
    src = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")

    print("=== Static copy guards ===")
    if 'Cleveland Cavaliers",4,"Eastern Conference","New York Knicks","Lost to New York Knicks, 4-2' in src:
        fail("Cleveland ELIMINATED_INFO still says Lost to New York Knicks, 4-2")
    else:
        ok("Cleveland elimination copy not 4-2 vs Knicks")

    if '("New York Knicks", "Atlanta Hawks", 2): ("Trae Young"' in src:
        fail("FALLBACK_GAME_MVPS still credits Trae Young for Hawks games")
    else:
        ok("No Trae Young in Knicks–Hawks fallback standouts")

    print("\n=== Playoff engine (demo backup) ===")
    stt = app.get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)

    cf = stt.get("cf") or {}
    cle_nyk = cf.get("CLE-NYK")
    if not cle_nyk:
        fail("CLE-NYK conference finals shell missing")
    else:
        nyk, cle = "New York Knicks", "Cleveland Cavaliers"
        tw, ow, _opp = app._team_series_record(nyk, cle_nyk)
        if cle_nyk.get("winner") != nyk or not (tw == 4 and ow == 0):
            fail(f"East CF must be Knicks 4-0, got winner={cle_nyk.get('winner')} score {tw}-{ow}")
        else:
            ok(f"East CF Knicks sweep Cavaliers ({tw}-{ow})")

    finals = stt.get("finals") or {}
    for _k, s in finals.items():
        teams = {s.get("a"), s.get("b")}
        if teams == {"New York Knicks", "San Antonio Spurs"}:
            ok(f"NBA Finals: {s.get('a')} vs {s.get('b')}")
            g1 = (s.get("games") or [{}])[0]
            sc = str(g1.get("Score", ""))
            canonical = getattr(app, "FINALS_GAME1_CANONICAL_SCORE", "Knicks 105, Spurs 95")
            if sc != canonical:
                fail(f"Finals G1 score must be {canonical!r}, got {sc!r}")
            elif sc in ("Knicks 118, Spurs 112", "Knicks 108, Spurs 102"):
                fail(f"Finals G1 uses retired incorrect score: {sc!r}")
            else:
                ok(f"Finals G1 score: {sc}")
        else:
            fail(f"Finals teams must be Knicks+Spurs, got {teams}")

    print("\n=== Unified validation guard ===")
    engine_errors = app.validate_playoff_factual_accuracy(stt)
    if engine_errors:
        for err in engine_errors:
            fail(err)
    else:
        ok("validate_playoff_factual_accuracy returned no issues")

    print("\n=== Per-game standout resolution ===")
    for s in app._iter_playoff_series_shells_merged(stt):
        a, b = s.get("a"), s.get("b")
        for idx, g in enumerate(s.get("games") or [], start=1):
            winner = g.get("Winner")
            mvp, _why = app.mvp_for_game(a, b, idx, winner)
            if mvp and not app._validate_game_standout_candidate(
                mvp, a, b, winner if winner in (a, b) else None
            ):
                fail(f"{a} vs {b} game {idx}: standout {mvp!r} failed roster check")
            if mvp and app._is_outdated_playoff_player(mvp, a):
                fail(f"{a} vs {b} game {idx}: outdated player {mvp!r} on {a}")
            if mvp and app._is_outdated_playoff_player(mvp, b):
                fail(f"{a} vs {b} game {idx}: outdated player {mvp!r} on {b}")

    if not any("standout" in f.lower() or "Trae" in f for f in FAILURES):
        ok("All resolved standouts pass roster/outdated checks")

    print("\n=== Active Finals roster (no outdated players) ===")
    for team in ("New York Knicks", "San Antonio Spurs"):
        prof = app.TEAM_PROFILES.get(team) or {}
        for name in (prof.get("starters") or []) + (prof.get("subs") or []):
            if app._is_outdated_playoff_player(name, team):
                fail(f"{team} profile lists outdated player {name!r}")
        board = (app.CURRENT_PLAYOFF_LINEUPS.get(team) or {}).get("bench")
        starters = [app.CURRENT_PLAYOFF_LINEUPS.get(team, {}).get(s) for s in ("PG", "SG", "SF", "PF", "C")]
        if "Jeremy Sochan" in starters and team == "San Antonio Spurs":
            fail("Spurs curated lineup still starts Jeremy Sochan")
        if "Precious Achiuwa" in (starters + (board or [])) and team == "New York Knicks":
            fail("Knicks curated lineup still includes Precious Achiuwa")
    if not any("Sochan" in f or "Achiuwa" in f for f in FAILURES):
        ok("Knicks and Spurs active rotations exclude outdated players")

    print("\n=== Player playoff log fallback ===")
    br_logs = app.fetch_playoff_gamelog("Jalen Brunson", "New York Knicks", app.CURRENT_NBA_SEASON)
    if br_logs.empty:
        fail("Jalen Brunson curated playoff log is empty")
    else:
        ok(f"Jalen Brunson playoff log: {len(br_logs)} games")
    kt_logs = app.fetch_playoff_gamelog("Karl-Anthony Towns", "New York Knicks", app.CURRENT_NBA_SEASON)
    if kt_logs.empty:
        fail("Karl-Anthony Towns curated playoff log is empty")
    else:
        ok(f"Karl-Anthony Towns playoff log: {len(kt_logs)} games")

    print("\n=== Summary ===")
    if FAILURES:
        print(f"FAILED ({len(FAILURES)} issue(s))")
        return 1
    print("All factual accuracy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
