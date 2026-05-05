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
    from nba_api.stats.endpoints import playergamelog
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

st.set_page_config(page_title="Daniel Cohen — NBA Playoff Companion AI", page_icon="🏀", layout="wide")
st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 playoff companion app with advanced live game center, dynamic bracket, player tracker, and AI analysis")

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
    "New York Knicks": {"seed": 3, "conference": "East", "status": "Active", "round": "Second Round", "current_opponent": "Philadelphia 76ers", "first_round_opponent": "Atlanta Hawks", "first_round_result": "Defeated Atlanta Hawks, 4-2", "starters": ["Jalen Brunson", "Mikal Bridges", "OG Anunoby", "Josh Hart", "Karl-Anthony Towns"], "subs": ["Miles McBride", "Mitchell Robinson", "Jordan Clarkson", "Landry Shamet", "Jose Alvarado"], "strengths": ["Brunson shot creation", "rebounding", "physical wing defense", "home-court energy"], "concerns": ["bench scoring consistency", "foul trouble", "overreliance on Brunson late"]},
    "Philadelphia 76ers": {"seed": 7, "conference": "East", "status": "Active", "round": "Second Round", "current_opponent": "New York Knicks", "first_round_opponent": "Boston Celtics", "first_round_result": "Defeated Boston Celtics, 4-3", "starters": ["Tyrese Maxey", "VJ Edgecombe", "Kelly Oubre Jr.", "Paul George", "Joel Embiid"], "subs": ["Quentin Grimes", "Andre Drummond", "Kyle Lowry", "Eric Gordon", "Caleb Martin"], "strengths": ["Embiid interior pressure", "Maxey speed", "free-throw pressure", "star scoring"], "concerns": ["Embiid health", "transition defense", "depth", "turnovers"]},
    "Detroit Pistons": {"seed": 1, "conference": "East", "status": "Active", "round": "Second Round", "current_opponent": "Cleveland Cavaliers", "first_round_opponent": "Orlando Magic", "first_round_result": "Defeated Orlando Magic, 4-3", "starters": ["Cade Cunningham", "Jaden Ivey", "Ausar Thompson", "Tobias Harris", "Jalen Duren"], "subs": ["Marcus Sasser", "Isaiah Stewart", "Simone Fontecchio", "Malik Beasley", "Ron Holland"], "strengths": ["Cade Cunningham creation", "rebounding", "young athleticism", "transition pressure"], "concerns": ["playoff inexperience", "late-game execution", "half-court droughts"]},
    "Cleveland Cavaliers": {"seed": 4, "conference": "East", "status": "Active", "round": "Second Round", "current_opponent": "Detroit Pistons", "first_round_opponent": "Toronto Raptors", "first_round_result": "Defeated Toronto Raptors, 4-3", "starters": ["Darius Garland", "Donovan Mitchell", "Max Strus", "Evan Mobley", "Jarrett Allen"], "subs": ["Caris LeVert", "Isaac Okoro", "Georges Niang", "Sam Merrill", "Dean Wade"], "strengths": ["guard scoring", "rim protection", "defensive size", "Mitchell shot creation"], "concerns": ["offensive droughts", "health", "turnovers under pressure"]},
    "Oklahoma City Thunder": {"seed": 1, "conference": "West", "status": "Active", "round": "Second Round", "current_opponent": "Los Angeles Lakers", "first_round_opponent": "Phoenix Suns", "first_round_result": "Defeated Phoenix Suns, 4-0", "starters": ["Shai Gilgeous-Alexander", "Lu Dort", "Jalen Williams", "Chet Holmgren", "Isaiah Hartenstein"], "subs": ["Cason Wallace", "Aaron Wiggins", "Isaiah Joe", "Jaylin Williams", "Kenrich Williams"], "strengths": ["SGA creation", "spacing", "defensive length", "pace"], "concerns": ["playoff physicality", "Lakers size", "late-game pressure"]},
    "Los Angeles Lakers": {"seed": 4, "conference": "West", "status": "Active", "round": "Second Round", "current_opponent": "Oklahoma City Thunder", "first_round_opponent": "Houston Rockets", "first_round_result": "Defeated Houston Rockets, 4-2", "starters": ["D'Angelo Russell", "Austin Reaves", "LeBron James", "Rui Hachimura", "Anthony Davis"], "subs": ["Gabe Vincent", "Jarred Vanderbilt", "Max Christie", "Christian Wood", "Jaxson Hayes"], "strengths": ["star experience", "rim pressure", "Anthony Davis defense", "LeBron control"], "concerns": ["transition defense", "age", "three-point consistency"]},
    "San Antonio Spurs": {"seed": 2, "conference": "West", "status": "Active", "round": "Second Round", "current_opponent": "Minnesota Timberwolves", "first_round_opponent": "Portland Trail Blazers", "first_round_result": "Defeated Portland Trail Blazers, 4-1", "starters": ["Stephon Castle", "Devin Vassell", "Keldon Johnson", "Jeremy Sochan", "Victor Wembanyama"], "subs": ["Tre Jones", "Julian Champagnie", "Zach Collins", "Malaki Branham", "Blake Wesley"], "strengths": ["Wembanyama two-way impact", "length", "rim protection", "young talent"], "concerns": ["playoff inexperience", "turnovers", "physicality"]},
    "Minnesota Timberwolves": {"seed": 6, "conference": "West", "status": "Active", "round": "Second Round", "current_opponent": "San Antonio Spurs", "first_round_opponent": "Denver Nuggets", "first_round_result": "Defeated Denver Nuggets, 4-2", "starters": ["Mike Conley", "Anthony Edwards", "Jaden McDaniels", "Naz Reid", "Rudy Gobert"], "subs": ["Nickeil Alexander-Walker", "Donte DiVincenzo", "Rob Dillingham", "Josh Minott", "Luka Garza"], "strengths": ["defense", "size", "Anthony Edwards scoring", "physicality"], "concerns": ["late-game offense", "spacing", "foul trouble"]},
}
# Add eliminated teams compactly
for name, seed, conf, opp, result in [
    ("Atlanta Hawks",6,"East","New York Knicks","Lost to New York Knicks, 4-2"), ("Boston Celtics",2,"East","Philadelphia 76ers","Lost to Philadelphia 76ers, 4-3"),
    ("Orlando Magic",8,"East","Detroit Pistons","Lost to Detroit Pistons, 4-3"), ("Toronto Raptors",5,"East","Cleveland Cavaliers","Lost to Cleveland Cavaliers, 4-3"),
    ("Phoenix Suns",8,"West","Oklahoma City Thunder","Lost to Oklahoma City Thunder, 4-0"), ("Portland Trail Blazers",7,"West","San Antonio Spurs","Lost to San Antonio Spurs, 4-1"),
    ("Denver Nuggets",3,"West","Minnesota Timberwolves","Lost to Minnesota Timberwolves, 4-2"), ("Houston Rockets",5,"West","Los Angeles Lakers","Lost to Los Angeles Lakers, 4-2")]:
    TEAM_PROFILES[name] = {"seed": seed, "conference": conf, "status":"Eliminated", "round":"Lost First Round", "current_opponent": None, "first_round_opponent": opp, "first_round_result": result, "starters": ["Starter 1","Starter 2","Starter 3","Starter 4","Starter 5"], "subs": ["Sub 1","Sub 2","Sub 3","Sub 4","Sub 5"], "strengths":["competitive playoff moments","individual talent","areas to build on"], "concerns":["series consistency","defensive execution","late-game scoring"]}

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

