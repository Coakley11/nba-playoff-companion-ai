import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Optional packages. The app still runs if one fails.
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
    from nba_api.stats.endpoints import playergamelog
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Daniel Cohen — NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 NBA Playoff-only fan companion app with live-game tracking and team-specific analysis")

# ---------------------------------------------------
# TEAM LOGOS AND ALIASES
# ---------------------------------------------------

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

TEAM_LOGOS = {
    "New York Knicks": "https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg",
    "Philadelphia 76ers": "https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg",
    "Detroit Pistons": "https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg",
    "Cleveland Cavaliers": "https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg",
    "Toronto Raptors": "https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg",
    "Boston Celtics": "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
    "Atlanta Hawks": "https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg",
    "Orlando Magic": "https://cdn.nba.com/logos/nba/1610612753/primary/L/logo.svg",
    "Oklahoma City Thunder": "https://cdn.nba.com/logos/nba/1610612760/primary/L/logo.svg",
    "Los Angeles Lakers": "https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg",
    "San Antonio Spurs": "https://cdn.nba.com/logos/nba/1610612759/primary/L/logo.svg",
    "Minnesota Timberwolves": "https://cdn.nba.com/logos/nba/1610612750/primary/L/logo.svg",
    "Denver Nuggets": "https://cdn.nba.com/logos/nba/1610612743/primary/L/logo.svg",
    "Houston Rockets": "https://cdn.nba.com/logos/nba/1610612745/primary/L/logo.svg",
    "Portland Trail Blazers": "https://cdn.nba.com/logos/nba/1610612757/primary/L/logo.svg",
    "Phoenix Suns": "https://cdn.nba.com/logos/nba/1610612756/primary/L/logo.svg",
}

# ---------------------------------------------------
# TEAM PROFILES
# ---------------------------------------------------

