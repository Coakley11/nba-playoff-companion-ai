import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from collections import defaultdict

# ==========================================================
# Optional imports
# ==========================================================
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

try:
    from nba_api.live.nba.endpoints import scoreboard, boxscore, playbyplay
    NBA_LIVE_AVAILABLE = True
except Exception:
    NBA_LIVE_AVAILABLE = False

try:
    from nba_api.stats.endpoints import scoreboardv2, playergamelog, playercareerstats
    from nba_api.stats.static import players as nba_players
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

# ==========================================================
# Page setup
# ==========================================================
st.set_page_config(
    page_title="Daniel Cohen — Real NBA Playoff Companion",
    page_icon="🏀",
    layout="wide",
)

st.title("Daniel Cohen — Real NBA Playoff Companion")
st.caption("Real NBA mode: the app follows actual NBA.com / nba_api schedule and completed games. No fictional bracket is used.")

st.markdown("""
<style>
section[data-testid="stSidebar"] {background: linear-gradient(180deg,#f8fafc,#e5e7eb)!important;color:#111827!important;}
section[data-testid="stSidebar"] * {color:#111827!important;}
.big-status {font-size:20px;font-weight:900;padding:12px 14px;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa;}
.good-card {padding:14px;border-radius:16px;background:#ecfdf5;border:1px solid #bbf7d0;margin:6px 0;}
.warn-card {padding:14px;border-radius:16px;background:#fff7ed;border:1px solid #fed7aa;margin:6px 0;}
.series-card {background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.18);border-radius:16px;padding:10px 12px;margin:9px 0;color:white;}
.team-row {display:flex;align-items:center;justify-content:space-between;padding:4px 0;font-size:15px;}
.wins {font-weight:900;font-size:18px;color:#fbbf24;}
.series-note {text-align:center;color:#bfdbfe;font-size:12px;margin-top:6px;}
.debug-box {background:#111827;color:#e5e7eb;border-radius:14px;padding:12px;font-family:monospace;font-size:13px;}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# Team data
# ==========================================================
TEAM_IDS = {
    "Atlanta Hawks": 1610612737, "Boston Celtics": 1610612738, "Brooklyn Nets": 1610612751,
    "Charlotte Hornets": 1610612766, "Chicago Bulls": 1610612741, "Cleveland Cavaliers": 1610612739,
    "Dallas Mavericks": 1610612742, "Denver Nuggets": 1610612743, "Detroit Pistons": 1610612765,
    "Golden State Warriors": 1610612744, "Houston Rockets": 1610612745, "Indiana Pacers": 1610612754,
    "LA Clippers": 1610612746, "Los Angeles Lakers": 1610612747, "Memphis Grizzlies": 1610612763,
    "Miami Heat": 1610612748, "Milwaukee Bucks": 1610612749, "Minnesota Timberwolves": 1610612750,
    "New Orleans Pelicans": 1610612740, "New York Knicks": 1610612752, "Oklahoma City Thunder": 1610612760,
    "Orlando Magic": 1610612753, "Philadelphia 76ers": 1610612755, "Phoenix Suns": 1610612756,
    "Portland Trail Blazers": 1610612757, "Sacramento Kings": 1610612758, "San Antonio Spurs": 1610612759,
    "Toronto Raptors": 1610612761, "Utah Jazz": 1610612762, "Washington Wizards": 1610612764,
}
ID_TO_TEAM = {v: k for k, v in TEAM_IDS.items()}
TEAM_ALIASES = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN", "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET", "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP", "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}
ALIAS_TO_TEAM = {v: k for k, v in TEAM_ALIASES.items()}
TEAM_LOGOS = {team: f"https://cdn.nba.com/logos/nba/{tid}/primary/L/logo.svg" for team, tid in TEAM_IDS.items()}

EAST_TEAMS = {
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls", "Cleveland Cavaliers",
    "Detroit Pistons", "Indiana Pacers", "Miami Heat", "Milwaukee Bucks", "New York Knicks", "Orlando Magic",
    "Philadelphia 76ers", "Toronto Raptors", "Washington Wizards"
}

# ==========================================================
# Utility helpers
# ==========================================================
def safe_int(x, default=0):
    try:
        if pd.isna(x):
            return default
        return int(float(x))
    except Exception:
        return default


def parse_date_value(v):
    if v is None or pd.isna(v):
        return None
    text = str(v)
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(text[:19] if "T" in text else text[:10], fmt).date()
        except Exception:
            pass
    try:
        return pd.to_datetime(text).date()
    except Exception:
        return None


def date_label(d):
    if not d:
        return ""
    try:
        return d.strftime("%b %-d, %Y")
    except Exception:
        return d.strftime("%b %d, %Y")


def logo_html(team, size=30):
    return f"<img src='{TEAM_LOGOS.get(team, '')}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"


def conf_for_team(team):
    return "East" if team in EAST_TEAMS else "West"

# ==========================================================
# NBA API fetching
# ==========================================================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_games():
    if not NBA_LIVE_AVAILABLE:
        return [], "nba_api live endpoints are not installed/available."
    try:
        data = scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", [])
        return data, None
    except Exception as e:
        return [], f"Live scoreboard error: {type(e).__name__}: {e}"


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_scoreboard_games_for_date(date_str):
    """Fetch one date from scoreboardv2. date_str must be YYYY-MM-DD."""
    if not NBA_STATS_AVAILABLE:
        return [], "nba_api stats endpoints are not installed/available."
    errors = []
    # scoreboardv2 is inconsistent by environment. Try ISO first, then NBA's common MM/DD/YYYY.
    attempts = [date_str]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        attempts.append(d.strftime("%m/%d/%Y"))
    except Exception:
        pass

    for ds in attempts:
        try:
            dfs = scoreboardv2.ScoreboardV2(game_date=ds, timeout=20).get_data_frames()
            if not dfs:
                continue
            df = dfs[0]
            if df is None or df.empty:
                return [], None
            rows = []
            for _, r in df.iterrows():
                home = ID_TO_TEAM.get(safe_int(r.get("HOME_TEAM_ID")))
                away = ID_TO_TEAM.get(safe_int(r.get("VISITOR_TEAM_ID")))
                if not home or not away:
                    continue
                game_date = parse_date_value(r.get("GAME_DATE_EST")) or datetime.strptime(date_str, "%Y-%m-%d").date()
                home_pts = safe_int(r.get("PTS_HOME"))
                away_pts = safe_int(r.get("PTS_AWAY"))
                status = str(r.get("GAME_STATUS_TEXT", ""))
                is_final = "final" in status.lower() or safe_int(r.get("GAME_STATUS_ID")) == 3
                winner = None
                if is_final and home_pts != away_pts:
                    winner = home if home_pts > away_pts else away
                rows.append({
                    "GameID": str(r.get("GAME_ID", "")),
                    "GameDate": game_date,
                    "Date": date_label(game_date),
                    "Home": home,
                    "Away": away,
                    "HomeScore": home_pts,
                    "AwayScore": away_pts,
                    "Winner": winner,
                    "Status": status,
                    "IsFinal": is_final,
                    "Matchup": f"{away} at {home}",
                    "Score": f"{away} {away_pts}, {home} {home_pts}" if is_final else status,
                })
            return rows, None
        except Exception as e:
            errors.append(f"{ds}: {type(e).__name__}: {e}")
    return [], " | ".join(errors) if errors else None


@st.cache_data(ttl=1800, show_spinner=True)
def fetch_real_nba_games(start_date, end_date):
    """Fetch all scoreboard games in date range. Returns list + debug dictionary."""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    all_games = []
    errors = []
    checked = []
    d = start
    while d <= end:
        ds = d.strftime("%Y-%m-%d")
        checked.append(ds)
        games, err = fetch_scoreboard_games_for_date(ds)
        if err:
            errors.append(f"{ds}: {err}")
        all_games.extend(games)
        d += timedelta(days=1)
    # de-dupe by GameID when available
    seen = set()
    clean = []
    for g in all_games:
        key = g.get("GameID") or (str(g.get("GameDate")) + g.get("Matchup", ""))
        if key in seen:
            continue
        seen.add(key)
        clean.append(g)
    clean.sort(key=lambda x: (x.get("GameDate") or date.min, x.get("GameID", "")))
    debug = {
        "NBA_STATS_AVAILABLE": NBA_STATS_AVAILABLE,
        "NBA_LIVE_AVAILABLE": NBA_LIVE_AVAILABLE,
        "dates_checked": len(checked),
        "start_date": start_date,
        "end_date": end_date,
        "games_found": len(clean),
        "final_games_found": sum(1 for g in clean if g.get("IsFinal")),
        "errors": errors[:8],
    }
    return clean, debug

# ==========================================================
# Build real series state from completed games
# ==========================================================
def canonical_pair(a, b):
    return tuple(sorted([a, b]))


def build_series_from_games(games, only_final=True):
    completed = [g for g in games if g.get("IsFinal") and g.get("Winner")] if only_final else games
    grouped = defaultdict(list)
    for g in completed:
        grouped[canonical_pair(g["Home"], g["Away"])].append(g)

    series = []
    for pair, gs in grouped.items():
        gs = sorted(gs, key=lambda x: (x.get("GameDate") or date.min, x.get("GameID", "")))
        # Likely playoff series: same teams played multiple times recently. One-game pairs still appear in "All Games" but not main bracket.
        wins = {pair[0]: 0, pair[1]: 0}
        game_rows = []
        for idx, g in enumerate(gs, start=1):
            wins[g["Winner"]] += 1
            game_rows.append({
                "Game": f"Game {idx}",
                "Date": g.get("Date", ""),
                "Matchup": g.get("Matchup", ""),
                "Score": g.get("Score", ""),
                "Winner": g.get("Winner", ""),
                "GameID": g.get("GameID", ""),
            })
        a, b = pair
        winner = a if wins[a] >= 4 else b if wins[b] >= 4 else None
        leader = a if wins[a] > wins[b] else b if wins[b] > wins[a] else "Tied"
        conf = conf_for_team(a) if conf_for_team(a) == conf_for_team(b) else "Cross-Conference"
        series.append({
            "a": a, "b": b,
            "a_wins": wins[a], "b_wins": wins[b],
            "winner": winner,
            "leader": leader,
            "conf": conf,
            "games": game_rows,
            "last_game": game_rows[-1] if game_rows else None,
            "num_games": len(game_rows),
        })
    series.sort(key=lambda s: (s["conf"], -s["num_games"], s["a"], s["b"]))
    return series


def find_team_series(series_list, team):
    matches = [s for s in series_list if team in [s["a"], s["b"]]]
    if not matches:
        return None
    matches.sort(key=lambda s: (s["num_games"], max(s["a_wins"], s["b_wins"])), reverse=True)
    return matches[0]


def series_status_text(s, team=None):
    if not s:
        return "No completed real series found yet."
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    if team:
        opp = b if team == a else a
        tw = aw if team == a else bw
        ow = bw if team == a else aw
        alias = TEAM_ALIASES.get(team, team)
        opp_alias = TEAM_ALIASES.get(opp, opp)
        if tw > ow:
            return f"{alias} leads {tw}-{ow} vs {opp_alias}"
        if tw < ow:
            return f"{alias} trails {tw}-{ow} vs {opp_alias}"
        return f"{alias} tied {tw}-{ow} vs {opp_alias}"
    if aw > bw:
        return f"{TEAM_ALIASES.get(a,a)} leads {aw}-{bw} vs {TEAM_ALIASES.get(b,b)}"
    if bw > aw:
        return f"{TEAM_ALIASES.get(b,b)} leads {bw}-{aw} vs {TEAM_ALIASES.get(a,a)}"
    return f"{TEAM_ALIASES.get(a,a)} and {TEAM_ALIASES.get(b,b)} tied {aw}-{bw}"

# ==========================================================
# Live helpers
# ==========================================================
def live_game_for_team(team):
    games, err = fetch_live_games()
    alias = TEAM_ALIASES.get(team)
    for g in games:
        h = g.get("homeTeam", {})
        a = g.get("awayTeam", {})
        if h.get("teamTricode") == alias or a.get("teamTricode") == alias:
            return g, err
    return None, err


@st.cache_data(ttl=30, show_spinner=False)
def get_boxscore(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return {}
    try:
        return boxscore.BoxScore(game_id).get_dict().get("game", {})
    except Exception:
        return {}


@st.cache_data(ttl=30, show_spinner=False)
def get_pbp(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return []
    try:
        return playbyplay.PlayByPlay(game_id).get_dict().get("game", {}).get("actions", [])
    except Exception:
        return []


def create_boxscore_df(game_box):
    rows = []
    for side in ["homeTeam", "awayTeam"]:
        t = game_box.get(side, {})
        tri = t.get("teamTricode", "")
        for p in t.get("players", []):
            stt = p.get("statistics", {})
            rows.append({
                "Team": tri,
                "Player": p.get("name", ""),
                "MIN": stt.get("minutes", ""),
                "PTS": stt.get("points", 0),
                "REB": stt.get("reboundsTotal", 0),
                "AST": stt.get("assists", 0),
                "STL": stt.get("steals", 0),
                "BLK": stt.get("blocks", 0),
                "TO": stt.get("turnovers", 0),
                "PF": stt.get("foulsPersonal", 0),
                "FGM": stt.get("fieldGoalsMade", 0),
                "FGA": stt.get("fieldGoalsAttempted", 0),
                "3PM": stt.get("threePointersMade", 0),
                "3PA": stt.get("threePointersAttempted", 0),
                "+/-": stt.get("plusMinusPoints", 0),
            })
    return pd.DataFrame(rows)


def is_top_play(desc):
    d = (desc or "").lower()
    if any(x in d for x in ["timeout", "substitution", "free throw", "personal foul", "violation"]):
        return False
    return any(x in d for x in ["dunk", "3pt", "three", "steal", "block", "fast break", "layup", "alley", "putback"])


def top_plays_for_game(game_id, team):
    alias = TEAM_ALIASES.get(team)
    actions = get_pbp(game_id)
    rows = []
    for a in actions:
        if alias and (a.get("teamTricode") or "") != alias:
            continue
        desc = a.get("description", "") or ""
        if is_top_play(desc):
            rows.append({
                "Period": a.get("period", ""),
                "Clock": a.get("clock", ""),
                "Top Play": desc,
                "Why it mattered": "This was a high-impact possession from the live play-by-play feed.",
            })
    return pd.DataFrame(rows[-8:])

# ==========================================================
# Rendering
# ==========================================================
def render_api_status(debug):
    st.markdown("### API Status")
    st.markdown(f"""
<div class='debug-box'>
NBA_STATS_AVAILABLE: {debug.get('NBA_STATS_AVAILABLE')}<br>
NBA_LIVE_AVAILABLE: {debug.get('NBA_LIVE_AVAILABLE')}<br>
Date window: {debug.get('start_date')} to {debug.get('end_date')}<br>
Dates checked: {debug.get('dates_checked')}<br>
Games found: {debug.get('games_found')}<br>
Final games found: {debug.get('final_games_found')}<br>
Recent errors shown: {len(debug.get('errors', []))}
</div>
""", unsafe_allow_html=True)
    if debug.get("errors"):
        with st.expander("Show API errors / warnings"):
            for e in debug.get("errors", []):
                st.code(e)


def render_team_header(team, s=None):
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        st.image(TEAM_LOGOS.get(team, ""), width=110)
    with c2:
        st.markdown(f"<div style='text-align:center'><h1>{team}</h1><h3>{series_status_text(s, team) if s else 'Real NBA mode'}</h3></div>", unsafe_allow_html=True)
    with c3:
        if s:
            opp = s["b"] if team == s["a"] else s["a"]
            st.image(TEAM_LOGOS.get(opp, ""), width=110)


def render_series_card(s):
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    winner = s.get("winner")
    note = "Final" if winner else "In progress / detected from completed games"
    return f"""
    <div class='series-card'>
      <div class='team-row'><div>{logo_html(a)}{a}</div><div class='wins'>{aw}</div></div>
      <div class='team-row'><div>{logo_html(b)}{b}</div><div class='wins'>{bw}</div></div>
      <div class='series-note'>{s['conf']} · {note} · {s['num_games']} completed game(s)</div>
    </div>
    """


def render_bracket(series_list):
    st.subheader("Real NBA Series / Bracket View")
    playoff_like = [s for s in series_list if s["num_games"] >= min_games_for_series]
    if not playoff_like:
        st.warning("No repeated team matchups found in this date window. Expand the date range or check API status.")
        return
    east = [s for s in playoff_like if s["conf"] == "East"]
    west = [s for s in playoff_like if s["conf"] == "West"]
    other = [s for s in playoff_like if s["conf"] == "Cross-Conference"]
    st.markdown("""
    <style>.bracket-wrap{background:linear-gradient(135deg,#07111f,#10213d,#301a55);padding:22px;border-radius:22px;border:1px solid rgba(255,255,255,.16);color:white;}.bracket-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.conf-title{text-align:center;font-size:24px;font-weight:900;margin-bottom:10px}</style>
    """, unsafe_allow_html=True)
    html = "<div class='bracket-wrap'><h2 style='text-align:center'>Real NBA Playoff/Series Tracker</h2><div class='bracket-grid'>"
    html += "<div><div class='conf-title'>Eastern Conference</div>" + "".join(render_series_card(s) for s in east) + "</div>"
    html += "<div><div class='conf-title'>Western Conference</div>" + "".join(render_series_card(s) for s in west) + "</div>"
    html += "</div>"
    if other:
        html += "<hr><h3>Cross-Conference / Other Repeated Matchups</h3>" + "".join(render_series_card(s) for s in other)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_team_outlook(team, s):
    st.subheader("Team Outlook")
    if not s:
        st.info("No completed repeated matchup found for this team in the selected date window yet.")
        return
    last = s.get("last_game")
    st.markdown(f"<div class='big-status'>{series_status_text(s, team)}</div>", unsafe_allow_html=True)
    if last:
        won_last = last.get("Winner") == team
        if won_last:
            st.markdown(f"<div class='good-card'><b>Most recent result:</b> {team} won {last['Game']} on {last['Date']}. Score: {last['Score']}.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='warn-card'><b>Most recent result:</b> {team} lost {last['Game']} on {last['Date']}. Score: {last['Score']}.</div>", unsafe_allow_html=True)
    tw = s["a_wins"] if team == s["a"] else s["b_wins"]
    ow = s["b_wins"] if team == s["a"] else s["a_wins"]
    st.markdown("### What is going well / what matters now")
    if tw > ow:
        st.success("The team has the series edge. The main priority is to keep the same formula working and avoid giving momentum back.")
        st.success("The most recent completed game is now the anchor for the dashboard, top plays, and outlook.")
    elif tw < ow:
        st.warning("The team is behind in the series. The next game becomes more urgent, especially for defensive adjustments and shot quality.")
    else:
        st.info("The series is tied. The next completed game will swing the dashboard and bracket automatically.")


def render_live_game_center(team):
    st.subheader("Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_refresh")
        st.caption("Auto-refreshing every 30 seconds while the app is open.")
    live, err = live_game_for_team(team)
    if err:
        st.warning(err)
    if not live:
        st.info("No live or same-day scheduled game found for this team right now from the live endpoint.")
        return
    home = live.get("homeTeam", {})
    away = live.get("awayTeam", {})
    gid = live.get("gameId", "")
    st.write(f"### {away.get('teamCity','')} {away.get('teamName','')} at {home.get('teamCity','')} {home.get('teamName','')}")
    st.write(f"**Status:** {live.get('gameStatusText', '')} | **Period:** {live.get('period','')} | **Clock:** {live.get('gameClock','')}")
    c1, c2 = st.columns(2)
    c1.metric(away.get("teamTricode", "Away"), safe_int(away.get("score", 0)))
    c2.metric(home.get("teamTricode", "Home"), safe_int(home.get("score", 0)))
    box = get_boxscore(gid)
    df = create_boxscore_df(box) if box else pd.DataFrame()
    if not df.empty:
        st.subheader("Live Box Score")
        st.dataframe(df, use_container_width=True)
    plays = top_plays_for_game(gid, team)
    if not plays.empty:
        st.subheader("Live Top Plays")
        st.dataframe(plays, use_container_width=True)

# ==========================================================
# Sidebar controls
# ==========================================================
today = datetime.now().date()
st.sidebar.header("Real NBA Mode Settings")
favorite_team = st.sidebar.selectbox("Choose team", list(TEAM_IDS.keys()), index=list(TEAM_IDS.keys()).index("New York Knicks"))

season_mode = st.sidebar.selectbox(
    "Date window",
    ["Current playoff-style window", "Last 30 days", "Custom"],
    index=0,
)
if season_mode == "Current playoff-style window":
    default_start = date(today.year, 4, 1)
    default_end = today + timedelta(days=2)
elif season_mode == "Last 30 days":
    default_start = today - timedelta(days=30)
    default_end = today + timedelta(days=2)
else:
    default_start = today - timedelta(days=60)
    default_end = today + timedelta(days=2)

if season_mode == "Custom":
    start_input = st.sidebar.date_input("Start date", value=default_start)
    end_input = st.sidebar.date_input("End date", value=default_end)
else:
    start_input, end_input = default_start, default_end

min_games_for_series = st.sidebar.slider("Minimum games to show as a series", 1, 7, 2)
show_all_games = st.sidebar.checkbox("Show all fetched games table", value=False)
show_api_debug = st.sidebar.checkbox("Show API debug status", value=True)
page = st.sidebar.radio("Choose page", ["Home Dashboard", "Real Bracket / Series", "Current Team Series", "Live Game Center", "All Games", "API Debug"])

if AUTOREFRESH_AVAILABLE:
    st.sidebar.success("Auto-refresh package installed")
else:
    st.sidebar.warning("streamlit-autorefresh not installed. Add it to requirements.txt for timed refresh.")

# Fetch real data
start_str = start_input.strftime("%Y-%m-%d") if hasattr(start_input, "strftime") else str(start_input)
end_str = end_input.strftime("%Y-%m-%d") if hasattr(end_input, "strftime") else str(end_input)
all_games, debug = fetch_real_nba_games(start_str, end_str)
series_list = build_series_from_games(all_games)
team_series = find_team_series(series_list, favorite_team)

# ==========================================================
# Pages
# ==========================================================
if page == "Home Dashboard":
    render_team_header(favorite_team, team_series)
    if show_api_debug:
        render_api_status(debug)
    c1, c2, c3 = st.columns(3)
    c1.metric("Games fetched", debug.get("games_found", 0))
    c2.metric("Final games fetched", debug.get("final_games_found", 0))
    c3.metric("Detected repeated matchups", len([s for s in series_list if s["num_games"] >= min_games_for_series]))
    st.divider()
    if team_series:
        st.subheader("Current / Most Relevant Series Scores")
        st.dataframe(pd.DataFrame(team_series["games"]), use_container_width=True)
        if team_series.get("last_game"):
            st.subheader("Previous Game Top Plays")
            plays = top_plays_for_game(team_series["last_game"].get("GameID", ""), favorite_team)
            if plays.empty:
                st.info("Top plays require live play-by-play availability for that GameID. If NBA live play-by-play is unavailable for the archived game, this section may be blank.")
            else:
                st.dataframe(plays, use_container_width=True)
        render_team_outlook(favorite_team, team_series)
    else:
        st.warning("No completed repeated matchup was found for this team in the selected date window. Expand the date range or check API Debug.")

elif page == "Real Bracket / Series":
    render_bracket(series_list)

elif page == "Current Team Series":
    render_team_header(favorite_team, team_series)
    render_team_outlook(favorite_team, team_series)
    if team_series:
        st.subheader("Game-by-game")
        st.dataframe(pd.DataFrame(team_series["games"]), use_container_width=True)
    related = [g for g in all_games if favorite_team in [g.get("Home"), g.get("Away")]]
    st.subheader(f"All fetched {favorite_team} games in date window")
    st.dataframe(pd.DataFrame(related), use_container_width=True)

elif page == "Live Game Center":
    render_team_header(favorite_team, team_series)
    render_live_game_center(favorite_team)

elif page == "All Games":
    st.subheader("All fetched NBA games")
    if all_games:
        df = pd.DataFrame(all_games)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download fetched games CSV", df.to_csv(index=False), file_name="nba_fetched_games.csv")
    else:
        st.warning("No games were fetched. Check API Debug.")

elif page == "API Debug":
    render_api_status(debug)
    st.subheader("Raw fetched games sample")
    st.dataframe(pd.DataFrame(all_games).head(100), use_container_width=True)
    st.markdown("### Requirements.txt")
    st.code("""streamlit
pandas
numpy
plotly
nba_api
streamlit-autorefresh
""", language="text")
    st.markdown("### What this mode means")
    st.info("This app now follows the real NBA schedule. If Knicks vs 76ers is not an actual completed series in NBA.com data, the app will not invent that series. It will show only real fetched games.")

st.divider()
st.caption("Real NBA mode | NBA API-first | no fictional bracket | refreshes while app is open | add streamlit-autorefresh for timed updates")