@st.cache_data(ttl=30)
def get_live_games():
    if not NBA_LIVE_AVAILABLE: return []
    try: return scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", [])
    except Exception: return []

def find_live_game_for_team(team_name):
    alias = TEAM_ALIASES.get(team_name)
    for game in get_live_games():
        h, a = game.get("homeTeam", {}), game.get("awayTeam", {})
        if h.get("teamTricode") == alias or a.get("teamTricode") == alias: return game
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

def safe_int(x, default=0):
    try: return int(x or default)
    except Exception: return default

def safe_float(x, default=0.0):
    try: return float(x or default)
    except Exception: return default

def calc_win_probability(margin, period, is_home):
    period = max(1, min(safe_int(period, 1), 4))
    raw = 50 + margin * {1:1.2,2:1.8,3:2.8,4:4.5}.get(period,4.5) + (2.5 if is_home else 0)
    return int(max(1, min(99, round(raw))))

def create_boxscore_dataframe(game_box):
    rows=[]
    for side in ["homeTeam","awayTeam"]:
        t=game_box.get(side,{})
        tri=t.get("teamTricode","")
        for p in t.get("players",[]):
            s=p.get("statistics",{})
            rows.append({"Team":tri,"Player":p.get("name",""),"MIN":s.get("minutes",""),"PTS":s.get("points",0),"REB":s.get("reboundsTotal",0),"AST":s.get("assists",0),"STL":s.get("steals",0),"BLK":s.get("blocks",0),"TO":s.get("turnovers",0),"PF":s.get("foulsPersonal",0),"FGM":s.get("fieldGoalsMade",0),"FGA":s.get("fieldGoalsAttempted",0),"3PM":s.get("threePointersMade",0),"3PA":s.get("threePointersAttempted",0),"FTM":s.get("freeThrowsMade",0),"FTA":s.get("freeThrowsAttempted",0),"+/-":s.get("plusMinusPoints",0)})
    return pd.DataFrame(rows)

