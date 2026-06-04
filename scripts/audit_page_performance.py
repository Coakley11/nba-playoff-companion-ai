"""Headless performance audit — ranks slowest engine paths (no browser).

Run from repo root:
  python scripts/audit_page_performance.py
  python scripts/audit_page_performance.py --team "New York Knicks"
"""
from __future__ import annotations

import argparse
import sys
import time
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

DEFAULT_TEAM = "New York Knicks"
OPP_TEAM = "San Antonio Spurs"
_BENCH_TIMEOUT_SEC = 45.0


def _ms(fn, *args, **kwargs) -> float:
    t0 = time.perf_counter()
    fn(*args, **kwargs)
    return (time.perf_counter() - t0) * 1000.0


def _bench(label: str, fn, *args, **kwargs) -> tuple[str, float] | None:
    t0 = time.perf_counter()
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        print(f"  {label}: ERROR ({exc})")
        return label, -1.0
    elapsed = (time.perf_counter() - t0) * 1000.0
    if elapsed > _BENCH_TIMEOUT_SEC * 1000.0:
        print(f"  {label}: {elapsed:.0f} ms (exceeded { _BENCH_TIMEOUT_SEC:.0f}s budget)")
    else:
        print(f"  {label}: {elapsed:.0f} ms")
    return label, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="NBA app performance audit")
    parser.add_argument("--team", default=DEFAULT_TEAM, help="Primary team for context paths")
    parser.add_argument(
        "--network",
        action="store_true",
        help="Include live CDN/stats/player-log benchmarks (can take 30s+ each)",
    )
    args = parser.parse_args()
    team = args.team
    opp = OPP_TEAM if team == DEFAULT_TEAM else DEFAULT_TEAM

    app.QA_MODE = True
    app.ULTRA_FAST_VALIDATION_MODE = True
    _st.session_state["QA_MODE"] = True
    _st.session_state["ULTRA_FAST_VALIDATION_MODE"] = True

    print("NBA Playoff Companion — performance audit (headless)")
    print(f"Team: {team} · QA + Ultra-fast (demo snapshot, no network)\n")

    timings: list[tuple[str, float]] = []

    print("=== Playoff engine (demo, no API) ===")
    row = _bench("get_playoff_state_snapshot", app.get_playoff_state_snapshot, True, False)
    if row:
        timings.append(row)
    stt = app.get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)
    row = _bench("validate_playoff_factual_accuracy", app.validate_playoff_factual_accuracy, stt)
    if row:
        timings.append(row)

    print("\n=== Home / bracket context ===")
    row = _bench("resolve_home_matchup_context_fast", app.resolve_home_matchup_context_fast, team)
    if row:
        timings.append(row)
    hctx = app.resolve_home_matchup_context_fast(team)
    row = _bench(
        "build_dashboard_playoff_context (quick)",
        app.build_dashboard_playoff_context,
        team,
        hctx,
        None,
        True,
    )
    if row:
        timings.append(row)
    row = _bench("get_display_matchup", app.get_display_matchup, team, stt)
    if row:
        timings.append(row)
    row = _bench("get_team_playoff_status", app.get_team_playoff_status, team, stt)
    if row:
        timings.append(row)

    print("\n=== Live Game Center ===")
    row = _bench(
        "resolve_live_game_state (profile only)",
        app.resolve_live_game_state,
        team,
        None,
        network=False,
    )
    if row:
        timings.append(row)
    if args.network:
        row = _bench("resolve_live_game_state (network)", app.resolve_live_game_state, team, None, network=True)
        if row:
            timings.append(row)
    else:
        print("  (skip network Live GC — pass --network to include)")

    print("\n=== Lineups / rosters ===")
    row = _bench("build_lineup_matchups (curated QA path)", app.build_lineup_matchups, team, opp)
    if row:
        timings.append(row)

    print("\n=== Player / legacy (API-heavy) ===")
    if args.network:
        anchor = (app.TEAM_PROFILES.get(team) or {}).get("starters", ["Jalen Brunson"])[0]
        pid = app.get_player_id(anchor)
        if pid:
            row = _bench("playoff_game_logs_for_player", app.playoff_game_logs_for_player, anchor)
            if row:
                timings.append(row)
        else:
            print(f"  (skip player logs — no id for {anchor})")
        row = _bench("build_matchup_intelligence_sections", app.build_matchup_intelligence_sections, team)
        if row:
            timings.append(row)
    else:
        print("  (skip player logs + matchup intel — pass --network to include)")

    print("\n=== Duplicate-call check ===")
    t_dup = time.perf_counter()
    for _ in range(3):
        app.get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)
    dup_ms = (time.perf_counter() - t_dup) * 1000.0 / 3.0
    print(f"  playoff_state x3 avg (uncached decorator in script): {dup_ms:.0f} ms")

    ranked = sorted(timings, key=lambda x: x[1], reverse=True)
    print("\n" + "=" * 60)
    print("TOP 5 BOTTLENECKS (approximate ms, cold headless run)")
    print("=" * 60)
    for i, (name, ms) in enumerate(ranked[:5], 1):
        print(f"  {i}. {name} — {ms:.0f} ms")

    print("\nNotes:")
    print("  - Streamlit @st.cache_data is bypassed in this script (identity decorator).")
    print("  - In the browser, enable sidebar 'QA mode' for fast factual testing.")
    print("  - Enable 'Show performance debug' for per-section timings on each page.")
    print("  - See docs/PERFORMANCE_AUDIT.md for Cloud targets and cache audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
