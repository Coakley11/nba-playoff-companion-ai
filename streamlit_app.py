
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================================
# Optional packages
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
    from nba_api.stats.static import players as nba_players
    from nba_api.stats.endpoints import playergamelog, playercareerstats, scoreboardv2
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

# ==========================================================
# Page setup
# ==========================================================
st.set_page_config(page_title="Daniel Cohen — NBA Playoff Companion AI", page_icon="🏀", layout="wide")
st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 NBA Playoff companion app — live game center, automatic series tracking, bracket, box scores, and fan-focused analysis")

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fafc, #e5e7eb) !important;
    color: #111827 !important;
}
section[data-testid="stSidebar"] * { color: #111827 !important; }
section[data-testid="stSidebar"] label { font-size: 16px !important; font-weight: 800 !important; }
div[role="radiogroup"] label { padding: 9px 8px !important; border-radius: 12px !important; }
div[role="radiogroup"] label:hover { background-color: rgba(249,115,22,.18) !important; }
.player-card { text-align:center; border-radius:16px; padding:8px; border:1px solid rgba(0,0,0,.12); background:rgba(255,255,255,.75); }
.big-status { font-size: 20px; font-weight: 800; padding: 10px 12px; border-radius: 12px; background: #fff7ed; border: 1px solid #fed7aa; }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# Static team data / fallback data
# ==========================================================
TEAM_IDS = {
    "Atlanta Hawks": 1610612737, "Boston Celtics": 1610612738, "Cleveland Cavaliers": 1610612739,
    "Denver Nuggets": 1610612743, "Houston Rockets": 1610612745, "Los Angeles Lakers": 1610612747,
    "Minnesota Timberwolves": 1610612750, "New York Knicks": 1610612752, "Orlando Magic": 1610612753,
    "Philadelphia 76ers": 1610612755, "Phoenix Suns": 1610612756, "Portland Trail Blazers": 1610612757,
    "San Antonio Spurs": 1610612759, "Oklahoma City Thunder": 1610612760, "Toronto Raptors": 1610612761,
    "Detroit Pistons": 1610612765,
}
ID_TO_TEAM = {v: k for k, v in TEAM_IDS.items()}

TEAM_ALIASES = {
    "Detroit Pistons": "DET", "Orlando Magic": "ORL", "Cleveland Cavaliers": "CLE", "Toronto Raptors": "TOR",
    "New York Knicks": "NYK", "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Philadelphia 76ers": "PHI",
    "Oklahoma City Thunder": "OKC", "Phoenix Suns": "PHX", "San Antonio Spurs": "SAS", "Portland Trail Blazers": "POR",
    "Denver Nuggets": "DEN", "Minnesota Timberwolves": "MIN", "Los Angeles Lakers": "LAL", "Houston Rockets": "HOU",
}
ALIAS_TO_TEAM = {v: k for k, v in TEAM_ALIASES.items()}

TEAM_LOGOS = {team: f"https://cdn.nba.com/logos/nba/{tid}/primary/L/logo.svg" for team, tid in TEAM_IDS.items()}

TEAM_PROFILES = {
    "New York Knicks": {"seed":3,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"Philadelphia 76ers","first_round_opponent":"Atlanta Hawks","first_round_result":"Defeated Atlanta Hawks, 4-2","starters":["Jalen Brunson","Mikal Bridges","OG Anunoby","Josh Hart","Karl-Anthony Towns"],"subs":["Miles McBride","Mitchell Robinson","Jordan Clarkson","Landry Shamet","Jose Alvarado"],"strengths":["Brunson shot creation","Towns spacing","OG/Bridges wing defense","Hart rebounding"],"concerns":["Towns foul trouble","bench scoring consistency","overreliance on Brunson late"]},
    "Philadelphia 76ers": {"seed":7,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"New York Knicks","first_round_opponent":"Boston Celtics","first_round_result":"Defeated Boston Celtics, 4-3","starters":["Tyrese Maxey","VJ Edgecombe","Kelly Oubre Jr.","Paul George","Joel Embiid"],"subs":["Quentin Grimes","Andre Drummond","Kyle Lowry","Eric Gordon","Caleb Martin"],"strengths":["Embiid pressure","Maxey speed","Paul George wing scoring","free-throw pressure"],"concerns":["Embiid health","transition defense","bench depth"]},
    "Detroit Pistons": {"seed":1,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"Cleveland Cavaliers","first_round_opponent":"Orlando Magic","first_round_result":"Defeated Orlando Magic, 4-3","starters":["Cade Cunningham","Jaden Ivey","Ausar Thompson","Tobias Harris","Jalen Duren"],"subs":["Marcus Sasser","Isaiah Stewart","Simone Fontecchio","Malik Beasley","Ron Holland"],"strengths":["Cade Cunningham control","Duren rebounding","young athleticism","transition pressure"],"concerns":["late-game execution","playoff inexperience","half-court droughts"]},
    "Cleveland Cavaliers": {"seed":4,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"Detroit Pistons","first_round_opponent":"Toronto Raptors","first_round_result":"Defeated Toronto Raptors, 4-3","starters":["Darius Garland","Donovan Mitchell","Max Strus","Evan Mobley","Jarrett Allen"],"subs":["Caris LeVert","Isaac Okoro","Georges Niang","Sam Merrill","Dean Wade"],"strengths":["Mitchell shot creation","Garland playmaking","Mobley/Allen rim protection","shooting around the guards"],"concerns":["offensive droughts","health","turnovers"]},
    "Oklahoma City Thunder": {"seed":1,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"Los Angeles Lakers","first_round_opponent":"Phoenix Suns","first_round_result":"Defeated Phoenix Suns, 4-0","starters":["Shai Gilgeous-Alexander","Lu Dort","Jalen Williams","Chet Holmgren","Isaiah Hartenstein"],"subs":["Cason Wallace","Aaron Wiggins","Isaiah Joe","Jaylin Williams","Kenrich Williams"],"strengths":["SGA creation","Chet rim protection","spacing","pace"],"concerns":["Lakers size","physicality","late-game pressure"]},
    "Los Angeles Lakers": {"seed":4,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"Oklahoma City Thunder","first_round_opponent":"Houston Rockets","first_round_result":"Defeated Houston Rockets, 4-2","starters":["D'Angelo Russell","Austin Reaves","LeBron James","Rui Hachimura","Anthony Davis"],"subs":["Gabe Vincent","Jarred Vanderbilt","Max Christie","Christian Wood","Jaxson Hayes"],"strengths":["LeBron control","Anthony Davis defense","rim pressure","playoff experience"],"concerns":["transition defense","age","three-point consistency"]},
    "San Antonio Spurs": {"seed":2,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"Minnesota Timberwolves","first_round_opponent":"Portland Trail Blazers","first_round_result":"Defeated Portland Trail Blazers, 4-1","starters":["Stephon Castle","Devin Vassell","Keldon Johnson","Jeremy Sochan","Victor Wembanyama"],"subs":["Tre Jones","Julian Champagnie","Zach Collins","Malaki Branham","Blake Wesley"],"strengths":["Wembanyama two-way impact","length","rim protection","young talent"],"concerns":["turnovers","playoff inexperience","foul trouble"]},
    "Minnesota Timberwolves": {"seed":6,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"San Antonio Spurs","first_round_opponent":"Denver Nuggets","first_round_result":"Defeated Denver Nuggets, 4-2","starters":["Mike Conley","Anthony Edwards","Jaden McDaniels","Naz Reid","Rudy Gobert"],"subs":["Nickeil Alexander-Walker","Donte DiVincenzo","Rob Dillingham","Josh Minott","Luka Garza"],"strengths":["Edwards scoring","Gobert/McDaniels defense","Naz Reid spacing","physicality"],"concerns":["late-game offense","spacing","foul trouble"]},
}
# Eliminated teams
ELIMINATED_INFO = [
    ("Atlanta Hawks",6,"Eastern Conference","New York Knicks","Lost to New York Knicks, 4-2",["Trae Young","Dyson Daniels","Zaccharie Risacher","Jalen Johnson","Onyeka Okongwu"],["Bogdan Bogdanovic","De'Andre Hunter","Clint Capela","Vit Krejci","Kobe Bufkin"]),
    ("Boston Celtics",2,"Eastern Conference","Philadelphia 76ers","Lost to Philadelphia 76ers, 4-3",["Jrue Holiday","Derrick White","Jaylen Brown","Jayson Tatum","Kristaps Porzingis"],["Payton Pritchard","Sam Hauser","Al Horford","Luke Kornet","Neemias Queta"]),
    ("Orlando Magic",8,"Eastern Conference","Detroit Pistons","Lost to Detroit Pistons, 4-3",["Jalen Suggs","Kentavious Caldwell-Pope","Franz Wagner","Paolo Banchero","Wendell Carter Jr."],["Cole Anthony","Jonathan Isaac","Anthony Black","Moritz Wagner","Gary Harris"]),
    ("Toronto Raptors",5,"Eastern Conference","Cleveland Cavaliers","Lost to Cleveland Cavaliers, 4-3",["Immanuel Quickley","RJ Barrett","Gradey Dick","Scottie Barnes","Jakob Poeltl"],["Bruce Brown","Kelly Olynyk","Ochai Agbaji","Chris Boucher","Davion Mitchell"]),
    ("Phoenix Suns",8,"Western Conference","Oklahoma City Thunder","Lost to Oklahoma City Thunder, 4-0",["Devin Booker","Bradley Beal","Grayson Allen","Kevin Durant","Jusuf Nurkic"],["Royce O'Neale","Eric Gordon","Bol Bol","Drew Eubanks","Josh Okogie"]),
    ("Portland Trail Blazers",7,"Western Conference","San Antonio Spurs","Lost to San Antonio Spurs, 4-1",["Scoot Henderson","Anfernee Simons","Shaedon Sharpe","Jerami Grant","Deandre Ayton"],["Toumani Camara","Matisse Thybulle","Robert Williams III","Dalano Banton","Kris Murray"]),
    ("Denver Nuggets",3,"Western Conference","Minnesota Timberwolves","Lost to Minnesota Timberwolves, 4-2",["Jamal Murray","Christian Braun","Michael Porter Jr.","Aaron Gordon","Nikola Jokic"],["Reggie Jackson","Peyton Watson","Zeke Nnaji","Julian Strawther","DeAndre Jordan"]),
    ("Houston Rockets",5,"Western Conference","Los Angeles Lakers","Lost to Los Angeles Lakers, 4-2",["Fred VanVleet","Jalen Green","Amen Thompson","Jabari Smith Jr.","Alperen Sengun"],["Dillon Brooks","Tari Eason","Cam Whitmore","Steven Adams","Reed Sheppard"]),
]
for name, seed, conf, opp, result, starters, subs in ELIMINATED_INFO:
    TEAM_PROFILES[name] = {"seed":seed,"conference":conf,"status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":opp,"first_round_result":result,"starters":starters,"subs":subs,"strengths":["main star creation","transition chances","playoff experience"],"concerns":["series ended in first round","needs depth/defense improvements","late-game consistency"]}

FIRST_ROUND_SERIES = {
    "DET-ORL": {"conf":"East","a":"Detroit Pistons","b":"Orlando Magic","a_wins":4,"b_wins":3,"winner":"Detroit Pistons"},
    "CLE-TOR": {"conf":"East","a":"Cleveland Cavaliers","b":"Toronto Raptors","a_wins":4,"b_wins":3,"winner":"Cleveland Cavaliers"},
    "NYK-ATL": {"conf":"East","a":"New York Knicks","b":"Atlanta Hawks","a_wins":4,"b_wins":2,"winner":"New York Knicks"},
    "BOS-PHI": {"conf":"East","a":"Boston Celtics","b":"Philadelphia 76ers","a_wins":3,"b_wins":4,"winner":"Philadelphia 76ers"},
    "OKC-PHX": {"conf":"West","a":"Oklahoma City Thunder","b":"Phoenix Suns","a_wins":4,"b_wins":0,"winner":"Oklahoma City Thunder"},
    "SAS-POR": {"conf":"West","a":"San Antonio Spurs","b":"Portland Trail Blazers","a_wins":4,"b_wins":1,"winner":"San Antonio Spurs"},
    "DEN-MIN": {"conf":"West","a":"Denver Nuggets","b":"Minnesota Timberwolves","a_wins":2,"b_wins":4,"winner":"Minnesota Timberwolves"},
    "LAL-HOU": {"conf":"West","a":"Los Angeles Lakers","b":"Houston Rockets","a_wins":4,"b_wins":2,"winner":"Los Angeles Lakers"},
}

# Fallback second-round state. API results override/supplement these when available.
SECOND_ROUND_SERIES_FALLBACK = {
    "DET-CLE": {"conf":"East","a":"Detroit Pistons","b":"Cleveland Cavaliers","a_wins":1,"b_wins":0,"winner":None,"games":[{"Game":"Game 1","Date":"","Score":"Pistons 111, Cavaliers 101","Winner":"Detroit Pistons","GameID":""}]},
    "NYK-PHI": {"conf":"East","a":"New York Knicks","b":"Philadelphia 76ers","a_wins":1,"b_wins":0,"winner":None,"games":[{"Game":"Game 1","Date":"","Score":"Knicks 137, 76ers 98","Winner":"New York Knicks","GameID":""}]},
    "OKC-LAL": {"conf":"West","a":"Oklahoma City Thunder","b":"Los Angeles Lakers","a_wins":0,"b_wins":0,"winner":None,"games":[]},
    "SAS-MIN": {"conf":"West","a":"San Antonio Spurs","b":"Minnesota Timberwolves","a_wins":0,"b_wins":1,"winner":None,"games":[{"Game":"Game 1","Date":"","Score":"Timberwolves 104, Spurs 102","Winner":"Minnesota Timberwolves","GameID":""}]},
}

FIRST_ROUND_GAME_SCORES = {
    "Detroit Pistons": [
        {"Game":1,"Date":"Apr 18","Matchup":"Magic at Pistons","Score":"Magic 112, Pistons 101","Winner":"Orlando Magic"},
        {"Game":2,"Date":"Apr 21","Matchup":"Magic at Pistons","Score":"Pistons 98, Magic 83","Winner":"Detroit Pistons"},
        {"Game":3,"Date":"Apr 24","Matchup":"Pistons at Magic","Score":"Magic 113, Pistons 105","Winner":"Orlando Magic"},
        {"Game":4,"Date":"Apr 26","Matchup":"Pistons at Magic","Score":"Magic 94, Pistons 88","Winner":"Orlando Magic"},
        {"Game":5,"Date":"Apr 29","Matchup":"Magic at Pistons","Score":"Pistons 116, Magic 109","Winner":"Detroit Pistons"},
        {"Game":6,"Date":"May 1","Matchup":"Pistons at Magic","Score":"Pistons 93, Magic 79","Winner":"Detroit Pistons"},
        {"Game":7,"Date":"May 3","Matchup":"Magic at Pistons","Score":"Pistons 116, Magic 94","Winner":"Detroit Pistons"},
    ],
    "Cleveland Cavaliers": [
        {"Game":1,"Date":"Apr 19","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 126, Raptors 113","Winner":"Cleveland Cavaliers"},
        {"Game":2,"Date":"Apr 22","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 115, Raptors 105","Winner":"Cleveland Cavaliers"},
        {"Game":3,"Date":"Apr 25","Matchup":"Cavaliers at Raptors","Score":"Raptors 126, Cavaliers 104","Winner":"Toronto Raptors"},
        {"Game":4,"Date":"Apr 27","Matchup":"Cavaliers at Raptors","Score":"Raptors 93, Cavaliers 89","Winner":"Toronto Raptors"},
        {"Game":5,"Date":"Apr 29","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 125, Raptors 120","Winner":"Cleveland Cavaliers"},
        {"Game":6,"Date":"May 1","Matchup":"Cavaliers at Raptors","Score":"Raptors 112, Cavaliers 110","Winner":"Toronto Raptors"},
        {"Game":7,"Date":"May 3","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 114, Raptors 102","Winner":"Cleveland Cavaliers"},
    ],
    "New York Knicks": [
        {"Game":1,"Date":"Apr 19","Matchup":"Hawks at Knicks","Score":"Knicks 113, Hawks 102","Winner":"New York Knicks"},
        {"Game":2,"Date":"Apr 22","Matchup":"Hawks at Knicks","Score":"Hawks 107, Knicks 106","Winner":"Atlanta Hawks"},
        {"Game":3,"Date":"Apr 25","Matchup":"Knicks at Hawks","Score":"Hawks 109, Knicks 108","Winner":"Atlanta Hawks"},
        {"Game":4,"Date":"Apr 27","Matchup":"Knicks at Hawks","Score":"Knicks 114, Hawks 98","Winner":"New York Knicks"},
        {"Game":5,"Date":"Apr 29","Matchup":"Hawks at Knicks","Score":"Knicks 126, Hawks 97","Winner":"New York Knicks"},
        {"Game":6,"Date":"May 1","Matchup":"Knicks at Hawks","Score":"Knicks 140, Hawks 89","Winner":"New York Knicks"},
    ],
    "Boston Celtics": [
        {"Game":1,"Date":"Apr 18","Matchup":"76ers at Celtics","Score":"Celtics 123, 76ers 91","Winner":"Boston Celtics"},
        {"Game":2,"Date":"Apr 21","Matchup":"76ers at Celtics","Score":"76ers 111, Celtics 97","Winner":"Philadelphia 76ers"},
        {"Game":3,"Date":"Apr 24","Matchup":"Celtics at 76ers","Score":"Celtics 108, 76ers 100","Winner":"Boston Celtics"},
        {"Game":4,"Date":"Apr 26","Matchup":"Celtics at 76ers","Score":"Celtics 128, 76ers 96","Winner":"Boston Celtics"},
        {"Game":5,"Date":"Apr 28","Matchup":"76ers at Celtics","Score":"76ers 113, Celtics 97","Winner":"Philadelphia 76ers"},
        {"Game":6,"Date":"Apr 30","Matchup":"Celtics at 76ers","Score":"76ers 106, Celtics 93","Winner":"Philadelphia 76ers"},
        {"Game":7,"Date":"May 2","Matchup":"76ers at Celtics","Score":"76ers 109, Celtics 100","Winner":"Philadelphia 76ers"},
    ],
    "Oklahoma City Thunder": [
        {"Game":1,"Date":"Apr 18","Matchup":"Suns at Thunder","Score":"Thunder 119, Suns 84","Winner":"Oklahoma City Thunder"},
        {"Game":2,"Date":"Apr 20","Matchup":"Suns at Thunder","Score":"Thunder 120, Suns 107","Winner":"Oklahoma City Thunder"},
        {"Game":3,"Date":"Apr 23","Matchup":"Thunder at Suns","Score":"Thunder 121, Suns 109","Winner":"Oklahoma City Thunder"},
        {"Game":4,"Date":"Apr 25","Matchup":"Thunder at Suns","Score":"Thunder 131, Suns 122","Winner":"Oklahoma City Thunder"},
    ],
    "San Antonio Spurs": [
        {"Game":1,"Date":"Apr 19","Matchup":"Trail Blazers at Spurs","Score":"Spurs 111, Trail Blazers 98","Winner":"San Antonio Spurs"},
        {"Game":2,"Date":"Apr 22","Matchup":"Trail Blazers at Spurs","Score":"Trail Blazers 106, Spurs 103","Winner":"Portland Trail Blazers"},
        {"Game":3,"Date":"Apr 24","Matchup":"Spurs at Trail Blazers","Score":"Spurs 120, Trail Blazers 108","Winner":"San Antonio Spurs"},
        {"Game":4,"Date":"Apr 26","Matchup":"Spurs at Trail Blazers","Score":"Spurs 114, Trail Blazers 93","Winner":"San Antonio Spurs"},
        {"Game":5,"Date":"Apr 28","Matchup":"Trail Blazers at Spurs","Score":"Spurs 114, Trail Blazers 95","Winner":"San Antonio Spurs"},
    ],
    "Denver Nuggets": [
        {"Game":1,"Date":"Apr 19","Matchup":"Timberwolves at Nuggets","Score":"Nuggets 116, Timberwolves 105","Winner":"Denver Nuggets"},
        {"Game":2,"Date":"Apr 21","Matchup":"Timberwolves at Nuggets","Score":"Timberwolves 119, Nuggets 114","Winner":"Minnesota Timberwolves"},
        {"Game":3,"Date":"Apr 24","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 113, Nuggets 96","Winner":"Minnesota Timberwolves"},
        {"Game":4,"Date":"Apr 26","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 112, Nuggets 96","Winner":"Minnesota Timberwolves"},
        {"Game":5,"Date":"Apr 29","Matchup":"Timberwolves at Nuggets","Score":"Nuggets 125, Timberwolves 113","Winner":"Denver Nuggets"},
        {"Game":6,"Date":"May 1","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 110, Nuggets 98","Winner":"Minnesota Timberwolves"},
    ],
    "Los Angeles Lakers": [
        {"Game":1,"Date":"Apr 18","Matchup":"Rockets at Lakers","Score":"Lakers 107, Rockets 98","Winner":"Los Angeles Lakers"},
        {"Game":2,"Date":"Apr 20","Matchup":"Rockets at Lakers","Score":"Lakers 101, Rockets 94","Winner":"Los Angeles Lakers"},
        {"Game":3,"Date":"Apr 23","Matchup":"Lakers at Rockets","Score":"Lakers 112, Rockets 108 (OT)","Winner":"Los Angeles Lakers"},
        {"Game":4,"Date":"Apr 25","Matchup":"Lakers at Rockets","Score":"Rockets 116, Lakers 96","Winner":"Houston Rockets"},
        {"Game":5,"Date":"Apr 28","Matchup":"Rockets at Lakers","Score":"Rockets 99, Lakers 93","Winner":"Houston Rockets"},
        {"Game":6,"Date":"Apr 30","Matchup":"Lakers at Rockets","Score":"Lakers 98, Rockets 78","Winner":"Los Angeles Lakers"},
    ],
}
for mirror, source in [("Orlando Magic","Detroit Pistons"),("Toronto Raptors","Cleveland Cavaliers"),("Atlanta Hawks","New York Knicks"),("Philadelphia 76ers","Boston Celtics"),("Phoenix Suns","Oklahoma City Thunder"),("Portland Trail Blazers","San Antonio Spurs"),("Minnesota Timberwolves","Denver Nuggets"),("Houston Rockets","Los Angeles Lakers")]:
    FIRST_ROUND_GAME_SCORES[mirror] = FIRST_ROUND_GAME_SCORES[source]

FALLBACK_TOP_PLAYS = {
    "New York Knicks": [
        {"Game":"Game 1 vs 76ers","Top Play":"Jalen Brunson controlled the half court early and repeatedly got New York into high-quality possessions.","Why it mattered":"It gave the Knicks control of the game and forced Philadelphia to chase."},
        {"Game":"Game 1 vs 76ers","Top Play":"OG Anunoby and Mikal Bridges pressured Philadelphia's wings and disrupted clean perimeter rhythm.","Why it mattered":"It helped the Knicks turn defensive possessions into control of the game."},
        {"Game":"Game 1 vs 76ers","Top Play":"Karl-Anthony Towns' spacing pulled size away from the rim and opened driving lanes.","Why it mattered":"It made the Knicks offense harder to load up against."},
    ],
    "Minnesota Timberwolves": [
        {"Game":"Game 1 vs Spurs","Top Play":"Anthony Edwards delivered late-game shot creation in a tight finish.","Why it mattered":"It gave Minnesota a reliable option when the game tightened."},
        {"Game":"Game 1 vs Spurs","Top Play":"Minnesota's defensive length contested San Antonio's key looks near the rim and on the wing.","Why it mattered":"Those stops protected the narrow win."},
    ],
    "Detroit Pistons": [{"Game":"Game 1 vs Cavaliers","Top Play":"Cade Cunningham organized Detroit's offense and kept the Pistons composed.","Why it mattered":"It helped Detroit take the early series lead."}],
}

# ==========================================================
# API / automatic tracking helpers
# ==========================================================
def safe_int(x, default=0):
    try: return int(x or default)
    except Exception: return default

def safe_float(x, default=0.0):
    try: return float(x or default)
    except Exception: return default

@st.cache_data(ttl=900)
def fetch_completed_games_recent(days_back=14, days_forward=1):
    """Attempts to pull recent completed NBA games from scoreboardv2. Falls back safely if unavailable."""
    if not NBA_STATS_AVAILABLE:
        return []
    records = []
    today = datetime.now().date()
    for i in range(-days_back, days_forward + 1):
        d = today + timedelta(days=i)
        date_str = d.strftime("%m/%d/%Y")
        try:
            df = scoreboardv2.ScoreboardV2(game_date=date_str).get_data_frames()[0]
        except Exception:
            continue
        if df.empty:
            continue
        for _, r in df.iterrows():
            status = str(r.get("GAME_STATUS_TEXT", ""))
            if "Final" not in status:
                continue
            home_id = safe_int(r.get("HOME_TEAM_ID"))
            away_id = safe_int(r.get("VISITOR_TEAM_ID"))
            home = ID_TO_TEAM.get(home_id)
            away = ID_TO_TEAM.get(away_id)
            if not home or not away:
                continue
            home_pts = safe_int(r.get("PTS_HOME"))
            away_pts = safe_int(r.get("PTS_AWAY"))
            winner = home if home_pts > away_pts else away if away_pts > home_pts else None
            records.append({
                "GameID": str(r.get("GAME_ID", "")),
                "Date": d.strftime("%b %-d") if hasattr(d, 'strftime') else str(d),
                "Home": home, "Away": away,
                "HomeScore": home_pts, "AwayScore": away_pts,
                "Winner": winner,
                "Score": f"{away} {away_pts}, {home} {home_pts}",
                "Matchup": f"{away} at {home}",
            })
    return records

def series_key_for_pair(t1, t2):
    pair = {t1, t2}
    for key, s in SECOND_ROUND_SERIES_FALLBACK.items():
        if {s["a"], s["b"]} == pair:
            return key
    return None

@st.cache_data(ttl=300)
def build_second_round_series():
    """Builds current second-round state from API completed games when possible, with fallback data if API fails."""
    dynamic = {k: {**v, "games": list(v.get("games", []))} for k, v in SECOND_ROUND_SERIES_FALLBACK.items()}
    api_games = fetch_completed_games_recent()
    grouped = {k: [] for k in dynamic}
    for g in api_games:
        key = series_key_for_pair(g["Home"], g["Away"])
        if key:
            grouped[key].append(g)
    for key, games in grouped.items():
        if not games:
            continue
        # Sort by date text not perfect; keep API order by query date and de-dupe by GameID.
        seen = set(); clean = []
        for g in games:
            ident = g.get("GameID") or (g["Date"] + g["Matchup"])
            if ident in seen: continue
            seen.add(ident); clean.append(g)
        s = dynamic[key]
        a, b = s["a"], s["b"]
        a_wins = sum(1 for g in clean if g["Winner"] == a)
        b_wins = sum(1 for g in clean if g["Winner"] == b)
        s["a_wins"], s["b_wins"] = a_wins, b_wins
        s["winner"] = a if a_wins >= 4 else b if b_wins >= 4 else None
        s["games"] = []
        for idx, g in enumerate(clean, start=1):
            s["games"].append({"Game": f"Game {idx}", "Date": g.get("Date",""), "Score": g["Score"], "Winner": g["Winner"], "GameID": g.get("GameID","")})
    return dynamic

def series_for_team(team_name):
    for key, s in build_second_round_series().items():
        if team_name in [s["a"], s["b"]]:
            return key, s
    return None, None

def series_status_text(team_name):
    _, s = series_for_team(team_name)
    if not s: return "No active series"
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    team_w = aw if team_name == a else bw
    opp = b if team_name == a else a
    opp_w = bw if team_name == a else aw
    verb = "leads" if team_w > opp_w else "trails" if team_w < opp_w else "tied"
    return f"{TEAM_ALIASES[team_name]} {verb} {team_w}-{opp_w} vs {TEAM_ALIASES[opp]}"

def historic_series_context(team_name):
    _, s = series_for_team(team_name)
    if not s: return pd.DataFrame()
    a, b = s["a"], s["b"]
    tw = s["a_wins"] if team_name == a else s["b_wins"]
    ow = s["b_wins"] if team_name == a else s["a_wins"]
    if tw == 1 and ow == 0:
        note = "Winning Game 1 improves the series outlook; Game 2 can create a major 2-0 advantage."
    elif tw == 2 and ow == 0:
        note = "A 2-0 lead is historically a very strong best-of-seven position."
    elif tw == 1 and ow == 1:
        note = "At 1-1, the series is close to a reset; Game 3 becomes a swing game."
    elif tw < ow:
        note = "The team is trailing and needs to change the series momentum quickly."
    elif tw == 0 and ow == 0:
        note = "No completed second-round game detected yet. Game 1 sets the tone."
    else:
        note = "The team has the series edge, but must keep winning possession battles to close it out."
    return pd.DataFrame([{"Series Status": series_status_text(team_name), "Historical Context": note}])

@st.cache_data(ttl=30)
def get_live_games():
    if not NBA_LIVE_AVAILABLE: return []
    try: return scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", [])
    except Exception: return []

def find_live_game_for_team(team_name):
    alias = TEAM_ALIASES.get(team_name)
    for g in get_live_games():
        home = g.get("homeTeam", {}); away = g.get("awayTeam", {})
        if home.get("teamTricode") == alias or away.get("teamTricode") == alias:
            return g
    return None

@st.cache_data(ttl=30)
def get_live_boxscore(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id: return {}
    try: return boxscore.BoxScore(game_id).get_dict().get("game", {})
    except Exception: return {}

@st.cache_data(ttl=30)
def get_live_playbyplay(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id: return []
    try: return playbyplay.PlayByPlay(game_id).get_dict().get("game", {}).get("actions", [])
    except Exception: return []

@st.cache_data(ttl=1800)
def get_playbyplay_by_game_id(game_id):
    return get_live_playbyplay(game_id)

@st.cache_data(ttl=3600)
def get_player_id(name):
    if not NBA_STATS_AVAILABLE: return None
    try:
        matches = [p for p in nba_players.get_players() if p["full_name"] == name]
        return matches[0]["id"] if matches else None
    except Exception: return None

@st.cache_data(ttl=86400)
def season_averages(name):
    pid = get_player_id(name)
    if not pid or not NBA_STATS_AVAILABLE: return {"PTS":"--","REB":"--","AST":"--","STL":"--","BLK":"--"}
    try:
        df = playercareerstats.PlayerCareerStats(player_id=pid).get_data_frames()[0]
        if df.empty: return {"PTS":"--","REB":"--","AST":"--","STL":"--","BLK":"--"}
        r = df.iloc[-1]; gp = max(float(r.get("GP", 1)), 1)
        return {k: round(float(r.get(k, 0)) / gp, 1) for k in ["PTS","REB","AST","STL","BLK"]}
    except Exception: return {"PTS":"--","REB":"--","AST":"--","STL":"--","BLK":"--"}

def headshot(name):
    pid = get_player_id(name)
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png" if pid else "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"

# ==========================================================
# Analysis / visualization helpers
# ==========================================================
def create_boxscore_df(game_box):
    rows = []
    for side in ["homeTeam", "awayTeam"]:
        t = game_box.get(side, {})
        tri = t.get("teamTricode", "")
        for p in t.get("players", []):
            stt = p.get("statistics", {})
            rows.append({"Team":tri,"Player":p.get("name",""),"MIN":stt.get("minutes",""),"PTS":stt.get("points",0),"REB":stt.get("reboundsTotal",0),"AST":stt.get("assists",0),"STL":stt.get("steals",0),"BLK":stt.get("blocks",0),"TO":stt.get("turnovers",0),"PF":stt.get("foulsPersonal",0),"FGM":stt.get("fieldGoalsMade",0),"FGA":stt.get("fieldGoalsAttempted",0),"3PM":stt.get("threePointersMade",0),"3PA":stt.get("threePointersAttempted",0),"+/-":stt.get("plusMinusPoints",0)})
    return pd.DataFrame(rows)

def min_to_float(v):
    try:
        if isinstance(v, str) and ":" in v:
            m, s = v.split(":"); return float(m) + float(s)/60
        return float(v)
    except Exception: return 0.0

def estimated_lineup(box_df, alias, team_name):
    df = box_df[box_df["Team"] == alias].copy() if not box_df.empty else pd.DataFrame()
    if df.empty:
        return pd.DataFrame([{"Team":alias,"Player":p,"MIN":"0:00","PTS":0,"REB":0,"AST":0,"STL":0,"BLK":0,"PF":0,"FGM":0,"FGA":0} for p in TEAM_PROFILES[team_name]["starters"]])
    df["MIN_FLOAT"] = df["MIN"].apply(min_to_float)
    return df.sort_values("MIN_FLOAT", ascending=False).head(5)

def player_temp(r):
    fga = safe_float(r.get("FGA")); fgm = safe_float(r.get("FGM")); pts = safe_float(r.get("PTS"))
    pct = fgm/fga if fga else 0
    if pts >= 18 and pct >= .50: return "🔥"
    if fga >= 8 and pct <= .30: return "❄️"
    return ""

def win_prob(margin, period, is_home):
    w = {1:1.2, 2:1.8, 3:2.8, 4:4.5}.get(max(1,min(safe_int(period,1),4)), 4.5)
    return int(max(1, min(99, round(50 + margin*w + (2.5 if is_home else 0)))))

def shot_df_from_pbp(actions, alias):
    rows=[]; rng=np.random.default_rng(17)
    for a in actions:
        tri = a.get("teamTricode") or ""
        if tri != alias: continue
        desc = a.get("description", "") or ""
        d = desc.lower()
        if not any(x in d for x in ["miss", "made", "makes", "layup", "dunk", "3pt", "shot"]): continue
        made = ("made" in d or "makes" in d) and "miss" not in d
        player = a.get("personName") or a.get("playerName") or "Unknown"
        if "3pt" in d or "three" in d:
            x, y = float(rng.uniform(-22,22)), float(rng.uniform(22,31))
        elif "layup" in d or "dunk" in d:
            x, y = float(rng.uniform(-5,5)), float(rng.uniform(1,8))
        else:
            x, y = float(rng.uniform(-16,16)), float(rng.uniform(8,22))
        rows.append({"Player":player,"Made":made,"x":x,"y":y,"Description":desc})
    return pd.DataFrame(rows)

def draw_court(shots, title):
    fig=go.Figure()
    fig.update_layout(title=title,height=620,plot_bgcolor="#c68642",paper_bgcolor="#f3d3a3",font=dict(color="#111827"),xaxis=dict(range=[-27,27],visible=False),yaxis=dict(range=[0,50],visible=False),legend=dict(orientation="h"),margin=dict(l=20,r=20,t=55,b=20))
    line=dict(color="#5c2e0e",width=3)
    for shape in [dict(type="rect",x0=-25,y0=0,x1=25,y1=47),dict(type="rect",x0=-8,y0=0,x1=8,y1=19),dict(type="circle",x0=-6,y0=-1,x1=6,y1=11),dict(type="circle",x0=-23.75,y0=0,x1=23.75,y1=47.5)]:
        fig.add_shape(**shape,line=line)
    fig.add_shape(type="line",x0=-22,y0=0,x1=-22,y1=14,line=line); fig.add_shape(type="line",x0=22,y0=0,x1=22,y1=14,line=line)
    if not shots.empty:
        made=shots[shots["Made"]==True]; miss=shots[shots["Made"]==False]
        fig.add_trace(go.Scatter(x=made["x"],y=made["y"],mode="markers",name="Made O",text=made["Description"],marker=dict(symbol="circle-open",color="#0047FF",size=18,line=dict(width=5,color="#0047FF"))))
        fig.add_trace(go.Scatter(x=miss["x"],y=miss["y"],mode="markers",name="Missed X",text=miss["Description"],marker=dict(symbol="x",color="#E00000",size=17,line=dict(width=5,color="#E00000"))))
    return fig

def is_top_play(desc):
    d=(desc or "").lower()
    if any(x in d for x in ["free throw", "personal foul", "timeout", "substitution", "violation", "delay"]): return False
    return any(x in d for x in ["dunk", "alley", "3pt", "three", "steal", "block", "fast break", "putback", "driving layup", "go-ahead", "ties", "step back"])

def explain_play(desc, team):
    d=(desc or "").lower()
    if "3pt" in d or "three" in d: return f"It was a high-value shot that changed spacing and scoreboard pressure for {team}."
    if "dunk" in d or "layup" in d or "alley" in d: return f"It showed efficient rim pressure for {team}."
    if "steal" in d: return "It created a turnover and a chance to run."
    if "block" in d: return "It protected the rim and stopped a quality look."
    return "It was one of the highest-impact plays available in the play-by-play feed."

def top_plays_from_game_id(game_id, team_name, limit=5):
    alias=TEAM_ALIASES[team_name]
    actions=get_playbyplay_by_game_id(game_id) if game_id else []
    rows=[]
    for a in actions:
        if (a.get("teamTricode") or "") != alias: continue
        desc=a.get("description","") or ""
        if not is_top_play(desc): continue
        rows.append({"Period":a.get("period",""),"Clock":a.get("clock",""),"Top Play":desc,"Why it mattered":explain_play(desc,team_name)})
    if rows: return pd.DataFrame(rows[-limit:])
    return pd.DataFrame(FALLBACK_TOP_PLAYS.get(team_name, [{"Game":"Previous game","Top Play":f"{team_name}'s key plays will appear here when play-by-play data is available.","Why it mattered":"Fallback shown because the API did not return detailed play-by-play for the previous game."}]))

def previous_game_top_plays(team_name):
    _, s = series_for_team(team_name)
    if s and s.get("games"):
        last=s["games"][-1]
        df=top_plays_from_game_id(last.get("GameID",""), team_name)
        if "Game" not in df.columns:
            df.insert(0,"Game",last.get("Game","Previous Game"))
        return df
    return pd.DataFrame(FALLBACK_TOP_PLAYS.get(team_name, []))

def game_story(team_name, margin, prob, box_df):
    alias=TEAM_ALIASES[team_name]
    if box_df.empty: return ["Live box score has not loaded yet."]
    df=box_df[box_df["Team"]==alias]
    lines=[]
    lines.append(f"{team_name} is {'ahead' if margin>0 else 'tied' if margin==0 else 'behind'} by {abs(margin)}.")
    lines.append(f"Tracked team line: {df['PTS'].sum()} points, {df['REB'].sum()} rebounds, {df['AST'].sum()} assists.")
    lines.append("The next stretch should focus on stops, clean possessions, and avoiding foul trouble.")
    return lines

def matchup_advantages(team, opp):
    t=TEAM_PROFILES[team]; o=TEAM_PROFILES[opp]
    positions=["PG","SG","SF","PF","C"]
    rows=[]
    for i,pos in enumerate(positions):
        tp=t["starters"][i]; op=o["starters"][i]
        if "Brunson" in tp or "Mitchell" in tp or "Shai" in tp or "Edwards" in tp or "LeBron" in tp or "Embiid" in tp or "Wembanyama" in tp:
            adv=team; why=f"{tp} is a primary playoff creator/anchor in this matchup."
        elif "Embiid" in op or "Mitchell" in op or "Shai" in op or "Edwards" in op or "LeBron" in op or "Wembanyama" in op:
            adv=opp; why=f"{op} has the bigger star-impact edge at this spot."
        else:
            adv="Close"; why="This position depends on shooting, defense, foul trouble, and role-player consistency."
        rows.append({"Position":pos, team:tp, opp:op, "Advantage":adv, "Why":why})
    return pd.DataFrame(rows)

# ==========================================================
# Rendering helpers
# ==========================================================
def render_matchup_header(team_name, first_round=False):
    p=TEAM_PROFILES[team_name]
    opp=p["first_round_opponent"] if first_round else (p.get("current_opponent") or p["first_round_opponent"])
    round_label="Previous Rounds / First Round Review" if first_round else p["round"]
    header=f"{p['conference']} {round_label}"
    c1,c2,c3=st.columns([1,2.5,1])
    with c1: st.image(TEAM_LOGOS[team_name], width=105)
    with c2:
        st.markdown(f"<div style='text-align:center'><h1>({p['seed']}) {team_name} vs ({TEAM_PROFILES[opp]['seed']}) {opp}</h1><h3>{header}</h3></div>", unsafe_allow_html=True)
    with c3: st.image(TEAM_LOGOS[opp], width=105)

def team_logo_html(team,size=28):
    return f"<img src='{TEAM_LOGOS[team]}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"

def series_card(s, round_name):
    a,b=s["a"],s["b"]; aw,bw=s["a_wins"],s["b_wins"]
    winner=s.get("winner")
    note="Final" if winner else "In progress"
    return f"""
    <div class='series-card'>
      <div class='team-row'><div>{team_logo_html(a)} <b>{TEAM_PROFILES[a]['seed']}</b> {a}</div><div class='wins'>{aw}</div></div>
      <div class='team-row'><div>{team_logo_html(b)} <b>{TEAM_PROFILES[b]['seed']}</b> {b}</div><div class='wins'>{bw}</div></div>
      <div class='series-note'>{round_name} · {note}</div>
    </div>
    """

def render_bracket():
    if AUTOREFRESH_AVAILABLE: st_autorefresh(interval=30000, key="bracket_refresh")
    st.markdown("""
    <style>
    .bracket-wrap{background:linear-gradient(135deg,#07111f,#10213d,#301a55);padding:22px;border-radius:22px;border:1px solid rgba(255,255,255,.16);color:white;}
    .bracket-title{text-align:center;font-size:34px;font-weight:900;margin-bottom:8px}.bracket-sub{text-align:center;color:#cbd5e1;margin-bottom:20px}
    .bracket-grid{display:grid;grid-template-columns:1.25fr 1fr .85fr 1fr 1.25fr;gap:14px;align-items:center}.conf-title{text-align:center;font-size:22px;font-weight:900;padding:8px;background:rgba(255,255,255,.08);border-radius:14px;margin-bottom:10px}.round-title{text-align:center;font-size:15px;color:#93c5fd;font-weight:800;margin-bottom:8px}.series-card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:10px 12px;margin:9px 0;min-height:80px}.team-row{display:flex;align-items:center;justify-content:space-between;padding:3px 0;font-size:14px}.wins{font-weight:900;font-size:17px;color:#fbbf24}.series-note{text-align:center;color:#93c5fd;font-size:12px;margin-top:5px}.finals-box{background:radial-gradient(circle at top,#fbbf24,#1f2937 45%,#111827);border:1px solid rgba(255,255,255,.18);border-radius:22px;padding:22px 10px;text-align:center}.trophy{font-size:54px}
    </style>""", unsafe_allow_html=True)
    second=build_second_round_series()
    east_fr=[s for s in FIRST_ROUND_SERIES.values() if s["conf"]=="East"]; west_fr=[s for s in FIRST_ROUND_SERIES.values() if s["conf"]=="West"]
    east_sr=[s for s in second.values() if s["conf"]=="East"]; west_sr=[s for s in second.values() if s["conf"]=="West"]
    east_cf=[s.get("winner") or "TBD" for s in east_sr]; west_cf=[s.get("winner") or "TBD" for s in west_sr]
    html=f"""
    <div class='bracket-wrap'><div class='bracket-title'>2026 NBA PLAYOFF BRACKET</div><div class='bracket-sub'>Auto-refreshing bracket view · API scores override fallback data when available</div>
    <div class='bracket-grid'>
    <div><div class='conf-title'>Eastern Conference</div><div class='round-title'>First Round</div>{''.join(series_card(s,'First Round') for s in east_fr)}</div>
    <div><div class='round-title'>Second Round</div>{''.join(series_card(s,'Second Round') for s in east_sr)}</div>
    <div class='finals-box'><h3>Conference Finals</h3><p>East: {east_cf[0]} / {east_cf[1]}</p><div class='trophy'>🏆</div><p>West: {west_cf[0]} / {west_cf[1]}</p><h3>NBA Finals</h3></div>
    <div><div class='round-title'>Second Round</div>{''.join(series_card(s,'Second Round') for s in west_sr)}</div>
    <div><div class='conf-title'>Western Conference</div><div class='round-title'>First Round</div>{''.join(series_card(s,'First Round') for s in west_fr)}</div>
    </div></div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_team_outlook(team):
    p=TEAM_PROFILES[team]
    st.subheader("Team Outlook")
    st.markdown(f"<div class='big-status'>{series_status_text(team)}</div>", unsafe_allow_html=True)
    st.markdown("### What is going well")
    for s in p["strengths"]:
        if team == "New York Knicks" and "Towns" in s:
            st.success("Karl-Anthony Towns gives New York spacing at center, but his impact depends on staying out of foul trouble.")
        else:
            st.success(s)
    st.markdown("### Specific concerns")
    for c in p["concerns"]:
        st.warning(c)
    st.markdown("### Next game keys")
    for item in ["Win the possession battle", "Keep the main creators fresh for the fourth quarter", "Avoid cheap fouls", "Get bench minutes that do not lose the lead"]:
        st.write(f"• {item}")

def render_game_countdown(team):
    live=find_live_game_for_team(team)
    st.subheader("Game Status / Live Link")
    if live:
        home=live.get("homeTeam",{}); away=live.get("awayTeam",{})
        status=live.get("gameStatusText", "Scheduled")
        matchup=f"{away.get('teamName','Away')} at {home.get('teamName','Home')}"
        if "Final" in status:
            st.success(f"Final: {matchup}"); st.write(status)
        elif status and ("Q" in status or ":" in status or "Halftime" in status):
            st.error(f"🔴 LIVE NOW: {matchup}"); st.write(status)
            if st.button("Go to Live Game Center"):
                st.session_state["page_override"]="🏀 Live Game Center"; st.rerun()
        else:
            st.info(f"Upcoming: {matchup}"); st.write(status)
    else:
        opp=TEAM_PROFILES[team].get("current_opponent")
        if opp: st.info(f"Next matchup: {team} vs {opp}. Live countdown appears when NBA live data is available.")

def render_lineup_cards(team, box_df):
    alias=TEAM_ALIASES[team]
    lineup=estimated_lineup(box_df, alias, team)
    positions=["PG","SG","SF","PF","C"]
    st.markdown(f"### {team} live lineup / estimated current high-usage lineup")
    cols=st.columns(5)
    for i, (_, r) in enumerate(lineup.iterrows()):
        name=r.get("Player",""); seas=season_averages(name)
        with cols[i]:
            st.markdown("<div class='player-card'>", unsafe_allow_html=True)
            try: st.image(headshot(name), width=95)
            except Exception: pass
            st.markdown(f"**{positions[i] if i < 5 else ''} — {name} {player_temp(r)}**")
            st.caption("Current Game")
            st.write(f"PTS {r.get('PTS',0)} | REB {r.get('REB',0)} | AST {r.get('AST',0)}")
            st.write(f"STL {r.get('STL',0)} | BLK {r.get('BLK',0)}")
            st.caption("Season Avg")
            st.write(f"PTS {seas['PTS']} | REB {seas['REB']} | AST {seas['AST']}")
            st.write(f"STL {seas['STL']} | BLK {seas['BLK']}")
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
# Sidebar
# ==========================================================
PAGES={
    "🏀 Home Dashboard":"Home Dashboard",
    "🏀 Playoff Bracket":"Playoff Bracket",
    "🏀 Current Series":"Current Series",
    "🏀 Previous Rounds":"Previous Rounds",
    "🏀 Live Game Center":"Live Game Center",
    "🏀 Player Playoff Tracker":"Player Playoff Tracker",
    "🏀 Legacy Tracker":"Legacy Tracker",
    "🏀 Matchup Lineups":"Matchup Lineups",
}
favorite_team=st.sidebar.selectbox("Choose your 2026 NBA playoff team", list(TEAM_PROFILES.keys()), index=list(TEAM_PROFILES.keys()).index("New York Knicks"))
profile=TEAM_PROFILES[favorite_team]
labels=list(PAGES.keys())
def_label=st.session_state.pop("page_override", "🏀 Home Dashboard")
page_label=st.sidebar.radio("Choose page", labels, index=labels.index(def_label) if def_label in labels else 0)
page=PAGES[page_label]

# ==========================================================
# Pages
# ==========================================================
if page == "Home Dashboard":
    render_matchup_header(favorite_team)
    c1,c2,c3=st.columns(3)
    c1.metric("Status", profile["status"])
    c2.markdown(f"<div class='big-status'>{series_status_text(favorite_team)}</div>", unsafe_allow_html=True)
    c3.metric("Seed", profile["seed"])
    render_game_countdown(favorite_team)
    _, s=series_for_team(favorite_team)
    if s and s.get("games"):
        st.subheader("Current Series Scores")
        st.dataframe(pd.DataFrame(s["games"]), use_container_width=True)
        st.subheader("Previous Game Top Plays")
        st.dataframe(previous_game_top_plays(favorite_team), use_container_width=True)
        st.subheader("Historical Series Tracking")
        st.dataframe(historic_series_context(favorite_team), use_container_width=True)
    render_team_outlook(favorite_team)

elif page == "Playoff Bracket":
    render_bracket()

elif page == "Current Series":
    if profile["status"] == "Active":
        render_matchup_header(favorite_team)
        st.markdown(f"<div class='big-status'>{series_status_text(favorite_team)}</div>", unsafe_allow_html=True)
        _, s=series_for_team(favorite_team)
        if s and s.get("games"):
            st.subheader("Game Results")
            st.dataframe(pd.DataFrame(s["games"]), use_container_width=True)
            st.subheader("Previous Game Top Plays")
            st.dataframe(previous_game_top_plays(favorite_team), use_container_width=True)
            st.subheader("Historical Series Tracking")
            st.dataframe(historic_series_context(favorite_team), use_container_width=True)
        render_team_outlook(favorite_team)
    else:
        st.warning(profile["first_round_result"])

elif page == "Previous Rounds":
    st.header(f"{profile['conference']} Previous Rounds")
    first_opp=profile["first_round_opponent"]
    render_matchup_header(favorite_team, first_round=True)
    st.info(profile["first_round_result"])
    st.subheader("First Round Game-by-Game Scores")
    st.dataframe(pd.DataFrame(FIRST_ROUND_GAME_SCORES.get(favorite_team, [])), use_container_width=True)
    _, s=series_for_team(favorite_team)
    if s and s.get("games"):
        st.subheader("Second Round Games Played So Far")
        st.dataframe(pd.DataFrame(s["games"]), use_container_width=True)

elif page == "Live Game Center":
    render_matchup_header(favorite_team)
    st.subheader("Advanced Live Game Center")
    if AUTOREFRESH_AVAILABLE: st_autorefresh(interval=30000, key="live_refresh"); st.caption("Refreshing every 30 seconds.")
    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live endpoints are unavailable. Check requirements.txt.")
    else:
        live=find_live_game_for_team(favorite_team)
        if not live:
            st.warning("No live or scheduled game found for this team right now.")
        else:
            home=live.get("homeTeam",{}); away=live.get("awayTeam",{})
            home_tri=home.get("teamTricode",""); away_tri=away.get("teamTricode","")
            home_score=safe_int(home.get("score",0)); away_score=safe_int(away.get("score",0))
            period=safe_int(live.get("period",1),1); clock=live.get("gameClock",""); status=live.get("gameStatusText","Unknown"); gid=live.get("gameId","")
            st.write(f"### {away.get('teamName','Away')} at {home.get('teamName','Home')}")
            st.write(f"**Status:** {status} | **Period:** {period} | **Clock:** {clock}")
            a,b=st.columns(2); a.metric(away.get("teamName","Away"), away_score); b.metric(home.get("teamName","Home"), home_score)
            alias=TEAM_ALIASES[favorite_team]; is_home=(home_tri==alias)
            team_score=home_score if is_home else away_score; opp_score=away_score if is_home else home_score
            margin=team_score-opp_score; prob=win_prob(margin, period, is_home)
            c1,c2,c3=st.columns(3); c1.metric(f"{favorite_team} Win Probability", f"{prob}%"); c2.metric("Score Margin", margin); c3.metric("Home Game", "Yes" if is_home else "No")
            st.plotly_chart(px.pie(pd.DataFrame({"Outcome":[f"{favorite_team} wins","Opponent wins"],"Probability":[prob,100-prob]}), names="Outcome", values="Probability", title="Current Win Probability"), use_container_width=True)
            timeline=pd.DataFrame({"Game Segment":["Start","Q1","Q2","Q3","Now"],"Win Probability":[50,max(1,min(99,prob-12)),max(1,min(99,prob-7)),max(1,min(99,prob-3)),prob],"Margin":[0,margin-8,margin-5,margin-2,margin]})
            st.subheader("Momentum / Win Probability Timeline"); st.plotly_chart(px.line(timeline,x="Game Segment",y="Win Probability",markers=True), use_container_width=True); st.plotly_chart(px.line(timeline,x="Game Segment",y="Margin",markers=True,title="Score Margin Momentum"), use_container_width=True)
            box=get_live_boxscore(gid); box_df=create_boxscore_df(box) if box else pd.DataFrame()
            if not box_df.empty:
                render_lineup_cards(favorite_team, box_df)
                opp=profile.get("current_opponent")
                if opp: render_lineup_cards(opp, box_df)
                st.subheader("Full Live Box Score"); st.dataframe(box_df, use_container_width=True)
                st.subheader("Foul Trouble Tracker")
                fouls=box_df[box_df["PF"].astype(float)>=4]
                st.dataframe(fouls[["Team","Player","PF","PTS","MIN"]], use_container_width=True) if not fouls.empty else st.success("No major foul trouble detected.")
                st.subheader("Game Story")
                for line in game_story(favorite_team, margin, prob, box_df): st.write(f"• {line}")
            st.subheader("AI Game Narrator")
            st.info(f"{favorite_team} is {'ahead' if margin>0 else 'tied' if margin==0 else 'behind'} by {abs(margin)}. The next stretch matters for turnovers, fouls, and shot quality.")
            st.subheader("What Needs To Happen Next")
            for item in ["Get stops without fouling", "Protect the defensive glass", "Create clean looks for the main scorer", "Avoid live-ball turnovers"]: st.write(f"• {item}")
            st.subheader("What-If Simulator")
            st.dataframe(pd.DataFrame([{"Scenario":f"{'+' if sw>=0 else ''}{sw} point swing","New Margin":margin+sw,"Win Probability":f"{win_prob(margin+sw,period,is_home)}%"} for sw in [10,5,0,-5,-10]]), use_container_width=True)
            actions=get_live_playbyplay(gid)
            if actions:
                shots=shot_df_from_pbp(actions, alias)
                st.subheader("Live Shot Chart")
                if shots.empty: st.info("No shot actions detected yet for this team.")
                else:
                    last=shots.iloc[-1]; st.info(f"Latest shot: {last['Player']} {'made' if last['Made'] else 'missed'} — {last['Description']}")
                    options=["All players"]+sorted(shots["Player"].dropna().unique().tolist()); shooter=st.selectbox("Choose shooter", options)
                    display=shots if shooter=="All players" else shots[shots["Player"]==shooter]
                    st.plotly_chart(draw_court(display, f"{favorite_team} shot chart — blue O = made, red X = missed"), use_container_width=True)
                st.subheader("Clutch Meter")
                st.warning("Clutch-time situation: fourth quarter and within five points.") if period>=4 and abs(margin)<=5 else st.info("Clutch meter becomes more important in the fourth quarter.")
                st.subheader("Top Plays From This Game")
                rows=[]
                for a in actions:
                    if (a.get("teamTricode") or "") == alias and is_top_play(a.get("description","")):
                        desc=a.get("description",""); rows.append({"Period":a.get("period",""),"Clock":a.get("clock",""),"Top Play":desc,"Why it mattered":explain_play(desc,favorite_team)})
                st.dataframe(pd.DataFrame(rows[-5:]) if rows else previous_game_top_plays(favorite_team), use_container_width=True)

elif page == "Player Playoff Tracker":
    render_matchup_header(favorite_team)
    plist=profile["starters"]+profile["subs"]
    player=st.selectbox("Choose player", plist); season=st.selectbox("Season", ["2025-26","2024-25","2023-24"], index=0)
    if not NBA_STATS_AVAILABLE: st.error("nba_api stats endpoints unavailable.")
    else:
        pid=get_player_id(player)
        if not pid: st.warning(f"Could not find player ID for {player}.")
        else:
            try: logs=playergamelog.PlayerGameLog(player_id=pid, season=season, season_type_all_star="Playoffs").get_data_frames()[0]
            except Exception: logs=pd.DataFrame()
            if logs.empty: st.warning(f"No playoff logs found for {player} in {season}.")
            else:
                cols=[c for c in ["GAME_DATE","MATCHUP","WL","MIN","PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","FT_PCT","PLUS_MINUS"] if c in logs.columns]
                st.dataframe(logs[cols], use_container_width=True)
                stat=st.selectbox("Choose stat", [c for c in ["PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","PLUS_MINUS","MIN"] if c in logs.columns])
                chart=logs.copy(); chart["Game Number"]=range(1,len(chart)+1)
                st.plotly_chart(px.line(chart,x="Game Number",y=stat,markers=True,title=f"{player} {stat} — Playoffs"), use_container_width=True)

elif page == "Legacy Tracker":
    render_matchup_header(favorite_team)
    player=st.selectbox("Choose starter", profile["starters"])
    pts=st.slider("Playoff scoring average",0,45,20); reb=st.slider("Playoff rebounding average",0,20,6); ast=st.slider("Playoff assists average",0,15,4); wins=st.slider("Series wins this run",0,4,1 if profile["status"]=="Active" else 0)
    score=min(100, round(50+pts*.5+reb*.6+ast*.5+wins*10,1)); st.metric(f"{player} Legacy Impact Score", score)
    st.plotly_chart(px.bar(pd.DataFrame({"Outcome":["Current","Win Second Round","Reach Conference Finals","Reach NBA Finals","Win Championship"],"Legacy Score":[50,65,78,90,100]}), x="Outcome", y="Legacy Score", title=f"{player} Legacy Path"), use_container_width=True)

elif page == "Matchup Lineups":
    render_matchup_header(favorite_team)
    if profile["status"] != "Active": st.warning("This team is eliminated, so current matchup lineups are not active.")
    else:
        opp=profile["current_opponent"]
        st.subheader("Projected Starter Matchups")
        st.dataframe(matchup_advantages(favorite_team, opp), use_container_width=True)
        st.caption("Lineups can change because of injuries, foul trouble, matchup choices, and coaching decisions.")
        st.subheader("Top Bench / Rotation Players")
        bench=[{"Team":favorite_team,"Player":p} for p in profile["subs"]]+[{"Team":opp,"Player":p} for p in TEAM_PROFILES[opp]["subs"]]
        st.dataframe(pd.DataFrame(bench), use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | automatic series tracking | previous rounds | live game center | shot chart")