def impact_score(row):
    return safe_float(row.get("PTS"))+1.2*safe_float(row.get("REB"))+1.5*safe_float(row.get("AST"))+3*safe_float(row.get("STL"))+3*safe_float(row.get("BLK"))+0.35*safe_float(row.get("+/-"))-1.2*safe_float(row.get("TO"))

def choose_team_mvp(box_df, team_alias):
    t=box_df[box_df["Team"]==team_alias].copy()
    if t.empty: return None
    t["Impact Score"]=t.apply(impact_score,axis=1)
    return t.sort_values("Impact Score",ascending=False).iloc[0]

def estimate_current_lineup(box_df, team_alias):
    t=box_df[box_df["Team"]==team_alias].copy()
    if t.empty: return pd.DataFrame()
    def mf(v):
        try:
            if isinstance(v,str) and ":" in v:
                m,s=v.split(":"); return float(m)+float(s)/60
            return float(v)
        except Exception: return 0
    t["MIN_FLOAT"]=t["MIN"].apply(mf)
    return t.sort_values("MIN_FLOAT",ascending=False).head(5)

def what_next(team_name, margin, period):
    p=TEAM_PROFILES[team_name]
    if margin>=8: return ["Protect the ball.","Keep the opponent off the offensive glass.",f"Keep leaning on {p['strengths'][0]}."]
    if margin>=0: return ["Win the next three-minute stretch.","Get a clean look for the main scorer.","Defend without fouling."]
    return ["Create a quick 6-0 run.","Increase defensive pressure without over-fouling.",f"Fix the danger area: {p['concerns'][0]}."]

def what_if_simulator(margin, period, is_home):
    return pd.DataFrame([{"Scenario":f"{'+' if sw>=0 else ''}{sw} point swing","New Margin":margin+sw,"Projected Win Probability":f"{calc_win_probability(margin+sw,period,is_home)}%"} for sw in [10,5,0,-5,-10]])

def create_synthetic_shot_chart(actions, team_alias):
    rows=[]; rng=np.random.default_rng(8)
    for a in actions:
        tri=a.get("teamTricode") or ""; desc=(a.get("description") or "").lower()
        if tri!=team_alias or not any(w in desc for w in ["miss","make","made","makes"]): continue
        made=any(w in desc for w in ["make","made","makes"]); is_three="3pt" in desc or "three" in desc
        if is_three: x=float(rng.uniform(-22,22)); y=float(rng.uniform(20,31))
        elif "dunk" in desc or "layup" in desc: x=float(rng.uniform(-5,5)); y=float(rng.uniform(0,8))
        else: x=float(rng.uniform(-15,15)); y=float(rng.uniform(8,20))
        rows.append({"Player":a.get("personName") or a.get("playerName") or "Unknown","x":x,"y":y,"Made":made,"Description":a.get("description","")})
    return pd.DataFrame(rows)

