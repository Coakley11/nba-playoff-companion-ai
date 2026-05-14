
import html
import re
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
  color: #f8fafc; border-radius: 16px; padding: 14px 16px 16px;
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


def canonical_series_key(team_a, team_b):
    """Stable tricode key for a two-team series (order-independent)."""
    if not team_a or not team_b:
        return ""
    x, y = TEAM_ALIASES.get(team_a, ""), TEAM_ALIASES.get(team_b, "")
    if not x or not y:
        return f"{team_a}-{team_b}"
    return "-".join(sorted([x, y]))


def second_round_series_for_team(team_name):
    """The second-round (semifinal) series shell containing this team, if any."""
    for key, s in build_second_round_series().items():
        if team_name in (s.get("a"), s.get("b")):
            return key, s
    return None, None


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


@st.cache_data(ttl=300)
def build_conference_finals_series_cached(use_demo_backup=False):
    """East/West Conference Finals shells from second-round winners + API games.

    No hard-coded CF pairings: each conference finals matchup is the two teams
    that won the conference's second-round series, discovered from completed games.
    """
    second = build_second_round_series_cached(use_demo_backup)
    out = {}
    for conf in ("East", "West"):
        semis = [(k, s) for k, s in second.items() if s.get("conf") == conf]
        winners = []
        for _k, s in semis:
            w = s.get("winner")
            if w:
                winners.append(w)
        if len(winners) != 2 or winners[0] == winners[1]:
            continue
        t1, t2 = winners[0], winners[1]
        key = canonical_series_key(t1, t2)
        a, b = sorted([t1, t2], key=lambda t: (TEAM_PROFILES.get(t, {}).get("seed", 99), t))
        shell = {"conf": conf, "round": "Conference Finals", "a": a, "b": b, "a_wins": 0, "b_wins": 0, "winner": None, "games": []}
        for g in fetch_completed_games_recent():
            h, aw = g.get("Home"), g.get("Away")
            if h and aw and {h, aw} == {a, b}:
                shell["games"].append({
                    "Game": "",
                    "Date": g.get("Date", ""),
                    "GameDate": g.get("GameDate", ""),
                    "Score": g.get("Score", ""),
                    "Winner": g.get("Winner", ""),
                    "GameID": g.get("GameID", ""),
                    "Source": "NBA API",
                })
        out[key] = shell
    return clean_and_recount_series(out)


def build_conference_finals_series():
    return build_conference_finals_series_cached(globals().get("USE_DEMO_BACKUP", False))


def _cf_champion_for_conference(cf_map, conf):
    for s in cf_map.values():
        if s.get("conf") == conf and s.get("winner"):
            return s.get("winner")
    return None


@st.cache_data(ttl=300)
def build_nba_finals_series_cached(use_demo_backup=False):
    """NBA Finals shell once both conference champions exist; games from API only."""
    cf = build_conference_finals_series_cached(use_demo_backup)
    east_ch = _cf_champion_for_conference(cf, "East")
    west_ch = _cf_champion_for_conference(cf, "West")
    if not east_ch or not west_ch:
        return {}
    a, b = sorted([east_ch, west_ch], key=lambda t: (TEAM_PROFILES.get(t, {}).get("seed", 99), t))
    key = canonical_series_key(east_ch, west_ch)
    shell = {"conf": "NBA Finals", "round": "NBA Finals", "a": a, "b": b, "a_wins": 0, "b_wins": 0, "winner": None, "games": []}
    for g in fetch_completed_games_recent():
        h, aw = g.get("Home"), g.get("Away")
        if h and aw and {h, aw} == {a, b}:
            shell["games"].append({
                "Game": "",
                "Date": g.get("Date", ""),
                "GameDate": g.get("GameDate", ""),
                "Score": g.get("Score", ""),
                "Winner": g.get("Winner", ""),
                "GameID": g.get("GameID", ""),
                "Source": "NBA API",
            })
    return clean_and_recount_series({key: shell})


def build_nba_finals_series():
    return build_nba_finals_series_cached(globals().get("USE_DEMO_BACKUP", False))


def infer_next_round_series(round_name, conf=None):
    """Return series dict(s) for Conference Finals or NBA Finals (API-driven).

    Conference Finals are built from second-round winners per conference.
    NBA Finals are built from conference-finals champions (not from semis).
    """
    if round_name == "Conference Finals":
        cf = build_conference_finals_series()
        if not cf:
            return None
        if conf:
            sub = {k: v for k, v in cf.items() if v.get("conf") == conf}
            return sub if sub else None
        return cf
    if round_name == "NBA Finals":
        nf = build_nba_finals_series()
        return nf if nf else None
    return None


def series_for_team(team_name):
    """Primary playoff series for this team: Finals, then Conference Finals, then active second round.

    After a team clinches a second-round series but before the conference finals shell exists
    (waiting on the other semi), returns (None, None) so the dashboard can show advancement context
    instead of the finished semi game log as the 'current' series.
    """
    nf = build_nba_finals_series()
    for key, s in nf.items():
        if team_name in (s.get("a"), s.get("b")):
            return key, s

    cf = build_conference_finals_series()
    for key, s in cf.items():
        if team_name in (s.get("a"), s.get("b")):
            return key, s

    second = build_second_round_series()
    sk, ss = None, None
    for key, s in second.items():
        if team_name in (s.get("a"), s.get("b")):
            sk, ss = key, s
            break
    if not ss:
        return None, None
    if ss.get("winner") == team_name:
        in_cf = any(team_name in (s.get("a"), s.get("b")) for s in (cf or {}).values())
        if not in_cf:
            return None, None
    return sk, ss


def fan_nick(team_name):
    """Short franchise handle for fan-first copy (e.g. Cleveland Cavaliers → Cavaliers)."""
    if not team_name:
        return "your team"
    return str(team_name).split()[-1]


def series_status_text(team_name):
    _, s = series_for_team(team_name)
    if not s:
        nick = fan_nick(team_name)
        _, semi = second_round_series_for_team(team_name)
        if semi and semi.get("winner") == team_name:
            return (
                f"You clinched the second round — {nick} advance while the other semi decides your next opponent."
            )
        if semi and semi.get("winner") and semi.get("winner") != team_name:
            w = semi["winner"]
            return f"That second-round run ended against {fan_nick(w)} — you're done for this postseason, but history pages still tell the story."
        return f"No active series on the board for {nick} right now — check the bracket when the next round locks."
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    team_w = aw if team_name == a else bw
    opp = b if team_name == a else a
    opp_w = bw if team_name == a else aw
    source_note = "" if s.get("source") == "NBA API" else f" ({s.get('source','')})"
    rnd = s.get("round", "Playoffs")
    if team_w > opp_w:
        ledger = f"You're up {team_w}-{opp_w} on {fan_nick(opp)}"
    elif team_w < opp_w:
        ledger = f"You're down {team_w}-{opp_w} to {fan_nick(opp)} — still time to flip the script"
    else:
        ledger = f"You're deadlocked {team_w}-{opp_w} with {fan_nick(opp)}"
    return f"{rnd}: {ledger}{source_note}"


def historic_series_context(team_name):
    _, s = series_for_team(team_name)
    if not s:
        return pd.DataFrame()
    a, b = s["a"], s["b"]
    tw = s["a_wins"] if team_name == a else s["b_wins"]
    ow = s["b_wins"] if team_name == a else s["a_wins"]
    opp = b if team_name == a else a
    nick = fan_nick(team_name)
    on = fan_nick(opp)
    last = s.get("games", [])[-1] if s.get("games") else None
    latest_note = (
        f" Last time out ({last.get('Game')} · {last.get('Date')}): {last.get('Score')}."
        if last
        else " Waiting on the first completed game in the feed."
    )
    if tw == 1 and ow == 0:
        note = f"You're ahead early — protect the next home game and you can really squeeze {on}."
    elif tw == 2 and ow == 0:
        note = f"2-0 is a monster spot for {nick} fans — one more punch and the math gets brutal for {on}."
    elif tw == 1 and ow == 1:
        note = f"Split so far — treat the next game like a reset; whoever owns the first six minutes usually rides the crowd energy."
    elif tw < ow:
        note = f"You're chasing {on} — the honest path back is a defensive tone-setter next, then steal a road game before panic sets in."
    elif tw == 0 and ow == 0:
        note = f"Series hasn't hit the log yet — Game 1 is where {nick} stamps identity vs {on}."
    else:
        note = f"You've got the edge on {on}, but close-out basketball is about rebounds, turnovers, and not gifting free points."
    return pd.DataFrame(
        [
            {
                "Series Status": series_status_text(team_name),
                "Data Source": s.get("source", ""),
                "Historical Context": note + latest_note,
            }
        ]
    )

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
    nick = fan_nick(team_name)
    if player in star_names:
        base = f"As a {nick} fan, watch {player} closely — availability swings your ceiling in this matchup."
    else:
        base = f"For {nick}, {player} matters for depth minutes and matchup flexibility."
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

