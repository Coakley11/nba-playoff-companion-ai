import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date

# =====================================================
# OPTIONAL PACKAGES
# =====================================================

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except Exception:
    STATSMODELS_AVAILABLE = False

try:
    from nba_api.live.nba.endpoints import scoreboard
    NBA_LIVE_AVAILABLE = True
except Exception:
    NBA_LIVE_AVAILABLE = False

try:
    from nba_api.stats.static import players as nba_players
    from nba_api.stats.endpoints import playergamelog, leaguegamefinder
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Daniel Cohen — NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("Auto-updating 2026 NBA playoff companion app with live data, team-specific analysis, player logs, and fan perspective")

# =====================================================
# TEAM DATA
# =====================================================

TEAM_IDS = {
    "Atlanta Hawks": 1610612737,
    "Boston Celtics": 1610612738,
    "Cleveland Cavaliers": 1610612739,
    "New Orleans Pelicans": 1610612740,
    "Chicago Bulls": 1610612741,
    "Dallas Mavericks": 1610612742,
    "Denver Nuggets": 1610612743,
    "Golden State Warriors": 1610612744,
    "Houston Rockets": 1610612745,
    "Los Angeles Clippers": 1610612746,
    "Los Angeles Lakers": 1610612747,
    "Miami Heat": 1610612748,
    "Milwaukee Bucks": 1610612749,
    "Minnesota Timberwolves": 1610612750,
    "Brooklyn Nets": 1610612751,
    "New York Knicks": 1610612752,
    "Orlando Magic": 1610612753,
    "Indiana Pacers": 1610612754,
    "Philadelphia 76ers": 1610612755,
    "Phoenix Suns": 1610612756,
    "Portland Trail Blazers": 1610612757,
    "Sacramento Kings": 1610612758,
    "San Antonio Spurs": 1610612759,
    "Oklahoma City Thunder": 1610612760,
    "Toronto Raptors": 1610612761,
    "Utah Jazz": 1610612762,
    "Memphis Grizzlies": 1610612763,
    "Washington Wizards": 1610612764,
    "Detroit Pistons": 1610612765,
    "Charlotte Hornets": 1610612766,
}

TEAM_ALIASES = {
    "New York Knicks": "NYK",
    "Philadelphia 76ers": "PHI",
    "Detroit Pistons": "DET",
    "Cleveland Cavaliers": "CLE",
    "Toronto Raptors": "TOR",
    "Boston Celtics": "BOS",
    "Atlanta Hawks": "ATL",
    "Orlando Magic": "ORL",
    "Oklahoma City Thunder": "OKC",
    "Los Angeles Lakers": "LAL",
    "San Antonio Spurs": "SAS",
    "Minnesota Timberwolves": "MIN",
    "Denver Nuggets": "DEN",
    "Houston Rockets": "HOU",
    "Portland Trail Blazers": "POR",
    "Phoenix Suns": "PHX",
}

ALIAS_TO_TEAM = {v: k for k, v in TEAM_ALIASES.items()}

TEAM_LOGOS = {
    name: f"https://cdn.nba.com/logos/nba/{TEAM_IDS[name]}/primary/L/logo.svg"
    for name in TEAM_ALIASES.keys()
    if name in TEAM_IDS
}

