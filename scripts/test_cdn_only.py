import time
from nba_api.live.nba.endpoints import scoreboard

t0 = time.perf_counter()
games = scoreboard.ScoreBoard(timeout=5).get_dict().get("scoreboard", {}).get("games", []) or []
print("games", len(games), "ms", int((time.perf_counter() - t0) * 1000))
for g in games[:6]:
    h, a = g.get("homeTeam", {}), g.get("awayTeam", {})
    print(a.get("teamTricode"), a.get("score"), "@", h.get("teamTricode"), h.get("score"), g.get("gameStatusText"))