def render_injury_report(team_name, opponent_name=None, show_page_header=True, fan_perspective_team=None):
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
        if fan_perspective_team:
            if tm == fan_perspective_team:
                st.caption(f"Your {fan_nick(tm)} — who to monitor before you get emotionally invested at tipoff.")
            else:
                st.caption(f"Opponent ({fan_nick(tm)}) — what could swing the matchup against your {fan_nick(fan_perspective_team)}.")
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
    nick = fan_nick(team)
    return [
        f"Through a {nick} lens: {prof['resume']}",
        f"What this means for your franchise story: {prof['team_context']}",
        f"If you're comparing résumés out loud, think about names like {', '.join(comps[:4])} — not identical players, but useful bar talk.",
        f"With these sliders, {player} moves from **{player_specific_tier(base, player, team)}** toward **{player_specific_tier(title, player, team)}** if {nick} hang a banner. That's the fan fantasy path.",
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
    alias = TEAM_ALIASES[team_name]
    nick = fan_nick(team_name)
    if box_df.empty:
        return [f"{nick} live box score is still loading — hang tight for real numbers."]
    df = box_df[box_df["Team"] == alias]
    lines = []
    if margin > 0:
        lines.append(f"Right now you're up {margin} — ride the run but don't get careless with fouls or turnovers.")
    elif margin == 0:
        lines.append("Score is knotted — next mini-run swings the building noise and the refs' whistle tone.")
    else:
        lines.append(f"You're down {abs(margin)} — the comeback starts with one clean defensive stop chain, then a good shot.")
    lines.append(
        f"Your guys on the floor: {int(df['PTS'].sum())} pts, {int(df['REB'].sum())} reb, {int(df['AST'].sum())} ast tracked in this feed."
    )
    lines.append("What you want to see next: extra pass threes, no live-ball gifts, and the glass on your end.")
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
# Matchup intelligence / series analysis engine
# ==========================================================
def _intel_parse_points_from_score(score_str, team, opp):
    """Extract each team's point total from common score strings (best-effort)."""
    if not score_str:
        return None, None
    s = re.sub(r"\([^)]*\)", "", str(score_str))
    chunks = [c.strip() for c in re.split(r",\s*", s) if c.strip()]
    found = {}
    for ch in chunks:
        m = re.search(r"(\d{2,3})\s*$", ch)
        if not m:
            continue
        pts = int(m.group(1))
        label = ch[: m.start()].strip().lower()
        for tm in (team, opp):
            tl = tm.lower()
            last = tm.split()[-1].lower()
            alias = TEAM_ALIASES.get(tm, "").lower()
            if tl in label or last in label or alias in label:
                found[tm] = pts
    if team in found and opp in found:
        return found[team], found[opp]
    nums = re.findall(r"\b(\d{2,3})\b", s)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return None, None


def _intel_margin_series(games, team, opp):
    """Per game: margin from team's perspective (positive = team won by that many)."""
    rows = []
    for g in games or []:
        w = g.get("Winner")
        tp, op = _intel_parse_points_from_score(g.get("Score", ""), team, opp)
        if w == team and tp is not None and op is not None:
            rows.append(tp - op)
        elif w == opp and tp is not None and op is not None:
            rows.append(-(tp - op))
        elif w == team:
            rows.append(8)
        elif w == opp:
            rows.append(-8)
    return rows


def _intel_injury_signal(team_name, opp_name):
    """Rough availability pressure for narrative (counts + one headline name)."""
    teams = [team_name, opp_name]
    out = {"team_out": 0, "team_q": 0, "opp_out": 0, "opp_q": 0, "headline": None}
    for i, tm in enumerate(teams):
        df, _ = get_injury_report(tm)
        if df is None or df.empty:
            continue
        for _, r in df.head(5).iterrows():
            stt = str(r.get("Status", "")).lower()
            pl = str(r.get("Player", ""))
            if "out" in stt:
                if i == 0:
                    out["team_out"] += 1
                else:
                    out["opp_out"] += 1
                if not out["headline"]:
                    out["headline"] = (tm, pl, "out")
            elif any(x in stt for x in ("question", "doubt", "game time")):
                if i == 0:
                    out["team_q"] += 1
                else:
                    out["opp_q"] += 1
                if not out["headline"]:
                    out["headline"] = (tm, pl, "questionable")
    return out


def _intel_variant(seed, options):
    h = sum(ord(c) for c in str(seed)) % len(options)
    return options[h]


MATCHUP_INTEL_PAIR_HOOKS = {
    frozenset({"New York Knicks", "Philadelphia 76ers"}): "**Brunson pick-and-roll** vs **Embiid drop depth** decides whether Philly gets clean weak-side threes or New York lives at the line.",
    frozenset({"Oklahoma City Thunder", "Los Angeles Lakers"}): "**Thunder transition** vs **Lakers early help back** — the first four minutes off misses usually set the night's pace.",
    frozenset({"Detroit Pistons", "Cleveland Cavaliers"}): "**Detroit offensive rebounding** vs **Cleveland's help-and-recover timing** can override cold half-court stretches.",
    frozenset({"San Antonio Spurs", "Minnesota Timberwolves"}): "**Wembanyama rim deterrence** vs **Edwards downhill pressure** forces the defense to pick between early doubles and one-on-one survival.",
}


def intel_games_opponent_and_record(team_name):
    """Resolve opponent, game rows, wins, and round label for analysis."""
    prof = TEAM_PROFILES[team_name]
    _, s = series_for_team(team_name)
    games = []
    opp = None
    round_label = prof.get("round", "Playoffs")
    if s:
        opp = s["b"] if team_name == s["a"] else s["a"]
        games = list(s.get("games") or [])
        round_label = s.get("round", round_label)
        tw = int(s.get("a_wins", 0)) if team_name == s["a"] else int(s.get("b_wins", 0))
        ow = int(s.get("b_wins", 0)) if team_name == s["a"] else int(s.get("a_wins", 0))
        return s, opp, games, tw, ow, round_label, "current"
    if prof.get("status") == "Eliminated":
        opp = prof.get("first_round_opponent")
        games = [dict(g) for g in FIRST_ROUND_GAME_SCORES.get(team_name, [])]
        tw = sum(1 for g in games if g.get("Winner") == team_name)
        ow = sum(1 for g in games if g.get("Winner") == opp)
        return None, opp, games, tw, ow, "First round (series complete)", "eliminated"
    _, s2 = second_round_series_for_team(team_name)
    if s2:
        opp = s2["b"] if team_name == s2["a"] else s2["a"]
        games = list(s2.get("games") or [])
        round_label = s2.get("round", round_label)
        tw = int(s2.get("a_wins", 0)) if team_name == s2["a"] else int(s2.get("b_wins", 0))
        ow = int(s2.get("b_wins", 0)) if team_name == s2["a"] else int(s2.get("a_wins", 0))
        return s2, opp, games, tw, ow, round_label, "current"
    opp = prof.get("current_opponent") or prof.get("first_round_opponent")
    return None, opp, [], 0, 0, round_label, "waiting"


def build_matchup_intelligence_sections(team_name):
    """Return nine analyst-style sections; inputs are series + profiles + injuries."""
    s, opp, games, tw, ow, rnd, mode = intel_games_opponent_and_record(team_name)
    if not opp or opp not in TEAM_PROFILES:
        return None, "We need a locked opponent for your sidebar team — try again once the bracket ties this matchup."

    t_prof = TEAM_PROFILES[team_name]
    o_prof = TEAM_PROFILES[opp]
    margins = _intel_margin_series(games, team_name, opp)
    inj = _intel_injury_signal(team_name, opp)
    last_w = games[-1].get("Winner") if games else None
    prev_w = games[-2].get("Winner") if len(games) > 1 else None
    blowouts_for = sum(1 for m in margins if m >= 15)
    blowouts_against = sum(1 for m in margins if m <= -15)
    close_games = sum(1 for m in margins if abs(m) <= 7)
    avg_abs = int(sum(abs(m) for m in margins) / len(margins)) if margins else 0

    t_strengths = t_prof.get("strengths", [])
    t_concerns = t_prof.get("concerns", [])
    o_strengths = o_prof.get("strengths", [])
    o_concerns = o_prof.get("concerns", [])
    t_star = (t_prof.get("starters") or [""])[0]
    o_star = (o_prof.get("starters") or [""])[0]
    x_name = (t_prof.get("subs") or t_prof.get("starters", [""]))[0] if t_prof.get("subs") else (t_prof.get("starters") or ["Rotation"])[-1]

    seed = f"{team_name}|{opp}|{tw}{ow}|{len(games)}"
    Y = fan_nick(team_name)
    O = fan_nick(opp)

    # --- 1. Key matchup advantage (your team's broadcast) ---
    if tw > ow:
        if margins:
            adv_body = _intel_variant(
                seed + "adv",
                [
                    f"You're seeing **{Y}** turn **{t_strengths[0] if t_strengths else 'your identity'}** into wins — **{tw}-{ow}** on {O}. What you want on film review is {O} never getting comfortable early-clock.",
                    f"The ledger **{tw}-{ow}** matches what you've felt: **{t_strengths[1] if len(t_strengths) > 1 else (t_strengths[0] if t_strengths else 'execution')}** is winning the physical battle for {Y}.",
                    f"Up **{tw}-{ow}**, you're dictating terms — especially **{t_strengths[0] if t_strengths else 'star creation'}** — and making {O} take tougher late-clock shots.",
                ],
            )
        else:
            adv_body = _intel_variant(
                seed + "advnom",
                [
                    f"Bracket says you're up **{tw}-{ow}** — even before full box parsing, it passes the eye test: **{t_strengths[0] if t_strengths else 'your best habits'}** are showing in winning minutes.",
                    f"You're ahead **{tw}-{ow}** where it counts. {O} has to steal **first good look** after misses — you feel that swing in the building.",
                    f"**{tw}-{ow}** favors {Y}; what you hope {O} never solves is taking away **{t_strengths[0] if t_strengths else 'paint touches'}** without giving up the arc.",
                ],
            )
    elif ow > tw:
        if margins:
            adv_body = _intel_variant(
                seed + "advo",
                [
                    f"Tough spot: **{O}** leads **{ow}-{tw}** leaning on **{o_strengths[0] if o_strengths else 'their best habits'}**. Your comeback map: fewer clean looks for **{o_star.split()[-1] if o_star else 'their star'}** and more **extra possessions**.",
                    f"The **{ow}-{tw}** scoreboard reflects {O} winning the **{o_strengths[0] if o_strengths else 'scheme'}** battle. Honest counter for {Y} fans: attack **{o_concerns[0] if o_concerns else 'their weak-side help'}** until it cracks.",
                    f"{O} has controlled **{ow}-{tw}** by making you defend **{o_strengths[1] if len(o_strengths) > 1 else (o_strengths[0] if o_strengths else 'multiple actions')}** without fouling — still doable, just louder in the huddle.",
                ],
            )
        else:
            adv_body = _intel_variant(
                seed + "advonm",
                [
                    f"{O} sits **{ow}-{tw}** — you need a cleaner **{t_strengths[0] if t_strengths else 'half-court'}** night and to stress **{o_concerns[0] if o_concerns else 'their turnover risk'}**.",
                    f"Trailing **{ow}-{tw}**, you're chasing **{o_strengths[0] if o_strengths else 'their best nights'}** with sharper **shot selection** and fewer **live-ball turnovers** — boring, but that's the door back in.",
                    f"The **{ow}-{tw}** hole means hunting **early switches** before {O} sets its **drop/tag** comfort zone.",
                ],
            )
    elif games:
        adv_body = _intel_variant(
            seed + "adv_even",
            [
                f"Deadlocked **{tw}-{ow}** — you win the night when **{t_strengths[0] if t_strengths else 'transition'}** turns into real points and you kill live-ball turnovers.",
                f"**{tw}-{ow}** is a **shot-quality race** for {Y} fans: your **{t_strengths[0] if t_strengths else 'spacing'}** vs their **{o_strengths[0] if o_strengths else 'rim protection'}**.",
                f"Next game is a swing — you want **{t_strengths[0] if t_strengths else 'your pace'}**; {O} wants a **{o_strengths[0] if o_strengths else 'grind'}** mud fight.",
            ],
        )
    else:
        adv_body = (
            f"Games aren't in the log yet — your preview heart still starts with **{t_strengths[0] if t_strengths else 'half-court execution'}** "
            f"vs **{o_strengths[0] if o_strengths else 'their set defense'}** once Game 1 posts."
        )

    hook = MATCHUP_INTEL_PAIR_HOOKS.get(frozenset({team_name, opp}))
    if hook:
        adv_body = adv_body.rstrip() + " " + hook
    if blowouts_for >= 1 and any("rebound" in (x or "").lower() for x in t_strengths):
        adv_body += f" You should feel good about **{Y} owning the glass** when help stays home."
    if blowouts_for >= 1 and any("pace" in (x or "").lower() or "transition" in (x or "").lower() for x in t_strengths):
        adv_body += f" **Transition runs** off stops have been your separator — keep pushing that edge."

    # --- 2. Biggest tactical concern ---
    concern_bits = []
    if inj.get("headline"):
        tm_h, pl_h, tag_h = inj["headline"]
        concern_bits.append(
            f"**{pl_h}** ({tm_h}) flagged **{tag_h}** — worth knowing so you're not blindsided at tip"
        )
    if inj["team_out"] or inj["team_q"]:
        concern_bits.append(
            f"your own room has stress (**{inj['team_out']}** out / **{inj['team_q']}** questionable signals)"
        )
    concern_bits.append(
        f"{O} can hurt you where you're thin: **{t_concerns[0] if t_concerns else 'slow rotations'}** vs their **{o_strengths[0] if o_strengths else 'shot creation'}**"
    )
    concern_body = "What should worry you most: " + " and ".join(concern_bits[:2]) + "."

    # --- 3. X-factor ---
    x_body = _intel_variant(
        seed + "xf",
        [
            f"**{x_name}** is your sneaky swing piece — when starters sit, {O} often loses juice if **{o_concerns[-1] if o_concerns else 'their depth'}** gets tested in foul trouble.",
            f"Keep eyes on **{x_name}** — these series flip when a non-headline guy bankrolls **spacing, extra possessions, or defensive plays** in a six-minute second-quarter stretch.",
            f"If **{x_name}** hits and avoids getting hunted, your stars stay fresher for late **pick-and-roll** possessions.",
        ],
    )

    # --- 4. Most important adjustment ---
    if blowouts_against >= 2:
        adj = f"You've been blown out multiple times — the fix you want to see is **early help rules + transition get-backs** so **{o_star.split()[-1] if o_star else O}** stops getting runway."
    elif blowouts_for >= 2:
        adj = f"You've shown you can **run away** from {O} — expect them to **slow the game**, shrink transition, and try to strand you in **late-clock isolations**."
    elif close_games >= max(2, len(margins) - 1) and margins:
        adj = f"**{close_games}** nail-biters (avg ~{avg_abs} pts) — your path is **ATO execution, SLOB/BLOB clarity, and winning the first six minutes after halftime**."
    else:
        adj = _intel_variant(
            seed + "adj",
            [
                f"Rotation chess — **rebounding vs switching** — whoever forces the other into **backup coverages** first usually owns the middle quarters.",
                f"Watch for a **PnR coverage tweak** on **{o_star.split()[-1] if o_star else O}** when your three goes cold.",
                f"**Side PnR placement** and **weak-side tag timing** — {O} wants **{t_star.split()[-1] if t_star else 'your star'}** off the nail without free corners.",
            ],
        )

    # --- 5. Defensive matchup problems ---
    def_body = _intel_variant(
        seed + "def",
        [
            f"You have to solve how {O} runs **{o_strengths[0] if o_strengths else 'star touches'}** in **spread PnR** — weak-side help is getting stretched and skips are turning into **clean threes**.",
            f"The stress point is **{o_star}** attacking **{t_concerns[0] if t_concerns else 'your point of attack'}** — help opens **ORBs and dump-offs** that hurt on the second side.",
            f"{O}'s **{o_strengths[1] if len(o_strengths) > 1 else (o_strengths[0] if o_strengths else 'size')}** forces you to pick: **switch mismatches** or **over-help rebound holes**.",
        ],
    )

    # --- 6. Momentum shift ---
    if last_w == team_name and prev_w == team_name:
        mom_txt = f"You're rolling — **back-to-back** wins for {Y} until {O} lands a **counterpunch quarter**."
        mom_class = "up"
    elif last_w == opp and prev_w == opp:
        mom_txt = f"{O} is stacking Ws — you need a **tone-setting defensive first quarter** next time out to flip how this feels on the couch."
        mom_class = "down"
    elif last_w == team_name:
        mom_txt = f"You took the last one — ride **possession quality** and **defensive rebounding** into the next tip."
        mom_class = "up"
    elif last_w == opp:
        mom_txt = f"{O} answered last — expect **scheme tweaks** and **extra physicality on screens** early; that's your cue to punch first."
        mom_class = "down"
    else:
        mom_txt = f"Momentum resets until the next result — **Game 1 (or next game)** sets whistle tone and pace for {Y} fans."
        mom_class = "flat"

    # --- 7. Clutch-time edge ---
    if not margins:
        clutch = "Once games populate, this reads how **tight vs blowout** nights shape your late-game stress as a fan."
    elif close_games >= len(margins) // 2 + 1:
        clutch = f"This has been a **nail-biter series** for you — clutch belongs to whoever wins **FTs, turnovers, and ORB on late misses**, not just the last shot."
    else:
        clutch = f"Some nights have broken open — for {Y}, clutch is less about one play and more about **avoiding the avalanche quarter** (**live-ball turnovers**, **transition threes**)."

    # --- 8. Pressure meter (higher = more heat on you as a fan) ---
    gp = tw + ow
    diff = tw - ow
    if mode == "eliminated":
        pressure = 88
        p_label = "Season-defining"
        p_note = "Honest mode: the run ended — what broke schematically and what still makes you proud of this group."
    elif gp == 0:
        pressure = 32
        p_label = "Pre-series"
        p_note = "Nerves are normal — the meter sharpens once Game 1 hits the log."
    elif abs(diff) >= 3 and gp >= 3:
        pressure = 22 if diff > 0 else 92
        p_label = "Series separation"
        p_note = (
            f"You've built cushion — enjoy it, but stay sharp; {O} needs a schematic shock, not just makes."
            if diff > 0
            else f"You're in a hole — the believable comeback starts with **defense-first quarters** and **no live-ball gifts**."
        )
    elif diff <= -2 and max(tw, ow) >= 3:
        pressure = 86
        p_label = "Catch-up heat"
        p_note = f"Every trip feels loud — timeouts, fouls, and boards decide how you feel walking out."
    elif diff >= 2 and max(tw, ow) >= 3:
        pressure = 34
        p_label = "Close-out leverage"
        p_note = f"You've got margin — complacency and whistle swings are the real villains now, not talent."
    elif tw == ow and gp >= 4:
        pressure = 58
        p_label = "Chess-match heat"
        p_note = f"Even series — lineups, health, and one hot quarter swing how {Y} fans sleep."
    else:
        pressure = int(40 + min(22, gp * 5) + abs(diff) * 4)
        pressure = min(88, max(24, pressure))
        p_label = "Series calibration"
        p_note = f"Still learning who imposes pace and paint touches early — that's the {Y} fan homework."

    # --- 9. Coaching chess match ---
    chess = _intel_variant(
        seed + "ch",
        [
            f"Timeout chess: {O} toggles **coverage on {t_star.split()[-1] if t_star else 'your star'}**; you counter with **off-ball screens** to hunt **switches**.",
            f"Rotation length — whoever shortens the bench without bleeding minutes usually stabilizes **your glass**.",
            f"Series-long bet: **help at the nail** vs **corner skips** — coaches sell out one to steal the other.",
        ],
    )

    # Star pressure (woven into pressure card)
    star_pressure = _intel_variant(
        seed + "sp",
        [
            f"**{t_star}** carries your heaviest **trap/double** decisions when offense stalls; {O} lives with rotations if it means **contested twos**.",
            f"**{t_star}**'s **usage vs efficiency** trade is the emotional ride — {O} wants late clocks and **bodies at the level**.",
            f"The narrative pressure you feel on **{t_star}** is real because **{o_star}** is the clearest counter-star.",
        ],
    )

    sections = [
        ("1", "Key matchup advantage", "🏆", adv_body, "good", None),
        ("2", "Biggest tactical concern", "⚠️", concern_body, "warn", None),
        ("3", "X-factor player", "✨", x_body, "neutral", None),
        ("4", "Most important adjustment", "🧭", adj, "neutral", None),
        ("5", "Defensive matchup problems", "🛡️", def_body, "warn", None),
        ("6", "Momentum shift", "📈", mom_txt, mom_class, "momentum"),
        ("7", "Clutch-time edge", "⏱️", clutch, "neutral", None),
        ("8", "Pressure meter + star load", "🎯", f"**{p_label}** ({pressure}/100). {p_note} {star_pressure}", "neutral", None),
        ("9", "Coaching chess match", "♟️", chess, "neutral", None),
    ]
    meta = {
        "opp": opp,
        "round": rnd,
        "tw": tw,
        "ow": ow,
        "games_n": len(games),
        "mode": mode,
        "pressure": pressure,
    }
    return meta, sections


def _inject_matchup_intel_css():
    st.markdown(
        """
<style>
.mi-wrap { max-width: 1100px; margin: 0 auto; }
.mi-card {
  border-radius: 14px;
  padding: 14px 16px 16px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
  border-left: 4px solid #38bdf8;
}
.mi-card.mi-good { border-left-color: #22c55e; }
.mi-card.mi-warn { border-left-color: #f97316; }
.mi-card.mi-neutral { border-left-color: #64748b; }
.mi-card.mi-mom-up { border-left-color: #16a34a; background: linear-gradient(135deg, #f0fdf4, #ffffff); }
.mi-card.mi-mom-down { border-left-color: #dc2626; background: linear-gradient(135deg, #fef2f2, #ffffff); }
.mi-card.mi-mom-flat { border-left-color: #94a3b8; }
.mi-num { font-size: 11px; font-weight: 800; color: #94a3b8; letter-spacing: 0.06em; }
.mi-title { font-size: 16px; font-weight: 900; color: #0f172a; margin: 2px 0 8px; display: flex; align-items: center; gap: 8px; }
.mi-body { font-size: 14px; line-height: 1.55; color: #334155; }
.mi-bar { height: 8px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin-top: 8px; }
.mi-bar > span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #38bdf8, #6366f1); }
</style>
""",
        unsafe_allow_html=True,
    )


def render_matchup_intelligence(team_name):
    _inject_matchup_intel_css()
    meta, payload = build_matchup_intelligence_sections(team_name)
    if meta is None:
        st.warning(payload)
        return
    opp = meta["opp"]
    st.markdown(
        f"<div class='mi-wrap'><p style='color:#64748b;font-size:14px;margin:0 0 12px'>"
        f"<strong style='color:#0f172a'>Your {html.escape(fan_nick(team_name))}</strong> vs "
        f"<strong style='color:#0f172a'>{html.escape(fan_nick(opp))}</strong> · "
        f"{html.escape(meta['round'])} · You at <strong>{meta['tw']}-{meta['ow']}</strong>"
        f" · {meta['games_n']} games in log</p></div>",
        unsafe_allow_html=True,
    )
    for num, title, icon, body, tone, kind in payload:
        if kind == "momentum":
            cls = f"mi-mom-{tone}"
        else:
            cls = {
                "good": "mi-good",
                "warn": "mi-warn",
                "neutral": "mi-neutral",
                "up": "mi-mom-up",
                "down": "mi-mom-down",
                "flat": "mi-mom-flat",
            }.get(tone, "mi-neutral")
        safe_title = html.escape(f"{icon} {title}")
        # Allow bold markdown from body — convert ** to <strong> lightly
        b = str(body)
        b = html.escape(b)
        b = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", b)
        extra = ""
        if num == "8":
            pv = max(5, min(100, int(meta.get("pressure", 50))))
            extra = f'<div class="mi-bar" title="Fan stress meter for {html.escape(fan_nick(team_name))} (higher = heavier)"><span style="width:{pv}%"></span></div>'
        st.markdown(
            f"<div class='mi-card {cls}'><div class='mi-num'>SECTION {num}</div>"
            f"<div class='mi-title'>{safe_title}</div><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )


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
def sibling_second_round_key(current_key, second_map):
    """The other second-round series in the same conference (dynamic bracket wiring)."""
    conf = second_map.get(current_key, {}).get("conf")
    if not conf:
        return None
    others = [k for k, s in second_map.items() if k != current_key and s.get("conf") == conf]
    return others[0] if len(others) == 1 else None


def next_round_context_for_team(team_name):
    """Return next-round display context when the team's second-round series is complete
    but conference finals are not yet formed (waiting on the other conference semi).

    Once conference finals (or finals) exist for this team, returns None — the home
    header uses ``series_for_team`` directly for that matchup.
    """
    _, s_active = series_for_team(team_name)
    if s_active and s_active.get("round") in ("Conference Finals", "NBA Finals"):
        return None

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
    paired_key = sibling_second_round_key(current_key, series_map)
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

def resolve_home_matchup_context(team_name):
    """Resolve current matchup / round for the Home Dashboard (no Streamlit output)."""
    profile = TEAM_PROFILES[team_name]
    _k, s = series_for_team(team_name)
    rnd = (s or {}).get("round", "")
    if s and rnd in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return {
            "mode": "bracket_series",
            "series": s,
            "round_label": rnd,
            "opponent": opp,
            "opponent_display": opp,
            "advanced": False,
            "bracket_series": True,
            "ctx": None,
        }
    ctx = next_round_context_for_team(team_name)
    if not ctx or not ctx.get("advanced"):
        opp = profile.get("current_opponent") or profile["first_round_opponent"]
        return {
            "mode": "standard",
            "series": s,
            "round_label": profile.get("round", "Playoffs"),
            "opponent": opp,
            "opponent_display": opp,
            "advanced": False,
            "bracket_series": False,
            "ctx": ctx,
        }
    return {
        "mode": "waiting_cf",
        "series": None,
        "round_label": ctx["round_label"],
        "opponent": None,
        "opponent_display": ctx.get("opponent_text", "TBD"),
        "opponents": ctx.get("opponents", []),
        "advanced": True,
        "bracket_series": False,
        "ctx": ctx,
    }


def _inject_home_command_center_css():
    st.markdown(
        """
<style>
.cmd-shell { max-width: 1200px; margin: 0 auto 8px auto; }
.cmd-hero {
  position: relative;
  border-radius: 20px;
  padding: 20px 18px 18px;
  margin-bottom: 14px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 18px 48px rgba(0,0,0,0.45);
  background: radial-gradient(120% 80% at 10% 0%, rgba(255,255,255,0.07) 0%, transparent 55%),
    linear-gradient(145deg, var(--cmd-bg0,#0b1220) 0%, var(--cmd-bg1,#111827) 45%, #0f172a 100%);
}
.cmd-hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, transparent 38%);
}
.cmd-hero-inner { position: relative; z-index: 1; color: #f8fafc; font-family: system-ui,-apple-system,sans-serif; }
.cmd-kicker { font-size: 11px; font-weight: 800; letter-spacing: 0.2em; text-transform: uppercase; color: #94a3b8; text-align: center; margin-bottom: 8px; }
.cmd-row { display: flex; align-items: center; justify-content: space-between; gap: 16px 24px; flex-wrap: wrap; }
.cmd-logo { width: clamp(72px, 14vw, 112px); height: auto; filter: drop-shadow(0 6px 18px rgba(0,0,0,0.55)); }
.cmd-vs { font-size: 13px; font-weight: 900; color: #64748b; letter-spacing: 0.12em; }
.cmd-center { text-align: center; min-width: min(100%, 260px); flex: 1 1 240px; }
.cmd-opp-logos { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 10px; min-width: 72px; }
.cmd-match { font-size: clamp(1.15rem, 3.2vw, 1.75rem); font-weight: 900; line-height: 1.15; margin: 0 0 6px; }
.cmd-round { display: inline-block; font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); color: #e2e8f0; margin-bottom: 8px; }
.cmd-scoreline { font-size: clamp(1.6rem, 4vw, 2.35rem); font-weight: 950; color: #fbbf24; letter-spacing: 0.06em; margin: 4px 0 10px; }
.cmd-rail { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 4px; }
.cmd-pill { font-size: 11px; font-weight: 800; padding: 5px 11px; border-radius: 999px; background: rgba(15,23,42,0.55); border: 1px solid rgba(148,163,184,0.35); color: #e2e8f0; }
.cmd-pill--accent { border-color: var(--cmd-accent, #38bdf8); color: #f0f9ff; background: var(--cmd-accent-soft, rgba(56,189,248,0.15)); }
.cmd-headline { text-align: center; font-size: 15px; font-weight: 800; color: #f1f5f9; margin: 12px auto 0; max-width: 38rem; line-height: 1.35; }
.cmd-inj { margin-top: 12px; font-size: 11px; color: #cbd5e1; text-align: center; line-height: 1.45; }
.cmd-sec { margin: 18px 0 8px; font-size: 13px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; border-bottom: 1px solid rgba(148,163,184,0.25); padding-bottom: 6px; }
.cmd-tile { background: rgba(15,23,42,0.55); border: 1px solid rgba(71,85,105,0.45); border-radius: 14px; padding: 10px 12px; text-align: center; }
.cmd-tile .v { font-size: 1.35rem; font-weight: 900; color: #f8fafc; }
.cmd-tile .k { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.cmd-next { background: rgba(15,23,42,0.45); border-radius: 14px; padding: 12px 14px; border: 1px solid rgba(71,85,105,0.4); margin-bottom: 12px; }
.cmd-next-title { font-size: 12px; font-weight: 800; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.cmd-grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; }
@media (max-width: 700px) {
  .cmd-row { flex-direction: column; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def _home_storyline_headline(team_name, hctx):
    """One broadcast-style headline for the hero — framed for the selected team's fans."""
    profile = TEAM_PROFILES[team_name]
    s = hctx.get("series")
    mode = hctx.get("mode")
    nick = fan_nick(team_name)
    if mode == "waiting_cf" and hctx.get("ctx"):
        return hctx["ctx"].get(
            "status_text",
            f"{nick} are waiting on the other conference semi — you're still in the hunt while the bracket sorts itself.",
        )
    if not s:
        if profile.get("status") == "Eliminated":
            return f"This playoff chapter is closed for {nick} — dig into legacy and film room pages to relive the run."
        return f"{nick} are queued for the next bracket update — stay locked in for the next opponent reveal."
    rnd = s.get("round", "Playoffs")
    a, b = s["a"], s["b"]
    tw = s["a_wins"] if team_name == a else s["b_wins"]
    ow = s["b_wins"] if team_name == a else s["a_wins"]
    opp = b if team_name == a else a
    on = fan_nick(opp)
    last = (s.get("games") or [])[-1] if s.get("games") else None
    lw = last.get("Winner") if last else None
    if s.get("winner") == team_name:
        return f"You did it — {nick} close the series {tw}-{ow} over {on}. Savor this one."
    if s.get("winner") and s.get("winner") != team_name:
        return f"{fan_nick(s['winner'])} ended the dream this round — here's what it means for your offseason storylines."
    if tw == 3 and ow <= 1:
        return f"One more win and {nick} punch the next round — you're up {tw}-{ow} on {on} in the {rnd}."
    if tw == ow and tw >= 1:
        return f"Deadlocked {tw}-{ow} with {on} — every possession feels huge from the {nick} side."
    if lw == team_name and last:
        return f"You took the last one ({last.get('Score','')}) — carry that juice into the chess match vs {on}."
    if lw and lw != team_name:
        return f"{on} answered last — what you want next is a cleaner start so {nick} reset the vibe early."
    if "Final" in rnd or "Conference" in rnd:
        return f"{rnd}: {nick} vs {on} — the stakes climb every night for your fanbase."
    return f"{nick} vs {on}, {tw}-{ow}. The {rnd} story is still being written from your seat."


def _home_series_win_probability(team_name, hctx, live):
    """Return integer 0-100 for favorite team; uses live win_prob when in-game."""
    s = hctx.get("series")
    if live:
        home = live.get("homeTeam", {}) or {}
        away = live.get("awayTeam", {}) or {}
        home_tri = home.get("teamTricode", "") or ""
        away_tri = away.get("teamTricode", "") or ""
        alias = TEAM_ALIASES.get(team_name, "")
        is_home = home_tri == alias
        hs, as_ = safe_int(home.get("score", 0)), safe_int(away.get("score", 0))
        margin = (hs - as_) if is_home else (as_ - hs)
        period = safe_int(live.get("period", 1), 1)
        stt = live.get("gameStatusText", "") or ""
        if "Final" in stt:
            return 100 if margin > 0 else (0 if margin < 0 else 50)
        if "Q" in stt or ":" in stt or "Halftime" in stt:
            return int(win_prob(margin, period, is_home))
    if not s:
        return 50
    if s.get("winner") == team_name:
        return 100
    if s.get("winner"):
        return 22
    a, b = s["a"], s["b"]
    tw = int(s.get("a_wins", 0) if team_name == a else s.get("b_wins", 0))
    ow = int(s.get("b_wins", 0) if team_name == a else s.get("a_wins", 0))
    diff = tw - ow
    games_played = tw + ow
    base = 50 + diff * 11 + (3 if games_played >= 4 else 0)
    return int(max(12, min(88, base)))


def _home_injury_hero_snippet(team_name, opponents):
    teams = [team_name]
    if isinstance(opponents, (list, tuple, set)):
        teams.extend([t for t in opponents if t and t not in teams])
    elif opponents and opponents not in teams:
        teams.append(opponents)
    parts = []
    for tm in teams[:3]:
        df, _ = get_injury_report(tm)
        if df is None or df.empty:
            continue
        row = df.iloc[0]
        parts.append(
            f"<strong>{html.escape(tm)}</strong>: {html.escape(str(row.get('Player','?')))} "
            f"<span style='opacity:.85'>({html.escape(str(row.get('Status','?')))})</span>"
        )
    if not parts:
        return f"Injuries for {html.escape(fan_nick(team_name))} & opponents load from ESPN when available — scroll to <strong>Key injuries</strong> below."
    return " · ".join(parts)


def _home_command_center_hero_html(team_name, hctx):
    pal = live_hero_palette(team_name)
    esc = html.escape
    profile = TEAM_PROFILES[team_name]
    s = hctx.get("series")
    live = find_live_game_for_team(team_name)
    prob = _home_series_win_probability(team_name, hctx, live)
    headline = _home_storyline_headline(team_name, hctx)
    opps = home_injury_opponents(team_name)
    inj = _home_injury_hero_snippet(team_name, opps)
    left_logo = TEAM_LOGOS.get(team_name, "")

    if hctx.get("mode") == "waiting_cf":
        parts = []
        for op in (hctx.get("opponents") or [])[:2]:
            u = TEAM_LOGOS.get(op, "")
            if u:
                parts.append(f"<img class='cmd-logo' src='{esc(u)}' alt=''/>")
        if not parts:
            parts.append(
                "<span style='font-size:12px;color:#94a3b8;font-weight:700'>TBD</span>"
            )
        right_html = f"<div class='cmd-opp-logos'>{''.join(parts)}</div>"
        matchup = (
            f"{esc(team_name)} <span style='opacity:.55'>vs</span> "
            f"{esc(hctx.get('opponent_display', 'TBD'))}"
        )
        score_txt = "Series TBD"
        rnd = esc(hctx.get("round_label", "Playoffs"))
    else:
        opp = hctx.get("opponent") or profile.get("current_opponent") or "TBD"
        ologo = TEAM_LOGOS.get(opp, "")
        right_html = (
            f"<div class='cmd-opp-logos'><img class='cmd-logo' src='{esc(ologo)}' alt=''/></div>"
        )
        matchup = (
            f"({profile['seed']}) {esc(team_name)} <span style='opacity:.55'>vs</span> "
            f"({TEAM_PROFILES.get(opp, {}).get('seed', '—')}) {esc(opp)}"
        )
        if s and not s.get("winner"):
            a, b = s["a"], s["b"]
            tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
            ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
            score_txt = f"{tw}–{ow}"
        elif s and s.get("winner"):
            a, b = s["a"], s["b"]
            tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
            ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
            score_txt = f"Final {tw}–{ow}"
        else:
            score_txt = "—"
        rnd = esc(
            (s or {}).get("round")
            or hctx.get("round_label")
            or profile.get("round", "Playoffs")
        )

    next_line = ""
    if live:
        stt = live.get("gameStatusText", "") or ""
        hs = live.get("homeTeam") or {}
        aw = live.get("awayTeam") or {}
        if not isinstance(hs, dict):
            hs = {}
        if not isinstance(aw, dict):
            aw = {}
        next_line = (
            f"{esc(_live_team_full_name(aw.get('teamTricode', ''), aw))} @ "
            f"{esc(_live_team_full_name(hs.get('teamTricode', ''), hs))} · "
            f"{esc(stt[:48])}"
        )
    else:
        next_line = (
            f"Next for you: {esc(fan_nick(team_name))} vs "
            f"{esc(hctx.get('opponent_display', profile.get('current_opponent') or 'opponent TBA'))} "
            f"— tip data when NBA schedule loads."
        )

    return f"""
<div class="cmd-shell" style="--cmd-bg0:{pal['bg0']};--cmd-bg1:{pal['bg1']};--cmd-accent:{pal['accent']};--cmd-accent-soft:{pal['accent_soft']};">
<div class="cmd-hero">
  <div class="cmd-hero-inner">
    <div class="cmd-kicker">Your playoff command center · {esc(fan_nick(team_name))}</div>
    <div class="cmd-row">
      <img class="cmd-logo" src="{esc(left_logo)}" alt=""/>
      <div class="cmd-center">
        <div class="cmd-round">{rnd}</div>
        <div class="cmd-match">{matchup}</div>
        <div class="cmd-scoreline">{score_txt}</div>
        <div class="cmd-rail">
          <span class="cmd-pill cmd-pill--accent">Your win probability · {prob}%</span>
          <span class="cmd-pill">Live pulse</span>
        </div>
      </div>
      {right_html}
    </div>
    <div class="cmd-headline">{esc(headline)}</div>
    <div class="cmd-inj">🩹 {inj}</div>
    <div class="cmd-next" style="margin-top:14px">
      <div class="cmd-next-title">Next game</div>
      <div style="font-size:14px;font-weight:700;color:#e2e8f0">{next_line}</div>
    </div>
  </div>
</div>
</div>
"""

def render_next_game_actions(team_name):
    """Compact live CTA row (replaces bulky countdown header)."""
    live = find_live_game_for_team(team_name)
    if live:
        stt = live.get("gameStatusText", "") or ""
        if "Final" not in stt and ("Q" in stt or ":" in stt or "Halftime" in stt):
            if st.button("Open Live Game Center", key="cmd_open_live"):
                st.session_state["page_override"] = "🏀 Live Game Center"
                st.rerun()


def render_playoff_command_center(team_name):
    _inject_home_command_center_css()
    hctx = resolve_home_matchup_context(team_name)
    st.markdown(_home_command_center_hero_html(team_name, hctx), unsafe_allow_html=True)
    render_next_game_actions(team_name)

    st.markdown('<div class="cmd-sec">1 · Your current series snapshot</div>', unsafe_allow_html=True)
    snap_cols = st.columns(4)
    status_txt = series_status_text(team_name)
    adv_like = hctx.get("advanced") or hctx.get("bracket_series")
    profile = TEAM_PROFILES[team_name]
    snap_cols[0].metric("Your playoff status", "Advanced" if adv_like else profile.get("status", "—"))
    snap_cols[1].metric("Your seed", profile.get("seed", "—"))
    snap_cols[2].metric("Round you're tracking", (hctx.get("series") or {}).get("round") or hctx.get("round_label") or profile.get("round", "—"))
    snap_cols[3].metric("Tonight's edge", "Live — you're on the broadcast" if find_live_game_for_team(team_name) else "Tracking next tip")
    st.markdown(
        f"<div style='font-size:14px;font-weight:600;color:#e2e8f0;margin:6px 0 8px'>{html.escape(status_txt)}</div>",
        unsafe_allow_html=True,
    )
    s = hctx.get("series")
    if s and s.get("games"):
        st.dataframe(pd.DataFrame(s["games"]), use_container_width=True, height=min(220, 38 + 28 * len(s["games"])))
    elif hctx.get("advanced"):
        st.info("You're through — Conference Finals pairings populate here once both semis finish.")
    elif s and s.get("round") in ("Conference Finals", "NBA Finals"):
        st.caption("CF/Finals shell is live — your game rows fill in as results post.")

    st.markdown('<div class="cmd-sec">2 · Injuries that could swing your night</div>', unsafe_allow_html=True)
    with st.container(border=True):
        render_injury_report(team_name, home_injury_opponents(team_name), show_page_header=False, fan_perspective_team=team_name)

    st.markdown('<div class="cmd-sec">3 · Your guys carrying the load</div>', unsafe_allow_html=True)
    starters = profile.get("starters", [])[:3]
    pc = st.columns(len(starters) or 1)
    for i, name in enumerate(starters or ["Rotation"]):
        with pc[i]:
            with st.container(border=True):
                st.markdown(f"**{name}**")
                try:
                    st.image(headshot(name), width=76)
                except Exception:
                    pass
                if name != "Rotation":
                    sa = season_averages(name)
                    st.metric("PTS", sa.get("PTS", "—"))
                    st.caption(f"REB {sa.get('REB','—')} · AST {sa.get('AST','—')}")

    st.markdown('<div class="cmd-sec">4 · Your momentum read</div>', unsafe_allow_html=True)
    hist = historic_series_context(team_name)
    if not hist.empty:
        st.markdown(f"<div style='font-size:13px;color:#cbd5e1;line-height:1.45'>{hist.iloc[0].get('Historical Context','')}</div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    _, s2 = series_for_team(team_name)
    if s2:
        a, b = s2["a"], s2["b"]
        tw = int(s2["a_wins"]) if team_name == a else int(s2["b_wins"])
        ow = int(s2["b_wins"]) if team_name == a else int(s2["a_wins"])
        m1.metric("Your series edge", f"+{tw - ow}" if tw > ow else (f"{tw - ow}" if tw < ow else "Even"))
        m2.metric("Games played", tw + ow)
        m3.metric("Data source", (s2.get("source") or "—")[:18])
    else:
        m1.metric("Your series edge", "—")
        m2.metric("Games played", "—")
        m3.metric("Data", "Awaiting")

    st.markdown('<div class="cmd-sec">5 · Legacy on your marquee name</div>', unsafe_allow_html=True)
    anchor = profile.get("starters", [""])[0]
    if anchor:
        logs = playoff_game_logs_for_player(anchor)
        sm = summarize_playoff_logs(logs)
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{anchor.split()[-1]} PTS", sm.get("PTS", 0))
        c2.metric("REB", sm.get("REB", 0))
        c3.metric("AST", sm.get("AST", 0))
    st.caption("Full what-if paths for your guys: **Legacy Tracker** page.")

    st.markdown('<div class="cmd-sec">6 · Your next game</div>', unsafe_allow_html=True)
    with st.container(border=True):
        live = find_live_game_for_team(team_name)
        if live:
            home = live.get("homeTeam", {}) or {}
            away = live.get("awayTeam", {}) or {}
            st.markdown(
                f"**{_live_team_full_name(away.get('teamTricode',''), away)}** @ **{_live_team_full_name(home.get('teamTricode',''), home)}** · _{live.get('gameStatusText','')}_"
            )
        else:
            opp = profile.get("current_opponent")
            st.info(
                f"Your {fan_nick(team_name)} vs {opp or 'opponent TBA'} — live tip and countdown appear when the NBA feed lists it."
            )

    st.markdown('<div class="cmd-sec">7 · Playoff storylines for your crew</div>', unsafe_allow_html=True)
    story_cols = st.columns(3)
    nk = fan_nick(team_name)
    stories = [
        (
            "Pressure cooker",
            f"When it's tight late, {nk} fans live and die with every whistle — execution matters more than narrative.",
        ),
        (
            "Health swings",
            "One availability change can flip matchups more than a scouting tweak — watch the injury strip all week.",
        ),
        (
            "Margin for error",
            "A cold stretch from three or two careless turnovers can hand the other side the night — you feel it in the building.",
        ),
    ]
    for col, (t, b) in zip(story_cols, stories):
        with col:
            with st.container(border=True):
                st.markdown(f"**{t}**")
                st.caption(b)

    st.markdown('<div class="cmd-sec">8 · Who owned the last game for you</div>', unsafe_allow_html=True)
    _, s3 = series_for_team(team_name)
    if s3 and s3.get("games"):
        last = s3["games"][-1]
        opp = s3["b"] if team_name == s3["a"] else s3["a"]
        gn = last.get("Game") if isinstance(last.get("Game"), int) else str(last.get("Game", "Game")).replace("Game ", "")
        try:
            gn_i = int(str(gn).replace("Game ", ""))
        except Exception:
            gn_i = len(s3["games"])
        mvp, why = mvp_for_game(team_name, opp, gn_i, last.get("Winner"))
        st.success(f"**{mvp}** — _{why}_")
        st.caption(f"{last.get('Date','')} · {last.get('Score','')}")
    else:
        st.caption("MVP tag unlocks when the most recent game row hits the log — tuned to your matchup.")

    st.markdown('<div class="cmd-sec">9 · Team outlook</div>', unsafe_allow_html=True)
    render_team_outlook(team_name)

    st.caption(f"Auto-updated bracket series + API where available · Refreshed {datetime.now().strftime('%b %d %I:%M %p')}")

def home_injury_opponents(team_name):
    ctx = next_round_context_for_team(team_name)
    if ctx and ctx.get("advanced"):
        return ctx.get("opponents", [])
    _, s = series_for_team(team_name)
    if s and s.get("round") in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return [opp]
    return TEAM_PROFILES.get(team_name, {}).get("current_opponent")

def _first_round_synthetic_games(team_a, team_b):
    """Static first-round game rows for bracket cards when API has not attached games."""
    rows = FIRST_ROUND_GAME_SCORES.get(team_a) or FIRST_ROUND_GAME_SCORES.get(team_b) or []
    out = []
    for r in rows:
        gn = r.get("Game", len(out) + 1)
        if isinstance(gn, int):
            gn = f"Game {gn}"
        out.append({
            "Game": str(gn),
            "Date": str(r.get("Date", "")),
            "Score": str(r.get("Score", "")),
            "Winner": str(r.get("Winner", "")),
            "Matchup": str(r.get("Matchup", "")),
        })
    return out


def _bracket_series_for_display(s, round_display_name):
    """Shallow copy of series shell with games filled from static first-round data when needed."""
    view = dict(s)
    games = view.get("games") or []
    if not games and round_display_name == "First Round":
        syn = _first_round_synthetic_games(view.get("a"), view.get("b"))
        if syn:
            view["games"] = syn
    return view


BRACKET_VISUAL_CSS = """
.bracket-wrap {
  background: linear-gradient(160deg, #070d18 0%, #0f172a 45%, #1e1b4b 100%);
  padding: 12px 10px 16px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
  color: #f8fafc;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  max-width: 100%;
  box-sizing: border-box;
}
.bmk-page-head { text-align: center; margin-bottom: 10px; }
.bmk-title {
  font-size: clamp(1.2rem, 2.6vw, 1.6rem);
  font-weight: 900;
  letter-spacing: -0.02em;
  margin: 0 0 4px;
  color: #f8fafc;
}
.bmk-sub {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.3;
  margin: 0 auto;
  max-width: 52rem;
}
.bmk-scroll {
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
  scrollbar-color: rgba(100, 116, 139, 0.55) rgba(15, 23, 42, 0.5);
}
.bmk-grid {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 0;
  min-width: 1580px;
  padding: 0;
  box-sizing: border-box;
}
.bmk-col {
  flex: 1 1 0;
  min-width: 300px;
  max-width: 400px;
  padding: 0 8px;
  border-right: 1px solid rgba(71, 85, 105, 0.38);
  box-sizing: border-box;
}
.bmk-col:last-child { border-right: none; }
.bmk-col--hub {
  min-width: 320px;
  max-width: 420px;
  flex: 1.12 1 0;
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.5) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-radius: 12px;
  margin: 0 2px;
  padding: 8px 10px 10px;
  border: 1px solid rgba(129, 140, 248, 0.35);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
.bmk-col-head {
  text-align: center;
  padding: 6px 2px 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(100, 116, 139, 0.28);
}
.bmk-col-eyebrow {
  display: block;
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #64748b;
  margin-bottom: 2px;
}
.bmk-col[data-conf="east"] .bmk-col-eyebrow { color: #7dd3fc; }
.bmk-col[data-conf="west"] .bmk-col-eyebrow { color: #fcd34d; }
.bmk-col-title {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #e2e8f0;
}
.bmk-col-stack { display: flex; flex-direction: column; gap: 8px; }
.bmk-hub { display: flex; flex-direction: column; gap: 8px; text-align: center; }
.bmk-hub-label {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #c4b5fd;
  margin-bottom: 4px;
}
.bmk-hub-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
}
.bmk-wait-card {
  background: rgba(30, 41, 59, 0.65);
  border: 1px dashed rgba(148, 163, 184, 0.35);
  border-radius: 10px;
  padding: 8px 10px 10px;
  text-align: center;
}
.bmk-wait-card--finals { border-style: solid; border-color: rgba(251, 191, 36, 0.45); }
.bmk-wait-kicker { font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 4px; }
.bmk-wait-title { font-size: 13px; font-weight: 800; color: #f8fafc; line-height: 1.25; }
.bmk-wait-line { margin: 4px 0 0; font-size: 11px; line-height: 1.35; color: #cbd5e1; }
.bmk-card {
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
  padding: 8px 10px 7px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28);
  transition: border-color 0.12s ease, box-shadow 0.12s ease, transform 0.12s ease;
}
.bmk-card:hover {
  transform: translateY(-1px);
  border-color: rgba(148, 163, 184, 0.45);
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);
}
.bmk-card--active { border-color: rgba(56, 189, 248, 0.5); box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.14), 0 4px 16px rgba(0, 0, 0, 0.26); }
.bmk-card--complete { border-color: rgba(52, 211, 153, 0.4); }
.bmk-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 6px;
  margin-bottom: 6px;
}
.bmk-chip-round {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.18);
  padding: 2px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}
.bmk-pill { font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
.bmk-pill--live { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.35); }
.bmk-pill--done { background: rgba(52, 211, 153, 0.18); color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.35); }
.bmk-series-score { font-size: 18px; font-weight: 900; color: #fbbf24; letter-spacing: 0.04em; flex-shrink: 0; white-space: nowrap; }
.bmk-rows { display: flex; flex-direction: column; gap: 4px; }
.bmk-team {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 8px;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.72);
  border: 1px solid rgba(71, 85, 105, 0.36);
  border-left: 3px solid var(--stripe, #64748b);
}
.bmk-team--leading { background: rgba(30, 58, 95, 0.48); border-color: rgba(56, 189, 248, 0.3); }
.bmk-team--winner { background: rgba(22, 78, 58, 0.36); border-color: rgba(52, 211, 153, 0.42); border-left-width: 4px; }
.bmk-team-main { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1 1 auto; }
.bmk-logo { width: 40px; height: 40px; object-fit: contain; flex-shrink: 0; filter: drop-shadow(0 1px 5px rgba(0, 0, 0, 0.4)); }
.bmk-team-text {
  min-width: 0;
  flex: 1 1 auto;
  text-align: left;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: baseline;
  gap: 6px;
}
.bmk-seed { font-size: 10px; font-weight: 700; color: #94a3b8; flex-shrink: 0; white-space: nowrap; }
.bmk-name {
  font-size: 13px;
  font-weight: 800;
  color: #f1f5f9;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  flex: 1 1 auto;
  word-break: normal;
  overflow-wrap: normal;
}
.bmk-team-meta { display: flex; align-items: center; gap: 5px; flex-shrink: 0; margin-left: 4px; }
.bmk-wins { font-size: 18px; font-weight: 900; color: #f8fafc; min-width: 22px; text-align: right; flex-shrink: 0; }
.bmk-won-badge {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6ee7b7;
  background: rgba(16, 185, 129, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.bmk-foot { font-size: 11px; color: #cbd5e1; margin-top: 5px; line-height: 1.25; text-align: left; word-break: break-word; }
.bmk-foot--next { margin-top: 2px; font-size: 10px; color: #94a3b8; line-height: 1.25; }
.bmk-details { margin-top: 5px; border-top: 1px solid rgba(51, 65, 85, 0.52); padding-top: 5px; }
.bmk-details summary { cursor: pointer; font-size: 11px; font-weight: 700; color: #93c5fd; list-style: none; }
.bmk-details summary::-webkit-details-marker { display: none; }
.bmk-log { margin: 4px 0 0; padding-left: 16px; text-align: left; }
@media (min-width: 1600px) {
  .bmk-grid { min-width: 1720px; }
  .bmk-col { min-width: 312px; max-width: 420px; }
}
"""


def bracket_team_accent(team):
    return {
        "New York Knicks": "#f97316",
        "Philadelphia 76ers": "#3b82f6",
        "Detroit Pistons": "#ef4444",
        "Cleveland Cavaliers": "#f472b6",
        "Oklahoma City Thunder": "#38bdf8",
        "Los Angeles Lakers": "#fbbf24",
        "San Antonio Spurs": "#cbd5e1",
        "Minnesota Timberwolves": "#34d399",
        "Boston Celtics": "#22c55e",
        "Atlanta Hawks": "#dc2626",
        "Orlando Magic": "#60a5fa",
        "Toronto Raptors": "#ef4444",
        "Phoenix Suns": "#fb923c",
        "Portland Trail Blazers": "#e11d48",
        "Denver Nuggets": "#facc15",
        "Houston Rockets": "#f87171",
    }.get(team, "#94a3b8")


def _bracket_latest_game_html(s):
    games = s.get("games") or []
    if not games:
        if s.get("winner"):
            return f"Latest: <strong>{html.escape(str(s['winner']))}</strong> won the series."
        return "Latest: <span style='opacity:.75'>No games in feed yet</span>"
    last = games[-1]
    score = html.escape(str(last.get("Score", "—")))
    dt = html.escape(str(last.get("Date", "")))
    win = html.escape(str(last.get("Winner", "")))
    gnum = html.escape(str(last.get("Game", "")))
    return f"Latest: <strong>{gnum}</strong> · {dt} · {score} · <strong>{win}</strong>"


def _bracket_next_game_html(s):
    if s.get("winner"):
        return "Next: <span style='opacity:.7'>—</span>"
    games = s.get("games") or []
    n = len(games) + 1
    return f"Next: <strong>Game {n}</strong> <span style='opacity:.75'>(schedule TBA)</span>"


def _bracket_game_log_items(s):
    games = s.get("games") or []
    rows = []
    for g in games[-8:]:
        rows.append(
            "<li style='margin:4px 0;font-size:12px;color:#e2e8f0'>"
            f"{html.escape(str(g.get('Game','')))} · {html.escape(str(g.get('Date','')))} · "
            f"{html.escape(str(g.get('Score','—')))} — <strong>{html.escape(str(g.get('Winner','')))}</strong></li>"
        )
    return "".join(rows) if rows else "<li style='opacity:.7'>No game rows yet</li>"


def bracket_series_card(s, round_display_name, show_round_chip=False):
    s_disp = _bracket_series_for_display(s, round_display_name)
    a, b = s_disp["a"], s_disp["b"]
    aw = int(s_disp.get("a_wins", 0) or 0)
    bw = int(s_disp.get("b_wins", 0) or 0)
    winner = s_disp.get("winner")
    active = not winner
    seed_a = TEAM_PROFILES.get(a, {}).get("seed", "—")
    seed_b = TEAM_PROFILES.get(b, {}).get("seed", "—")
    logo_a = html.escape(TEAM_LOGOS.get(a, ""), quote=True)
    logo_b = html.escape(TEAM_LOGOS.get(b, ""), quote=True)

    def team_row(team, wins, seed, logo_url, is_winner, is_leading):
        stripe = bracket_team_accent(team)
        classes = ["bmk-team"]
        if is_winner:
            classes.append("bmk-team--winner")
        elif active and is_leading:
            classes.append("bmk-team--leading")
        badge = '<span class="bmk-won-badge">Won series</span>' if is_winner else ""
        return (
            f'<div class="{" ".join(classes)}" style="--stripe:{stripe}">'
            f'<div class="bmk-team-main"><img class="bmk-logo" src="{logo_url}" alt="" width="40" height="40"/>'
            f'<div class="bmk-team-text"><span class="bmk-seed">({html.escape(str(seed))})</span>'
            f'<span class="bmk-name">{html.escape(team)}</span></div></div>'
            f'<div class="bmk-team-meta">{badge}<span class="bmk-wins">{wins}</span></div></div>'
        )

    row_a = team_row(a, aw, seed_a, logo_a, winner == a, aw > bw and not winner)
    row_b = team_row(b, bw, seed_b, logo_b, winner == b, bw > aw and not winner)
    pill = (
        '<span class="bmk-pill bmk-pill--live">In progress</span>'
        if active
        else '<span class="bmk-pill bmk-pill--done">Series complete</span>'
    )
    card_mod = "bmk-card--active" if active else "bmk-card--complete"
    chip = (
        f'<span class="bmk-chip-round">{html.escape(round_display_name)}</span>'
        if show_round_chip
        else ""
    )
    details = (
        f'<details class="bmk-details"><summary>Game log &amp; details</summary>'
        f'<div class="bmk-foot bmk-foot--next">{_bracket_next_game_html(s_disp)}</div>'
        f'<ul class="bmk-log">{_bracket_game_log_items(s_disp)}</ul></details>'
    )
    return (
        f'<div class="bmk-card {card_mod}"><div class="bmk-card-top">{chip}'
        f'<span class="bmk-series-score">{aw}–{bw}</span>{pill}</div>'
        f'<div class="bmk-rows">{row_a}{row_b}</div>'
        f'<div class="bmk-foot">{_bracket_latest_game_html(s_disp)}</div>{details}</div>'
    )


def _cf_waiting_placeholder(conf_full, sr_list):
    esc = html.escape
    if not sr_list:
        return (
            '<div class="bmk-wait-card">'
            f'<div class="bmk-wait-kicker">{esc(conf_full)}</div>'
            '<div class="bmk-wait-title">Waiting for semifinal results</div>'
            '<p class="bmk-wait-line">Semifinals will appear here when loaded.</p></div>'
        )
    decided = [s for s in sr_list if s.get("winner")]
    open_s = [s for s in sr_list if not s.get("winner")]
    kicker = esc(conf_full)
    if len(decided) == 1 and open_s:
        champ = str(decided[0].get("winner") or "")
        u = open_s[0]
        ta, tb = str(u.get("a") or ""), str(u.get("b") or "")
        aw = int(u.get("a_wins", 0) or 0)
        bw = int(u.get("b_wins", 0) or 0)
        title = f"{esc(champ)} await {esc(ta)} / {esc(tb)} winner"
        line = f"{esc(ta)} vs {esc(tb)} — series in progress ({aw}–{bw})."
    elif not decided:
        title = "Waiting for both semifinal winners"
        parts = []
        for semi in sr_list:
            sa, sb = semi.get("a"), semi.get("b")
            oa = int(semi.get("a_wins", 0) or 0)
            ob = int(semi.get("b_wins", 0) or 0)
            parts.append(f"{esc(str(sa))} vs {esc(str(sb))} ({oa}–{ob})")
        line = " · ".join(parts) if parts else "Scores updating…"
    else:
        title = "Conference Finals loading"
        line = "Both semifinals are decided; matchup should appear shortly."
    return (
        f'<div class="bmk-wait-card"><div class="bmk-wait-kicker">{kicker}</div>'
        f'<div class="bmk-wait-title">{title}</div><p class="bmk-wait-line">{line}</p></div>'
    )


def _markdown_safe_bracket_html(html_fragment):
    return "\n".join(line.lstrip() for line in html_fragment.splitlines())


def _bracket_fallback_dataframe(east_fr, east_sr, west_sr, west_fr, east_conf, west_conf, finals):
    rows = []

    def append_rows(column_label, series_list, round_name):
        for s in series_list:
            sd = _bracket_series_for_display(s, round_name)
            games = sd.get("games") or []
            if games:
                lg = games[-1]
                latest = f"{lg.get('Game', '')} {lg.get('Date', '')} {lg.get('Score', '')} → {lg.get('Winner', '')}"
            else:
                latest = "—"
            rows.append(
                {
                    "Column": column_label,
                    "Team A": sd.get("a"),
                    "Team B": sd.get("b"),
                    "Wins": f"{sd.get('a_wins', 0)}–{sd.get('b_wins', 0)}",
                    "Winner": sd.get("winner") or "—",
                    "Latest": latest,
                }
            )

    append_rows("East — First round", east_fr, "First Round")
    append_rows("East — Semifinals", east_sr, "Conference Semifinals")
    append_rows("West — Semifinals", west_sr, "Conference Semifinals")
    append_rows("West — First round", west_fr, "First Round")
    if east_conf and len(east_conf) == 1:
        append_rows("East — Conference finals", list(east_conf.values()), "Conference Finals")
    if west_conf and len(west_conf) == 1:
        append_rows("West — Conference finals", list(west_conf.values()), "Conference Finals")
    if finals and len(finals) == 1:
        append_rows("NBA Finals", list(finals.values()), "NBA Finals")
    return pd.DataFrame(rows)


def render_bracket():
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="bracket_refresh")

    second = build_second_round_series()
    east_fr = [s for s in FIRST_ROUND_SERIES.values() if s["conf"] == "East"]
    west_fr = [s for s in FIRST_ROUND_SERIES.values() if s["conf"] == "West"]
    east_sr = [s for s in second.values() if s["conf"] == "East"]
    west_sr = [s for s in second.values() if s["conf"] == "West"]
    east_conf = infer_next_round_series("Conference Finals", "East")
    west_conf = infer_next_round_series("Conference Finals", "West")
    finals = infer_next_round_series("NBA Finals")

    if east_conf and len(east_conf) == 1:
        east_cf_block = bracket_series_card(list(east_conf.values())[0], "Conference Finals")
    else:
        east_cf_block = _cf_waiting_placeholder("Eastern Conference Finals", east_sr)

    if west_conf and len(west_conf) == 1:
        west_cf_block = bracket_series_card(list(west_conf.values())[0], "Conference Finals")
    else:
        west_cf_block = _cf_waiting_placeholder("Western Conference Finals", west_sr)

    if finals and len(finals) == 1:
        finals_block = bracket_series_card(list(finals.values())[0], "NBA Finals")
    else:
        finals_block = (
            '<div class="bmk-wait-card bmk-wait-card--finals">'
            '<div class="bmk-wait-kicker">NBA Finals</div>'
            '<div class="bmk-wait-title">Waiting for conference champions</div>'
            '<p class="bmk-wait-line">Appears when East and West conference finals winners are set.</p></div>'
        )

    center_column = (
        '<div class="bmk-hub">'
        '<div><div class="bmk-hub-label">East — Conference Finals</div>'
        f"{east_cf_block}</div>"
        '<div class="bmk-hub-divider" aria-hidden="true"></div>'
        '<div><div class="bmk-hub-label">West — Conference Finals</div>'
        f"{west_cf_block}</div>"
        '<div class="bmk-hub-divider" aria-hidden="true"></div>'
        '<div><div class="bmk-hub-label">NBA Finals</div>'
        f"{finals_block}</div></div>"
    )

    east_fr_cards = "".join(bracket_series_card(s, "First Round") for s in east_fr)
    east_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals") for s in east_sr)
    west_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals") for s in west_sr)
    west_fr_cards = "".join(bracket_series_card(s, "First Round") for s in west_fr)

    bracket_body = f"""<div class="bmk-page-head">
<h2 class="bmk-title">2026 NBA Playoff Bracket</h2>
<p class="bmk-sub">East on the left, West on the right, conference finals and NBA Finals in the center. Scroll sideways on smaller screens. Open any series for the full game log.</p>
</div>
<div class="bmk-scroll" role="region" aria-label="Playoff bracket">
<div class="bmk-grid">
<div class="bmk-col" data-conf="east">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Eastern Conference</span>
<h3 class="bmk-col-title">First round</h3>
</div>
<div class="bmk-col-stack">{east_fr_cards}</div>
</div>
<div class="bmk-col" data-conf="east">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Eastern Conference</span>
<h3 class="bmk-col-title">Semifinals</h3>
</div>
<div class="bmk-col-stack">{east_sr_cards}</div>
</div>
<div class="bmk-col bmk-col--hub">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Center</span>
<h3 class="bmk-col-title">Conference &amp; NBA Finals</h3>
</div>
<div class="bmk-col-stack">{center_column}</div>
</div>
<div class="bmk-col" data-conf="west">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Western Conference</span>
<h3 class="bmk-col-title">Semifinals</h3>
</div>
<div class="bmk-col-stack">{west_sr_cards}</div>
</div>
<div class="bmk-col" data-conf="west">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Western Conference</span>
<h3 class="bmk-col-title">First round</h3>
</div>
<div class="bmk-col-stack">{west_fr_cards}</div>
</div>
</div>
</div>"""

    full_html = (
        '<div class="bracket-wrap"><style>'
        + BRACKET_VISUAL_CSS.strip()
        + "</style>"
        + bracket_body
        + "</div>"
    )
    full_html = _markdown_safe_bracket_html(full_html)

    try:
        st.markdown(full_html, unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Playoff Bracket HTML could not render ({exc}). Showing the same data in a table.")
        st.dataframe(
            _bracket_fallback_dataframe(
                east_fr, east_sr, west_sr, west_fr, east_conf, west_conf, finals
            ),
            use_container_width=True,
            hide_index=True,
        )


def latest_game_note(team):
    _, s = series_for_team(team)
    if not s or not s.get("games"):
        return "No completed current-series game is in the log yet — check back after tip."
    last = s["games"][-1]
    result = "won" if last.get("Winner") == team else "lost"
    nick = fan_nick(team)
    if result == "won":
        vibe = "That's a night you can feel good about as a fan — carry the energy into prep for the next one."
    else:
        vibe = "Tough watch — the bounce-back story starts with defense and cleaner possessions next game."
    return (
        f"Last result for {nick}: {last.get('Game','Previous game')} on {last.get('Date','recently')} — "
        f"{last.get('Score','score unavailable')}. You {result} that one. {vibe}"
    )

def render_team_outlook(team):
    p = TEAM_PROFILES[team]
    nick = fan_nick(team)
    st.subheader(f"Team outlook · {nick} fan lens")
    st.markdown(f"<div class='big-status'>{series_status_text(team)}</div>", unsafe_allow_html=True)
    st.info(latest_game_note(team))
    st.markdown("### What you should feel good about")
    for s in p["strengths"]:
        if team == "New York Knicks" and "Towns" in s:
            st.success(
                "Karl-Anthony Towns gives you real spacing at the five — the swing factor is keeping him on the floor without foul trouble."
            )
        else:
            st.success(s)
    st.markdown("### Honest worry list (so you're not surprised)")
    for c in p["concerns"]:
        st.warning(c)
    st.markdown("### What a win looks like next game")
    for item in [
        "You win the possession battle — fewer empty trips, no careless live-ball turnovers.",
        "Your main creators still have legs in the fourth because the bench didn't bleed the lead.",
        "You defend without fouling; bonus points if the glass tilts your way late.",
    ]:
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
    return "".join(lines) if lines else "<div style='margin-top:8px;color:#94a3b8;font-size:12px'>No injury rows from live source · see <b>Injuries</b> tab.</div>"


def live_hero_palette(favorite_team):
    """Subtle gradient + accent for sticky hero; tuned for contrast on dark backgrounds."""
    palettes = {
        "New York Knicks": {"bg0": "#0a1628", "bg1": "#152642", "accent": "#f97316", "accent_soft": "rgba(249,115,22,.22)"},
        "Philadelphia 76ers": {"bg0": "#0c1220", "bg1": "#1a1f3c", "accent": "#3b82f6", "accent_soft": "rgba(59,130,246,.22)"},
        "Detroit Pistons": {"bg0": "#1a0a0c", "bg1": "#241018", "accent": "#ef4444", "accent_soft": "rgba(239,68,68,.2)"},
        "Cleveland Cavaliers": {"bg0": "#1a0c12", "bg1": "#2a1220", "accent": "#f472b6", "accent_soft": "rgba(244,114,182,.18)"},
        "Oklahoma City Thunder": {"bg0": "#0a1524", "bg1": "#122238", "accent": "#38bdf8", "accent_soft": "rgba(56,189,248,.22)"},
        "Los Angeles Lakers": {"bg0": "#14081f", "bg1": "#251538", "accent": "#fbbf24", "accent_soft": "rgba(251,191,36,.2)"},
        "San Antonio Spurs": {"bg0": "#0c0c0c", "bg1": "#1c232e", "accent": "#cbd5e1", "accent_soft": "rgba(203,213,225,.18)"},
        "Minnesota Timberwolves": {"bg0": "#061a18", "bg1": "#0f2d28", "accent": "#34d399", "accent_soft": "rgba(52,211,153,.2)"},
        "Boston Celtics": {"bg0": "#061510", "bg1": "#0f2418", "accent": "#22c55e", "accent_soft": "rgba(34,197,94,.2)"},
        "Atlanta Hawks": {"bg0": "#1a0c0c", "bg1": "#2a1212", "accent": "#dc2626", "accent_soft": "rgba(220,38,38,.2)"},
        "Orlando Magic": {"bg0": "#0a1420", "bg1": "#122a45", "accent": "#60a5fa", "accent_soft": "rgba(96,165,250,.22)"},
        "Toronto Raptors": {"bg0": "#0f0f12", "bg1": "#1a1520", "accent": "#ef4444", "accent_soft": "rgba(239,68,68,.18)"},
        "Phoenix Suns": {"bg0": "#1a0f08", "bg1": "#2d1810", "accent": "#fb923c", "accent_soft": "rgba(251,146,60,.22)"},
        "Portland Trail Blazers": {"bg0": "#120808", "bg1": "#221010", "accent": "#e11d48", "accent_soft": "rgba(225,29,72,.2)"},
        "Denver Nuggets": {"bg0": "#0f1724", "bg1": "#1e2a42", "accent": "#facc15", "accent_soft": "rgba(250,204,21,.2)"},
        "Houston Rockets": {"bg0": "#140808", "bg1": "#241010", "accent": "#f87171", "accent_soft": "rgba(248,113,113,.2)"},
    }
    return palettes.get(favorite_team, {"bg0": "#0f172a", "bg1": "#1e293b", "accent": "#38bdf8", "accent_soft": "rgba(56,189,248,.18)"})


def render_live_game_center(favorite_team, profile):
    """Professional dashboard layout: sticky score hero + tabbed sections."""
    st.markdown("### 🏟️ Live Game Center")
    st.caption(f"Broadcast view for **{fan_nick(favorite_team)}** fans — tabs below stay on your team.")

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_refresh")
        st.caption("Auto-refresh every 30 seconds.")

    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live endpoints are unavailable. Check requirements.txt.")
        return

    live = find_live_game_for_team(favorite_team)
    if not live:
        st.warning(f"No live or scheduled game for {fan_nick(favorite_team)} in the feed right now — try again near tip.")
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

    opp_other = home_name if favorite_team == away_name else away_name
    nick_live = fan_nick(favorite_team)
    opp_nick_live = fan_nick(opp_other) if opp_other else "them"
    if prob > 58:
        momentum_note = f"Model likes {nick_live} right now — keep the foot on the gas, don't gift {opp_nick_live} free runs."
    elif prob >= 42:
        momentum_note = f"Toss-up — the next run decides how stressed you feel as a {nick_live} fan."
    else:
        momentum_note = f"{nick_live} need a defensive stop chain and better shot quality — model has you chasing {opp_nick_live}."

    series_line, series_src = _live_series_board(away_name, home_name)
    if not series_line and favorite_team in (away_name, home_name):
        series_line = series_status_text(favorite_team)
        _, s0 = series_for_team(favorite_team)
        series_src = (s0 or {}).get("source", "")

    clutch = period >= 4 and abs(margin) <= 5
    is_live = status and ("Q" in status or ":" in status or "Halftime" in status) and "Final" not in status

    logo_away = TEAM_LOGOS.get(away_name, f"https://cdn.nba.com/logos/nba/500/{away_tri}/primary/L/logo.svg")
    logo_home = TEAM_LOGOS.get(home_name, f"https://cdn.nba.com/logos/nba/500/{home_tri}/primary/L/logo.svg")

    inj_teams = []
    for t in (away_name, home_name):
        if t and t not in inj_teams and t in TEAM_PROFILES:
            inj_teams.append(t)
    if not inj_teams:
        inj_teams = [favorite_team]
        if profile.get("current_opponent") and profile["current_opponent"] not in inj_teams:
            inj_teams.append(profile["current_opponent"])

    pal = live_hero_palette(favorite_team)
    hero_box = "border: 1px solid rgba(255,255,255,.12); box-shadow: 0 10px 36px rgba(0,0,0,.42);"
    hero_style = f"background: linear-gradient(165deg, {pal['bg0']} 0%, {pal['bg1']} 52%, #070b12 100%); {hero_box}"
    away_score_color = pal["accent"] if away_name == favorite_team else "#f8fafc"
    home_score_color = pal["accent"] if home_name == favorite_team else "#f8fafc"
    prob_pill_style = f"background:{pal['accent_soft']}; border:1px solid {pal['accent']}77; color:#f8fafc"

    hero_html = f"""
<div class="live-score-sticky" style="{hero_style}">
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
      <div class="live-score-big"><span style="color:{away_score_color}">{away_score}</span>
        <span style="color:#64748b;margin:0 10px">—</span>
        <span style="color:{home_score_color}">{home_score}</span></div>
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
    <span class="live-pill prob" style="{prob_pill_style}">📈 Your win prob · {nick_live}: {prob}%</span>
  </div>
  <div class="live-tile-row">
    <div class="live-tile"><div class="k">Your margin</div><div class="v">{'+' if margin > 0 else ''}{margin}</div></div>
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
    opp = profile.get("current_opponent") or opp_other

    matchup_opp = opp if opp in TEAM_PROFILES else (opp_other if opp_other in TEAM_PROFILES else None)

    tab_sum, tab_inj, tab_mom, tab_top, tab_shot, tab_pbp, tab_what = st.tabs([
        "📋 Game Summary / Live Score",
        "🩹 Injuries",
        "📈 Momentum / Win Probability",
        "⭐ Top Performers",
        "🎯 Shot Chart",
        "📝 Play-by-Play",
        "🔮 What-If Simulator",
    ])

    with tab_sum:
        with st.container(border=True):
            st.markdown("##### Game Summary / Live Score")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Clock", clock or "—")
            m2.metric("Period", f"Q{period}")
            m3.metric(f"Your {nick_live} pts", team_score)
            m4.metric(f"Their ({opp_nick_live}) pts", opp_score)
            if not box_df.empty:
                st.markdown("**Box score**")
                st.dataframe(box_df, use_container_width=True, height=300)
                st.markdown("**Foul trouble (4+ PF)**")
                fouls = box_df[box_df["PF"].astype(float) >= 4]
                st.dataframe(fouls[["Team", "Player", "PF", "PTS", "MIN"]], use_container_width=True) if not fouls.empty else st.success("No major foul trouble detected.")
                st.markdown("**Game story**")
                for line in game_story(favorite_team, margin, prob, box_df):
                    st.write(f"• {line}")
            else:
                st.info("Live box score is still loading or unavailable.")
            if matchup_opp:
                st.divider()
                st.markdown("**Positional matchup**")
                st.dataframe(matchup_advantages(favorite_team, matchup_opp), use_container_width=True)
            st.divider()
            st.markdown("**Pressure & how it feels**")
            if margin > 0:
                feel = f"You're up {margin} — enjoy the moment, but the other side is one run from stealing the vibe."
            elif margin == 0:
                feel = "Deadlocked — next three minutes usually decide who walks to the car happy."
            else:
                feel = f"You're down {abs(margin)} — not dead yet: one stop-and-score swing changes the building."
            st.info(feel + " Watch turnovers, fouls, and who gets the clean look late.")
            st.markdown("**Your next priorities**")
            for item in [
                "Stops without fouling — make them hit contested twos.",
                "Defensive glass so they can't extend possessions.",
                "Clean looks for your best creator — no hero-ball early-clock shots.",
                "No live-ball turnovers that become free transition points.",
            ]:
                st.write(f"• {item}")
            st.caption("Legacy modeling from your player's angle: **Legacy Tracker** page.")

    with tab_inj:
        with st.container(border=True):
            st.markdown("##### Injuries & availability")
            render_injury_report(favorite_team, home_injury_opponents(favorite_team), show_page_header=False, fan_perspective_team=favorite_team)
            if away_name in TEAM_PROFILES and home_name in TEAM_PROFILES and {away_name, home_name} != {favorite_team, profile.get("current_opponent")}:
                st.caption("Favorite team + sidebar opponent list; live pair above may differ from profile when the bracket has advanced.")

    with tab_mom:
        with st.container(border=True):
            st.markdown("##### Momentum / win probability")
            cL, cR = st.columns((1, 1))
            with cL:
                st.plotly_chart(
                    px.pie(
                        pd.DataFrame(
                            {
                                "Outcome": [f"You ({nick_live}) win this game", f"{opp_nick_live} steal it"],
                                "Probability": [prob, 100 - prob],
                            }
                        ),
                        names="Outcome",
                        values="Probability",
                        title="Win probability split",
                        hole=0.45,
                        color_discrete_sequence=[pal["accent"], "#64748b"],
                    ),
                    use_container_width=True,
                )
            timeline = pd.DataFrame({
                "Game Segment": ["Start", "Q1", "Q2", "Q3", "Now"],
                "Win Probability": [50, max(1, min(99, prob - 12)), max(1, min(99, prob - 7)), max(1, min(99, prob - 3)), prob],
                "Margin": [0, margin - 8, margin - 5, margin - 2, margin],
            })
            with cR:
                st.plotly_chart(
                    px.line(timeline, x="Game Segment", y="Win Probability", markers=True, title="Win probability path (illustrative)"),
                    use_container_width=True,
                )
            st.plotly_chart(px.line(timeline, x="Game Segment", y="Margin", markers=True, title="Score margin momentum (illustrative)"), use_container_width=True)
            st.caption(f"Charts are tuned to how **{nick_live}** look vs **{opp_nick_live}** right now — illustrative path, not full reconstruction.")

    with tab_top:
        with st.container(border=True):
            st.markdown("##### Top performers <span class='badge-hot'>🔥</span> hot · <span class='badge-cold'>❄️</span> cold", unsafe_allow_html=True)
            if not box_df.empty:
                render_lineup_cards(favorite_team, box_df)
                if opp and opp in TEAM_PROFILES:
                    render_lineup_cards(opp, box_df)
                elif matchup_opp:
                    render_lineup_cards(matchup_opp, box_df)
            else:
                st.info("Lineup cards appear when the live box score loads.")

    with tab_shot:
        with st.container(border=True):
            st.markdown("##### Shot chart")
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
                    st.plotly_chart(draw_court(display, f"{nick_live} shot chart — blue ○ made, red × missed"), use_container_width=True)
                st.markdown("**Clutch meter (your stress index)**")
                if clutch:
                    st.warning(f"Buckle up — it's clutch time for {nick_live}: Q4 inside five. Every possession hits different.")
                else:
                    st.info(f"Not clutch-time yet for {nick_live} — if the margin tightens late, this meter becomes your pulse check.")
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

    with tab_pbp:
        with st.container(border=True):
            st.markdown("##### Play-by-play (latest)")
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

    with tab_what:
        with st.container(border=True):
            st.markdown("##### What-if simulator")
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
    _, s = second_round_series_for_team(team_name)
    return _series_games_for_history(team_name, s) if s else []


def _series_games_for_history(team_name, series_dict):
    """Build game rows for history cards from any series shell containing team_name."""
    if not series_dict or not series_dict.get("games"):
        return []
    a, b = series_dict["a"], series_dict["b"]
    opp = b if team_name == a else a
    games = []
    for idx, g in enumerate(series_dict.get("games", []), start=1):
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

    _, s2 = second_round_series_for_team(team_name)
    if s2 and s2.get("games"):
        opp2 = s2["b"] if team_name == s2["a"] else s2["a"]
        second_games = get_current_series_games_for_previous_rounds(team_name)
        sr_note = f"{s2['winner']} wins the series." if s2.get("winner") else None
        render_series_history_card(team_name, opp2, second_games, "Second Round", sr_note)

    for round_label, coll in (("Conference Finals", build_conference_finals_series()), ("NBA Finals", build_nba_finals_series())):
        for _k, s in (coll or {}).items():
            if team_name not in (s.get("a"), s.get("b")):
                continue
            opp = s["b"] if team_name == s["a"] else s["a"]
            games = _series_games_for_history(team_name, s)
            if not games:
                continue
            note = f"{s.get('winner')} wins the {round_label}." if s.get("winner") else None
            render_series_history_card(team_name, opp, games, round_label, note)

# ==========================================================
# Sidebar
# ==========================================================
PAGES={
    "🏀 Home Dashboard":"Home Dashboard",
    "🏀 Live Game Center":"Live Game Center",
    "🏀 Playoff Bracket":"Playoff Bracket",
    "🧠 Matchup Intelligence":"Matchup Intelligence",
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
    render_playoff_command_center(favorite_team)

elif page == "Playoff Bracket":
    render_bracket()

elif page == "Matchup Intelligence":
    render_matchup_header(favorite_team)
    st.subheader("Analyst layer — told from your sideline")
    st.caption(
        f"Built for **{fan_nick(favorite_team)}** fans: series log, margins when we can parse them, your roster tags, injuries, and recent swings. "
        "Heuristic read — not a betting model."
    )
    render_matchup_intelligence(favorite_team)

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
    st.subheader(f"Legacy Tracker · how {fan_nick(favorite_team)} history could rewrite if this run keeps going")

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

    st.info(
        "Fan-forward legacy toy — not an official ranking. It blends résumé, your current playoff line, efficiency, plus/minus, and how deep "
        f"{fan_nick(favorite_team)} advance. Real legacy also lives in signature games, who you beat, injuries, narrative, and rings."
    )

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
