import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
    from nba_api.stats.static import players as nba_players
    from nba_api.stats.endpoints import playergamelog, leaguegamefinder
    NBA_API_AVAILABLE = True
except Exception:
    NBA_API_AVAILABLE = False

st.set_page_config(
    page_title="Daniel Cohen — NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 NBA Playoff-only fan companion app | Live-aware bracket, team pages, player tracker, and game center")

# =====================================================
# DATA MODEL
# =====================================================

TEAM_LOGOS = {
    "Detroit Pistons": "https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg",
    "Orlando Magic": "https://cdn.nba.com/logos/nba/1610612753/primary/L/logo.svg",
    "Cleveland Cavaliers": "https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg",
    "Toronto Raptors": "https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg",
    "New York Knicks": "https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg",
    "Atlanta Hawks": "https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg",
    "Philadelphia 76ers": "https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg",
    "Boston Celtics": "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
    "Oklahoma City Thunder": "https://cdn.nba.com/logos/nba/1610612760/primary/L/logo.svg",
    "Phoenix Suns": "https://cdn.nba.com/logos/nba/1610612756/primary/L/logo.svg",
    "Los Angeles Lakers": "https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg",
    "Houston Rockets": "https://cdn.nba.com/logos/nba/1610612745/primary/L/logo.svg",
    "Denver Nuggets": "https://cdn.nba.com/logos/nba/1610612743/primary/L/logo.svg",
    "Minnesota Timberwolves": "https://cdn.nba.com/logos/nba/1610612750/primary/L/logo.svg",
    "San Antonio Spurs": "https://cdn.nba.com/logos/nba/1610612759/primary/L/logo.svg",
    "Portland Trail Blazers": "https://cdn.nba.com/logos/nba/1610612757/primary/L/logo.svg",
}

TEAM_ALIASES = {
    "Detroit Pistons": "DET", "Orlando Magic": "ORL", "Cleveland Cavaliers": "CLE", "Toronto Raptors": "TOR",
    "New York Knicks": "NYK", "Atlanta Hawks": "ATL", "Philadelphia 76ers": "PHI", "Boston Celtics": "BOS",
    "Oklahoma City Thunder": "OKC", "Phoenix Suns": "PHX", "Los Angeles Lakers": "LAL", "Houston Rockets": "HOU",
    "Denver Nuggets": "DEN", "Minnesota Timberwolves": "MIN", "San Antonio Spurs": "SAS", "Portland Trail Blazers": "POR",
}

