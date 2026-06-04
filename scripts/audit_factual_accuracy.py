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

    print("\n=== Summary ===")
    if FAILURES:
        print(f"FAILED ({len(FAILURES)} issue(s))")
        return 1
    print("All factual accuracy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