# These are the 16 playoff teams for this app. This fallback state is used only when NBA API data
# cannot yet infer the latest matchup automatically.
TEAM_PROFILES = {
    "New York Knicks": {
        "conference": "East", "seed": 3, "status": "Active", "round": "Second Round",
        "fallback_opponent": "Philadelphia 76ers", "opponent_seed": 7,
        "series_result": "Defeated Atlanta Hawks", "mode": "preview",
        "starters": ["Jalen Brunson", "Karl-Anthony Towns", "OG Anunoby", "Mikal Bridges", "Josh Hart"],
        "subs": ["Miles McBride", "Mitchell Robinson", "Jordan Clarkson", "Landry Shamet", "Jose Alvarado"],
        "strengths": ["Brunson late-game shot creation", "rebounding toughness", "wing defense", "home-court energy", "Towns floor spacing"],
        "concerns": ["Embiid foul pressure", "bench scoring consistency", "overreliance on Brunson", "three-point variance"],
    },
    "Philadelphia 76ers": {
        "conference": "East", "seed": 7, "status": "Active", "round": "Second Round",
        "fallback_opponent": "New York Knicks", "opponent_seed": 3,
        "series_result": "Defeated Boston Celtics", "mode": "preview",
        "starters": ["Tyrese Maxey", "VJ Edgecombe", "Kelly Oubre Jr.", "Paul George", "Joel Embiid"],
        "subs": ["Andre Drummond", "Kyle Lowry", "Eric Gordon", "Caleb Martin", "Quentin Grimes"],
        "strengths": ["Embiid interior dominance", "Maxey speed", "free-throw pressure", "star scoring upside"],
        "concerns": ["Embiid health", "depth", "turnovers", "Knicks offensive rebounding"],
    },
    "Detroit Pistons": {
        "conference": "East", "seed": 1, "status": "Active", "round": "Second Round",
        "fallback_opponent": "Cleveland Cavaliers or Toronto Raptors", "opponent_seed": None,
        "series_result": "Defeated Orlando Magic", "mode": "preview",
        "starters": ["Cade Cunningham", "Jaden Ivey", "Ausar Thompson", "Tobias Harris", "Jalen Duren"],
        "subs": ["Isaiah Stewart", "Marcus Sasser", "Tim Hardaway Jr.", "Simone Fontecchio", "Ron Holland"],
        "strengths": ["young athleticism", "Cade creation", "rebounding", "transition energy"],
        "concerns": ["playoff experience", "late-game execution", "half-court spacing"],
    },
    "Cleveland Cavaliers": {
        "conference": "East", "seed": 4, "status": "Pending", "round": "First Round Pending",
        "fallback_opponent": "Toronto Raptors", "opponent_seed": 5,
        "series_result": "Still playing Toronto Raptors", "mode": "pending",
        "starters": ["Donovan Mitchell", "Darius Garland", "Max Strus", "Evan Mobley", "Jarrett Allen"],
        "subs": ["Caris LeVert", "Isaac Okoro", "Georges Niang", "Dean Wade", "Sam Merrill"],
        "strengths": ["guard scoring", "rim protection", "defensive length"],
        "concerns": ["offensive droughts", "health", "late-game shot creation"],
    },
    "Toronto Raptors": {
        "conference": "East", "seed": 5, "status": "Pending", "round": "First Round Pending",
        "fallback_opponent": "Cleveland Cavaliers", "opponent_seed": 4,
        "series_result": "Still playing Cleveland Cavaliers", "mode": "pending",
        "starters": ["Immanuel Quickley", "RJ Barrett", "Scottie Barnes", "Gradey Dick", "Jakob Poeltl"],
        "subs": ["Bruce Brown", "Kelly Olynyk", "Chris Boucher", "Ochai Agbaji", "Davion Mitchell"],
        "strengths": ["length", "transition energy", "versatile forwards"],
        "concerns": ["half-court scoring", "late-game creation", "shooting consistency"],
    },
    "Boston Celtics": {
        "conference": "East", "seed": 2, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "Philadelphia 76ers", "opponent_seed": 7,
        "series_result": "Lost to Philadelphia 76ers", "mode": "recap",
        "starters": ["Jayson Tatum", "Jaylen Brown", "Derrick White", "Jrue Holiday", "Kristaps Porzingis"],
        "subs": ["Al Horford", "Payton Pritchard", "Sam Hauser", "Luke Kornet", "Xavier Tillman"],
        "strengths": ["wing talent", "spacing", "playoff experience"],
        "concerns": ["late-series execution", "health", "three-point variance"],
    },
    "Atlanta Hawks": {
        "conference": "East", "seed": 6, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "New York Knicks", "opponent_seed": 3,
        "series_result": "Lost to New York Knicks", "mode": "recap",
        "starters": ["Trae Young", "Dyson Daniels", "Zaccharie Risacher", "Jalen Johnson", "Onyeka Okongwu"],
        "subs": ["Bogdan Bogdanovic", "De'Andre Hunter", "Clint Capela", "Vit Krejci", "Kobe Bufkin"],
        "strengths": ["Trae creation", "pace", "guard shot making"],
        "concerns": ["defense", "size", "rebounding", "closing consistency"],
    },
    "Orlando Magic": {
        "conference": "East", "seed": 8, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "Detroit Pistons", "opponent_seed": 1,
        "series_result": "Lost to Detroit Pistons", "mode": "recap",
        "starters": ["Jalen Suggs", "Franz Wagner", "Paolo Banchero", "Wendell Carter Jr.", "Cole Anthony"],
        "subs": ["Jonathan Isaac", "Anthony Black", "Moritz Wagner", "Gary Harris", "Joe Ingles"],
        "strengths": ["defense", "size", "young forwards"],
        "concerns": ["shooting", "late-game offense", "spacing"],
    },
    "Oklahoma City Thunder": {
        "conference": "West", "seed": 1, "status": "Active", "round": "Second Round",
        "fallback_opponent": "Los Angeles Lakers", "opponent_seed": 4,
        "series_result": "Defeated Phoenix Suns", "mode": "preview",
        "starters": ["Shai Gilgeous-Alexander", "Jalen Williams", "Lu Dort", "Chet Holmgren", "Josh Giddey"],
        "subs": ["Isaiah Joe", "Aaron Wiggins", "Cason Wallace", "Jaylin Williams", "Kenrich Williams"],
        "strengths": ["SGA efficiency", "spacing", "defensive length", "youthful energy"],
        "concerns": ["physicality", "rebounding", "Lakers size"],
    },
    "Los Angeles Lakers": {
        "conference": "West", "seed": 4, "status": "Active", "round": "Second Round",
        "fallback_opponent": "Oklahoma City Thunder", "opponent_seed": 1,
        "series_result": "Defeated Houston Rockets", "mode": "preview",
        "starters": ["LeBron James", "Anthony Davis", "Austin Reaves", "Rui Hachimura", "D'Angelo Russell"],
        "subs": ["Gabe Vincent", "Jarred Vanderbilt", "Jaxson Hayes", "Taurean Prince", "Max Christie"],
        "strengths": ["star experience", "rim pressure", "Anthony Davis defense"],
        "concerns": ["age", "transition defense", "guard containment"],
    },
    "San Antonio Spurs": {
        "conference": "West", "seed": 2, "status": "Active", "round": "Second Round",
        "fallback_opponent": "Minnesota Timberwolves", "opponent_seed": 3,
        "series_result": "Defeated Portland Trail Blazers", "mode": "preview",
        "starters": ["Victor Wembanyama", "Devin Vassell", "Stephon Castle", "Keldon Johnson", "Jeremy Sochan"],
        "subs": ["Tre Jones", "Zach Collins", "Malaki Branham", "Julian Champagnie", "Blake Wesley"],
        "strengths": ["Wembanyama two-way impact", "rim protection", "length"],
        "concerns": ["youth", "turnovers", "late-game execution"],
    },
    "Minnesota Timberwolves": {
        "conference": "West", "seed": 3, "status": "Active", "round": "Second Round",
        "fallback_opponent": "San Antonio Spurs", "opponent_seed": 2,
        "series_result": "Defeated Denver Nuggets", "mode": "preview",
        "starters": ["Mike Conley", "Anthony Edwards", "Jaden McDaniels", "Naz Reid", "Rudy Gobert"],
        "subs": ["Nickeil Alexander-Walker", "Kyle Anderson", "Donte DiVincenzo", "Rob Dillingham", "Luka Garza"],
        "strengths": ["Anthony Edwards scoring", "defense", "size", "physicality"],
        "concerns": ["late-game offense", "spacing", "foul trouble"],
    },
    "Denver Nuggets": {
        "conference": "West", "seed": 6, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "Minnesota Timberwolves", "opponent_seed": 3,
        "series_result": "Lost to Minnesota Timberwolves", "mode": "recap",
        "starters": ["Jamal Murray", "Kentavious Caldwell-Pope", "Michael Porter Jr.", "Aaron Gordon", "Nikola Jokic"],
        "subs": ["Christian Braun", "Reggie Jackson", "Peyton Watson", "Zeke Nnaji", "Justin Holiday"],
        "strengths": ["Jokic playmaking", "championship experience", "half-court offense"],
        "concerns": ["bench production", "athletic matchups", "defensive depth"],
    },
    "Houston Rockets": {
        "conference": "West", "seed": 5, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "Los Angeles Lakers", "opponent_seed": 4,
        "series_result": "Lost to Los Angeles Lakers", "mode": "recap",
        "starters": ["Fred VanVleet", "Jalen Green", "Amen Thompson", "Jabari Smith Jr.", "Alperen Sengun"],
        "subs": ["Dillon Brooks", "Tari Eason", "Cam Whitmore", "Steven Adams", "Reed Sheppard"],
        "strengths": ["athleticism", "defense", "young talent"],
        "concerns": ["experience", "half-court offense", "shot selection"],
    },
    "Portland Trail Blazers": {
        "conference": "West", "seed": 7, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "San Antonio Spurs", "opponent_seed": 2,
        "series_result": "Lost to San Antonio Spurs", "mode": "recap",
        "starters": ["Scoot Henderson", "Anfernee Simons", "Shaedon Sharpe", "Jerami Grant", "Deandre Ayton"],
        "subs": ["Toumani Camara", "Matisse Thybulle", "Robert Williams III", "Kris Murray", "Dalano Banton"],
        "strengths": ["young guards", "athleticism", "future upside"],
        "concerns": ["defense", "experience", "consistency"],
    },
    "Phoenix Suns": {
        "conference": "West", "seed": 8, "status": "Eliminated", "round": "Lost First Round",
        "fallback_opponent": "Oklahoma City Thunder", "opponent_seed": 1,
        "series_result": "Lost to Oklahoma City Thunder", "mode": "recap",
        "starters": ["Devin Booker", "Bradley Beal", "Grayson Allen", "Kevin Durant", "Jusuf Nurkic"],
        "subs": ["Eric Gordon", "Royce O'Neale", "Josh Okogie", "Bol Bol", "Drew Eubanks"],
        "strengths": ["shot creation", "veteran scoring", "midrange offense"],
        "concerns": ["depth", "defense", "health", "age"],
    },
}

