import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="NBA Playoff Companion AI",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 NBA Playoff Companion AI")
st.subheader("Created by Daniel Cohen")

st.write(
    """
    This app is an interactive NBA playoff companion that helps users explore teams,
    compare players, analyze matchups, and think about playoff trends using basketball analytics.
    """
)

# -----------------------------
# Sample Data
# -----------------------------

teams = pd.DataFrame({
    "Team": [
        "Boston Celtics", "New York Knicks", "Milwaukee Bucks", "Philadelphia 76ers",
        "Denver Nuggets", "Minnesota Timberwolves", "Dallas Mavericks", "Oklahoma City Thunder"
    ],
    "Conference": [
        "East", "East", "East", "East",
        "West", "West", "West", "West"
    ],
    "Strength": [
        "Elite shooting and defense",
        "Rebounding, toughness, and depth",
        "Star power and scoring",
        "Half-court offense and star creation",
        "Championship experience and efficiency",
        "Defense and athleticism",
        "Elite guards and shot creation",
        "Young talent and spacing"
    ],
    "Concern": [
        "Late-game shot selection",
        "Health and offensive consistency",
        "Perimeter defense",
        "Depth and injuries",
        "Bench production",
        "Playoff experience",
        "Defense and rebounding",
        "Youth and physicality"
    ]
})

players = pd.DataFrame({
    "Player": [
        "Jayson Tatum", "Jalen Brunson", "Giannis Antetokounmpo", "Joel Embiid",
        "Nikola Jokic", "Anthony Edwards", "Luka Doncic", "Shai Gilgeous-Alexander"
    ],
    "Team": [
        "Boston Celtics", "New York Knicks", "Milwaukee Bucks", "Philadelphia 76ers",
        "Denver Nuggets", "Minnesota Timberwolves", "Dallas Mavericks", "Oklahoma City Thunder"
    ],
    "Points Per Game": [26.9, 28.7, 30.4, 34.7, 26.4, 25.9, 33.9, 30.1],
    "Assists Per Game": [4.9, 6.7, 6.5, 5.6, 9.0, 5.1, 9.8, 6.2],
    "Rebounds Per Game": [8.1, 3.6, 11.5, 11.0, 12.4, 5.4, 9.2, 5.5],
    "Playoff Role": [
        "Primary scorer and two-way wing",
        "Lead creator and clutch scorer",
        "Interior force and transition attacker",
        "Dominant scoring big man",
        "Offensive hub and elite passer",
        "Explosive scorer and defender",
        "Primary creator and shot maker",
        "Efficient scorer and lead guard"
    ]
})

# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a section:",
    [
        "Home",
        "Team Explorer",
        "Player Comparison",
        "Matchup Predictor",
        "Playoff Insights",
        "About"
    ]
)

# -----------------------------
# Home
# -----------------------------

if page == "Home":
    st.header("Welcome to the NBA Playoff Companion AI")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Teams Included", len(teams))

    with col2:
        st.metric("Players Included", len(players))

    with col3:
        st.metric("App Type", "Analytics")

    st.write("### What this app does")
    st.write(
        """
        This app helps basketball fans explore playoff teams, compare star players,
        think through matchups, and generate quick basketball insights.
        """
    )

    st.write("### Main Sections")
    st.write(
        """
        - Team Explorer  
        - Player Comparison  
        - Matchup Predictor  
        - Playoff Insights  
        """
    )

# -----------------------------
# Team Explorer
# -----------------------------

elif page == "Team Explorer":
    st.header("Team Explorer")

    conference = st.selectbox("Choose a conference:", ["All", "East", "West"])

    if conference == "All":
        filtered_teams = teams
    else:
        filtered_teams = teams[teams["Conference"] == conference]

    st.dataframe(filtered_teams, use_container_width=True)

    selected_team = st.selectbox("Choose a team to analyze:", filtered_teams["Team"])

    team_info = teams[teams["Team"] == selected_team].iloc[0]

    st.write(f"## {selected_team}")
    st.write(f"**Conference:** {team_info['Conference']}")
    st.write(f"**Main Strength:** {team_info['Strength']}")
    st.write(f"**Main Concern:** {team_info['Concern']}")

    st.write("### AI-Style Team Summary")
    st.success(
        f"{selected_team} could be dangerous in the playoffs because of its {team_info['Strength'].lower()}. "
        f"The biggest question is whether the team can overcome issues related to {team_info['Concern'].lower()}."
    )

# -----------------------------
# Player Comparison
# -----------------------------

