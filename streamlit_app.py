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
    from nba_api.live.nba.endpoints import scoreboard
    from nba_api.stats.static import players as nba_players
    from nba_api.stats.endpoints import playergamelog, leaguegamefinder
    NBA_API_AVAILABLE = True
except Exception:
    NBA_API_AVAILABLE = False

st.set_page_config(
    page_title="Daniel Cohen — NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide",
)

st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 NBA Playoff companion app · playoff-only · team-specific · live-aware")

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

TEAM_IDS = {
    "Detroit Pistons": 1610612765,
    "Orlando Magic": 1610612753,
    "Cleveland Cavaliers": 1610612739,
    "Toronto Raptors": 1610612761,
    "New York Knicks": 1610612752,
    "Atlanta Hawks": 1610612737,
    "Philadelphia 76ers": 1610612755,
    "Boston Celtics": 1610612738,
    "Oklahoma City Thunder": 1610612760,
    "Phoenix Suns": 1610612756,
    "Los Angeles Lakers": 1610612747,
    "Houston Rockets": 1610612745,
    "Denver Nuggets": 1610612743,
    "Minnesota Timberwolves": 1610612750,
    "San Antonio Spurs": 1610612759,
    "Portland Trail Blazers": 1610612757,
}

TEAM_ALIASES = {
    "Detroit Pistons": "DET", "Orlando Magic": "ORL", "Cleveland Cavaliers": "CLE", "Toronto Raptors": "TOR",
    "New York Knicks": "NYK", "Atlanta Hawks": "ATL", "Philadelphia 76ers": "PHI", "Boston Celtics": "BOS",
    "Oklahoma City Thunder": "OKC", "Phoenix Suns": "PHX", "Los Angeles Lakers": "LAL", "Houston Rockets": "HOU",
    "Denver Nuggets": "DEN", "Minnesota Timberwolves": "MIN", "San Antonio Spurs": "SAS", "Portland Trail Blazers": "POR",
}
ALIAS_TO_TEAM = {v: k for k, v in TEAM_ALIASES.items()}

