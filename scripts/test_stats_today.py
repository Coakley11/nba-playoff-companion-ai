import time
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

try:
    from nba_api.stats.endpoints import scoreboardv3
    NBA_STATS_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122",
        "Referer": "https://www.nba.com/",
    }
    et = ZoneInfo("America/New_York") if ZoneInfo else None
    today = datetime.now(et).date() if et else datetime.utcnow().date()
    fmt = today.strftime("%Y-%m-%d")
    t0 = time.perf_counter()
    dfs = scoreboardv3.ScoreboardV3(game_date=fmt, league_id="00", headers=NBA_STATS_HEADERS, timeout=10).get_data_frames()
    ms = int((time.perf_counter() - t0) * 1000)
    print("v3 frames", len(dfs), "ms", ms)
    if len(dfs) > 1:
        print("games", len(dfs[1]), "cols", list(dfs[1].columns)[:8])
except Exception as e:
    print("FAIL", type(e).__name__, e)