TEAM_PROFILES = {
    "New York Knicks": {
        "conference": "East", "seed": 3, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "Philadelphia 76ers", "opponent_seed": 7,
        "series_label": "3 New York Knicks vs 7 Philadelphia 76ers",
        "series_result": "Defeated Atlanta Hawks in the first round",
        "current_game_focus": "Game 1",
        "series_probability": 58, "game_probability": 61, "most_likely": "Knicks in 6",
        "starters": ["Jalen Brunson", "Mikal Bridges", "OG Anunoby", "Josh Hart", "Karl-Anthony Towns"],
        "subs": ["Miles McBride", "Mitchell Robinson", "Jordan Clarkson", "Landry Shamet", "Jose Alvarado"],
        "strengths": ["Brunson half-court creation", "physical rebounding", "wing defense", "MSG home-court energy", "Towns spacing"],
        "concerns": ["Embiid foul pressure", "bench stability", "overreliance on Brunson", "three-point variance"],
        "recap": "The Knicks advanced and are now trying to turn a strong first round into a deeper playoff run.",
        "next_year": "Keep building around Brunson, Towns, wing defense, and playoff toughness."
    },
    "Philadelphia 76ers": {
        "conference": "East", "seed": 7, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "New York Knicks", "opponent_seed": 3,
        "series_label": "7 Philadelphia 76ers vs 3 New York Knicks",
        "series_result": "Defeated Boston Celtics in the first round",
        "current_game_focus": "Game 1",
        "series_probability": 42, "game_probability": 39, "most_likely": "Knicks in 6",
        "starters": ["Tyrese Maxey", "VJ Edgecombe", "Kelly Oubre Jr.", "Paul George", "Joel Embiid"],
        "subs": ["Andre Drummond", "Quentin Grimes", "Kyle Lowry", "Eric Gordon", "Caleb Martin"],
        "strengths": ["Embiid interior dominance", "Maxey speed", "free-throw pressure", "star scoring upside"],
        "concerns": ["Embiid health", "bench consistency", "Knicks rebounding", "turnovers under pressure"],
        "recap": "Philadelphia survived Boston and now gets a physical second-round matchup with New York.",
        "next_year": "Continue maximizing Embiid and Maxey while strengthening depth and wing defense."
    },
    "Detroit Pistons": {
        "conference": "East", "seed": 1, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "Cleveland Cavaliers or Toronto Raptors", "opponent_seed": "4/5",
        "series_label": "1 Detroit Pistons vs 4/5 Cavaliers or Raptors",
        "series_result": "Defeated Orlando Magic in the first round",
        "current_game_focus": "Game 1 pending opponent",
        "series_probability": 54, "game_probability": 56, "most_likely": "Pistons in 7",
        "starters": ["Cade Cunningham", "Jaden Ivey", "Ausar Thompson", "Tobias Harris", "Jalen Duren"],
        "subs": ["Marcus Sasser", "Simone Fontecchio", "Isaiah Stewart", "Malik Beasley", "Ron Holland"],
        "strengths": ["Cade's playmaking", "young athleticism", "rebounding", "transition pressure"],
        "concerns": ["playoff inexperience", "late-game execution", "half-court spacing"],
        "recap": "Detroit advanced with momentum and now has a chance to prove its young core belongs deep in the playoffs.",
        "next_year": "Keep building around Cade, Duren, and the young defensive core."
    },
    "Cleveland Cavaliers": {
        "conference": "East", "seed": 4, "status": "Pending", "mode": "pending",
        "round": "First Round Pending", "opponent": "Toronto Raptors", "opponent_seed": 5,
        "series_label": "4 Cleveland Cavaliers vs 5 Toronto Raptors",
        "series_result": "First-round series pending",
        "current_game_focus": "Deciding game",
        "series_probability": 50, "game_probability": 50, "most_likely": "Pending",
        "starters": ["Donovan Mitchell", "Darius Garland", "Max Strus", "Evan Mobley", "Jarrett Allen"],
        "subs": ["Caris LeVert", "Isaac Okoro", "Georges Niang", "Dean Wade", "Sam Merrill"],
        "strengths": ["Mitchell scoring", "Mobley and Allen defense", "guard creation"],
        "concerns": ["offensive droughts", "health", "closing consistency"],
        "recap": "Cleveland is still fighting to advance.",
        "next_year": "Build more reliable playoff offense around Mitchell, Garland, and Mobley."
    },
    "Toronto Raptors": {
        "conference": "East", "seed": 5, "status": "Pending", "mode": "pending",
        "round": "First Round Pending", "opponent": "Cleveland Cavaliers", "opponent_seed": 4,
        "series_label": "5 Toronto Raptors vs 4 Cleveland Cavaliers",
        "series_result": "First-round series pending",
        "current_game_focus": "Deciding game",
        "series_probability": 50, "game_probability": 50, "most_likely": "Pending",
        "starters": ["Immanuel Quickley", "RJ Barrett", "Gradey Dick", "Scottie Barnes", "Jakob Poeltl"],
        "subs": ["Bruce Brown", "Kelly Olynyk", "Ochai Agbaji", "Chris Boucher", "Davion Mitchell"],
        "strengths": ["athletic wings", "transition play", "Scottie Barnes versatility"],
        "concerns": ["half-court offense", "shooting variance", "late-game shot creation"],
        "recap": "Toronto is still fighting for a second-round spot.",
        "next_year": "Keep growing the Barnes-Barrett-Quickley core and improve half-court offense."
    },
    "Boston Celtics": {
        "conference": "East", "seed": 2, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "Philadelphia 76ers", "opponent_seed": 7,
        "series_label": "2 Boston Celtics vs 7 Philadelphia 76ers",
        "series_result": "Lost to Philadelphia 76ers",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Jayson Tatum", "Jaylen Brown", "Derrick White", "Jrue Holiday", "Kristaps Porzingis"],
        "subs": ["Al Horford", "Payton Pritchard", "Sam Hauser", "Luke Kornet", "Xavier Tillman"],
        "strengths": ["wing talent", "spacing", "championship experience"],
        "concerns": ["late-series execution", "injury concerns", "offensive stagnation"],
        "recap": "Boston's season ended early after Philadelphia controlled enough late-series possessions.",
        "next_year": "Boston needs to reestablish its late-game offense and health profile next season."
    },
    "Atlanta Hawks": {
        "conference": "East", "seed": 6, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "New York Knicks", "opponent_seed": 3,
        "series_label": "6 Atlanta Hawks vs 3 New York Knicks",
        "series_result": "Lost to New York Knicks",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Trae Young", "Dyson Daniels", "Zaccharie Risacher", "Jalen Johnson", "Onyeka Okongwu"],
        "subs": ["Bogdan Bogdanovic", "De'Andre Hunter", "Clint Capela", "Vit Krejci", "Kobe Bufkin"],
        "strengths": ["Trae Young creation", "pace", "young wing upside"],
        "concerns": ["defense", "rebounding", "shot selection", "physical matchup with New York"],
        "recap": "Atlanta had moments of shot creation but could not consistently handle New York's physicality and late-game execution.",
        "next_year": "The Hawks should build around improved defense, more size, and a clearer late-game identity around Trae and Jalen Johnson."
    },
    "Orlando Magic": {
        "conference": "East", "seed": 8, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "Detroit Pistons", "opponent_seed": 1,
        "series_label": "8 Orlando Magic vs 1 Detroit Pistons",
        "series_result": "Lost to Detroit Pistons",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Jalen Suggs", "Franz Wagner", "Paolo Banchero", "Wendell Carter Jr.", "Goga Bitadze"],
        "subs": ["Cole Anthony", "Anthony Black", "Jonathan Isaac", "Moritz Wagner", "Gary Harris"],
        "strengths": ["young forwards", "defensive size", "physicality"],
        "concerns": ["shooting", "late-game offense", "closing a series"],
        "recap": "Orlando pushed the series but could not finish the job.",
        "next_year": "The Magic need more shooting and steadier late-game offense around Paolo and Franz."
    },
    "Oklahoma City Thunder": {
        "conference": "West", "seed": 1, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "Los Angeles Lakers", "opponent_seed": 4,
        "series_label": "1 Oklahoma City Thunder vs 4 Los Angeles Lakers",
        "series_result": "Defeated Phoenix Suns in the first round",
        "current_game_focus": "Game 1",
        "series_probability": 55, "game_probability": 57, "most_likely": "Thunder in 7",
        "starters": ["Shai Gilgeous-Alexander", "Lu Dort", "Jalen Williams", "Chet Holmgren", "Josh Giddey"],
        "subs": ["Isaiah Joe", "Cason Wallace", "Aaron Wiggins", "Kenrich Williams", "Jaylin Williams"],
        "strengths": ["SGA control", "spacing", "defensive length", "pace"],
        "concerns": ["Lakers size", "physicality", "late-game playoff pressure"],
        "recap": "OKC advanced and now faces a more experienced Lakers team.",
        "next_year": "OKC's core should remain one of the league's best long-term foundations."
    },
    "Los Angeles Lakers": {
        "conference": "West", "seed": 4, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "Oklahoma City Thunder", "opponent_seed": 1,
        "series_label": "4 Los Angeles Lakers vs 1 Oklahoma City Thunder",
        "series_result": "Defeated Houston Rockets in the first round",
        "current_game_focus": "Game 1",
        "series_probability": 45, "game_probability": 43, "most_likely": "Thunder in 7",
        "starters": ["D'Angelo Russell", "Austin Reaves", "LeBron James", "Rui Hachimura", "Anthony Davis"],
        "subs": ["Gabe Vincent", "Jarred Vanderbilt", "Max Christie", "Jaxson Hayes", "Taurean Prince"],
        "strengths": ["LeBron experience", "AD defense", "paint pressure", "playoff IQ"],
        "concerns": ["age", "transition defense", "guard containment", "depth"],
        "recap": "The Lakers advanced and now need to slow OKC's speed and spacing.",
        "next_year": "The Lakers need to balance LeBron's window with younger depth and shooting."
    },
    "San Antonio Spurs": {
        "conference": "West", "seed": 2, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "Minnesota Timberwolves", "opponent_seed": 3,
        "series_label": "2 San Antonio Spurs vs 3 Minnesota Timberwolves",
        "series_result": "Defeated Portland Trail Blazers in the first round",
        "current_game_focus": "Game 1",
        "series_probability": 48, "game_probability": 49, "most_likely": "Timberwolves in 7",
        "starters": ["Stephon Castle", "Devin Vassell", "Keldon Johnson", "Jeremy Sochan", "Victor Wembanyama"],
        "subs": ["Tre Jones", "Zach Collins", "Julian Champagnie", "Malaki Branham", "Blake Wesley"],
        "strengths": ["Wembanyama defense", "length", "shot blocking", "young upside"],
        "concerns": ["playoff experience", "physicality", "late-game execution"],
        "recap": "San Antonio advanced behind its young core and Wembanyama's impact.",
        "next_year": "The Spurs should continue building around Wembanyama with shooting and guard stability."
    },
    "Minnesota Timberwolves": {
        "conference": "West", "seed": 3, "status": "Active", "mode": "preview",
        "round": "Second Round", "opponent": "San Antonio Spurs", "opponent_seed": 2,
        "series_label": "3 Minnesota Timberwolves vs 2 San Antonio Spurs",
        "series_result": "Defeated Denver Nuggets in the first round",
        "current_game_focus": "Game 1",
        "series_probability": 52, "game_probability": 51, "most_likely": "Timberwolves in 7",
        "starters": ["Mike Conley", "Anthony Edwards", "Jaden McDaniels", "Naz Reid", "Rudy Gobert"],
        "subs": ["Nickeil Alexander-Walker", "Donte DiVincenzo", "Kyle Anderson", "Rob Dillingham", "Josh Minott"],
        "strengths": ["Anthony Edwards scoring", "elite defense", "size", "physicality"],
        "concerns": ["late-game offense", "spacing", "turnovers"],
        "recap": "Minnesota advanced by knocking out Denver and brings defensive force into round two.",
        "next_year": "The Wolves can keep building around Edwards and an elite defensive identity."
    },
    "Denver Nuggets": {
        "conference": "West", "seed": 6, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "Minnesota Timberwolves", "opponent_seed": 3,
        "series_label": "6 Denver Nuggets vs 3 Minnesota Timberwolves",
        "series_result": "Lost to Minnesota Timberwolves",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Jamal Murray", "Christian Braun", "Michael Porter Jr.", "Aaron Gordon", "Nikola Jokic"],
        "subs": ["Reggie Jackson", "Peyton Watson", "Julian Strawther", "Zeke Nnaji", "DeAndre Jordan"],
        "strengths": ["Jokic playmaking", "chemistry", "half-court offense"],
        "concerns": ["bench depth", "athletic matchups", "defensive pressure"],
        "recap": "Denver's playoff run ended against Minnesota's physical defense.",
        "next_year": "The Nuggets need more reliable depth and athletic support around Jokic."
    },
    "Houston Rockets": {
        "conference": "West", "seed": 5, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "Los Angeles Lakers", "opponent_seed": 4,
        "series_label": "5 Houston Rockets vs 4 Los Angeles Lakers",
        "series_result": "Lost to Los Angeles Lakers",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Fred VanVleet", "Jalen Green", "Dillon Brooks", "Jabari Smith Jr.", "Alperen Sengun"],
        "subs": ["Amen Thompson", "Tari Eason", "Cam Whitmore", "Steven Adams", "Jeff Green"],
        "strengths": ["athleticism", "defense", "young upside"],
        "concerns": ["half-court offense", "playoff experience", "shot selection"],
        "recap": "Houston gained playoff experience but could not overcome the Lakers' stars.",
        "next_year": "The Rockets should keep building half-court offense and late-game reliability."
    },
    "Portland Trail Blazers": {
        "conference": "West", "seed": 7, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "San Antonio Spurs", "opponent_seed": 2,
        "series_label": "7 Portland Trail Blazers vs 2 San Antonio Spurs",
        "series_result": "Lost to San Antonio Spurs",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Scoot Henderson", "Anfernee Simons", "Shaedon Sharpe", "Jerami Grant", "Deandre Ayton"],
        "subs": ["Toumani Camara", "Matisse Thybulle", "Robert Williams III", "Kris Murray", "Dalano Banton"],
        "strengths": ["young guards", "athleticism", "future upside"],
        "concerns": ["defense", "experience", "frontcourt consistency"],
        "recap": "Portland's young core got playoff experience but could not match San Antonio's size and Wembanyama effect.",
        "next_year": "Portland should focus on defensive growth and defining roles around Scoot and Sharpe."
    },
    "Phoenix Suns": {
        "conference": "West", "seed": 8, "status": "Eliminated", "mode": "recap",
        "round": "First Round", "opponent": "Oklahoma City Thunder", "opponent_seed": 1,
        "series_label": "8 Phoenix Suns vs 1 Oklahoma City Thunder",
        "series_result": "Lost to Oklahoma City Thunder",
        "current_game_focus": "Season recap",
        "series_probability": 0, "game_probability": 0, "most_likely": "Season over",
        "starters": ["Bradley Beal", "Devin Booker", "Grayson Allen", "Kevin Durant", "Jusuf Nurkic"],
        "subs": ["Eric Gordon", "Royce O'Neale", "Bol Bol", "Drew Eubanks", "Josh Okogie"],
        "strengths": ["shot creation", "star scoring", "midrange offense"],
        "concerns": ["depth", "defense", "age", "health"],
        "recap": "Phoenix's star scoring was not enough against OKC's younger, faster, deeper team.",
        "next_year": "The Suns need better depth, defense, and lineup balance around their stars."
    },
}