TEAM_PROFILES = {
    "Detroit Pistons": {
        "conference": "East", "seed": 1, "status": "Active", "round": "Second Round", "opponent": "Cleveland Cavaliers",
        "previous_opponent": "Orlando Magic", "series_result": "Defeated Orlando Magic 4-3", "mode": "preview",
        "starters": ["Cade Cunningham", "Jaden Ivey", "Ausar Thompson", "Tobias Harris", "Jalen Duren"],
        "subs": ["Marcus Sasser", "Malik Beasley", "Isaiah Stewart", "Ron Holland", "Simone Fontecchio"],
        "strengths": ["young athleticism", "transition energy", "Cade Cunningham's creation", "rebounding pressure"],
        "concerns": ["playoff inexperience", "half-court scoring droughts", "late-game execution"]
    },
    "Orlando Magic": {
        "conference": "East", "seed": 8, "status": "Eliminated", "round": "Lost First Round", "opponent": "Detroit Pistons",
        "previous_opponent": "Detroit Pistons", "series_result": "Lost to Detroit Pistons 4-3", "mode": "recap",
        "starters": ["Jalen Suggs", "Kentavious Caldwell-Pope", "Franz Wagner", "Paolo Banchero", "Wendell Carter Jr."],
        "subs": ["Cole Anthony", "Anthony Black", "Jonathan Isaac", "Moritz Wagner", "Gary Harris"],
        "strengths": ["defense", "size", "young forwards", "physicality"],
        "concerns": ["shooting consistency", "late-game offense", "spacing"]
    },
    "Cleveland Cavaliers": {
        "conference": "East", "seed": 4, "status": "Active", "round": "Second Round", "opponent": "Detroit Pistons",
        "previous_opponent": "Toronto Raptors", "series_result": "Defeated Toronto Raptors 4-3", "mode": "preview",
        "starters": ["Darius Garland", "Donovan Mitchell", "Max Strus", "Evan Mobley", "Jarrett Allen"],
        "subs": ["Caris LeVert", "Georges Niang", "Isaac Okoro", "Sam Merrill", "Dean Wade"],
        "strengths": ["guard scoring", "rim protection", "Mobley's defense", "Mitchell's late-game shot making"],
        "concerns": ["offensive droughts", "health", "turnovers against pressure"]
    },
    "Toronto Raptors": {
        "conference": "East", "seed": 5, "status": "Eliminated", "round": "Lost First Round", "opponent": "Cleveland Cavaliers",
        "previous_opponent": "Cleveland Cavaliers", "series_result": "Lost to Cleveland Cavaliers 4-3", "mode": "recap",
        "starters": ["Immanuel Quickley", "RJ Barrett", "Gradey Dick", "Scottie Barnes", "Jakob Poeltl"],
        "subs": ["Kelly Olynyk", "Bruce Brown", "Ochai Agbaji", "Chris Boucher", "Davion Mitchell"],
        "strengths": ["length", "transition play", "Scottie Barnes' versatility"],
        "concerns": ["half-court scoring", "young roster consistency", "late-game creation"]
    },
    "New York Knicks": {
        "conference": "East", "seed": 3, "status": "Active", "round": "Second Round", "opponent": "Philadelphia 76ers",
        "previous_opponent": "Atlanta Hawks", "series_result": "Defeated Atlanta Hawks 4-2", "mode": "preview",
        "starters": ["Jalen Brunson", "Mikal Bridges", "OG Anunoby", "Josh Hart", "Karl-Anthony Towns"],
        "subs": ["Miles McBride", "Mitchell Robinson", "Jordan Clarkson", "Landry Shamet", "Jose Alvarado"],
        "strengths": ["Brunson's half-court creation", "wing defense", "rebounding", "Towns spacing", "Madison Square Garden energy"],
        "concerns": ["Embiid matchup", "foul trouble", "bench stability", "overreliance on Brunson late"]
    },
    "Atlanta Hawks": {
        "conference": "East", "seed": 6, "status": "Eliminated", "round": "Lost First Round", "opponent": "New York Knicks",
        "previous_opponent": "New York Knicks", "series_result": "Lost to New York Knicks 4-2", "mode": "recap",
        "starters": ["Trae Young", "Dyson Daniels", "Zaccharie Risacher", "Jalen Johnson", "Onyeka Okongwu"],
        "subs": ["Bogdan Bogdanovic", "De'Andre Hunter", "Clint Capela", "Vit Krejci", "Kobe Bufkin"],
        "strengths": ["Trae Young creation", "pace", "guard scoring", "Jalen Johnson's athleticism"],
        "concerns": ["defense", "physicality against New York", "rebounding", "late-series shot quality"]
    },
    "Philadelphia 76ers": {
        "conference": "East", "seed": 7, "status": "Active", "round": "Second Round", "opponent": "New York Knicks",
        "previous_opponent": "Boston Celtics", "series_result": "Defeated Boston Celtics 4-3", "mode": "preview",
        "starters": ["Tyrese Maxey", "VJ Edgecombe", "Kelly Oubre Jr.", "Paul George", "Joel Embiid"],
        "subs": ["Andre Drummond", "Quentin Grimes", "Kyle Lowry", "Eric Gordon", "Caleb Martin"],
        "strengths": ["Embiid's interior dominance", "Maxey's speed", "free-throw pressure", "star shot creation"],
        "concerns": ["Embiid's health", "bench reliability", "Knicks rebounding", "turnovers"]
    },
    "Boston Celtics": {
        "conference": "East", "seed": 2, "status": "Eliminated", "round": "Lost First Round", "opponent": "Philadelphia 76ers",
        "previous_opponent": "Philadelphia 76ers", "series_result": "Lost to Philadelphia 76ers 4-3", "mode": "recap",
        "starters": ["Jrue Holiday", "Derrick White", "Jaylen Brown", "Jayson Tatum", "Kristaps Porzingis"],
        "subs": ["Payton Pritchard", "Al Horford", "Sam Hauser", "Luke Kornet", "Xavier Tillman"],
        "strengths": ["wing talent", "spacing", "defensive versatility", "championship experience"],
        "concerns": ["late-series scoring", "health", "execution against Philadelphia"]
    },
    "Oklahoma City Thunder": {
        "conference": "West", "seed": 1, "status": "Active", "round": "Second Round", "opponent": "Los Angeles Lakers",
        "previous_opponent": "Phoenix Suns", "series_result": "Defeated Phoenix Suns 4-0", "mode": "preview",
        "starters": ["Shai Gilgeous-Alexander", "Lu Dort", "Jalen Williams", "Chet Holmgren", "Isaiah Hartenstein"],
        "subs": ["Cason Wallace", "Aaron Wiggins", "Alex Caruso", "Isaiah Joe", "Jaylin Williams"],
        "strengths": ["Shai's efficiency", "spacing", "defensive length", "speed"],
        "concerns": ["Lakers size", "playoff physicality", "rebounding"]
    },
    "Phoenix Suns": {
        "conference": "West", "seed": 8, "status": "Eliminated", "round": "Lost First Round", "opponent": "Oklahoma City Thunder",
        "previous_opponent": "Oklahoma City Thunder", "series_result": "Lost to Oklahoma City Thunder 4-0", "mode": "recap",
        "starters": ["Devin Booker", "Bradley Beal", "Grayson Allen", "Kevin Durant", "Jusuf Nurkic"],
        "subs": ["Royce O'Neale", "Bol Bol", "Eric Gordon", "Josh Okogie", "Drew Eubanks"],
        "strengths": ["shot creation", "veteran scoring", "midrange offense"],
        "concerns": ["depth", "defense", "age", "health"]
    },
    "Los Angeles Lakers": {
        "conference": "West", "seed": 4, "status": "Active", "round": "Second Round", "opponent": "Oklahoma City Thunder",
        "previous_opponent": "Houston Rockets", "series_result": "Defeated Houston Rockets 4-2", "mode": "preview",
        "starters": ["D'Angelo Russell", "Austin Reaves", "LeBron James", "Rui Hachimura", "Anthony Davis"],
        "subs": ["Gabe Vincent", "Jarred Vanderbilt", "Taurean Prince", "Jaxson Hayes", "Max Christie"],
        "strengths": ["LeBron's control", "Anthony Davis defense", "playoff experience", "half-court control"],
        "concerns": ["age", "transition defense", "guard containment", "three-point consistency"]
    },
    "Houston Rockets": {
        "conference": "West", "seed": 5, "status": "Eliminated", "round": "Lost First Round", "opponent": "Los Angeles Lakers",
        "previous_opponent": "Los Angeles Lakers", "series_result": "Lost to Los Angeles Lakers 4-2", "mode": "recap",
        "starters": ["Fred VanVleet", "Jalen Green", "Dillon Brooks", "Jabari Smith Jr.", "Alperen Sengun"],
        "subs": ["Amen Thompson", "Tari Eason", "Cam Whitmore", "Steven Adams", "Aaron Holiday"],
        "strengths": ["young athleticism", "defense", "pace", "Sengun creation"],
        "concerns": ["experience", "shot selection", "half-court scoring"]
    },
    "Denver Nuggets": {
        "conference": "West", "seed": 3, "status": "Eliminated", "round": "Lost First Round", "opponent": "Minnesota Timberwolves",
        "previous_opponent": "Minnesota Timberwolves", "series_result": "Lost to Minnesota Timberwolves 4-2", "mode": "recap",
        "starters": ["Jamal Murray", "Christian Braun", "Michael Porter Jr.", "Aaron Gordon", "Nikola Jokic"],
        "subs": ["Reggie Jackson", "Peyton Watson", "Julian Strawther", "Zeke Nnaji", "DeAndre Jordan"],
        "strengths": ["Jokic's playmaking", "chemistry", "championship experience"],
        "concerns": ["bench production", "athletic matchups", "defensive depth"]
    },
    "Minnesota Timberwolves": {
        "conference": "West", "seed": 6, "status": "Active", "round": "Second Round", "opponent": "San Antonio Spurs",
        "previous_opponent": "Denver Nuggets", "series_result": "Defeated Denver Nuggets 4-2", "mode": "preview",
        "starters": ["Mike Conley", "Anthony Edwards", "Jaden McDaniels", "Naz Reid", "Rudy Gobert"],
        "subs": ["Donte DiVincenzo", "Nickeil Alexander-Walker", "Julius Randle", "Rob Dillingham", "Luka Garza"],
        "strengths": ["Anthony Edwards scoring", "elite defense", "size", "physicality"],
        "concerns": ["late-game offense", "spacing", "foul trouble"]
    },
    "San Antonio Spurs": {
        "conference": "West", "seed": 2, "status": "Active", "round": "Second Round", "opponent": "Minnesota Timberwolves",
        "previous_opponent": "Portland Trail Blazers", "series_result": "Defeated Portland Trail Blazers 4-1", "mode": "preview",
        "starters": ["Stephon Castle", "Devin Vassell", "Keldon Johnson", "Jeremy Sochan", "Victor Wembanyama"],
        "subs": ["Tre Jones", "Malaki Branham", "Zach Collins", "Julian Champagnie", "Blake Wesley"],
        "strengths": ["Wembanyama's two-way impact", "length", "shot blocking", "youthful energy"],
        "concerns": ["playoff inexperience", "physicality", "turnovers"]
    },
    "Portland Trail Blazers": {
        "conference": "West", "seed": 7, "status": "Eliminated", "round": "Lost First Round", "opponent": "San Antonio Spurs",
        "previous_opponent": "San Antonio Spurs", "series_result": "Lost to San Antonio Spurs 4-1", "mode": "recap",
        "starters": ["Scoot Henderson", "Anfernee Simons", "Shaedon Sharpe", "Jerami Grant", "Deandre Ayton"],
        "subs": ["Matisse Thybulle", "Robert Williams III", "Toumani Camara", "Kris Murray", "Dalano Banton"],
        "strengths": ["young guards", "athleticism", "future upside"],
        "concerns": ["defense", "experience", "frontcourt matchups"]
    },
}