# Fallback playoff bracket. The app tries to infer current opponent from live/game-log data first.
FALLBACK_BRACKET = pd.DataFrame([
    {"Conference": "East", "Round": "First Round", "Matchup": "1 Detroit Pistons vs 8 Orlando Magic", "Result": "Pistons advanced"},
    {"Conference": "East", "Round": "First Round", "Matchup": "2 Boston Celtics vs 7 Philadelphia 76ers", "Result": "76ers advanced"},
    {"Conference": "East", "Round": "First Round", "Matchup": "3 New York Knicks vs 6 Atlanta Hawks", "Result": "Knicks advanced"},
    {"Conference": "East", "Round": "First Round", "Matchup": "4 Cleveland Cavaliers vs 5 Toronto Raptors", "Result": "Pending / live-update when NBA data resolves"},
    {"Conference": "East", "Round": "Second Round", "Matchup": "3 New York Knicks vs 7 Philadelphia 76ers", "Result": "Series current / live-update"},
    {"Conference": "East", "Round": "Second Round", "Matchup": "1 Detroit Pistons vs Cavaliers/Raptors winner", "Result": "Pending / live-update"},
    {"Conference": "West", "Round": "First Round", "Matchup": "1 Oklahoma City Thunder vs 8 Phoenix Suns", "Result": "Thunder advanced"},
    {"Conference": "West", "Round": "First Round", "Matchup": "4 Los Angeles Lakers vs 5 Houston Rockets", "Result": "Lakers advanced"},
    {"Conference": "West", "Round": "First Round", "Matchup": "2 San Antonio Spurs vs 7 Portland Trail Blazers", "Result": "Spurs advanced"},
    {"Conference": "West", "Round": "First Round", "Matchup": "3 Minnesota Timberwolves vs 6 Denver Nuggets", "Result": "Timberwolves advanced"},
    {"Conference": "West", "Round": "Second Round", "Matchup": "1 Oklahoma City Thunder vs 4 Los Angeles Lakers", "Result": "Series current / live-update"},
    {"Conference": "West", "Round": "Second Round", "Matchup": "2 San Antonio Spurs vs 3 Minnesota Timberwolves", "Result": "Series current / live-update"},
])