# ---------------------------------------------------
# SCHEDULES AND SERIES SCORES
# ---------------------------------------------------

SERIES_SCHEDULES = {
    "New York Knicks": pd.DataFrame([
        {"Game": "Game 1", "Date": "Mon, May 4", "Time": "8:00 PM ET", "Matchup": "76ers at Knicks", "TV": "NBC / Peacock"},
        {"Game": "Game 2", "Date": "Wed, May 6", "Time": "7:00 PM ET", "Matchup": "76ers at Knicks", "TV": "ESPN"},
        {"Game": "Game 3", "Date": "Fri, May 8", "Time": "7:00 PM ET", "Matchup": "Knicks at 76ers", "TV": "Prime Video"},
        {"Game": "Game 4", "Date": "Sun, May 10", "Time": "3:30 PM ET", "Matchup": "Knicks at 76ers", "TV": "ABC"},
        {"Game": "Game 5", "Date": "Tue, May 12", "Time": "TBD", "Matchup": "76ers at Knicks", "TV": "TBD"},
        {"Game": "Game 6", "Date": "Thu, May 14", "Time": "TBD", "Matchup": "Knicks at 76ers", "TV": "TBD"},
        {"Game": "Game 7", "Date": "Sun, May 17", "Time": "TBD", "Matchup": "76ers at Knicks", "TV": "TBD"},
    ]),
    "Philadelphia 76ers": pd.DataFrame([
        {"Game": "Game 1", "Date": "Mon, May 4", "Time": "8:00 PM ET", "Matchup": "76ers at Knicks", "TV": "NBC / Peacock"},
        {"Game": "Game 2", "Date": "Wed, May 6", "Time": "7:00 PM ET", "Matchup": "76ers at Knicks", "TV": "ESPN"},
        {"Game": "Game 3", "Date": "Fri, May 8", "Time": "7:00 PM ET", "Matchup": "Knicks at 76ers", "TV": "Prime Video"},
        {"Game": "Game 4", "Date": "Sun, May 10", "Time": "3:30 PM ET", "Matchup": "Knicks at 76ers", "TV": "ABC"},
        {"Game": "Game 5", "Date": "Tue, May 12", "Time": "TBD", "Matchup": "76ers at Knicks", "TV": "TBD"},
        {"Game": "Game 6", "Date": "Thu, May 14", "Time": "TBD", "Matchup": "Knicks at 76ers", "TV": "TBD"},
        {"Game": "Game 7", "Date": "Sun, May 17", "Time": "TBD", "Matchup": "76ers at Knicks", "TV": "TBD"},
    ]),
}