def draw_halfcourt_shot_chart(shots_df, title):
    fig=go.Figure()
    fig.add_shape(type="rect", x0=-25,y0=0,x1=25,y1=47,line=dict(width=2))
    fig.add_shape(type="circle", x0=-6,y0=-1,x1=6,y1=11,line=dict(width=2))
    fig.add_shape(type="rect", x0=-8,y0=0,x1=8,y1=19,line=dict(width=2))
    fig.add_shape(type="circle", x0=-23.75,y0=0,x1=23.75,y1=47.5,line=dict(width=2))
    fig.add_shape(type="line", x0=-22,y0=0,x1=-22,y1=14,line=dict(width=2)); fig.add_shape(type="line", x0=22,y0=0,x1=22,y1=14,line=dict(width=2))
    if not shots_df.empty:
        made=shots_df[shots_df["Made"]==True]; miss=shots_df[shots_df["Made"]==False]
        fig.add_trace(go.Scatter(x=made["x"],y=made["y"],mode="markers",marker=dict(size=11,symbol="circle"),name="Made",text=made["Description"]))
        fig.add_trace(go.Scatter(x=miss["x"],y=miss["y"],mode="markers",marker=dict(size=12,symbol="x"),name="Missed",text=miss["Description"]))
    fig.update_layout(title=title,xaxis=dict(range=[-27,27],visible=False),yaxis=dict(range=[0,50],visible=False),height=600,showlegend=True)
    return fig

def team_logo_html(team,size=28): return f"<img src='{TEAM_LOGOS[team]}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"
def render_matchup_header(team_name, first_round=False):
    p=TEAM_PROFILES[team_name]; opp=p["first_round_opponent"] if first_round else (p["current_opponent"] or p["first_round_opponent"])
    c1,c2,c3=st.columns([1,2.4,1])
    with c1: st.image(TEAM_LOGOS[team_name], width=110)
    with c2: st.markdown(f"<div style='text-align:center;'><h1>({p['seed']}) {team_name} vs ({TEAM_PROFILES[opp]['seed']}) {opp}</h1><h3>{'First Round Review' if first_round else p['round']}</h3></div>", unsafe_allow_html=True)
    with c3: st.image(TEAM_LOGOS[opp], width=110)

def series_card_html(s, round_name):
    a,b=s["a"],s["b"]; aw,bw=s["a_wins"],s["b_wins"]; w=s.get("winner")
    ac="winner" if w==a else "loser" if w==b else ""; bc="winner" if w==b else "loser" if w==a else ""
    return f"<div class='series-card'><div class='team-row {ac}'><div>{team_logo_html(a)}<b>{TEAM_PROFILES[a]['seed']}</b> {a}</div><div class='wins'>{aw}</div></div><div class='team-row {bc}'><div>{team_logo_html(b)}<b>{TEAM_PROFILES[b]['seed']}</b> {b}</div><div class='wins'>{bw}</div></div><div class='series-note'>{round_name} · {'Final' if w else 'In progress'}</div></div>"