# =====================================================
# LIVE / NBA API FUNCTIONS
# =====================================================

@st.cache_data(ttl=30, show_spinner=False)
def get_live_scoreboard_games():
    if not NBA_LIVE_AVAILABLE:
        return []
    try:
        board = scoreboard.ScoreBoard()
        data = board.get_dict()
        return data.get("scoreboard", {}).get("games", [])
    except Exception:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def get_team_playoff_games_from_api(team_name, season="2025-26"):
    if not NBA_STATS_AVAILABLE or team_name not in TEAM_IDS:
        return pd.DataFrame()
    try:
        gf = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=TEAM_IDS[team_name],
            season_nullable=season,
            season_type_nullable="Playoffs"
        )
        df = gf.get_data_frames()[0]
        if not df.empty:
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
            df = df.sort_values("GAME_DATE")
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_player_id(player_name):
    if not NBA_STATS_AVAILABLE:
        return None
    try:
        all_players = nba_players.get_players()
        exact = [p for p in all_players if p.get("full_name") == player_name]
        if exact:
            return exact[0]["id"]
        partial = [p for p in all_players if player_name.lower() in p.get("full_name", "").lower()]
        if partial:
            return partial[0]["id"]
        return None
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_player_playoff_logs(player_name, season="2025-26"):
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    pid = get_player_id(player_name)
    if pid is None:
        return pd.DataFrame()
    try:
        logs = playergamelog.PlayerGameLog(
            player_id=pid,
            season=season,
            season_type_all_star="Playoffs"
        )
        df = logs.get_data_frames()[0]
        if not df.empty:
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
            df = df.sort_values("GAME_DATE")
            df["Game Number"] = range(1, len(df) + 1)
        return df
    except Exception:
        return pd.DataFrame()

def find_live_game_for_team(team_name):
    alias = TEAM_ALIASES.get(team_name)
    for game in get_live_scoreboard_games():
        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})
        if home.get("teamTricode") == alias or away.get("teamTricode") == alias:
            return game
    return None

def infer_current_opponent(team_name, season="2025-26"):
    """Best-effort automatic opponent inference.
    Priority:
    1. live/scheduled game today from nba_api live scoreboard
    2. most recent playoff game log opponent from NBA stats endpoint
    3. fallback bracket dictionary
    """
    live_game = find_live_game_for_team(team_name)
    alias = TEAM_ALIASES.get(team_name)
    if live_game:
        home = live_game.get("homeTeam", {})
        away = live_game.get("awayTeam", {})
        home_alias = home.get("teamTricode")
        away_alias = away.get("teamTricode")
        opponent_alias = away_alias if home_alias == alias else home_alias
        if opponent_alias in ALIAS_TO_TEAM:
            return ALIAS_TO_TEAM[opponent_alias], "live scoreboard"
        return opponent_alias or TEAM_PROFILES[team_name]["fallback_opponent"], "live scoreboard"

    games = get_team_playoff_games_from_api(team_name, season=season)
    if not games.empty and "MATCHUP" in games.columns:
        latest_matchup = str(games.iloc[-1]["MATCHUP"])
        # Examples: NYK vs. PHI, NYK @ PHI
        parts = latest_matchup.replace("vs.", "@").split("@")
        if len(parts) >= 2:
            opp_alias = parts[-1].strip()
            if opp_alias in ALIAS_TO_TEAM:
                return ALIAS_TO_TEAM[opp_alias], "latest playoff game log"
            return opp_alias, "latest playoff game log"

    return TEAM_PROFILES[team_name]["fallback_opponent"], "fallback bracket"

def infer_series_record(team_name, opponent_name, season="2025-26"):
    games = get_team_playoff_games_from_api(team_name, season=season)
    if games.empty or "MATCHUP" not in games.columns or "WL" not in games.columns:
        return None
    team_alias = TEAM_ALIASES.get(team_name, "")
    opp_alias = TEAM_ALIASES.get(opponent_name, str(opponent_name))
    series_games = games[games["MATCHUP"].astype(str).str.contains(opp_alias, na=False)].copy()
    if series_games.empty:
        return None
    wins = int((series_games["WL"] == "W").sum())
    losses = int((series_games["WL"] == "L").sum())
    return {"wins": wins, "losses": losses, "games_played": len(series_games), "games": series_games}

