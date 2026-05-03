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
    from nba_api.live.nba.endpoints import scoreboard, boxscore
    NBA_API_AVAILABLE = True
except Exception:
    NBA_API_AVAILABLE = False


st.set_page_config(
    page_title="NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 NBA Playoff Companion AI")
st.caption("2026 playoff-only app with live-data structure, win probability, and fan-centered analysis")


PLAYOFF_TEAMS = {
    "Detroit Pistons": {"conference": "East", "status": "Active", "round": "Second Round", "result": "Defeated Orlando Magic", "players": ["Cade Cunningham", "Jalen Duren", "Ausar Thompson"]},
    "Boston Celtics": {"conference": "East", "status": "Eliminated", "round": "Lost First Round", "result": "Lost to Philadelphia 76ers", "players": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis"]},
    "New York Knicks": {"conference": "East", "status": "Active", "round": "Second Round", "result": "Defeated Atlanta Hawks", "players": ["Jalen Brunson", "Karl-Anthony Towns", "Josh Hart", "Mikal Bridges"]},
    "Cleveland Cavaliers": {"conference": "East", "status": "Pending", "round": "First Round Pending", "result": "Still playing Toronto Raptors", "players": ["Donovan Mitchell", "Evan Mobley", "Darius Garland"]},
    "Toronto Raptors": {"conference": "East", "status": "Pending", "round": "First Round Pending", "result": "Still playing Cleveland Cavaliers", "players": ["Scottie Barnes", "RJ Barrett", "Immanuel Quickley"]},
    "Atlanta Hawks": {"conference": "East", "status": "Eliminated", "round": "Lost First Round", "result": "Lost to New York Knicks", "players": ["Trae Young", "Jalen Johnson", "Dejounte Murray"]},
    "Philadelphia 76ers": {"conference": "East", "status": "Active", "round": "Second Round", "result": "Defeated Boston Celtics", "players": ["Joel Embiid", "Tyrese Maxey", "Paul George"]},
    "Orlando Magic": {"conference": "East", "status": "Eliminated", "round": "Lost First Round", "result": "Lost to Detroit Pistons", "players": ["Paolo Banchero", "Franz Wagner", "Jalen Suggs"]},
    "Oklahoma City Thunder": {"conference": "West", "status": "Active", "round": "Second Round", "result": "Advanced from First Round", "players": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"]},
    "San Antonio Spurs": {"conference": "West", "status": "Active", "round": "Second Round", "result": "Advanced from First Round", "players": ["Victor Wembanyama", "Devin Vassell", "Stephon Castle"]},
    "Denver Nuggets": {"conference": "West", "status": "Eliminated", "round": "Lost First Round", "result": "Lost to Minnesota Timberwolves", "players": ["Nikola Jokic", "Jamal Murray", "Aaron Gordon"]},
    "Los Angeles Lakers": {"conference": "West", "status": "Active", "round": "Second Round", "result": "Defeated Houston Rockets", "players": ["LeBron James", "Anthony Davis", "Austin Reaves"]},
    "Houston Rockets": {"conference": "West", "status": "Eliminated", "round": "Lost First Round", "result": "Lost to Los Angeles Lakers", "players": ["Alperen Sengun", "Jalen Green", "Amen Thompson"]},
    "Minnesota Timberwolves": {"conference": "West", "status": "Active", "round": "Second Round", "result": "Defeated Denver Nuggets", "players": ["Anthony Edwards", "Rudy Gobert", "Jaden McDaniels"]},
    "Portland Trail Blazers": {"conference": "West", "status": "Eliminated", "round": "Lost First Round", "result": "Eliminated from playoffs", "players": ["Scoot Henderson", "Shaedon Sharpe", "Deandre Ayton"]},
    "Phoenix Suns": {"conference": "West", "status": "Eliminated", "round": "Lost First Round", "result": "Eliminated from playoffs", "players": ["Devin Booker", "Kevin Durant", "Bradley Beal"]},
}

TEAM_ALIASES = {
    "Detroit Pistons": "DET",
    "Boston Celtics": "BOS",
    "New York Knicks": "NYK",
    "Cleveland Cavaliers": "CLE",
    "Toronto Raptors": "TOR",
    "Atlanta Hawks": "ATL",
    "Philadelphia 76ers": "PHI",
    "Orlando Magic": "ORL",
    "Oklahoma City Thunder": "OKC",
    "San Antonio Spurs": "SAS",
    "Denver Nuggets": "DEN",
    "Los Angeles Lakers": "LAL",
    "Houston Rockets": "HOU",
    "Minnesota Timberwolves": "MIN",
    "Portland Trail Blazers": "POR",
    "Phoenix Suns": "PHX",
}


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

    if status == "Pending":
        base = 50
    else:
        base = 55

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

        X = train[["score_margin", "quarter", "is_home"]]
        X = sm.add_constant(X)
        y = train["won"]

        model = sm.Logit(y, X).fit(disp=False)

        test = pd.DataFrame({
            "score_margin": [score_margin],
            "quarter": [quarter],
            "is_home": [1 if is_home else 0]
        })
        test = sm.add_constant(test, has_constant="add")

        prob = float(model.predict(test)[0])
        return int(round(prob * 100))
    except Exception:
        return None


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
        "Live Game Center",
        "Series Preview",
        "Player Playoff Tracker",
        "Legacy Tracker",
        "Other Series Watch",
        "AI Prediction Center"
    ]
)


