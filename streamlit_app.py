import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 NBA Playoff Companion AI")
st.caption("2026 Playoff-only fan companion app | Created by Daniel Cohen")

# ---------------------------------------------------
# 2026 PLAYOFF TEAMS
# ---------------------------------------------------

PLAYOFF_TEAMS = {
    "Detroit Pistons": {
        "conference": "East",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Defeated Orlando Magic",
        "main_players": ["Cade Cunningham", "Jalen Duren", "Ausar Thompson"],
        "strengths": ["Young athletic core", "Defense", "Transition energy", "Physicality"],
        "concerns": ["Playoff experience", "Half-court scoring", "Late-game execution"]
    },
    "Boston Celtics": {
        "conference": "East",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Lost to Philadelphia 76ers",
        "main_players": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis"],
        "strengths": ["Shooting", "Wing scoring", "Playoff experience"],
        "concerns": ["Series execution", "Health", "Late-game offense"]
    },
    "New York Knicks": {
        "conference": "East",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Defeated Atlanta Hawks",
        "main_players": ["Jalen Brunson", "Karl-Anthony Towns", "Josh Hart", "Mikal Bridges"],
        "strengths": ["Brunson shot creation", "Rebounding", "Toughness", "Clutch scoring"],
        "concerns": ["Bench depth", "Heavy Brunson workload", "Three-point consistency"]
    },
    "Cleveland Cavaliers": {
        "conference": "East",
        "status": "Pending",
        "round": "First Round Game Pending",
        "first_round_result": "Still playing Toronto Raptors",
        "main_players": ["Donovan Mitchell", "Evan Mobley", "Darius Garland"],
        "strengths": ["Guard scoring", "Rim protection", "Defense"],
        "concerns": ["Offensive droughts", "Health", "Playoff consistency"]
    },
    "Toronto Raptors": {
        "conference": "East",
        "status": "Pending",
        "round": "First Round Game Pending",
        "first_round_result": "Still playing Cleveland Cavaliers",
        "main_players": ["Scottie Barnes", "RJ Barrett", "Immanuel Quickley"],
        "strengths": ["Length", "Energy", "Transition play"],
        "concerns": ["Experience", "Half-court offense", "Late-game shot creation"]
    },
    "Atlanta Hawks": {
        "conference": "East",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Lost to New York Knicks",
        "main_players": ["Trae Young", "Jalen Johnson", "Dejounte Murray"],
        "strengths": ["Guard creation", "Pick-and-roll offense", "Shot making"],
        "concerns": ["Defense", "Size", "Playoff consistency"]
    },
    "Philadelphia 76ers": {
        "conference": "East",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Defeated Boston Celtics",
        "main_players": ["Joel Embiid", "Tyrese Maxey", "Paul George"],
        "strengths": ["Star power", "Free-throw pressure", "Half-court scoring"],
        "concerns": ["Embiid health", "Depth", "Transition defense"]
    },
    "Orlando Magic": {
        "conference": "East",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Lost to Detroit Pistons",
        "main_players": ["Paolo Banchero", "Franz Wagner", "Jalen Suggs"],
        "strengths": ["Defense", "Size", "Young core"],
        "concerns": ["Shooting", "Offensive spacing", "Experience"]
    },
    "Oklahoma City Thunder": {
        "conference": "West",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Advanced from First Round",
        "main_players": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
        "strengths": ["Efficiency", "Spacing", "Youthful energy", "Two-way play"],
        "concerns": ["Physicality", "Interior rebounding", "Playoff pressure"]
    },
    "San Antonio Spurs": {
        "conference": "West",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Advanced from First Round",
        "main_players": ["Victor Wembanyama", "Devin Vassell", "Stephon Castle"],
        "strengths": ["Wembanyama impact", "Rim protection", "Length"],
        "concerns": ["Youth", "Turnovers", "Late-game execution"]
    },
    "Denver Nuggets": {
        "conference": "West",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Lost to Minnesota Timberwolves",
        "main_players": ["Nikola Jokic", "Jamal Murray", "Aaron Gordon"],
        "strengths": ["Jokic offense", "Chemistry", "Championship experience"],
        "concerns": ["Depth", "Athleticism", "Defensive matchups"]
    },
    "Los Angeles Lakers": {
        "conference": "West",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Defeated Houston Rockets",
        "main_players": ["LeBron James", "Anthony Davis", "Austin Reaves"],
        "strengths": ["Star experience", "Paint defense", "Playoff IQ"],
        "concerns": ["Age", "Three-point shooting", "Depth"]
    },
    "Houston Rockets": {
        "conference": "West",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Lost to Los Angeles Lakers",
        "main_players": ["Alperen Sengun", "Jalen Green", "Amen Thompson"],
        "strengths": ["Athleticism", "Defense", "Young talent"],
        "concerns": ["Experience", "Half-court offense", "Shot selection"]
    },
    "Minnesota Timberwolves": {
        "conference": "West",
        "status": "Active",
        "round": "Second Round",
        "first_round_result": "Defeated Denver Nuggets",
        "main_players": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
        "strengths": ["Defense", "Size", "Anthony Edwards scoring"],
        "concerns": ["Offensive consistency", "Turnovers", "Late-game spacing"]
    },
    "Portland Trail Blazers": {
        "conference": "West",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Eliminated from playoffs",
        "main_players": ["Scoot Henderson", "Shaedon Sharpe", "Deandre Ayton"],
        "strengths": ["Young guards", "Athleticism", "Future upside"],
        "concerns": ["Experience", "Defense", "Consistency"]
    },
    "Phoenix Suns": {
        "conference": "West",
        "status": "Eliminated",
        "round": "Lost in First Round",
        "first_round_result": "Eliminated from playoffs",
        "main_players": ["Devin Booker", "Kevin Durant", "Bradley Beal"],
        "strengths": ["Shot creation", "Star scoring", "Midrange offense"],
        "concerns": ["Depth", "Defense", "Health"]
    }
}

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