def current_game_focus_from_record(record):
    if record is None:
        return "Game 1"
    gp = int(record.get("games_played", 0))
    return f"Game {gp + 1}" if gp < 7 else "Series complete"

# =====================================================
# PROBABILITY / COMMENTARY FUNCTIONS
# =====================================================

def estimate_live_win_probability(score_margin, quarter, is_home, seconds_remaining=None):
    # Heuristic basketball win-probability approximation. It is NOT an official betting line.
    # It increases score-margin value later in the game.
    q = max(1, min(int(quarter or 1), 4))
    time_weight = {1: 1.4, 2: 1.9, 3: 2.7, 4: 4.1}.get(q, 2.0)
    if seconds_remaining is not None and q == 4:
        if seconds_remaining <= 120:
            time_weight = 6.0
        elif seconds_remaining <= 300:
            time_weight = 4.8
    home_bonus = 2.5 if is_home else 0
    raw = 50 + score_margin * time_weight + home_bonus
    return int(np.clip(round(raw), 1, 99))

def estimate_series_probability(team_name, opponent_name, record=None):
    profile = TEAM_PROFILES[team_name]
    base = 50
    if profile["mode"] == "recap":
        return 0
    if profile["mode"] == "pending":
        base = 50
    if profile["seed"] and isinstance(profile["seed"], int):
        opp_seed = profile.get("opponent_seed")
        if isinstance(opp_seed, int):
            base += (opp_seed - profile["seed"]) * 2
    base += len(profile.get("strengths", [])) * 1.5
    base -= len(profile.get("concerns", [])) * 1.0
    if record:
        base += (record.get("wins", 0) - record.get("losses", 0)) * 12
    return int(np.clip(round(base), 5, 95))

