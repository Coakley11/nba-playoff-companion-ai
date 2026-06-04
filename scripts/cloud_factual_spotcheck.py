"""Cloud factual UI spot-check — prints what each page should show (no browser).

Run before manual Cloud pass:
  python scripts/cloud_factual_spotcheck.py

Pair with browser checks on Streamlit Cloud (`dev` branch) per docs/VALIDATION_STATUS.md P5.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

from pathlib import Path

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
ELIM_SPOT = (
    "Cleveland Cavaliers",
    "Boston Celtics",
    "Los Angeles Lakers",
    "Atlanta Hawks",
)
LINEUP_SLOTS = app.LINEUP_SLOTS
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"  FAIL: {msg}")


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def print_team_header(team: str, stt: dict) -> None:
    dm = app.get_display_matchup(team, stt)
    eff = app.get_effective_team_profile(team, stt)
    pst = app.get_team_playoff_status(team, stt)
    print(f"\n--- {team} ---")
    print(f"  Engine status: {pst.get('status')} | round: {pst.get('current_round')}")
    print(f"  Display: {dm.get('round_short')} vs {dm.get('opponent_nick')} ({dm.get('series_record')})")
    print(f"  Eliminated flag: {dm.get('eliminated')} | badge: {dm.get('status_badge')}")
    print(f"  Effective profile: status={eff.get('status')} round={eff.get('round')} opp={eff.get('current_opponent')}")
    if dm.get("eliminated") and eff.get("status") == "Active":
        fail(f"{team}: eliminated in engine but effective profile still Active")


def print_series_for_team(team: str, stt: dict) -> None:
    for coll in ("finals", "cf", "second", "first"):
        for key, s in (stt.get(coll) or {}).items():
            if team not in (s.get("a"), s.get("b")):
                continue
            tw, ow, opp = app._team_series_record(team, s)
            print(f"  [{s.get('round')}] {key}: {tw}-{ow} vs {opp} winner={s.get('winner')} source={s.get('source')}")
            if s.get("winner") and app._series_has_confirmed_winner(s):
                ww = tw if s.get("winner") == team else ow
                if ww != 4:
                    fail(f"{team} {key}: winner should have 4 wins, has {ww}")


def print_cf_standouts(stt: dict) -> None:
    s = (stt.get("cf") or {}).get("CLE-NYK")
    if not s:
        fail("CLE-NYK conference finals missing")
        return
    a, b = s["a"], s["b"]
    print(f"  East CF shell: {s.get('a_wins')}-{s.get('b_wins')} winner={s.get('winner')}")
    for idx, g in enumerate(s.get("games") or [], start=1):
        mvp, why = app.mvp_for_game(a, b, idx, g.get("Winner"))
        line = mvp or "(not assigned)"
        print(f"    Game {idx}: {g.get('Score')} | standout={line}")


def print_lineups(team: str) -> None:
    board = app.CURRENT_PLAYOFF_LINEUPS.get(team) or {}
    lineup = [board.get(s, "TBD") for s in LINEUP_SLOTS]
    src = (
        "curated playoff override"
        if all(board.get(s) for s in LINEUP_SLOTS)
        else "TEAM_PROFILES fallback"
    )
    rejected = list(app.OUTDATED_PLAYOFF_PLAYERS.get(team) or [])
    print(f"  Source: {src} | resolved: {lineup}")
    if rejected:
        print(f"  Rejected/outdated: {rejected}")
    for slot in LINEUP_SLOTS:
        name = board.get(slot, "—")
        print(f"    {slot}: {name}")
    print("  Headshots: verify on Cloud (CDN uses NBA.com player id lookup per name)")
    bench = board.get("bench") or []
    print(f"  Bench: {bench}")


def print_offseason(team: str) -> None:
    pack = app.get_offseason_outlook(team)
    refl = (pack.get("reflection") or {})
    print(f"  Direction: {(pack.get('direction') or {}).get('label')}")
    cause = (refl.get("elimination_cause") or "")[:120]
    print(f"  Elimination: {cause}...")
    starters = (app.TEAM_PROFILES.get(team) or {}).get("starters") or []
    outdated = app.OUTDATED_PLAYOFF_PLAYERS.get(team) or []
    for name in outdated:
        if name in starters:
            fail(f"{team}: outdated player {name} still in profile starters")
    if team == "Atlanta Hawks" and "Trae Young" in starters:
        fail("Atlanta profile starters still list Trae Young")
    if team == "Cleveland Cavaliers" and "4-2" in str(app.TEAM_PROFILES[team].get("first_round_result", "")):
        fail("Cleveland first_round_result still says 4-2")


def print_tracker_defaults(team: str) -> None:
    prof = app.TEAM_PROFILES.get(team) or {}
    anchor = (prof.get("starters") or ["—"])[0]
    resume = app.player_resume_profile(anchor, team)
    print(f"  Default anchor: {anchor}")
    print(f"  Role: {resume.get('role')} | comps: {resume.get('comps', [])[:3]}")
    if team == "New York Knicks" and "Frazier" not in str(resume.get("comps")):
        fail("Knicks anchor should reference Knicks franchise comps")
    if team == "San Antonio Spurs" and anchor.lower().find("castle") >= 0:
        sp = app.specific_legacy_comparison(anchor, team, 22, 0.45, 0.35, 1, 3, False, 70)
        print(f"  Legacy sample: {sp[:100]}...")


def main() -> int:
    print("Cloud factual spot-check (demo backup, no API refresh)", flush=True)
    app.fetch_completed_games_recent = lambda *args, **kwargs: []
    stt = app.get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)
    errors = app.validate_playoff_factual_accuracy(stt)
    if errors:
        for e in errors:
            fail(e)
    else:
        print("\nEngine validate_playoff_factual_accuracy: OK")

    section("1. Home / Bracket / Ribbon (active teams)")
    for team in ACTIVE:
        print_team_header(team, stt)
        print_series_for_team(team, stt)

    section("2. Previous Rounds — East CF standouts (Knicks 4-0)")
    print_cf_standouts(stt)

    section("3. Matchup Lineups (Finals teams)")
    for team in ACTIVE:
        print(f"\n{team}")
        print_lineups(team)

    section("4. Player Playoff Tracker / Legacy defaults")
    for team in ACTIVE:
        print(f"\n{team}")
        print_tracker_defaults(team)
    print("\n  Game log order: app uses _df_newest_first_for_display (newest first)")

    section("5. Eliminated-team offseason (spot-check four)")
    for team in ELIM_SPOT:
        print(f"\n{team}")
        print_team_header(team, stt)
        print_offseason(team)

    section("6. Live Game Center")
    print("  FROZEN — validation fixes only. Spot-check trust strip on Cloud during live game (P1).")

    section("Manual Cloud checklist (browser)")
    pages = [
        "Home Dashboard",
        "Playoff Bracket",
        "Previous Rounds",
        "Matchup Lineups",
        "Player Playoff Tracker",
        "Legacy Tracker",
        "Team History & Leaders",
    ]
    for p in pages:
        print(f"  [ ] {p} — scores, standouts, rosters, active/eliminated state")

    if FAILURES:
        print(f"\n{len(FAILURES)} automated failure(s) — fix before signing off Cloud UI.")
        return 1
    print("\nAutomated spot-check OK. Complete browser pass on Streamlit Cloud (dev).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