def render_dynamic_bracket():
    if AUTOREFRESH_AVAILABLE: st_autorefresh(interval=30000,key="bracket_refresh")
    st.markdown("""
    <style>.bracket-wrap{background:linear-gradient(135deg,#07111f,#10213d,#301a55);padding:22px;border-radius:22px;color:white}.bracket-title{text-align:center;font-size:34px;font-weight:900}.bracket-sub{text-align:center;color:#cbd5e1;margin-bottom:20px}.bracket-grid{display:grid;grid-template-columns:1.25fr 1fr .85fr 1fr 1.25fr;gap:14px;align-items:center}.conf-title{text-align:center;font-size:22px;font-weight:900;padding:8px;background:rgba(255,255,255,.08);border-radius:14px;margin-bottom:10px}.round-title{text-align:center;font-size:15px;color:#93c5fd;font-weight:800;margin-bottom:8px}.series-card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:10px 12px;margin:9px 0}.team-row{display:flex;align-items:center;justify-content:space-between;padding:3px 0;font-size:14px}.wins{font-weight:900;font-size:17px;color:#fbbf24}.winner{color:#fff;font-weight:900}.loser{color:#cbd5e1}.series-note{text-align:center;color:#93c5fd;font-size:12px;margin-top:5px}.finals-box{background:radial-gradient(circle at top,#fbbf24,#1f2937 45%,#111827);border-radius:22px;padding:22px 10px;text-align:center}.trophy{font-size:54px}</style>
    """, unsafe_allow_html=True)
    ef=[s for s in FIRST_ROUND_SERIES.values() if s["conf"]=="East"]; wf=[s for s in FIRST_ROUND_SERIES.values() if s["conf"]=="West"]
    es=[s for s in SECOND_ROUND_SERIES.values() if s["conf"]=="East"]; ws=[s for s in SECOND_ROUND_SERIES.values() if s["conf"]=="West"]
    html=f"<div class='bracket-wrap'><div class='bracket-title'>2026 NBA PLAYOFF BRACKET</div><div class='bracket-sub'>Dynamic bracket view · refreshes every 30 seconds when enabled</div><div class='bracket-grid'><div><div class='conf-title'>Eastern Conference</div><div class='round-title'>First Round</div>{''.join(series_card_html(s,'First Round') for s in ef)}</div><div><div class='round-title'>Second Round</div>{''.join(series_card_html(s,'Second Round') for s in es)}</div><div class='finals-box'><h3>Conference Finals</h3><div class='trophy'>🏆</div><h3>NBA Finals</h3><p style='font-size:12px;color:#e5e7eb;'>Winners move here as series end</p></div><div><div class='round-title'>Second Round</div>{''.join(series_card_html(s,'Second Round') for s in ws)}</div><div><div class='conf-title'>Western Conference</div><div class='round-title'>First Round</div>{''.join(series_card_html(s,'First Round') for s in wf)}</div></div></div>"
    st.markdown(html, unsafe_allow_html=True)

favorite_team=st.sidebar.selectbox("Choose your playoff team", list(TEAM_PROFILES.keys()), index=list(TEAM_PROFILES.keys()).index("New York Knicks"))
profile=TEAM_PROFILES[favorite_team]
page=st.sidebar.radio("Choose page", ["Home Dashboard","Playoff Bracket","Current Series","First Round Review","Live Game Center","Player Playoff Tracker","Legacy Tracker","Matchup Lineups"])

if page=="Home Dashboard":
    render_matchup_header(favorite_team, False)
    c1,c2,c3=st.columns(3); c1.metric("Status",profile["status"]); c2.metric("Round",profile["round"]); c3.metric("Seed",profile["seed"])
    st.subheader("Team outlook")
    st.success(f"{favorite_team} is still alive. Current opponent: {profile['current_opponent']}.") if profile["status"]=="Active" else st.error(f"{favorite_team} has been eliminated. {profile['first_round_result']}")
    st.write("Strengths:"); [st.write(f"• {s}") for s in profile["strengths"]]
    st.write("Concerns:"); [st.write(f"• {c}") for c in profile["concerns"]]
elif page=="Playoff Bracket": render_dynamic_bracket()
elif page=="Current Series":
    if profile["status"]=="Active":
        render_matchup_header(favorite_team, False); st.subheader("Before the next game: what to look for")
        [st.success(s) for s in profile["strengths"]]; [st.warning(c) for c in profile["concerns"]]
    else: st.warning(profile["first_round_result"])
elif page=="First Round Review":
    render_matchup_header(favorite_team, True); st.info(profile["first_round_result"]); st.write("This page is only for the first-round matchup.")
