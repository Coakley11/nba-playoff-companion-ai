"""CDN + stats-today API timing (no streamlit_app import). Run: python scripts/test_live_gc_layer1.py"""
from __future__ import annotations

import time
from datetime import datetime, timezone

NBA_STATS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
}


def test_cdn():
    try:
        from nba_api.live.nba.endpoints import scoreboard
    except ImportError:
        print("CDN: nba_api live not installed")
        return None
    t0 = time.perf_counter()
    try:
        try:
            games = scoreboard.ScoreBoard(timeout=5).get_dict().get("scoreboard", {}).get("games", []) or []
        except TypeError:
            games = scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", []) or []
        err = None
    except Exception as exc:
        games, err = [], repr(exc)
    ms = (time.perf_counter() - t0) * 1000
    print(f"CDN: {len(games)} games in {ms:.0f}ms err={err!r}")
    for g in games[:6]:
        h, a = g.get("homeTeam", {}), g.get("awayTeam", {})
        print(
            f"  {a.get('teamTricode')}@{h.get('teamTricode')} "
            f"{a.get('score')}-{h.get('score')} {g.get('gameStatusText')}"
        )
    return err


def test_stats_today():
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        ZoneInfo = None
    try:
        from nba_api.stats.endpoints import scoreboardv3
    except ImportError:
        print("Stats: scoreboardv3 not available")
        return None
    et = ZoneInfo("America/New_York") if ZoneInfo else None
    today = datetime.now(et).date() if et else datetime.now(timezone.utc).date()
    fmt = today.strftime("%Y-%m-%d")
    t0 = time.perf_counter()
    try:
        dfs = scoreboardv3.ScoreboardV3(
            game_date=fmt, league_id="00", headers=NBA_STATS_HEADERS, timeout=10
        ).get_data_frames()
        err = None
        n = len(dfs[1]) if dfs and len(dfs) > 1 else 0
    except Exception as exc:
        dfs, err, n = None, repr(exc), 0
    ms = (time.perf_counter() - t0) * 1000
    print(f"Stats today ({fmt}): {n} games in {ms:.0f}ms err={err!r}")
    return err


def main():
    print("=== Live GC API smoke (no Streamlit) ===", datetime.now(timezone.utc).isoformat())
    test_cdn()
    test_stats_today()
    print("Done. Use the app with Show performance debug during a live game for full Layer 1 trace.")


if __name__ == "__main__":
    main()