FIRST_ROUND_SCOREBOARDS = {
    "Atlanta Hawks": pd.DataFrame([
        {"Game": 1, "Matchup": "Hawks at Knicks", "Hawks": 104, "Knicks": 113, "Result": "Loss"},
        {"Game": 2, "Matchup": "Hawks at Knicks", "Hawks": 108, "Knicks": 119, "Result": "Loss"},
        {"Game": 3, "Matchup": "Knicks at Hawks", "Hawks": 116, "Knicks": 109, "Result": "Win"},
        {"Game": 4, "Matchup": "Knicks at Hawks", "Hawks": 101, "Knicks": 110, "Result": "Loss"},
        {"Game": 5, "Matchup": "Hawks at Knicks", "Hawks": 107, "Knicks": 121, "Result": "Loss"},
    ]),
    "Boston Celtics": pd.DataFrame([
        {"Game": 1, "Matchup": "76ers at Celtics", "Celtics": 111, "76ers": 106, "Result": "Win"},
        {"Game": 2, "Matchup": "76ers at Celtics", "Celtics": 103, "76ers": 109, "Result": "Loss"},
        {"Game": 3, "Matchup": "Celtics at 76ers", "Celtics": 98, "76ers": 104, "Result": "Loss"},
        {"Game": 4, "Matchup": "Celtics at 76ers", "Celtics": 115, "76ers": 110, "Result": "Win"},
        {"Game": 5, "Matchup": "76ers at Celtics", "Celtics": 101, "76ers": 108, "Result": "Loss"},
        {"Game": 6, "Matchup": "Celtics at 76ers", "Celtics": 112, "76ers": 105, "Result": "Win"},
        {"Game": 7, "Matchup": "76ers at Celtics", "Celtics": 99, "76ers": 107, "Result": "Loss"},
    ]),
    "Orlando Magic": pd.DataFrame([
        {"Game": 1, "Matchup": "Magic at Pistons", "Magic": 92, "Pistons": 103, "Result": "Loss"},
        {"Game": 2, "Matchup": "Magic at Pistons", "Magic": 105, "Pistons": 99, "Result": "Win"},
        {"Game": 3, "Matchup": "Pistons at Magic", "Magic": 111, "Pistons": 107, "Result": "Win"},
        {"Game": 4, "Matchup": "Pistons at Magic", "Magic": 101, "Pistons": 96, "Result": "Win"},
        {"Game": 5, "Matchup": "Magic at Pistons", "Magic": 95, "Pistons": 110, "Result": "Loss"},
        {"Game": 6, "Matchup": "Pistons at Magic", "Magic": 98, "Pistons": 106, "Result": "Loss"},
        {"Game": 7, "Matchup": "Magic at Pistons", "Magic": 100, "Pistons": 108, "Result": "Loss"},
    ]),
}

# For teams without scoreboards yet, create a simple placeholder series table.
for _team, _profile in TEAM_PROFILES.items():
    if _profile["status"] == "Eliminated" and _team not in FIRST_ROUND_SCOREBOARDS:
        FIRST_ROUND_SCOREBOARDS[_team] = pd.DataFrame([
            {"Game": 1, "Matchup": f"{_team} vs {_profile['opponent']}", _team: 0, _profile["opponent"]: 0, "Result": "Series data pending"}
        ])

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def profile(team_name):
    return TEAM_PROFILES[team_name]


def opponent_name(team_name):
    return profile(team_name)["opponent"]


def get_team_players(team_name):
    p = profile(team_name)
    return p["starters"] + p["subs"]


def matchup_header(team_name):
    p = profile(team_name)
    opponent = p["opponent"]

    col1, col2, col3 = st.columns([1, 2.8, 1])
    with col1:
        if team_name in TEAM_LOGOS:
            st.image(TEAM_LOGOS[team_name], width=120)
        st.markdown(f"**{p['seed']} {team_name}**")

    with col2:
        st.markdown(
            f"<h1 style='text-align:center;'>{p['series_label']}</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h3 style='text-align:center;'>{p['round']} — {p['current_game_focus']}</h3>",
            unsafe_allow_html=True
        )

    with col3:
        if opponent in TEAM_LOGOS:
            st.image(TEAM_LOGOS[opponent], width=120)
        st.markdown(f"**{p['opponent_seed']} {opponent}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conference", p["conference"])
    c2.metric("Status", p["status"])
    c3.metric("Series/Recap", p["round"])
    c4.metric("Most Likely", p["most_likely"])
    st.info(p["series_result"])


