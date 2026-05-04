import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except Exception:
    STATSMODELS_AVAILABLE = False

try:
    from nba_api.live.nba.endpoints import scoreboard
    NBA_API_AVAILABLE = True
except Exception:
    NBA_API_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

st.set_page_config(
    page_title="Daniel Cohen — NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 playoff-only fan companion app with live-data structure, matchup analysis, player tracking, and legacy tracking")

# ---------------------------------------------------
# TEAM DATA
# ---------------------------------------------------

PLAYOFF_TEAMS = {
    "Detroit Pistons": {"conference": "East", "status": "Active", "seed": 6, "round": "Second Round", "result": "Defeated Orlando Magic", "players": ["Cade Cunningham", "Tobias Harris", "Ausar Thompson", "Jalen Duren", "Isaiah Stewart"]},
    "Boston Celtics": {"conference": "East", "status": "Eliminated", "seed": 2, "round": "Lost First Round", "result": "Lost to Philadelphia 76ers", "players": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis", "Derrick White", "Jrue Holiday"]},
    "New York Knicks": {"conference": "East", "status": "Active", "seed": 3, "round": "Second Round", "result": "Defeated Atlanta Hawks", "players": ["Jalen Brunson", "Karl-Anthony Towns", "OG Anunoby", "Mikal Bridges", "Josh Hart"]},
    "Cleveland Cavaliers": {"conference": "East", "status": "Pending", "seed": 4, "round": "First Round Pending", "result": "Still playing Toronto Raptors", "players": ["Donovan Mitchell", "Darius Garland", "Evan Mobley", "Jarrett Allen", "Max Strus"]},
    "Toronto Raptors": {"conference": "East", "status": "Pending", "seed": 5, "round": "First Round Pending", "result": "Still playing Cleveland Cavaliers", "players": ["Scottie Barnes", "RJ Barrett", "Immanuel Quickley", "Jakob Poeltl", "Gradey Dick"]},
    "Atlanta Hawks": {"conference": "East", "status": "Eliminated", "seed": 7, "round": "Lost First Round", "result": "Lost to New York Knicks", "players": ["Trae Young", "Jalen Johnson", "Dejounte Murray", "Clint Capela", "Bogdan Bogdanovic"]},
    "Philadelphia 76ers": {"conference": "East", "status": "Active", "seed": 7, "round": "Second Round", "result": "Defeated Boston Celtics", "players": ["Tyrese Maxey", "VJ Edgecombe", "Kelly Oubre Jr.", "Paul George", "Joel Embiid"]},
    "Orlando Magic": {"conference": "East", "status": "Eliminated", "seed": 8, "round": "Lost First Round", "result": "Lost to Detroit Pistons", "players": ["Paolo Banchero", "Franz Wagner", "Jalen Suggs", "Wendell Carter Jr.", "Cole Anthony"]},
    "Oklahoma City Thunder": {"conference": "West", "status": "Active", "seed": 1, "round": "Second Round", "result": "Defeated Phoenix Suns", "players": ["Shai Gilgeous-Alexander", "Jalen Williams", "Chet Holmgren", "Lu Dort", "Isaiah Hartenstein"]},
    "San Antonio Spurs": {"conference": "West", "status": "Active", "seed": 6, "round": "Second Round", "result": "Defeated Portland Trail Blazers", "players": ["Victor Wembanyama", "Devin Vassell", "Stephon Castle", "Keldon Johnson", "Jeremy Sochan"]},
    "Denver Nuggets": {"conference": "West", "status": "Eliminated", "seed": 4, "round": "Lost First Round", "result": "Lost to Minnesota Timberwolves", "players": ["Nikola Jokic", "Jamal Murray", "Aaron Gordon", "Michael Porter Jr.", "Christian Braun"]},
    "Los Angeles Lakers": {"conference": "West", "status": "Active", "seed": 5, "round": "Second Round", "result": "Defeated Houston Rockets", "players": ["LeBron James", "Anthony Davis", "Austin Reaves", "Rui Hachimura", "D'Angelo Russell"]},
    "Houston Rockets": {"conference": "West", "status": "Eliminated", "seed": 4, "round": "Lost First Round", "result": "Lost to Los Angeles Lakers", "players": ["Alperen Sengun", "Jalen Green", "Amen Thompson", "Fred VanVleet", "Jabari Smith Jr."]},
    "Minnesota Timberwolves": {"conference": "West", "status": "Active", "seed": 3, "round": "Second Round", "result": "Defeated Denver Nuggets", "players": ["Anthony Edwards", "Jaden McDaniels", "Rudy Gobert", "Mike Conley", "Naz Reid"]},
    "Portland Trail Blazers": {"conference": "West", "status": "Eliminated", "seed": 7, "round": "Lost First Round", "result": "Lost to San Antonio Spurs", "players": ["Scoot Henderson", "Shaedon Sharpe", "Deandre Ayton", "Jerami Grant", "Anfernee Simons"]},
    "Phoenix Suns": {"conference": "West", "status": "Eliminated", "seed": 8, "round": "Lost First Round", "result": "Lost to Oklahoma City Thunder", "players": ["Devin Booker", "Kevin Durant", "Bradley Beal", "Jusuf Nurkic", "Grayson Allen"]},
}

TEAM_ALIASES = {
    "Detroit Pistons": "DET", "Boston Celtics": "BOS", "New York Knicks": "NYK", "Cleveland Cavaliers": "CLE",
    "Toronto Raptors": "TOR", "Atlanta Hawks": "ATL", "Philadelphia 76ers": "PHI", "Orlando Magic": "ORL",
    "Oklahoma City Thunder": "OKC", "San Antonio Spurs": "SAS", "Denver Nuggets": "DEN", "Los Angeles Lakers": "LAL",
    "Houston Rockets": "HOU", "Minnesota Timberwolves": "MIN", "Portland Trail Blazers": "POR", "Phoenix Suns": "PHX",
}

TEAM_LOGOS = {
    "New York Knicks": "https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg",
    "Philadelphia 76ers": "https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg",
    "Detroit Pistons": "https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg",
    "Boston Celtics": "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
    "Cleveland Cavaliers": "https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg",
    "Toronto Raptors": "https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg",
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

AUTO_SERIES = {
    "New York Knicks": {"opponent": "Philadelphia 76ers", "series_name": "3 New York Knicks vs 7 Philadelphia 76ers", "round": "Second Round", "current_game_focus": "Game 1", "game_1_probability": 61, "series_probability": 58, "most_likely_result": "Knicks in 6"},
    "Philadelphia 76ers": {"opponent": "New York Knicks", "series_name": "7 Philadelphia 76ers vs 3 New York Knicks", "round": "Second Round", "current_game_focus": "Game 1", "game_1_probability": 39, "series_probability": 42, "most_likely_result": "Knicks in 6"},
    "Oklahoma City Thunder": {"opponent": "Los Angeles Lakers", "series_name": "1 Oklahoma City Thunder vs 5 Los Angeles Lakers", "round": "Second Round", "current_game_focus": "Game 1", "game_1_probability": 57, "series_probability": 55, "most_likely_result": "Thunder in 7"},
    "Los Angeles Lakers": {"opponent": "Oklahoma City Thunder", "series_name": "5 Los Angeles Lakers vs 1 Oklahoma City Thunder", "round": "Second Round", "current_game_focus": "Game 1", "game_1_probability": 43, "series_probability": 45, "most_likely_result": "Thunder in 7"},
    "San Antonio Spurs": {"opponent": "Minnesota Timberwolves", "series_name": "6 San Antonio Spurs vs 3 Minnesota Timberwolves", "round": "Second Round", "current_game_focus": "Game 1", "game_1_probability": 48, "series_probability": 46, "most_likely_result": "Timberwolves in 6"},
    "Minnesota Timberwolves": {"opponent": "San Antonio Spurs", "series_name": "3 Minnesota Timberwolves vs 6 San Antonio Spurs", "round": "Second Round", "current_game_focus": "Game 1", "game_1_probability": 52, "series_probability": 54, "most_likely_result": "Timberwolves in 6"},
}

KNICKS_SIXERS_SCHEDULE = pd.DataFrame([
    {"Game": "Game 1", "Date": "Mon, May 4", "Time": "8:00 PM ET", "Matchup": "76ers at Knicks", "Location": "Madison Square Garden", "TV": "NBC / Peacock"},
    {"Game": "Game 2", "Date": "Wed, May 6", "Time": "7:00 PM ET", "Matchup": "76ers at Knicks", "Location": "Madison Square Garden", "TV": "ESPN"},
    {"Game": "Game 3", "Date": "Fri, May 8", "Time": "7:00 PM ET", "Matchup": "Knicks at 76ers", "Location": "Philadelphia", "TV": "Prime Video"},
    {"Game": "Game 4", "Date": "Sun, May 10", "Time": "3:30 PM ET", "Matchup": "Knicks at 76ers", "Location": "Philadelphia", "TV": "ABC"},
    {"Game": "Game 5", "Date": "Tue, May 12", "Time": "TBD", "Matchup": "76ers at Knicks", "Location": "Madison Square Garden", "TV": "TBD"},
    {"Game": "Game 6", "Date": "Thu, May 14", "Time": "TBD", "Matchup": "Knicks at 76ers", "Location": "Philadelphia", "TV": "TBD"},
    {"Game": "Game 7", "Date": "Sun, May 17", "Time": "TBD", "Matchup": "76ers at Knicks", "Location": "Madison Square Garden", "TV": "TBD"},
])

# ---------------------------------------------------
# SAMPLE PLAYER GAME LOGS — replace with live data later
# ---------------------------------------------------

KNICKS_PLAYERS_10 = [
    "Jalen Brunson", "Karl-Anthony Towns", "OG Anunoby", "Mikal Bridges", "Josh Hart",
    "Miles McBride", "Mitchell Robinson", "Precious Achiuwa", "Cameron Payne", "Landry Shamet"
]

PLAYOFF_PLAYER_GAME_LOGS = pd.DataFrame([
    {"Player": "Jalen Brunson", "Series": "First Round vs Hawks", "Game": 1, "PTS": 34, "REB": 4, "AST": 8, "STL": 1, "BLK": 0, "TO": 3, "FG%": 48, "3P%": 38, "MIN": 41},
    {"Player": "Jalen Brunson", "Series": "First Round vs Hawks", "Game": 2, "PTS": 29, "REB": 3, "AST": 10, "STL": 2, "BLK": 0, "TO": 2, "FG%": 44, "3P%": 33, "MIN": 39},
    {"Player": "Jalen Brunson", "Series": "First Round vs Hawks", "Game": 3, "PTS": 41, "REB": 5, "AST": 7, "STL": 1, "BLK": 0, "TO": 4, "FG%": 52, "3P%": 42, "MIN": 43},
    {"Player": "Jalen Brunson", "Series": "First Round vs Hawks", "Game": 4, "PTS": 27, "REB": 4, "AST": 9, "STL": 1, "BLK": 0, "TO": 3, "FG%": 41, "3P%": 30, "MIN": 40},
    {"Player": "Jalen Brunson", "Series": "First Round vs Hawks", "Game": 5, "PTS": 38, "REB": 6, "AST": 8, "STL": 2, "BLK": 0, "TO": 2, "FG%": 50, "3P%": 40, "MIN": 42},
    {"Player": "Jalen Brunson", "Series": "First Round vs Hawks", "Game": 6, "PTS": 36, "REB": 4, "AST": 11, "STL": 1, "BLK": 0, "TO": 3, "FG%": 47, "3P%": 36, "MIN": 44},
    {"Player": "Karl-Anthony Towns", "Series": "First Round vs Hawks", "Game": 1, "PTS": 24, "REB": 11, "AST": 3, "STL": 1, "BLK": 1, "TO": 2, "FG%": 50, "3P%": 39, "MIN": 37},
    {"Player": "Karl-Anthony Towns", "Series": "First Round vs Hawks", "Game": 2, "PTS": 21, "REB": 13, "AST": 4, "STL": 0, "BLK": 2, "TO": 3, "FG%": 46, "3P%": 35, "MIN": 36},
    {"Player": "Karl-Anthony Towns", "Series": "First Round vs Hawks", "Game": 3, "PTS": 28, "REB": 10, "AST": 5, "STL": 1, "BLK": 1, "TO": 2, "FG%": 55, "3P%": 44, "MIN": 39},
    {"Player": "Karl-Anthony Towns", "Series": "First Round vs Hawks", "Game": 4, "PTS": 19, "REB": 14, "AST": 2, "STL": 1, "BLK": 1, "TO": 2, "FG%": 43, "3P%": 31, "MIN": 35},
    {"Player": "Karl-Anthony Towns", "Series": "First Round vs Hawks", "Game": 5, "PTS": 26, "REB": 12, "AST": 4, "STL": 0, "BLK": 2, "TO": 1, "FG%": 52, "3P%": 41, "MIN": 38},
    {"Player": "Karl-Anthony Towns", "Series": "First Round vs Hawks", "Game": 6, "PTS": 23, "REB": 15, "AST": 3, "STL": 1, "BLK": 1, "TO": 2, "FG%": 49, "3P%": 37, "MIN": 40},
    {"Player": "OG Anunoby", "Series": "First Round vs Hawks", "Game": 1, "PTS": 16, "REB": 6, "AST": 2, "STL": 2, "BLK": 1, "TO": 1, "FG%": 45, "3P%": 36, "MIN": 38},
    {"Player": "Mikal Bridges", "Series": "First Round vs Hawks", "Game": 1, "PTS": 18, "REB": 5, "AST": 4, "STL": 1, "BLK": 1, "TO": 1, "FG%": 47, "3P%": 39, "MIN": 39},
    {"Player": "Josh Hart", "Series": "First Round vs Hawks", "Game": 1, "PTS": 11, "REB": 12, "AST": 6, "STL": 1, "BLK": 0, "TO": 2, "FG%": 42, "3P%": 31, "MIN": 37},
    {"Player": "Jalen Brunson", "Series": "Second Round vs 76ers", "Game": 1, "PTS": 0, "REB": 0, "AST": 0, "STL": 0, "BLK": 0, "TO": 0, "FG%": 0, "3P%": 0, "MIN": 0},
    {"Player": "Karl-Anthony Towns", "Series": "Second Round vs 76ers", "Game": 1, "PTS": 0, "REB": 0, "AST": 0, "STL": 0, "BLK": 0, "TO": 0, "FG%": 0, "3P%": 0, "MIN": 0},
])

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

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


def estimate_win_probability(score_margin, quarter, is_home, status):
    if status == "Eliminated":
        return 0
    base = 50 if status == "Pending" else 55
    time_pressure = quarter * 3
    home_bonus = 3 if is_home else 0
    raw = base + (score_margin * 2.4) + time_pressure + home_bonus
    return int(max(1, min(99, raw)))


def statsmodels_probability(score_margin, quarter, is_home):
    if not STATSMODELS_AVAILABLE:
        return None
    try:
        train = pd.DataFrame({
            "score_margin": [-20, -15, -10, -5, 0, 5, 10, 15, 20, 25],
            "quarter": [1, 2, 2, 3, 3, 3, 4, 4, 4, 4],
            "is_home": [0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
            "won": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })
        X = sm.add_constant(train[["score_margin", "quarter", "is_home"]])
        y = train["won"]
        model = sm.Logit(y, X).fit(disp=False)
        test = pd.DataFrame({"score_margin": [score_margin], "quarter": [quarter], "is_home": [1 if is_home else 0]})
        test = sm.add_constant(test, has_constant="add")
        return int(round(float(model.predict(test)[0]) * 100))
    except Exception:
        return None


def show_header():
    series = AUTO_SERIES.get(favorite_team)
    opponent = series["opponent"] if series else None
    logo1 = TEAM_LOGOS.get(favorite_team)
    logo2 = TEAM_LOGOS.get(opponent) if opponent else None

    if series and logo1 and logo2:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.image(logo1, width=125)
        with col2:
            st.markdown(f"<h1 style='text-align:center;'>{series['series_name']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;'>{series['round']} — {series['current_game_focus']} Focus</h3>", unsafe_allow_html=True)
        with col3:
            st.image(logo2, width=125)
    else:
        st.header(f"{favorite_team} Playoff Companion")

    team = PLAYOFF_TEAMS[favorite_team]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Seed", team["seed"])
    c2.metric("Conference", team["conference"])
    c3.metric("Status", team["status"])
    c4.metric("Round", team["round"])
    st.info(f"Current result: {team['result']}")


def show_eliminated_message():
    team = PLAYOFF_TEAMS[favorite_team]
    st.error(f"{favorite_team} are out of the playoffs.")
    st.write(f"**Result:** {team['result']}")
    st.info("The app now shifts to recap mode: what went well, what went wrong, and what the team needs next season. Best of luck next season.")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

favorite_team = st.sidebar.selectbox(
    "Choose your 2026 playoff team",
    list(PLAYOFF_TEAMS.keys()),
    index=list(PLAYOFF_TEAMS.keys()).index("New York Knicks")
)
team = PLAYOFF_TEAMS[favorite_team]

page = st.sidebar.radio(
    "Choose page",
    [
        "Home Dashboard",
        "Series Command Center",
        "Live Game Center",
        "Matchup Lineups",
        "Player Playoff Tracker",
        "Legacy Tracker",
        "Playoff Bracket",
        "Other Series Watch",
        "AI Prediction Center",
    ]
)

# ---------------------------------------------------
# PAGES
# ---------------------------------------------------

if page == "Home Dashboard":
    show_header()
    st.subheader("App Purpose")
    st.write("This is a playoff-only fan companion app. It follows the 16 playoff teams and changes its analysis depending on whether the selected team is active, eliminated, or pending.")
    if team["status"] == "Active":
        st.success(f"{favorite_team} are still alive. The app focuses on their current series, upcoming game, live probability, and path forward.")
    elif team["status"] == "Eliminated":
        show_eliminated_message()
    else:
        st.warning(f"{favorite_team} are pending. Once the result is final, this app should switch to active or eliminated mode.")

elif page == "Series Command Center":
    show_header()
    series = AUTO_SERIES.get(favorite_team)
    if team["status"] == "Eliminated":
        show_eliminated_message()
    elif not series:
        st.warning("Automatic current-series data is not loaded yet for this team.")
    else:
        st.subheader(f"{series['series_name']} — {series['round']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Series Win Probability", f"{series['series_probability']}%")
        c2.metric("Game 1 Win Probability", f"{series['game_1_probability']}%")
        c3.metric("Most Likely Outcome", series["most_likely_result"])

        if favorite_team in ["New York Knicks", "Philadelphia 76ers"]:
            st.subheader("Series Schedule")
            st.dataframe(KNICKS_SIXERS_SCHEDULE, use_container_width=True)

        if favorite_team == "New York Knicks":
            st.subheader("Game 1 Preview From the Knicks Perspective")
            st.success("The Knicks have a favorable Game 1 setup because they are home at Madison Square Garden, Brunson gives them elite late-game creation, and their wing defense/rebounding can put pressure on Philadelphia.")
            st.subheader("What Has To Go Right For The Knicks In Game 1")
            for key in [
                "Brunson needs to control tempo and punish switches.",
                "Towns needs to pull Embiid away from the rim and create spacing.",
                "The Knicks need to win the rebounding battle.",
                "OG Anunoby and Mikal Bridges need to make Maxey work for everything.",
                "The Knicks need to avoid cheap fouls on Embiid.",
                "Bench minutes need to stay even or slightly positive.",
                "The Knicks need to protect home court and set the tone physically.",
            ]:
                st.write(f"• {key}")
            st.subheader("Sixers Weaknesses The Knicks Can Attack")
            for weakness in [
                "Embiid's health and mobility are the biggest swing factors.",
                "Philadelphia can become too dependent on Embiid and Maxey.",
                "The Sixers' bench depth can be inconsistent.",
                "If the Knicks force Maxey into half-court possessions, Philadelphia loses some speed advantage.",
                "Towns can drag Embiid away from the rim, opening driving lanes for Brunson.",
            ]:
                st.warning(weakness)
        else:
            st.info(f"This page is written from the {favorite_team} perspective. It should explain the current series, Game 1 focus, and the team's path forward.")

elif page == "Live Game Center":
    show_header()
    st.subheader("Live Game Center")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="live_refresh")
        st.caption("Live data refreshes every 30 seconds during games.")
    else:
        st.warning("streamlit-autorefresh is not installed. Add streamlit-autorefresh to requirements.txt for 30-second refresh.")

    if not NBA_API_AVAILABLE:
        st.error("nba_api is not installed or failed to load. Add nba_api to requirements.txt and redeploy.")
    else:
        live_game = find_team_live_game(favorite_team)
        if live_game is None:
            st.warning("No live or scheduled game found for this team today.")
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
            team_alias = TEAM_ALIASES[favorite_team]
            is_home = home.get("teamTricode") == team_alias
            team_score = home_score if is_home else away_score
            opponent_score = away_score if is_home else home_score
            score_margin = team_score - opponent_score
            try:
                quarter = int(live_game.get("period", 1))
            except Exception:
                quarter = 1
            heuristic_prob = estimate_win_probability(score_margin, quarter, is_home, team["status"])
            model_prob = statsmodels_probability(score_margin, quarter, is_home)
            final_prob = model_prob if model_prob is not None else heuristic_prob
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{favorite_team} Win Probability", f"{final_prob}%")
            c2.metric("Score Margin", score_margin)
            c3.metric("Quarter", quarter)
            prob_df = pd.DataFrame({"Outcome": [f"{favorite_team} Wins", "Opponent Wins"], "Probability": [final_prob, 100 - final_prob]})
            fig = px.pie(prob_df, names="Outcome", values="Probability", title="Live Win Probability")
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("AI Live Game Read")
            if score_margin >= 10:
                st.success(f"Very favorable: {favorite_team} are ahead by double digits. The priority is to avoid turnovers, protect the glass, and keep forcing difficult shots.")
            elif score_margin >= 5:
                st.success(f"Favorable: {favorite_team} are controlling the game slightly. In playoff games, this cushion matters because late-game possessions usually tighten.")
            elif score_margin >= 1:
                st.info(f"Positive but fragile: {favorite_team} are slightly ahead. The next few possessions can move win probability quickly.")
            elif score_margin == 0:
                st.warning("The game is tied. It is still very winnable, but execution and turnover control are critical now.")
            elif score_margin >= -5:
                st.warning(f"Close but trailing: {favorite_team} are still in range. A short scoring run or defensive adjustment can flip the game.")
            else:
                st.error(f"Difficult position: {favorite_team} need stops, better shot quality, and a momentum shift.")

            if favorite_team == "New York Knicks":
                st.subheader("Knicks-Specific Live Watch")
                st.write("• Is Brunson getting to his spots?")
                st.write("• Is Towns spacing the floor and pulling the opposing big away from the rim?")
                st.write("• Are the Knicks winning offensive rebounds?")
                st.write("• Are OG and Bridges slowing Maxey and the wings?")
                st.write("• Are the Knicks avoiding foul trouble?")

elif page == "Matchup Lineups":
    show_header()
    series = AUTO_SERIES.get(favorite_team)
    if not series:
        st.warning("No automatic matchup lineup loaded for this team yet.")
    else:
        opponent = series["opponent"]
        st.subheader(f"{series['series_name']} — Lineup Matchups")
        if favorite_team in ["New York Knicks", "Philadelphia 76ers"]:
            lineup_data = pd.DataFrame([
                {"Position": "Point Guard", "Knicks": "Jalen Brunson", "76ers": "Tyrese Maxey", "Advantage": "Knicks", "Analysis": "Brunson has the half-court and clutch creation edge; Maxey has speed and rim pressure."},
                {"Position": "Shooting Guard", "Knicks": "Mikal Bridges", "76ers": "VJ Edgecombe", "Advantage": "Knicks", "Analysis": "Bridges gives more proven two-way stability."},
                {"Position": "Small Forward", "Knicks": "OG Anunoby", "76ers": "Kelly Oubre Jr.", "Advantage": "Knicks", "Analysis": "OG's defense and physicality give New York a strong wing edge."},
                {"Position": "Power Forward", "Knicks": "Josh Hart", "76ers": "Paul George", "Advantage": "76ers", "Analysis": "George has the skill/scoring advantage if healthy; Hart brings rebounding and toughness."},
                {"Position": "Center", "Knicks": "Karl-Anthony Towns", "76ers": "Joel Embiid", "Advantage": "76ers", "Analysis": "Embiid is the biggest Sixers advantage; Towns gives the Knicks spacing and offensive versatility."},
            ])
            st.dataframe(lineup_data, use_container_width=True)
            st.subheader("Main Subs")
            bench = pd.DataFrame([
                {"Team": "Knicks", "Player": "Miles McBride", "Role": "Guard defense, ball pressure, spot-up shooting"},
                {"Team": "Knicks", "Player": "Mitchell Robinson", "Role": "Rim protection, offensive rebounding, Embiid minutes"},
                {"Team": "Knicks", "Player": "Precious Achiuwa", "Role": "Energy, switching, rebounding"},
                {"Team": "Knicks", "Player": "Cameron Payne", "Role": "Backup guard creation and pace"},
                {"Team": "Knicks", "Player": "Landry Shamet", "Role": "Floor spacing and shooting"},
                {"Team": "76ers", "Player": "Andre Drummond", "Role": "Backup center, rebounding, physicality"},
                {"Team": "76ers", "Player": "Kyle Lowry", "Role": "Veteran control and playoff toughness"},
                {"Team": "76ers", "Player": "Eric Gordon", "Role": "Shooting and veteran spacing"},
                {"Team": "76ers", "Player": "Caleb Martin", "Role": "Wing defense and playoff energy"},
                {"Team": "76ers", "Player": "Kelly Oubre Jr.", "Role": "Wing scoring and transition attacks"},
            ])
            st.dataframe(bench, use_container_width=True)
            st.info("Swing factors: Embiid's health, Knicks three-point shooting, Brunson traps, bench minutes, and who wins the rebounding battle.")
        else:
            st.info(f"Lineup matchup page for {favorite_team} vs {opponent} can be expanded next.")

elif page == "Player Playoff Tracker":
    show_header()
    st.subheader("Player Playoff Tracker")
    players_for_tracker = KNICKS_PLAYERS_10 if favorite_team == "New York Knicks" else team["players"]
    selected_player = st.selectbox("Choose player", players_for_tracker)

    available_series = PLAYOFF_PLAYER_GAME_LOGS[PLAYOFF_PLAYER_GAME_LOGS["Player"] == selected_player]["Series"].unique()
    if len(available_series) == 0:
        st.warning("No playoff game log data loaded yet for this player. Later this can connect to live box scores.")
    else:
        selected_series = st.selectbox("Choose series", available_series)
        player_series_df = PLAYOFF_PLAYER_GAME_LOGS[(PLAYOFF_PLAYER_GAME_LOGS["Player"] == selected_player) & (PLAYOFF_PLAYER_GAME_LOGS["Series"] == selected_series)]
        stat_choice = st.selectbox("Choose stat", ["PTS", "REB", "AST", "STL", "BLK", "TO", "FG%", "3P%", "MIN"])
        st.subheader(f"{selected_player} — {selected_series}")
        st.dataframe(player_series_df, use_container_width=True)
        fig = px.line(player_series_df, x="Game", y=stat_choice, markers=True, title=f"{selected_player} {stat_choice} by Game — {selected_series}")
        st.plotly_chart(fig, use_container_width=True)
        avg_stat = player_series_df[stat_choice].mean()
        max_stat = player_series_df[stat_choice].max()
        min_stat = player_series_df[stat_choice].min()
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Average {stat_choice}", round(avg_stat, 1))
        c2.metric(f"Best Game {stat_choice}", max_stat)
        c3.metric(f"Lowest Game {stat_choice}", min_stat)
        st.subheader("AI Player Insight")
        if selected_player == "Jalen Brunson":
            st.success("Brunson is the Knicks' playoff engine. If he is scoring efficiently and keeping turnovers under control, the Knicks' half-court offense becomes much harder to guard.")
        elif selected_player == "Karl-Anthony Towns":
            st.success("Towns changes the geometry of the series. If he scores efficiently and shoots well from three, he pulls opposing bigs away from the rim and opens lanes for Brunson.")
        elif selected_player in ["OG Anunoby", "Mikal Bridges"]:
            st.info(f"{selected_player}'s value is not only scoring. Defensive assignment, wing pressure, steals, minutes, and three-point shooting all matter.")
        elif selected_player == "Josh Hart":
            st.info("Hart's value comes from rebounding, hustle, transition play, and extra possessions. Strong rebounding means the Knicks are winning the physical parts of the game.")
        else:
            st.write(f"{selected_player}'s role is about stabilizing non-star minutes, defending, avoiding mistakes, and hitting open shots.")

elif page == "Legacy Tracker":
    show_header()
    st.subheader("Knicks Legacy Tracker")
    KNICKS_STARTERS_LEGACY = {
        "Jalen Brunson": {"current": "Already one of the most important modern Knicks. Clear franchise leader of this era.", "main_stat": "Points", "good_series": "If he averages 30+ points and wins another round, he moves closer to top-10 Knicks status.", "conference_finals": "If he leads the Knicks to the Eastern Conference Finals, he becomes one of the defining Knicks guards ever.", "nba_finals": "If he leads the Knicks to the NBA Finals, he has a strong argument for top 6-8 Knicks player ever.", "championship": "If he wins a championship as the lead scorer, he could become a top 3-5 Knick ever."},
        "Karl-Anthony Towns": {"current": "Major Knicks star, but still building his Knicks-specific legacy.", "main_stat": "Points / Rebounds", "good_series": "If he scores efficiently and rebounds well, he becomes a major part of this Knicks playoff era.", "conference_finals": "A Conference Finals run would make him remembered as a key co-star in a breakthrough season.", "nba_finals": "A Finals run would make him one of the most important Knicks big men of the modern era.", "championship": "A championship would permanently connect him to Knicks history."},
        "OG Anunoby": {"current": "Elite role-star and defensive anchor, but not yet a Knicks legacy centerpiece.", "main_stat": "Defense / Efficiency", "good_series": "If he shuts down top scorers while hitting open threes, his Knicks value rises sharply.", "conference_finals": "A deep run would make him remembered as one of the key defensive pieces of this team.", "nba_finals": "A Finals run would elevate him as a championship-level defensive wing.", "championship": "A championship would make him a beloved Knicks role-star."},
        "Mikal Bridges": {"current": "Important Knicks wing, still early in his Knicks legacy.", "main_stat": "Defense / Shooting", "good_series": "If he defends elite scorers and hits key shots, he becomes central to this playoff identity.", "conference_finals": "A Conference Finals run would establish him as a major two-way playoff piece.", "nba_finals": "A Finals run would make him a defining part of this Knicks era.", "championship": "A championship would make him remembered as a crucial two-way piece in Knicks history."},
        "Josh Hart": {"current": "Fan favorite and identity player. His legacy is built on toughness, rebounding, and effort.", "main_stat": "Rebounds / Hustle", "good_series": "If he keeps rebounding at a high level, he strengthens his identity as a classic Knicks playoff player.", "conference_finals": "A Conference Finals run would make him one of the symbolic heart-and-soul players of this era.", "nba_finals": "A Finals run would make him a beloved Knicks cult hero.", "championship": "A championship would make him remembered forever as a winning Knicks role player."},
    }
    if favorite_team != "New York Knicks":
        st.warning("This legacy tracker is currently built for the Knicks five starters. Other teams can be added later.")
    selected = st.selectbox("Choose Knicks starter", list(KNICKS_STARTERS_LEGACY.keys()))
    legacy = KNICKS_STARTERS_LEGACY[selected]
    st.info(legacy["current"])
    st.write(f"**Main legacy stat focus:** {legacy['main_stat']}")
    legacy_df = pd.DataFrame({
        "Outcome This Season": ["Current status", "Strong Second Round", "Reach Conference Finals", "Reach NBA Finals", "Win Championship"],
        "Legacy Meaning": [legacy["current"], legacy["good_series"], legacy["conference_finals"], legacy["nba_finals"], legacy["championship"]],
        "Legacy Score": [55, 68, 78, 90, 100]
    })
    st.dataframe(legacy_df, use_container_width=True)
    fig = px.bar(legacy_df, x="Outcome This Season", y="Legacy Score", title=f"{selected} Legacy Growth Path")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Live Performance Adjustment")
    points = st.slider("Playoff scoring average", 0, 45, 22)
    rebounds = st.slider("Playoff rebounding average", 0, 20, 6)
    assists = st.slider("Playoff assists average", 0, 15, 4)
    series_wins = st.slider("Series won this playoff run", 0, 4, 1)
    performance_score = min(100, round(50 + points * 0.6 + rebounds * 0.7 + assists * 0.5 + series_wins * 10, 1))
    st.metric("Live Legacy Impact Score", performance_score)
    st.subheader("AI Legacy Interpretation")
    if selected == "Jalen Brunson" and performance_score >= 90:
        st.success("Brunson is entering historic Knicks territory. The conversation shifts from great modern Knick to all-time Knicks legend.")
    elif selected == "Jalen Brunson":
        st.info("Brunson is already the face of this Knicks era, but another deep playoff run is what pushes him into the highest franchise tier.")
    elif selected == "Karl-Anthony Towns":
        st.info("Towns' Knicks legacy depends on whether his shooting, rebounding, and spacing help unlock the offense in the biggest games.")
    elif selected in ["OG Anunoby", "Mikal Bridges"]:
        st.info(f"{selected}'s legacy depends less on raw points and more on two-way playoff impact: defense, timely threes, and winning possessions.")
    else:
        st.info("Hart's legacy is about identity: rebounding, toughness, defense, and winning plays.")

elif page == "Playoff Bracket":
    st.header("2026 NBA Playoff Bracket")
    bracket_data = pd.DataFrame([
        {"Conference": "East", "Round": "First Round", "Matchup": "Pistons vs Magic", "Result": "Pistons advance"},
        {"Conference": "East", "Round": "First Round", "Matchup": "Celtics vs 76ers", "Result": "76ers advance"},
        {"Conference": "East", "Round": "First Round", "Matchup": "Knicks vs Hawks", "Result": "Knicks advance"},
        {"Conference": "East", "Round": "First Round", "Matchup": "Cavaliers vs Raptors", "Result": "Pending"},
        {"Conference": "East", "Round": "Second Round", "Matchup": "Knicks vs 76ers", "Result": "Game 1 focus"},
        {"Conference": "East", "Round": "Second Round", "Matchup": "Pistons vs Cavaliers/Raptors", "Result": "Pending"},
        {"Conference": "West", "Round": "First Round", "Matchup": "Thunder vs Suns", "Result": "Thunder advance"},
        {"Conference": "West", "Round": "First Round", "Matchup": "Lakers vs Rockets", "Result": "Lakers advance"},
        {"Conference": "West", "Round": "First Round", "Matchup": "Spurs vs Trail Blazers", "Result": "Spurs advance"},
        {"Conference": "West", "Round": "First Round", "Matchup": "Nuggets vs Timberwolves", "Result": "Timberwolves advance"},
        {"Conference": "West", "Round": "Second Round", "Matchup": "Thunder vs Lakers", "Result": "Game 1 focus"},
        {"Conference": "West", "Round": "Second Round", "Matchup": "Spurs vs Timberwolves", "Result": "Game 1 focus"},
    ])
    st.dataframe(bracket_data, use_container_width=True)
    fig = px.sunburst(bracket_data, path=["Conference", "Round", "Matchup"], title="2026 NBA Playoff Bracket Structure")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Other Series Watch":
    show_header()
    status_df = pd.DataFrame([{"Team": name, "Seed": data["seed"], "Conference": data["conference"], "Status": data["status"], "Round": data["round"], "Result": data["result"]} for name, data in PLAYOFF_TEAMS.items()])
    st.dataframe(status_df, use_container_width=True)
    st.write("Other series matter because they affect future opponent difficulty, rest, injuries, travel, and matchup style.")

elif page == "AI Prediction Center":
    show_header()
    if team["status"] == "Eliminated":
        st.error("This team is eliminated, so future playoff probability is 0%.")
    else:
        score_margin = st.slider("Current score margin for your team", -30, 30, 0)
        quarter = st.slider("Current quarter", 1, 4, 2)
        is_home = st.checkbox("Is your team home?", value=True)
        heuristic_prob = estimate_win_probability(score_margin, quarter, is_home, team["status"])
        model_prob = statsmodels_probability(score_margin, quarter, is_home)
        c1, c2 = st.columns(2)
        c1.metric("Heuristic Probability", f"{heuristic_prob}%")
        c2.metric("Statsmodels Probability", f"{model_prob}%" if model_prob is not None else "Unavailable")
        prob_df = pd.DataFrame({"Outcome": [f"{favorite_team} Wins", "Opponent Wins"], "Probability": [heuristic_prob, 100 - heuristic_prob]})
        fig = px.pie(prob_df, names="Outcome", values="Probability", title="Win Probability")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("NBA Playoff Companion AI | Created by Daniel Cohen | Live-data capable prototype")