TEAM_PROFILES = {
    "Detroit Pistons": {
        "conference": "East", "seed": 1, "status": "Active", "current_round": "Second Round", "current_opponent": "Cleveland Cavaliers",
        "first_opponent": "Orlando Magic", "first_result": "Defeated Orlando Magic, 4-3", "mode": "preview",
        "starters": ["Cade Cunningham", "Jaden Ivey", "Ausar Thompson", "Tobias Harris", "Jalen Duren"],
        "subs": ["Malik Beasley", "Isaiah Stewart", "Marcus Sasser", "Simone Fontecchio", "Ron Holland"],
        "strengths": ["Cade Cunningham creation", "rebounding", "youth and athleticism", "physical defense"],
        "concerns": ["playoff inexperience", "half-court scoring droughts", "late-game execution"],
        "recap": "Detroit survived a seven-game first round and now has momentum entering Round 2.",
        "next_year": "The Pistons can build around Cunningham, Duren, and their young athletic core."
    },
    "Orlando Magic": {
        "conference": "East", "seed": 8, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "Detroit Pistons", "first_result": "Lost to Detroit Pistons, 4-3", "mode": "recap",
        "starters": ["Paolo Banchero", "Franz Wagner", "Jalen Suggs", "Wendell Carter Jr.", "Cole Anthony"],
        "subs": ["Anthony Black", "Jonathan Isaac", "Moritz Wagner", "Gary Harris", "Caleb Houstan"],
        "strengths": ["young forwards", "defense", "physicality"],
        "concerns": ["shooting", "late-game offense", "closing series"],
        "recap": "Orlando competed well but could not close the series after having chances to advance.",
        "next_year": "The Magic need more shooting, half-court creation, and playoff closing experience."
    },
    "Cleveland Cavaliers": {
        "conference": "East", "seed": 4, "status": "Active", "current_round": "Second Round", "current_opponent": "Detroit Pistons",
        "first_opponent": "Toronto Raptors", "first_result": "Defeated Toronto Raptors, 4-3", "mode": "preview",
        "starters": ["Donovan Mitchell", "Darius Garland", "Max Strus", "Evan Mobley", "Jarrett Allen"],
        "subs": ["Caris LeVert", "Isaac Okoro", "Dean Wade", "Georges Niang", "Sam Merrill"],
        "strengths": ["guard scoring", "rim protection", "frontcourt defense"],
        "concerns": ["offensive droughts", "health", "late-game shot creation"],
        "recap": "Cleveland advanced after a difficult first-round series against Toronto.",
        "next_year": "The Cavaliers continue to build around Mitchell, Garland, Mobley, and Allen."
    },
    "Toronto Raptors": {
        "conference": "East", "seed": 5, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "Cleveland Cavaliers", "first_result": "Lost to Cleveland Cavaliers, 4-3", "mode": "recap",
        "starters": ["Immanuel Quickley", "RJ Barrett", "Scottie Barnes", "Gradey Dick", "Jakob Poeltl"],
        "subs": ["Kelly Olynyk", "Bruce Brown", "Ochai Agbaji", "Chris Boucher", "Davion Mitchell"],
        "strengths": ["athletic wings", "transition play", "defensive versatility"],
        "concerns": ["half-court scoring", "shooting consistency", "closing games"],
        "recap": "Toronto pushed Cleveland to the limit but came up short in the first round.",
        "next_year": "The Raptors need more shooting and late-game offensive structure."
    },
    "New York Knicks": {
        "conference": "East", "seed": 3, "status": "Active", "current_round": "Second Round", "current_opponent": "Philadelphia 76ers",
        "first_opponent": "Atlanta Hawks", "first_result": "Defeated Atlanta Hawks, 4-2", "mode": "preview",
        "starters": ["Jalen Brunson", "Karl-Anthony Towns", "OG Anunoby", "Mikal Bridges", "Josh Hart"],
        "subs": ["Miles McBride", "Mitchell Robinson", "Jordan Clarkson", "Landry Shamet", "Jose Alvarado"],
        "strengths": ["Brunson shot creation", "rebounding", "wing defense", "clutch scoring", "physicality"],
        "concerns": ["bench scoring consistency", "heavy Brunson workload", "foul trouble against elite bigs"],
        "recap": "The Knicks finished the Hawks series with a dominant closeout and strong two-way play.",
        "next_year": "The Knicks are still alive; this team is trying to turn a strong run into a deeper playoff breakthrough."
    },
    "Atlanta Hawks": {
        "conference": "East", "seed": 6, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "New York Knicks", "first_result": "Lost to New York Knicks, 4-2", "mode": "recap",
        "starters": ["Trae Young", "CJ McCollum", "Zaccharie Risacher", "Jalen Johnson", "Onyeka Okongwu"],
        "subs": ["Bogdan Bogdanovic", "Clint Capela", "Vit Krejci", "Kobe Bufkin", "De'Andre Hunter"],
        "strengths": ["guard shot creation", "pace", "pick-and-roll offense"],
        "concerns": ["defense", "rebounding", "late-series consistency"],
        "recap": "Atlanta had moments of shot-making and stole games, but New York's physicality and closeout-game dominance ended the series.",
        "next_year": "The Hawks need better defense, more size, and more consistent playoff half-court execution."
    },
    "Philadelphia 76ers": {
        "conference": "East", "seed": 7, "status": "Active", "current_round": "Second Round", "current_opponent": "New York Knicks",
        "first_opponent": "Boston Celtics", "first_result": "Defeated Boston Celtics, 4-3", "mode": "preview",
        "starters": ["Tyrese Maxey", "Quentin Grimes", "Kelly Oubre Jr.", "Paul George", "Joel Embiid"],
        "subs": ["Andre Drummond", "Kyle Lowry", "Eric Gordon", "Caleb Martin", "VJ Edgecombe"],
        "strengths": ["Embiid interior pressure", "Maxey speed", "free throws", "star scoring"],
        "concerns": ["Embiid health", "depth", "rebounding vs Knicks"],
        "recap": "Philadelphia came back to eliminate Boston and enters Round 2 with major momentum.",
        "next_year": "The 76ers are still alive; the focus is keeping Embiid healthy and maximizing Maxey."
    },
    "Boston Celtics": {
        "conference": "East", "seed": 2, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "Philadelphia 76ers", "first_result": "Lost to Philadelphia 76ers, 4-3", "mode": "recap",
        "starters": ["Jayson Tatum", "Jaylen Brown", "Derrick White", "Jrue Holiday", "Kristaps Porzingis"],
        "subs": ["Al Horford", "Payton Pritchard", "Sam Hauser", "Luke Kornet", "Xavier Tillman"],
        "strengths": ["wing talent", "spacing", "championship experience"],
        "concerns": ["late-series execution", "injuries", "three-point variance"],
        "recap": "Boston lost a seven-game series to Philadelphia and now shifts into offseason evaluation.",
        "next_year": "The Celtics still have elite talent, but the loss raises questions about health, depth, and late-game execution."
    },
    "Oklahoma City Thunder": {
        "conference": "West", "seed": 1, "status": "Active", "current_round": "Second Round", "current_opponent": "Los Angeles Lakers",
        "first_opponent": "Phoenix Suns", "first_result": "Defeated Phoenix Suns, 4-0", "mode": "preview",
        "starters": ["Shai Gilgeous-Alexander", "Jalen Williams", "Lu Dort", "Chet Holmgren", "Josh Giddey"],
        "subs": ["Isaiah Joe", "Cason Wallace", "Aaron Wiggins", "Jaylin Williams", "Kenrich Williams"],
        "strengths": ["guard creation", "spacing", "defensive length", "youth"],
        "concerns": ["playoff physicality", "rebounding", "late-game pressure"],
        "recap": "Oklahoma City controlled Round 1 and advanced quickly.",
        "next_year": "The Thunder are still alive and building a championship-level profile."
    },
    "Phoenix Suns": {
        "conference": "West", "seed": 8, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "Oklahoma City Thunder", "first_result": "Lost to Oklahoma City Thunder, 4-0", "mode": "recap",
        "starters": ["Devin Booker", "Kevin Durant", "Bradley Beal", "Grayson Allen", "Jusuf Nurkic"],
        "subs": ["Royce O'Neale", "Eric Gordon", "Bol Bol", "Josh Okogie", "Drew Eubanks"],
        "strengths": ["star scoring", "midrange shot creation", "veteran talent"],
        "concerns": ["depth", "defense", "age and health"],
        "recap": "Phoenix was swept by Oklahoma City and never gained control of the series.",
        "next_year": "The Suns need better depth, defense, and a clearer playoff identity."
    },
    "Los Angeles Lakers": {
        "conference": "West", "seed": 4, "status": "Active", "current_round": "Second Round", "current_opponent": "Oklahoma City Thunder",
        "first_opponent": "Houston Rockets", "first_result": "Defeated Houston Rockets, 4-2", "mode": "preview",
        "starters": ["LeBron James", "Anthony Davis", "Austin Reaves", "Rui Hachimura", "D'Angelo Russell"],
        "subs": ["Gabe Vincent", "Jarred Vanderbilt", "Max Christie", "Jaxson Hayes", "Taurean Prince"],
        "strengths": ["star experience", "paint defense", "late-game IQ"],
        "concerns": ["age", "transition defense", "three-point shooting"],
        "recap": "The Lakers advanced past Houston and now face a younger, faster Thunder team.",
        "next_year": "The Lakers are still alive; the question is whether experience can overcome OKC's speed."
    },
    "Houston Rockets": {
        "conference": "West", "seed": 5, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "Los Angeles Lakers", "first_result": "Lost to Los Angeles Lakers, 4-2", "mode": "recap",
        "starters": ["Fred VanVleet", "Jalen Green", "Dillon Brooks", "Jabari Smith Jr.", "Alperen Sengun"],
        "subs": ["Amen Thompson", "Tari Eason", "Cam Whitmore", "Steven Adams", "Aaron Holiday"],
        "strengths": ["young athleticism", "defense", "pace"],
        "concerns": ["playoff experience", "half-court offense", "shot selection"],
        "recap": "Houston showed growth but lost to the Lakers in six games.",
        "next_year": "The Rockets can build on playoff experience, defensive energy, and their young core."
    },
    "Denver Nuggets": {
        "conference": "West", "seed": 3, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "Minnesota Timberwolves", "first_result": "Lost to Minnesota Timberwolves, 4-2", "mode": "recap",
        "starters": ["Nikola Jokic", "Jamal Murray", "Michael Porter Jr.", "Aaron Gordon", "Christian Braun"],
        "subs": ["Reggie Jackson", "Peyton Watson", "Julian Strawther", "Zeke Nnaji", "DeAndre Jordan"],
        "strengths": ["Jokic offense", "chemistry", "half-court passing"],
        "concerns": ["bench depth", "athletic matchups", "defensive coverages"],
        "recap": "Denver could not solve Minnesota's size and defensive pressure consistently enough.",
        "next_year": "The Nuggets need more depth and more athletic answers around Jokic."
    },
    "Minnesota Timberwolves": {
        "conference": "West", "seed": 6, "status": "Active", "current_round": "Second Round", "current_opponent": "San Antonio Spurs",
        "first_opponent": "Denver Nuggets", "first_result": "Defeated Denver Nuggets, 4-2", "mode": "preview",
        "starters": ["Mike Conley", "Anthony Edwards", "Jaden McDaniels", "Naz Reid", "Rudy Gobert"],
        "subs": ["Donte DiVincenzo", "Nickeil Alexander-Walker", "Rob Dillingham", "Terrence Shannon Jr.", "Luka Garza"],
        "strengths": ["defense", "size", "Anthony Edwards scoring", "physicality"],
        "concerns": ["late-game offense", "spacing", "foul trouble"],
        "recap": "Minnesota eliminated Denver and enters Round 2 with defensive confidence.",
        "next_year": "The Timberwolves are still alive and can continue building around Edwards and elite defense."
    },
    "San Antonio Spurs": {
        "conference": "West", "seed": 2, "status": "Active", "current_round": "Second Round", "current_opponent": "Minnesota Timberwolves",
        "first_opponent": "Portland Trail Blazers", "first_result": "Defeated Portland Trail Blazers, 4-1", "mode": "preview",
        "starters": ["Victor Wembanyama", "Devin Vassell", "Stephon Castle", "Keldon Johnson", "Jeremy Sochan"],
        "subs": ["Tre Jones", "Malaki Branham", "Zach Collins", "Julian Champagnie", "Blake Wesley"],
        "strengths": ["Wembanyama defense", "length", "rim protection"],
        "concerns": ["youth", "turnovers", "late-game execution"],
        "recap": "San Antonio advanced behind Wembanyama's two-way impact.",
        "next_year": "The Spurs are still alive and accelerating their timeline around Wembanyama."
    },
    "Portland Trail Blazers": {
        "conference": "West", "seed": 7, "status": "Eliminated", "current_round": "Lost First Round", "current_opponent": None,
        "first_opponent": "San Antonio Spurs", "first_result": "Lost to San Antonio Spurs, 4-1", "mode": "recap",
        "starters": ["Scoot Henderson", "Anfernee Simons", "Shaedon Sharpe", "Jerami Grant", "Deandre Ayton"],
        "subs": ["Matisse Thybulle", "Robert Williams III", "Toumani Camara", "Kris Murray", "Dalano Banton"],
        "strengths": ["young guards", "athleticism", "future upside"],
        "concerns": ["defense", "experience", "frontcourt matchups"],
        "recap": "Portland gained playoff experience but lost to San Antonio in five games.",
        "next_year": "The Blazers need defensive growth and more consistent scoring structure."
    },
}