def team_strengths_concerns(team_name):
    p = profile(team_name)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"What is going right for {team_name}")
        for item in p["strengths"]:
            st.success(item)
    with c2:
        st.subheader("Main concerns")
        for item in p["concerns"]:
            st.warning(item)


def estimate_win_probability(score_margin, quarter, is_home, status, time_remaining_seconds=None):
    if status == "Eliminated":
        return 0

    base = 52 if status in ["Active", "Pending"] else 50
    home_bonus = 3 if is_home else 0
    quarter = max(1, min(4, int(quarter or 1)))

    # Score margin matters more later in the game.
    leverage = {1: 1.6, 2: 2.0, 3: 2.6, 4: 3.6}.get(quarter, 2.0)
    raw = base + score_margin * leverage + home_bonus

    # If late fourth quarter, make big leads extremely decisive.
    if quarter >= 4 and time_remaining_seconds is not None:
        if time_remaining_seconds <= 120 and score_margin >= 10:
            raw = max(raw, 95)
        elif time_remaining_seconds <= 300 and score_margin >= 10:
            raw = max(raw, 90)
        elif time_remaining_seconds <= 120 and score_margin <= -10:
            raw = min(raw, 5)

    return int(max(1, min(99, round(raw))))


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
        model = sm.Logit(train["won"], X).fit(disp=False)
        test = pd.DataFrame({
            "score_margin": [score_margin],
            "quarter": [quarter],
            "is_home": [1 if is_home else 0],
        })
        test = sm.add_constant(test, has_constant="add")
        return int(round(float(model.predict(test)[0]) * 100))
    except Exception:
        return None


@st.cache_data(ttl=30)
def get_live_scoreboard():
    if not NBA_LIVE_AVAILABLE:
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


def parse_game_clock_seconds(game_clock):
    # NBA live API may return strings like PT04M32.00S or 04:32 depending on source.
    if not game_clock:
        return None
    try:
        text = str(game_clock)
        if text.startswith("PT"):
            text = text.replace("PT", "").replace("S", "")
            minutes = 0
            seconds = 0
            if "M" in text:
                m_part, s_part = text.split("M")
                minutes = int(float(m_part or 0))
                seconds = int(float(s_part or 0))
            return minutes * 60 + seconds
        if ":" in text:
            m, s = text.split(":")[:2]
            return int(m) * 60 + int(float(s))
    except Exception:
        return None
    return None


def live_ai_read(team_name, score_margin, quarter, probability, team_score, opp_score, is_home, time_left_seconds=None):
    p = profile(team_name)
    opponent = p["opponent"]
    perspective = f"From a {team_name} fan perspective"

    if score_margin >= 10:
        lead_text = f"{perspective}, this is very favorable. {team_name} is ahead by double digits, which usually means they are controlling the flow of the game."
    elif score_margin >= 5:
        lead_text = f"{perspective}, this is a good position. A {score_margin}-point lead gives them some cushion in a playoff game."
    elif score_margin >= 1:
        lead_text = f"{perspective}, {team_name} is slightly ahead. The game is still fragile, but the current direction is positive."
    elif score_margin == 0:
        lead_text = f"{perspective}, the game is tied. The next run matters, especially if the stars can control the next few possessions."
    elif score_margin >= -5:
        lead_text = f"{perspective}, this is still very winnable. They are trailing, but the margin is small enough that one run can flip the game."
    else:
        lead_text = f"{perspective}, this is a difficult spot. They need stops, better shot quality, and a momentum swing."

    late_text = ""
    if quarter >= 4 and time_left_seconds is not None:
        if time_left_seconds <= 120 and score_margin >= 10:
            late_text = f" With under two minutes left and a double-digit lead, teams in this situation usually have an extremely high chance of winning. The app estimates {probability}% for {team_name}."
        elif time_left_seconds <= 300 and score_margin >= 8:
            late_text = f" Late in the fourth quarter, this is strongly favorable. The priority is avoiding turnovers and not fouling shooters."
        elif time_left_seconds <= 300 and score_margin <= -8:
            late_text = f" Late in the fourth quarter, the path is narrow. They need quick stops, threes, or free throws to make it realistic."

    if team_score >= opp_score + 8:
        trend_text = f"The scoreboard suggests the {team_name} offense and defense are working together: they are either scoring efficiently, getting stops, or both."
    elif team_score >= 60 and quarter <= 2:
        trend_text = f"The scoring pace is favorable. If {team_name} is already scoring this well early, it usually means they are getting quality shots or forcing tempo."
    elif opp_score >= team_score + 8:
        trend_text = f"The concern is that {opponent} is dictating too much of the game. {team_name} needs to slow the opponent's best actions and create easier offense."
    else:
        trend_text = f"This is still a possession-by-possession game. Rebounding, turnovers, and fouls will probably decide the next swing."

    keys = "\n".join([f"- {x}" for x in p["strengths"][:3]])
    concerns = "\n".join([f"- {x}" for x in p["concerns"][:3]])

    return f"""
{lead_text}{late_text}

**What appears favorable right now**
{trend_text}

**Team identity factors to watch**
{keys}

**Risks that could turn the game**
{concerns}
"""


@st.cache_data(ttl=3600)
def find_player_id(player_name):
    if not NBA_STATS_AVAILABLE:
        return None
    try:
        matches = nba_players.find_players_by_full_name(player_name)
        if matches:
            # Prefer exact match if possible.
            for p in matches:
                if p.get("full_name", "").lower() == player_name.lower():
                    return p.get("id")
            return matches[0].get("id")
    except Exception:
        return None
    return None


@st.cache_data(ttl=900)
def get_player_playoff_logs(player_name, season_value="2025-26"):
    pid = find_player_id(player_name)
    if not pid or not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    try:
        logs = playergamelog.PlayerGameLog(
            player_id=pid,
            season=season_value,
            season_type_all_star="Playoffs"
        )
        df = logs.get_data_frames()[0]
        return df
    except Exception:
        return pd.DataFrame()