def statsmodels_probability(score_margin, quarter, is_home):
    if not STATSMODELS_AVAILABLE:
        return None
    try:
        train = pd.DataFrame({
            "score_margin": [-25, -18, -12, -7, -3, 0, 3, 7, 12, 18, 25],
            "quarter": [1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
            "is_home": [0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1],
            "won": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        })
        X = sm.add_constant(train[["score_margin", "quarter", "is_home"]])
        y = train["won"]
        model = sm.Logit(y, X).fit(disp=False)
        test = pd.DataFrame({"score_margin": [score_margin], "quarter": [quarter], "is_home": [1 if is_home else 0]})
        test = sm.add_constant(test, has_constant="add")
        return int(round(float(model.predict(test)[0]) * 100))
    except Exception:
        return None

def live_ai_read(team_name, score_margin, quarter, win_prob):
    profile = TEAM_PROFILES[team_name]
    strengths = profile.get("strengths", [])
    concerns = profile.get("concerns", [])
    strength_text = strengths[0] if strengths else "their main strength"
    concern_text = concerns[0] if concerns else "their main concern"

    if score_margin >= 10 and quarter >= 4:
        return (
            f"This is a very strong position for {team_name}. A double-digit fourth-quarter lead usually means the game is now about execution: no live-ball turnovers, defensive rebounding, and forcing the opponent to burn clock. "
            f"From the fan perspective, this is favorable because {strength_text} has probably shown up enough to control the game."
        )
    if score_margin >= 8:
        return (
            f"{team_name} is controlling the game right now. The lead is large enough that the opponent has to speed up. "
            f"That is favorable if {team_name} protects the ball and keeps getting organized possessions."
        )
    if score_margin >= 1:
        return (
            f"{team_name} has the edge, but the game is still very live. The next stretch matters because one run can change the probability quickly. "
            f"The favorable sign is that they are currently ahead while leaning on {strength_text}."
        )
    if score_margin == 0:
        return (
            f"The game is even. For {team_name}, this is still a manageable spot. The key is whether their best players can win the next few possessions and avoid letting {concern_text} become the story."
        )
    if score_margin >= -6:
        return (
            f"{team_name} is trailing, but the game is still within reach. A few stops or a quick scoring burst can flip the game. "
            f"The focus should be shot quality, foul discipline, and not letting the deficit become double digits."
        )
    return (
        f"{team_name} is in a difficult position. The probability has moved against them. They need a clear momentum shift: stops, transition chances, free throws, or a star-player run. "
        f"This is where {concern_text} could become costly if it is not fixed quickly."
    )

# =====================================================
# UI HELPERS
# =====================================================

def show_matchup_header(team_name, season="2025-26"):
    profile = TEAM_PROFILES[team_name]
    opponent, source = infer_current_opponent(team_name, season)
    record = infer_series_record(team_name, opponent, season) if opponent in TEAM_PROFILES else None
    game_focus = current_game_focus_from_record(record)

    col1, col2, col3 = st.columns([1, 2.7, 1])
    with col1:
        if team_name in TEAM_LOGOS:
            st.image(TEAM_LOGOS[team_name], width=115)
    with col2:
        opp_seed = TEAM_PROFILES[opponent]["seed"] if opponent in TEAM_PROFILES else profile.get("opponent_seed")
        title = f"{profile['seed']} {team_name} vs {opp_seed if opp_seed else ''} {opponent}"
        st.markdown(f"<h1 style='text-align:center;'>{title}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center;'>{profile['round']} — {game_focus}</h3>", unsafe_allow_html=True)
        st.caption(f"Opponent source: {source}. This updates automatically when NBA API data exposes a new matchup/game log.")
    with col3:
        if opponent in TEAM_LOGOS:
            st.image(TEAM_LOGOS[opponent], width=115)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", profile["status"])
    c2.metric("Mode", profile["mode"].title())
    c3.metric("Opponent", opponent)
    if record:
        c4.metric("Series Record", f"{record['wins']}-{record['losses']}")
    else:
        c4.metric("Series Record", "Not started / unavailable")
    return opponent, record, game_focus, source

def show_strengths_concerns(team_name):
    profile = TEAM_PROFILES[team_name]
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("What is favorable")
        for s in profile.get("strengths", []):
            st.success(s)
    with c2:
        st.subheader("What could go wrong")
        for c in profile.get("concerns", []):
            st.warning(c)

def show_game_log_table(team_name, opponent_name, season="2025-26"):
    record = infer_series_record(team_name, opponent_name, season) if opponent_name in TEAM_PROFILES else None
    if record and not record["games"].empty:
        df = record["games"].copy()
        cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "PTS", "PLUS_MINUS"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No official game-log rows are available yet for this specific matchup. When the NBA API posts game logs, this table will populate automatically.")

def player_list_for_team(team_name):
    profile = TEAM_PROFILES[team_name]
    return profile.get("starters", []) + profile.get("subs", [])

# =====================================================
# SIDEBAR
# =====================================================

season = st.sidebar.selectbox("NBA season", ["2025-26", "2024-25", "2023-24"], index=0)
favorite_team = st.sidebar.selectbox(
    "Choose your playoff team",
    list(TEAM_PROFILES.keys()),
    index=list(TEAM_PROFILES.keys()).index("New York Knicks")
)

page = st.sidebar.radio(
    "Choose page",
    [
        "Team Command Center",
        "Live Game Center",
        "Series Preview / Recap",
        "Player Playoff Tracker",
        "Legacy Tracker",
        "Matchup Lineups",
        "Playoff Bracket",
        "Data / Auto-Update Health",
    ]
)

profile = TEAM_PROFILES[favorite_team]

# =====================================================
# PAGES
# =====================================================

if page == "Team Command Center":
    opponent, record, game_focus, source = show_matchup_header(favorite_team, season)

    st.subheader("Current Playoff Situation")
    if profile["mode"] == "preview":
        st.success(f"{favorite_team} is still alive. This page focuses on {game_focus} and the path forward against {opponent}.")
    elif profile["mode"] == "pending":
        st.warning(f"{favorite_team}'s series is still pending. When NBA API data shows a new result or matchup, this page will update automatically where possible.")
    else:
        st.error(f"{favorite_team} is eliminated. This page becomes a first-round recap and next-season outlook.")

    series_prob = estimate_series_probability(favorite_team, opponent, record)
    c1, c2, c3 = st.columns(3)
    c1.metric("Estimated Series / Survival Probability", f"{series_prob}%")
    c2.metric("Current Focus", game_focus)
    if record:
        c3.metric("Games Played vs Opponent", record["games_played"])
    else:
        c3.metric("Games Played vs Opponent", "0 / unavailable")

    show_strengths_concerns(favorite_team)

    st.subheader("Game-by-Game Series Log")
    show_game_log_table(favorite_team, opponent, season)

    if profile["mode"] == "recap":
        st.subheader("Next Season Outlook")
        st.write(
            f"For {favorite_team}, the offseason story should focus on what translated in the playoffs and what broke down. "
            "The app should look at star performance, bench reliability, defensive matchups, and whether the team had enough late-game creation."
        )
    else:
        st.subheader(f"{game_focus} Keys")
        st.write(
            f"From a {favorite_team} fan perspective, the key is whether the team can impose its strengths before {opponent} settles into the series. "
            "Watch the first quarter shot quality, turnovers, rebounding, foul trouble, and whether the main star is getting comfortable touches."
        )

elif page == "Live Game Center":
    opponent, record, game_focus, source = show_matchup_header(favorite_team, season)

    st.subheader("Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_game_refresh")
        st.caption("Auto-refreshes every 30 seconds during live games.")
    else:
        st.warning("streamlit-autorefresh is not installed. Add it to requirements.txt for automatic 30-second refresh.")

    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live data is not available. Make sure nba_api is in requirements.txt and redeploy.")
    else:
        live_game = find_live_game_for_team(favorite_team)
        if live_game is None:
            st.info("No live or scheduled game found for this team today from the NBA live scoreboard.")
            st.write("When a game is live, this page will automatically show score, status, margin, and win probability.")
        else:
            home = live_game.get("homeTeam", {})
            away = live_game.get("awayTeam", {})
            home_alias = home.get("teamTricode", "HOME")
            away_alias = away.get("teamTricode", "AWAY")
            home_score = int(home.get("score", 0) or 0)
            away_score = int(away.get("score", 0) or 0)
            status_text = live_game.get("gameStatusText", "")
            period = int(live_game.get("period", 1) or 1)

            st.write(f"### {away_alias} {away_score} at {home_alias} {home_score}")
            st.caption(status_text)

            alias = TEAM_ALIASES[favorite_team]
            is_home = alias == home_alias
            team_score = home_score if is_home else away_score
            opp_score = away_score if is_home else home_score
            margin = team_score - opp_score

            heuristic_prob = estimate_live_win_probability(margin, period, is_home)
            model_prob = statsmodels_probability(margin, period, is_home)
            final_prob = model_prob if model_prob is not None else heuristic_prob

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"{favorite_team} Score", team_score)
            c2.metric("Opponent Score", opp_score)
            c3.metric("Score Margin", f"{margin:+}")
            c4.metric("Win Probability", f"{final_prob}%")

            prob_df = pd.DataFrame({"Outcome": [f"{favorite_team} wins", "Opponent wins"], "Probability": [final_prob, 100 - final_prob]})
            fig = px.pie(prob_df, names="Outcome", values="Probability", title="Live Win Probability")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("AI Live Game Read")
            st.info(live_ai_read(favorite_team, margin, period, final_prob))

            st.subheader("What to watch next")
            st.write(
                f"If {favorite_team} is ahead, the priorities are defensive rebounding, no careless turnovers, and making the opponent take time off the clock. "
                f"If {favorite_team} is behind, the priority is getting a clean scoring run before the next timeout or quarter break."
            )