FIRST_ROUND_SERIES = [
    {"conf": "East", "top_seed": 1, "top": "Detroit Pistons", "bottom_seed": 8, "bottom": "Orlando Magic", "top_wins": 4, "bottom_wins": 3, "winner": "Detroit Pistons"},
    {"conf": "East", "top_seed": 4, "top": "Cleveland Cavaliers", "bottom_seed": 5, "bottom": "Toronto Raptors", "top_wins": 4, "bottom_wins": 3, "winner": "Cleveland Cavaliers"},
    {"conf": "East", "top_seed": 3, "top": "New York Knicks", "bottom_seed": 6, "bottom": "Atlanta Hawks", "top_wins": 4, "bottom_wins": 2, "winner": "New York Knicks"},
    {"conf": "East", "top_seed": 2, "top": "Boston Celtics", "bottom_seed": 7, "bottom": "Philadelphia 76ers", "top_wins": 3, "bottom_wins": 4, "winner": "Philadelphia 76ers"},
    {"conf": "West", "top_seed": 1, "top": "Oklahoma City Thunder", "bottom_seed": 8, "bottom": "Phoenix Suns", "top_wins": 4, "bottom_wins": 0, "winner": "Oklahoma City Thunder"},
    {"conf": "West", "top_seed": 4, "top": "Los Angeles Lakers", "bottom_seed": 5, "bottom": "Houston Rockets", "top_wins": 4, "bottom_wins": 2, "winner": "Los Angeles Lakers"},
    {"conf": "West", "top_seed": 3, "top": "Denver Nuggets", "bottom_seed": 6, "bottom": "Minnesota Timberwolves", "top_wins": 2, "bottom_wins": 4, "winner": "Minnesota Timberwolves"},
    {"conf": "West", "top_seed": 2, "top": "San Antonio Spurs", "bottom_seed": 7, "bottom": "Portland Trail Blazers", "top_wins": 4, "bottom_wins": 1, "winner": "San Antonio Spurs"},
]

SECOND_ROUND_SERIES = [
    {"conf": "East", "a_seed": 1, "a": "Detroit Pistons", "b_seed": 4, "b": "Cleveland Cavaliers", "a_wins": 0, "b_wins": 0, "winner": None},
    {"conf": "East", "a_seed": 3, "a": "New York Knicks", "b_seed": 7, "b": "Philadelphia 76ers", "a_wins": 0, "b_wins": 0, "winner": None},
    {"conf": "West", "a_seed": 1, "a": "Oklahoma City Thunder", "b_seed": 4, "b": "Los Angeles Lakers", "a_wins": 0, "b_wins": 0, "winner": None},
    {"conf": "West", "a_seed": 2, "a": "San Antonio Spurs", "b_seed": 6, "b": "Minnesota Timberwolves", "a_wins": 0, "b_wins": 0, "winner": None},
]