def render_schedule_or_recap(team_name):
    p = profile(team_name)
    if p["mode"] == "preview":
        st.subheader("Series Schedule")
        if team_name in SERIES_SCHEDULES:
            st.dataframe(SERIES_SCHEDULES[team_name], use_container_width=True)
        else:
            st.info("Detailed schedule will appear here once this series is fully set.")
    elif p["mode"] == "recap":
        st.subheader("First-Round Game Results")
        board = FIRST_ROUND_SCOREBOARDS.get(team_name)
        if board is not None:
            st.dataframe(board, use_container_width=True)
        else:
            st.info("Game-by-game scores are not loaded yet for this team.")
    else:
        st.subheader("Series Status")
        st.warning("This team's series is still pending. Once the result is final, this page will switch to preview or recap mode.")


def player_insight(player, stat, avg, team_name):
    p = profile(team_name)
    if "Brunson" in player or "Young" in player or "Mitchell" in player or "Maxey" in player or "Shai" in player or "Edwards" in player:
        return f"{player}'s {stat} tells you how much the offense depends on lead-guard creation. A high average is favorable if turnovers stay manageable."
    if "Towns" in player or "Embiid" in player or "Jokic" in player or "Wembanyama" in player or "Gobert" in player or "Duren" in player:
        return f"{player}'s {stat} should be read through the big-man matchup. Scoring, rebounding, efficiency, and foul pressure can swing the whole series."
    if player in p["subs"]:
        return f"{player}'s role is about stabilizing non-star minutes. Positive production from the bench can change the series margin."
    return f"{player}'s {stat} trend shows whether he is helping {team_name} win his role in the series."

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

favorite_team = st.sidebar.selectbox(
    "Choose your 2026 playoff team",
    list(TEAM_PROFILES.keys()),
    index=list(TEAM_PROFILES.keys()).index("New York Knicks")
)

page = st.sidebar.radio(
    "Choose page",
    [
        "Team Command Center",
        "Live Game Center",
        "Series Preview / Recap",
        "Matchup Lineups",
        "Player Playoff Tracker",
        "Legacy Tracker",
        "Other Series Watch",
        "Playoff Bracket",
        "AI Prediction Center",
    ]
)

# ---------------------------------------------------
# PAGES
# ---------------------------------------------------

if page == "Team Command Center":
    matchup_header(favorite_team)
    p = profile(favorite_team)

    if p["mode"] == "preview":
        c1, c2, c3 = st.columns(3)
        c1.metric("Series Win Probability", f"{p['series_probability']}%")
        c2.metric("Current Game Win Probability", f"{p['game_probability']}%")
        c3.metric("Most Likely Scenario", p["most_likely"])

        st.subheader(f"{p['current_game_focus']} Preview From the {favorite_team} Perspective")
        st.success(
            f"{favorite_team} is still alive. The app should focus on what has to go right in {p['current_game_focus']}: controlling the team's identity, exploiting opponent weaknesses, and avoiding the concerns listed below."
        )
        render_schedule_or_recap(favorite_team)
        team_strengths_concerns(favorite_team)

    elif p["mode"] == "recap":
        st.error(f"{favorite_team} is out of the playoffs. This page now becomes a first-round recap and next-season outlook.")
        render_schedule_or_recap(favorite_team)
        team_strengths_concerns(favorite_team)
        st.subheader("What went right")
        st.write(p["recap"])
        st.subheader("Going forward to next season")
        st.info(p["next_year"])

    else:
        st.warning(f"{favorite_team}'s first-round result is still pending.")
        render_schedule_or_recap(favorite_team)
        team_strengths_concerns(favorite_team)


elif page == "Live Game Center":
    matchup_header(favorite_team)

    st.subheader("Live Game Center")

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_game_refresh")
        st.caption("Live data refreshes every 30 seconds during games.")
    else:
        st.warning("Install streamlit-autorefresh to enable automatic 30-second refresh.")

    if not NBA_LIVE_AVAILABLE:
        st.error("nba_api live tools are not available. Make sure nba_api is in requirements.txt.")
    else:
        live_game = find_team_live_game(favorite_team)

        if live_game is None:
            st.warning("No live or scheduled game found for this selected team today.")
            st.info("When a game is live, this page will show score, quarter, win probability, and AI-style fan-perspective analysis.")
        else:
            home = live_game.get("homeTeam", {})
            away = live_game.get("awayTeam", {})

            home_name = home.get("teamName", "Home")
            away_name = away.get("teamName", "Away")
            home_tri = home.get("teamTricode", "")
            away_tri = away.get("teamTricode", "")
            home_score = int(home.get("score", 0) or 0)
            away_score = int(away.get("score", 0) or 0)
            status_text = live_game.get("gameStatusText", "Unknown")
            quarter = int(live_game.get("period", 1) or 1)
            clock = live_game.get("gameClock") or live_game.get("clock")
            time_seconds = parse_game_clock_seconds(clock)

            st.write(f"### {away_name} ({away_tri}) at {home_name} ({home_tri})")
            st.write(f"**Status:** {status_text}")
            if clock:
                st.write(f"**Clock:** {clock}")

            c1, c2 = st.columns(2)
            c1.metric(f"{away_name}", away_score)
            c2.metric(f"{home_name}", home_score)

            selected_alias = TEAM_ALIASES.get(favorite_team)
            is_home = home_tri == selected_alias
            team_score = home_score if is_home else away_score
            opp_score = away_score if is_home else home_score
            score_margin = team_score - opp_score

            heuristic_prob = estimate_win_probability(
                score_margin=score_margin,
                quarter=quarter,
                is_home=is_home,
                status=profile(favorite_team)["status"],
                time_remaining_seconds=time_seconds,
            )
            model_prob = statsmodels_probability(score_margin, quarter, is_home)
            final_prob = model_prob if model_prob is not None else heuristic_prob

            c1, c2, c3 = st.columns(3)
            c1.metric(f"{favorite_team} Win Probability", f"{final_prob}%")
            c2.metric("Score Margin", score_margin)
            c3.metric("Quarter", quarter)

            prob_df = pd.DataFrame({
                "Outcome": [f"{favorite_team} Wins", "Opponent Wins"],
                "Probability": [final_prob, 100 - final_prob],
            })
            fig = px.pie(prob_df, names="Outcome", values="Probability", title="Live Win Probability")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("AI Live Game Read")
            st.markdown(live_ai_read(favorite_team, score_margin, quarter, final_prob, team_score, opp_score, is_home, time_seconds))

            st.subheader("What to watch next")
            watch = [
                "Does the selected team win the next 3-4 possessions?",
                "Are turnovers giving the opponent transition chances?",
                "Is the best player getting efficient shots?",
                "Is the defense forcing difficult half-court possessions?",
                "Are foul trouble or bench minutes changing the matchup?",
            ]
            for item in watch:
                st.write(f"• {item}")