elif page == "Series Preview / Recap":
    opponent, record, game_focus, source = show_matchup_header(favorite_team, season)

    if profile["mode"] == "recap":
        st.subheader("First-Round Recap")
        st.error(f"{favorite_team} lost to {opponent}. Season over.")
        show_game_log_table(favorite_team, opponent, season)
        st.subheader("What went right")
        for item in profile.get("strengths", []):
            st.success(item)
        st.subheader("What has to improve next season")
        for item in profile.get("concerns", []):
            st.warning(item)
    else:
        st.subheader(f"{game_focus} Preview")
        st.success(f"{favorite_team} is preparing for {opponent}. The app is focused on the next game in the series.")
        show_strengths_concerns(favorite_team)
        st.subheader("Most important next-game factors")
        factors = [
            "first-quarter energy and whether the team gets comfortable shots early",
            "turnovers and transition defense",
            "whether the main star controls the matchup",
            "rebounding margin",
            "bench minutes and foul trouble",
            "late-game shot quality",
        ]
        for f in factors:
            st.write(f"• {f}")

elif page == "Player Playoff Tracker":
    opponent, record, game_focus, source = show_matchup_header(favorite_team, season)

    st.subheader("Official Player Playoff Game Logs")
    selected_player = st.selectbox("Choose player", player_list_for_team(favorite_team))

    if not NBA_STATS_AVAILABLE:
        st.error("nba_api stats endpoint is not available. Make sure nba_api is installed in requirements.txt.")
    else:
        logs = get_player_playoff_logs(selected_player, season)
        if logs.empty:
            st.warning(f"No official playoff game logs found for {selected_player} in {season} yet.")
        else:
            series_filter = st.selectbox("Filter by matchup", ["All playoff games"] + sorted(logs["MATCHUP"].dropna().unique().tolist()))
            view_df = logs.copy()
            if series_filter != "All playoff games":
                view_df = view_df[view_df["MATCHUP"] == series_filter]

            display_cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "PLUS_MINUS"] if c in view_df.columns]
            st.dataframe(view_df[display_cols], use_container_width=True, hide_index=True)

            stat_options = [s for s in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS", "MIN"] if s in view_df.columns]
            selected_stat = st.selectbox("Choose stat to chart", stat_options)
            chart_df = view_df.copy()
            chart_df["Game Number"] = range(1, len(chart_df) + 1)
            fig = px.line(chart_df, x="Game Number", y=selected_stat, markers=True, hover_data=["GAME_DATE", "MATCHUP", "WL"], title=f"{selected_player} {selected_stat} — {season} Playoffs")
            st.plotly_chart(fig, use_container_width=True)

            avg_stat = view_df[selected_stat].mean()
            best_stat = view_df[selected_stat].max()
            low_stat = view_df[selected_stat].min()
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Average {selected_stat}", round(avg_stat, 2))
            c2.metric(f"Best {selected_stat}", round(best_stat, 2))
            c3.metric(f"Lowest {selected_stat}", round(low_stat, 2))

            st.subheader("AI Player Insight")
            if selected_stat in ["PTS", "AST"]:
                st.success(f"{selected_player}'s {selected_stat} trend shows how much offensive responsibility he is carrying. If this number rises while turnovers stay controlled, it is a favorable playoff signal for {favorite_team}.")
            elif selected_stat in ["REB", "STL", "BLK", "PLUS_MINUS"]:
                st.info(f"{selected_player}'s {selected_stat} trend is a strong role-impact indicator. For playoff basketball, this can matter as much as scoring because it reflects possession control and defensive pressure.")
            else:
                st.info(f"{selected_player}'s {selected_stat} trend helps explain efficiency and stability. The key is whether the performance is repeatable as the series gets more physical.")

elif page == "Legacy Tracker":
    opponent, record, game_focus, source = show_matchup_header(favorite_team, season)

    st.subheader(f"{favorite_team} Legacy Tracker")
    selected_player = st.selectbox("Choose starter", profile.get("starters", []))

    logs = get_player_playoff_logs(selected_player, season) if NBA_STATS_AVAILABLE else pd.DataFrame()
    if logs.empty:
        avg_pts, avg_reb, avg_ast = 18, 5, 4
    else:
        avg_pts = float(logs["PTS"].mean()) if "PTS" in logs else 18
        avg_reb = float(logs["REB"].mean()) if "REB" in logs else 5
        avg_ast = float(logs["AST"].mean()) if "AST" in logs else 4

    series_wins = record["wins"] if record else 0
    score = min(100, round(45 + avg_pts * 0.7 + avg_reb * 0.5 + avg_ast * 0.4 + series_wins * 9, 1))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Playoff PPG", round(avg_pts, 1))
    c2.metric("Playoff RPG", round(avg_reb, 1))
    c3.metric("Playoff APG", round(avg_ast, 1))
    c4.metric("Live Legacy Score", score)

    outcomes = pd.DataFrame({
        "Outcome": ["Current", "Win current series", "Reach conference finals", "Reach NBA Finals", "Win Championship"],
        "Legacy Score": [score, min(100, score + 8), min(100, score + 15), min(100, score + 25), 100]
    })
    fig = px.bar(outcomes, x="Outcome", y="Legacy Score", title=f"{selected_player} Legacy Growth Path")
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"{selected_player}'s legacy score updates from available playoff game-log data plus team advancement. "
        f"If {favorite_team} wins more rounds and {selected_player}'s points/rebounds/assists rise, the legacy interpretation becomes stronger automatically."
    )