FIRST_ROUND_GAME_SCORES = {
    "New York Knicks": [
        {"Game": 1, "Matchup": "Hawks at Knicks", "Result": "Knicks win", "Score": "NYK 112, ATL 101"},
        {"Game": 2, "Matchup": "Hawks at Knicks", "Result": "Knicks win", "Score": "NYK 106, ATL 99"},
        {"Game": 3, "Matchup": "Knicks at Hawks", "Result": "Hawks win", "Score": "ATL 118, NYK 111"},
        {"Game": 4, "Matchup": "Knicks at Hawks", "Result": "Knicks win", "Score": "NYK 109, ATL 104"},
        {"Game": 5, "Matchup": "Hawks at Knicks", "Result": "Hawks win", "Score": "ATL 115, NYK 110"},
        {"Game": 6, "Matchup": "Knicks at Hawks", "Result": "Knicks win", "Score": "NYK 121, ATL 107"},
    ],
    "Atlanta Hawks": [
        {"Game": 1, "Matchup": "Hawks at Knicks", "Result": "Hawks loss", "Score": "NYK 112, ATL 101"},
        {"Game": 2, "Matchup": "Hawks at Knicks", "Result": "Hawks loss", "Score": "NYK 106, ATL 99"},
        {"Game": 3, "Matchup": "Knicks at Hawks", "Result": "Hawks win", "Score": "ATL 118, NYK 111"},
        {"Game": 4, "Matchup": "Knicks at Hawks", "Result": "Hawks loss", "Score": "NYK 109, ATL 104"},
        {"Game": 5, "Matchup": "Hawks at Knicks", "Result": "Hawks win", "Score": "ATL 115, NYK 110"},
        {"Game": 6, "Matchup": "Knicks at Hawks", "Result": "Hawks loss", "Score": "NYK 121, ATL 107"},
    ],
}

SECOND_ROUND_SCHEDULE = {
    ("New York Knicks", "Philadelphia 76ers"): [
        {"Game": "Game 1", "Date": "Mon, May 4", "Time": "8:00 PM ET", "Location": "Madison Square Garden", "TV": "NBC / Peacock", "Matchup": "76ers at Knicks"},
        {"Game": "Game 2", "Date": "Wed, May 6", "Time": "7:00 PM ET", "Location": "Madison Square Garden", "TV": "ESPN", "Matchup": "76ers at Knicks"},
        {"Game": "Game 3", "Date": "Fri, May 8", "Time": "7:00 PM ET", "Location": "Philadelphia", "TV": "Prime Video", "Matchup": "Knicks at 76ers"},
        {"Game": "Game 4", "Date": "Sun, May 10", "Time": "3:30 PM ET", "Location": "Philadelphia", "TV": "ABC", "Matchup": "Knicks at 76ers"},
        {"Game": "Game 5", "Date": "Tue, May 12", "Time": "TBD", "Location": "Madison Square Garden", "TV": "TBD", "Matchup": "76ers at Knicks"},
        {"Game": "Game 6", "Date": "Thu, May 14", "Time": "TBD", "Location": "Philadelphia", "TV": "TBD", "Matchup": "Knicks at 76ers"},
        {"Game": "Game 7", "Date": "Sun, May 17", "Time": "TBD", "Location": "Madison Square Garden", "TV": "TBD", "Matchup": "76ers at Knicks"},
    ],
}

# =====================================================
# LIVE DATA HELPERS
# =====================================================

@st.cache_data(ttl=30)
def get_live_scoreboard():
    if not NBA_API_AVAILABLE:
        return []
    try:
        board = scoreboard.ScoreBoard()
        data = board.get_dict()
        return data.get("scoreboard", {}).get("games", [])
    except Exception:
        return []


def find_team_live_game(team_name):
    games = get_live_scoreboard()
    alias = TEAM_ALIASES.get(team_name)
    for game in games:
        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})
        if home.get("teamTricode") == alias or away.get("teamTricode") == alias:
            return game
    return None


@st.cache_data(ttl=600)
def get_official_playoff_gamefinder(season="2025-26"):
    if not NBA_API_AVAILABLE:
        return pd.DataFrame()
    try:
        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable="Playoffs"
        )
        return finder.get_data_frames()[0]
    except Exception:
        return pd.DataFrame()


def update_series_from_official_games(series_list, season="2025-26"):
    games = get_official_playoff_gamefinder(season)
    updated = []

    for s in series_list:
        row = dict(s)
        a_name = row.get("a", row.get("top"))
        b_name = row.get("b", row.get("bottom"))
        a_abbr = TEAM_ALIASES.get(a_name)
        b_abbr = TEAM_ALIASES.get(b_name)

        if games.empty or not a_abbr or not b_abbr or "TEAM_ABBREVIATION" not in games.columns or "WL" not in games.columns:
            updated.append(row)
            continue

        matchup_col = games["MATCHUP"].astype(str) if "MATCHUP" in games.columns else pd.Series([""] * len(games))
        a_rows = games[(games["TEAM_ABBREVIATION"] == a_abbr) & (matchup_col.str.contains(b_abbr, na=False)) & (games["WL"] == "W")]
        b_rows = games[(games["TEAM_ABBREVIATION"] == b_abbr) & (matchup_col.str.contains(a_abbr, na=False)) & (games["WL"] == "W")]

        if len(a_rows) > 0 or len(b_rows) > 0:
            if "a_wins" in row:
                row["a_wins"] = int(len(a_rows))
                row["b_wins"] = int(len(b_rows))
                if row["a_wins"] >= 4:
                    row["winner"] = a_name
                elif row["b_wins"] >= 4:
                    row["winner"] = b_name
            else:
                row["top_wins"] = int(len(a_rows))
                row["bottom_wins"] = int(len(b_rows))
                if row["top_wins"] >= 4:
                    row["winner"] = a_name
                elif row["bottom_wins"] >= 4:
                    row["winner"] = b_name
        updated.append(row)
    return updated


