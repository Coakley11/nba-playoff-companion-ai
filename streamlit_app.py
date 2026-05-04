
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

try:
    from nba_api.live.nba.endpoints import scoreboard, boxscore
    NBA_LIVE_AVAILABLE = True
except Exception:
    NBA_LIVE_AVAILABLE = False

try:
    from nba_api.stats.static import players as nba_players
    from nba_api.stats.endpoints import playergamelog
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

st.set_page_config(
    page_title="Daniel Cohen — NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("Final production-style version: dynamic bracket, live game center, first-round review, player tracker, and team pages.")

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
    "Detroit Pistons": {"seed":1,"conference":"East","status":"Active","round":"Second Round","current_opponent":"Cleveland Cavaliers","first_round_opponent":"Orlando Magic","first_round_result":"Defeated Orlando Magic, 4-3","starters":["Cade Cunningham","Jaden Ivey","Ausar Thompson","Tobias Harris","Jalen Duren"],"subs":["Marcus Sasser","Isaiah Stewart","Simone Fontecchio","Malik Beasley","Ron Holland"],"strengths":["Cade Cunningham's creation","young athleticism","rebounding","transition pressure"],"concerns":["playoff inexperience","half-court scoring droughts","late-game execution"]},
    "Orlando Magic": {"seed":8,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Detroit Pistons","first_round_result":"Lost to Detroit Pistons, 4-3","starters":["Jalen Suggs","Kentavious Caldwell-Pope","Franz Wagner","Paolo Banchero","Wendell Carter Jr."],"subs":["Cole Anthony","Jonathan Isaac","Anthony Black","Moritz Wagner","Gary Harris"],"strengths":["defense","size","young star forwards"],"concerns":["shooting","late-game offense","spacing"]},
    "Cleveland Cavaliers": {"seed":4,"conference":"East","status":"Active","round":"Second Round","current_opponent":"Detroit Pistons","first_round_opponent":"Toronto Raptors","first_round_result":"Defeated Toronto Raptors, 4-3","starters":["Darius Garland","Donovan Mitchell","Max Strus","Evan Mobley","Jarrett Allen"],"subs":["Caris LeVert","Isaac Okoro","Georges Niang","Sam Merrill","Dean Wade"],"strengths":["guard scoring","rim protection","defensive size"],"concerns":["offensive droughts","health","turnovers"]},
    "Toronto Raptors": {"seed":5,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Cleveland Cavaliers","first_round_result":"Lost to Cleveland Cavaliers, 4-3","starters":["Immanuel Quickley","RJ Barrett","Gradey Dick","Scottie Barnes","Jakob Poeltl"],"subs":["Bruce Brown","Kelly Olynyk","Ochai Agbaji","Chris Boucher","Davion Mitchell"],"strengths":["length","transition play","Scottie Barnes' versatility"],"concerns":["half-court scoring","shooting consistency","late-game creation"]},
    "New York Knicks": {"seed":3,"conference":"East","status":"Active","round":"Second Round","current_opponent":"Philadelphia 76ers","first_round_opponent":"Atlanta Hawks","first_round_result":"Defeated Atlanta Hawks, 4-2","starters":["Jalen Brunson","Mikal Bridges","OG Anunoby","Josh Hart","Karl-Anthony Towns"],"subs":["Miles McBride","Mitchell Robinson","Jordan Clarkson","Landry Shamet","Jose Alvarado"],"strengths":["Brunson shot creation","rebounding","physical wing defense","home-court energy"],"concerns":["bench scoring consistency","foul trouble against Embiid","overreliance on Brunson late"]},
    "Atlanta Hawks": {"seed":6,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"New York Knicks","first_round_result":"Lost to New York Knicks, 4-2","starters":["Trae Young","Dyson Daniels","Zaccharie Risacher","Jalen Johnson","Onyeka Okongwu"],"subs":["Bogdan Bogdanovic","De'Andre Hunter","Clint Capela","Vit Krejci","Kobe Bufkin"],"strengths":["Trae Young's creation","pace","guard scoring"],"concerns":["defense","rebounding","physical matchups"]},
    "Boston Celtics": {"seed":2,"conference":"East","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Philadelphia 76ers","first_round_result":"Lost to Philadelphia 76ers, 4-3","starters":["Jrue Holiday","Derrick White","Jaylen Brown","Jayson Tatum","Kristaps Porzingis"],"subs":["Payton Pritchard","Sam Hauser","Al Horford","Luke Kornet","Neemias Queta"],"strengths":["wing scoring","spacing","playoff experience"],"concerns":["late-series execution","health","three-point variance"]},
    "Philadelphia 76ers": {"seed":7,"conference":"East","status":"Active","round":"Second Round","current_opponent":"New York Knicks","first_round_opponent":"Boston Celtics","first_round_result":"Defeated Boston Celtics, 4-3","starters":["Tyrese Maxey","VJ Edgecombe","Kelly Oubre Jr.","Paul George","Joel Embiid"],"subs":["Quentin Grimes","Andre Drummond","Kyle Lowry","Eric Gordon","Caleb Martin"],"strengths":["Embiid interior dominance","Maxey speed","free throw pressure"],"concerns":["Embiid health","depth","transition defense"]},
    "Oklahoma City Thunder": {"seed":1,"conference":"West","status":"Active","round":"Second Round","current_opponent":"Los Angeles Lakers","first_round_opponent":"Phoenix Suns","first_round_result":"Defeated Phoenix Suns, 4-0","starters":["Shai Gilgeous-Alexander","Lu Dort","Jalen Williams","Chet Holmgren","Isaiah Hartenstein"],"subs":["Cason Wallace","Aaron Wiggins","Isaiah Joe","Jaylin Williams","Kenrich Williams"],"strengths":["SGA creation","spacing","defensive length"],"concerns":["playoff physicality","Lakers size","late-game pressure"]},
    "Phoenix Suns": {"seed":8,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Oklahoma City Thunder","first_round_result":"Lost to Oklahoma City Thunder, 4-0","starters":["Devin Booker","Bradley Beal","Grayson Allen","Kevin Durant","Jusuf Nurkic"],"subs":["Royce O'Neale","Eric Gordon","Bol Bol","Drew Eubanks","Josh Okogie"],"strengths":["shot creation","veteran scoring","midrange offense"],"concerns":["depth","defense","age"]},
    "San Antonio Spurs": {"seed":2,"conference":"West","status":"Active","round":"Second Round","current_opponent":"Minnesota Timberwolves","first_round_opponent":"Portland Trail Blazers","first_round_result":"Defeated Portland Trail Blazers, 4-1","starters":["Stephon Castle","Devin Vassell","Keldon Johnson","Jeremy Sochan","Victor Wembanyama"],"subs":["Tre Jones","Julian Champagnie","Zach Collins","Malaki Branham","Blake Wesley"],"strengths":["Wembanyama two-way impact","length","rim protection"],"concerns":["playoff inexperience","turnovers","physicality"]},
    "Portland Trail Blazers": {"seed":7,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"San Antonio Spurs","first_round_result":"Lost to San Antonio Spurs, 4-1","starters":["Scoot Henderson","Anfernee Simons","Shaedon Sharpe","Jerami Grant","Deandre Ayton"],"subs":["Toumani Camara","Matisse Thybulle","Robert Williams III","Dalano Banton","Kris Murray"],"strengths":["young guards","athleticism","future upside"],"concerns":["defense","experience","consistency"]},
    "Denver Nuggets": {"seed":3,"conference":"West","status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":"Minnesota Timberwolves","first_round_result":"Lost to Minnesota Timberwolves, 4-2","starters":["Jamal Murray","Christian Braun","Michael Porter Jr.","Aaron Gordon","Nikola Jokic"],"subs":["Reggie Jackson","Peyton Watson","Zeke Nnaji","Julian Strawther","DeAndre Jordan"],"strengths":["Jokic offense","chemistry","half-court execution"],"concerns":["bench depth","athletic matchups","defensive speed"]},
    "Minnesota Timberwolves": {"seed":6,"conference":"West","status":"Active","round":"Second Round","current_opponent":"San Antonio Spurs","first_round_opponent":"Denver Nuggets","first_round_result":"Defeated Denver Nuggets, 4-2","starters":["Mike Conley","Anthony Edwards","Jaden McDaniels","Naz Reid","Rudy Gobert"],"subs":["Nickeil Alexander-Walker","Donte DiVincenzo","Rob Dillingham","Josh Minott","Luka Garza"],"strengths":["defense","size","Anthony Edwards scoring"],"concerns":["late-game offense","spacing","foul trouble"]},
    "Los Angeles Lakers": {"seed":4,"conference":"West","status":"Active","round":"Second Round","current_opponent":"Oklahoma City Thunder","first_round_opponent":"Houston Rockets","first_round_result":"Defeated Houston Rockets, 4-2","starters":["D'Angelo Russell","Austin Reaves","LeBron James","Rui Hachimura","Anthony Davis"],"subs":["Gabe Vincent","Jarred Vanderbilt","Max Christie","Christian Wood","Jaxson Hayes"],"strengths":["star experience","rim pressure","Anthony Davis defense"],"concerns":["transition defense","age","three-point consistency"]},
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
    "DET-CLE": {"conf":"East","a":"Detroit Pistons","b":"Cleveland Cavaliers","a_wins":0,"b_wins":0,"winner":None},
    "NYK-PHI": {"conf":"East","a":"New York Knicks","b":"Philadelphia 76ers","a_wins":0,"b_wins":0,"winner":None},
    "OKC-LAL": {"conf":"West","a":"Oklahoma City Thunder","b":"Los Angeles Lakers","a_wins":0,"b_wins":0,"winner":None},
    "SAS-MIN": {"conf":"West","a":"San Antonio Spurs","b":"Minnesota Timberwolves","a_wins":0,"b_wins":0,"winner":None},
}

FIRST_ROUND_GAME_SCORES = {
    "New York Knicks": [
        {"Game":1,"Date":"Apr 19","Matchup":"Hawks at Knicks","Score":"Knicks 113, Hawks 102","Winner":"New York Knicks"},
        {"Game":2,"Date":"Apr 22","Matchup":"Hawks at Knicks","Score":"Hawks 107, Knicks 106","Winner":"Atlanta Hawks"},
        {"Game":3,"Date":"Apr 25","Matchup":"Knicks at Hawks","Score":"Hawks 109, Knicks 108","Winner":"Atlanta Hawks"},
        {"Game":4,"Date":"Apr 27","Matchup":"Knicks at Hawks","Score":"Knicks 114, Hawks 98","Winner":"New York Knicks"},
        {"Game":5,"Date":"Apr 29","Matchup":"Hawks at Knicks","Score":"Knicks 126, Hawks 97","Winner":"New York Knicks"},
        {"Game":6,"Date":"May 1","Matchup":"Knicks at Hawks","Score":"Knicks 140, Hawks 89","Winner":"New York Knicks"},
    ],
    "Atlanta Hawks": [
        {"Game":1,"Date":"Apr 19","Matchup":"Hawks at Knicks","Score":"Knicks 113, Hawks 102","Winner":"New York Knicks"},
        {"Game":2,"Date":"Apr 22","Matchup":"Hawks at Knicks","Score":"Hawks 107, Knicks 106","Winner":"Atlanta Hawks"},
        {"Game":3,"Date":"Apr 25","Matchup":"Knicks at Hawks","Score":"Hawks 109, Knicks 108","Winner":"Atlanta Hawks"},
        {"Game":4,"Date":"Apr 27","Matchup":"Knicks at Hawks","Score":"Knicks 114, Hawks 98","Winner":"New York Knicks"},
        {"Game":5,"Date":"Apr 29","Matchup":"Hawks at Knicks","Score":"Knicks 126, Hawks 97","Winner":"New York Knicks"},
        {"Game":6,"Date":"May 1","Matchup":"Knicks at Hawks","Score":"Knicks 140, Hawks 89","Winner":"New York Knicks"},
    ],
}

SERIES_SCHEDULES = {
    "NYK-PHI": [
        {"Game":"Game 1","Date":"May 4","Time":"8:00 PM ET","Matchup":"76ers at Knicks","TV":"NBC / Peacock"},
        {"Game":"Game 2","Date":"May 6","Time":"7:00 PM ET","Matchup":"76ers at Knicks","TV":"ESPN"},
        {"Game":"Game 3","Date":"May 8","Time":"7:00 PM ET","Matchup":"Knicks at 76ers","TV":"Prime Video"},
        {"Game":"Game 4","Date":"May 10","Time":"3:30 PM ET","Matchup":"Knicks at 76ers","TV":"ABC"},
    ],
}

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

def calc_live_win_prob(margin, period, is_home):
    period = max(1, min(int(period or 1), 4))
    weight = {1:1.2, 2:1.8, 3:2.7, 4:4.2}.get(period, 4.2)
    raw = 50 + margin * weight + (2.5 if is_home else 0)
    return int(max(1, min(99, round(raw))))

def positive_live_read(team_name, margin, prob, period):
    p = TEAM_PROFILES[team_name]
    if margin >= 10:
        return f"{team_name} is in a very strong position. A double-digit lead suggests control of pace, shot quality, and scoreboard pressure. The key is avoiding turnovers and protecting the glass."
    if margin >= 4:
        return f"{team_name} has the edge. The lead is not safe, but playoff games often tighten late, so this is a good position if they keep using {p['strengths'][0]}."
    if margin >= 0:
        return f"{team_name} is slightly ahead or tied. The next stretch matters. Good signs would be clean possessions, strong rebounding, and forcing difficult half-court shots."
    if margin >= -8:
        return f"{team_name} is behind, but this is manageable. One defensive stretch or one star-player scoring run can flip the game quickly."
    return f"{team_name} is in a tough spot, but the comeback path is clear: get stops, reduce empty possessions, and cut the lead before the next quarter break."

def team_logo_html(team, size=28):
    return f"<img src='{TEAM_LOGOS[team]}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"

def render_matchup_header(team_name, use_first_round=False):
    p = TEAM_PROFILES[team_name]
    opponent = p["first_round_opponent"] if use_first_round else (p.get("current_opponent") or p["first_round_opponent"])
    label = "First Round Review" if use_first_round else p["round"]
    c1, c2, c3 = st.columns([1,2.2,1])
    with c1:
        st.image(TEAM_LOGOS[team_name], width=115)
    with c2:
        st.markdown(
            f"<div style='text-align:center;'><h1>({p['seed']}) {team_name} vs ({TEAM_PROFILES[opponent]['seed']}) {opponent}</h1><h3>{label}</h3></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.image(TEAM_LOGOS[opponent], width=115)

def series_card_html(series, round_name):
    a,b = series["a"], series["b"]
    aw,bw = series["a_wins"], series["b_wins"]
    winner = series.get("winner")
    a_style = "font-weight:900;color:white;" if winner == a else "color:#cbd5e1;"
    b_style = "font-weight:900;color:white;" if winner == b else "color:#cbd5e1;"
    note = "Final" if winner else "In progress"
    return f"""
    <div class='series-card'>
      <div class='team-row' style='{a_style}'><span>{team_logo_html(a)} <b>{TEAM_PROFILES[a]['seed']}</b> {a}</span><span class='wins'>{aw}</span></div>
      <div class='team-row' style='{b_style}'><span>{team_logo_html(b)} <b>{TEAM_PROFILES[b]['seed']}</b> {b}</span><span class='wins'>{bw}</span></div>
      <div class='series-note'>{round_name} · {note}</div>
    </div>
    """

def render_dynamic_bracket():
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="bracket_refresh")
    st.markdown("""
    <style>
    .bracket-wrap{background:linear-gradient(135deg,#07111f,#101d35,#2c174a);padding:22px;border-radius:22px;border:1px solid rgba(255,255,255,.16);box-shadow:0 0 30px rgba(0,0,0,.35);color:white;}
    .bracket-title{text-align:center;font-size:34px;font-weight:900;margin-bottom:8px;letter-spacing:.5px;}
    .bracket-subtitle{text-align:center;color:#cbd5e1;margin-bottom:20px;}
    .bracket-grid{display:grid;grid-template-columns:1.25fr 1fr .85fr 1fr 1.25fr;gap:14px;align-items:center;}
    .conf-title{text-align:center;font-size:22px;font-weight:900;padding:8px;background:rgba(255,255,255,.08);border-radius:14px;margin-bottom:10px;}
    .round-title{text-align:center;font-size:15px;font-weight:800;color:#93c5fd;margin-bottom:8px;}
    .series-card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:10px 12px;margin:9px 0;min-height:82px;}
    .team-row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:3px 0;font-size:14px;}
    .wins{font-weight:900;font-size:18px;color:#fbbf24;}
    .series-note{font-size:12px;color:#93c5fd;margin-top:5px;text-align:center;}
    .finals-box{background:radial-gradient(circle at top,#fbbf24,#1f2937 45%,#111827);border:1px solid rgba(255,255,255,.18);border-radius:22px;padding:22px 10px;text-align:center;}
    .finals-title{font-size:22px;font-weight:900;margin-bottom:8px;}
    .trophy{font-size:54px;margin:10px 0;}
    </style>
    """, unsafe_allow_html=True)
    east_fr = [s for s in FIRST_ROUND_SERIES.values() if s["conf"] == "East"]
    west_fr = [s for s in FIRST_ROUND_SERIES.values() if s["conf"] == "West"]
    east_sr = [s for s in SECOND_ROUND_SERIES.values() if s["conf"] == "East"]
    west_sr = [s for s in SECOND_ROUND_SERIES.values() if s["conf"] == "West"]
    html = f"""
    <div class='bracket-wrap'>
      <div class='bracket-title'>2026 NBA PLAYOFF BRACKET</div>
      <div class='bracket-subtitle'>Dynamic bracket style · updates every 30 seconds where live data is available</div>
      <div class='bracket-grid'>
        <div><div class='conf-title'>Eastern Conference</div><div class='round-title'>First Round</div>{''.join(series_card_html(s, "First Round") for s in east_fr)}</div>
        <div><div class='round-title'>Second Round</div>{''.join(series_card_html(s, "Second Round") for s in east_sr)}</div>
        <div class='finals-box'><div class='finals-title'>Conference Finals</div><div>East Winner</div><div class='trophy'>🏆</div><div>West Winner</div><hr><div class='finals-title'>NBA Finals</div><div style='font-size:12px;'>Winner appears here after conference finals</div></div>
        <div><div class='round-title'>Second Round</div>{''.join(series_card_html(s, "Second Round") for s in west_sr)}</div>
        <div><div class='conf-title'>Western Conference</div><div class='round-title'>First Round</div>{''.join(series_card_html(s, "First Round") for s in west_fr)}</div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

favorite_team = st.sidebar.selectbox("Choose your playoff team", list(TEAM_PROFILES.keys()), index=list(TEAM_PROFILES.keys()).index("New York Knicks"))
page = st.sidebar.radio("Choose page", ["Home Dashboard","Playoff Bracket","Current Series","First Round Review","Live Game Center","Player Playoff Tracker","Legacy Tracker","Matchup Lineups"])
profile = TEAM_PROFILES[favorite_team]

if page == "Home Dashboard":
    render_matchup_header(favorite_team, use_first_round=False)
    c1,c2,c3 = st.columns(3)
    c1.metric("Status", profile["status"])
    c2.metric("Round", profile["round"])
    c3.metric("Seed", profile["seed"])
    if profile["status"] == "Active":
        st.success(f"{favorite_team} is still alive. Current opponent: {profile['current_opponent']}.")
        st.subheader("Strengths")
        for s in profile["strengths"]: st.write(f"• {s}")
        st.subheader("Concerns")
        for c in profile["concerns"]: st.write(f"• {c}")
    else:
        st.error(profile["first_round_result"])
        st.write("Next-season focus: improve the areas that ended the playoff run and build more reliable playoff options.")

elif page == "Playoff Bracket":
    render_dynamic_bracket()

elif page == "Current Series":
    if profile["status"] == "Active":
        render_matchup_header(favorite_team, use_first_round=False)
        st.subheader("Current Series Preview")
        st.write(f"{favorite_team} vs {profile['current_opponent']}")
        key = next((k for k,s in SECOND_ROUND_SERIES.items() if favorite_team in [s["a"],s["b"]]), None)
        if key in SERIES_SCHEDULES:
            st.subheader("Series Schedule")
            st.dataframe(pd.DataFrame(SERIES_SCHEDULES[key]), use_container_width=True)
        st.subheader("What has to go right")
        for s in profile["strengths"]: st.success(s)
        st.subheader("Main things to watch")
        for c in profile["concerns"]: st.warning(c)
    else:
        st.warning("This team is eliminated. Current Series is now a recap page.")
        st.write(profile["first_round_result"])

elif page == "First Round Review":
    render_matchup_header(favorite_team, use_first_round=True)
    st.subheader("First Round Matchup Only")
    st.info(profile["first_round_result"])
    st.subheader("Game-by-game scores")
    scores = FIRST_ROUND_GAME_SCORES.get(favorite_team, [])
    if scores:
        st.dataframe(pd.DataFrame(scores), use_container_width=True)
    else:
        st.warning("Fallback game-by-game scores are not fully loaded for this matchup yet. This page still shows only the first-round matchup, not the second-round matchup.")
    st.subheader("Series review")
    if profile["status"] == "Eliminated":
        st.write(f"{favorite_team} showed some useful playoff pieces, but the series exposed: {', '.join(profile['concerns'])}.")
        st.write("Next season, the focus should be improving the weakest playoff areas and building more reliable late-game options.")
    else:
        st.write(f"{favorite_team} advanced because its strengths showed up: {', '.join(profile['strengths'])}.")

elif page == "Live Game Center":
    render_matchup_header(favorite_team, use_first_round=False)
    st.subheader("Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_game_center_refresh")
        st.caption("Refreshing every 30 seconds.")
    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live data is not available. Make sure nba_api is in requirements.txt.")
    else:
        game = find_live_game_for_team(favorite_team)
        if not game:
            st.warning("No live or scheduled game found for this team right now.")
        else:
            home, away = game.get("homeTeam", {}), game.get("awayTeam", {})
            home_score, away_score = int(home.get("score",0) or 0), int(away.get("score",0) or 0)
            home_tri, away_tri = home.get("teamTricode"), away.get("teamTricode")
            st.write(f"### {away.get('teamName','Away')} at {home.get('teamName','Home')}")
            st.write(f"**Status:** {game.get('gameStatusText','Unknown')} | **Period:** {game.get('period',1)} | **Clock:** {game.get('gameClock','')}")
            c1,c2 = st.columns(2)
            c1.metric(away.get("teamName","Away"), away_score)
            c2.metric(home.get("teamName","Home"), home_score)
            alias = TEAM_ALIASES[favorite_team]
            is_home = home_tri == alias
            team_score = home_score if is_home else away_score
            opp_score = away_score if is_home else home_score
            margin = team_score - opp_score
            period = int(game.get("period",1) or 1)
            prob = calc_live_win_prob(margin, period, is_home)
            c1,c2,c3 = st.columns(3)
            c1.metric(f"{favorite_team} Win Probability", f"{prob}%")
            c2.metric("Score Margin", margin)
            c3.metric("Home Game", "Yes" if is_home else "No")
            st.plotly_chart(px.pie(pd.DataFrame({"Outcome":[f"{favorite_team} wins","Opponent wins"],"Probability":[prob,100-prob]}), names="Outcome", values="Probability", title="Live Win Probability"), use_container_width=True)
            st.subheader("Live Read")
            st.info(positive_live_read(favorite_team, margin, prob, period))
            bs = get_live_boxscore(game.get("gameId"))
            if bs:
                rows = []
                for side in ["homeTeam","awayTeam"]:
                    t = bs.get(side,{})
                    tri = t.get("teamTricode","")
                    for p in t.get("players",[]):
                        stats = p.get("statistics",{})
                        rows.append({"Team":tri,"Player":p.get("name",""),"MIN":stats.get("minutes",""),"PTS":stats.get("points",0),"REB":stats.get("reboundsTotal",0),"AST":stats.get("assists",0),"STL":stats.get("steals",0),"BLK":stats.get("blocks",0),"TO":stats.get("turnovers",0),"+/-":stats.get("plusMinusPoints",0)})
                if rows:
                    st.subheader("Live Player Box Score")
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)

elif page == "Player Playoff Tracker":
    render_matchup_header(favorite_team, use_first_round=False)
    players = profile["starters"] + profile["subs"]
    selected_player = st.selectbox("Choose player", players)
    season = st.selectbox("Season", ["2025-26","2024-25","2023-24"], index=0)
    if not NBA_STATS_AVAILABLE:
        st.error("nba_api stats tools are unavailable.")
    else:
        @st.cache_data(ttl=3600)
        def get_player_id(name):
            matches = [p for p in nba_players.get_players() if p["full_name"] == name]
            return matches[0]["id"] if matches else None
        @st.cache_data(ttl=900)
        def get_logs(pid, season_val):
            try:
                return playergamelog.PlayerGameLog(player_id=pid, season=season_val, season_type_all_star="Playoffs").get_data_frames()[0]
            except Exception:
                return pd.DataFrame()
        pid = get_player_id(selected_player)
        if pid is None:
            st.warning(f"Could not find NBA player ID for {selected_player}.")
        else:
            logs = get_logs(pid, season)
            if logs.empty:
                st.warning(f"No playoff logs found yet for {selected_player} in {season}.")
            else:
                cols = [c for c in ["GAME_DATE","MATCHUP","WL","MIN","PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","FT_PCT","PLUS_MINUS"] if c in logs.columns]
                st.dataframe(logs[cols], use_container_width=True)
                stat = st.selectbox("Choose stat", [c for c in ["PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","PLUS_MINUS","MIN"] if c in logs.columns])
                chart_df = logs.copy()
                chart_df["Game Number"] = range(1, len(chart_df)+1)
                st.plotly_chart(px.line(chart_df, x="Game Number", y=stat, markers=True, title=f"{selected_player} {stat} — Playoffs"), use_container_width=True)
                st.write(f"{selected_player}'s {stat} trend helps show his playoff impact. Strong production, efficient shooting, low turnovers, and positive plus/minus are strong signs.")

elif page == "Legacy Tracker":
    render_matchup_header(favorite_team, use_first_round=False)
    selected_player = st.selectbox("Choose starter", profile["starters"])
    st.subheader(f"{selected_player} Legacy Tracker")
    points = st.slider("Playoff scoring average", 0, 45, 20)
    rebounds = st.slider("Playoff rebounding average", 0, 20, 6)
    assists = st.slider("Playoff assists average", 0, 15, 4)
    series_wins = st.slider("Series wins this run", 0, 4, 1 if profile["status"] == "Active" else 0)
    score = min(100, round(50 + points*.5 + rebounds*.6 + assists*.5 + series_wins*10, 1))
    st.metric("Legacy Impact Score", score)
    outcomes = pd.DataFrame({"Outcome":["Current","Win Second Round","Reach Conference Finals","Reach NBA Finals","Win Championship"],"Legacy Score":[50,65,78,90,100]})
    st.plotly_chart(px.bar(outcomes, x="Outcome", y="Legacy Score", title=f"{selected_player} Legacy Path"), use_container_width=True)

elif page == "Matchup Lineups":
    render_matchup_header(favorite_team, use_first_round=False)
    if profile["status"] != "Active":
        st.warning("This team is eliminated, so current matchup lineups are not active.")
    else:
        opponent = profile["current_opponent"]
        opp = TEAM_PROFILES[opponent]
        positions = ["PG","SG","SF","PF","C"]
        rows = [{"Position":pos, favorite_team: profile["starters"][i], opponent: opp["starters"][i], "Advantage":"Depends on matchup"} for i,pos in enumerate(positions)]
        st.subheader("Projected Starters")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        bench = [{"Team":favorite_team,"Player":p} for p in profile["subs"]] + [{"Team":opponent,"Player":p} for p in opp["subs"]]
        st.subheader("Main Bench / Subs")
        st.dataframe(pd.DataFrame(bench), use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | Dynamic bracket + live data where available")