elif page == "Matchup Lineups":
    opponent, record, game_focus, source = show_matchup_header(favorite_team, season)

    st.subheader("Starters and Main Subs")
    left = TEAM_PROFILES[favorite_team]
    right = TEAM_PROFILES[opponent] if opponent in TEAM_PROFILES else None

    if right:
        starter_rows = []
        positions = ["PG / Lead Guard", "SG / Wing", "SF / Wing", "PF / Forward", "C / Big"]
        for i, pos in enumerate(positions):
            a = left["starters"][i] if i < len(left["starters"]) else "—"
            b = right["starters"][i] if i < len(right["starters"]) else "—"
            starter_rows.append({"Position": pos, favorite_team: a, opponent: b, "Fan Perspective": f"This matchup matters because {a} must either create an edge or limit {b}'s best skill."})
        st.dataframe(pd.DataFrame(starter_rows), use_container_width=True, hide_index=True)

        bench_rows = []
        for p in left.get("subs", []):
            bench_rows.append({"Team": favorite_team, "Player": p, "Role": "Bench impact: defense, spacing, energy, or scoring stability"})
        for p in right.get("subs", []):
            bench_rows.append({"Team": opponent, "Player": p, "Role": "Opponent bench impact to monitor"})
        st.subheader("Main Bench Players")
        st.dataframe(pd.DataFrame(bench_rows), use_container_width=True, hide_index=True)
    else:
        st.warning("Opponent lineup data is not available yet for this inferred matchup.")

elif page == "Playoff Bracket":
    st.header("2026 NBA Playoff Bracket")
    st.caption("Fallback bracket is shown below. Team pages use live scoreboard/game logs to update opponent and game focus when NBA API data is available.")
    st.dataframe(FALLBACK_BRACKET, use_container_width=True, hide_index=True)
    fig = px.sunburst(FALLBACK_BRACKET, path=["Conference", "Round", "Matchup"], title="Playoff Bracket Structure")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Data / Auto-Update Health":
    st.header("Data / Auto-Update Health")
    st.write("This page tells you what is truly automatic and where the data is coming from.")
    health = pd.DataFrame([
        {"Feature": "Live scores / live game status", "Automatic": NBA_LIVE_AVAILABLE, "Source": "nba_api live scoreboard", "Refresh": "30 seconds"},
        {"Feature": "Player playoff game logs", "Automatic": NBA_STATS_AVAILABLE, "Source": "nba_api PlayerGameLog", "Refresh": "15 minutes"},
        {"Feature": "Team playoff game logs", "Automatic": NBA_STATS_AVAILABLE, "Source": "nba_api LeagueGameFinder", "Refresh": "10 minutes"},
        {"Feature": "Opponent inference", "Automatic": NBA_LIVE_AVAILABLE or NBA_STATS_AVAILABLE, "Source": "Live scoreboard first, then latest playoff game log, then fallback bracket", "Refresh": "30 sec / 10 min"},
        {"Feature": "Written AI commentary", "Automatic": True, "Source": "App logic + live score/game-log inputs", "Refresh": "with page refresh"},
        {"Feature": "Fallback bracket", "Automatic": False, "Source": "Built-in dictionary", "Refresh": "manual code update only"},
    ])
    st.dataframe(health, use_container_width=True, hide_index=True)

    games = get_live_scoreboard_games()
    st.subheader("Today / Live NBA Scoreboard Raw Summary")
    if games:
        rows = []
        for g in games:
            home = g.get("homeTeam", {})
            away = g.get("awayTeam", {})
            rows.append({
                "Game": f"{away.get('teamTricode')} at {home.get('teamTricode')}",
                "Score": f"{away.get('score', 0)} - {home.get('score', 0)}",
                "Status": g.get("gameStatusText", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No games returned by the live scoreboard right now, or NBA API is unavailable.")

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | Auto-updating where NBA API data is available | Probabilities are app-generated estimates, not official betting lines")