elif page == "Series Preview / Recap":
    matchup_header(favorite_team)
    p = profile(favorite_team)

    if p["mode"] == "recap":
        st.subheader("First-Round Recap")
        st.write(p["recap"])
        render_schedule_or_recap(favorite_team)
        st.subheader("What this means for next season")
        st.info(p["next_year"])
    elif p["mode"] == "preview":
        st.subheader(f"{p['current_game_focus']} Preview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Series Probability", f"{p['series_probability']}%")
        c2.metric("Game Probability", f"{p['game_probability']}%")
        c3.metric("Most Likely", p["most_likely"])
        render_schedule_or_recap(favorite_team)
        team_strengths_concerns(favorite_team)
    else:
        st.warning("This series is still pending. The page will switch after the result is final.")
        team_strengths_concerns(favorite_team)


elif page == "Matchup Lineups":
    matchup_header(favorite_team)
    p = profile(favorite_team)
    opponent = p["opponent"]

    st.subheader("Starting Lineup Matchups")

    if opponent in TEAM_PROFILES:
        opp = profile(opponent)
        rows = []
        positions = ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"]
        for i, pos in enumerate(positions):
            team_player = p["starters"][i] if i < len(p["starters"]) else "TBD"
            opp_player = opp["starters"][i] if i < len(opp["starters"]) else "TBD"
            advantage = favorite_team if i in [0, 2] else opponent if i in [3, 4] else "Even"
            rows.append({
                "Position": pos,
                favorite_team: team_player,
                opponent: opp_player,
                "Advantage": advantage,
                "Analysis": f"{team_player} vs {opp_player}: this matchup matters because it affects shot creation, defense, and role execution."
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.subheader("Main Bench / Subs")
        bench_rows = []
        for pl in p["subs"]:
            bench_rows.append({"Team": favorite_team, "Player": pl, "Role": "Bench minutes, defense, spacing, and stability"})
        for pl in opp["subs"]:
            bench_rows.append({"Team": opponent, "Player": pl, "Role": "Bench minutes, matchup flexibility, and scoring support"})
        st.dataframe(pd.DataFrame(bench_rows), use_container_width=True)
    else:
        st.warning("Opponent is not fully set yet, so lineup matchups are pending.")
        st.write("Current possible opponent:", opponent)

    st.subheader("Matchup Summary")
    if p["mode"] == "recap":
        st.info(f"Because {favorite_team} is eliminated, this page explains why the first-round matchups did or did not work.")
    else:
        st.info(f"For {favorite_team}, the key is to turn strengths into repeatable advantages and prevent the opponent from attacking the listed concerns.")


elif page == "Player Playoff Tracker":
    matchup_header(favorite_team)
    st.subheader("Player Playoff Tracker")

    player_pool = get_team_players(favorite_team)
    selected_player = st.selectbox("Choose player", player_pool)
    season = st.selectbox("Choose season", ["2025-26", "2024-25", "2023-24"], index=0)

    logs_df = get_player_playoff_logs(selected_player, season)

    if logs_df.empty:
        st.warning(f"No official nba_api playoff game logs found yet for {selected_player} in {season}.")
        st.info("This can happen if NBA.com has not updated the endpoint, the player did not appear, or the API is temporarily unavailable.")
    else:
        display_cols = [
            "GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV",
            "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "PLUS_MINUS"
        ]
        display_cols = [c for c in display_cols if c in logs_df.columns]
        st.dataframe(logs_df[display_cols], use_container_width=True)

        stat_options = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS", "MIN"]
        stat_options = [s for s in stat_options if s in logs_df.columns]
        selected_stat = st.selectbox("Choose stat", stat_options)

        chart_df = logs_df.copy()
        chart_df = chart_df.iloc[::-1].reset_index(drop=True)
        chart_df["Game Number"] = range(1, len(chart_df) + 1)

        fig = px.line(
            chart_df,
            x="Game Number",
            y=selected_stat,
            markers=True,
            hover_data=[c for c in ["GAME_DATE", "MATCHUP", "WL"] if c in chart_df.columns],
            title=f"{selected_player} {selected_stat} — {season} Playoffs"
        )
        st.plotly_chart(fig, use_container_width=True)

        avg = chart_df[selected_stat].mean()
        best = chart_df[selected_stat].max()
        low = chart_df[selected_stat].min()
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Average {selected_stat}", round(avg, 2))
        c2.metric(f"Best {selected_stat}", round(best, 2))
        c3.metric(f"Lowest {selected_stat}", round(low, 2))

        st.subheader("AI Player Insight")
        st.write(player_insight(selected_player, selected_stat, avg, favorite_team))


elif page == "Legacy Tracker":
    matchup_header(favorite_team)
    p = profile(favorite_team)

    st.subheader(f"{favorite_team} Legacy Tracker")
    selected_player = st.selectbox("Choose starter", p["starters"])

    st.write(f"This page interprets {selected_player}'s legacy from the {favorite_team} perspective.")

    if p["mode"] == "recap":
        st.info(f"Because {favorite_team} is eliminated, legacy analysis focuses on what the series revealed and what can carry into next season.")
    else:
        st.info(f"Because {favorite_team} is still alive, legacy can still rise with each round and each major performance.")

    legacy_df = pd.DataFrame({
        "Outcome This Season": ["Current", "Strong current round", "Conference Finals", "NBA Finals", "Championship", "Finals MVP / team leader"],
        "Legacy Score": [55, 68, 78, 88, 96, 100],
        "Meaning": [
            "Current franchise standing",
            "Improves this playoff narrative",
            "Becomes a defining run",
            "Major historical leap",
            "Permanent franchise memory",
            "Highest legacy boost"
        ]
    })
    st.dataframe(legacy_df, use_container_width=True)
    fig = px.bar(legacy_df, x="Outcome This Season", y="Legacy Score", title=f"{selected_player} Legacy Path")
    st.plotly_chart(fig, use_container_width=True)

    points = st.slider("Current playoff scoring average", 0, 45, 20)
    rebounds = st.slider("Current playoff rebounding average", 0, 20, 5)
    assists = st.slider("Current playoff assists average", 0, 15, 4)
    series_wins = st.slider("Series won this playoff run", 0, 4, 1 if p["mode"] == "preview" else 0)
    score = min(100, round(50 + points * 0.6 + rebounds * 0.6 + assists * 0.5 + series_wins * 10, 1))
    st.metric("Live Legacy Impact Score", score)

    if score >= 90:
        st.success(f"{selected_player} is moving into major franchise-history territory if this performance level continues.")
    elif score >= 75:
        st.success(f"{selected_player}'s legacy is rising. Winning another round would make the run much more meaningful.")
    else:
        st.info(f"{selected_player}'s legacy is still being shaped. The next round or next season can change the interpretation quickly.")


elif page == "Other Series Watch":
    matchup_header(favorite_team)
    st.subheader("2026 Playoff Team Status Board")
    status_df = pd.DataFrame([
        {
            "Team": name,
            "Conference": data["conference"],
            "Seed": data["seed"],
            "Status": data["status"],
            "Round": data["round"],
            "Opponent": data["opponent"],
            "Result": data["series_result"],
        }
        for name, data in TEAM_PROFILES.items()
    ])
    st.dataframe(status_df, use_container_width=True)

    st.subheader(f"How other series affect {favorite_team}")
    if profile(favorite_team)["mode"] == "preview":
        st.write("Other series affect rest, travel, future opponents, injuries, and matchup difficulty.")
    else:
        st.write("Since this team is eliminated or pending, this board helps fans follow the rest of the bracket.")


elif page == "Playoff Bracket":
    st.header("2026 NBA Playoff Bracket")
    bracket_data = pd.DataFrame([
        {"Conference": "East", "Round": "First Round", "Matchup": "1 Pistons vs 8 Magic", "Result": "Pistons advance"},
        {"Conference": "East", "Round": "First Round", "Matchup": "2 Celtics vs 7 76ers", "Result": "76ers advance"},
        {"Conference": "East", "Round": "First Round", "Matchup": "3 Knicks vs 6 Hawks", "Result": "Knicks advance"},
        {"Conference": "East", "Round": "First Round", "Matchup": "4 Cavaliers vs 5 Raptors", "Result": "Pending"},
        {"Conference": "East", "Round": "Second Round", "Matchup": "3 Knicks vs 7 76ers", "Result": "Active"},
        {"Conference": "East", "Round": "Second Round", "Matchup": "1 Pistons vs Cavaliers/Raptors", "Result": "Pending"},
        {"Conference": "West", "Round": "First Round", "Matchup": "1 Thunder vs 8 Suns", "Result": "Thunder advance"},
        {"Conference": "West", "Round": "First Round", "Matchup": "4 Lakers vs 5 Rockets", "Result": "Lakers advance"},
        {"Conference": "West", "Round": "First Round", "Matchup": "2 Spurs vs 7 Trail Blazers", "Result": "Spurs advance"},
        {"Conference": "West", "Round": "First Round", "Matchup": "3 Timberwolves vs 6 Nuggets", "Result": "Timberwolves advance"},
        {"Conference": "West", "Round": "Second Round", "Matchup": "1 Thunder vs 4 Lakers", "Result": "Active"},
        {"Conference": "West", "Round": "Second Round", "Matchup": "2 Spurs vs 3 Timberwolves", "Result": "Active"},
    ])
    st.dataframe(bracket_data, use_container_width=True)
    fig = px.sunburst(bracket_data, path=["Conference", "Round", "Matchup"], title="Bracket Structure")
    st.plotly_chart(fig, use_container_width=True)


elif page == "AI Prediction Center":
    matchup_header(favorite_team)
    p = profile(favorite_team)

    if p["status"] == "Eliminated":
        st.error(f"{favorite_team} is eliminated, so future playoff win probability is 0%.")
        st.write(p["recap"])
    else:
        st.subheader("Manual Scenario Model")
        st.caption("Use this when the game is not live, or to simulate possible game states.")
        score_margin = st.slider("Current score margin for selected team", -30, 30, 0)
        quarter = st.slider("Current quarter", 1, 4, 2)
        is_home = st.checkbox("Is selected team home?", value=True)
        minutes_left = st.slider("Approximate minutes left in quarter/game situation", 0, 12, 6)
        time_seconds = minutes_left * 60

        heuristic = estimate_win_probability(score_margin, quarter, is_home, p["status"], time_seconds)
        model = statsmodels_probability(score_margin, quarter, is_home)
        final = model if model is not None else heuristic

        c1, c2 = st.columns(2)
        c1.metric("Heuristic Probability", f"{heuristic}%")
        if model is not None:
            c2.metric("Statsmodels Probability", f"{model}%")
        else:
            c2.metric("Statsmodels Probability", "Unavailable")

        prob_df = pd.DataFrame({"Outcome": [f"{favorite_team} Wins", "Opponent Wins"], "Probability": [final, 100 - final]})
        fig = px.pie(prob_df, names="Outcome", values="Probability", title="Scenario Win Probability")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("AI Scenario Explanation")
        st.markdown(live_ai_read(favorite_team, score_margin, quarter, final, max(0, 100 + score_margin), 100, is_home, time_seconds))

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | Generalized team-specific version | Live-data capable")
