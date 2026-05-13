
import html
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
    from nba_api.stats.endpoints import playergamelog, playercareerstats, scoreboardv2, leaguegamefinder, commonteamroster, leaguedashplayerstats
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False


try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False

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
.injury-card { border:1px solid rgba(0,0,0,.12); border-radius:16px; padding:10px; background:rgba(255,255,255,.85); margin-bottom:10px; min-height:135px; }
.injury-status { font-weight:900; padding:4px 8px; border-radius:999px; display:inline-block; background:#fee2e2; color:#991b1b; }
.injury-note { font-size:13px; color:#374151; }
.live-score-sticky {
  position: sticky; top: 0; z-index: 1000;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc; border-radius: 16px; padding: 14px 16px 16px;
  border: 1px solid rgba(148,163,184,.35);
  box-shadow: 0 8px 30px rgba(15,23,42,.35);
  margin-bottom: 14px;
}
.live-hero-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center; }
@media (max-width: 900px) {
  .live-hero-grid { grid-template-columns: 1fr; text-align: center; }
  .live-hero-side { justify-content: center !important; }
}
.live-hero-side { display: flex; align-items: center; gap: 10px; }
.live-hero-side.right { flex-direction: row-reverse; }
.live-score-big { font-size: clamp(2rem, 5vw, 2.75rem); font-weight: 900; letter-spacing: -0.02em; line-height: 1.1; }
.live-meta-row { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 10px; }
.live-pill { font-size: 12px; font-weight: 700; padding: 5px 10px; border-radius: 999px; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18); }
.live-pill.live { background: rgba(239,68,68,.25); border-color: rgba(252,165,165,.5); color: #fecaca; }
.live-pill.clutch { background: rgba(234,179,8,.22); border-color: rgba(253,224,71,.45); color: #fef08a; }
.live-pill.prob { background: rgba(56,189,248,.18); border-color: rgba(125,211,252,.4); color: #bae6fd; }
.live-pill.series { background: rgba(167,139,250,.2); border-color: rgba(196,181,253,.4); color: #e9d5ff; }
.live-tile-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 12px; }
.live-tile { background: rgba(15,23,42,.45); border-radius: 12px; padding: 8px 10px; text-align: center; border: 1px solid rgba(148,163,184,.2); }
.live-tile .v { font-size: 1.25rem; font-weight: 800; color: #fff; }
.live-tile .k { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: .04em; }
.live-inj-strip { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(148,163,184,.25); font-size: 12px; color: #cbd5e1; }
.badge-hot { color: #f97316; font-weight: 800; }
.badge-cold { color: #38bdf8; font-weight: 800; }
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

# ESPN team slugs are used for injury reports because nba_api does not expose a
# reliable official injury-report endpoint. This is automatic when ESPN is reachable.
ESPN_INJURY_SLUGS = {
    "Atlanta Hawks": "atl/atlanta-hawks",
    "Boston Celtics": "bos/boston-celtics",
    "Cleveland Cavaliers": "cle/cleveland-cavaliers",
    "Denver Nuggets": "den/denver-nuggets",
    "Houston Rockets": "hou/houston-rockets",
    "Los Angeles Lakers": "lal/los-angeles-lakers",
    "Minnesota Timberwolves": "min/minnesota-timberwolves",
    "New York Knicks": "ny/new-york-knicks",
    "Orlando Magic": "orl/orlando-magic",
    "Philadelphia 76ers": "phi/philadelphia-76ers",
    "Phoenix Suns": "phx/phoenix-suns",
    "Portland Trail Blazers": "por/portland-trail-blazers",
    "San Antonio Spurs": "sa/san-antonio-spurs",
    "Oklahoma City Thunder": "okc/oklahoma-city-thunder",
    "Toronto Raptors": "tor/toronto-raptors",
    "Detroit Pistons": "det/detroit-pistons",
}

FALLBACK_INJURY_REPORT = {
    "New York Knicks": [
        {"Player":"OG Anunoby","Status":"Questionable / Monitor","Injury":"Availability status","Latest Update":"Key wing availability should be checked on the official pregame report before every Knicks game.","Impact":"If Anunoby is out or limited, New York loses a primary wing defender, matchup flexibility, and transition finishing."},
        {"Player":"Mitchell Robinson","Status":"Monitor","Injury":"Availability/conditioning","Latest Update":"Check pregame status before tipoff.","Impact":"If limited, rim protection and offensive rebounding become more dependent on the starting frontcourt."},
    ],
    "Philadelphia 76ers": [
        {"Player":"Joel Embiid","Status":"Monitor","Injury":"Health management","Latest Update":"Check official pregame report before tipoff.","Impact":"If limited or out, Philadelphia loses its main half-court pressure point."},
    ],
    "Los Angeles Lakers": [
        {"Player":"LeBron James","Status":"Monitor","Injury":"Veteran workload/health status","Latest Update":"Check pregame status before tipoff.","Impact":"If limited, the Lakers lose late-game organization and matchup control."},
        {"Player":"Anthony Davis","Status":"Monitor","Injury":"Health status","Latest Update":"Check pregame status before tipoff.","Impact":"If limited, the Lakers lose rim protection and interior scoring."},
    ],
}

TEAM_LOGOS = {team: f"https://cdn.nba.com/logos/nba/{tid}/primary/L/logo.svg" for team, tid in TEAM_IDS.items()}

# Current season used for live roster / rotation lookups.
# Change this once the next NBA season starts.
CURRENT_NBA_SEASON = "2025-26"

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

# ==========================================================
# Automatic playoff series templates
# ==========================================================
# These are matchup shells, not score data. The app should get scores from the
# NBA API first. Demo/fallback scores are only used when the API is unavailable
# or when you intentionally turn on demo backup in the sidebar.
SECOND_ROUND_SERIES_TEMPLATE = {
    "DET-CLE": {"conf":"East","round":"Second Round","a":"Detroit Pistons","b":"Cleveland Cavaliers"},
    "NYK-PHI": {"conf":"East","round":"Second Round","a":"New York Knicks","b":"Philadelphia 76ers"},
    "OKC-LAL": {"conf":"West","round":"Second Round","a":"Oklahoma City Thunder","b":"Los Angeles Lakers"},
    "SAS-MIN": {"conf":"West","round":"Second Round","a":"San Antonio Spurs","b":"Minnesota Timberwolves"},
}

# Emergency/demo backup only. Do not use these as the normal truth source.
SECOND_ROUND_DEMO_BACKUP = {
    "DET-CLE": {"games":[
        {"Game":"Game 1","Date":"May 4","Score":"Pistons 111, Cavaliers 101","Winner":"Detroit Pistons","GameID":"demo-det-cle-g1"},
        {"Game":"Game 2","Date":"May 6","Score":"Pistons 105, Cavaliers 97","Winner":"Detroit Pistons","GameID":"demo-det-cle-g2"},
    ]},
    "NYK-PHI": {"games":[
        {"Game":"Game 1","Date":"May 4","Score":"Knicks 137, 76ers 98","Winner":"New York Knicks","GameID":"demo-nyk-phi-g1"},
        {"Game":"Game 2","Date":"May 6","Score":"Knicks 108, 76ers 102","Winner":"New York Knicks","GameID":"demo-nyk-phi-g2"},
    ]},
    "OKC-LAL": {"games":[]},
    "SAS-MIN": {"games":[
        {"Game":"Game 1","Date":"May 5","Score":"Timberwolves 104, Spurs 102","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g1"},
    ]},
}

PLAYOFF_START_DATE = "2026-04-18"
PLAYOFF_END_DATE = "2026-06-30"

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
        {"Game":"Game 2 vs 76ers","Top Play":"New York closed out a 108-102 win and moved the series lead to 2-0.","Why it mattered":"The most recent completed game now drives the dashboard, bracket, and team outlook instead of stale Game 1 data."},
        {"Game":"Game 2 vs 76ers","Top Play":"The Knicks protected the late-game margin and finished the fourth quarter with better control.","Why it mattered":"That is the type of playoff possession management that turns a 1-0 lead into a 2-0 series edge."},
        {"Game":"Game 2 vs 76ers","Top Play":"New York held Philadelphia to 102 points.","Why it mattered":"The defensive floor is becoming a major part of the series story."},
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

@st.cache_data(ttl=300)
def fetch_completed_games_recent(days_back=120, days_forward=1):
    """API-first completed game pull for the custom playoff bracket.

    This function uses TWO NBA.com-backed nba_api methods:
      1) scoreboardv2 by date, which is good for specific completed dates.
      2) leaguegamefinder for the full 2025-26 Playoffs, which is better when
         scoreboardv2 returns empty on Streamlit Cloud or misses older games.

    Important: this does NOT invent scores. It only updates a custom matchup
    such as NYK-PHI if NBA.com/nba_api has actual completed games for that pair.
    Demo backup scores can still appear only when the sidebar backup switch is on.
    """
    if not NBA_STATS_AVAILABLE:
        return []

    records = []
    today = datetime.now().date()
    playoff_start = datetime.fromisoformat(PLAYOFF_START_DATE).date()
    playoff_end = datetime.fromisoformat(PLAYOFF_END_DATE).date()
    start_date = max(playoff_start, today - timedelta(days=days_back))
    end_date = min(playoff_end, today + timedelta(days=days_forward))

    def add_record(game_id, game_date, home, away, home_pts, away_pts, source):
        if not home or not away:
            return
        home_pts = safe_int(home_pts)
        away_pts = safe_int(away_pts)
        if home_pts == 0 and away_pts == 0:
            return
        winner = home if home_pts > away_pts else away if away_pts > home_pts else None
        d_obj = game_date if hasattr(game_date, 'isoformat') else datetime.fromisoformat(str(game_date)[:10]).date()
        records.append({
            "GameID": str(game_id or ""),
            "GameDate": d_obj.isoformat(),
            "Date": d_obj.strftime("%b %d").replace(" 0", " "),
            "Home": home,
            "Away": away,
            "HomeScore": home_pts,
            "AwayScore": away_pts,
            "Winner": winner,
            "Score": f"{away} {away_pts}, {home} {home_pts}",
            "Matchup": f"{away} at {home}",
            "Source": source,
        })

    # Source 1: scoreboardv2, checked day by day.
    d = start_date
    while d <= end_date:
        for date_str in [d.strftime("%m/%d/%Y"), d.strftime("%Y-%m-%d")]:
            try:
                df = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=20).get_data_frames()[0]
            except Exception:
                continue
            if df is None or df.empty:
                continue
            for _, r in df.iterrows():
                status = str(r.get("GAME_STATUS_TEXT", ""))
                if "Final" not in status:
                    continue
                home = ID_TO_TEAM.get(safe_int(r.get("HOME_TEAM_ID")))
                away = ID_TO_TEAM.get(safe_int(r.get("VISITOR_TEAM_ID")))
                add_record(r.get("GAME_ID", ""), d, home, away, r.get("PTS_HOME"), r.get("PTS_AWAY"), "NBA API scoreboardv2")
            break
        d += timedelta(days=1)

    # Source 2: LeagueGameFinder playoff logs, often more reliable for completed games.
    try:
        # The 2025-26 season is the season that contains the 2026 playoffs.
        lgf = leaguegamefinder.LeagueGameFinder(
            league_id_nullable="00",
            season_nullable="2025-26",
            season_type_nullable="Playoffs",
            timeout=30,
        )
        logs = lgf.get_data_frames()[0]
    except Exception:
        logs = pd.DataFrame()

    if logs is not None and not logs.empty:
        logs = logs.copy()
        logs["GAME_DATE"] = pd.to_datetime(logs["GAME_DATE"], errors="coerce")
        logs = logs[(logs["GAME_DATE"].dt.date >= playoff_start) & (logs["GAME_DATE"].dt.date <= end_date)]
        for game_id, gdf in logs.groupby("GAME_ID"):
            if len(gdf) < 2:
                continue
            rows = gdf.to_dict("records")
            r1, r2 = rows[0], rows[1]
            t1 = ALIAS_TO_TEAM.get(str(r1.get("TEAM_ABBREVIATION", "")))
            t2 = ALIAS_TO_TEAM.get(str(r2.get("TEAM_ABBREVIATION", "")))
            if not t1 or not t2:
                continue
            matchup1 = str(r1.get("MATCHUP", ""))
            if " vs. " in matchup1:
                home_row, away_row = r1, r2
                home, away = t1, t2
            elif " @ " in matchup1:
                home_row, away_row = r2, r1
                home, away = t2, t1
            else:
                # If the home/away marker is missing, still count the game using row order.
                home_row, away_row = r1, r2
                home, away = t1, t2
            game_date = pd.to_datetime(home_row.get("GAME_DATE"), errors="coerce")
            if pd.isna(game_date):
                continue
            add_record(game_id, game_date.date(), home, away, home_row.get("PTS"), away_row.get("PTS"), "NBA API leaguegamefinder")

    # De-dupe across both sources.
    clean = []
    seen = set()
    for g in sorted(records, key=lambda x: (x.get("GameDate", ""), x.get("GameID", ""))):
        ident = g.get("GameID") or f"{g.get('GameDate')}|{g.get('Away')}|{g.get('Home')}|{g.get('Score')}"
        if ident in seen:
            continue
        seen.add(ident)
        clean.append(g)
    return clean


def series_key_for_pair(t1, t2, templates=None):
    pair = {t1, t2}
    templates = templates or SECOND_ROUND_SERIES_TEMPLATE
    for key, s in templates.items():
        if {s["a"], s["b"]} == pair:
            return key
    return None

def clean_and_recount_series(series):
    """De-dupe, sort, label Game 1/Game 2/etc., and recalculate wins."""
    for key, s in series.items():
        a, b = s["a"], s["b"]
        cleaned, seen = [], set()
        for g in s.get("games", []):
            ident = g.get("GameID") or f"{g.get('GameDate','')}|{g.get('Score','')}|{g.get('Winner','')}"
            if ident in seen:
                continue
            seen.add(ident)
            cleaned.append(dict(g))

        def sort_key(g):
            gd = g.get("GameDate", "")
            if gd:
                return gd
            try:
                return datetime.strptime(g.get("Date", "") + " 2026", "%b %d %Y").date().isoformat()
            except Exception:
                return "9999-12-31"

        cleaned = sorted(cleaned, key=sort_key)
        for idx, g in enumerate(cleaned, start=1):
            g["Game"] = f"Game {idx}"
            g.pop("GameDate", None)
        s["games"] = cleaned
        s["a_wins"] = sum(1 for g in cleaned if g.get("Winner") == a)
        s["b_wins"] = sum(1 for g in cleaned if g.get("Winner") == b)
        s["winner"] = a if s["a_wins"] >= 4 else b if s["b_wins"] >= 4 else None
        s["source"] = "NBA API" if any(g.get("Source") == "NBA API" for g in cleaned) else ("Demo backup" if cleaned else "Waiting for API games")
    return series

@st.cache_data(ttl=300)
def build_second_round_series_cached(use_demo_backup=False):
    """Build second-round series automatically from NBA API data.

    If use_demo_backup=False, no scores are hard-coded for the current round.
    The bracket waits for the API to report completed games.
    """
    dynamic = {k: {**v, "a_wins":0, "b_wins":0, "winner":None, "games":[]} for k, v in SECOND_ROUND_SERIES_TEMPLATE.items()}

    api_games = fetch_completed_games_recent()
    for g in api_games:
        key = series_key_for_pair(g.get("Home"), g.get("Away"), SECOND_ROUND_SERIES_TEMPLATE)
        if not key:
            continue
        dynamic[key].setdefault("games", []).append({
            "Game": "",
            "Date": g.get("Date", ""),
            "GameDate": g.get("GameDate", ""),
            "Score": g.get("Score", ""),
            "Winner": g.get("Winner", ""),
            "GameID": g.get("GameID", ""),
            "Source": "NBA API",
        })

    # Optional demo backup only if the API has not produced any games for that series.
    if use_demo_backup:
        for key, backup in SECOND_ROUND_DEMO_BACKUP.items():
            if key in dynamic and not dynamic[key].get("games"):
                dynamic[key]["games"] = [dict(g, Source="Demo backup") for g in backup.get("games", [])]

    return clean_and_recount_series(dynamic)

def build_second_round_series():
    # The sidebar variable is created later; default is strict API mode.
    return build_second_round_series_cached(globals().get("USE_DEMO_BACKUP", False))

def infer_next_round_series(round_name, conf=None):
    """Infer Conference Finals/Finals once API games between winners appear.

    This avoids hard-coding future scores. Once second-round winners are known,
    games between those winners are grouped automatically. Finals are inferred
    once East and West winners have NBA API games against each other.
    """
    second = build_second_round_series()
    east_winners = [s.get("winner") for s in second.values() if s.get("conf") == "East" and s.get("winner")]
    west_winners = [s.get("winner") for s in second.values() if s.get("conf") == "West" and s.get("winner")]

    if round_name == "Conference Finals":
        teams = east_winners if conf == "East" else west_winners
        if len(teams) != 2:
            return None
        templates = {f"{TEAM_ALIASES[teams[0]]}-{TEAM_ALIASES[teams[1]]}": {"conf":conf,"round":"Conference Finals","a":teams[0],"b":teams[1]}}
    else:
        if len(east_winners) != 1 or len(west_winners) != 1:
            return None
        templates = {f"{TEAM_ALIASES[east_winners[0]]}-{TEAM_ALIASES[west_winners[0]]}": {"conf":"NBA Finals","round":"NBA Finals","a":east_winners[0],"b":west_winners[0]}}

    dynamic = {k: {**v, "a_wins":0, "b_wins":0, "winner":None, "games":[]} for k, v in templates.items()}
    for g in fetch_completed_games_recent():
        key = series_key_for_pair(g.get("Home"), g.get("Away"), templates)
        if key:
            dynamic[key]["games"].append({
                "Game":"", "Date":g.get("Date",""), "GameDate":g.get("GameDate",""),
                "Score":g.get("Score",""), "Winner":g.get("Winner",""),
                "GameID":g.get("GameID",""), "Source":"NBA API"
            })
    return clean_and_recount_series(dynamic)

def series_for_team(team_name):
    for key, s in build_second_round_series().items():
        if team_name in [s["a"], s["b"]]:
            return key, s
    # Future rounds, if already generated by API results.
    for collection in [infer_next_round_series("Conference Finals", "East"), infer_next_round_series("Conference Finals", "West"), infer_next_round_series("NBA Finals")]:
        if collection:
            for key, s in collection.items():
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
    source_note = "" if s.get("source") == "NBA API" else f" ({s.get('source','')})"
    return f"{TEAM_ALIASES[team_name]} {verb} {team_w}-{opp_w} vs {TEAM_ALIASES[opp]}{source_note}"

def historic_series_context(team_name):
    _, s = series_for_team(team_name)
    if not s: return pd.DataFrame()
    a, b = s["a"], s["b"]
    tw = s["a_wins"] if team_name == a else s["b_wins"]
    ow = s["b_wins"] if team_name == a else s["a_wins"]
    last = s.get("games", [])[-1] if s.get("games") else None
    latest_note = f" Most recent completed game: {last.get('Game')} on {last.get('Date')}: {last.get('Score')}." if last else " No completed API game has been loaded yet."
    if tw == 1 and ow == 0:
        note = "Winning Game 1 improves the series outlook; Game 2 can create a major 2-0 advantage."
    elif tw == 2 and ow == 0:
        note = "A 2-0 lead is historically a very strong best-of-seven position."
    elif tw == 1 and ow == 1:
        note = "At 1-1, the series is close to a reset; Game 3 becomes a swing game."
    elif tw < ow:
        note = "The team is trailing and needs to change the series momentum quickly."
    elif tw == 0 and ow == 0:
        note = "No completed game detected yet. Game 1 sets the tone."
    else:
        note = "The team has the series edge, but must keep winning possession battles to close it out."
    return pd.DataFrame([{"Series Status": series_status_text(team_name), "Data Source": s.get("source",""), "Historical Context": note + latest_note}])

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


@st.cache_data(ttl=21600)
def fetch_current_roster(team_name, season=CURRENT_NBA_SEASON):
    """Return current NBA.com roster for a team. Falls back safely if NBA API is unavailable."""
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    tid = TEAM_IDS.get(team_name)
    if not tid:
        return pd.DataFrame()
    try:
        df = commonteamroster.CommonTeamRoster(team_id=tid, season=season, timeout=20).get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        # CommonTeamRoster columns usually include PLAYER, NUM, POSITION, HEIGHT, WEIGHT, AGE, EXP, SCHOOL, PLAYER_ID
        rename = {"PLAYER": "Player", "POSITION": "Position", "NUM": "Number", "PLAYER_ID": "PlayerID"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        keep = [c for c in ["Player", "Position", "Number", "PlayerID", "AGE", "EXP", "SCHOOL"] if c in df.columns]
        return df[keep].drop_duplicates(subset=["Player"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=21600)
def fetch_team_rotation_by_minutes(team_name, season=CURRENT_NBA_SEASON):
    """Use current-season NBA.com player stats to estimate the active rotation by total minutes."""
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    tid = TEAM_IDS.get(team_name)
    if not tid:
        return pd.DataFrame()
    try:
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            season_type_all_star="Regular Season",
            team_id_nullable=tid,
            per_mode_detailed="Totals",
            timeout=25,
        ).get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        # Common columns: PLAYER_NAME, TEAM_ABBREVIATION, GP, MIN, PTS, REB, AST, PLAYER_ID
        cols = [c for c in ["PLAYER_NAME", "PLAYER_ID", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK"] if c in df.columns]
        out = df[cols].copy()
        out = out.rename(columns={"PLAYER_NAME":"Player", "PLAYER_ID":"PlayerID"})
        if "MIN" in out.columns:
            out["MIN_SORT"] = pd.to_numeric(out["MIN"], errors="coerce").fillna(0)
            out = out.sort_values("MIN_SORT", ascending=False)
        return out.drop_duplicates(subset=["Player"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

def current_roster_names(team_name, limit=None):
    """Current roster names from NBA API, with hard-coded profile only as backup."""
    rot = fetch_team_rotation_by_minutes(team_name)
    if not rot.empty and "Player" in rot.columns:
        names = rot["Player"].dropna().astype(str).tolist()
        return names[:limit] if limit else names
    roster = fetch_current_roster(team_name)
    if not roster.empty and "Player" in roster.columns:
        names = roster["Player"].dropna().astype(str).tolist()
        return names[:limit] if limit else names
    names = TEAM_PROFILES[team_name].get("starters", []) + TEAM_PROFILES[team_name].get("subs", [])
    return names[:limit] if limit else names

def estimated_starters_from_api(team_name):
    """Best available estimate: top 5 by current-season minutes, otherwise fallback profile starters."""
    return current_roster_names(team_name, limit=5)

def estimated_bench_from_api(team_name, start=5, end=12):
    names = current_roster_names(team_name, limit=end)
    return names[start:end] if len(names) > start else TEAM_PROFILES[team_name].get("subs", [])

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

@st.cache_data(ttl=1800)
def fetch_espn_injury_report(team_name):
    """Fetch current injury report from ESPN team injury page.

    nba_api does not provide a dependable injury-report endpoint, so this uses
    ESPN as the live injury source when available. If ESPN changes its page or
    blocks the request, the app falls back to a small monitor list and clearly
    labels that it is fallback data.
    """
    if not REQUESTS_AVAILABLE:
        return pd.DataFrame(), "requests package unavailable"
    slug = ESPN_INJURY_SLUGS.get(team_name)
    if not slug:
        return pd.DataFrame(), "no ESPN injury slug for team"
    url = f"https://www.espn.com/nba/team/injuries/_/name/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        html = requests.get(url, headers=headers, timeout=12).text
    except Exception as e:
        return pd.DataFrame(), f"ESPN request failed: {e}"

    # First try pandas table parsing.
    try:
        tables = pd.read_html(html)
        rows = []
        for tbl in tables:
            cols = [str(c).strip() for c in tbl.columns]
            lower = [c.lower() for c in cols]
            if not any("player" in c or "name" in c for c in lower):
                continue
            tbl.columns = cols
            for _, r in tbl.iterrows():
                player = str(r.get("PLAYER", r.get("Player", r.get("Name", "")))).strip()
                if not player or player.lower() == "nan":
                    continue
                status = str(r.get("STATUS", r.get("Status", "Monitor"))).strip()
                injury = str(r.get("INJURY", r.get("Injury", "Not specified"))).strip()
                date = str(r.get("DATE", r.get("Date", ""))).strip()
                comment = str(r.get("COMMENT", r.get("Comment", r.get("Latest Update", "")))).strip()
                rows.append({
                    "Player": player,
                    "Status": status if status and status.lower() != "nan" else "Monitor",
                    "Injury": injury if injury and injury.lower() != "nan" else "Not specified",
                    "Latest Update": comment if comment and comment.lower() != "nan" else date,
                    "Impact": injury_impact_note(player, status, injury, team_name),
                    "Source": "ESPN injury report",
                })
        if rows:
            return pd.DataFrame(rows).drop_duplicates(subset=["Player"]).reset_index(drop=True), "ESPN injury report"
    except Exception:
        pass

    # Backup parse using BeautifulSoup when tables are not readable.
    if BS4_AVAILABLE:
        try:
            soup = BeautifulSoup(html, "html.parser")
            text_blocks = [x.get_text(" ", strip=True) for x in soup.select("tbody tr")]
            rows = []
            for block in text_blocks:
                if len(block.split()) < 3:
                    continue
                # Conservative fallback: keep a readable line as the update.
                rows.append({
                    "Player": block.split("  ")[0].strip(),
                    "Status": "Monitor",
                    "Injury": "See latest update",
                    "Latest Update": block,
                    "Impact": "Check pregame availability because this could change rotation minutes.",
                    "Source": "ESPN injury report parsed text",
                })
            if rows:
                return pd.DataFrame(rows).head(10), "ESPN injury report parsed text"
        except Exception:
            pass
    return pd.DataFrame(), "No ESPN injury rows found"

def injury_impact_note(player, status, injury, team_name):
    status_l = str(status).lower()
    injury_l = str(injury).lower()
    star_names = set(TEAM_PROFILES.get(team_name, {}).get("starters", [])[:3])
    if player in star_names:
        base = f"{player} is a major rotation piece for {team_name}; his status can change matchup planning and usage."
    else:
        base = f"{player}'s status mainly affects depth, bench minutes, and matchup flexibility."
    if "out" in status_l:
        return base + " If out, expect the rotation to tighten and another player to absorb minutes."
    if "question" in status_l or "doubt" in status_l or "game" in status_l:
        return base + " Pregame warmups and final injury report matter here."
    if "prob" in status_l or "available" in status_l:
        return base + " He is more likely to play, but workload may still matter."
    if any(x in injury_l for x in ["knee", "ankle", "hamstring", "calf", "foot"]):
        return base + " Lower-body injuries can affect defense, transition play, and late-game burst."
    return base

def get_injury_report(team_name):
    df, source = fetch_espn_injury_report(team_name)
    if df is not None and not df.empty:
        return df, source
    fallback = FALLBACK_INJURY_REPORT.get(team_name, [])
    if fallback:
        out = pd.DataFrame(fallback)
        out["Source"] = "Fallback monitor list — check official pregame report"
        return out, source + "; showing fallback monitor list"
    return pd.DataFrame(columns=["Player","Status","Injury","Latest Update","Impact","Source"]), source

def render_injury_report(team_name, opponent_name=None, show_page_header=True):
    if show_page_header:
        st.subheader("Injury Report / Pregame Availability")
        st.caption("Live source: ESPN injury pages when reachable. nba_api does not reliably provide official injury reports, so fallback rows are clearly labeled. Key fallback monitor rows are included when live injury data is unavailable.")
    teams = [team_name]
    if isinstance(opponent_name, (list, tuple, set)):
        for op in opponent_name:
            if op and op not in teams:
                teams.append(op)
    elif opponent_name and opponent_name not in teams:
        teams.append(opponent_name)
    for tm in teams:
        df, source = get_injury_report(tm)
        st.markdown(f"### {tm}")
        st.caption(f"Source/status: {source} · refreshed about every 30 minutes")
        if df.empty:
            st.success("No injury rows found from the live source right now.")
            continue
        cols = st.columns(min(3, max(1, len(df))))
        for i, (_, r) in enumerate(df.iterrows()):
            with cols[i % len(cols)]:
                st.markdown("<div class='injury-card'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1:
                    try:
                        st.image(headshot(str(r.get("Player", ""))), width=72)
                    except Exception:
                        pass
                with c2:
                    st.markdown(f"**{r.get('Player','Unknown')}**")
                    st.markdown(f"<span class='injury-status'>{r.get('Status','Monitor')}</span>", unsafe_allow_html=True)
                    st.write(f"**Injury:** {r.get('Injury','Not specified')}")
                st.markdown(f"<div class='injury-note'><b>Latest:</b> {r.get('Latest Update','Check pregame report')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='injury-note'><b>Scouting impact:</b> {r.get('Impact','Could affect rotation minutes.')}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


@st.cache_data(ttl=1800)
def playoff_game_logs_for_player(name, season=CURRENT_NBA_SEASON):
    """Return current playoff game logs for selected player from NBA API."""
    pid = get_player_id(name)
    if not pid or not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    try:
        df = playergamelog.PlayerGameLog(
            player_id=pid,
            season=season,
            season_type_all_star="Playoffs",
            timeout=25,
        ).get_data_frames()[0]
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def summarize_playoff_logs(logs):
    """Create per-game playoff summary stats from NBA API game logs."""
    if logs is None or logs.empty:
        return {"GP":0,"PTS":0.0,"REB":0.0,"AST":0.0,"STL":0.0,"BLK":0.0,"TOV":0.0,"FG_PCT":0.0,"FG3_PCT":0.0,"FT_PCT":0.0,"PLUS_MINUS":0.0}
    out = {"GP": len(logs)}
    for c in ["PTS","REB","AST","STL","BLK","TOV","PLUS_MINUS"]:
        out[c] = round(pd.to_numeric(logs.get(c, pd.Series(dtype=float)), errors="coerce").fillna(0).mean(), 1)
    for c in ["FG_PCT","FG3_PCT","FT_PCT"]:
        vals = pd.to_numeric(logs.get(c, pd.Series(dtype=float)), errors="coerce").dropna()
        out[c] = round(float(vals.mean()), 3) if len(vals) else 0.0
    return out

def _name_tokens(name):
    return {tok for tok in str(name).lower().replace(".", " ").replace("-", " ").split() if len(tok) >= 3}

def _remove_self_comparisons(player_name, comps):
    """Never compare a player to himself. Also removes near matches by last/name token overlap."""
    player_tokens = _name_tokens(player_name)
    clean = []
    for comp in comps:
        comp_tokens = _name_tokens(comp)
        if str(comp).lower() == str(player_name).lower():
            continue
        # Avoid things like selected Donovan Mitchell being compared to Donovan Mitchell.
        if player_tokens and comp_tokens and player_tokens.issubset(comp_tokens):
            continue
        if comp not in clean:
            clean.append(comp)
    backup = ["Walt Frazier", "Isiah Thomas", "Dwyane Wade", "Kawhi Leonard", "Dirk Nowitzki", "Kevin Garnett", "Jimmy Butler", "Chauncey Billups", "Robert Horry", "Shane Battier"]
    for b in backup:
        if b not in clean and not (_name_tokens(player_name) and _name_tokens(player_name).issubset(_name_tokens(b))):
            clean.append(b)
        if len(clean) >= 6:
            break
    return clean[:6]


def player_resume_profile(player_name, team_name=""):
    """Career/resume starting point before this playoff run.
    Higher baselines reflect already-established NBA/team legacy.
    """
    n = player_name.lower()
    team = str(team_name)

    profiles = {
        "lebron": {
            "baseline": 94, "ceiling": 100, "role": "all-time legend",
            "tier_name": "all-time NBA-history tier",
            "resume": "LeBron already starts near the top because his résumé includes multiple championships, MVP-level longevity, Finals runs, and a long-standing place in the GOAT conversation.",
            "team_context": "For the Lakers, another title would add another late-career championship chapter rather than create his legacy from scratch.",
            "comps": ["Michael Jordan", "Kareem Abdul-Jabbar", "Magic Johnson", "Larry Bird", "Kobe Bryant", "Tim Duncan"]
        },
        "brunson": {
            "baseline": 68, "ceiling": 96, "role": "lead guard",
            "tier_name": "Knicks lead-guard tier",
            "resume": "Brunson already starts high for a Knick because he has become the offense's identity, the late-game creator, and the player most associated with this Knicks era.",
            "team_context": "A deeper run would push him closer to the Knicks guard lineage of Walt Frazier, Earl Monroe, and the most memorable modern Madison Square Garden playoff stars.",
            "comps": ["Walt Frazier", "Earl Monroe", "Chauncey Billups", "Damian Lillard", "Isiah Thomas", "Allen Iverson"]
        },
        "towns": {
            "baseline": 61, "ceiling": 91, "role": "scoring big",
            "tier_name": "star big-man tier",
            "resume": "Karl-Anthony Towns starts above normal starters because he entered this run as an established All-Star caliber offensive big with major scoring and spacing value.",
            "team_context": "For the Knicks, a title-level run would connect him to the franchise's historic big-man tradition, though he would still need signature playoff moments to approach Ewing/Reed territory.",
            "comps": ["Patrick Ewing", "Willis Reed", "Chris Bosh", "Dirk Nowitzki", "Anthony Davis", "Pau Gasol"]
        },
        "anunoby": {
            "baseline": 50, "ceiling": 82, "role": "two-way wing",
            "tier_name": "elite two-way wing tier",
            "resume": "OG Anunoby starts with a strong defender's résumé and championship-role credibility, but his legacy ceiling depends on visible two-way impact in big series.",
            "team_context": "For the Knicks, his path is about becoming a remembered defensive stopper and wing connector in a deep playoff run.",
            "comps": ["Kawhi Leonard", "Andre Iguodala", "Tayshaun Prince", "Shane Battier", "Scottie Pippen", "Bruce Bowen"]
        },
        "bridges": {
            "baseline": 48, "ceiling": 82, "role": "two-way wing",
            "tier_name": "two-way ironman wing tier",
            "resume": "Mikal Bridges starts with strong defensive reputation, durability, and high-end role-player/star-adjacent value, but needs a major playoff run to jump tiers.",
            "team_context": "For the Knicks, his legacy grows most if he becomes the wing who guards stars while also hitting timely shots.",
            "comps": ["Andre Iguodala", "Tayshaun Prince", "Shane Battier", "Khris Middleton", "Jimmy Butler", "Kawhi Leonard"]
        },
        "hart": {
            "baseline": 44, "ceiling": 76, "role": "winning role star",
            "tier_name": "Knicks glue-guy tier",
            "resume": "Josh Hart starts with a real fan-legacy base because his rebounding, toughness, and energy already define part of the Knicks identity.",
            "team_context": "His Knicks legacy rises through winning possessions, huge rebounds, and fourth-quarter plays more than superstar scoring numbers.",
            "comps": ["Charles Oakley", "Anthony Mason", "Draymond Green", "Shane Battier", "Marcus Smart", "Andre Iguodala"]
        },
        "cunningham": {
            "baseline": 56, "ceiling": 95, "role": "franchise guard",
            "tier_name": "Pistons franchise-guard tier",
            "resume": "Cade Cunningham starts with a meaningful but still-building résumé as Detroit's primary creator and franchise centerpiece.",
            "team_context": "For Detroit, each round matters because he is trying to move from promising centerpiece to a guard remembered with Isiah Thomas, Joe Dumars, and Chauncey Billups references.",
            "comps": ["Isiah Thomas", "Joe Dumars", "Chauncey Billups", "Grant Hill", "Luka Doncic", "Shai Gilgeous-Alexander"]
        },
        "embiid": {
            "baseline": 76, "ceiling": 98, "role": "MVP center",
            "tier_name": "MVP-center tier",
            "resume": "Joel Embiid starts very high because he already has MVP-level peak value and years as a dominant regular-season centerpiece.",
            "team_context": "His legacy jumps most from deep playoff advancement because that is the missing piece people use against his résumé.",
            "comps": ["Moses Malone", "Hakeem Olajuwon", "Shaquille O'Neal", "Nikola Jokic", "Patrick Ewing", "David Robinson"]
        },
        "davis": {
            "baseline": 78, "ceiling": 96, "role": "championship defensive big",
            "tier_name": "championship big-man tier",
            "resume": "Anthony Davis starts very high because he already has a championship, elite defensive peak, and All-NBA level two-way résumé.",
            "team_context": "Another Lakers run would strengthen his case as one of the great two-way bigs of his era.",
            "comps": ["Kevin Garnett", "David Robinson", "Hakeem Olajuwon", "Tim Duncan", "Dwight Howard", "Pau Gasol"]
        },
    }

    for key, prof in profiles.items():
        if key in n:
            return prof

    # General named stars / high baselines
    if any(x in n for x in ["mitchell", "tatum", "brown", "durant", "booker", "george", "shai", "gilgeous", "edwards", "jokic", "giannis", "luka", "doncic"]):
        return {"baseline": 66, "ceiling": 95, "role": "established star", "tier_name": "established NBA-star tier",
                "resume": f"{player_name} starts above normal starters because he already has a star résumé before this playoff run.",
                "team_context": f"For {team}, the run matters most if he is one of the main reasons the team keeps advancing.",
                "comps": ["Dwyane Wade", "Kevin Durant", "Kawhi Leonard", "James Harden", "Damian Lillard", "Jimmy Butler"]}
    if any(x in n for x in ["maxey", "garland", "mobley", "holmgren", "wembanyama", "reaves", "gobert"]):
        return {"baseline": 54, "ceiling": 89, "role": "high-impact core player", "tier_name": "core playoff-piece tier",
                "resume": f"{player_name} starts with a meaningful current-era résumé, but still has room to define his playoff reputation.",
                "team_context": f"For {team}, the run can turn him from important core player into a player tied to a specific playoff breakthrough.",
                "comps": ["Kyrie Irving", "Klay Thompson", "Pau Gasol", "Draymond Green", "Ben Wallace", "Jrue Holiday"]}
    if any(x in n for x in ["mcbride", "robinson", "clarkson", "shamet", "alvarado", "lowry", "drummond", "sasser", "stewart", "strus", "okoro", "conley", "divincenzo", "dort", "wallace", "hartenstein"]):
        return {"baseline": 34, "ceiling": 73, "role": "rotation playoff contributor", "tier_name": "role-player playoff-memory tier",
                "resume": f"{player_name} starts with a role-player résumé, so his legacy movement comes from specific playoff moments, defense, shooting, rebounding, or stabilizing minutes.",
                "team_context": f"For {team}, his path is becoming the player fans remember for a key series, not passing the team's all-time stars.",
                "comps": ["Robert Horry", "Shane Battier", "Derek Fisher", "Bruce Bowen", "Steve Kerr", "Andre Iguodala"]}
    return {"baseline": 40, "ceiling": 78, "role": "playoff contributor", "tier_name": "team-playoff contributor tier",
            "resume": f"{player_name} starts from a modest legacy base and needs visible playoff impact to move up.",
            "team_context": f"For {team}, the run matters if his production becomes tied to a winning series.",
            "comps": ["Robert Horry", "Andre Iguodala", "Chauncey Billups", "Jimmy Butler", "Kyle Lowry", "Shane Battier"]}

def player_legacy_archetype(player_name):
    prof = player_resume_profile(player_name)
    return prof["role"], _remove_self_comparisons(player_name, prof["comps"])

def player_legacy_ceiling(player_name, team_name=""):
    return player_resume_profile(player_name, team_name)["ceiling"]

def player_legacy_floor(player_name):
    return player_resume_profile(player_name)["baseline"]

def player_specific_tier(score, player_name, team_name=""):
    prof = player_resume_profile(player_name, team_name)
    baseline = prof["baseline"]
    ceiling = prof["ceiling"]
    span = max(1, ceiling - baseline)
    pct = (score - baseline) / span
    if pct >= .88:
        return f"{player_name} peak {prof['tier_name']}"
    if pct >= .68:
        return f"{player_name} major leap"
    if pct >= .45:
        return f"{player_name} clear playoff boost"
    if pct >= .22:
        return f"{player_name} modest rise"
    return f"{player_name} résumé mostly unchanged"

def legacy_score_from_inputs(pts, reb, ast, stl, blk, fg, three, plus_minus, rounds_won, title_won=False, player_name="", team_name=""):
    prof = player_resume_profile(player_name, team_name)
    baseline = prof["baseline"]
    ceiling = prof["ceiling"]
    # This is intentionally an incremental playoff-run score on top of career résumé.
    scoring = pts * 0.42
    all_around = reb * 0.22 + ast * 0.30 + stl * 0.70 + blk * 0.55
    efficiency = max(0, (fg - 0.43) * 24) + max(0, (three - 0.34) * 10)
    impact = plus_minus * 0.22
    winning = rounds_won * 4.2 + (7.0 if title_won else 0)
    raw = baseline + scoring + all_around + efficiency + impact + winning
    return round(max(0, min(ceiling, raw)), 1)

def legacy_tier(score):
    # Kept for old code compatibility, but the UI now uses player_specific_tier().
    if score >= 92: return "top personal legacy tier"
    if score >= 82: return "major personal legacy tier"
    if score >= 72: return "strong personal legacy tier"
    if score >= 60: return "meaningful personal legacy tier"
    if score >= 48: return "modest personal legacy tier"
    return "limited movement"

def _scenario_meaning(player, team, score, scenario_label, rounds, title):
    prof = player_resume_profile(player, team)
    comps = _remove_self_comparisons(player, prof["comps"])
    tier = player_specific_tier(score, player, team)
    if title:
        team_hist = f"For {team}, {player}'s title version would be judged against names like {comps[0]} and {comps[1]} because the championship would attach his stat line to a specific banner-level run."
        nba_hist = f"NBA-wide, this would not erase the old résumé; it would add a new chapter to his existing {prof['role']} case and move him toward the {tier} range."
    elif rounds >= 3:
        team_hist = f"A Finals trip would make {player}'s run a remembered {team} chapter, especially if his averages stay near these slider settings."
        nba_hist = f"NBA-wide, the reference range becomes players such as {comps[1]} and {comps[2]}: not because the careers are identical, but because the playoff role would feel comparable."
    elif rounds >= 2:
        team_hist = f"A conference-finals trip would give {player} a much stronger {team} playoff case, above ordinary good-season memories."
        nba_hist = f"NBA-wide, the conversation would start using comparison names like {comps[2]} and {comps[3]} as role/impact reference points."
    elif rounds >= 1:
        team_hist = f"Winning this round would make {player}'s current production part of the {team} series story, not just an individual box-score stretch."
        nba_hist = f"NBA-wide, this is still mostly a team-advancement boost unless his stat line stays strong enough to resemble {comps[3]} or {comps[4]} in role."
    else:
        team_hist = prof["team_context"]
        nba_hist = prof["resume"]
    return team_hist, nba_hist

def build_legacy_path(player, team, pts, reb, ast, stl, blk, fg, three, plus_minus):
    steps = [
        ("Current résumé + current run", 0, False),
        ("Win current round", 1, False),
        ("Reach Conference Finals", 2, False),
        ("Reach NBA Finals", 3, False),
        ("Win championship", 4, True),
    ]
    rows=[]
    for label, rounds, title in steps:
        sc = legacy_score_from_inputs(pts, reb, ast, stl, blk, fg, three, plus_minus, rounds, title, player, team)
        tier = player_specific_tier(sc, player, team)
        team_hist, nba_hist = _scenario_meaning(player, team, sc, label, rounds, title)
        rows.append({"Scenario":label,"Projected Legacy Score":sc,"Player-Specific Tier":tier,"Team History Meaning":team_hist,"NBA History Meaning":nba_hist})
    return pd.DataFrame(rows)

def legacy_takeaways(player, team, pts, reb, ast, stl, blk, fg, three, plus_minus):
    prof = player_resume_profile(player, team)
    archetype, comps = player_legacy_archetype(player)
    base = legacy_score_from_inputs(pts, reb, ast, stl, blk, fg, three, plus_minus, 0, False, player, team)
    title = legacy_score_from_inputs(pts, reb, ast, stl, blk, fg, three, plus_minus, 4, True, player, team)
    return [
        prof["resume"],
        prof["team_context"],
        f"Comparison references for this player: {', '.join(comps[:4])}.",
        f"With these slider settings, {player} moves from {player_specific_tier(base, player, team)} to {player_specific_tier(title, player, team)} if the run ends in a championship."
    ]
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
        names = estimated_starters_from_api(team_name)
        return pd.DataFrame([{"Team":alias,"Player":p,"MIN":"0:00","PTS":0,"REB":0,"AST":0,"STL":0,"BLK":0,"PF":0,"FGM":0,"FGA":0} for p in names])
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
    t_starters = estimated_starters_from_api(team)
    o_starters = estimated_starters_from_api(opp)
    positions=["PG","SG","SF","PF","C"]
    rows=[]
    for i,pos in enumerate(positions):
        tp=t_starters[i] if i < len(t_starters) else "TBD"
        op=o_starters[i] if i < len(o_starters) else "TBD"
        if "TBD" in [tp, op]:
            adv="TBD"; why="NBA API roster data was incomplete for this position."
        elif any(x in tp for x in ["Brunson","Mitchell","Shai","Edwards","LeBron","Embiid","Wembanyama","Cunningham","Maxey","Towns","Davis"]):
            adv=team; why=f"{tp} grades as one of the higher-impact current rotation players in this matchup."
        elif any(x in op for x in ["Brunson","Mitchell","Shai","Edwards","LeBron","Embiid","Wembanyama","Cunningham","Maxey","Towns","Davis"]):
            adv=opp; why=f"{op} gives {opp} the bigger star-impact edge at this spot."
        else:
            adv="Close"; why="This spot depends on current form, shooting, defense, matchup choices, and foul trouble."
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


# ==========================================================
# Next-round advancement helpers
# ==========================================================
def paired_second_round_key(series_key):
    pairs = {
        "NYK-PHI": "DET-CLE",
        "DET-CLE": "NYK-PHI",
        "OKC-LAL": "SAS-MIN",
        "SAS-MIN": "OKC-LAL",
    }
    return pairs.get(series_key)

def next_round_context_for_team(team_name):
    """Return next-round display context when the team's current custom series is complete.

    Example: if NYK has finished NYK-PHI and DET-CLE is not finished yet,
    the home dashboard shows Knicks vs Pistons / Cavaliers in the Eastern
    Conference Championship instead of staying stuck on Knicks vs 76ers.
    """
    series_map = build_second_round_series()
    current_key = None
    current_series = None
    for key, series in series_map.items():
        if team_name in [series.get("a"), series.get("b")]:
            current_key = key
            current_series = series
            break
    if not current_series or not current_series.get("winner"):
        return None
    if current_series.get("winner") != team_name:
        return {
            "advanced": False,
            "eliminated": True,
            "round_label": "Eliminated",
            "opponents": [],
            "opponent_text": current_series.get("winner", "Opponent"),
            "status_text": f"{team_name} was eliminated by {current_series.get('winner')}.",
            "completed_series": current_series,
        }
    paired_key = paired_second_round_key(current_key)
    paired = series_map.get(paired_key) if paired_key else None
    if not paired:
        return None
    conf = current_series.get("conf", "")
    round_label = "Eastern Conference Championship" if conf == "East" else "Western Conference Championship"
    if paired.get("winner"):
        opponents = [paired["winner"]]
        opponent_text = paired["winner"]
    else:
        opponents = [paired.get("a"), paired.get("b")]
        opponent_text = f"{paired.get('a')} / {paired.get('b')}"
    opponents = [op for op in opponents if op in TEAM_PROFILES]
    return {
        "advanced": True,
        "eliminated": False,
        "round_label": round_label,
        "opponents": opponents,
        "opponent_text": opponent_text,
        "status_text": f"{team_name} advances to the {round_label} vs {opponent_text}.",
        "completed_series": current_series,
        "paired_series": paired,
    }

def render_home_matchup_header(team_name):
    ctx = next_round_context_for_team(team_name)
    if not ctx or not ctx.get("advanced"):
        render_matchup_header(team_name)
        return ctx
    p = TEAM_PROFILES[team_name]
    c1, c2, c3 = st.columns([1, 2.8, 1.4])
    with c1:
        st.image(TEAM_LOGOS[team_name], width=110)
    with c2:
        st.markdown(
            f"<div style='text-align:center'><h1>({p['seed']}) {team_name} vs {ctx['opponent_text']}</h1>"
            f"<h3>{ctx['round_label']}</h3><p>{ctx['status_text']}</p></div>",
            unsafe_allow_html=True,
        )
    with c3:
        logo_cols = st.columns(max(1, len(ctx.get("opponents", []))))
        for i, op in enumerate(ctx.get("opponents", [])):
            with logo_cols[i % len(logo_cols)]:
                st.image(TEAM_LOGOS[op], width=82)
                st.caption(op)
    return ctx

def home_injury_opponents(team_name):
    ctx = next_round_context_for_team(team_name)
    if ctx and ctx.get("advanced"):
        return ctx.get("opponents", [])
    return TEAM_PROFILES.get(team_name, {}).get("current_opponent")

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
    east_conf = infer_next_round_series("Conference Finals", "East")
    west_conf = infer_next_round_series("Conference Finals", "West")
    finals = infer_next_round_series("NBA Finals")
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

def latest_game_note(team):
    _, s = series_for_team(team)
    if not s or not s.get("games"):
        return "No completed current-series game has been detected yet."
    last = s["games"][-1]
    result = "won" if last.get("Winner") == team else "lost"
    return f"Most recent game: {last.get('Game','Previous Game')} on {last.get('Date','recently')} — {last.get('Score','score unavailable')}. {team} {result} that game."

def render_team_outlook(team):
    p=TEAM_PROFILES[team]
    st.subheader("Team Outlook")
    st.markdown(f"<div class='big-status'>{series_status_text(team)}</div>", unsafe_allow_html=True)
    st.info(latest_game_note(team))
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


def _live_team_full_name(team_tricode, team_obj):
    t = ALIAS_TO_TEAM.get(team_tricode or "")
    if t:
        return t
    city = (team_obj or {}).get("teamCity") or ""
    nick = (team_obj or {}).get("teamName") or (team_tricode or "?")
    return f"{city} {nick}".strip() or nick


def _live_series_board(away_name, home_name):
    pair = {away_name, home_name}
    candidates = []
    candidates.extend(build_second_round_series().values())
    for coll in (
        infer_next_round_series("Conference Finals", "East"),
        infer_next_round_series("Conference Finals", "West"),
        infer_next_round_series("NBA Finals"),
    ):
        if coll:
            candidates.extend(coll.values())
    for s in candidates:
        if not s:
            continue
        if {s.get("a"), s.get("b")} == pair:
            a, b = s["a"], s["b"]
            return f"{TEAM_ALIASES[a]} {s['a_wins']}–{s['b_wins']} {TEAM_ALIASES[b]}", s.get("source") or ""
    return None, None


def _seed_badge(team_name):
    if team_name not in TEAM_PROFILES:
        return "—"
    return f"Seed {TEAM_PROFILES[team_name]['seed']}"


def _injury_hero_lines(team_names, max_each=2):
    lines = []
    for tm in team_names:
        if not tm:
            continue
        df, _src = get_injury_report(tm)
        if df is None or df.empty:
            continue
        bits = []
        for _, r in df.head(max_each).iterrows():
            pl = html.escape(str(r.get("Player", "?")))
            stt = html.escape(str(r.get("Status", "?")))
            bits.append(f"<span class='live-pill' style='font-size:11px'>🩹 {pl}: {stt}</span>")
        if bits:
            lines.append(f"<div style='margin-top:6px'><span style='font-weight:800;color:#e2e8f0'>{html.escape(tm)}</span> {' '.join(bits)}</div>")
    return "".join(lines) if lines else "<div style='margin-top:8px;color:#94a3b8;font-size:12px'>No injury rows from live source · see <b>Key Injuries</b> tab.</div>"


def render_live_game_center(favorite_team, profile):
    """Professional dashboard layout: sticky score hero + tabbed sections."""
    st.markdown("### 🏟️ Live Game Center")
    st.caption("Compact layout · use tabs below for depth · refreshes with sidebar autorefresh when enabled")

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_refresh")
        st.caption("Auto-refresh every 30 seconds.")

    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live endpoints are unavailable. Check requirements.txt.")
        return

    live = find_live_game_for_team(favorite_team)
    if not live:
        st.warning("No live or scheduled game found for this team right now.")
        return

    home = live.get("homeTeam", {}) or {}
    away = live.get("awayTeam", {}) or {}
    home_tri = home.get("teamTricode", "") or ""
    away_tri = away.get("teamTricode", "") or ""
    home_score = safe_int(home.get("score", 0))
    away_score = safe_int(away.get("score", 0))
    period = safe_int(live.get("period", 1), 1)
    clock = live.get("gameClock", "") or ""
    status = live.get("gameStatusText", "Unknown") or "Unknown"
    gid = live.get("gameId", "") or ""

    away_name = _live_team_full_name(away_tri, away)
    home_name = _live_team_full_name(home_tri, home)
    alias = TEAM_ALIASES[favorite_team]
    is_home = home_tri == alias
    team_score = home_score if is_home else away_score
    opp_score = away_score if is_home else home_score
    margin = team_score - opp_score
    prob = win_prob(margin, period, is_home)

    series_line, series_src = _live_series_board(away_name, home_name)
    if not series_line and favorite_team in (away_name, home_name):
        series_line = series_status_text(favorite_team)
        _, s0 = series_for_team(favorite_team)
        series_src = (s0 or {}).get("source", "")

    clutch = period >= 4 and abs(margin) <= 5
    is_live = status and ("Q" in status or ":" in status or "Halftime" in status) and "Final" not in status

    logo_away = TEAM_LOGOS.get(away_name, f"https://cdn.nba.com/logos/nba/500/{away_tri}/primary/L/logo.svg")
    logo_home = TEAM_LOGOS.get(home_name, f"https://cdn.nba.com/logos/nba/500/{home_tri}/primary/L/logo.svg")

    momentum_note = "Favored team trending up in model" if prob > 55 else "Tight game in model" if prob >= 45 else "Underdog needs stops & quality looks"

    inj_teams = []
    for t in (away_name, home_name):
        if t and t not in inj_teams and t in TEAM_PROFILES:
            inj_teams.append(t)
    if not inj_teams:
        inj_teams = [favorite_team]
        if profile.get("current_opponent") and profile["current_opponent"] not in inj_teams:
            inj_teams.append(profile["current_opponent"])

    hero_html = f"""
<div class="live-score-sticky">
  <div class="live-hero-grid">
    <div class="live-hero-side">
      <img src="{logo_away}" width="56" height="56" style="object-fit:contain" alt="" />
      <div>
        <div style="font-size:13px;font-weight:800;color:#cbd5e1">{html.escape(away_tri)}</div>
        <div style="font-size:15px;font-weight:800">{html.escape(away_name)}</div>
        <div style="font-size:12px;color:#94a3b8">{html.escape(_seed_badge(away_name))}</div>
      </div>
    </div>
    <div style="text-align:center;padding:4px 8px">
      <div style="font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:.06em">LIVE SCOREBOARD</div>
      <div class="live-score-big"><span style="color:#f8fafc">{away_score}</span>
        <span style="color:#64748b;margin:0 10px">—</span>
        <span style="color:#f8fafc">{home_score}</span></div>
      <div style="font-size:14px;font-weight:700;color:#e2e8f0;margin-top:4px">{html.escape(away_tri)} @ {html.escape(home_tri)}</div>
    </div>
    <div class="live-hero-side right">
      <img src="{logo_home}" width="56" height="56" style="object-fit:contain" alt="" />
      <div>
        <div style="font-size:13px;font-weight:800;color:#cbd5e1">{html.escape(home_tri)}</div>
        <div style="font-size:15px;font-weight:800">{html.escape(home_name)}</div>
        <div style="font-size:12px;color:#94a3b8">{html.escape(_seed_badge(home_name))}</div>
      </div>
    </div>
  </div>
  <div class="live-meta-row">
    <span class="live-pill {'live' if is_live else ''}">{'🔴 LIVE' if is_live else '📅 ' + html.escape(status[:40])}</span>
    <span class="live-pill">⏱ Q{period} · {html.escape(clock or '—')}</span>
    <span class="live-pill series">🏆 {html.escape(series_line or 'Series')}</span>
    {('<span class="live-pill clutch">⚡ CLUTCH</span>' if clutch else '')}
    <span class="live-pill prob">📈 Win prob · {favorite_team.split()[-1]}: {prob}%</span>
  </div>
  <div class="live-tile-row">
    <div class="live-tile"><div class="k">Margin ({favorite_team.split()[-1]})</div><div class="v">{'+' if margin > 0 else ''}{margin}</div></div>
    <div class="live-tile"><div class="k">Venue</div><div class="v">{'HOME' if is_home else 'AWAY'}</div></div>
    <div class="live-tile"><div class="k">Momentum (model)</div><div class="v" style="font-size:12px;line-height:1.25;font-weight:700">{html.escape(momentum_note)}</div></div>
  </div>
  <div class="live-inj-strip"><div style="font-weight:800;margin-bottom:4px;color:#f1f5f9">🩹 Availability snapshot</div>
  {_injury_hero_lines(inj_teams)}
  {('<div style="margin-top:6px;font-size:11px;color:#64748b">' + html.escape(str(series_src)) + '</div>' if series_src else '')}
  </div>
</div>
"""
    st.markdown(hero_html, unsafe_allow_html=True)

    box = get_live_boxscore(gid)
    box_df = create_boxscore_df(box) if box else pd.DataFrame()
    actions = get_live_playbyplay(gid) if gid else []
    opp_other = home_name if favorite_team == away_name else away_name
    opp = profile.get("current_opponent") or opp_other

    matchup_opp = opp if opp in TEAM_PROFILES else (opp_other if opp_other in TEAM_PROFILES else None)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Scoreboard",
        "🩹 Key Injuries",
        "📈 Momentum & Win %",
        "⭐ Top Performers",
        "⚔️ Matchup",
        "📝 Play-by-Play",
        "🎯 Shot Charts",
        "✨ Legacy Impact",
        "🔮 What-If",
    ])

    with tab1:
        with st.container(border=True):
            st.markdown("##### 📊 Game summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Clock", clock or "—")
            m2.metric("Period", f"Q{period}")
            m3.metric(f"{favorite_team.split()[-1]} pts", team_score)
            m4.metric("Opponent pts", opp_score)
            if not box_df.empty:
                st.markdown("**Full box score**")
                st.dataframe(box_df, use_container_width=True, height=320)
                st.markdown("**Foul trouble (4+ PF)**")
                fouls = box_df[box_df["PF"].astype(float) >= 4]
                st.dataframe(fouls[["Team", "Player", "PF", "PTS", "MIN"]], use_container_width=True) if not fouls.empty else st.success("No major foul trouble detected.")
                st.markdown("**Game story**")
                for line in game_story(favorite_team, margin, prob, box_df):
                    st.write(f"• {line}")
            else:
                st.info("Live box score is still loading or unavailable.")

    with tab2:
        with st.container(border=True):
            st.markdown("##### 🩹 Key injuries & availability")
            render_injury_report(favorite_team, home_injury_opponents(favorite_team), show_page_header=False)
            if away_name in TEAM_PROFILES and home_name in TEAM_PROFILES and {away_name, home_name} != {favorite_team, profile.get("current_opponent")}:
                st.caption("Showing favorite team + sidebar opponent list; live matchup names above may differ from profile when bracket has advanced.")

    with tab3:
        with st.container(border=True):
            st.markdown("##### 📈 Live momentum & win probability")
            cL, cR = st.columns((1, 1))
            with cL:
                st.plotly_chart(
                    px.pie(
                        pd.DataFrame({"Outcome": [f"{favorite_team} wins", "Opponent wins"], "Probability": [prob, 100 - prob]}),
                        names="Outcome",
                        values="Probability",
                        title="Win probability split",
                        hole=0.45,
                        color_discrete_sequence=["#0ea5e9", "#64748b"],
                    ),
                    use_container_width=True,
                )
            timeline = pd.DataFrame({
                "Game Segment": ["Start", "Q1", "Q2", "Q3", "Now"],
                "Win Probability": [50, max(1, min(99, prob - 12)), max(1, min(99, prob - 7)), max(1, min(99, prob - 3)), prob],
                "Margin": [0, margin - 8, margin - 5, margin - 2, margin],
            })
            with cR:
                st.plotly_chart(px.line(timeline, x="Game Segment", y="Win Probability", markers=True, title="Win probability path (illustrative)"), use_container_width=True)
            st.plotly_chart(px.line(timeline, x="Game Segment", y="Margin", markers=True, title="Score margin momentum (illustrative)"), use_container_width=True)
            st.caption("Timeline is a compact visual aid tied to the current margin and period, not a full play-by-play reconstruction.")

    with tab4:
        with st.container(border=True):
            st.markdown("##### ⭐ Top performers <span class='badge-hot'>🔥</span> hot · <span class='badge-cold'>❄️</span> cold", unsafe_allow_html=True)
            if not box_df.empty:
                render_lineup_cards(favorite_team, box_df)
                if opp and opp in TEAM_PROFILES:
                    render_lineup_cards(opp, box_df)
                elif matchup_opp:
                    render_lineup_cards(matchup_opp, box_df)
            else:
                st.info("Lineup cards appear when the live box score loads.")

    with tab5:
        with st.container(border=True):
            st.markdown("##### ⚔️ Team matchup analysis")
            if matchup_opp:
                st.dataframe(matchup_advantages(favorite_team, matchup_opp), use_container_width=True)
            else:
                st.warning("No opponent on file for positional matchup grid.")

    with tab6:
        with st.container(border=True):
            st.markdown("##### 📝 Play-by-play (latest)")
            if actions:
                rows = []
                for a in actions[-80:]:
                    rows.append({
                        "Q": a.get("period", ""),
                        "Clock": a.get("clock", ""),
                        "Team": a.get("teamTricode", ""),
                        "Play": (a.get("description") or "")[:200],
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
            else:
                st.info("Play-by-play not available for this game yet.")

    with tab7:
        with st.container(border=True):
            st.markdown("##### 🎯 Shot charts")
            if actions:
                shots = shot_df_from_pbp(actions, alias)
                if shots.empty:
                    st.info("No shot actions detected yet for this team.")
                else:
                    last = shots.iloc[-1]
                    st.info(
                        f"Latest: {last['Player']} {'made' if last['Made'] else 'missed'} — {str(last['Description'])[:120]}"
                    )
                    options = ["All players"] + sorted(shots["Player"].dropna().unique().tolist())
                    shooter = st.selectbox("Shooter filter", options, key="live_shot_shooter")
                    display = shots if shooter == "All players" else shots[shots["Player"] == shooter]
                    st.plotly_chart(draw_court(display, f"{favorite_team} shot chart — blue ○ made, red × missed"), use_container_width=True)
                st.markdown("**Clutch meter**")
                if clutch:
                    st.warning("Clutch-time situation: fourth quarter and within five points.")
                else:
                    st.info("Clutch meter becomes more important in the fourth quarter within five points.")
                st.markdown("**Top plays (this game)**")
                rows_tp = []
                for a in actions:
                    if (a.get("teamTricode") or "") == alias and is_top_play(a.get("description", "")):
                        desc = a.get("description", "")
                        rows_tp.append({
                            "Period": a.get("period", ""),
                            "Clock": a.get("clock", ""),
                            "Top Play": desc,
                            "Why it mattered": explain_play(desc, favorite_team),
                        })
                st.dataframe(pd.DataFrame(rows_tp[-5:]) if rows_tp else previous_game_top_plays(favorite_team), use_container_width=True)
            else:
                st.info("Shot chart needs play-by-play data.")

    with tab8:
        with st.container(border=True):
            st.markdown("##### ✨ Legacy impact & pressure")
            st.info(
                f"{favorite_team} is {'ahead' if margin > 0 else 'tied' if margin == 0 else 'behind'} by {abs(margin)}. "
                "The next stretch matters for turnovers, fouls, and shot quality."
            )
            st.markdown("**What needs to happen next**")
            for item in ["Get stops without fouling", "Protect the defensive glass", "Create clean looks for the main scorer", "Avoid live-ball turnovers"]:
                st.write(f"• {item}")
            if not box_df.empty:
                st.markdown("**Storylines**")
                for line in game_story(favorite_team, margin, prob, box_df):
                    st.write(f"• {line}")
            st.caption("For full legacy modeling, use the Legacy Tracker page.")

    with tab9:
        with st.container(border=True):
            st.markdown("##### 🔮 What-if simulator")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Scenario": f"{'+' if sw >= 0 else ''}{sw} point swing",
                            "New margin": margin + sw,
                            "Win probability": f"{win_prob(margin + sw, period, is_home)}%",
                        }
                        for sw in [10, 5, 0, -5, -10]
                    ]
                ),
                use_container_width=True,
            )


# ==========================================================
# Previous rounds / playoff path helpers
# ==========================================================
FALLBACK_GAME_MVPS = {
    ("New York Knicks", "Atlanta Hawks", 1): ("Jalen Brunson", "Controlled the half court and gave New York the Game 1 tone."),
    ("New York Knicks", "Atlanta Hawks", 2): ("Trae Young", "Late-shot creation and pressure helped Atlanta steal a road game."),
    ("New York Knicks", "Atlanta Hawks", 3): ("Trae Young", "Carried Atlanta's offense in a one-possession finish."),
    ("New York Knicks", "Atlanta Hawks", 4): ("Jalen Brunson", "Reset the series for New York with stronger offensive control."),
    ("New York Knicks", "Atlanta Hawks", 5): ("Karl-Anthony Towns", "Spacing and scoring changed the geometry of the Knicks offense."),
    ("New York Knicks", "Atlanta Hawks", 6): ("Jalen Brunson", "Closed the series with lead-guard control and playoff poise."),
    ("New York Knicks", "Philadelphia 76ers", 1): ("Jalen Brunson", "Set the pace for New York's second-round opener."),
    ("New York Knicks", "Philadelphia 76ers", 2): ("Jalen Brunson", "Protected the late-game margin and pushed the Knicks to a 2-0 series edge."),
    ("Detroit Pistons", "Orlando Magic", 1): ("Paolo Banchero", "Powered Orlando's Game 1 road win."),
    ("Detroit Pistons", "Orlando Magic", 2): ("Cade Cunningham", "Got Detroit's offense organized and tied the series."),
    ("Detroit Pistons", "Orlando Magic", 3): ("Paolo Banchero", "Kept Orlando ahead with star-level shot creation."),
    ("Detroit Pistons", "Orlando Magic", 4): ("Franz Wagner", "Gave Orlando secondary scoring and two-way stability."),
    ("Detroit Pistons", "Orlando Magic", 5): ("Cade Cunningham", "Kept Detroit alive with command of the offense."),
    ("Detroit Pistons", "Orlando Magic", 6): ("Jalen Duren", "Controlled the glass and helped extend the series."),
    ("Detroit Pistons", "Orlando Magic", 7): ("Cade Cunningham", "Delivered the Game 7 control that sent Detroit forward."),
    ("Detroit Pistons", "Cleveland Cavaliers", 1): ("Cade Cunningham", "Organized Detroit's offense and gave the Pistons the series lead."),
    ("Detroit Pistons", "Cleveland Cavaliers", 2): ("Cade Cunningham", "Pushed Detroit to a 2-0 lead with steady lead-option control."),
}

def infer_opponent_from_matchup(matchup, team_name):
    if not matchup or " at " not in str(matchup):
        return "Opponent"
    left, right = str(matchup).split(" at ", 1)
    def short_name(full):
        return full.replace("New York ", "").replace("Philadelphia ", "").replace("Atlanta ", "").replace("Detroit ", "").replace("Cleveland ", "").replace("Oklahoma City ", "").replace("Los Angeles ", "").replace("San Antonio ", "").replace("Minnesota ", "").replace("Portland ", "").replace("Phoenix ", "").strip()
    team_short = short_name(team_name)
    if team_short in left:
        return right
    if team_short in right:
        return left
    return left if right == team_short else right

def mvp_for_game(team_a, team_b, game_num, winner=None):
    for key in [(team_a, team_b, game_num), (team_b, team_a, game_num)]:
        if key in FALLBACK_GAME_MVPS:
            return FALLBACK_GAME_MVPS[key]
    # Generic but still concrete: use the main creator/anchor from winner if known.
    chosen_team = winner if winner in TEAM_PROFILES else team_a
    candidates = TEAM_PROFILES.get(chosen_team, {}).get("starters", [])
    name = candidates[0] if candidates else "Top performer"
    return name, f"Best estimated standout for {chosen_team} based on the game result and team role hierarchy."

def get_current_series_games_for_previous_rounds(team_name):
    _, s = series_for_team(team_name)
    if not s or not s.get("games"):
        return []
    games = []
    opp = s["b"] if team_name == s["a"] else s["a"]
    for idx, g in enumerate(s.get("games", []), start=1):
        row = dict(g)
        row["Game"] = row.get("Game") or f"Game {idx}"
        row["Matchup"] = row.get("Matchup") or f"{team_name} vs {opp}"
        mvp, why = mvp_for_game(team_name, opp, idx, row.get("Winner"))
        row["Game MVP"] = row.get("Game MVP") or mvp
        row["MVP Note"] = row.get("MVP Note") or why
        games.append(row)
    return games

def render_series_history_card(team_a, team_b, games, round_label, result_text=None):
    if not games:
        st.info(f"No game results available yet for {team_a} vs {team_b}.")
        return
    a_wins = sum(1 for g in games if g.get("Winner") == team_a)
    b_wins = sum(1 for g in games if g.get("Winner") == team_b)
    st.markdown("""
    <style>
    .history-card{border:1px solid rgba(0,0,0,.12);border-radius:20px;padding:16px;margin:12px 0;background:linear-gradient(135deg,#ffffff,#f8fafc);box-shadow:0 4px 18px rgba(15,23,42,.06)}
    .history-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}.history-team{text-align:center;font-weight:900;font-size:18px}.history-score{font-size:28px;font-weight:950;color:#ea580c;text-align:center}.game-row{border-top:1px solid rgba(0,0,0,.08);padding:10px 2px}.mvp-pill{display:inline-block;background:#fff7ed;border:1px solid #fed7aa;border-radius:999px;padding:3px 10px;font-weight:800;color:#9a3412}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='history-card'>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1.2,.8,1.2])
    with c1:
        st.image(TEAM_LOGOS.get(team_a,""), width=82)
        st.markdown(f"<div class='history-team'>({TEAM_PROFILES[team_a]['seed']}) {team_a}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='history-score'>{a_wins} - {b_wins}</div>", unsafe_allow_html=True)
        st.caption(round_label)
    with c3:
        st.image(TEAM_LOGOS.get(team_b,""), width=82)
        st.markdown(f"<div class='history-team'>({TEAM_PROFILES[team_b]['seed']}) {team_b}</div>", unsafe_allow_html=True)
    if result_text:
        st.info(result_text)
    for idx, g in enumerate(games, start=1):
        game_num = g.get("Game", f"Game {idx}")
        try:
            n = int(str(game_num).replace("Game", "").strip())
        except Exception:
            n = idx
        if "Game MVP" not in g:
            mvp, why = mvp_for_game(team_a, team_b, n, g.get("Winner"))
        else:
            mvp, why = g.get("Game MVP"), g.get("MVP Note", "Standout performer for this game.")
        st.markdown(f"<div class='game-row'><b>{game_num}</b> · {g.get('Date','Date TBD')} · {g.get('Matchup', team_a+' vs '+team_b)}<br><b>Score:</b> {g.get('Score','Score TBD')}<br><span class='mvp-pill'>Game MVP: {mvp}</span><br><span style='color:#475569'>{why}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_previous_rounds_history(team_name):
    profile = TEAM_PROFILES[team_name]
    first_opp = profile["first_round_opponent"]
    st.subheader("Playoff Path So Far")
    st.caption("Includes logos, scores, winners, and estimated game MVP/standout player for each completed game.")
    first_games = []
    for idx, row in enumerate(FIRST_ROUND_GAME_SCORES.get(team_name, []), start=1):
        r = dict(row)
        n = int(r.get("Game", idx)) if str(r.get("Game", idx)).isdigit() else idx
        mvp, why = mvp_for_game(team_name, first_opp, n, r.get("Winner"))
        r["Game"] = f"Game {n}"
        r["Game MVP"] = mvp
        r["MVP Note"] = why
        first_games.append(r)
    render_series_history_card(team_name, first_opp, first_games, "First Round", profile.get("first_round_result"))

    current_opp = profile.get("current_opponent")
    if current_opp:
        second_games = get_current_series_games_for_previous_rounds(team_name)
        render_series_history_card(team_name, current_opp, second_games, "Current Round / Second Round", series_status_text(team_name))

# ==========================================================
# Sidebar
# ==========================================================
PAGES={
    "🏀 Home Dashboard":"Home Dashboard",
    "🏀 Live Game Center":"Live Game Center",
    "🏀 Playoff Bracket":"Playoff Bracket",
    "🏀 Matchup Lineups":"Matchup Lineups",
    "🏀 Player Playoff Tracker":"Player Playoff Tracker",
    "🏀 Legacy Tracker":"Legacy Tracker",
    "🏀 Previous Rounds":"Previous Rounds",
}
favorite_team=st.sidebar.selectbox("Choose your 2026 NBA playoff team", list(TEAM_PROFILES.keys()), index=list(TEAM_PROFILES.keys()).index("New York Knicks"))
USE_DEMO_BACKUP = st.sidebar.toggle(
    "Use demo backup scores only if NBA API has no game data",
    value=False,
    help="Leave this OFF for true automatic tracking. Turn it ON only when testing or when nba_api is unavailable."
)
profile=TEAM_PROFILES[favorite_team]
labels=list(PAGES.keys())
def_label=st.session_state.pop("page_override", "🏀 Home Dashboard")
page_label=st.sidebar.radio("Choose page", labels, index=labels.index(def_label) if def_label in labels else 0)
page=PAGES[page_label]

# ==========================================================
# Pages
# ==========================================================
if page == "Home Dashboard":
    home_ctx = render_home_matchup_header(favorite_team)
    c1,c2,c3=st.columns(3)
    c1.metric("Status", "Advanced" if home_ctx and home_ctx.get("advanced") else profile["status"])
    home_status = home_ctx["status_text"] if home_ctx and home_ctx.get("advanced") else series_status_text(favorite_team)
    c2.markdown(f"<div class='big-status'>{home_status}</div>", unsafe_allow_html=True)
    c3.metric("Seed", profile["seed"])
    render_game_countdown(favorite_team)
    render_injury_report(favorite_team, home_injury_opponents(favorite_team))
    _, s=series_for_team(favorite_team)
    if s and s.get("games"):
        st.caption(f"Auto-updated from completed games/fallback data · Last app refresh: {datetime.now().strftime('%b %d, %Y %I:%M %p')}")
        st.subheader("Current Series Scores")
        st.dataframe(pd.DataFrame(s["games"]), use_container_width=True)
        st.subheader("Previous Game Top Plays")
        st.dataframe(previous_game_top_plays(favorite_team), use_container_width=True)
        st.subheader("Historical Series Tracking")
        st.dataframe(historic_series_context(favorite_team), use_container_width=True)
    render_team_outlook(favorite_team)

elif page == "Playoff Bracket":
    render_bracket()

elif page == "Previous Rounds":
    st.header(f"{profile['conference']} Previous Rounds")
    render_matchup_header(favorite_team, first_round=True)
    render_previous_rounds_history(favorite_team)

elif page == "Live Game Center":
    render_live_game_center(favorite_team, profile)

elif page == "Player Playoff Tracker":
    render_matchup_header(favorite_team)
    plist=current_roster_names(favorite_team)
    st.caption("Player list is pulled from NBA API current roster/rotation when available. Hard-coded names are used only as backup.")
    player=st.selectbox("Choose player", plist); season=st.selectbox("Season", [CURRENT_NBA_SEASON,"2024-25","2023-24"], index=0)
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
    st.subheader("Legacy Tracker: Current Playoff Stats + What-If Legacy Simulator")

    player_pool = current_roster_names(favorite_team, limit=15)
    player = st.selectbox("Choose player", player_pool)
    logs = playoff_game_logs_for_player(player)
    current = summarize_playoff_logs(logs)

    if logs.empty:
        st.warning("NBA API did not return current playoff game logs for this player. The sliders still work, but the starting values come from safe defaults.")
    else:
        st.success(f"Loaded {current['GP']} current playoff games for {player} from NBA API.")
        show_cols = [c for c in ["GAME_DATE","MATCHUP","WL","MIN","PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","FT_PCT","PLUS_MINUS"] if c in logs.columns]
        st.dataframe(logs[show_cols], use_container_width=True)

    st.markdown("### Current playoff averages")
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("Games", current.get("GP",0))
    m2.metric("PTS", current.get("PTS",0))
    m3.metric("REB", current.get("REB",0))
    m4.metric("AST", current.get("AST",0))
    m5.metric("STL", current.get("STL",0))
    m6.metric("BLK", current.get("BLK",0))

    st.markdown("### Change the stat line to test legacy scenarios")
    c1,c2,c3 = st.columns(3)
    with c1:
        pts = st.slider("Playoff PPG", 0.0, 45.0, float(current.get("PTS", 20.0) or 20.0), 0.5)
        reb = st.slider("Playoff RPG", 0.0, 20.0, float(current.get("REB", 6.0) or 6.0), 0.5)
        ast = st.slider("Playoff APG", 0.0, 15.0, float(current.get("AST", 4.0) or 4.0), 0.5)
    with c2:
        stl = st.slider("Playoff steals per game", 0.0, 4.0, float(current.get("STL", 1.0) or 1.0), 0.1)
        blk = st.slider("Playoff blocks per game", 0.0, 5.0, float(current.get("BLK", 0.5) or 0.5), 0.1)
        plus_minus = st.slider("Average plus/minus", -20.0, 20.0, float(current.get("PLUS_MINUS", 0.0) or 0.0), 0.5)
    with c3:
        fg = st.slider("FG%", 0.300, 0.700, float(current.get("FG_PCT", 0.460) or 0.460), 0.005)
        three = st.slider("3PT%", 0.200, 0.550, float(current.get("FG3_PCT", 0.360) or 0.360), 0.005)
        ft = st.slider("FT%", 0.500, 1.000, float(current.get("FT_PCT", 0.800) or 0.800), 0.005)

    path = build_legacy_path(player, favorite_team, pts, reb, ast, stl, blk, fg, three, plus_minus)
    current_score = float(path.iloc[0]["Projected Legacy Score"])
    title_score = float(path.iloc[-1]["Projected Legacy Score"])

    a,b,c,d = st.columns(4)
    a.metric("Current Legacy Score", current_score)
    b.metric("Championship Scenario Score", title_score)
    c.metric("Possible Gain", round(title_score-current_score,1))
    d.metric("Player-Specific Max", player_legacy_ceiling(player, favorite_team))
    st.caption("The score now starts with the player’s existing career résumé and previous success. LeBron begins near the top already; Brunson and Towns begin above normal Knicks role players; each player has his own ceiling and tier labels.")

    st.plotly_chart(px.bar(path, x="Scenario", y="Projected Legacy Score", color="Player-Specific Tier", title=f"{player} legacy path if {favorite_team} keeps advancing"), use_container_width=True)
    st.dataframe(path, use_container_width=True)

    st.markdown("### Interpretation")
    for line in legacy_takeaways(player, favorite_team, pts, reb, ast, stl, blk, fg, three, plus_minus):
        st.write(f"• {line}")

    st.info("This is an analytical legacy model, not an official ranking. It now combines existing career résumé, current playoff production, efficiency, plus/minus, and round advancement. Actual legacy also depends on signature games, opponent quality, injuries, media narrative, and championships.")

elif page == "Matchup Lineups":
    render_matchup_header(favorite_team)
    if profile["status"] != "Active": st.warning("This team is eliminated, so current matchup lineups are not active.")
    else:
        opp=profile["current_opponent"]
        st.subheader("Projected Starter Matchups")
        st.caption("Starter/rotation estimates use NBA API current-season minutes when available. Actual playoff starters can still change by injury, matchup choice, or coaching decision.")
        st.dataframe(matchup_advantages(favorite_team, opp), use_container_width=True)

        st.subheader("Current Rosters from NBA API")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{favorite_team} current roster / rotation**")
            roster = fetch_current_roster(favorite_team)
            rotation = fetch_team_rotation_by_minutes(favorite_team)
            if not rotation.empty:
                st.dataframe(rotation.drop(columns=[c for c in ["MIN_SORT"] if c in rotation.columns]).head(12), use_container_width=True)
            elif not roster.empty:
                st.dataframe(roster, use_container_width=True)
            else:
                st.warning("NBA API roster lookup failed. Showing backup saved names.")
                st.dataframe(pd.DataFrame({"Player": current_roster_names(favorite_team)}), use_container_width=True)
        with c2:
            st.markdown(f"**{opp} current roster / rotation**")
            roster = fetch_current_roster(opp)
            rotation = fetch_team_rotation_by_minutes(opp)
            if not rotation.empty:
                st.dataframe(rotation.drop(columns=[c for c in ["MIN_SORT"] if c in rotation.columns]).head(12), use_container_width=True)
            elif not roster.empty:
                st.dataframe(roster, use_container_width=True)
            else:
                st.warning("NBA API roster lookup failed. Showing backup saved names.")
                st.dataframe(pd.DataFrame({"Player": current_roster_names(opp)}), use_container_width=True)

        st.subheader("Top Bench / Rotation Players")
        bench=[{"Team":favorite_team,"Player":p} for p in estimated_bench_from_api(favorite_team)]+[{"Team":opp,"Player":p} for p in estimated_bench_from_api(opp)]
        st.dataframe(pd.DataFrame(bench), use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | automatic series tracking | previous rounds | live game center | shot chart")