elif page=="Live Game Center":
    render_matchup_header(favorite_team, False); st.subheader("Advanced Live Game Center")
    if AUTOREFRESH_AVAILABLE: st_autorefresh(interval=30000,key="live_game_refresh"); st.caption("Refreshing every 30 seconds.")
    else: st.warning("streamlit-autorefresh is not installed.")
    if not NBA_LIVE_AVAILABLE: st.error("nba_api live endpoints are unavailable. Check requirements.txt.")
    else:
        live_game=find_live_game_for_team(favorite_team)
        if not live_game: st.warning("No live or scheduled game found for this team right now.")
        else:
            home,away=live_game.get("homeTeam",{}),live_game.get("awayTeam",{})
            home_name,away_name=home.get("teamName","Home"),away.get("teamName","Away")
            home_tri,away_tri=home.get("teamTricode",""),away.get("teamTricode","")
            home_score,away_score=safe_int(home.get("score",0)),safe_int(away.get("score",0))
            period=safe_int(live_game.get("period",1),1); clock=live_game.get("gameClock",""); status_text=live_game.get("gameStatusText","Unknown"); game_id=live_game.get("gameId")
            st.write(f"### {away_name} at {home_name}"); st.write(f"**Status:** {status_text} | **Period:** {period} | **Clock:** {clock}")
            c1,c2=st.columns(2); c1.metric(away_name,away_score); c2.metric(home_name,home_score)
            alias=TEAM_ALIASES[favorite_team]; is_home=home_tri==alias; team_score=home_score if is_home else away_score; opp_score=away_score if is_home else home_score; margin=team_score-opp_score; prob=calc_win_probability(margin,period,is_home)
            p1,p2,p3=st.columns(3); p1.metric(f"{favorite_team} Win Probability", f"{prob}%"); p2.metric("Score Margin", margin); p3.metric("Home Game", "Yes" if is_home else "No")
            st.plotly_chart(px.pie(pd.DataFrame({"Outcome":[f"{favorite_team} wins","Opponent wins"],"Probability":[prob,100-prob]}), names="Outcome", values="Probability", title="Current Win Probability"), use_container_width=True)
            timeline=pd.DataFrame({"Game Segment":["Start","Q1","Q2","Q3","Now"],"Win Probability":[50,max(1,min(99,prob-12)),max(1,min(99,prob-7)),max(1,min(99,prob-3)),prob],"Margin":[0,margin-8,margin-5,margin-2,margin]})
            st.subheader("Win Probability Timeline"); st.plotly_chart(px.line(timeline,x="Game Segment",y="Win Probability",markers=True),use_container_width=True)
            st.subheader("Momentum Graph"); st.plotly_chart(px.line(timeline,x="Game Segment",y="Margin",markers=True,title="Score Margin Momentum"),use_container_width=True)
            box=get_live_boxscore(game_id); box_df=create_boxscore_dataframe(box) if box else pd.DataFrame()
            if not box_df.empty:
                st.subheader("Full Live Box Score"); st.dataframe(box_df,use_container_width=True)
                st.subheader("Player of the Game / Team MVP"); mvp=choose_team_mvp(box_df,alias)
                if mvp is not None: st.success(f"🔥 {mvp['Player']}"); st.write(f"{mvp['PTS']} points, {mvp['REB']} rebounds, {mvp['AST']} assists, {mvp['+/-']} plus/minus")
                st.subheader("Foul Trouble Tracker"); foul_df=box_df[box_df["PF"].astype(float)>=4]
                st.success("No major foul trouble detected.") if foul_df.empty else st.dataframe(foul_df[["Team","Player","PF","PTS","MIN"]],use_container_width=True)
                st.subheader("Live Lineup Tracker"); st.dataframe(estimate_current_lineup(box_df,alias)[["Team","Player","MIN","PTS","REB","AST","PF","+/-"]],use_container_width=True)
                st.subheader("Rotation Impact Tracker"); st.dataframe(box_df[box_df["Team"]==alias][["Player","MIN","+/-","PTS","REB","AST"]].sort_values("+/-",ascending=False),use_container_width=True)
            st.subheader("AI Game Narrator"); st.info(f"{favorite_team} is currently {'ahead' if margin>0 else 'tied' if margin==0 else 'behind'} by {abs(margin)}. The model gives them about {prob}% right now.")
            st.subheader("What Needs To Happen Next"); [st.write(f"• {x}") for x in what_next(favorite_team,margin,period)]
            st.subheader("What-If Simulator"); st.dataframe(what_if_simulator(margin,period,is_home),use_container_width=True)
            actions=get_live_playbyplay(game_id)
            if actions:
                st.subheader("Smart Play-by-Play Insights"); [st.write(f"• {a.get('description','')}") for a in actions[-12:][::-1] if a.get('description')]
                st.subheader("Clutch Meter"); st.metric("Fourth-quarter actions tracked", len([a for a in actions if safe_int(a.get('period',0))==4]))
                st.subheader("Team Shot Chart"); shot_df=create_synthetic_shot_chart(actions,alias)
                if not shot_df.empty:
                    opts=["All players"]+sorted(shot_df["Player"].dropna().unique().tolist()); shooter=st.selectbox("Choose shooter",opts); chart_df=shot_df if shooter=="All players" else shot_df[shot_df["Player"]==shooter]
                    st.plotly_chart(draw_halfcourt_shot_chart(chart_df,f"{favorite_team} Live Shot Chart"),use_container_width=True)
                st.subheader("Top Plays"); [st.write(f"• {a.get('description','')}") for a in actions[-5:][::-1] if a.get('description')]
            else: st.info("Live play-by-play is not available yet. Shot chart and top plays will appear when data loads.")