FIRST_ROUND_SERIES = [
    {"conf": "East", "a_seed": 1, "a": "Detroit Pistons", "b_seed": 8, "b": "Orlando Magic", "a_wins": 4, "b_wins": 3, "winner": "Detroit Pistons"},
    {"conf": "East", "a_seed": 4, "a": "Cleveland Cavaliers", "b_seed": 5, "b": "Toronto Raptors", "a_wins": 4, "b_wins": 3, "winner": "Cleveland Cavaliers"},
    {"conf": "East", "a_seed": 3, "a": "New York Knicks", "b_seed": 6, "b": "Atlanta Hawks", "a_wins": 4, "b_wins": 2, "winner": "New York Knicks"},
    {"conf": "East", "a_seed": 2, "a": "Boston Celtics", "b_seed": 7, "b": "Philadelphia 76ers", "a_wins": 3, "b_wins": 4, "winner": "Philadelphia 76ers"},
    {"conf": "West", "a_seed": 1, "a": "Oklahoma City Thunder", "b_seed": 8, "b": "Phoenix Suns", "a_wins": 4, "b_wins": 0, "winner": "Oklahoma City Thunder"},
    {"conf": "West", "a_seed": 4, "a": "Los Angeles Lakers", "b_seed": 5, "b": "Houston Rockets", "a_wins": 4, "b_wins": 2, "winner": "Los Angeles Lakers"},
    {"conf": "West", "a_seed": 3, "a": "Denver Nuggets", "b_seed": 6, "b": "Minnesota Timberwolves", "a_wins": 2, "b_wins": 4, "winner": "Minnesota Timberwolves"},
    {"conf": "West", "a_seed": 2, "a": "San Antonio Spurs", "b_seed": 7, "b": "Portland Trail Blazers", "a_wins": 4, "b_wins": 1, "winner": "San Antonio Spurs"},
]

SECOND_ROUND_SERIES = [
    {"conf": "East", "a_seed": 1, "a": "Detroit Pistons", "b_seed": 4, "b": "Cleveland Cavaliers", "a_wins": 0, "b_wins": 0},
    {"conf": "East", "a_seed": 3, "a": "New York Knicks", "b_seed": 7, "b": "Philadelphia 76ers", "a_wins": 0, "b_wins": 0},
    {"conf": "West", "a_seed": 1, "a": "Oklahoma City Thunder", "b_seed": 4, "b": "Los Angeles Lakers", "a_wins": 0, "b_wins": 0},
    {"conf": "West", "a_seed": 2, "a": "San Antonio Spurs", "b_seed": 6, "b": "Minnesota Timberwolves", "a_wins": 0, "b_wins": 0},
]