def series_card_html(team_a, seed_a, wins_a, team_b, seed_b, wins_b, winner=None):
    logo_a = TEAM_LOGOS.get(team_a, "")
    logo_b = TEAM_LOGOS.get(team_b, "")
    abbr_a = TEAM_ALIASES.get(team_a, team_a[:3].upper())
    abbr_b = TEAM_ALIASES.get(team_b, team_b[:3].upper())
    check_a = "✅" if winner == team_a else ""
    check_b = "✅" if winner == team_b else ""
    faded_a = " winner-row" if winner == team_a else (" faded-row" if winner and winner != team_a else "")
    faded_b = " winner-row" if winner == team_b else (" faded-row" if winner and winner != team_b else "")
    return f"""
    <div class='series-card'>
      <div class='team-row{faded_a}'>
        <span class='seed'>{seed_a}</span>
        <img src='{logo_a}' class='team-logo' />
        <span class='abbr'>{abbr_a}</span>
        <span class='wins'>{wins_a}</span>
        <span class='check'>{check_a}</span>
      </div>
      <div class='team-row{faded_b}'>
        <span class='seed'>{seed_b}</span>
        <img src='{logo_b}' class='team-logo' />
        <span class='abbr'>{abbr_b}</span>
        <span class='wins'>{wins_b}</span>
        <span class='check'>{check_b}</span>
      </div>
    </div>
    """


def tbd_card_html(title="TBD"):
    return f"""
    <div class='series-card tbd-card'>
      <div class='team-row'><span class='seed'>-</span><span class='abbr'>{title}</span><span class='wins'>--</span></div>
      <div class='team-row'><span class='seed'>-</span><span class='abbr'>TBD</span><span class='wins'>--</span></div>
    </div>
    """


def render_dynamic_bracket():
    first = update_series_from_official_games(FIRST_ROUND_SERIES)
    second = update_series_from_official_games(SECOND_ROUND_SERIES)

    east_first = [x for x in first if x["conf"] == "East"]
    west_first = [x for x in first if x["conf"] == "West"]
    east_second = [x for x in second if x["conf"] == "East"]
    west_second = [x for x in second if x["conf"] == "West"]

    east_finalists = [s.get("winner") for s in east_second if s.get("winner")]
    west_finalists = [s.get("winner") for s in west_second if s.get("winner")]

    css = """
    <style>
    .bracket-wrap {background: radial-gradient(circle at top, #222078, #090b1a 60%, #05060d); padding: 24px; border-radius: 24px; border: 1px solid rgba(255,255,255,.15); color: white;}
    .bracket-title {text-align:center; font-size:52px; font-weight:900; letter-spacing:2px; margin-bottom:2px;}
    .bracket-subtitle {text-align:center; color:#cdd3ff; font-size:18px; margin-bottom:18px;}
    .bracket-grid {display:grid; grid-template-columns: 1.2fr 1fr .9fr 1fr 1.2fr; gap:22px; align-items:center;}
    .conf-title-east {color:#4da3ff; font-size:24px; font-weight:800; margin: 8px 0 12px;}
    .conf-title-west {color:#ff5050; font-size:24px; font-weight:800; margin: 8px 0 12px; text-align:right;}
    .round-title {font-weight:800; color:#ffffff; text-transform:uppercase; margin: 10px 0; font-size:16px;}
    .series-card {background:linear-gradient(135deg, rgba(255,255,255,.13), rgba(255,255,255,.04)); border:1px solid rgba(255,255,255,.22); border-radius:12px; margin:10px 0; padding:8px; box-shadow:0 12px 28px rgba(0,0,0,.28);}
    .team-row {display:grid; grid-template-columns: 26px 36px 1fr 32px 24px; align-items:center; gap:8px; padding:6px; border-bottom:1px solid rgba(255,255,255,.12);}
    .team-row:last-child {border-bottom:0;}
    .team-logo {width:32px; height:32px; object-fit:contain;}
    .seed {font-weight:800; color:#d7e0ff;}
    .abbr {font-weight:900; font-size:20px; letter-spacing:.5px;}
    .wins {font-weight:900; font-size:24px; text-align:right;}
    .check {color:#32ff76; font-size:20px;}
    .winner-row {background:rgba(44,255,120,.12); border-radius:8px;}
    .faded-row {opacity:.55;}
    .center-panel {text-align:center;}
    .trophy {font-size:78px; margin:8px 0;}
    .finals-box {background:linear-gradient(180deg, rgba(255,255,255,.12), rgba(255,255,255,.04)); border:1px solid rgba(255,255,255,.28); border-radius:16px; padding:18px; margin:12px 0;}
    .live-dot {display:inline-block; width:12px; height:12px; background:#13e45d; border-radius:999px; margin-right:8px;}
    .small-note {font-size:13px; color:#c8cae8; text-align:center; margin-top:12px;}
    @media (max-width: 1000px) {.bracket-grid {grid-template-columns:1fr;} .conf-title-west {text-align:left;} .bracket-title{font-size:34px;}}
    </style>
    """

    html = css + "<div class='bracket-wrap'>"
    html += "<div class='bracket-title'>NBA PLAYOFFS</div><div class='bracket-subtitle'>2026 • Auto-updating bracket view</div>"
    html += "<div class='bracket-grid'>"

    html += "<div><div class='conf-title-east'>EASTERN CONFERENCE</div><div class='round-title'>First Round</div>"
    for s in east_first:
        html += series_card_html(s["top"], s["top_seed"], s["top_wins"], s["bottom"], s["bottom_seed"], s["bottom_wins"], s.get("winner"))
    html += "</div>"

    html += "<div><div class='round-title'>Conference Semifinals</div>"
    for s in east_second:
        html += series_card_html(s["a"], s["a_seed"], s["a_wins"], s["b"], s["b_seed"], s["b_wins"], s.get("winner"))
    html += "</div>"

    html += "<div class='center-panel'><div class='round-title'>Conference Finals</div>"
    if len(east_finalists) >= 2:
        html += series_card_html(east_finalists[0], TEAM_PROFILES[east_finalists[0]]["seed"], 0, east_finalists[1], TEAM_PROFILES[east_finalists[1]]["seed"], 0, None)
    else:
        html += tbd_card_html("EAST TBD")
    html += "<div class='trophy'>🏆</div><div class='finals-box'><b>NBA FINALS</b><br/>Eastern Champion: TBD<br/>Western Champion: TBD</div>"
    if len(west_finalists) >= 2:
        html += series_card_html(west_finalists[0], TEAM_PROFILES[west_finalists[0]]["seed"], 0, west_finalists[1], TEAM_PROFILES[west_finalists[1]]["seed"], 0, None)
    else:
        html += tbd_card_html("WEST TBD")
    html += "</div>"

    html += "<div><div class='round-title'>Conference Semifinals</div>"
    for s in west_second:
        html += series_card_html(s["a"], s["a_seed"], s["a_wins"], s["b"], s["b_seed"], s["b_wins"], s.get("winner"))
    html += "</div>"

    html += "<div><div class='conf-title-west'>WESTERN CONFERENCE</div><div class='round-title'>First Round</div>"
    for s in west_first:
        html += series_card_html(s["top"], s["top_seed"], s["top_wins"], s["bottom"], s["bottom_seed"], s["bottom_wins"], s.get("winner"))
    html += "</div>"

    html += "</div><div class='small-note'><span class='live-dot'></span>Auto-refreshes on the app. Official NBA playoff game logs are used when available; otherwise the app uses the built-in bracket model.</div></div>"
    st.markdown(html, unsafe_allow_html=True)

    return first, second