favorite_team = st.sidebar.selectbox(
    "Choose your playoff team",
    list(PLAYOFF_TEAMS.keys()),
    index=list(PLAYOFF_TEAMS.keys()).index("New York Knicks")
)

team = PLAYOFF_TEAMS[favorite_team]

pages = [
    "Home Dashboard",
    "Team Status",
    "Series Preview",
    "Player Playoff Tracker",
    "Legacy Tracker",
    "Other Series Watch",
    "Injury Impact",
    "AI Prediction Center"
]

page = st.sidebar.radio("Choose page", pages)

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def show_team_header():
    st.header(f"{favorite_team} Playoff Companion")
    col1, col2, col3 = st.columns(3)
    col1.metric("Conference", team["conference"])
    col2.metric("Status", team["status"])
    col3.metric("Round", team["round"])

    if team["status"] == "Active":
        st.success(f"{favorite_team} are still alive. This app will analyze their path forward.")
    elif team["status"] == "Eliminated":
        st.error(f"{favorite_team} are out of the playoffs. This app will recap their series and season.")
    else:
        st.warning(f"{favorite_team} are still pending. Their next result will determine whether they advance.")

def show_strengths_concerns():
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Strengths")
        for s in team["strengths"]:
            st.success(s)

    with c2:
        st.subheader("Concerns")
        for c in team["concerns"]:
            st.warning(c)

def active_team_analysis():
    st.subheader("Going Forward Analysis")
    st.write(
        f"""
        The {favorite_team} are still alive, so the app should focus on what they need to do next.

        Key questions:
        - Can their stars control the series?
        - Are they winning the rebounding and turnover battles?
        - Are they getting enough bench production?
        - Are they creating good shots late in games?
        - Are injuries changing the matchup?
        """
    )

def eliminated_team_analysis():
    st.subheader("Season Recap")
    st.write(
        f"""
        The {favorite_team} have been eliminated from the 2026 NBA Playoffs.

        First-round result:
        **{team["first_round_result"]}**

        The season is over, but the app can still analyze:
        - what went wrong
        - what went well
        - which players helped their value
        - what the team needs next season

        Best of luck next season.
        """
    )