# Verified hard-coded first-round fallback data for all 8 series.
# The app can still try NBA API first, but these make First Round Review reliable even if the API fails.
FALLBACK_FIRST_ROUND_GAMES = {
    ("Detroit Pistons", "Orlando Magic"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "Magic at Pistons", "Winner": "Orlando Magic", "Score": "Magic 112, Pistons 101"},
        {"Game": 2, "Date": "Wed, Apr 22, 2026", "Matchup": "Magic at Pistons", "Winner": "Detroit Pistons", "Score": "Pistons 98, Magic 83"},
        {"Game": 3, "Date": "Sat, Apr 25, 2026", "Matchup": "Pistons at Magic", "Winner": "Orlando Magic", "Score": "Magic 113, Pistons 105"},
        {"Game": 4, "Date": "Mon, Apr 27, 2026", "Matchup": "Pistons at Magic", "Winner": "Orlando Magic", "Score": "Magic 94, Pistons 88"},
        {"Game": 5, "Date": "Wed, Apr 29, 2026", "Matchup": "Magic at Pistons", "Winner": "Detroit Pistons", "Score": "Pistons 116, Magic 109"},
        {"Game": 6, "Date": "Fri, May 1, 2026", "Matchup": "Pistons at Magic", "Winner": "Detroit Pistons", "Score": "Pistons 93, Magic 79"},
        {"Game": 7, "Date": "Sun, May 3, 2026", "Matchup": "Magic at Pistons", "Winner": "Detroit Pistons", "Score": "Pistons 116, Magic 94"},
    ],
    ("Orlando Magic", "Detroit Pistons"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "Magic at Pistons", "Winner": "Orlando Magic", "Score": "Magic 112, Pistons 101"},
        {"Game": 2, "Date": "Wed, Apr 22, 2026", "Matchup": "Magic at Pistons", "Winner": "Detroit Pistons", "Score": "Pistons 98, Magic 83"},
        {"Game": 3, "Date": "Sat, Apr 25, 2026", "Matchup": "Pistons at Magic", "Winner": "Orlando Magic", "Score": "Magic 113, Pistons 105"},
        {"Game": 4, "Date": "Mon, Apr 27, 2026", "Matchup": "Pistons at Magic", "Winner": "Orlando Magic", "Score": "Magic 94, Pistons 88"},
        {"Game": 5, "Date": "Wed, Apr 29, 2026", "Matchup": "Magic at Pistons", "Winner": "Detroit Pistons", "Score": "Pistons 116, Magic 109"},
        {"Game": 6, "Date": "Fri, May 1, 2026", "Matchup": "Pistons at Magic", "Winner": "Detroit Pistons", "Score": "Pistons 93, Magic 79"},
        {"Game": 7, "Date": "Sun, May 3, 2026", "Matchup": "Magic at Pistons", "Winner": "Detroit Pistons", "Score": "Pistons 116, Magic 94"},
    ],
    ("Cleveland Cavaliers", "Toronto Raptors"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 126, Raptors 113"},
        {"Game": 2, "Date": "Mon, Apr 20, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 115, Raptors 105"},
        {"Game": 3, "Date": "Thu, Apr 23, 2026", "Matchup": "Cavaliers at Raptors", "Winner": "Toronto Raptors", "Score": "Raptors 126, Cavaliers 104"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Cavaliers at Raptors", "Winner": "Toronto Raptors", "Score": "Raptors 93, Cavaliers 89"},
        {"Game": 5, "Date": "Wed, Apr 29, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 125, Raptors 120"},
        {"Game": 6, "Date": "Fri, May 1, 2026", "Matchup": "Cavaliers at Raptors", "Winner": "Toronto Raptors", "Score": "Raptors 112, Cavaliers 110"},
        {"Game": 7, "Date": "Sun, May 3, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 114, Raptors 102"},
    ],
    ("Toronto Raptors", "Cleveland Cavaliers"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 126, Raptors 113"},
        {"Game": 2, "Date": "Mon, Apr 20, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 115, Raptors 105"},
        {"Game": 3, "Date": "Thu, Apr 23, 2026", "Matchup": "Cavaliers at Raptors", "Winner": "Toronto Raptors", "Score": "Raptors 126, Cavaliers 104"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Cavaliers at Raptors", "Winner": "Toronto Raptors", "Score": "Raptors 93, Cavaliers 89"},
        {"Game": 5, "Date": "Wed, Apr 29, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 125, Raptors 120"},
        {"Game": 6, "Date": "Fri, May 1, 2026", "Matchup": "Cavaliers at Raptors", "Winner": "Toronto Raptors", "Score": "Raptors 112, Cavaliers 110"},
        {"Game": 7, "Date": "Sun, May 3, 2026", "Matchup": "Raptors at Cavaliers", "Winner": "Cleveland Cavaliers", "Score": "Cavaliers 114, Raptors 102"},
    ],
    ("New York Knicks", "Atlanta Hawks"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Hawks at Knicks", "Winner": "New York Knicks", "Score": "Knicks 113, Hawks 102"},
        {"Game": 2, "Date": "Mon, Apr 20, 2026", "Matchup": "Hawks at Knicks", "Winner": "Atlanta Hawks", "Score": "Hawks 107, Knicks 106"},
        {"Game": 3, "Date": "Thu, Apr 23, 2026", "Matchup": "Knicks at Hawks", "Winner": "Atlanta Hawks", "Score": "Hawks 109, Knicks 108"},
        {"Game": 4, "Date": "Sat, Apr 25, 2026", "Matchup": "Knicks at Hawks", "Winner": "New York Knicks", "Score": "Knicks 114, Hawks 98"},
        {"Game": 5, "Date": "Tue, Apr 28, 2026", "Matchup": "Hawks at Knicks", "Winner": "New York Knicks", "Score": "Knicks 126, Hawks 97"},
        {"Game": 6, "Date": "Thu, Apr 30, 2026", "Matchup": "Knicks at Hawks", "Winner": "New York Knicks", "Score": "Knicks 140, Hawks 89"},
    ],
    ("Atlanta Hawks", "New York Knicks"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Hawks at Knicks", "Winner": "New York Knicks", "Score": "Knicks 113, Hawks 102"},
        {"Game": 2, "Date": "Mon, Apr 20, 2026", "Matchup": "Hawks at Knicks", "Winner": "Atlanta Hawks", "Score": "Hawks 107, Knicks 106"},
        {"Game": 3, "Date": "Thu, Apr 23, 2026", "Matchup": "Knicks at Hawks", "Winner": "Atlanta Hawks", "Score": "Hawks 109, Knicks 108"},
        {"Game": 4, "Date": "Sat, Apr 25, 2026", "Matchup": "Knicks at Hawks", "Winner": "New York Knicks", "Score": "Knicks 114, Hawks 98"},
        {"Game": 5, "Date": "Tue, Apr 28, 2026", "Matchup": "Hawks at Knicks", "Winner": "New York Knicks", "Score": "Knicks 126, Hawks 97"},
        {"Game": 6, "Date": "Thu, Apr 30, 2026", "Matchup": "Knicks at Hawks", "Winner": "New York Knicks", "Score": "Knicks 140, Hawks 89"},
    ],
    ("Boston Celtics", "Philadelphia 76ers"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "76ers at Celtics", "Winner": "Boston Celtics", "Score": "Celtics 123, 76ers 91"},
        {"Game": 2, "Date": "Tue, Apr 21, 2026", "Matchup": "76ers at Celtics", "Winner": "Philadelphia 76ers", "Score": "76ers 111, Celtics 97"},
        {"Game": 3, "Date": "Fri, Apr 24, 2026", "Matchup": "Celtics at 76ers", "Winner": "Boston Celtics", "Score": "Celtics 108, 76ers 100"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Celtics at 76ers", "Winner": "Boston Celtics", "Score": "Celtics 128, 76ers 96"},
        {"Game": 5, "Date": "Tue, Apr 28, 2026", "Matchup": "76ers at Celtics", "Winner": "Philadelphia 76ers", "Score": "76ers 113, Celtics 97"},
        {"Game": 6, "Date": "Thu, Apr 30, 2026", "Matchup": "Celtics at 76ers", "Winner": "Philadelphia 76ers", "Score": "76ers 106, Celtics 93"},
        {"Game": 7, "Date": "Sat, May 2, 2026", "Matchup": "76ers at Celtics", "Winner": "Philadelphia 76ers", "Score": "76ers 109, Celtics 100"},
    ],
    ("Philadelphia 76ers", "Boston Celtics"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "76ers at Celtics", "Winner": "Boston Celtics", "Score": "Celtics 123, 76ers 91"},
        {"Game": 2, "Date": "Tue, Apr 21, 2026", "Matchup": "76ers at Celtics", "Winner": "Philadelphia 76ers", "Score": "76ers 111, Celtics 97"},
        {"Game": 3, "Date": "Fri, Apr 24, 2026", "Matchup": "Celtics at 76ers", "Winner": "Boston Celtics", "Score": "Celtics 108, 76ers 100"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Celtics at 76ers", "Winner": "Boston Celtics", "Score": "Celtics 128, 76ers 96"},
        {"Game": 5, "Date": "Tue, Apr 28, 2026", "Matchup": "76ers at Celtics", "Winner": "Philadelphia 76ers", "Score": "76ers 113, Celtics 97"},
        {"Game": 6, "Date": "Thu, Apr 30, 2026", "Matchup": "Celtics at 76ers", "Winner": "Philadelphia 76ers", "Score": "76ers 106, Celtics 93"},
        {"Game": 7, "Date": "Sat, May 2, 2026", "Matchup": "76ers at Celtics", "Winner": "Philadelphia 76ers", "Score": "76ers 109, Celtics 100"},
    ],
    ("Oklahoma City Thunder", "Phoenix Suns"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "Suns at Thunder", "Winner": "Oklahoma City Thunder", "Score": "Thunder 119, Suns 84"},
        {"Game": 2, "Date": "Wed, Apr 22, 2026", "Matchup": "Suns at Thunder", "Winner": "Oklahoma City Thunder", "Score": "Thunder 120, Suns 107"},
        {"Game": 3, "Date": "Sat, Apr 25, 2026", "Matchup": "Thunder at Suns", "Winner": "Oklahoma City Thunder", "Score": "Thunder 121, Suns 109"},
        {"Game": 4, "Date": "Mon, Apr 27, 2026", "Matchup": "Thunder at Suns", "Winner": "Oklahoma City Thunder", "Score": "Thunder 131, Suns 122"},
    ],
    ("Phoenix Suns", "Oklahoma City Thunder"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "Suns at Thunder", "Winner": "Oklahoma City Thunder", "Score": "Thunder 119, Suns 84"},
        {"Game": 2, "Date": "Wed, Apr 22, 2026", "Matchup": "Suns at Thunder", "Winner": "Oklahoma City Thunder", "Score": "Thunder 120, Suns 107"},
        {"Game": 3, "Date": "Sat, Apr 25, 2026", "Matchup": "Thunder at Suns", "Winner": "Oklahoma City Thunder", "Score": "Thunder 121, Suns 109"},
        {"Game": 4, "Date": "Mon, Apr 27, 2026", "Matchup": "Thunder at Suns", "Winner": "Oklahoma City Thunder", "Score": "Thunder 131, Suns 122"},
    ],
    ("Los Angeles Lakers", "Houston Rockets"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Rockets at Lakers", "Winner": "Los Angeles Lakers", "Score": "Lakers 107, Rockets 98"},
        {"Game": 2, "Date": "Tue, Apr 21, 2026", "Matchup": "Rockets at Lakers", "Winner": "Los Angeles Lakers", "Score": "Lakers 101, Rockets 94"},
        {"Game": 3, "Date": "Fri, Apr 24, 2026", "Matchup": "Lakers at Rockets", "Winner": "Los Angeles Lakers", "Score": "Lakers 112, Rockets 108"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Lakers at Rockets", "Winner": "Houston Rockets", "Score": "Rockets 115, Lakers 96"},
        {"Game": 5, "Date": "Wed, Apr 29, 2026", "Matchup": "Rockets at Lakers", "Winner": "Houston Rockets", "Score": "Rockets 99, Lakers 93"},
        {"Game": 6, "Date": "Fri, May 1, 2026", "Matchup": "Lakers at Rockets", "Winner": "Los Angeles Lakers", "Score": "Lakers 98, Rockets 78"},
    ],
    ("Houston Rockets", "Los Angeles Lakers"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Rockets at Lakers", "Winner": "Los Angeles Lakers", "Score": "Lakers 107, Rockets 98"},
        {"Game": 2, "Date": "Tue, Apr 21, 2026", "Matchup": "Rockets at Lakers", "Winner": "Los Angeles Lakers", "Score": "Lakers 101, Rockets 94"},
        {"Game": 3, "Date": "Fri, Apr 24, 2026", "Matchup": "Lakers at Rockets", "Winner": "Los Angeles Lakers", "Score": "Lakers 112, Rockets 108"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Lakers at Rockets", "Winner": "Houston Rockets", "Score": "Rockets 115, Lakers 96"},
        {"Game": 5, "Date": "Wed, Apr 29, 2026", "Matchup": "Rockets at Lakers", "Winner": "Houston Rockets", "Score": "Rockets 99, Lakers 93"},
        {"Game": 6, "Date": "Fri, May 1, 2026", "Matchup": "Lakers at Rockets", "Winner": "Los Angeles Lakers", "Score": "Lakers 98, Rockets 78"},
    ],
    ("Denver Nuggets", "Minnesota Timberwolves"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Timberwolves at Nuggets", "Winner": "Denver Nuggets", "Score": "Nuggets 116, Timberwolves 105"},
        {"Game": 2, "Date": "Mon, Apr 20, 2026", "Matchup": "Timberwolves at Nuggets", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 119, Nuggets 114"},
        {"Game": 3, "Date": "Thu, Apr 23, 2026", "Matchup": "Nuggets at Timberwolves", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 113, Nuggets 96"},
        {"Game": 4, "Date": "Sat, Apr 25, 2026", "Matchup": "Nuggets at Timberwolves", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 112, Nuggets 96"},
        {"Game": 5, "Date": "Mon, Apr 27, 2026", "Matchup": "Timberwolves at Nuggets", "Winner": "Denver Nuggets", "Score": "Nuggets 125, Timberwolves 113"},
        {"Game": 6, "Date": "Thu, Apr 30, 2026", "Matchup": "Nuggets at Timberwolves", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 110, Nuggets 98"},
    ],
    ("Minnesota Timberwolves", "Denver Nuggets"): [
        {"Game": 1, "Date": "Sat, Apr 18, 2026", "Matchup": "Timberwolves at Nuggets", "Winner": "Denver Nuggets", "Score": "Nuggets 116, Timberwolves 105"},
        {"Game": 2, "Date": "Mon, Apr 20, 2026", "Matchup": "Timberwolves at Nuggets", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 119, Nuggets 114"},
        {"Game": 3, "Date": "Thu, Apr 23, 2026", "Matchup": "Nuggets at Timberwolves", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 113, Nuggets 96"},
        {"Game": 4, "Date": "Sat, Apr 25, 2026", "Matchup": "Nuggets at Timberwolves", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 112, Nuggets 96"},
        {"Game": 5, "Date": "Mon, Apr 27, 2026", "Matchup": "Timberwolves at Nuggets", "Winner": "Denver Nuggets", "Score": "Nuggets 125, Timberwolves 113"},
        {"Game": 6, "Date": "Thu, Apr 30, 2026", "Matchup": "Nuggets at Timberwolves", "Winner": "Minnesota Timberwolves", "Score": "Timberwolves 110, Nuggets 98"},
    ],
    ("San Antonio Spurs", "Portland Trail Blazers"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "Trail Blazers at Spurs", "Winner": "San Antonio Spurs", "Score": "Spurs 111, Trail Blazers 98"},
        {"Game": 2, "Date": "Tue, Apr 21, 2026", "Matchup": "Trail Blazers at Spurs", "Winner": "Portland Trail Blazers", "Score": "Trail Blazers 106, Spurs 103"},
        {"Game": 3, "Date": "Fri, Apr 24, 2026", "Matchup": "Spurs at Trail Blazers", "Winner": "San Antonio Spurs", "Score": "Spurs 120, Trail Blazers 108"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Spurs at Trail Blazers", "Winner": "San Antonio Spurs", "Score": "Spurs 114, Trail Blazers 93"},
        {"Game": 5, "Date": "Tue, Apr 28, 2026", "Matchup": "Trail Blazers at Spurs", "Winner": "San Antonio Spurs", "Score": "Spurs 114, Trail Blazers 95"},
    ],
    ("Portland Trail Blazers", "San Antonio Spurs"): [
        {"Game": 1, "Date": "Sun, Apr 19, 2026", "Matchup": "Trail Blazers at Spurs", "Winner": "San Antonio Spurs", "Score": "Spurs 111, Trail Blazers 98"},
        {"Game": 2, "Date": "Tue, Apr 21, 2026", "Matchup": "Trail Blazers at Spurs", "Winner": "Portland Trail Blazers", "Score": "Trail Blazers 106, Spurs 103"},
        {"Game": 3, "Date": "Fri, Apr 24, 2026", "Matchup": "Spurs at Trail Blazers", "Winner": "San Antonio Spurs", "Score": "Spurs 120, Trail Blazers 108"},
        {"Game": 4, "Date": "Sun, Apr 26, 2026", "Matchup": "Spurs at Trail Blazers", "Winner": "San Antonio Spurs", "Score": "Spurs 114, Trail Blazers 93"},
        {"Game": 5, "Date": "Tue, Apr 28, 2026", "Matchup": "Trail Blazers at Spurs", "Winner": "San Antonio Spurs", "Score": "Spurs 114, Trail Blazers 95"},
    ],
}

SERIES_SCHEDULES = {
    "New York Knicks": pd.DataFrame([
        {"Game": "Game 1", "Date": "Mon, May 4", "Time": "8:00 PM ET", "Location": "Madison Square Garden", "TV": "NBC / Peacock", "Matchup": "76ers at Knicks"},
        {"Game": "Game 2", "Date": "Wed, May 6", "Time": "7:00 PM ET", "Location": "Madison Square Garden", "TV": "ESPN", "Matchup": "76ers at Knicks"},
        {"Game": "Game 3", "Date": "Fri, May 8", "Time": "7:00 PM ET", "Location": "Philadelphia", "TV": "Prime Video", "Matchup": "Knicks at 76ers"},
        {"Game": "Game 4", "Date": "Sun, May 10", "Time": "3:30 PM ET", "Location": "Philadelphia", "TV": "ABC", "Matchup": "Knicks at 76ers"},
        {"Game": "Game 5", "Date": "Tue, May 12", "Time": "TBD", "Location": "Madison Square Garden", "TV": "TBD", "Matchup": "76ers at Knicks"},
        {"Game": "Game 6", "Date": "Thu, May 14", "Time": "TBD", "Location": "Philadelphia", "TV": "TBD", "Matchup": "Knicks at 76ers"},
        {"Game": "Game 7", "Date": "Sun, May 17", "Time": "TBD", "Location": "Madison Square Garden", "TV": "TBD", "Matchup": "76ers at Knicks"},
    ])
}
SERIES_SCHEDULES["Philadelphia 76ers"] = SERIES_SCHEDULES["New York Knicks"]

@st.cache_data(ttl=1800)
def fetch_team_vs_team_games(team_a, team_b, season="2025-26"):
    """Return real NBA API playoff games between two teams when available."""
    if not NBA_API_AVAILABLE:
        return pd.DataFrame()
    try:
        team_id = TEAM_IDS[team_a]
        finder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            season_nullable=season,
            season_type_nullable="Playoffs"
        )
        df = finder.get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        opp_alias = TEAM_ALIASES[team_b]
        df = df[df["MATCHUP"].astype(str).str.contains(opp_alias, na=False)].copy()
        if df.empty:
            return pd.DataFrame()
        df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
        df = df.sort_values("GAME_DATE")
        rows = []
        for i, (_, r) in enumerate(df.iterrows(), start=1):
            matchup = str(r.get("MATCHUP", ""))
            pts_for = int(r.get("PTS", 0))
            plus_minus = int(r.get("PLUS_MINUS", 0)) if not pd.isna(r.get("PLUS_MINUS", np.nan)) else 0
            pts_against = pts_for - plus_minus
            winner = team_a if r.get("WL") == "W" else team_b
            if "@" in matchup:
                matchup_text = f"{team_a} at {team_b}"
            else:
                matchup_text = f"{team_b} at {team_a}"
            if r.get("WL") == "W":
                score = f"{team_a} {pts_for}, {team_b} {pts_against}"
            else:
                score = f"{team_b} {pts_against}, {team_a} {pts_for}"
            rows.append({"Game": i, "Date": r["GAME_DATE"].strftime("%a, %b %d, %Y"), "Matchup": matchup_text, "Winner": winner, "Score": score})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def profile(team):
    return TEAM_PROFILES[team]

def first_round_series_for_team(team):
    for s in FIRST_ROUND_SERIES:
        if team in [s["a"], s["b"]]:
            return s
    return None

def current_series_for_team(team):
    for s in SECOND_ROUND_SERIES:
        if team in [s["a"], s["b"]]:
            return s
    return None

def logo_img(team, width=90):
    st.image(TEAM_LOGOS[team], width=width)

def render_matchup_header(team_a, seed_a, team_b, seed_b, round_name, series_text=None):
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        logo_img(team_a, 100)
        st.markdown(f"**({seed_a}) {team_a}**")
    with c2:
        st.markdown(f"<h2 style='text-align:center;'>{round_name}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>({seed_a}) {team_a} vs ({seed_b}) {team_b}</h1>", unsafe_allow_html=True)
        if series_text:
            st.markdown(f"<h3 style='text-align:center;'>{series_text}</h3>", unsafe_allow_html=True)
    with c3:
        logo_img(team_b, 100)
        st.markdown(f"**({seed_b}) {team_b}**")

def first_round_header(team):
    s = first_round_series_for_team(team)
    if not s:
        st.warning("First-round matchup not found.")
        return
    series_text = f"{s['winner']} won {s['a_wins']}-{s['b_wins']}" if s.get("winner") else f"Series {s['a_wins']}-{s['b_wins']}"
    render_matchup_header(s["a"], s["a_seed"], s["b"], s["b_seed"], "First Round Review", series_text)

def current_round_header(team):
    p = profile(team)
    if p["status"] == "Eliminated":
        first_round_header(team)
        return
    s = current_series_for_team(team)
    if s:
        series_text = f"Series {s['a_wins']}-{s['b_wins']}"
        render_matchup_header(s["a"], s["a_seed"], s["b"], s["b_seed"], "Second Round", series_text)
    else:
        first_round_header(team)

def get_first_round_game_table(team):
    s = first_round_series_for_team(team)
    if not s:
        return pd.DataFrame()
    a, b = s["a"], s["b"]
    api_df = fetch_team_vs_team_games(a, b)
    if not api_df.empty:
        return api_df
    fallback = FALLBACK_FIRST_ROUND_GAMES.get((a, b)) or FALLBACK_FIRST_ROUND_GAMES.get((b, a))
    if fallback:
        return pd.DataFrame(fallback)
    return pd.DataFrame([
        {"Game": "Real NBA API lookup", "Date": "Run app with nba_api enabled", "Matchup": f"{a} vs {b}", "Winner": "Pending data", "Score": "Real scores will load from NBA API when available"}
    ])

def render_first_round_review(team):
    first_round_header(team)
    st.subheader("Game-by-game scores")
    table = get_first_round_game_table(team)
    st.dataframe(table, use_container_width=True, hide_index=True)
    p = profile(team)
    if p["status"] == "Eliminated":
        st.error(p["first_result"])
        st.subheader("What went right")
        st.write(p["recap"])
        st.subheader("Going forward to next season")
        st.info(p["next_year"])
    else:
        st.success(p["first_result"])
        st.subheader("What carried over from Round 1")
        st.write(p["recap"])

def team_strengths_concerns(team):
    p = profile(team)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Strengths")
        for x in p["strengths"]:
            st.success(x)
    with c2:
        st.subheader("Concerns")
        for x in p["concerns"]:
            st.warning(x)

@st.cache_data(ttl=30)
def get_live_games():
    if not NBA_API_AVAILABLE:
        return []
    try:
        return scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", [])
    except Exception:
        return []

def find_live_game(team):
    alias = TEAM_ALIASES[team]
    for game in get_live_games():
        if game.get("homeTeam", {}).get("teamTricode") == alias or game.get("awayTeam", {}).get("teamTricode") == alias:
            return game
    return None

def estimate_win_probability(margin, quarter, is_home, status):
    if status == "Eliminated":
        return 0
    base = 52 + (3 if is_home else 0)
    pressure = quarter * 3
    raw = base + margin * 2.5 + pressure
    return int(max(1, min(99, raw)))

@st.cache_data(ttl=900)
def get_player_id(player_name):
    if not NBA_API_AVAILABLE:
        return None
    try:
        matches = [p for p in nba_players.get_players() if p["full_name"] == player_name]
        return matches[0]["id"] if matches else None
    except Exception:
        return None

@st.cache_data(ttl=900)
def get_player_logs(player_id, season="2025-26"):
    if not NBA_API_AVAILABLE or player_id is None:
        return pd.DataFrame()
    try:
        logs = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star="Playoffs")
        return logs.get_data_frames()[0]
    except Exception:
        return pd.DataFrame()

def render_bracket_cards():
    st.subheader("2026 NBA Playoff Bracket")
    st.caption("Second round is shown as the current main bracket. First round results remain available in First Round Review.")
    col_e, col_w = st.columns(2)
    with col_e:
        st.markdown("### Eastern Conference")
        for s in FIRST_ROUND_SERIES[:4]:
            st.markdown(f"**First Round:** ({s['a_seed']}) {s['a']} {s['a_wins']} — {s['b_wins']} ({s['b_seed']}) {s['b']}  ")
        st.divider()
        for s in SECOND_ROUND_SERIES[:2]:
            st.markdown(f"**Second Round:** ({s['a_seed']}) {s['a']} {s['a_wins']} — {s['b_wins']} ({s['b_seed']}) {s['b']}")
    with col_w:
        st.markdown("### Western Conference")
        for s in FIRST_ROUND_SERIES[4:]:
            st.markdown(f"**First Round:** ({s['a_seed']}) {s['a']} {s['a_wins']} — {s['b_wins']} ({s['b_seed']}) {s['b']}  ")
        st.divider()
        for s in SECOND_ROUND_SERIES[2:]:
            st.markdown(f"**Second Round:** ({s['a_seed']}) {s['a']} {s['a_wins']} — {s['b_wins']} ({s['b_seed']}) {s['b']}")
    bracket_df = pd.DataFrame([
        {"Conference": s["conf"], "Round": "First Round", "Matchup": f"({s['a_seed']}) {s['a']} vs ({s['b_seed']}) {s['b']}", "Series": f"{s['a_wins']}-{s['b_wins']}", "Winner": s["winner"]}
        for s in FIRST_ROUND_SERIES
    ] + [
        {"Conference": s["conf"], "Round": "Second Round", "Matchup": f"({s['a_seed']}) {s['a']} vs ({s['b_seed']}) {s['b']}", "Series": f"{s['a_wins']}-{s['b_wins']}", "Winner": "TBD"}
        for s in SECOND_ROUND_SERIES
    ])
    st.dataframe(bracket_df, use_container_width=True, hide_index=True)
    fig = px.sunburst(bracket_df, path=["Conference", "Round", "Matchup"], title="Bracket Structure")
    st.plotly_chart(fig, use_container_width=True)

favorite_team = st.sidebar.selectbox("Choose your 2026 playoff team", list(TEAM_PROFILES.keys()), index=list(TEAM_PROFILES.keys()).index("New York Knicks"))
page = st.sidebar.radio("Choose page", [
    "Team Command Center",
    "Live Game Center",
    "Series Preview / Recap",
    "First Round Review",
    "Matchup Lineups",
    "Player Playoff Tracker",
    "Legacy Tracker",
    "Other Series Watch",
    "Playoff Bracket",
    "AI Prediction Center",
])

p = profile(favorite_team)

if page == "Team Command Center":
    current_round_header(favorite_team)
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", p["status"])
    c2.metric("Current round", p["current_round"])
    c3.metric("First-round result", p["first_result"])
    if p["status"] == "Active":
        st.subheader("Current series focus")
        st.write(f"{favorite_team} is in the second round against {p['current_opponent']}.")
        if favorite_team in SERIES_SCHEDULES:
            st.dataframe(SERIES_SCHEDULES[favorite_team], use_container_width=True, hide_index=True)
    else:
        render_first_round_review(favorite_team)
    team_strengths_concerns(favorite_team)

elif page == "Live Game Center":
    current_round_header(favorite_team)
    st.subheader("Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_game_refresh")
        st.caption("Updates every 30 seconds during games.")
    if not NBA_API_AVAILABLE:
        st.error("nba_api is not available. Check requirements.txt.")
    else:
        game = find_live_game(favorite_team)
        if not game:
            st.warning("No live or scheduled game found for this team today.")
        else:
            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})
            home_name = ALIAS_TO_TEAM.get(home.get("teamTricode"), home.get("teamName", "Home"))
            away_name = ALIAS_TO_TEAM.get(away.get("teamTricode"), away.get("teamName", "Away"))
            home_score = int(home.get("score", 0) or 0)
            away_score = int(away.get("score", 0) or 0)
            status = game.get("gameStatusText", "")
            st.write(f"### {away_name} at {home_name}")
            st.write(f"**Status:** {status}")
            c1, c2 = st.columns(2)
            c1.metric(away_name, away_score)
            c2.metric(home_name, home_score)
            team_alias = TEAM_ALIASES[favorite_team]
            is_home = home.get("teamTricode") == team_alias
            margin = (home_score - away_score) if is_home else (away_score - home_score)
            try:
                q = int(game.get("period", 1))
            except Exception:
                q = 1
            prob = estimate_win_probability(margin, q, is_home, p["status"])
            st.metric("Estimated live win probability", f"{prob}%")
            if margin >= 10:
                st.success(f"{favorite_team} is controlling the game. The biggest priorities are avoiding turnovers, closing possessions with rebounds, and protecting the lead.")
            elif margin >= 1:
                st.info(f"{favorite_team} has a small edge. The next few possessions can strongly shape the win probability.")
            elif margin == 0:
                st.warning("The game is tied. Late-clock shot quality, rebounding, and foul trouble matter most now.")
            elif margin >= -7:
                st.warning(f"{favorite_team} is close enough to flip the game with one run.")
            else:
                st.error(f"{favorite_team} needs a momentum shift: stops, clean looks, and fewer empty possessions.")

elif page == "Series Preview / Recap":
    current_round_header(favorite_team)
    if p["status"] == "Active":
        st.subheader("Second Round Preview")
        st.write(f"Current matchup: {favorite_team} vs {p['current_opponent']}.")
        team_strengths_concerns(favorite_team)
        if favorite_team in SERIES_SCHEDULES:
            st.dataframe(SERIES_SCHEDULES[favorite_team], use_container_width=True, hide_index=True)
    else:
        render_first_round_review(favorite_team)

elif page == "First Round Review":
    render_first_round_review(favorite_team)

elif page == "Matchup Lineups":
    current_round_header(favorite_team)
    st.subheader("Projected rotation")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Starters")
        for player in p["starters"]:
            st.write(f"• {player}")
    with col2:
        st.markdown("### Main subs")
        for player in p["subs"]:
            st.write(f"• {player}")

elif page == "Player Playoff Tracker":
    current_round_header(favorite_team)
    roster = p["starters"] + p["subs"]
    player = st.selectbox("Choose player", roster)
    season = st.selectbox("Season", ["2025-26", "2024-25", "2023-24"], index=0)
    player_id = get_player_id(player)
    logs = get_player_logs(player_id, season)
    if logs.empty:
        st.warning(f"No official playoff game logs loaded for {player} in {season}.")
    else:
        cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS"] if c in logs.columns]
        st.dataframe(logs[cols], use_container_width=True, hide_index=True)
        stat = st.selectbox("Choose stat", [c for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "PLUS_MINUS", "MIN"] if c in logs.columns])
        chart = logs.copy().sort_values("GAME_DATE")
        chart["Game Number"] = range(1, len(chart) + 1)
        fig = px.line(chart, x="Game Number", y=stat, markers=True, hover_data=["GAME_DATE", "MATCHUP", "WL"], title=f"{player} {stat} — playoff game log")
        st.plotly_chart(fig, use_container_width=True)
        st.metric(f"Average {stat}", round(chart[stat].mean(), 2))

elif page == "Legacy Tracker":
    current_round_header(favorite_team)
    player = st.selectbox("Choose player", p["starters"])
    st.subheader(f"{player} Legacy Tracker")
    st.write("This section evaluates how another playoff round, a deeper run, or a major statistical series changes the player's franchise meaning.")
    pts = st.slider("Playoff scoring average", 0, 45, 22)
    reb = st.slider("Playoff rebounding average", 0, 20, 6)
    ast = st.slider("Playoff assists average", 0, 15, 4)
    wins = st.slider("Series won this playoff run", 0, 4, 1)
    score = min(100, round(50 + pts*0.6 + reb*0.7 + ast*0.5 + wins*10, 1))
    st.metric("Legacy Impact Score", score)

elif page == "Other Series Watch":
    current_round_header(favorite_team)
    rows = []
    for name, data in TEAM_PROFILES.items():
        rows.append({"Team": name, "Conference": data["conference"], "Seed": data["seed"], "Status": data["status"], "Current round": data["current_round"], "First round": data["first_result"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Playoff Bracket":
    render_bracket_cards()

elif page == "AI Prediction Center":
    current_round_header(favorite_team)
    margin = st.slider("Current score margin for selected team", -30, 30, 0)
    quarter = st.slider("Current quarter", 1, 4, 2)
    is_home = st.checkbox("Selected team is home", value=True)
    prob = estimate_win_probability(margin, quarter, is_home, p["status"])
    st.metric("Estimated win probability", f"{prob}%")
    fig = px.pie(pd.DataFrame({"Outcome": [f"{favorite_team} wins", "Opponent wins"], "Probability": [prob, 100-prob]}), names="Outcome", values="Probability")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | First Round Review uses first-round matchup only; live stats use NBA API when available.")