def show_header():
    st.header(f"{favorite_team} Playoff Companion")

    c1, c2, c3 = st.columns(3)
    c1.metric("Conference", team["conference"])
    c2.metric("Status", team["status"])
    c3.metric("Round", team["round"])

    st.info(f"First-round/current result: {team['result']}")


if page == "Home Dashboard":
    show_header()

    if team["status"] == "Active":
        st.success(f"{favorite_team} are still alive. The app analyzes their path forward.")
    elif team["status"] == "Eliminated":
        st.error(f"{favorite_team} are eliminated. The app now gives a playoff recap and next-season outlook.")
        st.write("Best of luck next season.")
    else:
        st.warning(f"{favorite_team} are pending. Their next result decides whether the app switches to active mode or recap mode.")

    st.subheader("Main Players")
    for player in team["players"]:
        st.write(f"• {player}")


elif page == "Live Game Center":
    show_header()

    st.subheader("Live Game Data")

    if not NBA_API_AVAILABLE:
        st.error("nba_api is not installed. Add nba_api to requirements.txt and redeploy.")
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
            st.write(f"**Status:** {status_text}")

            c1, c2 = st.columns(2)
            c1.metric(away_name, away_score)
            c2.metric(home_name, home_score)

            team_alias = TEAM_ALIASES[favorite_team]
            is_home = home.get("teamTricode") == team_alias

            if is_home:
                score_margin = home_score - away_score
            else:
                score_margin = away_score - home_score

            quarter = live_game.get("period", 1)
            try:
                quarter = int(quarter)
            except Exception:
                quarter = 1

            heuristic_prob = estimate_win_probability(
                score_margin=score_margin,
                quarter=quarter,
                is_home=is_home,
                status=team["status"]
            )

            model_prob = statsmodels_probability(
                score_margin=score_margin,
                quarter=quarter,
                is_home=is_home
            )

            st.subheader("Live Win Probability")

            c1, c2 = st.columns(2)
            c1.metric("Heuristic Win Probability", f"{heuristic_prob}%")

            if model_prob is not None:
                c2.metric("Statsmodels Probability", f"{model_prob}%")
            else:
                c2.metric("Statsmodels Probability", "Unavailable")

            st.write(
                f"""
                From a {favorite_team} fan perspective:

                - Current margin: {score_margin}
                - Quarter: {quarter}
                - Home game: {is_home}

                The model updates based on score margin, game stage, and home court.
                """
            )


elif page == "Series Preview":
    show_header()

    if team["status"] == "Eliminated":
        st.error("This team is out. Series preview has shifted to recap mode.")
        st.write(f"{favorite_team} result: {team['result']}")
    else:
        opponent = st.selectbox(
            "Choose opponent",
            [x for x in PLAYOFF_TEAMS.keys() if x != favorite_team]
        )

        st.subheader(f"{favorite_team} vs {opponent}")
        st.write(
            f"""
            This preview is written from the {favorite_team} fan perspective.

            Key questions:
            - Can the stars control the game?
            - Can the team survive bad shooting stretches?
            - Can they win the rebounding battle?
            - Can they defend without fouling?
            - Can they close in the fourth quarter?
            """
        )


elif page == "Player Playoff Tracker":
    show_header()

    player = st.selectbox("Choose player", team["players"])

    st.subheader(f"{player} Playoff Tracker")

    sample = pd.DataFrame({
        "Game": [1, 2, 3, 4, 5, 6, 7],
        "Points": [24, 31, 28, 36, 22, 34, 40],
        "Assists": [5, 7, 6, 8, 4, 9, 7],
        "Rebounds": [4, 5, 3, 6, 5, 4, 6],
    })

    stat = st.selectbox("Choose stat", ["Points", "Assists", "Rebounds"])

    fig = px.line(sample, x="Game", y=stat, markers=True, title=f"{player} Playoff {stat}")
    st.plotly_chart(fig, use_container_width=True)

    st.write(
        f"""
        Future upgrade: this page can pull live box score data for {player}
        during playoff games and update the chart after each game.
        """
    )


elif page == "Legacy Tracker":
    show_header()

    player = st.selectbox("Choose player", team["players"])

    st.subheader(f"{player} Legacy Tracker")

    outcomes = pd.DataFrame({
        "Outcome": ["First Round", "Second Round", "Conference Finals", "NBA Finals", "Championship", "Finals MVP"],
        "Legacy Score": [50, 62, 76, 88, 96, 100]
    })

    fig = px.bar(outcomes, x="Outcome", y="Legacy Score", title=f"{player} Possible Legacy Impact")
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"If {player} leads the {favorite_team} deep into the playoffs, his franchise legacy score rises."
    )


elif page == "Other Series Watch":
    show_header()

    status_df = pd.DataFrame([
        {
            "Team": name,
            "Conference": data["conference"],
            "Status": data["status"],
            "Round": data["round"],
            "Result": data["result"]
        }
        for name, data in PLAYOFF_TEAMS.items()
    ])

    st.dataframe(status_df, use_container_width=True)


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

        if model_prob is not None:
            c2.metric("Statsmodels Logistic Probability", f"{model_prob}%")
        else:
            c2.metric("Statsmodels Logistic Probability", "Unavailable")

        prob_df = pd.DataFrame({
            "Outcome": [f"{favorite_team} Wins", "Opponent Wins"],
            "Probability": [heuristic_prob, 100 - heuristic_prob]
        })

        fig = px.pie(prob_df, names="Outcome", values="Probability", title="Win Probability")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("NBA Playoff Companion AI | Live-data capable Version 2 | Created by Daniel Cohen")