def pending_team_analysis():
    st.subheader("Pending Series Result")
    st.write(
        f"""
        The {favorite_team} are still waiting on a first-round result.

        Current situation:
        **{team["first_round_result"]}**

        Once the result is final, this page should switch to either:
        - active second-round analysis
        - eliminated season recap
        """
    )

# ---------------------------------------------------
# HOME DASHBOARD
# ---------------------------------------------------

if page == "Home Dashboard":
    show_team_header()

    st.subheader("App Purpose")
    st.write(
        """
        This is a playoff-only companion app. It is not meant to analyze the regular season generally.
        It follows the 16 playoff teams and changes the analysis based on whether the selected team is
        still alive, eliminated, or pending.
        """
    )

    show_strengths_concerns()

    if team["status"] == "Active":
        active_team_analysis()
    elif team["status"] == "Eliminated":
        eliminated_team_analysis()
    else:
        pending_team_analysis()

# ---------------------------------------------------
# TEAM STATUS
# ---------------------------------------------------

elif page == "Team Status":
    show_team_header()

    st.subheader("First Round Result")
    st.info(team["first_round_result"])

    if team["status"] == "Active":
        st.subheader("Current Focus")
        st.write(
            f"""
            Since the {favorite_team} are still playing, the app should focus on the next playoff game,
            matchup adjustments, injury impact, and their path to the next round.
            """
        )
    elif team["status"] == "Eliminated":
        eliminated_team_analysis()
    else:
        pending_team_analysis()

# ---------------------------------------------------
# SERIES PREVIEW
# ---------------------------------------------------

elif page == "Series Preview":
    show_team_header()

    if team["status"] == "Eliminated":
        eliminated_team_analysis()
    else:
        opponent = st.selectbox(
            "Choose possible/current opponent",
            [t for t in PLAYOFF_TEAMS.keys() if t != favorite_team]
        )

        st.subheader(f"{favorite_team} vs {opponent}")

        st.write(
            f"""
            This page previews the playoff matchup from the **{favorite_team} fan perspective**.

            The app should analyze:
            - how the {favorite_team} can win
            - which matchups matter most
            - what could go wrong
            - which players need to step up
            - how injuries could change the series
            """
        )

        show_strengths_concerns()

        st.subheader("Keys to Winning Next Game")
        keys = [
            "Win the rebounding battle",
            "Limit live-ball turnovers",
            "Get efficient scoring from the main star",
            "Defend without unnecessary fouling",
            "Survive non-star minutes",
            "Make enough open threes"
        ]

        for k in keys:
            st.write(f"• {k}")

# ---------------------------------------------------
# PLAYER PLAYOFF TRACKER
# ---------------------------------------------------