def infer_live_series_update(team_name):
    # This layer is live-aware. It checks today's live/scheduled opponent first.
    # If there is no live game, it falls back to the known 2026 bracket data above.
    live_game = find_team_live_game(team_name)
    profile = TEAM_PROFILES[team_name]
    if live_game:
        home = live_game.get("homeTeam", {})
        away = live_game.get("awayTeam", {})
        alias = TEAM_ALIASES.get(team_name)
        if home.get("teamTricode") == alias:
            opponent_alias = away.get("teamTricode")
        else:
            opponent_alias = home.get("teamTricode")
        for name, abbr in TEAM_ALIASES.items():
            if abbr == opponent_alias:
                return name, live_game.get("gameStatusText", "Live/Scheduled")
    return profile.get("opponent"), "Bracket data"


def estimate_win_probability(score_margin, quarter, is_home, status):
    if status == "Eliminated":
        return 0
    base = 55 if status == "Active" else 50
    home_bonus = 3 if is_home else 0
    quarter_pressure = max(1, quarter) * 3
    raw = base + score_margin * 2.4 + home_bonus + quarter_pressure
    return int(max(1, min(99, raw)))


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

@st.cache_data(ttl=900)
def get_player_id(player_name):
    if not NBA_API_AVAILABLE:
        return None
    try:
        matches = [p for p in nba_players.get_players() if p["full_name"].lower() == player_name.lower()]
        return matches[0]["id"] if matches else None
    except Exception:
        return None

@st.cache_data(ttl=900)
def get_real_playoff_logs(player_id, season_value):
    if not NBA_API_AVAILABLE or player_id is None:
        return pd.DataFrame()
    try:
        logs = playergamelog.PlayerGameLog(player_id=player_id, season=season_value, season_type_all_star="Playoffs")
        return logs.get_data_frames()[0]
    except Exception:
        return pd.DataFrame()

# =====================================================
# UI HELPERS
# =====================================================

def small_logo(team_name, width=48):
    logo = TEAM_LOGOS.get(team_name)
    if logo:
        st.image(logo, width=width)


def matchup_title(team_name):
    profile = TEAM_PROFILES[team_name]
    opponent, source = infer_live_series_update(team_name)
    opponent_profile = TEAM_PROFILES.get(opponent, {})

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        small_logo(team_name, 110)
    with col2:
        if profile["status"] == "Eliminated":
            text = f"{profile['seed']} {team_name} vs {opponent_profile.get('seed', '')} {opponent}"
            subtitle = f"First Round Recap — {profile['series_result']}"
        else:
            text = f"{profile['seed']} {team_name} vs {opponent_profile.get('seed', '')} {opponent}"
            subtitle = f"{profile['round']} — Current matchup"
        st.markdown(f"<h1 style='text-align:center;'>{text}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center;'>{subtitle}</h3>", unsafe_allow_html=True)
        st.caption(f"Opponent source: {source}. Bracket auto-refreshes on page load and live-game data refreshes when games are active.")
    with col3:
        small_logo(opponent, 110)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conference", profile["conference"])
    c2.metric("Seed", profile["seed"])
    c3.metric("Status", profile["status"])
    c4.metric("Round", profile["round"])


def selected_roster(team_name):
    p = TEAM_PROFILES[team_name]
    return p["starters"] + p["subs"]


def team_perspective_text(team_name):
    p = TEAM_PROFILES[team_name]
    if p["status"] == "Eliminated":
        return f"From the {team_name} perspective, the app now becomes a first-round recap and next-season planning tool."
    return f"From the {team_name} perspective, the app now focuses on the second-round matchup against {p['opponent']} and what must go right next."

# =====================================================
# SIDEBAR
# =====================================================

favorite_team = st.sidebar.selectbox(
    "Choose your 2026 playoff team",
    list(TEAM_PROFILES.keys()),
    index=list(TEAM_PROFILES.keys()).index("New York Knicks"),
)
team = TEAM_PROFILES[favorite_team]

page = st.sidebar.radio(
    "Choose page",
    [
        "Home Dashboard",
        "Playoff Bracket",
        "Current Series / Recap",
        "First-Round Review",
        "Live Game Center",
        "Player Playoff Tracker",
        "Matchup Lineups",
        "Legacy Tracker",
        "Other Series Watch",
        "AI Prediction Center",
    ],
)

# =====================================================
# PAGES
# =====================================================

if page == "Home Dashboard":
    matchup_title(favorite_team)
    st.subheader("Team Perspective")
    st.write(team_perspective_text(favorite_team))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Strengths")
        for x in team["strengths"]:
            st.success(x)
    with col2:
        st.subheader("Concerns")
        for x in team["concerns"]:
            st.warning(x)

    if team["status"] == "Active":
        st.subheader("Second-Round Focus")
        st.info(f"The regular page now shows the current second-round matchup: {favorite_team} vs {team['opponent']}.")
    else:
        st.subheader("Season Recap Mode")
        st.error(f"{favorite_team} are eliminated. Result: {team['series_result']}")
        st.write("Best of luck next season. This team page now focuses on what went right, what went wrong, and what to build on.")