elif page == "Player Comparison":
    st.header("Player Comparison Tool")

    player_1 = st.selectbox("Choose Player 1:", players["Player"], index=0)
    player_2 = st.selectbox("Choose Player 2:", players["Player"], index=1)

    p1 = players[players["Player"] == player_1].iloc[0]
    p2 = players[players["Player"] == player_2].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(player_1)
        st.write(f"**Team:** {p1['Team']}")
        st.metric("Points Per Game", p1["Points Per Game"])
        st.metric("Assists Per Game", p1["Assists Per Game"])
        st.metric("Rebounds Per Game", p1["Rebounds Per Game"])
        st.write(f"**Role:** {p1['Playoff Role']}")

    with col2:
        st.subheader(player_2)
        st.write(f"**Team:** {p2['Team']}")
        st.metric("Points Per Game", p2["Points Per Game"])
        st.metric("Assists Per Game", p2["Assists Per Game"])
        st.metric("Rebounds Per Game", p2["Rebounds Per Game"])
        st.write(f"**Role:** {p2['Playoff Role']}")

    comparison_data = pd.DataFrame({
        "Stat": ["Points Per Game", "Assists Per Game", "Rebounds Per Game"],
        player_1: [p1["Points Per Game"], p1["Assists Per Game"], p1["Rebounds Per Game"]],
        player_2: [p2["Points Per Game"], p2["Assists Per Game"], p2["Rebounds Per Game"]]
    })

    st.write("### Statistical Comparison")
    st.dataframe(comparison_data, use_container_width=True)

    st.bar_chart(comparison_data.set_index("Stat"))

    st.write("### AI-Style Comparison")
    if p1["Points Per Game"] > p2["Points Per Game"]:
        scorer = player_1
    elif p2["Points Per Game"] > p1["Points Per Game"]:
        scorer = player_2
    else:
        scorer = "Both players"

    st.info(
        f"Based on the sample data, {scorer} has the scoring edge. "
        "In a playoff series, the better overall player may depend on efficiency, defense, matchups, and late-game execution."
    )

# -----------------------------
# Matchup Predictor
# -----------------------------

elif page == "Matchup Predictor":
    st.header("Matchup Predictor")

    team_1 = st.selectbox("Choose Team 1:", teams["Team"], index=0)
    team_2 = st.selectbox("Choose Team 2:", teams["Team"], index=1)

    t1 = teams[teams["Team"] == team_1].iloc[0]
    t2 = teams[teams["Team"] == team_2].iloc[0]

    st.write(f"## {team_1} vs. {team_2}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(team_1)
        st.write(f"**Strength:** {t1['Strength']}")
        st.write(f"**Concern:** {t1['Concern']}")

    with col2:
        st.subheader(team_2)
        st.write(f"**Strength:** {t2['Strength']}")
        st.write(f"**Concern:** {t2['Concern']}")

    st.write("### Matchup Factors")

    offense = st.slider("Team 1 offensive advantage", 0, 10, 5)
    defense = st.slider("Team 1 defensive advantage", 0, 10, 5)
    star_power = st.slider("Team 1 star power advantage", 0, 10, 5)
    depth = st.slider("Team 1 bench/depth advantage", 0, 10, 5)

    score = offense + defense + star_power + depth

    st.write("### Prediction")

    if score > 24:
        st.success(f"{team_1} appears to have the edge based on your ratings.")
    elif score < 16:
        st.warning(f"{team_2} appears to have the edge based on your ratings.")
    else:
        st.info("This looks like a close matchup based on your ratings.")

    st.write(f"**Team 1 total matchup score:** {score} out of 40")

# -----------------------------
# Playoff Insights
# -----------------------------

elif page == "Playoff Insights":
    st.header("Playoff Insights")

    st.write("### Key Playoff Questions")

    question = st.selectbox(
        "Choose a playoff question:",
        [
            "Which team has the best championship profile?",
            "Which player is most important to his team?",
            "What matters most in the playoffs?",
            "How can an underdog win a series?"
        ]
    )

    if question == "Which team has the best championship profile?":
        st.write(
            """
            A championship team usually needs elite shot creation, strong defense,
            reliable late-game execution, depth, and the ability to adjust across a series.
            """
        )

    elif question == "Which player is most important to his team?":
        st.write(
            """
            The most important player is usually the player who creates efficient offense,
            draws defensive attention, and raises the level of teammates.
            """
        )

    elif question == "What matters most in the playoffs?":
        st.write(
            """
            In the playoffs, half-court offense, defense, rebounding, coaching adjustments,
            health, and star performance become more important because teams face each other repeatedly.
            """
        )

    elif question == "How can an underdog win a series?":
        st.write(
            """
            An underdog can win by controlling pace, winning the three-point battle,
            forcing turnovers, dominating the glass, and turning the series into a matchup problem.
            """
        )

    st.write("### Sample Player Data")
    st.dataframe(players, use_container_width=True)

# -----------------------------
# About
# -----------------------------

elif page == "About":
    st.header("About This App")

    st.write(
        """
        NBA Playoff Companion AI was created by Daniel Cohen as a sports analytics
        and AI-style basketball companion app.
        """
    )

    st.write("### Purpose")
    st.write(
        """
        The purpose of this project is to demonstrate skills in:
        
        - Python programming
        - Streamlit app development
        - Data analysis
        - Sports analytics
        - Interactive dashboards
        - AI-style insight generation
        """
    )

    st.write("### Future Improvements")
    st.write(
        """
        Future versions could include:
        
        - Live NBA data
        - Real playoff brackets
        - Advanced player statistics
        - Machine learning predictions
        - Shot charts
        - Team efficiency ratings
        - Historical playoff comparisons
        """
    )

st.divider()
st.caption("NBA Playoff Companion AI | Created by Daniel Cohen")