elif page == "Player Playoff Tracker":
    show_team_header()

    selected_player = st.selectbox("Choose player", team["main_players"])

    st.subheader(f"{selected_player} Playoff Tracker")

    sample_stats = pd.DataFrame({
        "Game": [1, 2, 3, 4, 5, 6, 7],
        "Points": [24, 31, 28, 36, 22, 34, 40],
        "Assists": [5, 7, 6, 8, 4, 9, 7],
        "Rebounds": [4, 5, 3, 6, 5, 4, 6]
    })

    stat_choice = st.selectbox("Choose stat", ["Points", "Assists", "Rebounds"])

    fig = px.line(
        sample_stats,
        x="Game",
        y=stat_choice,
        markers=True,
        title=f"{selected_player} Playoff {stat_choice}"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("AI-Style Player Analysis")
    st.write(
        f"""
        {selected_player} is one of the key playoff players for the {favorite_team}.

        This section should eventually use real playoff game data to evaluate:
        - scoring efficiency
        - consistency
        - clutch performance
        - series impact
        - whether the player is improving or declining as the playoffs continue
        """
    )

# ---------------------------------------------------
# LEGACY TRACKER
# ---------------------------------------------------

elif page == "Legacy Tracker":
    show_team_header()

    selected_player = st.selectbox("Choose franchise player", team["main_players"])

    st.subheader(f"{selected_player} Legacy Tracker")

    if team["status"] == "Eliminated":
        st.write(
            f"""
            Since the {favorite_team} are eliminated, this page evaluates how the playoff loss affects
            {selected_player}'s franchise legacy.
            """
        )
    else:
        st.write(
            f"""
            Since the {favorite_team} are still alive, this page estimates how far {selected_player}
            could rise in franchise history depending on what happens next.
            """
        )

    legacy_df = pd.DataFrame({
        "Outcome": [
            "Good first round",
            "Second round win",
            "Conference Finals",
            "NBA Finals",
            "Championship",
            "Finals MVP"
        ],
        "Legacy Impact Score": [55, 68, 78, 88, 96, 100]
    })

    fig = px.bar(
        legacy_df,
        x="Outcome",
        y="Legacy Impact Score",
        title=f"{selected_player} Possible Legacy Impact"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"""
        Example: If {selected_player} leads the {favorite_team} to a championship,
        the app could move him into a much higher all-time franchise tier.
        """
    )

# ---------------------------------------------------
# OTHER SERIES WATCH
# ---------------------------------------------------

elif page == "Other Series Watch":
    show_team_header()

    st.subheader("2026 Playoff Team Status Board")

    status_df = pd.DataFrame([
        {
            "Team": name,
            "Conference": data["conference"],
            "Status": data["status"],
            "Round": data["round"],
            "First Round Result": data["first_round_result"]
        }
        for name, data in PLAYOFF_TEAMS.items()
    ])

    st.dataframe(status_df, use_container_width=True)

    st.subheader(f"Why Other Series Matter for {favorite_team}")

    if team["status"] == "Active":
        st.write(
            f"""
            Other playoff series matter because they affect the {favorite_team}'s path to the Finals.

            Important factors:
            - which opponent advances
            - how many games the other series lasts
            - injuries in other series
            - travel and rest advantage
            - matchup difficulty
            """
        )
    else:
        st.write(
            f"""
            Since the {favorite_team} are eliminated, this page can help fans follow the rest of the playoffs
            and understand which teams are still alive.
            """
        )

# ---------------------------------------------------
# INJURY IMPACT
# ---------------------------------------------------

elif page == "Injury Impact":
    show_team_header()

    st.subheader("Injury Impact Model")

    st.write(
        f"""
        This page should eventually connect to current injury/inactive data.

        For the {favorite_team}, injuries affect:
        - rotation depth
        - defensive assignments
        - rebounding
        - shot creation
        - late-game lineup options
        """
    )

    injury_df = pd.DataFrame({
        "Player": team["main_players"],
        "Status": ["Available", "Available", "Questionable"][:len(team["main_players"])],
        "Estimated Impact": ["High", "High", "Medium"][:len(team["main_players"])]
    })

    st.dataframe(injury_df, use_container_width=True)

# ---------------------------------------------------
# AI PREDICTION CENTER
# ---------------------------------------------------

elif page == "AI Prediction Center":
    show_team_header()

    if team["status"] == "Eliminated":
        st.subheader("Prediction Disabled")
        st.error(
            f"""
            The {favorite_team} are eliminated, so the app should not project future playoff games for them.
            Instead, it should explain why the season ended and what they need next year.
            """
        )
    else:
        st.subheader("Series Win Probability")

        probability = st.slider(
            f"{favorite_team} win probability",
            min_value=0,
            max_value=100,
            value=58
        )

        prob_df = pd.DataFrame({
            "Outcome": [f"{favorite_team} Wins", "Opponent Wins"],
            "Probability": [probability, 100 - probability]
        })

        fig = px.pie(
            prob_df,
            names="Outcome",
            values="Probability",
            title="Series Win Probability"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("AI Explanation")
        st.write(
            f"""
            The {favorite_team}'s playoff probability should eventually update using:
            - score margin
            - time remaining
            - home/away status
            - injuries
            - player performance
            - shooting variance
            - rebounding
            - turnovers
            - recent playoff momentum
            """
        )

st.divider()
st.caption("NBA Playoff Companion AI | 2026 playoff-only app | Created by Daniel Cohen")