elif page == "Playoff Bracket":
    st.header("2026 NBA Playoff Bracket")

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=60000, key="bracket_refresh")
        st.caption("This bracket refreshes every 60 seconds. When official NBA playoff data is available, series records update automatically.")
    else:
        st.caption("Add streamlit-autorefresh to requirements.txt for automatic bracket refresh.")

    st.info(
        "This is the dynamic app version of the bracket image: team logos, seeds, first-round results, second-round matchups, and live-updating series records when NBA data is available."
    )

    updated_first, updated_second = render_dynamic_bracket()

    with st.expander("See bracket data table"):
        rows = []
        for s in updated_first:
            rows.append({
                "Conference": s["conf"],
                "Round": "First Round",
                "Matchup": f"{s['top_seed']} {s['top']} vs {s['bottom_seed']} {s['bottom']}",
                "Series": f"{s['top_wins']}-{s['bottom_wins']}",
                "Winner": s.get("winner", "TBD")
            })
        for s in updated_second:
            rows.append({
                "Conference": s["conf"],
                "Round": "Second Round",
                "Matchup": f"{s['a_seed']} {s['a']} vs {s['b_seed']} {s['b']}",
                "Series": f"{s['a_wins']}-{s['b_wins']}",
                "Winner": s.get("winner") or "TBD"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Current Series / Recap":
    matchup_title(favorite_team)
    if team["status"] == "Active":
        opponent = team["opponent"]
        st.subheader(f"Current Second-Round Matchup: {favorite_team} vs {opponent}")
        key = (favorite_team, opponent) if (favorite_team, opponent) in SECOND_ROUND_SCHEDULE else (opponent, favorite_team)
        schedule = SECOND_ROUND_SCHEDULE.get(key, [])
        if schedule:
            st.subheader("Series Schedule")
            st.dataframe(pd.DataFrame(schedule), use_container_width=True, hide_index=True)
        else:
            st.info("Schedule will appear here when loaded for this matchup.")
        st.subheader("What Has To Go Right")
        for x in team["strengths"]:
            st.success(f"{favorite_team} must lean into: {x}")
        st.subheader("What Could Swing The Series")
        for x in team["concerns"]:
            st.warning(f"Watch for: {x}")
        st.info(f"Game 1 focus: establish the series identity, test matchup coverages, and see how {favorite_team}'s main stars handle the opponent's pressure.")
    else:
        st.subheader("First-Round Recap")
        st.error(team["series_result"])
        st.write(f"From the {favorite_team} perspective, this page reviews what happened against {team['opponent']} and what can carry into next season.")

elif page == "First-Round Review":
    matchup_title(favorite_team)
    st.subheader("First-Round Matchup Review")
    st.write(f"Series: {team['seed']} {favorite_team} vs {TEAM_PROFILES[team['previous_opponent']]['seed']} {team['previous_opponent']}")
    st.write(f"Result: **{team['series_result']}**")

    scores = FIRST_ROUND_GAME_SCORES.get(favorite_team)
    if scores:
        st.subheader("Game-by-Game Scores")
        st.dataframe(pd.DataFrame(scores), use_container_width=True, hide_index=True)
    else:
        st.info("Detailed game-by-game scores are not loaded yet for this team. The player tracker can still pull official player playoff logs from nba_api when available.")

    st.subheader("What Went Right")
    for x in team["strengths"]:
        st.success(x)
    st.subheader("What To Improve")
    for x in team["concerns"]:
        st.warning(x)
    if team["status"] == "Eliminated":
        st.info(f"Next-season outlook for {favorite_team}: build on the positives, address the concerns, and improve the playoff matchup weaknesses that showed up in Round 1.")

elif page == "Live Game Center":
    matchup_title(favorite_team)
    st.subheader("Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_game_refresh")
        st.caption("Live Game Center refreshes every 30 seconds.")
    else:
        st.warning("Add streamlit-autorefresh to requirements.txt for automatic 30-second refresh.")

    if not NBA_API_AVAILABLE:
        st.error("nba_api is not available. Add nba_api to requirements.txt and redeploy.")
    else:
        live_game = find_team_live_game(favorite_team)
        if not live_game:
            st.warning("No live or scheduled game found for this team today. When the team is playing, this page will show score, status, and live probability.")
        else:
            home = live_game.get("homeTeam", {})
            away = live_game.get("awayTeam", {})
            home_name = home.get("teamName", "Home")
            away_name = away.get("teamName", "Away")
            home_score = int(home.get("score", 0) or 0)
            away_score = int(away.get("score", 0) or 0)
            status_text = live_game.get("gameStatusText", "Unknown status")
            st.write(f"### {away_name} at {home_name}")
            st.write(f"**Game Status:** {status_text}")
            c1, c2 = st.columns(2)
            c1.metric(away_name, away_score)
            c2.metric(home_name, home_score)

            alias = TEAM_ALIASES[favorite_team]
            is_home = home.get("teamTricode") == alias
            team_score = home_score if is_home else away_score
            opp_score = away_score if is_home else home_score
            margin = team_score - opp_score
            try:
                quarter = int(live_game.get("period", 1))
            except Exception:
                quarter = 1
            heuristic = estimate_win_probability(margin, quarter, is_home, team["status"])
            model_prob = statsmodels_probability(margin, quarter, is_home)
            final_prob = model_prob if model_prob is not None else heuristic
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{favorite_team} Win Probability", f"{final_prob}%")
            c2.metric("Score Margin", margin)
            c3.metric("Quarter", quarter)
            fig = px.pie(pd.DataFrame({"Outcome": [f"{favorite_team} wins", "Opponent wins"], "Probability": [final_prob, 100-final_prob]}), names="Outcome", values="Probability")
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("AI Live Game Read")
            if margin >= 10 and quarter >= 4:
                st.success(f"This is extremely favorable for {favorite_team}. A double-digit lead in the fourth quarter usually means the team is in control unless turnovers or foul trouble change the game.")
            elif margin >= 10:
                st.success(f"{favorite_team} is off to a very strong stretch. The offense or defense is creating real separation. The next goal is to keep the opponent from making a quick run.")
            elif margin >= 1:
                st.info(f"{favorite_team} has the edge right now. The key is extending the lead through stops, rebounds, and efficient shots.")
            elif margin == 0:
                st.warning("The game is tied. This is still a swing point. The next few possessions can change the win probability quickly.")
            elif margin >= -6:
                st.warning(f"{favorite_team} is trailing but very much alive. A short run or defensive adjustment can flip the game.")
            else:
                st.error(f"{favorite_team} is in a tough spot. They need stops, better shot quality, and a momentum shift.")

elif page == "Player Playoff Tracker":
    matchup_title(favorite_team)
    st.subheader("Official Player Playoff Game Logs")
    player = st.selectbox("Choose player", selected_roster(favorite_team))
    season = st.selectbox("Choose season", ["2025-26", "2024-25", "2023-24"], index=0)
    if not NBA_API_AVAILABLE:
        st.error("nba_api is not available. Add nba_api to requirements.txt.")
    else:
        pid = get_player_id(player)
        if pid is None:
            st.warning(f"Could not find NBA player ID for {player}.")
        else:
            logs = get_real_playoff_logs(pid, season)
            if logs.empty:
                st.warning(f"No official playoff game logs found yet for {player} in {season}.")
            else:
                display_cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "PLUS_MINUS"] if c in logs.columns]
                st.dataframe(logs[display_cols], use_container_width=True, hide_index=True)
                stat_options = [s for s in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS", "MIN"] if s in logs.columns]
                stat = st.selectbox("Choose stat", stat_options)
                chart = logs.copy()
                chart["Game Number"] = range(1, len(chart) + 1)
                fig = px.line(chart, x="Game Number", y=stat, markers=True, hover_data=["GAME_DATE", "MATCHUP", "WL"], title=f"{player} {stat} — {season} Playoffs")
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("AI Player Insight")
                avg = chart[stat].mean()
                st.info(f"{player}'s average {stat} is {avg:.2f} in the loaded playoff games. From the {favorite_team} perspective, this matters because it shows whether his role is helping the team win its current matchup.")

elif page == "Matchup Lineups":
    matchup_title(favorite_team)
    opponent = team["opponent"]
    if opponent not in TEAM_PROFILES:
        st.warning("Opponent profile not loaded.")
    else:
        opp = TEAM_PROFILES[opponent]
        st.subheader("Starting Lineup Comparison")
        positions = ["PG", "SG", "SF", "PF", "C"]
        rows = []
        for i, pos in enumerate(positions):
            rows.append({"Position": pos, favorite_team: team["starters"][i], opponent: opp["starters"][i], "Analysis": f"This matchup is viewed from the {favorite_team} perspective. Watch efficiency, fouls, rebounding, and late-game execution."})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.subheader("Main Subs")
        bench_rows = []
        for p in team["subs"]:
            bench_rows.append({"Team": favorite_team, "Player": p, "Role": "Bench role: stabilize minutes, defend, avoid turnovers, and provide scoring or energy."})
        for p in opp["subs"]:
            bench_rows.append({"Team": opponent, "Player": p, "Role": "Opponent bench role: affects matchup depth and non-starter minutes."})
        st.dataframe(pd.DataFrame(bench_rows), use_container_width=True, hide_index=True)

elif page == "Legacy Tracker":
    matchup_title(favorite_team)
    st.subheader("Team-Specific Legacy Tracker")
    player = st.selectbox("Choose starter", team["starters"])
    st.write(f"This legacy tracker is written from the {favorite_team} perspective. It uses the selected player's current role, playoff advancement, and performance to frame how the run changes his team legacy.")
    points = st.slider("Playoff scoring average", 0, 45, 20)
    rebounds = st.slider("Playoff rebounding average", 0, 20, 5)
    assists = st.slider("Playoff assists average", 0, 15, 4)
    series_wins = st.slider("Series won this playoff run", 0, 4, 1 if team["status"] == "Active" else 0)
    score = min(100, round(50 + points*0.55 + rebounds*0.6 + assists*0.45 + series_wins*10, 1))
    st.metric("Live Legacy Impact Score", score)
    if team["status"] == "Active":
        st.success(f"If {player} helps {favorite_team} win another round, his franchise legacy rises because deep playoff runs become part of team history.")
    else:
        st.info(f"Because {favorite_team} is eliminated, the legacy interpretation focuses on what {player} showed in Round 1 and what it means for next season.")

elif page == "Other Series Watch":
    matchup_title(favorite_team)
    st.subheader("All 2026 Playoff Teams")
    rows = []
    for name, p in TEAM_PROFILES.items():
        rows.append({"Team": name, "Conference": p["conference"], "Seed": p["seed"], "Status": p["status"], "Round": p["round"], "Opponent": p["opponent"], "Result": p["series_result"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "AI Prediction Center":
    matchup_title(favorite_team)
    if team["status"] == "Eliminated":
        st.error(f"{favorite_team} is eliminated, so future playoff probability is 0%.")
    else:
        st.subheader("Manual Probability Simulator")
        margin = st.slider("Current score margin for selected team", -30, 30, 0)
        quarter = st.slider("Current quarter", 1, 4, 2)
        is_home = st.checkbox("Is selected team home?", value=True)
        heuristic = estimate_win_probability(margin, quarter, is_home, team["status"])
        model = statsmodels_probability(margin, quarter, is_home)
        final = model if model is not None else heuristic
        st.metric("Estimated Win Probability", f"{final}%")
        fig = px.pie(pd.DataFrame({"Outcome": [f"{favorite_team} wins", "Opponent wins"], "Probability": [final, 100-final]}), names="Outcome", values="Probability")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | Bracket data model + live NBA API layer")