elif page=="Player Playoff Tracker":
    render_matchup_header(favorite_team, False); player_list=profile["starters"]+profile["subs"]; selected_player=st.selectbox("Choose player",player_list); season=st.selectbox("Season",["2025-26","2024-25","2023-24"],index=0)
    if not NBA_STATS_AVAILABLE: st.error("nba_api stats endpoints unavailable.")
    else:
        @st.cache_data(ttl=3600)
        def get_player_id(name):
            matches=[p for p in nba_players.get_players() if p["full_name"]==name]; return matches[0]["id"] if matches else None
        @st.cache_data(ttl=900)
        def get_logs(pid,season_val):
            try: return playergamelog.PlayerGameLog(player_id=pid,season=season_val,season_type_all_star="Playoffs").get_data_frames()[0]
            except Exception: return pd.DataFrame()
        pid=get_player_id(selected_player)
        if pid is None: st.warning(f"Could not find player ID for {selected_player}.")
        else:
            logs=get_logs(pid,season)
            if logs.empty: st.warning(f"No playoff game logs found for {selected_player} in {season}.")
            else:
                cols=[c for c in ["GAME_DATE","MATCHUP","WL","MIN","PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","FT_PCT","PLUS_MINUS"] if c in logs.columns]; st.dataframe(logs[cols],use_container_width=True)
                stat=st.selectbox("Choose stat",[c for c in ["PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","PLUS_MINUS","MIN"] if c in logs.columns]); chart_df=logs.copy(); chart_df["Game Number"]=range(1,len(chart_df)+1); st.plotly_chart(px.line(chart_df,x="Game Number",y=stat,markers=True,title=f"{selected_player} {stat} — Playoffs"),use_container_width=True)
elif page=="Legacy Tracker":
    render_matchup_header(favorite_team,False); selected_player=st.selectbox("Choose starter",profile["starters"]); st.subheader(f"{selected_player} Legacy Tracker")
    pts=st.slider("Playoff scoring average",0,45,20); reb=st.slider("Playoff rebounding average",0,20,6); ast=st.slider("Playoff assists average",0,15,4); wins=st.slider("Series wins this run",0,4,1 if profile["status"]=="Active" else 0)
    score=min(100,round(50+pts*.5+reb*.6+ast*.5+wins*10,1)); st.metric("Legacy Impact Score",score); st.plotly_chart(px.bar(pd.DataFrame({"Outcome":["Current","Win Second Round","Reach Conference Finals","Reach NBA Finals","Win Championship"],"Legacy Score":[50,65,78,90,100]}),x="Outcome",y="Legacy Score",title=f"{selected_player} Legacy Path"),use_container_width=True)
elif page=="Matchup Lineups":
    render_matchup_header(favorite_team,False)
    if profile["status"]!="Active": st.warning("This team is eliminated, so current matchup lineups are not active.")
    else:
        opp=profile["current_opponent"]; op=TEAM_PROFILES[opp]; positions=["PG","SG","SF","PF","C"]
        st.subheader("Projected Starters"); st.dataframe(pd.DataFrame([{"Position":pos,favorite_team:profile["starters"][i],opp:op["starters"][i],"Advantage":"Depends on health, matchup, and game plan"} for i,pos in enumerate(positions)]),use_container_width=True)
        st.subheader("Main Subs"); st.dataframe(pd.DataFrame([{"Team":favorite_team,"Player":p} for p in profile["subs"]]+[{"Team":opp,"Player":p} for p in op["subs"]]),use_container_width=True)
st.divider(); st.caption("Daniel Cohen — NBA Playoff Companion AI | Advanced live game center | Dynamic bracket | Player tracker")
