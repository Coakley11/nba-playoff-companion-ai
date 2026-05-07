from datetime import datetime, timezone, timedelta
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
    from nba_api.stats.endpoints import playergamelog, playercareerstats, leaguegamefinder
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

st.set_page_config(page_title="Daniel Cohen — NBA Playoff Companion AI", page_icon="🏀", layout="wide")
st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 NBA playoff companion app with live game center, dynamic bracket, box scores, and live shot chart")

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #1f2937);
}
section[data-testid="stSidebar"] label {
    font-size: 16px !important;
    font-weight: 700 !important;
}
div[role="radiogroup"] label {
    padding: 8px 6px;
    border-radius: 10px;
}
div[role="radiogroup"] label:hover {
    background-color: rgba(255,255,255,0.08);
}
.player-card {
    text-align:center;
    border-radius: 16px;
    padding: 8px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

TEAM_LOGOS = {
    "Detroit Pistons": "https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg",
    "Orlando Magic": "https://cdn.nba.com/logos/nba/1610612753/primary/L/logo.svg",
    "Cleveland Cavaliers": "https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg",
    "Toronto Raptors": "https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg",
    "New York Knicks": "https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg",
    "Atlanta Hawks": "https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg",
    "Boston Celtics": "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
    "Philadelphia 76ers": "https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg",
    "Oklahoma City Thunder": "https://cdn.nba.com/logos/nba/1610612760/primary/L/logo.svg",
    "Phoenix Suns": "https://cdn.nba.com/logos/nba/1610612756/primary/L/logo.svg",
    "San Antonio Spurs": "https://cdn.nba.com/logos/nba/1610612759/primary/L/logo.svg",
    "Portland Trail Blazers": "https://cdn.nba.com/logos/nba/1610612757/primary/L/logo.svg",
    "Denver Nuggets": "https://cdn.nba.com/logos/nba/1610612743/primary/L/logo.svg",
    "Minnesota Timberwolves": "https://cdn.nba.com/logos/nba/1610612750/primary/L/logo.svg",
    "Los Angeles Lakers": "https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg",
    "Houston Rockets": "https://cdn.nba.com/logos/nba/1610612745/primary/L/logo.svg",
}

TEAM_ALIASES = {
    "Detroit Pistons": "DET", "Orlando Magic": "ORL", "Cleveland Cavaliers": "CLE", "Toronto Raptors": "TOR",
    "New York Knicks": "NYK", "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Philadelphia 76ers": "PHI",
    "Oklahoma City Thunder": "OKC", "Phoenix Suns": "PHX", "San Antonio Spurs": "SAS", "Portland Trail Blazers": "POR",
    "Denver Nuggets": "DEN", "Minnesota Timberwolves": "MIN", "Los Angeles Lakers": "LAL", "Houston Rockets": "HOU",
}

TEAM_PROFILES = {
    "New York Knicks": {"seed":3,"conference":"East","status":"Active","round":"Second Round","current_opponent":"Philadelphia 76ers","first_round_opponent":"Atlanta Hawks","first_round_result":"Defeated Atlanta Hawks, 4-2","starters":["Jalen Brunson","Mikal Bridges","OG Anunoby","Josh Hart","Karl-Anthony Towns"],"subs":["Miles McBride","Mitchell Robinson","Jordan Clarkson","Landry Shamet","Jose Alvarado"],"strengths":["Brunson shot creation","rebounding","physical wing defense","home-court energy"],"concerns":["bench scoring consistency","foul trouble","overreliance on Brunson late"]},
    "Philadelphia 76ers": {"seed":7,"conference":"East","status":"Active","round":"Second Round","current_opponent":"New York Knicks","first_round_opponent":"Boston Celtics","first_round_result":"Defeated Boston Celtics, 4-3","starters":["Tyrese Maxey","VJ Edgecombe","Kelly Oubre Jr.","Paul George","Joel Embiid"],"subs":["Quentin Grimes","Andre Drummond","Kyle Lowry","Eric Gordon","Caleb Martin"],"strengths":["Embiid interior pressure","Maxey speed","free-throw pressure","star scoring"],"concerns":["Embiid health","transition defense","depth","turnovers"]},
    "Detroit Pistons": {"seed":1,"conference":"East","status":"Active","round":"Second Round","current_opponent":"Cleveland Cavaliers","first_round_opponent":"Orlando Magic","first_round_result":"Defeated Orlando Magic, 4-3","starters":["Cade Cunningham","Jaden Ivey","Ausar Thompson","Tobias Harris","Jalen Duren"],"subs":["Marcus Sasser","Isaiah Stewart","Simone Fontecchio","Malik Beasley","Ron Holland"],"strengths":["Cade Cunningham creation","rebounding","young athleticism","transition pressure"],"concerns":["playoff inexperience","late-game execution","half-court droughts"]},
    "Cleveland Cavaliers": {"seed":4,"conference":"East","status":"Active","round":"Second Round","current_opponent":"Detroit Pistons","first_round_opponent":"Toronto Raptors","first_round_result":"Defeated Toronto Raptors, 4-3","starters":["Darius Garland","Donovan Mitchell","Max Strus","Evan Mobley","Jarrett Allen"],"subs":["Caris LeVert","Isaac Okoro","Georges Niang","Sam Merrill","Dean Wade"],"strengths":["guard scoring","rim protection","defensive size","Mitchell shot creation"],"concerns":["offensive droughts","health","turnovers under pressure"]},
    "Oklahoma City Thunder": {"seed":1,"conference":"West","status":"Active","round":"Second Round","current_opponent":"Los Angeles Lakers","first_round_opponent":"Phoenix Suns","first_round_result":"Defeated Phoenix Suns, 4-0","starters":["Shai Gilgeous-Alexander","Lu Dort","Jalen Williams","Chet Holmgren","Isaiah Hartenstein"],"subs":["Cason Wallace","Aaron Wiggins","Isaiah Joe","Jaylin Williams","Kenrich Williams"],"strengths":["SGA creation","spacing","defensive length","pace"],"concerns":["playoff physicality","Lakers size","late-game pressure"]},
    "Los Angeles Lakers": {"seed":4,"conference":"West","status":"Active","round":"Second Round","current_opponent":"Oklahoma City Thunder","first_round_opponent":"Houston Rockets","first_round_result":"Defeated Houston Rockets, 4-2","starters":["D'Angelo Russell","Austin Reaves","LeBron James","Rui Hachimura","Anthony Davis"],"subs":["Gabe Vincent","Jarred Vanderbilt","Max Christie","Christian Wood","Jaxson Hayes"],"strengths":["star experience","rim pressure","Anthony Davis defense","LeBron control"],"concerns":["transition defense","age","three-point consistency"]},
    "San Antonio Spurs": {"seed":2,"conference":"West","status":"Active","round":"Second Round","current_opponent":"Minnesota Timberwolves","first_round_opponent":"Portland Trail Blazers","first_round_result":"Defeated Portland Trail Blazers, 4-1","starters":["Stephon Castle","Devin Vassell","Keldon Johnson","Jeremy Sochan","Victor Wembanyama"],"subs":["Tre Jones","Julian Champagnie","Zach Collins","Malaki Branham","Blake Wesley"],"strengths":["Wembanyama two-way impact","length","rim protection","young talent"],"concerns":["playoff inexperience","turnovers","physicality"]},
    "Minnesota Timberwolves": {"seed":6,"conference":"West","status":"Active","round":"Second Round","current_opponent":"San Antonio Spurs","first_round_opponent":"Denver Nuggets","first_round_result":"Defeated Denver Nuggets, 4-2","starters":["Mike Conley","Anthony Edwards","Jaden McDaniels","Naz Reid","Rudy Gobert"],"subs":["Nickeil Alexander-Walker","Donte DiVincenzo","Rob Dillingham","Josh Minott","Luka Garza"],"strengths":["defense","size","Anthony Edwards scoring","physicality"],"concerns":["late-game offense","spacing","foul trouble"]},
    "Atlanta Hawks": {"seed":6,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"New York Knicks","first_round_result":"Lost to New York Knicks, 4-2","starters":["Trae Young","Dyson Daniels","Zaccharie Risacher","Jalen Johnson","Onyeka Okongwu"],"subs":["Bogdan Bogdanovic","De'Andre Hunter","Clint Capela","Vit Krejci","Kobe Bufkin"],"strengths":["Trae creation","pace","pick-and-roll scoring"],"concerns":["defense","rebounding","physical matchups"]},
    "Boston Celtics": {"seed":2,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Philadelphia 76ers","first_round_result":"Lost to Philadelphia 76ers, 4-3","starters":["Jrue Holiday","Derrick White","Jaylen Brown","Jayson Tatum","Kristaps Porzingis"],"subs":["Payton Pritchard","Sam Hauser","Al Horford","Luke Kornet","Neemias Queta"],"strengths":["wing scoring","spacing","experience"],"concerns":["late-series execution","health","three-point variance"]},
    "Orlando Magic": {"seed":8,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Detroit Pistons","first_round_result":"Lost to Detroit Pistons, 4-3","starters":["Jalen Suggs","Kentavious Caldwell-Pope","Franz Wagner","Paolo Banchero","Wendell Carter Jr."],"subs":["Cole Anthony","Jonathan Isaac","Anthony Black","Moritz Wagner","Gary Harris"],"strengths":["defense","size","young forwards"],"concerns":["shooting","late-game offense","spacing"]},
    "Toronto Raptors": {"seed":5,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Cleveland Cavaliers","first_round_result":"Lost to Cleveland Cavaliers, 4-3","starters":["Immanuel Quickley","RJ Barrett","Gradey Dick","Scottie Barnes","Jakob Poeltl"],"subs":["Bruce Brown","Kelly Olynyk","Ochai Agbaji","Chris Boucher","Davion Mitchell"],"strengths":["length","transition offense","versatility"],"concerns":["half-court scoring","shooting consistency","late-game creation"]},
    "Phoenix Suns": {"seed":8,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Oklahoma City Thunder","first_round_result":"Lost to Oklahoma City Thunder, 4-0","starters":["Devin Booker","Bradley Beal","Grayson Allen","Kevin Durant","Jusuf Nurkic"],"subs":["Royce O'Neale","Eric Gordon","Bol Bol","Drew Eubanks","Josh Okogie"],"strengths":["shot creation","veteran scoring"],"concerns":["depth","defense","health"]},
    "Portland Trail Blazers": {"seed":7,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"San Antonio Spurs","first_round_result":"Lost to San Antonio Spurs, 4-1","starters":["Scoot Henderson","Anfernee Simons","Shaedon Sharpe","Jerami Grant","Deandre Ayton"],"subs":["Toumani Camara","Matisse Thybulle","Robert Williams III","Dalano Banton","Kris Murray"],"strengths":["young guards","athleticism"],"concerns":["defense","experience","consistency"]},
    "Denver Nuggets": {"seed":3,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Minnesota Timberwolves","first_round_result":"Lost to Minnesota Timberwolves, 4-2","starters":["Jamal Murray","Christian Braun","Michael Porter Jr.","Aaron Gordon","Nikola Jokic"],"subs":["Reggie Jackson","Peyton Watson","Zeke Nnaji","Julian Strawther","DeAndre Jordan"],"strengths":["Jokic offense","chemistry","half-court execution"],"concerns":["bench depth","athletic matchups","defensive speed"]},
    "Houston Rockets": {"seed":5,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Los Angeles Lakers","first_round_result":"Lost to Los Angeles Lakers, 4-2","starters":["Fred VanVleet","Jalen Green","Amen Thompson","Jabari Smith Jr.","Alperen Sengun"],"subs":["Dillon Brooks","Tari Eason","Cam Whitmore","Steven Adams","Reed Sheppard"],"strengths":["young athleticism","defense","pace"],"concerns":["half-court scoring","playoff experience","shot selection"]},
}

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

SECOND_ROUND_SERIES = {
    "DET-CLE": {"conf":"East","a":"Detroit Pistons","b":"Cleveland Cavaliers","a_wins":1,"b_wins":0,"winner":None,"games":[{"Game":"Game 1","Score":"Pistons 111, Cavaliers 101","Winner":"Detroit Pistons"}]},
    "NYK-PHI": {"conf":"East","a":"New York Knicks","b":"Philadelphia 76ers","a_wins":1,"b_wins":0,"winner":None,"games":[{"Game":"Game 1","Score":"Knicks 137, 76ers 98","Winner":"New York Knicks"}]},
    "OKC-LAL": {"conf":"West","a":"Oklahoma City Thunder","b":"Los Angeles Lakers","a_wins":0,"b_wins":0,"winner":None,"games":[]},
    "SAS-MIN": {"conf":"West","a":"San Antonio Spurs","b":"Minnesota Timberwolves","a_wins":0,"b_wins":1,"winner":None,"games":[{"Game":"Game 1","Score":"Timberwolves 104, Spurs 102","Winner":"Minnesota Timberwolves"}]},
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
    "Orlando Magic": [],
    "Cleveland Cavaliers": [
        {"Game":1,"Date":"Apr 19","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 126, Raptors 113","Winner":"Cleveland Cavaliers"},
        {"Game":2,"Date":"Apr 22","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 115, Raptors 105","Winner":"Cleveland Cavaliers"},
        {"Game":3,"Date":"Apr 25","Matchup":"Cavaliers at Raptors","Score":"Raptors 126, Cavaliers 104","Winner":"Toronto Raptors"},
        {"Game":4,"Date":"Apr 27","Matchup":"Cavaliers at Raptors","Score":"Raptors 93, Cavaliers 89","Winner":"Toronto Raptors"},
        {"Game":5,"Date":"Apr 29","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 125, Raptors 120","Winner":"Cleveland Cavaliers"},
        {"Game":6,"Date":"May 1","Matchup":"Cavaliers at Raptors","Score":"Raptors 112, Cavaliers 110","Winner":"Toronto Raptors"},
        {"Game":7,"Date":"May 3","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 114, Raptors 102","Winner":"Cleveland Cavaliers"},
    ],
    "Toronto Raptors": [],
    "New York Knicks": [
        {"Game":1,"Date":"Apr 19","Matchup":"Hawks at Knicks","Score":"Knicks 113, Hawks 102","Winner":"New York Knicks"},
        {"Game":2,"Date":"Apr 22","Matchup":"Hawks at Knicks","Score":"Hawks 107, Knicks 106","Winner":"Atlanta Hawks"},
        {"Game":3,"Date":"Apr 25","Matchup":"Knicks at Hawks","Score":"Hawks 109, Knicks 108","Winner":"Atlanta Hawks"},
        {"Game":4,"Date":"Apr 27","Matchup":"Knicks at Hawks","Score":"Knicks 114, Hawks 98","Winner":"New York Knicks"},
        {"Game":5,"Date":"Apr 29","Matchup":"Hawks at Knicks","Score":"Knicks 126, Hawks 97","Winner":"New York Knicks"},
        {"Game":6,"Date":"May 1","Matchup":"Knicks at Hawks","Score":"Knicks 140, Hawks 89","Winner":"New York Knicks"},
    ],
    "Atlanta Hawks": [],
    "Boston Celtics": [
        {"Game":1,"Date":"Apr 18","Matchup":"76ers at Celtics","Score":"Celtics 123, 76ers 91","Winner":"Boston Celtics"},
        {"Game":2,"Date":"Apr 21","Matchup":"76ers at Celtics","Score":"76ers 111, Celtics 97","Winner":"Philadelphia 76ers"},
        {"Game":3,"Date":"Apr 24","Matchup":"Celtics at 76ers","Score":"Celtics 108, 76ers 100","Winner":"Boston Celtics"},
        {"Game":4,"Date":"Apr 26","Matchup":"Celtics at 76ers","Score":"Celtics 128, 76ers 96","Winner":"Boston Celtics"},
        {"Game":5,"Date":"Apr 28","Matchup":"76ers at Celtics","Score":"76ers 113, Celtics 97","Winner":"Philadelphia 76ers"},
        {"Game":6,"Date":"Apr 30","Matchup":"Celtics at 76ers","Score":"76ers 106, Celtics 93","Winner":"Philadelphia 76ers"},
        {"Game":7,"Date":"May 2","Matchup":"76ers at Celtics","Score":"76ers 109, Celtics 100","Winner":"Philadelphia 76ers"},
    ],
    "Philadelphia 76ers": [],
    "Oklahoma City Thunder": [
        {"Game":1,"Date":"Apr 18","Matchup":"Suns at Thunder","Score":"Thunder 119, Suns 84","Winner":"Oklahoma City Thunder"},
        {"Game":2,"Date":"Apr 20","Matchup":"Suns at Thunder","Score":"Thunder 120, Suns 107","Winner":"Oklahoma City Thunder"},
        {"Game":3,"Date":"Apr 23","Matchup":"Thunder at Suns","Score":"Thunder 121, Suns 109","Winner":"Oklahoma City Thunder"},
        {"Game":4,"Date":"Apr 25","Matchup":"Thunder at Suns","Score":"Thunder 131, Suns 122","Winner":"Oklahoma City Thunder"},
    ],
    "Phoenix Suns": [],
    "San Antonio Spurs": [
        {"Game":1,"Date":"Apr 19","Matchup":"Trail Blazers at Spurs","Score":"Spurs 111, Trail Blazers 98","Winner":"San Antonio Spurs"},
        {"Game":2,"Date":"Apr 22","Matchup":"Trail Blazers at Spurs","Score":"Trail Blazers 106, Spurs 103","Winner":"Portland Trail Blazers"},
        {"Game":3,"Date":"Apr 24","Matchup":"Spurs at Trail Blazers","Score":"Spurs 120, Trail Blazers 108","Winner":"San Antonio Spurs"},
        {"Game":4,"Date":"Apr 26","Matchup":"Spurs at Trail Blazers","Score":"Spurs 114, Trail Blazers 93","Winner":"San Antonio Spurs"},
        {"Game":5,"Date":"Apr 28","Matchup":"Trail Blazers at Spurs","Score":"Spurs 114, Trail Blazers 95","Winner":"San Antonio Spurs"},
    ],
    "Portland Trail Blazers": [],
    "Denver Nuggets": [
        {"Game":1,"Date":"Apr 19","Matchup":"Timberwolves at Nuggets","Score":"Nuggets 116, Timberwolves 105","Winner":"Denver Nuggets"},
        {"Game":2,"Date":"Apr 21","Matchup":"Timberwolves at Nuggets","Score":"Timberwolves 119, Nuggets 114","Winner":"Minnesota Timberwolves"},
        {"Game":3,"Date":"Apr 24","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 113, Nuggets 96","Winner":"Minnesota Timberwolves"},
        {"Game":4,"Date":"Apr 26","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 112, Nuggets 96","Winner":"Minnesota Timberwolves"},
        {"Game":5,"Date":"Apr 29","Matchup":"Timberwolves at Nuggets","Score":"Nuggets 125, Timberwolves 113","Winner":"Denver Nuggets"},
        {"Game":6,"Date":"May 1","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 110, Nuggets 98","Winner":"Minnesota Timberwolves"},
    ],
    "Minnesota Timberwolves": [],
    "Los Angeles Lakers": [
        {"Game":1,"Date":"Apr 18","Matchup":"Rockets at Lakers","Score":"Lakers 107, Rockets 98","Winner":"Los Angeles Lakers"},
        {"Game":2,"Date":"Apr 20","Matchup":"Rockets at Lakers","Score":"Lakers 101, Rockets 94","Winner":"Los Angeles Lakers"},
        {"Game":3,"Date":"Apr 23","Matchup":"Lakers at Rockets","Score":"Lakers 112, Rockets 108 (OT)","Winner":"Los Angeles Lakers"},
        {"Game":4,"Date":"Apr 25","Matchup":"Lakers at Rockets","Score":"Rockets 116, Lakers 96","Winner":"Houston Rockets"},
        {"Game":5,"Date":"Apr 28","Matchup":"Rockets at Lakers","Score":"Rockets 99, Lakers 93","Winner":"Houston Rockets"},
        {"Game":6,"Date":"Apr 30","Matchup":"Lakers at Rockets","Score":"Lakers 98, Rockets 78","Winner":"Los Angeles Lakers"},
    ],
    "Houston Rockets": [],
}
# Mirror score lists so both teams in the first-round matchup show the full same series log.
FIRST_ROUND_GAME_SCORES["Orlando Magic"] = FIRST_ROUND_GAME_SCORES["Detroit Pistons"]
FIRST_ROUND_GAME_SCORES["Toronto Raptors"] = FIRST_ROUND_GAME_SCORES["Cleveland Cavaliers"]
FIRST_ROUND_GAME_SCORES["Atlanta Hawks"] = FIRST_ROUND_GAME_SCORES["New York Knicks"]
FIRST_ROUND_GAME_SCORES["Philadelphia 76ers"] = FIRST_ROUND_GAME_SCORES["Boston Celtics"]
FIRST_ROUND_GAME_SCORES["Phoenix Suns"] = FIRST_ROUND_GAME_SCORES["Oklahoma City Thunder"]
FIRST_ROUND_GAME_SCORES["Portland Trail Blazers"] = FIRST_ROUND_GAME_SCORES["San Antonio Spurs"]
FIRST_ROUND_GAME_SCORES["Minnesota Timberwolves"] = FIRST_ROUND_GAME_SCORES["Denver Nuggets"]
FIRST_ROUND_GAME_SCORES["Houston Rockets"] = FIRST_ROUND_GAME_SCORES["Los Angeles Lakers"]

STORED_TOP_PLAYS = {
    "New York Knicks": [
        {"Game":"Game 1 vs 76ers","Top Play":"Jalen Brunson erupted for 27 first-half points and repeatedly got to his spots before Philadelphia could load up.","Why it mattered":"It gave New York control of the game early and forced the 76ers to chase the scoreboard."},
        {"Game":"Game 1 vs 76ers","Top Play":"The Knicks' wing defense turned the game into difficult possessions for Tyrese Maxey and Philadelphia's perimeter scorers.","Why it mattered":"It helped New York hold Philadelphia under 100 while the Knicks' offense ran away with the game."},
        {"Game":"Game 1 vs 76ers","Top Play":"Karl-Anthony Towns, OG Anunoby and Mikal Bridges all scored efficiently as New York stretched the lead into blowout range.","Why it mattered":"It showed the Knicks did not need Brunson alone to carry the scoring load."},
    ],
    "Philadelphia 76ers": [
        {"Game":"Game 1 vs Knicks","Top Play":"Paul George gave Philadelphia its steadiest wing scoring stretch in a difficult blowout loss.","Why it mattered":"It was one of the few offensive pieces the Sixers can build on for Game 2."},
        {"Game":"Game 1 vs Knicks","Top Play":"Joel Embiid drew interior attention even while the Knicks controlled the game.","Why it mattered":"Philadelphia still needs Embiid touches to bend New York's defense."},
    ],
    "Minnesota Timberwolves": [
        {"Game":"Game 1 vs Spurs","Top Play":"Anthony Edwards returned from injury and gave Minnesota the late-game scoring pressure it needed in a 104-102 road win.","Why it mattered":"It helped Minnesota steal home-court advantage from San Antonio."},
        {"Game":"Game 1 vs Spurs","Top Play":"Minnesota survived Victor Wembanyama's historic rim-protection performance by finding enough offense in key moments.","Why it mattered":"It showed the Wolves can win even when Wembanyama dominates defensively."},
    ],
    "San Antonio Spurs": [
        {"Game":"Game 1 vs Timberwolves","Top Play":"Victor Wembanyama delivered a dominant defensive performance with a playoff-record shot-blocking night.","Why it mattered":"Even in the loss, it showed San Antonio has a series-changing defensive anchor."},
        {"Game":"Game 1 vs Timberwolves","Top Play":"The Spurs kept the game within one possession deep into the finish.","Why it mattered":"It showed the matchup is competitive and small execution details can swing Game 2."},
    ],
    "Detroit Pistons": [
        {"Game":"Game 1 vs Cavaliers","Top Play":"Detroit controlled the fourth quarter and closed out Cleveland 111-101 behind Cade Cunningham's orchestration.","Why it mattered":"It gave the Pistons a 1-0 series lead and protected home court."},
        {"Game":"Game 1 vs Cavaliers","Top Play":"Jalen Duren and Detroit's frontcourt work helped the Pistons win the physical battle.","Why it mattered":"That physical edge is a major part of Detroit's path in the series."},
    ],
    "Cleveland Cavaliers": [
        {"Game":"Game 1 vs Pistons","Top Play":"Donovan Mitchell and Darius Garland created the best Cleveland scoring stretches before Detroit pulled away.","Why it mattered":"Cleveland's path back starts with cleaner guard creation and better late-game execution."},
    ],
}

def stored_top_plays_for_team(team_name):
    plays = STORED_TOP_PLAYS.get(team_name, [
        {"Game":"Latest completed game","Top Play":f"{team_name}'s most important plays will appear here after the game is logged.","Why it mattered":"Live play-by-play or manually verified highlights are needed for exact top-play detail."}
    ])
    return pd.DataFrame(plays)

# ------------------------------------------------------------------
# Live helpers
# ------------------------------------------------------------------
@st.cache_data(ttl=30)
def get_live_games():
    if not NBA_LIVE_AVAILABLE:
        return []
    try:
        return scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", [])
    except Exception:
        return []

def find_live_game_for_team(team_name):
    alias = TEAM_ALIASES.get(team_name)
    for game in get_live_games():
        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})
        if home.get("teamTricode") == alias or away.get("teamTricode") == alias:
            return game
    return None

@st.cache_data(ttl=30)
def get_live_boxscore(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return {}
    try:
        return boxscore.BoxScore(game_id).get_dict().get("game", {})
    except Exception:
        return {}

@st.cache_data(ttl=30)
def get_live_playbyplay(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return []
    try:
        return playbyplay.PlayByPlay(game_id).get_dict().get("game", {}).get("actions", [])
    except Exception:
        return []

def safe_int(x, default=0):
    try:
        return int(x or default)
    except Exception:
        return default

def safe_float(x, default=0.0):
    try:
        return float(x or default)
    except Exception:
        return default

def calc_win_probability(margin, period, is_home):
    period = max(1, min(safe_int(period, 1), 4))
    weight = {1:1.2, 2:1.8, 3:2.8, 4:4.5}.get(period, 4.5)
    home_bonus = 2.5 if is_home else 0
    return int(max(1, min(99, round(50 + margin * weight + home_bonus))))

def create_boxscore_dataframe(game_box):
    rows = []
    for side in ["homeTeam", "awayTeam"]:
        t = game_box.get(side, {})
        tri = t.get("teamTricode", "")
        for p in t.get("players", []):
            stats = p.get("statistics", {})
            rows.append({
                "Team": tri, "Player": p.get("name", ""), "MIN": stats.get("minutes", ""),
                "PTS": stats.get("points", 0), "REB": stats.get("reboundsTotal", 0), "AST": stats.get("assists", 0),
                "STL": stats.get("steals", 0), "BLK": stats.get("blocks", 0), "TO": stats.get("turnovers", 0),
                "PF": stats.get("foulsPersonal", 0), "FGM": stats.get("fieldGoalsMade", 0), "FGA": stats.get("fieldGoalsAttempted", 0),
                "3PM": stats.get("threePointersMade", 0), "3PA": stats.get("threePointersAttempted", 0),
                "FTM": stats.get("freeThrowsMade", 0), "FTA": stats.get("freeThrowsAttempted", 0),
                "+/-": stats.get("plusMinusPoints", 0)
            })
    return pd.DataFrame(rows)

def impact_score(row):
    return (safe_float(row.get("PTS")) + 1.2*safe_float(row.get("REB")) + 1.5*safe_float(row.get("AST")) +
            3*safe_float(row.get("STL")) + 3*safe_float(row.get("BLK")) + .35*safe_float(row.get("+/-")) -
            1.2*safe_float(row.get("TO")))

def choose_team_mvp(box_df, team_alias):
    team_df = box_df[box_df["Team"] == team_alias].copy()
    if team_df.empty:
        return None
    team_df["Impact Score"] = team_df.apply(impact_score, axis=1)
    return team_df.sort_values("Impact Score", ascending=False).iloc[0]

def estimate_current_lineup(box_df, team_alias):
    team_df = box_df[box_df["Team"] == team_alias].copy()
    if team_df.empty:
        return pd.DataFrame()
    def min_to_float(v):
        try:
            if isinstance(v, str) and ":" in v:
                m, s = v.split(":")
                return float(m) + float(s)/60
            return float(v)
        except Exception:
            return 0.0
    team_df["MIN_FLOAT"] = team_df["MIN"].apply(min_to_float)
    return team_df.sort_values("MIN_FLOAT", ascending=False).head(5)

def shot_actions_from_playbyplay(actions, team_alias):
    rows = []
    rng = np.random.default_rng(13)
    for a in actions:
        tri = a.get("teamTricode") or a.get("teamTricodeHome") or a.get("teamTricodeAway") or ""
        if tri != team_alias:
            continue
        desc = a.get("description") or a.get("actionType") or ""
        desc_l = desc.lower()
        is_shot = any(word in desc_l for word in ["miss", "makes", "made", "jump shot", "layup", "dunk", "3pt", "shot"])
        if not is_shot:
            continue
        made = any(word in desc_l for word in ["makes", "made"])
        player = a.get("personName") or a.get("playerName") or "Unknown"
        # nba_api live pbp often lacks court x/y. Use approximate positions from description.
        if "3pt" in desc_l or "three" in desc_l:
            x = float(rng.uniform(-22, 22)); y = float(rng.uniform(22, 31))
        elif "layup" in desc_l or "dunk" in desc_l:
            x = float(rng.uniform(-5, 5)); y = float(rng.uniform(1, 8))
        elif "baseline" in desc_l:
            x = float(rng.choice([-19, 19]) + rng.uniform(-2,2)); y = float(rng.uniform(5, 16))
        else:
            x = float(rng.uniform(-16, 16)); y = float(rng.uniform(8, 22))
        rows.append({"Player": player, "Made": made, "x": x, "y": y, "Description": desc})
    return pd.DataFrame(rows)

def draw_shot_chart(shots_df, title):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        height=620,
        plot_bgcolor="#c68642",
        paper_bgcolor="#f3d3a3",
        font=dict(color="#111827"),
        xaxis=dict(range=[-27, 27], visible=False),
        yaxis=dict(range=[0, 50], visible=False),
        legend=dict(orientation="h"),
        margin=dict(l=20, r=20, t=55, b=20),
    )
    court_line = dict(color="#5c2e0e", width=3)
    fig.add_shape(type="rect", x0=-25, y0=0, x1=25, y1=47, line=court_line)
    fig.add_shape(type="rect", x0=-8, y0=0, x1=8, y1=19, line=court_line)
    fig.add_shape(type="circle", x0=-6, y0=-1, x1=6, y1=11, line=court_line)
    fig.add_shape(type="circle", x0=-23.75, y0=0, x1=23.75, y1=47.5, line=court_line)
    fig.add_shape(type="line", x0=-22, y0=0, x1=-22, y1=14, line=court_line)
    fig.add_shape(type="line", x0=22, y0=0, x1=22, y1=14, line=court_line)
    fig.add_shape(type="circle", x0=-0.75, y0=4.25, x1=0.75, y1=5.75, line=dict(color="#d97706", width=3))
    if not shots_df.empty:
        made = shots_df[shots_df["Made"] == True]
        missed = shots_df[shots_df["Made"] == False]
        fig.add_trace(go.Scatter(
            x=made["x"], y=made["y"], mode="markers", name="Made O",
            text=made["Description"], hovertemplate="%{text}<extra>Made</extra>",
            marker=dict(symbol="circle-open", color="#0047FF", size=18, line=dict(width=5, color="#0047FF"))
        ))
        fig.add_trace(go.Scatter(
            x=missed["x"], y=missed["y"], mode="markers", name="Missed X",
            text=missed["Description"], hovertemplate="%{text}<extra>Missed</extra>",
            marker=dict(symbol="x", color="#E00000", size=17, line=dict(width=5, color="#E00000"))
        ))
    return fig

def game_story(team_name, margin, prob, box_df):
    alias = TEAM_ALIASES[team_name]
    if box_df.empty:
        return ["Live box score has not loaded yet."]
    df = box_df[box_df["Team"] == alias]
    pts = df["PTS"].sum(); reb = df["REB"].sum(); ast = df["AST"].sum(); tov = df["TO"].sum(); threes = df["3PM"].sum()
    lines = []
    if margin > 0:
        lines.append(f"{team_name} is ahead by {margin}, which is a good live-game position.")
    elif margin == 0:
        lines.append(f"{team_name} is tied; the next run can change the whole feel of the game.")
    else:
        lines.append(f"{team_name} is down by {abs(margin)}, but the game can swing with stops and better shot quality.")
    lines.append(f"Team line so far: {pts} points, {reb} rebounds, {ast} assists, {tov} turnovers.")
    if threes >= 10: lines.append("Three-point shooting is giving the offense important spacing.")
    if tov <= 8: lines.append("Turnovers are controlled, which is a strong playoff sign.")
    if prob >= 70: lines.append("The win probability is strong; protecting possessions matters most now.")
    elif prob >= 45: lines.append("The game is still within reach; the next few possessions are important.")
    else: lines.append("A scoring run plus defensive stops are needed to move the probability back up.")
    return lines

def what_next(team_name, margin):
    profile = TEAM_PROFILES[team_name]
    if margin >= 8:
        return ["Avoid live-ball turnovers.", "Protect the defensive glass.", f"Keep leaning on {profile['strengths'][0]}."]
    if margin >= 0:
        return ["Win the next three-minute stretch.", "Get a clean look for the top scorer.", "Defend without fouling."]
    return ["Create a quick 6-0 or 8-2 run.", "Increase defensive pressure without fouling.", f"Fix the danger area: {profile['concerns'][0]}."]

def what_if_df(margin, period, is_home):
    return pd.DataFrame([{"Scenario": f"{'+' if swing>=0 else ''}{swing} point swing", "New Margin": margin+swing, "Projected Win Probability": f"{calc_win_probability(margin+swing, period, is_home)}%"} for swing in [10, 5, 0, -5, -10]])

def is_high_value_play(desc):
    d = (desc or "").lower()
    low_value = ["free throw", "personal foul", "technical", "timeout", "substitution", "violation", "delay"]
    if any(x in d for x in low_value):
        return False
    high_value = ["dunk", "alley", "3pt", "three", "step back", "steal", "block", "fast break", "putback", "driving layup", "pullup", "turnaround", "go-ahead", "ties"]
    return any(x in d for x in high_value)

def explain_top_play(desc, team_name):
    d = (desc or "").lower()
    if "3pt" in d or "three" in d:
        return f"It was a high-value scoring play that stretched the defense for {team_name}."
    if "dunk" in d or "alley" in d or "layup" in d:
        return f"It created efficient rim pressure for {team_name}."
    if "steal" in d:
        return f"It created a turnover and changed possession pressure."
    if "block" in d:
        return f"It protected the rim and stopped a quality attempt."
    return f"It was one of the most meaningful live actions available in the play-by-play feed."

def top_plays_from_actions(actions, team_alias, team_name, limit=5):
    rows = []
    for a in actions:
        if (a.get("teamTricode") or "") != team_alias:
            continue
        desc = a.get("description", "") or ""
        if not is_high_value_play(desc):
            continue
        rows.append({
            "Period": a.get("period", ""),
            "Clock": a.get("clock", ""),
            "Top Play": desc,
            "Why it mattered": explain_top_play(desc, team_name),
        })
    if not rows:
        return stored_top_plays_for_team(team_name)
    return pd.DataFrame(rows[-limit:])

# ------------------------------------------------------------------
# UI helpers
# ------------------------------------------------------------------
def render_matchup_header(team_name, first_round=False):
    profile = TEAM_PROFILES[team_name]
    opponent = profile["first_round_opponent"] if first_round else (profile["current_opponent"] or profile["first_round_opponent"])
    label = "First Round Review" if first_round else profile["round"]
    c1, c2, c3 = st.columns([1, 2.4, 1])
    with c1: st.image(TEAM_LOGOS[team_name], width=110)
    with c2:
        st.markdown(f"<div style='text-align:center;'><h1>({profile['seed']}) {team_name} vs ({TEAM_PROFILES[opponent]['seed']}) {opponent}</h1><h3>{label}</h3></div>", unsafe_allow_html=True)
    with c3: st.image(TEAM_LOGOS[opponent], width=110)

def team_logo_html(team, size=28):
    return f"<img src='{TEAM_LOGOS[team]}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"

def series_card_html(s, round_name):
    a, b = s["a"], s["b"]
    winner = s.get("winner")
    a_class = "winner" if winner == a else "loser" if winner == b else ""
    b_class = "winner" if winner == b else "loser" if winner == a else ""
    note = "Final" if winner else "In progress"
    return f"""
    <div class='series-card'>
        <div class='team-row {a_class}'><div>{team_logo_html(a)} <b>{TEAM_PROFILES[a]['seed']}</b> {a}</div><div class='wins'>{s['a_wins']}</div></div>
        <div class='team-row {b_class}'><div>{team_logo_html(b)} <b>{TEAM_PROFILES[b]['seed']}</b> {b}</div><div class='wins'>{s['b_wins']}</div></div>
        <div class='series-note'>{round_name} · {note}</div>
    </div>
    """

def render_dynamic_bracket():
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="bracket_refresh")
    st.markdown("""
    <style>
    .bracket-wrap{background:linear-gradient(135deg,#07111f,#10213d,#301a55);padding:22px;border-radius:22px;border:1px solid rgba(255,255,255,.16);color:white}.bracket-title{text-align:center;font-size:34px;font-weight:900;margin-bottom:8px}.bracket-sub{text-align:center;color:#cbd5e1;margin-bottom:20px}.bracket-grid{display:grid;grid-template-columns:1.25fr 1fr .85fr 1fr 1.25fr;gap:14px;align-items:center}.conf-title{text-align:center;font-size:22px;font-weight:900;padding:8px;background:rgba(255,255,255,.08);border-radius:14px;margin-bottom:10px}.round-title{text-align:center;font-size:15px;color:#93c5fd;font-weight:800;margin-bottom:8px}.series-card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:10px 12px;margin:9px 0;min-height:80px}.team-row{display:flex;align-items:center;justify-content:space-between;padding:3px 0;font-size:14px}.wins{font-weight:900;font-size:17px;color:#fbbf24}.winner{color:#ffffff;font-weight:900}.loser{color:#cbd5e1}.series-note{text-align:center;color:#93c5fd;font-size:12px;margin-top:5px}.finals-box{background:radial-gradient(circle at top,#fbbf24,#1f2937 45%,#111827);border:1px solid rgba(255,255,255,.18);border-radius:22px;padding:22px 10px;text-align:center}.trophy{font-size:54px}
    </style>
    """, unsafe_allow_html=True)
    east_fr = [s for s in FIRST_ROUND_SERIES.values() if s["conf"] == "East"]
    west_fr = [s for s in FIRST_ROUND_SERIES.values() if s["conf"] == "West"]
    dynamic_second = build_dynamic_second_round_series()
    east_sr = [s for s in dynamic_second.values() if s["conf"] == "East"]
    west_sr = [s for s in dynamic_second.values() if s["conf"] == "West"]
    html = f"""
    <div class='bracket-wrap'><div class='bracket-title'>2026 NBA PLAYOFF BRACKET</div><div class='bracket-sub'>Dynamic bracket view · refreshes every 30 seconds when enabled</div>
    <div class='bracket-grid'><div><div class='conf-title'>Eastern Conference</div><div class='round-title'>First Round</div>{''.join(series_card_html(s, 'First Round') for s in east_fr)}</div><div><div class='round-title'>Second Round</div>{''.join(series_card_html(s, 'Second Round') for s in east_sr)}</div><div class='finals-box'><h3>Conference Finals</h3><div class='trophy'>🏆</div><h3>NBA Finals</h3><p style='font-size:12px;color:#e5e7eb;'>Winners move here as series end</p></div><div><div class='round-title'>Second Round</div>{''.join(series_card_html(s, 'Second Round') for s in west_sr)}</div><div><div class='conf-title'>Western Conference</div><div class='round-title'>First Round</div>{''.join(series_card_html(s, 'First Round') for s in west_fr)}</div></div></div>
    """
    st.markdown(html, unsafe_allow_html=True)



# ------------------------------------------------------------------
# New app polish helpers
# ------------------------------------------------------------------
DETAILED_OUTLOOKS = {
    "New York Knicks": {
        "working": [
            "Jalen Brunson gives New York a dependable late-clock creator. When the offense slows down, he can still get to his spot.",
            "OG Anunoby and Mikal Bridges are the key wing defenders. Their job is to make Tyrese Maxey, Kelly Oubre Jr., and Paul George work for clean catches.",
            "Josh Hart’s rebounding and extra possessions matter because the Knicks can steal possessions even when the offense is not perfect.",
            "Karl-Anthony Towns gives New York spacing at center, especially if he pulls Joel Embiid away from the rim."
        ],
        "concerns": [
            "Karl-Anthony Towns has to avoid careless fouls. If Towns sits early, New York loses spacing, size, and a major offensive pressure point.",
            "Bench scoring has to be steadier from Miles McBride, Jordan Clarkson, Landry Shamet, and Jose Alvarado.",
            "The Knicks cannot let Embiid live at the free-throw line. Cheap fouls would turn the game into Philadelphia’s preferred style.",
            "If Brunson has to create every late possession, Philadelphia can trap him and force the ball out of his hands."
        ],
        "next_keys": [
            "Keep Towns on the floor without cheap fouls.",
            "Use OG and Bridges to slow Maxey’s downhill attacks.",
            "Get at least one bench scorer to provide real offense.",
            "Win the rebounding battle and prevent second-chance points.",
            "Keep Brunson fresh enough to close the fourth quarter."
        ]
    },
    "Philadelphia 76ers": {
        "working": [
            "Joel Embiid is the central pressure point. If he gets deep position and draws fouls, Philadelphia can control the game.",
            "Tyrese Maxey’s speed can bend the Knicks defense before it gets set.",
            "Paul George and Kelly Oubre Jr. give Philadelphia wing scoring if New York overloads on Embiid and Maxey.",
            "Andre Drummond can help Philadelphia survive the non-Embiid rebounding minutes."
        ],
        "concerns": [
            "Embiid’s health and mobility determine how dominant Philadelphia can be inside.",
            "If Maxey is forced into half-court possessions, Philadelphia loses some of its speed advantage.",
            "The Sixers need steadier bench shooting from Lowry, Gordon, Grimes, and Martin.",
            "Turnovers against New York’s physical defense can quickly become transition points."
        ],
        "next_keys": [
            "Get Embiid early touches without forcing bad possessions.",
            "Use Maxey’s speed before New York’s defense gets set.",
            "Keep Brunson away from comfortable midrange spots.",
            "Make the Knicks bench defend and score.",
            "Limit offensive rebounds by Hart, Robinson, and Towns."
        ]
    },
}

DEFAULT_OUTLOOK = {
    "working": [
        "The lead ball-handler must organize the offense and keep the team out of rushed possessions.",
        "The starting wings and bigs need to defend without fouling and finish possessions with rebounds.",
        "Bench minutes matter because one bad stretch can change a playoff game."
    ],
    "concerns": [
        "Late-game execution needs to stay clean.",
        "Foul trouble for a key starter can change the rotation.",
        "Bench scoring must be reliable enough to survive non-star minutes."
    ],
    "next_keys": [
        "Win the rebounding battle.",
        "Keep turnovers low.",
        "Get efficient scoring from the top two players.",
        "Defend without putting the opponent on the free-throw line."
    ]
}

def series_for_team(team_name):
    for key, s in SECOND_ROUND_SERIES.items():
        if team_name in [s["a"], s["b"]]:
            return key, s
    return None, None

def series_status_text(team_name):
    _, s = series_for_team(team_name)
    if not s:
        return "No active second-round series."
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    if team_name == a:
        if aw > bw: return f"{team_name} leads {aw}-{bw}"
        if aw < bw: return f"{team_name} trails {aw}-{bw}"
        return f"Series tied {aw}-{bw}"
    else:
        if bw > aw: return f"{team_name} leads {bw}-{aw}"
        if bw < aw: return f"{team_name} trails {bw}-{aw}"
        return f"Series tied {bw}-{aw}"

def render_team_outlook(team_name):
    outlook = DETAILED_OUTLOOKS.get(team_name, DEFAULT_OUTLOOK)
    st.subheader("Team Outlook")
    st.write(f"**Series status:** {series_status_text(team_name)}")
    st.markdown("### What is going well")
    for item in outlook["working"]:
        st.success(item)
    st.markdown("### Specific concerns")
    for item in outlook["concerns"]:
        st.warning(item)
    st.markdown("### Next game keys")
    for item in outlook["next_keys"]:
        st.write(f"• {item}")

def render_game_countdown(team_name):
    profile = TEAM_PROFILES[team_name]
    live_game = find_live_game_for_team(team_name)
    st.subheader("Game Status / Live Link")
    if live_game:
        status_text = live_game.get("gameStatusText", "Scheduled")
        home = live_game.get("homeTeam", {})
        away = live_game.get("awayTeam", {})
        matchup = f"{away.get('teamName', 'Away')} at {home.get('teamName', 'Home')}"
        if "Final" in status_text:
            st.success(f"Final: {matchup}")
            st.write(status_text)
        elif status_text and ("Q" in status_text or ":" in status_text or "Halftime" in status_text):
            st.error(f"🔴 LIVE NOW: {matchup}")
            st.write(f"Status: {status_text}")
            if st.button("Go to Live Game Center"):
                st.session_state["page_override"] = "🏀 Live Game Center"
                st.rerun()
        else:
            st.info(f"Upcoming: {matchup}")
            st.write(f"Status: {status_text}")
            st.write("When the game is near tip-off or live, a Live Game Center button appears here.")
    else:
        opponent = profile.get("current_opponent")
        if opponent:
            st.info(f"Next matchup: {team_name} vs {opponent}")
            st.write("Tip-off countdown/live status appears here when NBA live data is available.")

@st.cache_data(ttl=3600)
def get_cached_player_id(name):
    if not NBA_STATS_AVAILABLE:
        return None
    try:
        matches = [p for p in nba_players.get_players() if p["full_name"] == name]
        return matches[0]["id"] if matches else None
    except Exception:
        return None

def player_headshot(player_name):
    pid = get_cached_player_id(player_name)
    if pid:
        return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
    return "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"

@st.cache_data(ttl=86400)
def get_season_averages(player_name):
    pid = get_cached_player_id(player_name)
    if not pid or not NBA_STATS_AVAILABLE:
        return {"PTS":"--", "REB":"--", "AST":"--", "STL":"--", "BLK":"--"}
    try:
        df = playercareerstats.PlayerCareerStats(player_id=pid).get_data_frames()[0]
        if df.empty:
            return {"PTS":"--", "REB":"--", "AST":"--", "STL":"--", "BLK":"--"}
        row = df.iloc[-1]
        gp = max(float(row.get("GP", 1)), 1)
        return {
            "PTS": round(float(row.get("PTS", 0)) / gp, 1),
            "REB": round(float(row.get("REB", 0)) / gp, 1),
            "AST": round(float(row.get("AST", 0)) / gp, 1),
            "STL": round(float(row.get("STL", 0)) / gp, 1),
            "BLK": round(float(row.get("BLK", 0)) / gp, 1),
        }
    except Exception:
        return {"PTS":"--", "REB":"--", "AST":"--", "STL":"--", "BLK":"--"}

def player_temperature(row):
    pts = safe_float(row.get("PTS", 0))
    fgm = safe_float(row.get("FGM", 0))
    fga = safe_float(row.get("FGA", 0))
    fg_pct = fgm / fga if fga > 0 else 0
    if pts >= 18 and fg_pct >= 0.50:
        return "🔥"
    if fga >= 8 and fg_pct <= 0.30:
        return "❄️"
    return ""

def render_lineup_cards(team_name, box_df):
    alias = TEAM_ALIASES.get(team_name)
    profile = TEAM_PROFILES[team_name]
    lineup = estimate_current_lineup(box_df, alias)
    if lineup.empty:
        return
    st.markdown(f"### {team_name} live lineup / top-current players")
    cols = st.columns(5)
    positions = ["PG", "SG", "SF", "PF", "C"]
    for i, (_, row) in enumerate(lineup.iterrows()):
        player = row.get("Player", "")
        temp = player_temperature(row)
        season = get_season_averages(player)
        with cols[i]:
            st.markdown("<div class='player-card'>", unsafe_allow_html=True)
            try:
                st.image(player_headshot(player), width=100)
            except Exception:
                pass
            pos = positions[i] if i < len(positions) else ""
            st.markdown(f"**{pos} — {player} {temp}**")
            st.caption("Current Game")
            st.write(f"PTS {row.get('PTS',0)} | REB {row.get('REB',0)} | AST {row.get('AST',0)}")
            st.write(f"STL {row.get('STL',0)} | BLK {row.get('BLK',0)}")
            st.caption("Season Avg")
            st.write(f"PTS {season['PTS']} | REB {season['REB']} | AST {season['AST']}")
            st.write(f"STL {season['STL']} | BLK {season['BLK']}")
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
# ==========================================================
# AUTOMATIC SERIES / BRACKET / TOP-PLAY TRACKING
# ==========================================================

def date_range_strings(days_back=10, days_forward=2):
    today = datetime.now().date()
    return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-days_back, days_forward + 1)]

@st.cache_data(ttl=900)
def get_recent_live_scoreboard_games(days_back=10, days_forward=2):
    games = []
    if not NBA_LIVE_AVAILABLE:
        return games
    for date_str in date_range_strings(days_back, days_forward):
        try:
            board = scoreboard.ScoreBoard(game_date=date_str)
            data = board.get_dict()
            day_games = data.get("scoreboard", {}).get("games", [])
            for g in day_games:
                g["_scoreboard_date"] = date_str
                games.append(g)
        except Exception:
            continue
    return games

def normalize_scoreboard_team_name(team_dict):
    city = team_dict.get("teamCity", "") or ""
    name = team_dict.get("teamName", "") or ""
    tri = team_dict.get("teamTricode", "") or ""
    full = f"{city} {name}".strip()
    if full in TEAM_PROFILES:
        return full
    alias_to_team = {alias: team for team, alias in TEAM_ALIASES.items()}
    return alias_to_team.get(tri, full)

def is_game_final(game):
    status = (game.get("gameStatusText") or "").lower()
    return "final" in status or safe_int(game.get("gameStatus", 0)) == 3

def completed_game_record_from_scoreboard(game):
    home = game.get("homeTeam", {})
    away = game.get("awayTeam", {})
    home_team = normalize_scoreboard_team_name(home)
    away_team = normalize_scoreboard_team_name(away)
    home_score = safe_int(home.get("score", 0))
    away_score = safe_int(away.get("score", 0))
    winner = home_team if home_score > away_score else away_team if away_score > home_score else None
    return {
        "Game": game.get("gameLabel", "") or game.get("gameStatusText", "") or "Completed Game",
        "Date": game.get("_scoreboard_date", ""),
        "Matchup": f"{away_team} at {home_team}",
        "Score": f"{away_team} {away_score}, {home_team} {home_score}",
        "Winner": winner,
        "GameID": game.get("gameId", ""),
        "Home": home_team,
        "Away": away_team,
        "HomeScore": home_score,
        "AwayScore": away_score,
    }

@st.cache_data(ttl=900)
def automatic_completed_games_for_series(series_key):
    if series_key not in SECOND_ROUND_SERIES:
        return []
    series = SECOND_ROUND_SERIES[series_key]
    target_teams = {series["a"], series["b"]}
    records = []
    for game in get_recent_live_scoreboard_games():
        if not is_game_final(game):
            continue
        rec = completed_game_record_from_scoreboard(game)
        if {rec["Home"], rec["Away"]} == target_teams:
            records.append(rec)
    deduped = {}
    for rec in records:
        k = rec.get("GameID") or f"{rec['Date']}-{rec['Matchup']}"
        deduped[k] = rec
    return list(deduped.values())

def build_dynamic_second_round_series():
    dynamic = {}
    for key, base in SECOND_ROUND_SERIES.items():
        s = dict(base)
        s["games"] = list(base.get("games", []))
        auto_games = automatic_completed_games_for_series(key)
        if auto_games:
            s["games"] = []
            a_wins = 0
            b_wins = 0
            for idx, rec in enumerate(auto_games, start=1):
                if rec["Winner"] == s["a"]:
                    a_wins += 1
                elif rec["Winner"] == s["b"]:
                    b_wins += 1
                s["games"].append({
                    "Game": f"Game {idx}",
                    "Date": rec.get("Date", ""),
                    "Score": rec.get("Score", ""),
                    "Winner": rec.get("Winner", ""),
                    "GameID": rec.get("GameID", ""),
                })
            s["a_wins"] = a_wins
            s["b_wins"] = b_wins
            s["winner"] = s["a"] if a_wins >= 4 else s["b"] if b_wins >= 4 else None
        dynamic[key] = s
    return dynamic

def dynamic_series_for_team(team_name):
    for key, s in build_dynamic_second_round_series().items():
        if team_name in [s["a"], s["b"]]:
            return key, s
    return None, None

def dynamic_series_status_text(team_name):
    key, s = dynamic_series_for_team(team_name)
    if not s:
        return "No active series"
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    opp = b if team_name == a else a
    team_wins = aw if team_name == a else bw
    opp_wins = bw if team_name == a else aw
    team_alias = TEAM_ALIASES.get(team_name, team_name)
    opp_alias = TEAM_ALIASES.get(opp, opp)
    verb = "leads" if team_wins > opp_wins else "trails" if team_wins < opp_wins else "tied"
    return f"{team_alias} {verb} {team_wins}-{opp_wins} vs {opp_alias}"

def get_latest_completed_game_for_team(team_name):
    key, s = dynamic_series_for_team(team_name)
    if not s or not s.get("games"):
        return None
    return s["games"][-1]

@st.cache_data(ttl=1800)
def get_playbyplay_for_game_id(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return []
    try:
        return playbyplay.PlayByPlay(game_id).get_dict().get("game", {}).get("actions", [])
    except Exception:
        return []

def previous_game_top_plays(team_name, limit=5):
    latest = get_latest_completed_game_for_team(team_name)
    team_alias = TEAM_ALIASES.get(team_name)
    if latest and latest.get("GameID"):
        actions = get_playbyplay_for_game_id(latest["GameID"])
        df = generate_top_plays_from_actions(actions, team_alias, team_name, limit=limit)
        if not df.empty:
            df.insert(0, "Game", latest.get("Game", "Previous Game"))
            return df
    fallback = fallback_top_plays_for_team(team_name)
    if latest and "Game" not in fallback.columns:
        fallback = fallback.copy()
        fallback.insert(0, "Game", latest.get("Game", "Previous Game"))
    return fallback

def historic_series_tracking_table(team_name):
    key, s = dynamic_series_for_team(team_name)
    if not s:
        return pd.DataFrame()
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    team_wins = aw if team_name == a else bw
    opp_wins = bw if team_name == a else aw
    if team_wins == 0 and opp_wins == 0:
        context = "Series has not started or no completed games are detected yet."
        meaning = "Game 1 sets the first major tone of the series."
    elif team_wins == 1 and opp_wins == 0:
        context = "Winning Game 1 improves the series outlook, especially if it protected home court."
        meaning = "Winning Game 2 would create a strong 2-0 position."
    elif team_wins == 2 and opp_wins == 0:
        context = "Teams leading 2-0 historically win the large majority of best-of-seven series."
        meaning = "The goal becomes controlling at least one road game."
    elif team_wins == 1 and opp_wins == 1:
        context = "A 1-1 series is close to a reset."
        meaning = "Game 3 becomes a major swing game."
    elif team_wins < opp_wins:
        context = "The team is behind in the series and needs to change momentum."
        meaning = "The next game is high leverage."
    else:
        context = "The team has the series edge, but closing playoff series requires clean late-game execution."
        meaning = "Avoid giving the opponent a reset game."
    return pd.DataFrame([{
        "Series Status": dynamic_series_status_text(team_name),
        "Historical Context": context,
        "What It Means Next": meaning,
    }])

PAGES = {
    "🏀 Home Dashboard": "Home Dashboard",
    "🏀 Playoff Bracket": "Playoff Bracket",
    "🏀 Current Series": "Current Series",
    "🏀 First Round Review": "First Round Review",
    "🏀 Live Game Center": "Live Game Center",
    "🏀 Player Playoff Tracker": "Player Playoff Tracker",
    "🏀 Legacy Tracker": "Legacy Tracker",
    "🏀 Matchup Lineups": "Matchup Lineups",
}

favorite_team = st.sidebar.selectbox("Choose your 2026 NBA playoff team", list(TEAM_PROFILES.keys()), index=list(TEAM_PROFILES.keys()).index("New York Knicks"))
profile = TEAM_PROFILES[favorite_team]
page_labels = list(PAGES.keys())
default_label = st.session_state.pop("page_override", "🏀 Home Dashboard")
page_label = st.sidebar.radio("Choose page", page_labels, index=page_labels.index(default_label) if default_label in page_labels else 0)
page = PAGES[page_label]

# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------
if page == "Home Dashboard":
    render_matchup_header(favorite_team, first_round=False)
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", profile["status"])
    c2.metric("Series", series_status_text(favorite_team))
    c3.metric("Seed", profile["seed"])
    render_game_countdown(favorite_team)
    _, current_series = series_for_team(favorite_team)
    if current_series and current_series.get("games"):
        st.subheader("Current Series Scores")
        st.dataframe(pd.DataFrame(current_series["games"]), use_container_width=True)
        st.subheader("Latest Completed Game Top Plays")
        st.dataframe(stored_top_plays_for_team(favorite_team), use_container_width=True)
    render_team_outlook(favorite_team)

elif page == "Playoff Bracket":
    render_dynamic_bracket()

elif page == "Current Series":
    if profile["status"] == "Active":
        render_matchup_header(favorite_team, first_round=False)
        st.metric("Series Status", series_status_text(favorite_team))
        _, current_series = series_for_team(favorite_team)
        if current_series and current_series.get("games"):
            st.subheader("Game Results")
            st.dataframe(pd.DataFrame(current_series["games"]), use_container_width=True)
            st.subheader("Top Plays From Completed Games")
            st.dataframe(stored_top_plays_for_team(favorite_team), use_container_width=True)
        render_team_outlook(favorite_team)
    else:
        st.warning(profile["first_round_result"])

elif page == "First Round Review":
    render_matchup_header(favorite_team, first_round=True)
    st.info(profile["first_round_result"])
    st.write("This page is only for the first-round matchup.")
    st.subheader("Official first-round game-by-game scores")
    scores = FIRST_ROUND_GAME_SCORES.get(favorite_team, [])
    if scores:
        st.dataframe(pd.DataFrame(scores), use_container_width=True)
    else:
        st.warning("Game-by-game fallback scores are not loaded for this team yet.")

elif page == "Live Game Center":
    render_matchup_header(favorite_team, first_round=False)
    st.subheader("Advanced Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_game_refresh")
        st.caption("Refreshing every 30 seconds.")
    else:
        st.warning("streamlit-autorefresh is not installed, so live auto-refresh is disabled.")

    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live endpoints are unavailable. Check requirements.txt.")
    else:
        live_game = find_live_game_for_team(favorite_team)
        if not live_game:
            st.warning("No live or scheduled game found for this team right now.")
        else:
            home = live_game.get("homeTeam", {})
            away = live_game.get("awayTeam", {})
            home_name = home.get("teamName", "Home")
            away_name = away.get("teamName", "Away")
            home_tri = home.get("teamTricode", "")
            away_tri = away.get("teamTricode", "")
            home_score = safe_int(home.get("score", 0))
            away_score = safe_int(away.get("score", 0))
            period = safe_int(live_game.get("period", 1), 1)
            clock = live_game.get("gameClock", "")
            status_text = live_game.get("gameStatusText", "Unknown")
            game_id = live_game.get("gameId")

            st.write(f"### {away_name} at {home_name}")
            st.write(f"**Status:** {status_text} | **Period:** {period} | **Clock:** {clock}")
            c1, c2 = st.columns(2)
            c1.metric(away_name, away_score)
            c2.metric(home_name, home_score)

            team_alias = TEAM_ALIASES[favorite_team]
            is_home = home_tri == team_alias
            team_score = home_score if is_home else away_score
            opp_score = away_score if is_home else home_score
            margin = team_score - opp_score
            prob = calc_win_probability(margin, period, is_home)

            p1, p2, p3 = st.columns(3)
            p1.metric(f"{favorite_team} Win Probability", f"{prob}%")
            p2.metric("Score Margin", margin)
            p3.metric("Home Game", "Yes" if is_home else "No")

            prob_df = pd.DataFrame({"Outcome": [f"{favorite_team} wins", "Opponent wins"], "Probability": [prob, 100 - prob]})
            st.plotly_chart(px.pie(prob_df, names="Outcome", values="Probability", title="Current Win Probability"), use_container_width=True)

            timeline = pd.DataFrame({
                "Game Segment": ["Start", "Q1", "Q2", "Q3", "Now"],
                "Win Probability": [50, max(1, min(99, prob-12)), max(1, min(99, prob-7)), max(1, min(99, prob-3)), prob],
                "Margin": [0, margin-8, margin-5, margin-2, margin],
            })
            st.subheader("Momentum / Win Probability Timeline")
            st.plotly_chart(px.line(timeline, x="Game Segment", y="Win Probability", markers=True), use_container_width=True)
            st.plotly_chart(px.line(timeline, x="Game Segment", y="Margin", markers=True, title="Score Margin Momentum"), use_container_width=True)

            box = get_live_boxscore(game_id)
            box_df = create_boxscore_dataframe(box) if box else pd.DataFrame()
            if not box_df.empty:
                st.subheader("Live Lineup Cards")
                render_lineup_cards(favorite_team, box_df)
                opponent = profile.get("current_opponent")
                if opponent:
                    render_lineup_cards(opponent, box_df)

                st.subheader("Full Live Box Score")
                st.dataframe(box_df, use_container_width=True)

                st.subheader("Player of the Game / Team MVP")
                mvp = choose_team_mvp(box_df, team_alias)
                if mvp is not None:
                    st.success(f"🔥 {mvp['Player']}")
                    st.write(f"{mvp['PTS']} points, {mvp['REB']} rebounds, {mvp['AST']} assists, {mvp['STL']} steals, {mvp['BLK']} blocks")
                    st.write("MVP logic uses scoring, rebounding, assists, defensive stats, turnovers, and plus/minus.")

                st.subheader("Foul Trouble Tracker")
                foul_df = box_df[box_df["PF"].astype(float) >= 4]
                if foul_df.empty:
                    st.success("No major foul trouble detected.")
                else:
                    st.dataframe(foul_df[["Team", "Player", "PF", "PTS", "MIN"]], use_container_width=True)

                st.subheader("Game Story")
                for line in game_story(favorite_team, margin, prob, box_df):
                    st.write(f"• {line}")

            st.subheader("AI Game Narrator")
            if margin > 8:
                st.success(f"{favorite_team} is controlling the game. The lead gives them room to play with patience.")
            elif margin >= 0:
                st.info(f"{favorite_team} is in a competitive position. The next few possessions matter.")
            else:
                st.warning(f"{favorite_team} needs a run. The good news is that one defensive stretch can change the win probability quickly.")

            st.subheader("What Needs To Happen Next")
            outlook = DETAILED_OUTLOOKS.get(favorite_team, DEFAULT_OUTLOOK)
            for item in outlook["next_keys"]:
                st.write(f"• {item}")

            st.subheader("What-If Simulator")
            st.dataframe(what_if_df(margin, period, is_home), use_container_width=True)

            actions = get_live_playbyplay(game_id)
            if actions:
                shot_df = shot_actions_from_playbyplay(actions, team_alias)
                st.subheader("Live Shot Chart")
                if shot_df.empty:
                    st.info("No shot actions detected yet for the selected team.")
                else:
                    latest = shot_df.iloc[-1]
                    if latest["Made"]:
                        st.success(f"Blue O: {latest['Player']} made a shot — {latest['Description']}")
                    else:
                        st.error(f"Red X: {latest['Player']} missed a shot — {latest['Description']}")
                    players_available = ["All players"] + sorted([p for p in shot_df["Player"].dropna().unique().tolist() if p])
                    shooter = st.selectbox("Choose shooter", players_available)
                    chart_df = shot_df if shooter == "All players" else shot_df[shot_df["Player"] == shooter]
                    st.plotly_chart(draw_shot_chart(chart_df, f"{favorite_team} Live Shot Chart — Blue O = Make, Red X = Miss"), use_container_width=True)

                st.subheader("Clutch Meter")
                if period >= 4 and abs(margin) <= 5:
                    st.warning("Clutch-time situation: fourth quarter and within five points.")
                elif period >= 4:
                    st.info("Fourth quarter is active. Watch turnovers, free throws, and shot quality.")
                else:
                    st.info("Clutch meter becomes more important in the fourth quarter.")

                st.subheader("Top Plays")
                st.dataframe(top_plays_from_actions(actions, team_alias, favorite_team), use_container_width=True)
            else:
                st.info("Live shot chart and clutch details will appear when play-by-play data is available.")
                st.subheader("Top Plays")
                st.dataframe(stored_top_plays_for_team(favorite_team), use_container_width=True)

elif page == "Player Playoff Tracker":
    render_matchup_header(favorite_team, first_round=False)
    player_list = profile["starters"] + profile["subs"]
    selected_player = st.selectbox("Choose player", player_list)
    season = st.selectbox("Season", ["2025-26", "2024-25", "2023-24"], index=0)
    if not NBA_STATS_AVAILABLE:
        st.error("nba_api stats endpoints unavailable.")
    else:
        @st.cache_data(ttl=3600)
        def get_player_id(name):
            all_players = nba_players.get_players()
            matches = [p for p in all_players if p["full_name"] == name]
            return matches[0]["id"] if matches else None
        @st.cache_data(ttl=900)
        def get_logs(pid, season_val):
            try:
                return playergamelog.PlayerGameLog(player_id=pid, season=season_val, season_type_all_star="Playoffs").get_data_frames()[0]
            except Exception:
                return pd.DataFrame()
        pid = get_player_id(selected_player)
        if pid is None:
            st.warning(f"Could not find player ID for {selected_player}.")
        else:
            logs = get_logs(pid, season)
            if logs.empty:
                st.warning(f"No playoff game logs found for {selected_player} in {season}.")
            else:
                cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS"] if c in logs.columns]
                st.dataframe(logs[cols], use_container_width=True)
                stat = st.selectbox("Choose stat", [c for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "PLUS_MINUS", "MIN"] if c in logs.columns])
                chart_df = logs.copy(); chart_df["Game Number"] = range(1, len(chart_df)+1)
                st.plotly_chart(px.line(chart_df, x="Game Number", y=stat, markers=True, title=f"{selected_player} {stat} — Playoffs"), use_container_width=True)

elif page == "Legacy Tracker":
    render_matchup_header(favorite_team, first_round=False)
    selected_player = st.selectbox("Choose starter", profile["starters"])
    st.subheader(f"{selected_player} Legacy Tracker")
    points = st.slider("Playoff scoring average", 0, 45, 20)
    rebounds = st.slider("Playoff rebounding average", 0, 20, 6)
    assists = st.slider("Playoff assists average", 0, 15, 4)
    series_wins = st.slider("Series wins this run", 0, 4, 1 if profile["status"] == "Active" else 0)
    score = min(100, round(50 + points*.5 + rebounds*.6 + assists*.5 + series_wins*10, 1))
    st.metric("Legacy Impact Score", score)
    legacy_df = pd.DataFrame({"Outcome":["Current", "Win Second Round", "Reach Conference Finals", "Reach NBA Finals", "Win Championship"], "Legacy Score":[50,65,78,90,100]})
    st.plotly_chart(px.bar(legacy_df, x="Outcome", y="Legacy Score", title=f"{selected_player} Legacy Path"), use_container_width=True)

elif page == "Matchup Lineups":
    render_matchup_header(favorite_team, first_round=False)
    if profile["status"] != "Active":
        st.warning("This team is eliminated, so current matchup lineups are not active.")
    else:
        opponent = profile["current_opponent"]
        opp_profile = TEAM_PROFILES[opponent]
        rows = []
        for i, pos in enumerate(["PG", "SG", "SF", "PF", "C"]):
            rows.append({"Position": pos, favorite_team: profile["starters"][i], opponent: opp_profile["starters"][i], "Advantage": "Depends on health, matchup, and game plan"})
        st.subheader("Projected Starters")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        bench_rows = [{"Team": favorite_team, "Player": p} for p in profile["subs"]]
        bench_rows += [{"Team": opponent, "Player": p} for p in opp_profile["subs"]]
        st.subheader("Main Subs")
        st.dataframe(pd.DataFrame(bench_rows), use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | Fixed Streamlit output | Live shot chart: Blue O = make, Red X = miss")
