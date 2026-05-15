
import html
import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, time, timezone
import time as pytime
import concurrent.futures

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

# ==========================================================
# Optional packages
# ==========================================================
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
    from nba_api.stats.endpoints import playergamelog, playercareerstats, scoreboardv2, leaguegamefinder, commonteamroster, leaguedashplayerstats
    NBA_STATS_AVAILABLE = True
except Exception:
    NBA_STATS_AVAILABLE = False

try:
    from nba_api.stats.endpoints import scoreboardv3
    NBA_SCOREBOARD_V3_AVAILABLE = True
except Exception:
    scoreboardv3 = None  # type: ignore
    NBA_SCOREBOARD_V3_AVAILABLE = False


try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False

# Browser-like headers for stats.nba.com (some environments block generic clients).
NBA_STATS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 NBAPlayoffCompanion/1.0"
    ),
    "Referer": "https://www.nba.com/",
    "Accept": "application/json, text/plain, */*",
}

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False

# ==========================================================
# Page setup
# ==========================================================
st.set_page_config(page_title="Daniel Cohen — NBA Playoff Companion AI", page_icon="🏀", layout="wide")
st.title("Daniel Cohen — NBA Playoff Companion AI")
st.caption("2026 NBA Playoff companion app — live game center, automatic series tracking, bracket, box scores, and fan-focused analysis")

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fafc, #e5e7eb) !important;
    color: #111827 !important;
}
section[data-testid="stSidebar"] * { color: #111827 !important; }
section[data-testid="stSidebar"] label { font-size: 16px !important; font-weight: 800 !important; }
div[role="radiogroup"] label { padding: 9px 8px !important; border-radius: 12px !important; }
div[role="radiogroup"] label:hover { background-color: rgba(249,115,22,.18) !important; }
.player-card { text-align:center; border-radius:16px; padding:8px; border:1px solid rgba(0,0,0,.12); background:rgba(255,255,255,.75); }
.big-status { font-size: 20px; font-weight: 800; padding: 10px 12px; border-radius: 12px; background: #fff7ed; border: 1px solid #fed7aa; }
.injury-card { border:1px solid rgba(0,0,0,.12); border-radius:16px; padding:10px; background:rgba(255,255,255,.85); margin-bottom:10px; min-height:135px; }
.injury-status { font-weight:900; padding:4px 8px; border-radius:999px; display:inline-block; background:#fee2e2; color:#991b1b; }
.injury-note { font-size:13px; color:#374151; }
.live-score-sticky {
  position: sticky; top: 0; z-index: 1000;
  color: #f8fafc; border-radius: 16px; padding: 14px 16px 16px;
  margin-bottom: 14px;
}
.live-hero-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center; }
@media (max-width: 900px) {
  .live-hero-grid { grid-template-columns: 1fr; text-align: center; }
  .live-hero-side { justify-content: center !important; }
}
.live-hero-side { display: flex; align-items: center; gap: 10px; }
.live-hero-side.right { flex-direction: row-reverse; }
.live-score-big { font-size: clamp(2rem, 5vw, 2.75rem); font-weight: 900; letter-spacing: -0.02em; line-height: 1.1; }
.live-meta-row { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 10px; }
.live-pill { font-size: 12px; font-weight: 700; padding: 5px 10px; border-radius: 999px; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18); }
.live-pill.live { background: rgba(239,68,68,.25); border-color: rgba(252,165,165,.5); color: #fecaca; }
.live-pill.clutch { background: rgba(234,179,8,.22); border-color: rgba(253,224,71,.45); color: #fef08a; }
.live-pill.prob { background: rgba(56,189,248,.18); border-color: rgba(125,211,252,.4); color: #bae6fd; }
.live-pill.series { background: rgba(167,139,250,.2); border-color: rgba(196,181,253,.4); color: #e9d5ff; }
.live-tile-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 12px; }
.live-tile { background: rgba(15,23,42,.45); border-radius: 12px; padding: 8px 10px; text-align: center; border: 1px solid rgba(148,163,184,.2); }
.live-tile .v { font-size: 1.25rem; font-weight: 800; color: #fff; }
.live-tile .k { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: .04em; }
.live-inj-strip { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(148,163,184,.25); font-size: 12px; color: #cbd5e1; }
.badge-hot { color: #f97316; font-weight: 800; }
.badge-cold { color: #38bdf8; font-weight: 800; }
/* Player Playoff Story Hub */
.pp-wrap { max-width: 1280px; margin: 0 auto; }
.pp-hero {
  display: grid; grid-template-columns: auto 1fr auto; gap: 18px; align-items: center;
  padding: 18px 20px; border-radius: 18px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #0c4a6e 100%);
  color: #f8fafc; border: 1px solid rgba(148,163,184,.35);
  margin-bottom: 16px;
}
.pp-hero h2 { margin: 0 0 6px 0; font-size: 1.45rem; letter-spacing: -0.02em; }
.pp-hero .sub { color: #94a3b8; font-size: 14px; line-height: 1.45; }
.pp-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.pp-badge {
  font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em;
  padding: 5px 10px; border-radius: 999px;
  background: rgba(56,189,248,.15); border: 1px solid rgba(125,211,252,.35); color: #bae6fd;
}
.pp-badge.gold { background: rgba(234,179,8,.18); border-color: rgba(253,224,71,.4); color: #fef08a; }
.pp-badge.fire { background: rgba(249,115,22,.2); border-color: rgba(253,186,116,.45); color: #ffedd5; }
.pp-sec {
  font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .08em;
  color: #64748b; margin: 22px 0 10px 0;
}
.pp-card {
  border: 1px solid rgba(15,23,42,.12); border-radius: 16px; padding: 14px 16px;
  background: #fff; box-shadow: 0 1px 2px rgba(15,23,42,.04);
  margin-bottom: 12px;
}
.pp-card h4 { margin: 0 0 8px 0; font-size: 1.02rem; color: #0f172a; }
.pp-muted { color: #64748b; font-size: 13px; line-height: 1.5; }
.pp-meter { height: 10px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin: 6px 0 4px 0; }
.pp-meter > span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #0ea5e9, #6366f1); }
.pp-meter > span.gold { background: linear-gradient(90deg, #ca8a04, #f97316); }
.pp-meter > span.ember { background: linear-gradient(90deg, #dc2626, #f97316); }
.pp-timeline { border-left: 3px solid #cbd5e1; margin-left: 8px; padding-left: 14px; }
.pp-tl-item { margin-bottom: 10px; font-size: 13px; color: #334155; }
.pp-tl-item b { color: #0f172a; }
/* Fan branding (team CSS vars injected per selected team) */
.team-match-header {
  text-align: center; padding: 14px 16px; border-radius: 18px; margin-bottom: 14px;
  background: linear-gradient(135deg, var(--team-bg0,#0f172a) 0%, var(--team-bg1,#1e293b) 100%);
  border: 1px solid var(--team-border, rgba(148,163,184,.35));
  color: #f8fafc; box-shadow: 0 10px 32px rgba(0,0,0,.25);
}
.team-match-header h1 { margin: 0 0 6px; font-size: clamp(1.1rem, 2.8vw, 1.65rem); }
.team-match-header h3 { margin: 0; font-size: 0.95rem; font-weight: 700; color: var(--team-accent,#38bdf8); }
.team-sec {
  font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .08em;
  color: var(--team-accent,#64748b); margin: 20px 0 10px; padding: 8px 12px;
  border-left: 4px solid var(--team-primary,#38bdf8);
  background: var(--team-accent-soft, rgba(56,189,248,.08)); border-radius: 0 10px 10px 0;
}
.team-card {
  border: 1px solid var(--team-border, rgba(15,23,42,.12)); border-radius: 16px; padding: 14px 16px;
  background: linear-gradient(180deg, #fff 0%, var(--team-card-tint, #f8fafc) 100%);
  box-shadow: 0 2px 8px rgba(15,23,42,.06); margin-bottom: 12px;
}
.team-card h4 { margin: 0 0 8px; color: #0f172a; }
.fan-player-card {
  display: grid; grid-template-columns: auto 1fr auto; gap: 14px; align-items: center;
  padding: 14px 16px; border-radius: 16px; margin-bottom: 12px;
  background: linear-gradient(135deg, var(--team-bg0,#0f172a) 0%, var(--team-bg1,#1e293b) 72%, #0f172a 100%);
  border: 1px solid var(--team-border, rgba(148,163,184,.3)); color: #f8fafc;
}
.fan-player-card img.hs { width: 88px; height: 88px; border-radius: 14px; object-fit: cover;
  border: 2px solid var(--team-primary,#38bdf8); background: #0b1224; }
.fan-player-card img.logo { width: 48px; opacity: .95; }
.fan-player-name { font-size: 1.15rem; font-weight: 900; margin: 0 0 4px; }
.fan-player-role { font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
.fan-stat-tiles { display: flex; flex-wrap: wrap; gap: 8px; }
.fan-stat-tile {
  min-width: 58px; text-align: center; padding: 6px 10px; border-radius: 10px;
  background: rgba(15,23,42,.45); border: 1px solid var(--team-border, rgba(148,163,184,.25));
}
.fan-stat-tile .v { font-size: 1.05rem; font-weight: 900; color: #fff; }
.fan-stat-tile .k { font-size: 9px; text-transform: uppercase; letter-spacing: .06em; color: #94a3b8; }
.fan-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.fan-badge {
  font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em;
  padding: 4px 9px; border-radius: 999px; border: 1px solid transparent;
}
.fan-badge.hot { background: rgba(249,115,22,.22); border-color: rgba(253,186,116,.5); color: #ffedd5; }
.fan-badge.clutch { background: rgba(234,179,8,.2); border-color: rgba(253,224,71,.45); color: #fef9c3; }
.fan-badge.xfactor { background: rgba(167,139,250,.22); border-color: rgba(196,181,253,.45); color: #ede9fe; }
.fan-badge.bounce { background: rgba(239,68,68,.18); border-color: rgba(252,165,165,.4); color: #fee2e2; }
.fan-badge.injury { background: rgba(248,113,113,.2); border-color: rgba(254,202,202,.45); color: #fecaca; }
.fan-stat-table-wrap { overflow-x: auto; margin: 8px 0 14px; border-radius: 14px;
  border: 1px solid var(--team-border, rgba(148,163,184,.35)); }
table.fan-stat-table { width: 100%; border-collapse: collapse; font-size: 13px; }
table.fan-stat-table th {
  background: linear-gradient(90deg, var(--team-bg0,#0f172a), var(--team-bg1,#1e293b));
  color: #f8fafc; padding: 10px 12px; text-align: left; font-size: 11px;
  text-transform: uppercase; letter-spacing: .06em;
}
table.fan-stat-table td { padding: 9px 12px; border-bottom: 1px solid rgba(148,163,184,.15); color: #1e293b; }
table.fan-stat-table tr.row-even td { background: var(--team-row-even, rgba(248,250,252,.9)); }
table.fan-stat-table tr.row-odd td { background: var(--team-row-odd, #fff); }
table.fan-stat-table td.stat-good { color: #15803d; font-weight: 800; }
table.fan-stat-table td.stat-warn { color: #b45309; font-weight: 800; }
table.fan-stat-table td.stat-bad { color: #b91c1c; font-weight: 800; }
.injury-card { border:1px solid var(--team-border, rgba(0,0,0,.12)); border-radius:16px; padding:10px;
  background: linear-gradient(180deg, #fff, var(--team-card-tint, #f8fafc)); margin-bottom:10px; min-height:135px; }
.injury-status { font-weight:900; padding:4px 8px; border-radius:999px; display:inline-block;
  background: rgba(254,226,226,.9); color:#991b1b; border: 1px solid rgba(248,113,113,.35); }
.pp-hero.team-branded {
  background: linear-gradient(135deg, var(--team-bg0,#0f172a) 0%, var(--team-bg1,#1e293b) 55%, #0c1224 100%) !important;
  border-color: var(--team-border, rgba(148,163,184,.35)) !important;
}
.pp-badge.team { background: var(--team-accent-soft); border-color: var(--team-primary); color: #f8fafc; }
.cmd-sec { color: var(--team-accent, #64748b) !important; border-bottom-color: var(--team-primary, rgba(148,163,184,.35)) !important; }
/* Matchup Intelligence */
.mi-wrap { max-width: 1100px; margin: 0 auto; }
.mi-hero {
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  padding: 14px 16px; border-radius: 16px; margin-bottom: 14px;
  background: linear-gradient(135deg, var(--team-bg0,#0f172a), var(--team-bg1,#1e293b));
  border: 1px solid var(--team-border); color: #f8fafc;
}
.mi-hero img.logo { width: 52px; height: 52px; filter: drop-shadow(0 4px 12px rgba(0,0,0,.35)); }
.mi-card {
  border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
  background: linear-gradient(135deg, #fff 0%, var(--team-card-tint, #f8fafc) 100%);
  border: 1px solid rgba(15,23,42,.08); box-shadow: 0 4px 14px rgba(15,23,42,.06);
  border-left: 4px solid var(--team-primary, #38bdf8);
}
.mi-card.mi-good { border-left-color: var(--team-good, #22c55e); }
.mi-card.mi-warn { border-left-color: var(--team-warn, #f97316); }
.mi-card.mi-mom-up { border-left-color: var(--team-good); background: linear-gradient(135deg, #f0fdf4, var(--team-card-tint)); }
.mi-card.mi-mom-down { border-left-color: var(--team-bad); background: linear-gradient(135deg, #fef2f2, #fff); }
.mi-num { font-size: 11px; font-weight: 800; color: #94a3b8; letter-spacing: .06em; }
.mi-title { font-size: 16px; font-weight: 900; color: #0f172a; margin: 2px 0 8px; }
.mi-body { font-size: 14px; line-height: 1.55; color: #334155; }
.mi-bar { height: 8px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin-top: 8px; }
.mi-bar > span { display: block; height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--team-primary), var(--team-accent)); }
.mi-mom-pill { display: inline-block; font-size: 10px; font-weight: 800; padding: 3px 9px;
  border-radius: 999px; margin-left: 6px; text-transform: uppercase; letter-spacing: .05em; }
.mi-mom-pill.up { background: rgba(34,197,94,.15); color: #15803d; }
.mi-mom-pill.down { background: rgba(220,38,38,.12); color: #b91c1c; }
.mi-mom-pill.flat { background: var(--team-accent-soft); color: #475569; }
/* Live Game Center */
.live-fan-hero {
  border-radius: 18px; padding: 16px 18px; margin-bottom: 14px;
  background: linear-gradient(135deg, var(--team-bg0), var(--team-bg1));
  border: 1px solid var(--team-border); color: #f8fafc;
}
.live-score-banner {
  text-align: center; padding: 18px 16px; border-radius: 16px; margin: 12px 0;
  background: linear-gradient(145deg, rgba(15,23,42,.85), rgba(15,23,42,.55));
  border: 2px solid var(--team-accent); box-shadow: 0 12px 36px rgba(0,0,0,.35);
}
.live-score-banner.live { animation: homeLivePulse 2.4s ease-in-out infinite; border-color: var(--team-accent); }
.live-score-big { font-size: clamp(2rem, 5vw, 2.8rem); font-weight: 950; color: #fff; letter-spacing: .04em; }
.live-momentum { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 10px; }
.live-gc-board {
  display: flex; align-items: center; justify-content: center; gap: 14px; flex-wrap: wrap;
  padding: 16px; border-radius: 16px; margin: 10px 0 14px;
  background: linear-gradient(135deg, var(--team-bg0), var(--team-bg1));
  border: 1px solid var(--team-border); color: #f8fafc;
}
.live-gc-board img { width: 64px; height: 64px; filter: drop-shadow(0 4px 12px rgba(0,0,0,.35)); }
.live-gc-score { font-size: clamp(1.8rem, 4vw, 2.6rem); font-weight: 950; letter-spacing: .04em; }
.live-gc-clock { font-size: 13px; color: #cbd5e1; margin-top: 4px; text-align: center; }
.live-gc-series { font-size: 12px; color: #94a3b8; margin-top: 6px; text-align: center; }
.live-gc-perf { border: 1px solid var(--team-border); border-radius: 12px; padding: 10px 12px;
  background: linear-gradient(180deg, #fff, var(--team-card-tint)); margin-bottom: 8px; }
/* Bracket — your team highlight */
.bracket-wrap { border-color: var(--team-border) !important; }
.bmk-card--yours { border-color: var(--team-accent) !important;
  box-shadow: 0 0 0 1px var(--team-accent-soft), 0 6px 22px rgba(0,0,0,.35) !important; }
.bmk-team--yours { border-left-color: var(--team-primary) !important;
  background: linear-gradient(90deg, var(--team-accent-soft), rgba(30,41,59,.72)) !important; }
/* Previous rounds */
.history-card {
  border: 1px solid var(--team-border); border-radius: 20px; padding: 16px; margin: 12px 0;
  background: linear-gradient(135deg, #fff, var(--team-card-tint));
  box-shadow: 0 4px 18px rgba(15,23,42,.08);
}
.history-score { font-size: 28px; font-weight: 950; color: var(--team-accent); text-align: center; }
.mvp-pill { display: inline-block; background: var(--team-accent-soft);
  border: 1px solid var(--team-border); border-radius: 999px; padding: 3px 10px;
  font-weight: 800; color: #0f172a; }
.fan-player-card.large img.hs { width: 104px; height: 104px; }
.mode-banner {
  padding: 12px 14px; border-radius: 12px; margin-bottom: 14px;
  border: 1px solid var(--team-border); background: var(--team-accent-soft);
}
.mode-banner .k { font-size: 10px; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; color: var(--team-accent); }
.mode-banner .b { font-size: 0.95rem; line-height: 1.5; color: #1e293b; margin-top: 6px; }
.mode-banner--postmortem { border-color: rgba(248,113,113,.55); background: rgba(254,226,226,.35); }
.mode-banner--postmortem .k { color: #b91c1c; }
.mode-banner--live { border-color: rgba(52,211,153,.45); background: rgba(209,250,229,.4); }
.mode-banner--live .k { color: #047857; }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# Static team data / fallback data
# ==========================================================
TEAM_IDS = {
    "Atlanta Hawks": 1610612737, "Boston Celtics": 1610612738, "Cleveland Cavaliers": 1610612739,
    "Denver Nuggets": 1610612743, "Houston Rockets": 1610612745, "Los Angeles Lakers": 1610612747,
    "Minnesota Timberwolves": 1610612750, "New York Knicks": 1610612752, "Orlando Magic": 1610612753,
    "Philadelphia 76ers": 1610612755, "Phoenix Suns": 1610612756, "Portland Trail Blazers": 1610612757,
    "San Antonio Spurs": 1610612759, "Oklahoma City Thunder": 1610612760, "Toronto Raptors": 1610612761,
    "Detroit Pistons": 1610612765,
}
ID_TO_TEAM = {v: k for k, v in TEAM_IDS.items()}

TEAM_ALIASES = {
    "Detroit Pistons": "DET", "Orlando Magic": "ORL", "Cleveland Cavaliers": "CLE", "Toronto Raptors": "TOR",
    "New York Knicks": "NYK", "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Philadelphia 76ers": "PHI",
    "Oklahoma City Thunder": "OKC", "Phoenix Suns": "PHX", "San Antonio Spurs": "SAS", "Portland Trail Blazers": "POR",
    "Denver Nuggets": "DEN", "Minnesota Timberwolves": "MIN", "Los Angeles Lakers": "LAL", "Houston Rockets": "HOU",
}
ALIAS_TO_TEAM = {v: k for k, v in TEAM_ALIASES.items()}

# ESPN team slugs are used for injury reports because nba_api does not expose a
# reliable official injury-report endpoint. This is automatic when ESPN is reachable.
ESPN_INJURY_SLUGS = {
    "Atlanta Hawks": "atl/atlanta-hawks",
    "Boston Celtics": "bos/boston-celtics",
    "Cleveland Cavaliers": "cle/cleveland-cavaliers",
    "Denver Nuggets": "den/denver-nuggets",
    "Houston Rockets": "hou/houston-rockets",
    "Los Angeles Lakers": "lal/los-angeles-lakers",
    "Minnesota Timberwolves": "min/minnesota-timberwolves",
    "New York Knicks": "ny/new-york-knicks",
    "Orlando Magic": "orl/orlando-magic",
    "Philadelphia 76ers": "phi/philadelphia-76ers",
    "Phoenix Suns": "phx/phoenix-suns",
    "Portland Trail Blazers": "por/portland-trail-blazers",
    "San Antonio Spurs": "sa/san-antonio-spurs",
    "Oklahoma City Thunder": "okc/oklahoma-city-thunder",
    "Toronto Raptors": "tor/toronto-raptors",
    "Detroit Pistons": "det/detroit-pistons",
}

FALLBACK_INJURY_REPORT = {
    "New York Knicks": [
        {"Player":"OG Anunoby","Status":"Questionable / Monitor","Injury":"Availability status","Latest Update":"Key wing availability should be checked on the official pregame report before every Knicks game.","Impact":"If Anunoby is out or limited, New York loses a primary wing defender, matchup flexibility, and transition finishing."},
        {"Player":"Mitchell Robinson","Status":"Monitor","Injury":"Availability/conditioning","Latest Update":"Check pregame status before tipoff.","Impact":"If limited, rim protection and offensive rebounding become more dependent on the starting frontcourt."},
    ],
    "Philadelphia 76ers": [
        {"Player":"Joel Embiid","Status":"Monitor","Injury":"Health management","Latest Update":"Check official pregame report before tipoff.","Impact":"If limited or out, Philadelphia loses its main half-court pressure point."},
    ],
    "Los Angeles Lakers": [
        {"Player":"LeBron James","Status":"Monitor","Injury":"Veteran workload/health status","Latest Update":"Check pregame status before tipoff.","Impact":"If limited, the Lakers lose late-game organization and matchup control."},
        {"Player":"Anthony Davis","Status":"Monitor","Injury":"Health status","Latest Update":"Check pregame status before tipoff.","Impact":"If limited, the Lakers lose rim protection and interior scoring."},
    ],
}

TEAM_LOGOS = {team: f"https://cdn.nba.com/logos/nba/{tid}/primary/L/logo.svg" for team, tid in TEAM_IDS.items()}

# Current season used for live roster / rotation lookups.
# Change this once the next NBA season starts.
CURRENT_NBA_SEASON = "2025-26"

TEAM_PROFILES = {
    "New York Knicks": {"seed":3,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"Philadelphia 76ers","first_round_opponent":"Atlanta Hawks","first_round_result":"Defeated Atlanta Hawks, 4-2","starters":["Jalen Brunson","Mikal Bridges","OG Anunoby","Josh Hart","Karl-Anthony Towns"],"subs":["Miles McBride","Mitchell Robinson","Jordan Clarkson","Landry Shamet","Jose Alvarado"],"strengths":["Brunson shot creation","Towns spacing","OG/Bridges wing defense","Hart rebounding"],"concerns":["Towns foul trouble","bench scoring consistency","overreliance on Brunson late"]},
    "Philadelphia 76ers": {"seed":7,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"New York Knicks","first_round_opponent":"Boston Celtics","first_round_result":"Defeated Boston Celtics, 4-3","starters":["Tyrese Maxey","VJ Edgecombe","Kelly Oubre Jr.","Paul George","Joel Embiid"],"subs":["Quentin Grimes","Andre Drummond","Kyle Lowry","Eric Gordon","Caleb Martin"],"strengths":["Embiid pressure","Maxey speed","Paul George wing scoring","free-throw pressure"],"concerns":["Embiid health","transition defense","bench depth"]},
    "Detroit Pistons": {"seed":1,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"Cleveland Cavaliers","first_round_opponent":"Orlando Magic","first_round_result":"Defeated Orlando Magic, 4-3","starters":["Cade Cunningham","Jaden Ivey","Ausar Thompson","Tobias Harris","Jalen Duren"],"subs":["Marcus Sasser","Isaiah Stewart","Simone Fontecchio","Malik Beasley","Ron Holland"],"strengths":["Cade Cunningham control","Duren rebounding","young athleticism","transition pressure"],"concerns":["late-game execution","playoff inexperience","half-court droughts"]},
    "Cleveland Cavaliers": {"seed":4,"conference":"Eastern Conference","status":"Active","round":"Second Round","current_opponent":"Detroit Pistons","first_round_opponent":"Toronto Raptors","first_round_result":"Defeated Toronto Raptors, 4-3","starters":["Darius Garland","Donovan Mitchell","Max Strus","Evan Mobley","Jarrett Allen"],"subs":["Caris LeVert","Isaac Okoro","Georges Niang","Sam Merrill","Dean Wade"],"strengths":["Mitchell shot creation","Garland playmaking","Mobley/Allen rim protection","shooting around the guards"],"concerns":["offensive droughts","health","turnovers"]},
    "Oklahoma City Thunder": {"seed":1,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"Los Angeles Lakers","first_round_opponent":"Phoenix Suns","first_round_result":"Defeated Phoenix Suns, 4-0","starters":["Shai Gilgeous-Alexander","Lu Dort","Jalen Williams","Chet Holmgren","Isaiah Hartenstein"],"subs":["Cason Wallace","Aaron Wiggins","Isaiah Joe","Jaylin Williams","Kenrich Williams"],"strengths":["SGA creation","Chet rim protection","spacing","pace"],"concerns":["Lakers size","physicality","late-game pressure"]},
    "Los Angeles Lakers": {"seed":4,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"Oklahoma City Thunder","first_round_opponent":"Houston Rockets","first_round_result":"Defeated Houston Rockets, 4-2","starters":["D'Angelo Russell","Austin Reaves","LeBron James","Rui Hachimura","Anthony Davis"],"subs":["Gabe Vincent","Jarred Vanderbilt","Max Christie","Christian Wood","Jaxson Hayes"],"strengths":["LeBron control","Anthony Davis defense","rim pressure","playoff experience"],"concerns":["transition defense","age","three-point consistency"]},
    "San Antonio Spurs": {"seed":2,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"Minnesota Timberwolves","first_round_opponent":"Portland Trail Blazers","first_round_result":"Defeated Portland Trail Blazers, 4-1","starters":["Stephon Castle","Devin Vassell","Keldon Johnson","Jeremy Sochan","Victor Wembanyama"],"subs":["Tre Jones","Julian Champagnie","Zach Collins","Malaki Branham","Blake Wesley"],"strengths":["Wembanyama two-way impact","length","rim protection","young talent"],"concerns":["turnovers","playoff inexperience","foul trouble"]},
    "Minnesota Timberwolves": {"seed":6,"conference":"Western Conference","status":"Active","round":"Second Round","current_opponent":"San Antonio Spurs","first_round_opponent":"Denver Nuggets","first_round_result":"Defeated Denver Nuggets, 4-2","starters":["Mike Conley","Anthony Edwards","Jaden McDaniels","Naz Reid","Rudy Gobert"],"subs":["Nickeil Alexander-Walker","Donte DiVincenzo","Rob Dillingham","Josh Minott","Luka Garza"],"strengths":["Edwards scoring","Gobert/McDaniels defense","Naz Reid spacing","physicality"],"concerns":["late-game offense","spacing","foul trouble"]},
}
# Eliminated teams
ELIMINATED_INFO = [
    ("Atlanta Hawks",6,"Eastern Conference","New York Knicks","Lost to New York Knicks, 4-2",["Trae Young","Dyson Daniels","Zaccharie Risacher","Jalen Johnson","Onyeka Okongwu"],["Bogdan Bogdanovic","De'Andre Hunter","Clint Capela","Vit Krejci","Kobe Bufkin"]),
    ("Boston Celtics",2,"Eastern Conference","Philadelphia 76ers","Lost to Philadelphia 76ers, 4-3",["Jrue Holiday","Derrick White","Jaylen Brown","Jayson Tatum","Kristaps Porzingis"],["Payton Pritchard","Sam Hauser","Al Horford","Luke Kornet","Neemias Queta"]),
    ("Orlando Magic",8,"Eastern Conference","Detroit Pistons","Lost to Detroit Pistons, 4-3",["Jalen Suggs","Kentavious Caldwell-Pope","Franz Wagner","Paolo Banchero","Wendell Carter Jr."],["Cole Anthony","Jonathan Isaac","Anthony Black","Moritz Wagner","Gary Harris"]),
    ("Toronto Raptors",5,"Eastern Conference","Cleveland Cavaliers","Lost to Cleveland Cavaliers, 4-3",["Immanuel Quickley","RJ Barrett","Gradey Dick","Scottie Barnes","Jakob Poeltl"],["Bruce Brown","Kelly Olynyk","Ochai Agbaji","Chris Boucher","Davion Mitchell"]),
    ("Phoenix Suns",8,"Western Conference","Oklahoma City Thunder","Lost to Oklahoma City Thunder, 4-0",["Devin Booker","Bradley Beal","Grayson Allen","Kevin Durant","Jusuf Nurkic"],["Royce O'Neale","Eric Gordon","Bol Bol","Drew Eubanks","Josh Okogie"]),
    ("Portland Trail Blazers",7,"Western Conference","San Antonio Spurs","Lost to San Antonio Spurs, 4-1",["Scoot Henderson","Anfernee Simons","Shaedon Sharpe","Jerami Grant","Deandre Ayton"],["Toumani Camara","Matisse Thybulle","Robert Williams III","Dalano Banton","Kris Murray"]),
    ("Denver Nuggets",3,"Western Conference","Minnesota Timberwolves","Lost to Minnesota Timberwolves, 4-2",["Jamal Murray","Christian Braun","Michael Porter Jr.","Aaron Gordon","Nikola Jokic"],["Reggie Jackson","Peyton Watson","Zeke Nnaji","Julian Strawther","DeAndre Jordan"]),
    ("Houston Rockets",5,"Western Conference","Los Angeles Lakers","Lost to Los Angeles Lakers, 4-2",["Fred VanVleet","Jalen Green","Amen Thompson","Jabari Smith Jr.","Alperen Sengun"],["Dillon Brooks","Tari Eason","Cam Whitmore","Steven Adams","Reed Sheppard"]),
]
for name, seed, conf, opp, result, starters, subs in ELIMINATED_INFO:
    TEAM_PROFILES[name] = {"seed":seed,"conference":conf,"status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":opp,"first_round_result":result,"starters":starters,"subs":subs,"strengths":["main star creation","transition chances","playoff experience"],"concerns":["series ended in first round","needs depth/defense improvements","late-game consistency"]}


def _is_home_eliminated(team_name):
    """True when Home Dashboard should show offseason / future outlook (not live playoff chase mode)."""
    p = TEAM_PROFILES.get(team_name) or {}
    if not p:
        return False
    if p.get("status") == "Eliminated":
        return True
    stt = str(p.get("status") or "").strip().lower()
    if "eliminat" in stt:
        return True
    rnd = str(p.get("round") or "").lower()
    if "lost" in rnd and "round" in rnd:
        return True
    res = str(p.get("first_round_result") or "")
    if p.get("current_opponent") is None and res.startswith("Lost"):
        return True
    if _dynamic_playoff_eliminated(team_name):
        return True
    return False


def _generic_offseason_outlook(team_name):
    """Fallback offseason copy when a team is eliminated but not in the detailed table."""
    nick = fan_nick(team_name)
    prof = TEAM_PROFILES.get(team_name) or {}
    lost = None
    try:
        lost = _last_elimination_series_for_team(team_name)
    except Exception:
        lost = None
    if lost and team_name in (lost.get("a"), lost.get("b")):
        a, b = lost.get("a"), lost.get("b")
        if team_name == a:
            tw, ow = int(lost.get("a_wins", 0)), int(lost.get("b_wins", 0))
            opp = b
        else:
            tw, ow = int(lost.get("b_wins", 0)), int(lost.get("a_wins", 0))
            opp = a
        rd = str(lost.get("round") or "playoffs").strip() or "the playoffs"
        went_right = (
            f"{nick} stayed alive deep enough to matter in the {rd} — the regular-season identity showed up "
            "in at least a few playoff possessions that looked like winning basketball on tape."
        )
        elimination_cause = (
            f"The postseason run ended in the {rd} against {fan_nick(opp)} ({tw}–{ow}). "
            "Each round asks harder questions: late-clock execution, bench swings, and rebounding battles decide who advances."
        )
    else:
        opp = prof.get("first_round_opponent") or "their opponent"
        res = prof.get("first_round_result") or "playoff series"
        went_right = f"{nick} still reached the postseason — the regular season showed enough to earn a seven-game stage against {fan_nick(opp)}."
        elimination_cause = f"The first round ended with {res}; the tighter margins in May usually go to the group that wins late-clock execution and depth minutes."
    return {
        "reflection": {
            "went_right": went_right,
            "elimination_cause": elimination_cause,
            "playoff_strengths": [
                "Moments where the main creators bent the defense and generated clean looks.",
                "Home energy and the ability to stay in games when the shot diet tightened.",
            ],
            "playoff_weaknesses": [
                "Role-player production when the opponent shrank the floor to the stars.",
                "Consistency on defense across four quarters as the series lengthened.",
            ],
        },
        "priorities": [
            "Secondary shot creation when defenses load to the primary initiator.",
            "Wing size and versatility to survive cross-matches in a deep East/West.",
            "Bench scoring that does not crater the margin when starters sit.",
            "Spacing and decision-making against switching defenses.",
        ],
        "roster": {
            "summary": f"The core that got {nick} here is still the starting point — summer is about who fits around that core under real cap rules.",
            "bullets": [
                "Free agency: identify which rotation pieces are worth paying vs. replacing on the margin.",
                "Veterans: decide who returns on value contracts versus who needs a fresh role elsewhere.",
                "Trades: explore upgrades that address the holes this series exposed without stripping the identity.",
                "Extensions: align young contracts with the timeline you want to chase.",
                "Young players: internal development is still the cheapest way to raise the ceiling.",
                "Cap: one expensive mistake can lock you out of flexibility for multiple summers.",
            ],
        },
        "future": [
            f"The next step for {nick} is turning regular-season proof into repeatable May basketball — that is as much roster construction as it is coaching.",
            "Conference rivals are not standing still; every improvement has to answer a specific matchup problem.",
        ],
        "draft_assets": [
            "Draft capital depends on protections and swaps already on the books — treat picks as trade currency or developmental bets, not magic beans.",
            "If picks are outgoing, the pressure rises to hit on minimum-salary contributors and undrafted finds.",
        ],
        "players_outlook": [
            "Free agency: map every player option and cap hold before you shop outside names — your own free agents often eat the room first.",
            "Veterans on short deals are the fastest turnover layer; decide who is culture glue vs. who is blocking a developmental minute path.",
            "Trade candidates usually overlap with redundant skill sets, expiring money, or contracts that no longer match the timeline.",
            "Cap and tax lines determine whether you can take salary back in a deal or have to match money in smaller moves.",
        ],
        "archetypes": [
            "Two-way wing who can guard multiple positions without hiding on offense.",
            "Secondary creator who keeps the offense organized when the defense traps the star.",
            "Stretch big or movement shooter who opens the paint without bleeding points on the other end.",
        ],
        "direction": {
            "label": "Uncertain direction",
            "blurb": f"The honest read: {nick} are neither clearly rebuilding nor clearly a finished product — the summer meetings will define which path they take.",
        },
    }


OFFSEASON_OUTLOOK_BY_TEAM = {
    "Atlanta Hawks": {
        "reflection": {
            "went_right": "Atlanta still played meaningful playoff minutes with a younger supporting cast around Trae Young — there were stretches where pace, screening, and shot-making looked like a modern offense.",
            "elimination_cause": "New York controlled the glass and physicality in too many fourth quarters; when the Knicks shrank the floor to Young, Atlanta did not generate enough clean secondary shots or enough stops in succession to extend the series.",
            "playoff_strengths": [
                "Young’s pull-up gravity and passing still bent defenses even when blitzed.",
                "Okongwu’s minutes often stabilized the paint on both ends when he could stay on the floor.",
                "Transition opportunities when turnovers turned into early offense.",
            ],
            "playoff_weaknesses": [
                "Perimeter size against bigger Knicks wings — contests and closeouts were a half-step late in key moments.",
                "Half-court shot quality when the game slowed; too many late-clock heaves under pressure.",
                "Bench scoring dry spells when the starters’ minutes spiked.",
            ],
        },
        "priorities": [
            "Perimeter defense and length on the wing without sacrificing spacing.",
            "Secondary shot creation beside Young — a reliable pick-and-roll partner or downhill scorer.",
            "Rim protection and rebounding from the big rotation in playoff minutes.",
            "Bench depth that can survive 8–9 man playoff rotations.",
            "Late-game execution packages when defenses trap the ball-handler.",
        ],
        "roster": {
            "summary": "The roster core still has offensive identity, but the wing rotation needs more playoff-grade size and fewer defensive leaks.",
            "bullets": [
                "Key free agents / options: audit who among rotation wings and bigs returns on value vs. cap relief.",
                "Veterans: decide which short-contract vets are culture fits versus roster churn.",
                "Trade candidates: expiring or redundant skill sets that could consolidate into one higher-minute upgrade.",
                "Young players: Jalen Johnson and Onyeka Okongwu development curves should influence how aggressive the front office is on win-now trades.",
                "Cap flexibility: Atlanta’s summer is less about one max slot and more about stacking 2–3 reliable playoff pieces without punting future picks.",
            ],
        },
        "future": [
            "The window is not a single-season sprint — it is about whether Young’s prime years align with a defense that can survive three playoff rounds.",
            "The East is deep with size at the wing; Atlanta’s contender case depends on closing the talent gap without mortgaging every future pick.",
        ],
        "draft_assets": [
            "Treat future firsts and swaps as conditional trade ammo only if the return solves a clear playoff problem (wing size, rim protection, secondary creation).",
            "If picks stay home, prioritize ready-to-contribute shooters or switchable defenders rather than duplicate skill sets.",
        ],
        "archetypes": [
            "Two-way wing with real size (6–7+ wingspan) who can guard New York-style matchups.",
            "Secondary creator who can run pick-and-roll when Young is trapped.",
            "Backup rim protector who does not kill spacing in short roll minutes.",
            "High-volume movement shooter who punishes help off Young drives.",
        ],
        "direction": {"label": "Retooling around a star", "blurb": "Atlanta is not starting over — the front office is one or two correct upgrades away from feeling dangerous in a seven-game series again."},
    },
    "Boston Celtics": {
        "reflection": {
            "went_right": "Boston still looked like a championship-caliber regular-season team for long stretches — spacing, scheme discipline, and two-way talent were obvious when the offense flowed.",
            "elimination_cause": "Philadelphia won the possession war in the games that mattered most: extra possessions, timely shot-making from role players, and critical late-quarter execution when the margin was one or two possessions.",
            "playoff_strengths": [
                "Tatum and Brown’s ability to generate efficient looks against set defenses.",
                "Switchable perimeter defense when healthy lineups were available.",
                "Payton Pritchard–led bench sparks that kept home-court energy alive.",
            ],
            "playoff_weaknesses": [
                "Depth behind the stars when rotations shortened and fouls or fatigue stacked.",
                "Interior answers when Embiid’s gravity collapsed the paint.",
                "Turnover stretches that fed Philly run-outs.",
            ],
        },
        "priorities": [
            "Big-man depth and playoff-ready interior size behind the starting frontcourt.",
            "Ball-handling relief so late-game offense is not only isolation-heavy.",
            "Health management and minute plans for a core that has deep playoff mileage.",
            "Bench shooting that holds up when defenses run shooters off the line.",
        ],
        "roster": {
            "summary": "The championship core is still elite on paper — the summer is about whether the front office refreshes the middle of the roster or reshapes bigger pieces.",
            "bullets": [
                "Free agents: evaluate backup center and wing depth on short, flexible deals.",
                "Veterans: Al Horford–era minutes require succession planning even if leadership returns.",
                "Trade candidates: any consolidation that upgrades playoff reliability without gutting identity.",
                "Extensions: align Jaylen/Jayson timeline decisions with tax apron realities.",
                "Young players: continue developing late-first developmental wings into rotation defense.",
                "Cap / tax: Boston’s moves are often about small edges at the margins while staying title-or-bust competitive.",
            ],
        },
        "future": [
            "The next two seasons still represent a real title window if health and depth answers arrive.",
            "Conference competition is brutal — Milwaukee, New York, and emerging East teams force constant roster sharpening.",
        ],
        "draft_assets": [
            "Future picks are more likely trade chips than lottery tickets — protected swaps matter when chasing a veteran upgrade.",
            "If picks convey, hit on low-cost shooters or switchable defenders who can survive playoff minutes.",
        ],
        "archetypes": [
            "Backup rim protector who can survive Embiid-style physicality for stretches.",
            "Veteran point guard or connector who organizes second units without turning it over.",
            "Stretch big who can pick-and-pop without being targeted every switch.",
        ],
        "direction": {"label": "Championship contender (health-dependent)", "blurb": "Boston’s direction is still title-first — this exit is a roster and execution postmortem, not a rebuild signal."},
    },
    "Orlando Magic": {
        "reflection": {
            "went_right": "Orlando proved its defense-first identity travels — length, activity, and scheme buy-in made Detroit work for late-clock looks in multiple games.",
            "elimination_cause": "Detroit’s half-court creation and physicality won the war of attrition; Orlando’s offense could not generate enough easy baskets when possessions slowed and shooting variance swung cold.",
            "playoff_strengths": [
                "Paolo Banchero’s downhill scoring gravity in isolation and early post touches.",
                "Franz Wagner’s complementary shot-making when the floor opened.",
                "Team defense forcing tough twos and contested late-clock shots.",
            ],
            "playoff_weaknesses": [
                "Three-point reliability when defenses packed the paint.",
                "Playmaking under trap pressure — turnovers fed Detroit run-outs.",
                "Bench offensive creation when starters rested.",
            ],
        },
        "priorities": [
            "Spacing and shooting around Banchero without giving back too much defense.",
            "Secondary creator who can run pick-and-roll when defenses load to Paolo.",
            "Veteran leadership and playoff poise in close games.",
            "Shot creation in late-clock situations — fewer contested isolations.",
        ],
        "roster": {
            "summary": "The young core is the asset — the question is how many veterans you add before you crowd developmental minutes.",
            "bullets": [
                "Free agents: target movement shooters and backup point guard stability.",
                "Veterans: decide which short deals teach winning habits without blocking minutes for Black/Anthony/Isaac pathways.",
                "Trade candidates: redundant defensive profiles could consolidate into one offensive upgrade.",
                "Extensions: Banchero/Wagner timelines should drive cap planning.",
                "Young players: Anthony Black and Jett Howard development changes how aggressive Orlando is on the trade market.",
                "Cap: Orlando can still operate with flexibility if it avoids long-term dead money on the middle class.",
            ],
        },
        "future": [
            "The young core suggests long-term sustainability — this exit is a skill-development checkpoint, not a ceiling statement.",
            "The East is getting younger and longer; Orlando’s path is internal growth plus selective veteran shooting.",
        ],
        "draft_assets": [
            "Orlando can still draft-and-develop if picks stay — prioritize shooting variance reducers (elite FT%, mechanical repeatability).",
            "Pick swaps outgoing could limit flexibility; if swaps are incoming, treat them as opportunistic trade windows.",
        ],
        "archetypes": [
            "Movement shooter who can defend enough to stay on the floor in a switching scheme.",
            "Veteran backup point guard who limits turnovers under pressure.",
            "Stretch big who opens driving lanes without being hunted every switch.",
        ],
        "direction": {"label": "Rising young team", "blurb": "Orlando’s arrow still points up — the offseason is about turning defense into a playoff offense without losing identity."},
    },
    "Toronto Raptors": {
        "reflection": {
            "went_right": "Toronto showed competitive spirit in a seven-game rock fight — Quickley’s pace, Barnes’ two-way flashes, and home swings kept Cleveland from walking the series.",
            "elimination_cause": "Cleveland’s star shot-making and playoff experience won the tight moments; Toronto’s half-court offense stalled when spacing tightened and turnovers fed run-outs.",
            "playoff_strengths": [
                "Scottie Barnes’ defensive versatility and transition finishing.",
                "Quickley’s pick-and-roll manipulation when the floor was spaced.",
                "Poeltl’s interior presence on the glass in stretches.",
            ],
            "playoff_weaknesses": [
                "Half-court scoring against set defenses — too many late-clock contested twos.",
                "Perimeter shot-making consistency from the supporting cast.",
                "Defending Cleveland’s guard scoring without over-helping off shooters.",
            ],
        },
        "priorities": [
            "Spacing and high-volume three-point reliability.",
            "Secondary scoring when Barnes is blitzed or doubled.",
            "Rim protection behind aggressive perimeter defense.",
            "Bench depth that does not bleed points in non-starter minutes.",
        ],
        "roster": {
            "summary": "Toronto is in a retooling sweet spot — enough young talent to dream on, enough questions to justify aggressive cap creativity.",
            "bullets": [
                "Free agents: add shooting specialists on short deals if the price is right.",
                "Veterans: evaluate Bruce Brown–type contracts for trade value versus fit.",
                "Trade candidates: consolidate overlapping wings into one higher-end creator if the market allows.",
                "Extensions: Barnes is the compass — align every move with his timeline.",
                "Young players: Gradey Dick and wing development determine how much shooting you must buy.",
                "Cap: Toronto can chase flexibility or consolidation; the direction choice is the real story.",
            ],
        },
        "future": [
            "The conference is crowded with playoff-tested teams — Toronto’s climb requires star-level leap from Barnes or an external infusion.",
            "Coaching stability helps development teams; roster churn should not outpace scheme continuity.",
        ],
        "draft_assets": [
            "If Toronto holds picks, prioritize shooting and size at the wing — the playoff tape screamed for both.",
            "Outgoing protections on past trades can quietly shrink room; audit every owed pick before chasing a star.",
        ],
        "archetypes": [
            "High-volume shooter who can relocate and punish helps off Barnes drives.",
            "Perimeter stopper with length who can survive multiple assignments.",
            "Secondary creator who can run offense when Quickley sits.",
        ],
        "direction": {"label": "Retooling", "blurb": "Toronto is not tanking outright — the franchise is trying to turn competitive minutes into a clearer star pathway."},
    },
    "Phoenix Suns": {
        "reflection": {
            "went_right": "Phoenix still had stretches where star shot-making looked playoff-real — Booker’s pull-up gravity and Durant’s late-clock shot quality kept scoreboard pressure on OKC for moments.",
            "elimination_cause": "Oklahoma City’s depth, pace, and defensive activity overwhelmed a thin rotation; the sweep math reflects turnovers, rebounding, and the Thunder winning the non-star minutes decisively.",
            "playoff_strengths": [
                "Booker’s ability to bend defenses in pick-and-roll and mid-range.",
                "Durant’s isolation scoring when matchups allowed single coverage.",
                "Grayson Allen’s movement shooting when he could get clean launches.",
            ],
            "playoff_weaknesses": [
                "Rebounding and transition defense when OKC turned misses into sprints.",
                "Bench survivability — the Suns could not sustain minutes when stars rested.",
                "Rim protection and interior size against OKC’s drivers.",
            ],
        },
        "priorities": [
            "Bench depth and playable wings who do not shrink the margin.",
            "Rebounding and physicality without killing spacing.",
            "Younger athletic wings who can switch and survive in space.",
            "Financial flexibility — hard choices on multi-star cap stacking.",
        ],
        "roster": {
            "summary": "The core is expensive and older — the summer is as much accounting as it is basketball.",
            "bullets": [
                "Free agents: limited room unless moves clear salary — target minimum contributors who defend.",
                "Veterans: Durant/Booker/Beal realities force trade conversations if the tax bill is untenable.",
                "Trade candidates: any non-core salary becomes a puzzle piece in consolidation trades.",
                "Extensions: younger pieces (if any) become trade sweeteners more than extension priorities.",
                "Young players: internal growth is critical because premium picks may be outgoing.",
                "Cap: Phoenix may be forced toward veteran-focused upgrades on the margin, not another max.",
            ],
        },
        "future": [
            "The championship window is real but narrow — every season of age and tax compounds the urgency.",
            "Western contenders are younger and deeper; Phoenix must solve non-star minutes or repeat early exits.",
        ],
        "draft_assets": [
            "Limited draft flexibility may force the front office toward veteran minimums and second-round hits.",
            "If any future picks remain unencumbered, treat them as precious — do not spend them on marginal upgrades.",
        ],
        "archetypes": [
            "Two-way wing who can defend multiple positions and hit open threes.",
            "Backup rim protector who can play 12–16 playoff minutes without being hunted.",
            "Athletic bench wing who raises transition defense and offensive rebounding.",
        ],
        "direction": {"label": "Aging contender", "blurb": "Phoenix is still trying to win now — but the path is increasingly about financial surgery and finding playable depth."},
    },
    "Portland Trail Blazers": {
        "reflection": {
            "went_right": "Portland showed young guard scoring flashes — Henderson and Simons could heat up in bursts, and the roster competed early before San Antonio’s length took over.",
            "elimination_cause": "San Antonio’s defense keyed on drivers and the paint; Portland could not match Wembanyama’s rim influence or generate enough clean late-clock shots when possessions slowed.",
            "playoff_strengths": [
                "Simons’ shot-making gravity when he got downhill.",
                "Sharpe’s athletic scoring flashes in transition.",
                "Grant’s veteran shot diet in half-court isolations.",
            ],
            "playoff_weaknesses": [
                "Turnovers and decision-making against length.",
                "Interior defense and rebounding against a tall, disciplined front line.",
                "Half-court execution when the game became a half-court wrestling match.",
            ],
        },
        "priorities": [
            "Rim protection and interior size behind the starting big.",
            "Veteran point guard stability to reduce live-ball turnovers.",
            "Spacing around young guards without bleeding points defensively.",
            "Bench depth that can survive physical playoff minutes.",
        ],
        "roster": {
            "summary": "Portland is still building — the playoff exit clarifies which young pieces are keepers versus trade candidates.",
            "bullets": [
                "Free agents: short veteran deals on defense-first wings or backup bigs.",
                "Veterans: Grant’s contract is a natural trade discussion if the timeline shifts younger.",
                "Trade candidates: consolidate overlapping guard minutes if a two-way wing upgrade appears.",
                "Extensions: align Scoot/Sharpe timelines with draft capital usage.",
                "Young players: Camara and defensive-minded wings are the cheap growth path.",
                "Cap: Portland can stay flexible if it avoids long-term middle-class clutter.",
            ],
        },
        "future": [
            "The young core suggests long-term sustainability if defense and decision-making mature on schedule.",
            "The West is unforgiving — Portland’s contender clock starts when the defense becomes playoff-real, not just exciting.",
        ],
        "draft_assets": [
            "Multiple future picks (when unencumbered) give Portland flexibility to pursue another star or to keep drafting defense-first profiles.",
            "If picks are outgoing from prior deals, the margin for error on development hits shrinks.",
        ],
        "archetypes": [
            "Backup rim protector who can contest without fouling.",
            "Veteran point guard who organizes half court and limits turnovers.",
            "Two-way wing who raises the defensive floor around young scorers.",
        ],
        "direction": {"label": "Rebuilding with upside", "blurb": "Portland is not pretending to be finished — the offseason is about collecting real defensive answers while the young guards grow."},
    },
    "Denver Nuggets": {
        "reflection": {
            "went_right": "Denver still showed why Jokic is the system — elite half-court offense, two-man game mastery, and clutch shot quality kept Minnesota honest for stretches.",
            "elimination_cause": "Minnesota’s length and defensive activity won the possession battle; Denver’s supporting shot-making and wing defense wobbled when rotations shortened and the Wolves pressured passing lanes.",
            "playoff_strengths": [
                "Jokic’s passing geometry and scoring efficiency against switches.",
                "Murray’s shot-making in big moments when rhythm was right.",
                "Aaron Gordon’s defensive versatility on forwards.",
            ],
            "playoff_weaknesses": [
                "Perimeter defense against athletic wings.",
                "Bench scoring when the starters’ minutes spiked.",
                "Turnovers under pressure when Minnesota loaded the ball-handler.",
            ],
        },
        "priorities": [
            "Wing defense and size without killing Jokic spacing.",
            "Bench scoring and shot creation when Murray sits.",
            "Athleticism on the wing to survive West playoff matchups.",
            "Health and minute management for a core with deep mileage.",
        ],
        "roster": {
            "summary": "The championship core is still elite — the summer is about patching the holes this series exposed without breaking chemistry.",
            "bullets": [
                "Free agents: target playable wings and backup offense on value.",
                "Veterans: Reggie Jackson–type minutes may need an upgrade path.",
                "Trade candidates: Porter Jr. conversations return whenever tax and fit tension rises — only move if the return solves defense.",
                "Extensions: align young pieces with tax apron realities.",
                "Young players: Peyton Watson development changes how many veterans you must buy.",
                "Cap: Denver is often trading marginal salary for marginal upgrades at the tax line.",
            ],
        },
        "future": [
            "Jokic’s prime is the window — Denver remains a contender if wing defense and bench offense improve.",
            "The West is loaded with size and athleticism; every summer is an arms race on the wing.",
        ],
        "draft_assets": [
            "Late picks and swaps are trade sweeteners more than lottery tickets — use them to chase a defensive wing upgrade.",
            "If picks convey out, development staff has to hit on undrafted two-way types.",
        ],
        "archetypes": [
            "Perimeter stopper with size who can survive switching onto wings.",
            "Secondary creator who can run offense when Murray is trapped.",
            "Stretch big who can spot minutes without being targeted defensively.",
        ],
        "direction": {"label": "Championship contender", "blurb": "Denver is still in the inner circle — this exit is about roster edges, not existential doubt."},
    },
    "Houston Rockets": {
        "reflection": {
            "went_right": "Houston showed why the league fears its young talent — transition pressure, offensive rebounding, and Sengun’s interior craft kept the Lakers from coasting.",
            "elimination_cause": "Los Angeles’ playoff experience, half-court shotmaking, and Anthony Davis’ rim presence won the late-game math; Houston’s half-court offense stalled when spacing tightened and turnovers fed Laker run-outs.",
            "playoff_strengths": [
                "Alperen Sengun’s post playmaking and touch around the rim.",
                "Amen Thompson’s defensive disruption and transition attacks.",
                "Physicality and offensive rebounding that shortened possessions for LA.",
            ],
            "playoff_weaknesses": [
                "Three-point consistency and spacing against set defenses.",
                "Late-clock execution when defenses loaded to the ball-handler.",
                "Defensive discipline on closeouts against LeBron/AD–style leverage.",
            ],
        },
        "priorities": [
            "Spacing and high-volume shooting around the young core.",
            "Veteran leadership and playoff poise in tight games.",
            "Secondary shot creation when defenses shrink the floor.",
            "Bench depth that can hold leads when stars sit.",
        ],
        "roster": {
            "summary": "The core is young and exciting — the summer is about turning potential into playoff shot quality without losing defensive identity.",
            "bullets": [
                "Free agents: add shooters and backup point guard stability if price fits.",
                "Veterans: Fred VanVleet’s leadership vs. long-term cap allocation is a real conversation.",
                "Trade candidates: Dillon Brooks–type contracts can be moved if the return raises ceiling.",
                "Extensions: align Sengun/Green timelines with how aggressive Houston wants to be.",
                "Young players: Amen and Jabari growth determines how much shooting you must buy externally.",
                "Cap: Houston can still operate with room if it avoids toxic long-term deals.",
            ],
        },
        "future": [
            "The next two seasons may represent the peak growth window before extension math tightens the rotation choices.",
            "The West is deep — Houston’s contender case depends on shooting development plus selective veteran adds.",
        ],
        "draft_assets": [
            "If picks remain, prioritize shooting and switchable defense — the playoff tape asked for both.",
            "Pick swaps can be outgoing from prior deals; audit obligations before chasing a star trade.",
        ],
        "archetypes": [
            "Stretch big or movement shooter who opens the paint for Sengun.",
            "Veteran point guard who reduces turnovers under playoff pressure.",
            "Two-way wing who raises spacing without hiding on defense.",
        ],
        "direction": {"label": "Rising young team", "blurb": "Houston is one clear offensive upgrade away from feeling dangerous in a seven-game series — the summer is about finding that upgrade without mortgaging the defense."},
    },
}


def get_offseason_outlook(team_name):
    """Team-specific offseason / future outlook copy for eliminated franchises."""
    return OFFSEASON_OUTLOOK_BY_TEAM.get(team_name) or _generic_offseason_outlook(team_name)


def _offseason_players_out_bullets(od):
    """Bullets for 'Players / contracts who may not return' — explicit list or roster-line extraction."""
    raw = od.get("players_outlook")
    if isinstance(raw, list) and raw:
        return raw
    hits = []
    for b in od.get("roster", {}).get("bullets", []):
        b = str(b)
        if any(
            b.startswith(k)
            for k in (
                "Free agents",
                "Free agency",
                "Veterans",
                "Trade candidates",
                "Extensions",
                "Young players",
                "Cap",
                "Key free agents",
            )
        ):
            hits.append(b)
    return hits if hits else [
        "Every exit summer starts with a hard list: who is a free agent, who has a player/team option, and who is extension-eligible.",
        "Trade noise usually follows redundant roles or money that no longer matches the competitive timeline.",
        "Veterans on expiring or short deals are the first layer that can turn over without touching the core identity.",
    ]


def render_offseason_future_outlook_sections(team_name):
    """Home Dashboard: high-visibility offseason analysis (eliminated teams only)."""
    od = get_offseason_outlook(team_name)
    ref = od["reflection"]
    nick = fan_nick(team_name)
    prof = TEAM_PROFILES.get(team_name) or {}
    try:
        exit_line = _elimination_exit_line(team_name)
    except Exception:
        exit_line = prof.get("first_round_result") or "Playoff exit"

    th = get_team_theme(team_name)
    st.markdown(
        f"""
<div style="padding:16px 18px;border-radius:16px;border:2px solid {th['primary']};
background:linear-gradient(135deg,{th['bg0']} 0%,{th['bg1']} 55%,#0f172a 100%);
margin:0 0 18px 0;box-shadow:0 12px 40px rgba(0,0,0,0.35);display:flex;gap:14px;align-items:flex-start">
  <img src="{html.escape(TEAM_LOGOS.get(team_name, ''))}" width="58" alt=""/>
  <div>
  <div style="font-size:11px;font-weight:900;letter-spacing:0.18em;color:{th['accent']};text-transform:uppercase;margin-bottom:8px">
    Offseason mode · {html.escape(fan_nick(team_name))}</div>
  <div style="font-size:1.35rem;font-weight:900;color:#fffbeb;line-height:1.2;margin-bottom:8px">Postmortem & future outlook</div>
  <div style="font-size:0.98rem;color:#fef3c7;line-height:1.5;opacity:0.95">
    Live chase mode is off for this club. Below is a front-office style read: what broke in the playoffs,
    what the roster needs next, draft and trade assets, and who might not be back.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption(f"**{exit_line}** · Analysis is team-specific and tied to this postseason run.")

    team_section_header("1 · Season reflection", "📋")
    with st.container(border=True):
        st.markdown(f"**What went right**\n\n{ref['went_right']}")
        st.markdown(f"**What caused elimination**\n\n{ref['elimination_cause']}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Playoff strengths (on tape)**")
            for line in ref["playoff_strengths"]:
                st.markdown(f"- {line}")
        with c2:
            st.markdown("**Playoff weaknesses exposed**")
            for line in ref["playoff_weaknesses"]:
                st.markdown(f"- {line}")

    st.markdown("### 2 · Offseason priorities & roster construction")
    with st.container(border=True):
        st.markdown("**What the roster needs next** (from how this series looked)")
        for p in od["priorities"]:
            st.markdown(f"- {p}")
        ro = od["roster"]
        st.markdown("**Roster construction snapshot**")
        st.markdown(ro["summary"])
        for b in ro["bullets"]:
            st.markdown(f"- {b}")

    st.markdown("### 3 · Future outlook")
    with st.container(border=True):
        for para in od["future"]:
            st.markdown(para)
        d = od["direction"]
        st.markdown(f"**Direction: {d['label']}**")
        st.markdown(d["blurb"])
        st.caption(
            "Championship window, young core vs. aging curve, and whether the path is contender / retool / rebuild — summarized in the direction line above plus these paragraphs."
        )

    st.markdown("### 4 · Draft picks & asset outlook")
    with st.container(border=True):
        for line in od["draft_assets"]:
            st.markdown(f"- {line}")
        st.caption("Future picks, swaps, protections, and trade flexibility — how strong the war chest is for the next star chase or depth upgrade.")

    st.markdown("### 5 · Players who may not return (contracts & movement)")
    with st.container(border=True):
        for line in _offseason_players_out_bullets(od):
            st.markdown(f"- {line}")
        st.caption("Free agents, trade candidates, extension decisions, and cap pressure — not predictions, but the real questions the front office has to answer.")

    st.markdown("### 6 · Ideal player types to add")
    with st.container(border=True):
        st.markdown(
            "Archetypes that fit the holes above — **defensive wing**, **secondary scorer**, **rim protector**, **bench shooting**, **backup creator**, etc."
        )
        for a in od["archetypes"]:
            st.markdown(f"- {a}")


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

# ==========================================================
# Automatic playoff series templates
# ==========================================================
# These are matchup shells, not score data. The app should get scores from the
# NBA API first. Demo/fallback scores are only used when the API is unavailable
# or when you intentionally turn on demo backup in the sidebar.
SECOND_ROUND_SERIES_TEMPLATE = {
    "DET-CLE": {"conf":"East","round":"Second Round","a":"Detroit Pistons","b":"Cleveland Cavaliers"},
    "NYK-PHI": {"conf":"East","round":"Second Round","a":"New York Knicks","b":"Philadelphia 76ers"},
    "OKC-LAL": {"conf":"West","round":"Second Round","a":"Oklahoma City Thunder","b":"Los Angeles Lakers"},
    "SAS-MIN": {"conf":"West","round":"Second Round","a":"San Antonio Spurs","b":"Minnesota Timberwolves"},
}

# Emergency/demo backup only. Merged into the bracket when API has no rows for a series
# (see ``get_playoff_state_cached(True)``). Enough games here to crown winners so CF shells form.
SECOND_ROUND_DEMO_BACKUP = {
    "DET-CLE": {"games":[
        {"Game":"Game 1","Date":"May 4","Score":"Pistons 111, Cavaliers 101","Winner":"Detroit Pistons","GameID":"demo-det-cle-g1"},
        {"Game":"Game 2","Date":"May 6","Score":"Pistons 105, Cavaliers 97","Winner":"Detroit Pistons","GameID":"demo-det-cle-g2"},
        {"Game":"Game 3","Date":"May 8","Score":"Cavaliers 112, Pistons 108","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g3"},
        {"Game":"Game 4","Date":"May 10","Score":"Pistons 102, Cavaliers 99","Winner":"Detroit Pistons","GameID":"demo-det-cle-g4"},
        {"Game":"Game 5","Date":"May 12","Score":"Cavaliers 118, Pistons 114","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g5"},
        {"Game":"Game 6","Date":"May 14","Score":"Cavaliers 101, Pistons 98","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g6"},
        {"Game":"Game 7","Date":"May 16","Score":"Pistons 110, Cavaliers 102","Winner":"Detroit Pistons","GameID":"demo-det-cle-g7"},
    ]},
    "NYK-PHI": {"games":[
        {"Game":"Game 1","Date":"May 4","Score":"Knicks 137, 76ers 98","Winner":"New York Knicks","GameID":"demo-nyk-phi-g1"},
        {"Game":"Game 2","Date":"May 6","Score":"Knicks 108, 76ers 102","Winner":"New York Knicks","GameID":"demo-nyk-phi-g2"},
        {"Game":"Game 3","Date":"May 8","Score":"Knicks 112, 76ers 99","Winner":"New York Knicks","GameID":"demo-nyk-phi-g3"},
        {"Game":"Game 4","Date":"May 10","Score":"Knicks 106, 76ers 95","Winner":"New York Knicks","GameID":"demo-nyk-phi-g4"},
    ]},
    "OKC-LAL": {"games":[
        {"Game":"Game 1","Date":"May 5","Score":"Thunder 118, Lakers 104","Winner":"Oklahoma City Thunder","GameID":"demo-okc-lal-g1"},
        {"Game":"Game 2","Date":"May 7","Score":"Thunder 122, Lakers 111","Winner":"Oklahoma City Thunder","GameID":"demo-okc-lal-g2"},
        {"Game":"Game 3","Date":"May 9","Score":"Lakers 108, Thunder 105","Winner":"Los Angeles Lakers","GameID":"demo-okc-lal-g3"},
        {"Game":"Game 4","Date":"May 11","Score":"Thunder 121, Lakers 109","Winner":"Oklahoma City Thunder","GameID":"demo-okc-lal-g4"},
        {"Game":"Game 5","Date":"May 13","Score":"Thunder 115, Lakers 98","Winner":"Oklahoma City Thunder","GameID":"demo-okc-lal-g5"},
    ]},
    "SAS-MIN": {"games":[
        {"Game":"Game 1","Date":"May 5","Score":"Timberwolves 104, Spurs 102","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g1"},
        {"Game":"Game 2","Date":"May 7","Score":"Timberwolves 110, Spurs 106","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g2"},
        {"Game":"Game 3","Date":"May 9","Score":"Spurs 112, Timberwolves 108","Winner":"San Antonio Spurs","GameID":"demo-sas-min-g3"},
        {"Game":"Game 4","Date":"May 11","Score":"Timberwolves 114, Spurs 105","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g4"},
        {"Game":"Game 5","Date":"May 13","Score":"Spurs 109, Timberwolves 107","Winner":"San Antonio Spurs","GameID":"demo-sas-min-g5"},
        {"Game":"Game 6","Date":"May 15","Score":"Timberwolves 118, Spurs 112","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g6"},
    ]},
}

PLAYOFF_START_DATE = "2026-04-18"
PLAYOFF_END_DATE = "2026-06-30"

FIRST_ROUND_GAME_SCORES = {
    "Detroit Pistons": [
        {"Game":1,"Date":"Apr 18","Matchup":"Magic at Pistons","Score":"Magic 112, Pistons 101","Winner":"Orlando Magic"},
        {"Game":2,"Date":"Apr 21","Matchup":"Magic at Pistons","Score":"Pistons 98, Magic 83","Winner":"Detroit Pistons"},
        {"Game":3,"Date":"Apr 24","Matchup":"Pistons at Magic","Score":"Magic 113, Pistons 105","Winner":"Orlando Magic"},
        {"Game":4,"Date":"Apr 26","Matchup":"Pistons at Magic","Score":"Magic 94, Pistons 88","Winner":"Orlando Magic"},
        {"Game":5,"Date":"Apr 29","Matchup":"Magic at Pistons","Score":"Pistons 116, Magic 109","Winner":"Detroit Pistons"},
        {"Game":6,"Date":"May 1","Matchup":"Pistons at Magic","Score":"Pistons 93, Magic 79","Winner":"Detroit Pistons"},
        {"Game":7,"Date":"May 3","Matchup":"Magic at Pistons","Score":"Pistons 116, Magic 94","Winner":"Detroit Pistons"},
    ],
    "Cleveland Cavaliers": [
        {"Game":1,"Date":"Apr 19","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 126, Raptors 113","Winner":"Cleveland Cavaliers"},
        {"Game":2,"Date":"Apr 22","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 115, Raptors 105","Winner":"Cleveland Cavaliers"},
        {"Game":3,"Date":"Apr 25","Matchup":"Cavaliers at Raptors","Score":"Raptors 126, Cavaliers 104","Winner":"Toronto Raptors"},
        {"Game":4,"Date":"Apr 27","Matchup":"Cavaliers at Raptors","Score":"Raptors 93, Cavaliers 89","Winner":"Toronto Raptors"},
        {"Game":5,"Date":"Apr 29","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 125, Raptors 120","Winner":"Cleveland Cavaliers"},
        {"Game":6,"Date":"May 1","Matchup":"Cavaliers at Raptors","Score":"Raptors 112, Cavaliers 110","Winner":"Toronto Raptors"},
        {"Game":7,"Date":"May 3","Matchup":"Raptors at Cavaliers","Score":"Cavaliers 114, Raptors 102","Winner":"Cleveland Cavaliers"},
    ],
    "New York Knicks": [
        {"Game":1,"Date":"Apr 19","Matchup":"Hawks at Knicks","Score":"Knicks 113, Hawks 102","Winner":"New York Knicks"},
        {"Game":2,"Date":"Apr 22","Matchup":"Hawks at Knicks","Score":"Hawks 107, Knicks 106","Winner":"Atlanta Hawks"},
        {"Game":3,"Date":"Apr 25","Matchup":"Knicks at Hawks","Score":"Hawks 109, Knicks 108","Winner":"Atlanta Hawks"},
        {"Game":4,"Date":"Apr 27","Matchup":"Knicks at Hawks","Score":"Knicks 114, Hawks 98","Winner":"New York Knicks"},
        {"Game":5,"Date":"Apr 29","Matchup":"Hawks at Knicks","Score":"Knicks 126, Hawks 97","Winner":"New York Knicks"},
        {"Game":6,"Date":"May 1","Matchup":"Knicks at Hawks","Score":"Knicks 140, Hawks 89","Winner":"New York Knicks"},
    ],
    "Boston Celtics": [
        {"Game":1,"Date":"Apr 18","Matchup":"76ers at Celtics","Score":"Celtics 123, 76ers 91","Winner":"Boston Celtics"},
        {"Game":2,"Date":"Apr 21","Matchup":"76ers at Celtics","Score":"76ers 111, Celtics 97","Winner":"Philadelphia 76ers"},
        {"Game":3,"Date":"Apr 24","Matchup":"Celtics at 76ers","Score":"Celtics 108, 76ers 100","Winner":"Boston Celtics"},
        {"Game":4,"Date":"Apr 26","Matchup":"Celtics at 76ers","Score":"Celtics 128, 76ers 96","Winner":"Boston Celtics"},
        {"Game":5,"Date":"Apr 28","Matchup":"76ers at Celtics","Score":"76ers 113, Celtics 97","Winner":"Philadelphia 76ers"},
        {"Game":6,"Date":"Apr 30","Matchup":"Celtics at 76ers","Score":"76ers 106, Celtics 93","Winner":"Philadelphia 76ers"},
        {"Game":7,"Date":"May 2","Matchup":"76ers at Celtics","Score":"76ers 109, Celtics 100","Winner":"Philadelphia 76ers"},
    ],
    "Oklahoma City Thunder": [
        {"Game":1,"Date":"Apr 18","Matchup":"Suns at Thunder","Score":"Thunder 119, Suns 84","Winner":"Oklahoma City Thunder"},
        {"Game":2,"Date":"Apr 20","Matchup":"Suns at Thunder","Score":"Thunder 120, Suns 107","Winner":"Oklahoma City Thunder"},
        {"Game":3,"Date":"Apr 23","Matchup":"Thunder at Suns","Score":"Thunder 121, Suns 109","Winner":"Oklahoma City Thunder"},
        {"Game":4,"Date":"Apr 25","Matchup":"Thunder at Suns","Score":"Thunder 131, Suns 122","Winner":"Oklahoma City Thunder"},
    ],
    "San Antonio Spurs": [
        {"Game":1,"Date":"Apr 19","Matchup":"Trail Blazers at Spurs","Score":"Spurs 111, Trail Blazers 98","Winner":"San Antonio Spurs"},
        {"Game":2,"Date":"Apr 22","Matchup":"Trail Blazers at Spurs","Score":"Trail Blazers 106, Spurs 103","Winner":"Portland Trail Blazers"},
        {"Game":3,"Date":"Apr 24","Matchup":"Spurs at Trail Blazers","Score":"Spurs 120, Trail Blazers 108","Winner":"San Antonio Spurs"},
        {"Game":4,"Date":"Apr 26","Matchup":"Spurs at Trail Blazers","Score":"Spurs 114, Trail Blazers 93","Winner":"San Antonio Spurs"},
        {"Game":5,"Date":"Apr 28","Matchup":"Trail Blazers at Spurs","Score":"Spurs 114, Trail Blazers 95","Winner":"San Antonio Spurs"},
    ],
    "Denver Nuggets": [
        {"Game":1,"Date":"Apr 19","Matchup":"Timberwolves at Nuggets","Score":"Nuggets 116, Timberwolves 105","Winner":"Denver Nuggets"},
        {"Game":2,"Date":"Apr 21","Matchup":"Timberwolves at Nuggets","Score":"Timberwolves 119, Nuggets 114","Winner":"Minnesota Timberwolves"},
        {"Game":3,"Date":"Apr 24","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 113, Nuggets 96","Winner":"Minnesota Timberwolves"},
        {"Game":4,"Date":"Apr 26","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 112, Nuggets 96","Winner":"Minnesota Timberwolves"},
        {"Game":5,"Date":"Apr 29","Matchup":"Timberwolves at Nuggets","Score":"Nuggets 125, Timberwolves 113","Winner":"Denver Nuggets"},
        {"Game":6,"Date":"May 1","Matchup":"Nuggets at Timberwolves","Score":"Timberwolves 110, Nuggets 98","Winner":"Minnesota Timberwolves"},
    ],
    "Los Angeles Lakers": [
        {"Game":1,"Date":"Apr 18","Matchup":"Rockets at Lakers","Score":"Lakers 107, Rockets 98","Winner":"Los Angeles Lakers"},
        {"Game":2,"Date":"Apr 20","Matchup":"Rockets at Lakers","Score":"Lakers 101, Rockets 94","Winner":"Los Angeles Lakers"},
        {"Game":3,"Date":"Apr 23","Matchup":"Lakers at Rockets","Score":"Lakers 112, Rockets 108 (OT)","Winner":"Los Angeles Lakers"},
        {"Game":4,"Date":"Apr 25","Matchup":"Lakers at Rockets","Score":"Rockets 116, Lakers 96","Winner":"Houston Rockets"},
        {"Game":5,"Date":"Apr 28","Matchup":"Rockets at Lakers","Score":"Rockets 99, Lakers 93","Winner":"Houston Rockets"},
        {"Game":6,"Date":"Apr 30","Matchup":"Lakers at Rockets","Score":"Lakers 98, Rockets 78","Winner":"Los Angeles Lakers"},
    ],
}
for mirror, source in [("Orlando Magic","Detroit Pistons"),("Toronto Raptors","Cleveland Cavaliers"),("Atlanta Hawks","New York Knicks"),("Philadelphia 76ers","Boston Celtics"),("Phoenix Suns","Oklahoma City Thunder"),("Portland Trail Blazers","San Antonio Spurs"),("Minnesota Timberwolves","Denver Nuggets"),("Houston Rockets","Los Angeles Lakers")]:
    FIRST_ROUND_GAME_SCORES[mirror] = FIRST_ROUND_GAME_SCORES[source]

FALLBACK_TOP_PLAYS = {
    "New York Knicks": [
        {"Game":"Game 2 vs 76ers","Top Play":"New York closed out a 108-102 win and moved the series lead to 2-0.","Why it mattered":"The most recent completed game now drives the dashboard, bracket, and team outlook instead of stale Game 1 data."},
        {"Game":"Game 2 vs 76ers","Top Play":"The Knicks protected the late-game margin and finished the fourth quarter with better control.","Why it mattered":"That is the type of playoff possession management that turns a 1-0 lead into a 2-0 series edge."},
        {"Game":"Game 2 vs 76ers","Top Play":"New York held Philadelphia to 102 points.","Why it mattered":"The defensive floor is becoming a major part of the series story."},
    ],
    "Minnesota Timberwolves": [
        {"Game":"Game 1 vs Spurs","Top Play":"Anthony Edwards delivered late-game shot creation in a tight finish.","Why it mattered":"It gave Minnesota a reliable option when the game tightened."},
        {"Game":"Game 1 vs Spurs","Top Play":"Minnesota's defensive length contested San Antonio's key looks near the rim and on the wing.","Why it mattered":"Those stops protected the narrow win."},
    ],
    "Detroit Pistons": [{"Game":"Game 1 vs Cavaliers","Top Play":"Cade Cunningham organized Detroit's offense and kept the Pistons composed.","Why it mattered":"It helped Detroit take the early series lead."}],
}

# ==========================================================
# API / automatic tracking helpers
# ==========================================================
def safe_int(x, default=0):
    try: return int(x or default)
    except Exception: return default

def safe_float(x, default=0.0):
    try: return float(x or default)
    except Exception: return default

@st.cache_data(ttl=300)
def fetch_completed_games_recent(days_back=120, days_forward=1):
    """API-first completed game pull for the custom playoff bracket.

    This function uses TWO NBA.com-backed nba_api methods:
      1) scoreboardv2 by date, which is good for specific completed dates.
      2) leaguegamefinder for the full 2025-26 Playoffs, which is better when
         scoreboardv2 returns empty on Streamlit Cloud or misses older games.

    Important: this does NOT invent scores. It only updates a custom matchup
    such as NYK-PHI if NBA.com/nba_api has actual completed games for that pair.
    Demo backup scores can still appear only when the sidebar backup switch is on.
    """
    if not NBA_STATS_AVAILABLE:
        return []

    records = []
    today = datetime.now().date()
    playoff_start = datetime.fromisoformat(PLAYOFF_START_DATE).date()
    playoff_end = datetime.fromisoformat(PLAYOFF_END_DATE).date()
    start_date = max(playoff_start, today - timedelta(days=days_back))
    end_date = min(playoff_end, today + timedelta(days=days_forward))

    def add_record(game_id, game_date, home, away, home_pts, away_pts, source):
        if not home or not away:
            return
        home_pts = safe_int(home_pts)
        away_pts = safe_int(away_pts)
        if home_pts == 0 and away_pts == 0:
            return
        winner = home if home_pts > away_pts else away if away_pts > home_pts else None
        d_obj = game_date if hasattr(game_date, 'isoformat') else datetime.fromisoformat(str(game_date)[:10]).date()
        records.append({
            "GameID": str(game_id or ""),
            "GameDate": d_obj.isoformat(),
            "Date": d_obj.strftime("%b %d").replace(" 0", " "),
            "Home": home,
            "Away": away,
            "HomeScore": home_pts,
            "AwayScore": away_pts,
            "Winner": winner,
            "Score": f"{away} {away_pts}, {home} {home_pts}",
            "Matchup": f"{away} at {home}",
            "Source": source,
        })

    # Source 1: scoreboardv2, checked day by day.
    d = start_date
    while d <= end_date:
        for date_str in [d.strftime("%m/%d/%Y"), d.strftime("%Y-%m-%d")]:
            try:
                df = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=20).get_data_frames()[0]
            except Exception:
                continue
            if df is None or df.empty:
                continue
            for _, r in df.iterrows():
                status = str(r.get("GAME_STATUS_TEXT", ""))
                if "Final" not in status:
                    continue
                home = ID_TO_TEAM.get(safe_int(r.get("HOME_TEAM_ID")))
                away = ID_TO_TEAM.get(safe_int(r.get("VISITOR_TEAM_ID")))
                add_record(r.get("GAME_ID", ""), d, home, away, r.get("PTS_HOME"), r.get("PTS_AWAY"), "NBA API scoreboardv2")
            break
        d += timedelta(days=1)

    # Source 2: LeagueGameFinder playoff logs, often more reliable for completed games.
    try:
        # The 2025-26 season is the season that contains the 2026 playoffs.
        lgf = leaguegamefinder.LeagueGameFinder(
            league_id_nullable="00",
            season_nullable="2025-26",
            season_type_nullable="Playoffs",
            timeout=30,
        )
        logs = lgf.get_data_frames()[0]
    except Exception:
        logs = pd.DataFrame()

    if logs is not None and not logs.empty:
        logs = logs.copy()
        logs["GAME_DATE"] = pd.to_datetime(logs["GAME_DATE"], errors="coerce")
        logs = logs[(logs["GAME_DATE"].dt.date >= playoff_start) & (logs["GAME_DATE"].dt.date <= end_date)]
        for game_id, gdf in logs.groupby("GAME_ID"):
            if len(gdf) < 2:
                continue
            rows = gdf.to_dict("records")
            r1, r2 = rows[0], rows[1]
            t1 = ALIAS_TO_TEAM.get(str(r1.get("TEAM_ABBREVIATION", "")))
            t2 = ALIAS_TO_TEAM.get(str(r2.get("TEAM_ABBREVIATION", "")))
            if not t1 or not t2:
                continue
            matchup1 = str(r1.get("MATCHUP", ""))
            if " vs. " in matchup1:
                home_row, away_row = r1, r2
                home, away = t1, t2
            elif " @ " in matchup1:
                home_row, away_row = r2, r1
                home, away = t2, t1
            else:
                # If the home/away marker is missing, still count the game using row order.
                home_row, away_row = r1, r2
                home, away = t1, t2
            game_date = pd.to_datetime(home_row.get("GAME_DATE"), errors="coerce")
            if pd.isna(game_date):
                continue
            add_record(game_id, game_date.date(), home, away, home_row.get("PTS"), away_row.get("PTS"), "NBA API leaguegamefinder")

    # De-dupe across both sources.
    clean = []
    seen = set()
    for g in sorted(records, key=lambda x: (x.get("GameDate", ""), x.get("GameID", ""))):
        ident = g.get("GameID") or f"{g.get('GameDate')}|{g.get('Away')}|{g.get('Home')}|{g.get('Score')}"
        if ident in seen:
            continue
        seen.add(ident)
        clean.append(g)
    return clean


def series_key_for_pair(t1, t2, templates=None):
    pair = {t1, t2}
    templates = templates or SECOND_ROUND_SERIES_TEMPLATE
    for key, s in templates.items():
        if {s["a"], s["b"]} == pair:
            return key
    return None


def canonical_series_key(team_a, team_b):
    """Stable tricode key for a two-team series (order-independent)."""
    if not team_a or not team_b:
        return ""
    x, y = TEAM_ALIASES.get(team_a, ""), TEAM_ALIASES.get(team_b, "")
    if not x or not y:
        return f"{team_a}-{team_b}"
    return "-".join(sorted([x, y]))


def second_round_series_for_team(team_name):
    """The second-round (semifinal) series shell containing this team, if any."""
    second = get_playoff_state_cached(True)["second"]
    for key, s in second.items():
        if team_name in (s.get("a"), s.get("b")):
            return key, s
    return None, None


def clean_and_recount_series(series):
    """De-dupe, sort, label Game 1/Game 2/etc., and recalculate wins."""
    for key, s in series.items():
        a, b = s["a"], s["b"]
        cleaned, seen = [], set()
        for g in s.get("games", []):
            ident = g.get("GameID") or f"{g.get('GameDate','')}|{g.get('Score','')}|{g.get('Winner','')}"
            if ident in seen:
                continue
            seen.add(ident)
            cleaned.append(dict(g))

        def sort_key(g):
            gd = g.get("GameDate", "")
            if gd:
                return gd
            try:
                return datetime.strptime(g.get("Date", "") + " 2026", "%b %d %Y").date().isoformat()
            except Exception:
                return "9999-12-31"

        cleaned = sorted(cleaned, key=sort_key)
        for idx, g in enumerate(cleaned, start=1):
            g["Game"] = f"Game {idx}"
            g.pop("GameDate", None)
        s["games"] = cleaned
        s["a_wins"] = sum(1 for g in cleaned if g.get("Winner") == a)
        s["b_wins"] = sum(1 for g in cleaned if g.get("Winner") == b)
        s["winner"] = a if s["a_wins"] >= 4 else b if s["b_wins"] >= 4 else None
        s["source"] = "NBA API" if any(g.get("Source") == "NBA API" for g in cleaned) else ("Demo backup" if cleaned else "Waiting for API games")
    return series

@st.cache_data(ttl=300)
def build_second_round_series_cached(use_demo_backup=False):
    """Build second-round series automatically from NBA API data.

    If use_demo_backup=False, no scores are hard-coded for the current round.
    The bracket waits for the API to report completed games.
    """
    dynamic = {k: {**v, "a_wins":0, "b_wins":0, "winner":None, "games":[]} for k, v in SECOND_ROUND_SERIES_TEMPLATE.items()}

    api_games = fetch_completed_games_recent()
    for g in api_games:
        key = series_key_for_pair(g.get("Home"), g.get("Away"), SECOND_ROUND_SERIES_TEMPLATE)
        if not key:
            continue
        dynamic[key].setdefault("games", []).append({
            "Game": "",
            "Date": g.get("Date", ""),
            "GameDate": g.get("GameDate", ""),
            "Score": g.get("Score", ""),
            "Winner": g.get("Winner", ""),
            "GameID": g.get("GameID", ""),
            "Source": "NBA API",
        })

    # Optional demo backup only if the API has not produced any games for that series.
    if use_demo_backup:
        for key, backup in SECOND_ROUND_DEMO_BACKUP.items():
            if key in dynamic and not dynamic[key].get("games"):
                dynamic[key]["games"] = [dict(g, Source="Demo backup") for g in backup.get("games", [])]

    return clean_and_recount_series(dynamic)

def build_second_round_series():
    # The sidebar variable is created later; default is strict API mode.
    return build_second_round_series_cached(globals().get("USE_DEMO_BACKUP", False))


@st.cache_data(ttl=300)
def build_conference_finals_series_cached(use_demo_backup=False):
    """East/West Conference Finals shells from second-round winners + API games.

    No hard-coded CF pairings: each conference finals matchup is the two teams
    that won the conference's second-round series, discovered from completed games.
    """
    second = build_second_round_series_cached(use_demo_backup)
    out = {}
    for conf in ("East", "West"):
        semis = [(k, s) for k, s in second.items() if s.get("conf") == conf]
        winners = []
        for _k, s in semis:
            w = s.get("winner")
            if w:
                winners.append(w)
        if len(winners) != 2 or winners[0] == winners[1]:
            continue
        t1, t2 = winners[0], winners[1]
        key = canonical_series_key(t1, t2)
        a, b = sorted([t1, t2], key=lambda t: (TEAM_PROFILES.get(t, {}).get("seed", 99), t))
        shell = {"conf": conf, "round": "Conference Finals", "a": a, "b": b, "a_wins": 0, "b_wins": 0, "winner": None, "games": []}
        for g in fetch_completed_games_recent():
            h, aw = g.get("Home"), g.get("Away")
            if h and aw and {h, aw} == {a, b}:
                shell["games"].append({
                    "Game": "",
                    "Date": g.get("Date", ""),
                    "GameDate": g.get("GameDate", ""),
                    "Score": g.get("Score", ""),
                    "Winner": g.get("Winner", ""),
                    "GameID": g.get("GameID", ""),
                    "Source": "NBA API",
                })
        out[key] = shell
    return clean_and_recount_series(out)


def build_conference_finals_series():
    return build_conference_finals_series_cached(globals().get("USE_DEMO_BACKUP", False))


def _cf_champion_for_conference(cf_map, conf):
    for s in cf_map.values():
        if s.get("conf") == conf and s.get("winner"):
            return s.get("winner")
    return None


@st.cache_data(ttl=300)
def build_nba_finals_series_cached(use_demo_backup=False):
    """NBA Finals shell once both conference champions exist; games from API only."""
    cf = build_conference_finals_series_cached(use_demo_backup)
    east_ch = _cf_champion_for_conference(cf, "East")
    west_ch = _cf_champion_for_conference(cf, "West")
    if not east_ch or not west_ch:
        return {}
    a, b = sorted([east_ch, west_ch], key=lambda t: (TEAM_PROFILES.get(t, {}).get("seed", 99), t))
    key = canonical_series_key(east_ch, west_ch)
    shell = {"conf": "NBA Finals", "round": "NBA Finals", "a": a, "b": b, "a_wins": 0, "b_wins": 0, "winner": None, "games": []}
    for g in fetch_completed_games_recent():
        h, aw = g.get("Home"), g.get("Away")
        if h and aw and {h, aw} == {a, b}:
            shell["games"].append({
                "Game": "",
                "Date": g.get("Date", ""),
                "GameDate": g.get("GameDate", ""),
                "Score": g.get("Score", ""),
                "Winner": g.get("Winner", ""),
                "GameID": g.get("GameID", ""),
                "Source": "NBA API",
            })
    return clean_and_recount_series({key: shell})


def build_nba_finals_series():
    return build_nba_finals_series_cached(globals().get("USE_DEMO_BACKUP", False))


@st.cache_data(ttl=120)
def get_playoff_state_cached(use_demo_backup: bool = True):
    """Single cached snapshot: first-round results, semis, conference finals, and NBA Finals shells.

    ``use_demo_backup`` follows the sidebar toggle for strict API mode; the bracket page passes
    ``True`` so bundled second-round rows still render when the NBA feed is empty.
    """
    second = build_second_round_series_cached(use_demo_backup)
    cf = build_conference_finals_series_cached(use_demo_backup)
    nf = build_nba_finals_series_cached(use_demo_backup)
    east_fr = [dict(s) for s in FIRST_ROUND_SERIES.values() if s.get("conf") == "East"]
    west_fr = [dict(s) for s in FIRST_ROUND_SERIES.values() if s.get("conf") == "West"]
    east_sr = [s for s in second.values() if s.get("conf") == "East"]
    west_sr = [s for s in second.values() if s.get("conf") == "West"]
    east_cf = {k: v for k, v in (cf or {}).items() if v.get("conf") == "East"}
    west_cf = {k: v for k, v in (cf or {}).items() if v.get("conf") == "West"}
    return {
        "second": second,
        "cf": cf or {},
        "finals": nf or {},
        "east_fr": east_fr,
        "west_fr": west_fr,
        "east_sr": east_sr,
        "west_sr": west_sr,
        "east_cf": east_cf if east_cf else None,
        "west_cf": west_cf if west_cf else None,
    }


ROUND_DEPTH_FOR_EXIT = {
    "NBA Finals": 4,
    "Conference Finals": 3,
    "Second Round": 2,
    "First Round": 1,
}


def _iter_playoff_series_shells_merged():
    """All playoff series shells: semis, CF, Finals (cached merge) plus static first round."""
    stt = get_playoff_state_cached(True)
    for s in (stt.get("second") or {}).values():
        if s:
            yield s
    for s in (stt.get("cf") or {}).values():
        if s:
            yield s
    for s in (stt.get("finals") or {}).values():
        if s:
            yield s
    for s in FIRST_ROUND_SERIES.values():
        yield {
            "a": s["a"],
            "b": s["b"],
            "a_wins": int(s.get("a_wins", 0)),
            "b_wins": int(s.get("b_wins", 0)),
            "winner": s.get("winner"),
            "round": "First Round",
            "games": [],
        }


def _last_elimination_series_for_team(team_name):
    """Deepest completed series on the bracket where ``team_name`` lost (any round)."""
    best = None
    best_depth = -1
    for s in _iter_playoff_series_shells_merged():
        if team_name not in (s.get("a"), s.get("b")):
            continue
        w = s.get("winner")
        if not w or w == team_name:
            continue
        rd = str(s.get("round") or "")
        depth = ROUND_DEPTH_FOR_EXIT.get(rd, 0)
        if depth == 0 and "first" in rd.lower():
            depth = 1
        if depth > best_depth:
            best_depth = depth
            best = s
    return best


def _dynamic_playoff_eliminated(team_name):
    """Eliminated from the current postseason if the merged bracket shows a series loss."""
    if team_name not in TEAM_PROFILES:
        return False
    try:
        return _last_elimination_series_for_team(team_name) is not None
    except Exception:
        return False


def _count_series_wins_for_team(team_name):
    """How many completed playoff series ``team_name`` has won this postseason (merged bracket)."""
    if not team_name:
        return 0
    n = 0
    try:
        for s in _iter_playoff_series_shells_merged():
            if team_name not in (s.get("a"), s.get("b")):
                continue
            if s.get("winner") == team_name:
                n += 1
    except Exception:
        return 0
    return n


def infer_next_round_series(round_name, conf=None):
    """Return series dict(s) for Conference Finals or NBA Finals (from cached playoff state)."""
    use_demo = bool(globals().get("USE_DEMO_BACKUP", False))
    stt = get_playoff_state_cached(use_demo)
    if round_name == "Conference Finals":
        cf = stt["cf"]
        if not cf:
            return None
        if conf:
            sub = {k: v for k, v in cf.items() if v.get("conf") == conf}
            return sub if sub else None
        return cf
    if round_name == "NBA Finals":
        nf = stt["finals"]
        return nf if nf else None
    return None


def series_for_team(team_name):
    """Primary playoff series for this team: Finals, then Conference Finals, then active second round.

    After a team clinches a second-round series but before the conference finals shell exists
    (waiting on the other semi), returns (None, None) so the dashboard can show advancement context
    instead of the finished semi game log as the 'current' series.
    """
    use_demo = bool(globals().get("USE_DEMO_BACKUP", False))
    stt = get_playoff_state_cached(use_demo)
    nf = stt["finals"]
    cf = stt["cf"]
    second = stt["second"]
    for key, s in nf.items():
        if team_name in (s.get("a"), s.get("b")):
            return key, s

    for key, s in cf.items():
        if team_name in (s.get("a"), s.get("b")):
            return key, s

    sk, ss = None, None
    for key, s in second.items():
        if team_name in (s.get("a"), s.get("b")):
            sk, ss = key, s
            break
    if not ss:
        return None, None
    if ss.get("winner") == team_name:
        in_cf = any(team_name in (s.get("a"), s.get("b")) for s in (cf or {}).values())
        if not in_cf:
            return None, None
    return sk, ss


def fan_nick(team_name):
    """Short franchise handle for fan-first copy (e.g. Cleveland Cavaliers → Cavaliers)."""
    if not team_name:
        return "your team"
    return str(team_name).split()[-1]


def _elimination_exit_line(team_name):
    """Human-readable playoff exit line from merged bracket data when available."""
    prof = TEAM_PROFILES.get(team_name) or {}
    try:
        lost = _last_elimination_series_for_team(team_name)
    except Exception:
        lost = None
    if not lost:
        return prof.get("first_round_result") or "Playoff exit"
    a, b = lost.get("a"), lost.get("b")
    if team_name not in (a, b):
        return prof.get("first_round_result") or "Playoff exit"
    if team_name == a:
        tw, ow = int(lost.get("a_wins", 0)), int(lost.get("b_wins", 0))
        opp = b
    else:
        tw, ow = int(lost.get("b_wins", 0)), int(lost.get("a_wins", 0))
        opp = a
    rd = str(lost.get("round") or "Playoffs").strip() or "Playoffs"
    return f"{rd}: {fan_nick(team_name)} exit vs {fan_nick(opp)} ({tw}–{ow} final)"


def series_status_text(team_name, series_obj=None):
    if series_obj is not None:
        s = series_obj
    else:
        _, s = series_for_team(team_name)
    if not s:
        nick = fan_nick(team_name)
        _, semi = second_round_series_for_team(team_name)
        if semi and semi.get("winner") == team_name:
            return (
                f"You clinched the second round — {nick} advance while the other semi decides your next opponent."
            )
        if semi and semi.get("winner") and semi.get("winner") != team_name:
            w = semi["winner"]
            return f"That second-round run ended against {fan_nick(w)} — you're done for this postseason, but history pages still tell the story."
        return f"No active series on the board for {nick} right now — check the bracket when the next round locks."
    a, b = s["a"], s["b"]
    aw, bw = s["a_wins"], s["b_wins"]
    team_w = aw if team_name == a else bw
    opp = b if team_name == a else a
    opp_w = bw if team_name == a else aw
    source_note = "" if s.get("source") == "NBA API" else f" ({s.get('source','')})"
    rnd = s.get("round", "Playoffs")
    if team_w > opp_w:
        ledger = f"You're up {team_w}-{opp_w} on {fan_nick(opp)}"
    elif team_w < opp_w:
        ledger = f"You're down {team_w}-{opp_w} to {fan_nick(opp)} — still time to flip the script"
    else:
        ledger = f"You're deadlocked {team_w}-{opp_w} with {fan_nick(opp)}"
    return f"{rnd}: {ledger}{source_note}"


def historic_series_context(team_name, series_obj=None):
    if series_obj is not None:
        s = series_obj
    else:
        _, s = series_for_team(team_name)
    if not s:
        return pd.DataFrame()
    a, b = s["a"], s["b"]
    tw = s["a_wins"] if team_name == a else s["b_wins"]
    ow = s["b_wins"] if team_name == a else s["a_wins"]
    opp = b if team_name == a else a
    nick = fan_nick(team_name)
    on = fan_nick(opp)
    last = s.get("games", [])[-1] if s.get("games") else None
    latest_note = (
        f" Last time out ({last.get('Game')} · {last.get('Date')}): {last.get('Score')}."
        if last
        else " Waiting on the first completed game in the feed."
    )
    if tw == 1 and ow == 0:
        note = f"You're ahead early — protect the next home game and you can really squeeze {on}."
    elif tw == 2 and ow == 0:
        note = f"2-0 is a monster spot for {nick} fans — one more punch and the math gets brutal for {on}."
    elif tw == 1 and ow == 1:
        note = f"Split so far — treat the next game like a reset; whoever owns the first six minutes usually rides the crowd energy."
    elif tw < ow:
        note = f"You're chasing {on} — the honest path back is a defensive tone-setter next, then steal a road game before panic sets in."
    elif tw == 0 and ow == 0:
        note = f"Series hasn't hit the log yet — Game 1 is where {nick} stamps identity vs {on}."
    else:
        note = f"You've got the edge on {on}, but close-out basketball is about rebounds, turnovers, and not gifting free points."
    return pd.DataFrame(
        [
            {
                "Series Status": series_status_text(team_name, s),
                "Data Source": s.get("source", ""),
                "Historical Context": note + latest_note,
            }
        ]
    )

def _nba_et_zone():
    if ZoneInfo:
        try:
            return ZoneInfo("America/New_York")
        except Exception:
            pass
    return None


def _nba_et_now():
    """Current instant in NBA Eastern (IANA) or a UTC-offset fallback if tz data is missing."""
    et = _nba_et_zone()
    if et:
        try:
            return datetime.now(et)
        except Exception:
            pass
    u = datetime.now(timezone.utc)
    mo, dy = u.month, u.day
    # Rough US Eastern DST window (NBA playoffs are EDT): not exact on transition Sundays.
    dst_like = (mo > 3 or (mo == 3 and dy >= 12)) and (mo < 11 or (mo == 11 and dy <= 5))
    off = -4 if dst_like else -5
    return u + timedelta(hours=off)


def _nba_calendar_dates_window(days_each_side=1):
    """Yesterday / today / tomorrow on the NBA calendar (Eastern when available)."""
    try:
        base = _nba_et_now().date()
    except Exception:
        base = datetime.now(timezone.utc).date()
    return [base + timedelta(days=d) for d in range(-days_each_side, days_each_side + 1)]


def _nba_et_date_today():
    """Today's calendar date for NBA scoreboard pulls (America/New_York when possible)."""
    try:
        return _nba_et_now().date()
    except Exception:
        return datetime.now(timezone.utc).date()


def _tricode_from_team_dict(t):
    """Resolve NBA tricode from live CDN or stats shapes (handles missing teamTricode)."""
    if not isinstance(t, dict):
        return ""
    for k in ("teamTricode", "triCode", "teamKey"):
        v = t.get(k)
        if v and str(v).strip():
            s = str(v).strip().upper()
            if s.isalpha() and 2 <= len(s) <= 4:
                return s
    tid = safe_int(t.get("teamId"), 0)
    if tid and tid in ID_TO_TEAM:
        full = ID_TO_TEAM[tid]
        return (TEAM_ALIASES.get(full, "") or "").upper()
    return ""


def normalize_scoreboard_game(g):
    """Ensure home/away carry teamTricode when teamId is present (fixes CDN vs stats mismatches)."""
    if not isinstance(g, dict):
        return g
    out = dict(g)
    for side in ("homeTeam", "awayTeam"):
        t = out.get(side)
        if not isinstance(t, dict):
            continue
        nt = dict(t)
        tri = _tricode_from_team_dict(nt)
        if tri:
            nt["teamTricode"] = tri
        out[side] = nt
    return out


def _merge_scoreboard_games(cdn_row, stats_row):
    """Merge CDN live board row with scoreboardv2 row for the same gameId (fill tricodes, status, scores)."""
    if not isinstance(cdn_row, dict):
        cdn_row = {}
    if not isinstance(stats_row, dict):
        stats_row = {}
    out = dict(cdn_row)
    for key in ("gameStatus", "gameStatusText", "period", "gameClock", "gameTimeUTC", "gameEt"):
        a, b = out.get(key), stats_row.get(key)
        if (a in (None, "", 0)) and b not in (None, "", 0):
            out[key] = b
    st_out = safe_int(out.get("gameStatus"), 0)
    st_b = safe_int(stats_row.get("gameStatus"), 0)
    if st_b > st_out:
        out["gameStatus"] = stats_row.get("gameStatus")
    p_out = safe_int(out.get("period"), 0)
    p_b = safe_int(stats_row.get("period"), 0)
    if p_b > p_out:
        out["period"] = stats_row.get("period")
    for side in ("homeTeam", "awayTeam"):
        p = out.get(side) or {}
        s = stats_row.get(side) or {}
        if not isinstance(p, dict):
            p = {}
        if not isinstance(s, dict):
            s = {}
        m = dict(p)
        if not _tricode_from_team_dict(m) and _tricode_from_team_dict(s):
            m["teamTricode"] = s.get("teamTricode") or _tricode_from_team_dict(s)
        if not safe_int(m.get("teamId"), 0) and safe_int(s.get("teamId"), 0):
            m["teamId"] = s.get("teamId")
        ps, ss = safe_int(m.get("score"), -1), safe_int(s.get("score"), -1)
        if ss > ps:
            m["score"] = s.get("score")
        elif ps < 0 and ss >= 0:
            m["score"] = s.get("score")
        out[side] = m
    return out


def _game_involves_team(game, team_name):
    """True if this scoreboard row includes team_name (home or away), by tricode or teamId."""
    if not team_name or not isinstance(game, dict):
        return False
    alias = (TEAM_ALIASES.get(team_name) or "").upper()
    tid = TEAM_IDS.get(team_name, 0)
    for side in ("homeTeam", "awayTeam"):
        t = game.get(side) or {}
        if not isinstance(t, dict):
            continue
        tri = _tricode_from_team_dict(t).upper()
        if alias and tri == alias:
            return True
        if tid and safe_int(t.get("teamId"), 0) == tid:
            return True
    return False


def _live_gc_team_name_tokens(team_name):
    """Lowercase tokens for fuzzy scoreboard matching (CDN rows sometimes omit ids)."""
    if not team_name:
        return frozenset()
    nick = fan_nick(team_name).strip().lower()
    full = str(team_name).strip().lower()
    last = full.split()[-1] if full else ""
    alias = (TEAM_ALIASES.get(team_name) or "").strip().lower()
    out = {full, nick, last, alias}
    return frozenset(x for x in out if x)


def _live_gc_side_tokens(team_obj):
    """Identifiers present on one home/away dict."""
    if not isinstance(team_obj, dict):
        return frozenset()
    tid = safe_int(team_obj.get("teamId"), 0)
    tri = (_tricode_from_team_dict(team_obj) or str(team_obj.get("teamTricode") or "")).strip().upper()
    city = str(team_obj.get("teamCity") or "").strip().lower()
    nick = str(team_obj.get("teamName") or "").strip().lower()
    bits = {tri.lower(), nick, city}
    if city and nick:
        bits.add(f"{city} {nick}".strip())
    if tid and tid in ID_TO_TEAM:
        fn = ID_TO_TEAM[tid]
        bits.add(fn.lower())
        bits.add(fan_nick(fn).lower())
        bits.add(fn.split()[-1].lower())
    if tri and tri in ALIAS_TO_TEAM:
        fn2 = ALIAS_TO_TEAM[tri]
        bits.add(fn2.lower())
        bits.add(fan_nick(fn2).lower())
    return frozenset(x for x in bits if x)


def _game_involves_team_loose(game, team_name):
    """Like _game_involves_team but tolerates partial CDN payloads (name-only sides)."""
    if _game_involves_team(game, team_name):
        return True
    if not team_name or not isinstance(game, dict):
        return False
    need = _live_gc_team_name_tokens(team_name)
    if not need:
        return False
    for side in ("homeTeam", "awayTeam"):
        side_ts = _live_gc_side_tokens(game.get(side) or {})
        if need & side_ts:
            return True
    return False


def _coarse_live_signal_v2(g):
    """Heuristic: stats row suggests in-progress even if GAME_STATUS_ID lags."""
    if not isinstance(g, dict):
        return False
    gsi = safe_int(g.get("gameStatus"), 0)
    per = safe_int(g.get("period"), 0)
    txt = (g.get("gameStatusText") or "").lower()
    if gsi == 2:
        return True
    if per >= 1 and "final" not in txt:
        return True
    markers = ("q1", "q2", "q3", "q4", "q5", "ot", "half", "halftime", "1st", "2nd", "3rd", "4th", "overtime")
    return any(m in txt for m in markers) and "final" not in txt


def _line_v2_total_pts(lr):
    """Total points from ScoreboardV2 line score row (PTS may be null pregame)."""
    if lr is None:
        return 0
    try:
        raw = lr.get("PTS")
        if raw is not None and str(raw).strip() != "" and str(raw).lower() != "nan":
            return safe_int(raw, 0)
    except Exception:
        pass
    s = 0
    for i in range(1, 5):
        s += safe_int(lr.get(f"PTS_QTR{i}"), 0)
    for j in range(1, 11):
        s += safe_int(lr.get(f"PTS_OT{j}"), 0)
    return s


def _v2_team_dict_from_line(lr, tid):
    tri = str(lr.get("TEAM_ABBREVIATION", "") or "").strip().upper()
    city = str(lr.get("TEAM_CITY_NAME", "") or "")
    nick = str(lr.get("TEAM_NAME", "") or "")
    full = (ALIAS_TO_TEAM.get(tri) or f"{city} {nick}".strip() or tri)
    if " " in full:
        tcity, tnick = full.rsplit(" ", 1)[0], full.rsplit(" ", 1)[1]
    else:
        tcity, tnick = city, nick
    return {
        "teamId": safe_int(tid, 0),
        "teamTricode": tri,
        "teamName": tnick,
        "teamCity": tcity,
        "score": _line_v2_total_pts(lr),
    }


def _v3_home_away_rows(ts_df, game_code_full):
    """Pick home/away line rows; gameCode tail is usually awayTri(3)+homeTri(3), e.g. CLEDET."""
    tail = str(game_code_full or "").split("/")[-1].strip().upper()
    up = {str(r.get("teamTricode") or "").strip().upper(): r for _, r in ts_df.iterrows()}
    if len(tail) >= 6:
        a_tri, h_tri = tail[:3], tail[3:6]
        ar, hr = up.get(a_tri), up.get(h_tri)
        if ar is not None and hr is not None:
            return hr, ar
    if len(ts_df) >= 2:
        return ts_df.iloc[0], ts_df.iloc[1]
    return None, None


def _pseudo_games_from_scoreboard_v3(game_date):
    if not (NBA_STATS_AVAILABLE and NBA_SCOREBOARD_V3_AVAILABLE and scoreboardv3):
        return []
    out = []
    d = game_date if hasattr(game_date, "strftime") else datetime.strptime(str(game_date)[:10], "%Y-%m-%d").date()
    fmts = (d.strftime("%Y-%m-%d"), d.strftime("%m/%d/%Y"))
    for fmt in fmts:
        for attempt in range(2):
            try:
                try:
                    dfs = scoreboardv3.ScoreboardV3(
                        game_date=fmt, league_id="00", headers=NBA_STATS_HEADERS, timeout=10
                    ).get_data_frames()
                except TypeError:
                    try:
                        dfs = scoreboardv3.ScoreboardV3(game_date=fmt, league_id="00", timeout=10).get_data_frames()
                    except TypeError:
                        dfs = scoreboardv3.ScoreboardV3(game_date=fmt, league_id="00").get_data_frames()
            except Exception:
                continue
            if dfs is None or len(dfs) < 3 or dfs[1].empty or dfs[2].empty:
                break
            games_hdr, teams_df = dfs[1], dfs[2]
            for _, gr in games_hdr.iterrows():
                gid = str(gr.get("gameId") or "")
                if not gid:
                    continue
                ts = teams_df[teams_df["gameId"].astype(str) == gid]
                if ts.shape[0] < 2:
                    continue
                home_lr, away_lr = _v3_home_away_rows(ts, gr.get("gameCode", ""))
                if home_lr is None or away_lr is None:
                    continue
                hid = safe_int(home_lr.get("teamId"), 0)
                aid = safe_int(away_lr.get("teamId"), 0)
                gst = str(gr.get("gameStatusText") or "")
                gst_l = gst.lower()
                gsi = safe_int(gr.get("gameStatus"), 0)
                per = safe_int(gr.get("period"), 0)
                live_like = gsi == 2 or (
                    per >= 1
                    and "final" not in gst_l
                    and any(
                        x in gst_l
                        for x in (
                            "q1", "q2", "q3", "q4", "q5", "ot", "half", "halftime",
                            "1st", "2nd", "3rd", "4th", "overtime",
                        )
                    )
                )
                if gsi == 3 or "final" in gst_l:
                    cdn_st = 3
                elif live_like:
                    cdn_st = 2
                else:
                    cdn_st = 1
                period = per if per > 0 else (4 if cdn_st == 3 else 1)
                clock = str(gr.get("gameClock") or "")
                h_tri = str(home_lr.get("teamTricode") or "").upper()
                a_tri = str(away_lr.get("teamTricode") or "").upper()
                pseudo = {
                    "gameId": gid,
                    "gameStatus": cdn_st,
                    "gameStatusText": gst,
                    "period": period,
                    "gameClock": clock,
                    "gameTimeUTC": gr.get("gameTimeUTC"),
                    "gameEt": str(gr.get("gameEt") or ""),
                    "seriesText": str(gr.get("seriesText") or gr.get("gameLabel") or ""),
                    "_source": "scoreboardv3",
                    "_game_date_est": d.strftime("%Y-%m-%d"),
                    "homeTeam": {
                        "teamId": hid,
                        "teamTricode": h_tri,
                        "teamName": str(home_lr.get("teamName") or ""),
                        "teamCity": str(home_lr.get("teamCity") or ""),
                        "score": safe_int(home_lr.get("score"), 0),
                    },
                    "awayTeam": {
                        "teamId": aid,
                        "teamTricode": a_tri,
                        "teamName": str(away_lr.get("teamName") or ""),
                        "teamCity": str(away_lr.get("teamCity") or ""),
                        "score": safe_int(away_lr.get("score"), 0),
                    },
                }
                out.append(pseudo)
            if out:
                return out
            break
    return out


def _pseudo_games_from_scoreboard_v2(game_date):
    """ScoreboardV2 fallback — never drops a game solely because TEAM_IDS is incomplete."""
    if not NBA_STATS_AVAILABLE:
        return []
    out = []
    d = game_date if hasattr(game_date, "strftime") else datetime.strptime(str(game_date)[:10], "%Y-%m-%d").date()
    for fmt in (d.strftime("%m/%d/%Y"), d.strftime("%Y-%m-%d")):
        try:
            try:
                dfs = scoreboardv2.ScoreboardV2(
                    game_date=fmt, league_id="00", day_offset=0, headers=NBA_STATS_HEADERS, timeout=8
                ).get_data_frames()
            except TypeError:
                try:
                    dfs = scoreboardv2.ScoreboardV2(game_date=fmt, league_id="00", day_offset=0, timeout=8).get_data_frames()
                except TypeError:
                    dfs = scoreboardv2.ScoreboardV2(game_date=fmt, league_id="00", day_offset=0).get_data_frames()
        except Exception:
            continue
        if dfs is None or len(dfs) < 2 or dfs[0].empty:
            continue
        hdr, lines = dfs[0], dfs[1]
        lines_by_gid = {}
        if lines is not None and not lines.empty:
            for _, lr in lines.iterrows():
                gid = str(lr.get("GAME_ID", ""))
                if gid:
                    lines_by_gid.setdefault(gid, []).append(lr)
        for _, r in hdr.iterrows():
            gid = str(r.get("GAME_ID", ""))
            if not gid:
                continue
            hid, vid = safe_int(r.get("HOME_TEAM_ID")), safe_int(r.get("VISITOR_TEAM_ID"))
            lr_h = next((x for x in lines_by_gid.get(gid, []) if safe_int(x.get("TEAM_ID")) == hid), None)
            lr_a = next((x for x in lines_by_gid.get(gid, []) if safe_int(x.get("TEAM_ID")) == vid), None)
            ht, at = ID_TO_TEAM.get(hid), ID_TO_TEAM.get(vid)
            if ht and at:
                h_tri, a_tri = TEAM_ALIASES.get(ht, ""), TEAM_ALIASES.get(at, "")
                hpts = _line_v2_total_pts(lr_h) if lr_h is not None else 0
                apts = _line_v2_total_pts(lr_a) if lr_a is not None else 0
            elif lr_h is not None and lr_a is not None:
                h_tri = str(lr_h.get("TEAM_ABBREVIATION", "") or "").upper()
                a_tri = str(lr_a.get("TEAM_ABBREVIATION", "") or "").upper()
                hpts, apts = _line_v2_total_pts(lr_h), _line_v2_total_pts(lr_a)
            else:
                continue
            live_period = safe_int(r.get("LIVE_PERIOD"), 0)
            gst = str(r.get("GAME_STATUS_TEXT", "") or "")
            gst_l = gst.lower()
            gsi = safe_int(r.get("GAME_STATUS_ID"), 0)
            live_like = (
                gsi == 2
                or live_period >= 1
                or any(
                    x in gst_l
                    for x in (
                        "q1", "q2", "q3", "q4", "q5", "ot", "half", "halftime",
                        "1st", "2nd", "3rd", "4th", "overtime",
                    )
                )
            )
            if gsi == 3 or "final" in gst_l:
                cdn_st, _ph = 3, "final"
            elif live_like and "final" not in gst_l:
                cdn_st, _ph = 2, "live"
            else:
                cdn_st, _ph = 1, "scheduled"
            period = live_period if live_period > 0 else (4 if cdn_st == 3 else 1)
            clock = str(r.get("LIVE_PC_TIME") or "")
            if ht and at:
                home_team = {
                    "teamId": hid,
                    "teamTricode": h_tri,
                    "teamName": ht.split()[-1] if ht else "",
                    "teamCity": " ".join(ht.split()[:-1]) if ht and " " in ht else "",
                    "score": hpts,
                }
                away_team = {
                    "teamId": vid,
                    "teamTricode": a_tri,
                    "teamName": at.split()[-1] if at else "",
                    "teamCity": " ".join(at.split()[:-1]) if at and " " in at else "",
                    "score": apts,
                }
            else:
                home_team = _v2_team_dict_from_line(lr_h, hid)
                away_team = _v2_team_dict_from_line(lr_a, vid)
            pseudo = {
                "gameId": gid,
                "gameStatus": cdn_st,
                "gameStatusText": gst,
                "period": period,
                "gameClock": clock,
                "gameTimeUTC": None,
                "gameEt": str(r.get("LIVE_PERIOD_TIME_BCAST") or ""),
                "seriesText": str(r.get("GAMECODE", "") or ""),
                "_source": "scoreboardv2",
                "_game_date_est": str(r.get("GAME_DATE_EST", "")),
                "homeTeam": home_team,
                "awayTeam": away_team,
            }
            out.append(pseudo)
        if out:
            break
    return out


@st.cache_data(ttl=22)
def get_live_games():
    """Today's live CDN scoreboard (NBA 'today' in ET). Cached ~20s to balance freshness vs load."""
    if not NBA_LIVE_AVAILABLE:
        return []
    try:
        try:
            return scoreboard.ScoreBoard(timeout=5).get_dict().get("scoreboard", {}).get("games", []) or []
        except TypeError:
            return scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", []) or []
    except Exception:
        return []


@st.cache_data(ttl=28)
def _scoreboard_v2_games_for_date(game_date):
    """Stats scoreboard for one calendar date → pseudo-live dicts (ScoreboardV3 first, then fixed V2)."""
    if not NBA_STATS_AVAILABLE:
        return []
    v3 = _pseudo_games_from_scoreboard_v3(game_date)
    if v3:
        return v3
    return _pseudo_games_from_scoreboard_v2(game_date)


def _gather_team_scoreboard_games(team_name):
    """Merge CDN live board + scoreboardv2 (yesterday→tomorrow ET); match by tricode, triCode, teamId, or loose name tokens."""
    if not team_name or (not TEAM_ALIASES.get(team_name) and not TEAM_IDS.get(team_name)):
        return []
    profile = TEAM_PROFILES.get(team_name) or {}
    opponent = profile.get("current_opponent")
    by_gid = {}
    for g in get_live_games():
        gid = str(g.get("gameId") or "")
        if gid:
            by_gid[gid] = dict(g)
    for d in _nba_calendar_dates_window(1):
        for g in _scoreboard_v2_games_for_date(d):
            gid = str(g.get("gameId") or "")
            if not gid:
                continue
            if gid in by_gid:
                by_gid[gid] = _merge_scoreboard_games(by_gid[gid], g)
            else:
                by_gid[gid] = dict(g)
    strict, loose = [], []
    for g in by_gid.values():
        g2 = normalize_scoreboard_game(dict(g))
        if _game_involves_team(g2, team_name) or (opponent and _game_involves_team(g2, opponent)):
            strict.append(g2)
        elif _game_involves_team_loose(g2, team_name) or (opponent and _game_involves_team_loose(g2, opponent)):
            loose.append(g2)
    return strict if strict else loose


@st.cache_data(ttl=22)
def _merged_stats_games_et_window():
    """All stats scoreboard games for yesterday→tomorrow Eastern (deduped by gameId). CDN not used."""
    if not NBA_STATS_AVAILABLE:
        return []
    merged = {}
    try:
        for d in _nba_calendar_dates_window(1):
            for g in _scoreboard_v2_games_for_date(d):
                gid = str((g or {}).get("gameId") or "")
                if gid:
                    merged[gid] = dict(g)
        return [normalize_scoreboard_game(dict(x)) for x in merged.values()]
    except Exception:
        return []


@st.cache_data(ttl=35)
def _scoreboard_pipeline_debug_report():
    """Raw shapes for ScoreboardV3/V2 — for the Live Game Center debug panel."""
    rows = []
    rows.append(f"nba_et_now={_nba_et_now().isoformat()}")
    rows.append(f"et_window_dates={[d.isoformat() for d in _nba_calendar_dates_window(1)]}")
    rows.append(f"NBA_SCOREBOARD_V3_AVAILABLE={NBA_SCOREBOARD_V3_AVAILABLE}")
    for d in _nba_calendar_dates_window(1):
        ds = d.isoformat()
        if NBA_SCOREBOARD_V3_AVAILABLE and scoreboardv3:
            for fmt in (d.strftime("%Y-%m-%d"), d.strftime("%m/%d/%Y")):
                try:
                    try:
                        dfs = scoreboardv3.ScoreboardV3(
                            game_date=fmt, league_id="00", headers=NBA_STATS_HEADERS, timeout=10
                        ).get_data_frames()
                    except TypeError:
                        dfs = scoreboardv3.ScoreboardV3(game_date=fmt, league_id="00", timeout=10).get_data_frames()
                    rows.append(f"v3 date={ds} fmt={fmt} n_frames={len(dfs)} shapes={[x.shape for x in dfs]}")
                    if dfs and len(dfs) > 1 and hasattr(dfs[1], "columns"):
                        rows.append(f"v3 date={ds} game_row_columns={list(dfs[1].columns)}")
                    break
                except Exception as e:
                    rows.append(f"v3 date={ds} fmt={fmt} ERROR {e!r}")
        try:
            n_merged = len(_scoreboard_v2_games_for_date(d))
            rows.append(f"pseudo_games_after_merge(date={ds}) count={n_merged}")
        except Exception as e:
            rows.append(f"pseudo_games(date={ds}) ERROR {e!r}")
    return "\n".join(rows)


def _live_broadcast_phase(g):
    """Classify scoreboard row for UI routing."""
    st = safe_int(g.get("gameStatus"), 0)
    txt = (g.get("gameStatusText") or "").lower()
    per = safe_int(g.get("period"), 0)
    clock = str(g.get("gameClock") or "").strip()
    if st == 3 or "final" in txt:
        return "postgame"
    if st == 2:
        return "live"
    if any(
        x in txt
        for x in (
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "ot",
            "half",
            "halftime",
            "1st",
            "2nd",
            "3rd",
            "4th",
            "overtime",
        )
    ) and "final" not in txt:
        return "live"
    if per >= 1 and re.match(r"^\d{1,2}:\d{2}", clock) and "final" not in txt and st != 3:
        return "live"
    if st != 3 and "final" not in txt and per >= 1 and st != 1:
        return "live"
    if ":" in txt and ("pm" in txt or "am" in txt) and "final" not in txt:
        return "pregame"
    if st == 1:
        return "pregame"
    return "pregame"


def _tipoff_utc_dt(g):
    raw = g.get("gameTimeUTC")
    if raw:
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            pass
    et = _nba_et_zone()
    dstr = g.get("_game_date_est")
    if et and dstr:
        try:
            d = datetime.strptime(str(dstr)[:10], "%Y-%m-%d").date()
            return datetime.combine(d, time(19, 30), tzinfo=et).astimezone(timezone.utc)
        except Exception:
            pass
    return None


def _seconds_to_tipoff(g):
    tip = _tipoff_utc_dt(g)
    if not tip:
        return None
    now = datetime.now(timezone.utc)
    return (tip.astimezone(timezone.utc) - now).total_seconds()


def _pick_featured_game_for_team_uncached(team_name):
    """Prefer in-progress, then tipoff soon, then most recent final, else next scheduled."""
    games = _gather_team_scoreboard_games(team_name)
    if not games:
        return None

    def sort_key(g):
        phase = _live_broadcast_phase(g)
        sec = _seconds_to_tipoff(g)
        if sec is None:
            sec = 9e9
        if phase == "live":
            return (0, 0, sec)
        if phase == "pregame":
            if sec is not None and 0 < sec <= 3600:
                return (1, sec, 0)
            if sec is not None and sec > 3600:
                return (2, sec, 0)
            return (3, sec, 0)
        if phase == "postgame":
            return (4, -sec if sec else 0, 0)
        return (5, sec, 0)

    games.sort(key=sort_key)
    return normalize_scoreboard_game(dict(games[0]))


@st.cache_data(ttl=22)
def _pick_featured_game_for_team_cached(team_name: str):
    """Cached featured row — home hub + live strip should not re-merge the full ET window every rerun."""
    return _pick_featured_game_for_team_uncached(team_name)


def _pick_featured_game_for_team(team_name):
    return _pick_featured_game_for_team_cached(team_name)


def find_live_game_for_team(team_name):
    """Best scoreboard row for sidebar team (live CDN + scoreboardv2 window)."""
    return _pick_featured_game_for_team(team_name)


@st.cache_data(ttl=12)
def featured_broadcast_state_cached(team_name: str):
    """Normalize featured row for hub + live center — cached separately from raw pick."""
    try:
        g = find_live_game_for_team(team_name)
        if not g:
            return None
        g = normalize_scoreboard_game(dict(g))
        phase = _live_broadcast_phase(g)
        sec = _seconds_to_tipoff(g)
        soon = sec is not None and 0 < sec <= 3600
        return {"game": g, "phase": phase, "seconds_to_tip": sec, "starting_soon": bool(soon)}
    except Exception as e:
        return {
            "game": None,
            "phase": "unknown",
            "seconds_to_tip": None,
            "starting_soon": False,
            "_merge_error": repr(e),
        }


def featured_broadcast_state(team_name):
    """Single merged scoreboard row for Live Game Center + Home hub (CDN + stats, normalized)."""
    return featured_broadcast_state_cached(team_name)


def get_live_game_detection_context_impl(team_name):
    """When the merged featured pick is empty: classify today ET vs window using CDN + scoreboardv2 (no false 'no game')."""
    featured = _pick_featured_game_for_team_uncached(team_name)
    if featured is not None:
        today_et = _nba_et_date_today()
        d_est = featured.get("_game_date_est")
        has_today = False
        if d_est:
            try:
                has_today = datetime.strptime(str(d_est)[:10], "%Y-%m-%d").date() == today_et
            except Exception:
                pass
        return {
            "tier": "ok",
            "message": "",
            "has_today_et": has_today,
            "likely_feed_gap": False,
            "window_has_team": True,
            "best_stub_game": featured,
            "featured": featured,
        }
    profile = TEAM_PROFILES.get(team_name) or {}
    opponent = profile.get("current_opponent")
    today_et = _nba_et_date_today()
    window_rows = []
    for d in _nba_calendar_dates_window(1):
        if not NBA_STATS_AVAILABLE:
            break
        for g in _scoreboard_v2_games_for_date(d):
            gn = normalize_scoreboard_game(dict(g))
            if _game_involves_team_loose(gn, team_name) or (opponent and _game_involves_team_loose(gn, opponent)):
                window_rows.append({"date": d, "game": gn})
    cdn_hits = []
    if NBA_LIVE_AVAILABLE:
        for g in get_live_games():
            gn = normalize_scoreboard_game(dict(g))
            if _game_involves_team_loose(gn, team_name) or (opponent and _game_involves_team_loose(gn, opponent)):
                cdn_hits.append(gn)
    today_games = [x for x in window_rows if x["date"] == today_et]
    has_today_et = len(today_games) > 0
    v2_live_today = any(_coarse_live_signal_v2(x["game"]) for x in today_games)
    has_window = bool(window_rows or cdn_hits)

    best_stub = None
    if today_games:
        best_stub = today_games[0]["game"]
    elif window_rows:
        best_stub = window_rows[0]["game"]
    elif cdn_hits:
        best_stub = cdn_hits[0]

    if has_today_et and v2_live_today:
        tier = "likely_live_feed_gap"
        message = (
            "Game may be in progress, but the live feed is delayed. "
            "Today's stats scoreboard shows in-progress signals — wait for CDN to sync or tap refresh."
        )
    elif has_today_et:
        tier = "scheduled_today"
        message = "Game scheduled today — live feed not detected yet."
    elif has_window:
        tier = "window_off_today"
        message = (
            f"{fan_nick(team_name)} show up on the **yesterday→tomorrow ET** stats board, but not on **today's ET date**. "
            "Double-check slate timing if you expected a tip tonight."
        )
    else:
        tier = "no_game_window"
        message = (
            f"No {fan_nick(team_name)} (or sidebar opponent) row in **live CDN + stats scoreboard** for yesterday through tomorrow Eastern."
        )

    return {
        "tier": tier,
        "message": message,
        "has_today_et": has_today_et,
        "likely_feed_gap": tier == "likely_live_feed_gap",
        "window_has_team": has_window,
        "best_stub_game": best_stub,
        "featured": None,
    }


@st.cache_data(ttl=12)
def get_live_game_detection_context_cached(team_name: str):
    """ET-window detection — short TTL so Live Game Center tracks tip/live transitions."""
    return get_live_game_detection_context_impl(team_name)


def get_live_game_detection_context(team_name):
    return get_live_game_detection_context_cached(team_name)


def get_current_or_today_game_uncached(team_name):
    """Resolve the best scoreboard row for Live Game Center — multi-source, never a single point of failure."""
    errors = []
    try:
        det_ctx = dict(get_live_game_detection_context_impl(team_name))
    except Exception as e:
        errors.append(repr(e))
        det_ctx = {
            "tier": "unknown",
            "message": str(e),
            "best_stub_game": None,
            "featured": None,
            "has_today_et": False,
        }

    game_row = det_ctx.get("featured") or det_ctx.get("best_stub_game")
    data_source = game_row.get("_source") if isinstance(game_row, dict) else None

    if not game_row and NBA_LIVE_AVAILABLE:
        try:
            for g in get_live_games():
                gn = normalize_scoreboard_game(dict(g))
                if _game_involves_team_loose(gn, team_name):
                    game_row = gn
                    data_source = "live_cdn_rescue"
                    break
        except Exception as e:
            errors.append(f"cdn_rescue:{e!r}")

    if not game_row and NBA_STATS_AVAILABLE:
        try:
            opp = TEAM_PROFILES.get(team_name, {}).get("current_opponent")
            pool = []
            merged = {}
            for d in _nba_calendar_dates_window(1):
                for g in _scoreboard_v2_games_for_date(d):
                    gid = str((g or {}).get("gameId") or "")
                    if gid:
                        merged[gid] = normalize_scoreboard_game(dict(g))
            for g in merged.values():
                if _game_involves_team_loose(g, team_name) or (opp and _game_involves_team_loose(g, opp)):
                    pool.append(g)

            def _sort_key(g):
                phase = _live_broadcast_phase(g)
                sec = _seconds_to_tipoff(g)
                if sec is None:
                    sec = 9e9
                if phase == "live":
                    return (0, 0, sec)
                if phase == "pregame":
                    if sec is not None and 0 < sec <= 3600:
                        return (1, sec, 0)
                    if sec is not None and sec > 3600:
                        return (2, sec, 0)
                    return (3, sec, 0)
                if phase == "postgame":
                    return (4, -sec if sec else 0, 0)
                return (5, sec, 0)

            if pool:
                pool.sort(key=_sort_key)
                game_row = pool[0]
                data_source = game_row.get("_source") or "stats_et_rescue"
        except Exception as e:
            errors.append(f"stats_rescue:{e!r}")

    phase = _live_broadcast_phase(game_row) if game_row else "unknown"
    if phase == "live":
        gstat = "live"
    elif phase == "postgame":
        gstat = "final"
    elif phase == "pregame":
        gstat = "scheduled"
    else:
        gstat = "unavailable"

    home = away = {}
    home_score = away_score = period = 0
    clock = status_txt = gid = ""
    home_name = away_name = ""

    if game_row:
        home = game_row.get("homeTeam") or {}
        away = game_row.get("awayTeam") or {}
        home_tri = (home.get("teamTricode") or "") or _tricode_from_team_dict(home)
        away_tri = (away.get("teamTricode") or "") or _tricode_from_team_dict(away)
        home_score = safe_int(home.get("score", 0))
        away_score = safe_int(away.get("score", 0))
        home_name = _live_team_full_name(home_tri, home)
        away_name = _live_team_full_name(away_tri, away)
        period = safe_int(game_row.get("period", 0), 0)
        clock = str(game_row.get("gameClock") or "").strip()
        status_txt = str(game_row.get("gameStatusText") or "").strip()
        gid = str(game_row.get("gameId") or "")

    if game_row:
        det_ctx = dict(det_ctx)
        det_ctx["tier"] = "ok"
        det_ctx["likely_feed_gap"] = False
        det_ctx["message"] = ""

    return {
        "game_found": game_row is not None,
        "game_status": gstat,
        "phase": phase,
        "game_row": game_row,
        "home_team": home_name,
        "away_team": away_name,
        "home_score": home_score,
        "away_score": away_score,
        "period": period,
        "clock": clock,
        "game_status_text": status_txt,
        "game_id": gid,
        "data_source": data_source or ("none" if not game_row else "unknown"),
        "error_messages": errors,
        "detection_tier": det_ctx.get("tier", "unknown"),
        "detection_message": det_ctx.get("message", ""),
        "det_ctx": det_ctx,
    }


@st.cache_data(ttl=12)
def get_current_or_today_game(team_name: str):
    """Cached snapshot for Live Game Center — refreshes quickly during live play."""
    return get_current_or_today_game_uncached(team_name)


@st.cache_data(ttl=30)
def get_live_boxscore(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return {}
    try:
        try:
            return boxscore.BoxScore(game_id, timeout=8).get_dict().get("game", {})
        except TypeError:
            return boxscore.BoxScore(game_id).get_dict().get("game", {})
    except Exception:
        return {}


@st.cache_data(ttl=30)
def get_live_playbyplay(game_id):
    if not NBA_LIVE_AVAILABLE or not game_id:
        return []
    try:
        try:
            return playbyplay.PlayByPlay(game_id, timeout=8).get_dict().get("game", {}).get("actions", [])
        except TypeError:
            return playbyplay.PlayByPlay(game_id).get_dict().get("game", {}).get("actions", [])
    except Exception:
        return []

@st.cache_data(ttl=30)
def get_playbyplay_by_game_id(game_id):
    return get_live_playbyplay(game_id)


@st.cache_data(ttl=21600)
def fetch_current_roster(team_name, season=CURRENT_NBA_SEASON):
    """Return current NBA.com roster for a team. Falls back safely if NBA API is unavailable."""
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    tid = TEAM_IDS.get(team_name)
    if not tid:
        return pd.DataFrame()
    try:
        df = commonteamroster.CommonTeamRoster(team_id=tid, season=season, timeout=20).get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        # CommonTeamRoster columns usually include PLAYER, NUM, POSITION, HEIGHT, WEIGHT, AGE, EXP, SCHOOL, PLAYER_ID
        rename = {"PLAYER": "Player", "POSITION": "Position", "NUM": "Number", "PLAYER_ID": "PlayerID"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        keep = [c for c in ["Player", "Position", "Number", "PlayerID", "AGE", "EXP", "SCHOOL"] if c in df.columns]
        return df[keep].drop_duplicates(subset=["Player"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=21600)
def fetch_team_rotation_by_minutes(team_name, season=CURRENT_NBA_SEASON):
    """Use current-season NBA.com player stats to estimate the active rotation by total minutes."""
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    tid = TEAM_IDS.get(team_name)
    if not tid:
        return pd.DataFrame()
    try:
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            season_type_all_star="Regular Season",
            team_id_nullable=tid,
            per_mode_detailed="Totals",
            timeout=25,
        ).get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        # Common columns: PLAYER_NAME, TEAM_ABBREVIATION, GP, MIN, PTS, REB, AST, PLAYER_ID
        cols = [c for c in ["PLAYER_NAME", "PLAYER_ID", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK"] if c in df.columns]
        out = df[cols].copy()
        out = out.rename(columns={"PLAYER_NAME":"Player", "PLAYER_ID":"PlayerID"})
        if "MIN" in out.columns:
            out["MIN_SORT"] = pd.to_numeric(out["MIN"], errors="coerce").fillna(0)
            out = out.sort_values("MIN_SORT", ascending=False)
        return out.drop_duplicates(subset=["Player"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

def current_roster_names(team_name, limit=None):
    """Current roster names from NBA API, with hard-coded profile only as backup."""
    rot = fetch_team_rotation_by_minutes(team_name)
    if not rot.empty and "Player" in rot.columns:
        names = rot["Player"].dropna().astype(str).tolist()
        return names[:limit] if limit else names
    roster = fetch_current_roster(team_name)
    if not roster.empty and "Player" in roster.columns:
        names = roster["Player"].dropna().astype(str).tolist()
        return names[:limit] if limit else names
    names = TEAM_PROFILES[team_name].get("starters", []) + TEAM_PROFILES[team_name].get("subs", [])
    return names[:limit] if limit else names

def estimated_starters_from_api(team_name):
    """Best available estimate: top 5 by current-season minutes, otherwise fallback profile starters."""
    return current_roster_names(team_name, limit=5)

def estimated_bench_from_api(team_name, start=5, end=12):
    names = current_roster_names(team_name, limit=end)
    return names[start:end] if len(names) > start else TEAM_PROFILES[team_name].get("subs", [])

@st.cache_data(ttl=3600)
def get_player_id(name):
    if not NBA_STATS_AVAILABLE: return None
    try:
        matches = [p for p in nba_players.get_players() if p["full_name"] == name]
        return matches[0]["id"] if matches else None
    except Exception: return None

@st.cache_data(ttl=86400)
def season_averages(name):
    pid = get_player_id(name)
    if not pid or not NBA_STATS_AVAILABLE: return {"PTS":"--","REB":"--","AST":"--","STL":"--","BLK":"--"}
    try:
        try:
            df = playercareerstats.PlayerCareerStats(player_id=pid, timeout=5).get_data_frames()[0]
        except TypeError:
            df = playercareerstats.PlayerCareerStats(player_id=pid).get_data_frames()[0]
        if df.empty: return {"PTS":"--","REB":"--","AST":"--","STL":"--","BLK":"--"}
        r = df.iloc[-1]; gp = max(float(r.get("GP", 1)), 1)
        return {k: round(float(r.get(k, 0)) / gp, 1) for k in ["PTS","REB","AST","STL","BLK"]}
    except Exception: return {"PTS":"--","REB":"--","AST":"--","STL":"--","BLK":"--"}

def headshot(name):
    pid = get_player_id(name)
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png" if pid else "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"

@st.cache_data(ttl=180)
def fetch_espn_injury_report(team_name):
    """Fetch current injury report from ESPN team injury page.

    nba_api does not provide a dependable injury-report endpoint, so this uses
    ESPN as the live injury source when available. If ESPN changes its page or
    blocks the request, the app falls back to a small monitor list and clearly
    labels that it is fallback data.
    """
    if not REQUESTS_AVAILABLE:
        return pd.DataFrame(), "requests package unavailable"
    slug = ESPN_INJURY_SLUGS.get(team_name)
    if not slug:
        return pd.DataFrame(), "no ESPN injury slug for team"
    url = f"https://www.espn.com/nba/team/injuries/_/name/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        html = requests.get(url, headers=headers, timeout=3).text
    except Exception as e:
        return pd.DataFrame(), f"ESPN request failed: {e}"

    # First try pandas table parsing.
    try:
        tables = pd.read_html(html)
        rows = []
        for tbl in tables:
            cols = [str(c).strip() for c in tbl.columns]
            lower = [c.lower() for c in cols]
            if not any("player" in c or "name" in c for c in lower):
                continue
            tbl.columns = cols
            for _, r in tbl.iterrows():
                player = str(r.get("PLAYER", r.get("Player", r.get("Name", "")))).strip()
                if not player or player.lower() == "nan":
                    continue
                status = str(r.get("STATUS", r.get("Status", "Monitor"))).strip()
                injury = str(r.get("INJURY", r.get("Injury", "Not specified"))).strip()
                date = str(r.get("DATE", r.get("Date", ""))).strip()
                comment = str(r.get("COMMENT", r.get("Comment", r.get("Latest Update", "")))).strip()
                rows.append({
                    "Player": player,
                    "Status": status if status and status.lower() != "nan" else "Monitor",
                    "Injury": injury if injury and injury.lower() != "nan" else "Not specified",
                    "Latest Update": comment if comment and comment.lower() != "nan" else date,
                    "Impact": injury_impact_note(player, status, injury, team_name),
                    "Source": "ESPN injury report",
                })
        if rows:
            return pd.DataFrame(rows).drop_duplicates(subset=["Player"]).reset_index(drop=True), "ESPN injury report"
    except Exception:
        pass

    # Backup parse using BeautifulSoup when tables are not readable.
    if BS4_AVAILABLE:
        try:
            soup = BeautifulSoup(html, "html.parser")
            text_blocks = [x.get_text(" ", strip=True) for x in soup.select("tbody tr")]
            rows = []
            for block in text_blocks:
                if len(block.split()) < 3:
                    continue
                # Conservative fallback: keep a readable line as the update.
                rows.append({
                    "Player": block.split("  ")[0].strip(),
                    "Status": "Monitor",
                    "Injury": "See latest update",
                    "Latest Update": block,
                    "Impact": "Check pregame availability because this could change rotation minutes.",
                    "Source": "ESPN injury report parsed text",
                })
            if rows:
                return pd.DataFrame(rows).head(10), "ESPN injury report parsed text"
        except Exception:
            pass
    return pd.DataFrame(), "No ESPN injury rows found"

def injury_impact_note(player, status, injury, team_name):
    status_l = str(status).lower()
    injury_l = str(injury).lower()
    star_names = set(TEAM_PROFILES.get(team_name, {}).get("starters", [])[:3])
    nick = fan_nick(team_name)
    if player in star_names:
        base = f"As a {nick} fan, watch {player} closely — availability swings your ceiling in this matchup."
    else:
        base = f"For {nick}, {player} matters for depth minutes and matchup flexibility."
    if "out" in status_l:
        return base + " If out, expect the rotation to tighten and another player to absorb minutes."
    if "question" in status_l or "doubt" in status_l or "game" in status_l:
        return base + " Pregame warmups and final injury report matter here."
    if "prob" in status_l or "available" in status_l:
        return base + " He is more likely to play, but workload may still matter."
    if any(x in injury_l for x in ["knee", "ankle", "hamstring", "calf", "foot"]):
        return base + " Lower-body injuries can affect defense, transition play, and late-game burst."
    return base

def get_injury_report(team_name):
    return get_injury_report_cached(str(team_name))


@st.cache_data(ttl=300)
def get_injury_report_cached(team_name: str):
    """Injury rows + fallback — cached so Home + hero strip do not hammer ESPN every rerun."""
    df, source = fetch_espn_injury_report(team_name)
    if df is not None and not df.empty:
        return df, source
    fallback = FALLBACK_INJURY_REPORT.get(team_name, [])
    if fallback:
        out = pd.DataFrame(fallback)
        out["Source"] = "Fallback monitor list — check official pregame report"
        return out, source + "; showing fallback monitor list"
    return pd.DataFrame(columns=["Player","Status","Injury","Latest Update","Impact","Source"]), source

def render_injury_report(team_name, opponent_name=None, show_page_header=True, fan_perspective_team=None, neutral_framing=False):
    if show_page_header:
        st.subheader("Injury Report / Pregame Availability")
        st.caption("Live source: ESPN injury pages when reachable. nba_api does not reliably provide official injury reports, so fallback rows are clearly labeled. Key fallback monitor rows are included when live injury data is unavailable.")
    teams = [team_name]
    if isinstance(opponent_name, (list, tuple, set)):
        for op in opponent_name:
            if op and op not in teams:
                teams.append(op)
    elif opponent_name and opponent_name not in teams:
        teams.append(opponent_name)
    for tm in teams:
        df, source = get_injury_report(tm)
        st.markdown(f"### {tm}")
        if fan_perspective_team:
            if neutral_framing:
                if tm == fan_perspective_team:
                    st.caption(f"{fan_nick(tm)} · availability before tip — rotation and minute shifts matter most here.")
                else:
                    st.caption(f"{fan_nick(tm)} · opponent availability that can tilt matchups in this series.")
            else:
                if tm == fan_perspective_team:
                    st.caption(f"Your {fan_nick(tm)} — who to monitor before you get emotionally invested at tipoff.")
                else:
                    st.caption(f"Opponent ({fan_nick(tm)}) — what could swing the matchup against your {fan_nick(fan_perspective_team)}.")
        st.caption(f"Source/status: {source} · refreshed about every 30 minutes")
        if df.empty:
            st.success("No injury rows found from the live source right now.")
            continue
        cols = st.columns(min(3, max(1, len(df))))
        for i, (_, r) in enumerate(df.iterrows()):
            with cols[i % len(cols)]:
                st.markdown("<div class='injury-card'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1:
                    try:
                        st.image(headshot(str(r.get("Player", ""))), width=72)
                    except Exception:
                        pass
                with c2:
                    st.markdown(f"**{r.get('Player','Unknown')}**")
                    st.markdown(f"<span class='injury-status'>{r.get('Status','Monitor')}</span>", unsafe_allow_html=True)
                    st.write(f"**Injury:** {r.get('Injury','Not specified')}")
                st.markdown(f"<div class='injury-note'><b>Latest:</b> {r.get('Latest Update','Check pregame report')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='injury-note'><b>Scouting impact:</b> {r.get('Impact','Could affect rotation minutes.')}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


@st.cache_data(ttl=21600)
def playoff_game_logs_for_player(name, season=CURRENT_NBA_SEASON):
    """Return current playoff game logs for selected player from NBA API."""
    pid = get_player_id(name)
    if not pid or not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    try:
        df = playergamelog.PlayerGameLog(
            player_id=pid,
            season=season,
            season_type_all_star="Playoffs",
            timeout=10,
        ).get_data_frames()[0]
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def summarize_playoff_logs(logs):
    """Create per-game playoff summary stats from NBA API game logs."""
    if logs is None or logs.empty:
        return {"GP":0,"PTS":0.0,"REB":0.0,"AST":0.0,"STL":0.0,"BLK":0.0,"TOV":0.0,"FG_PCT":0.0,"FG3_PCT":0.0,"FT_PCT":0.0,"PLUS_MINUS":0.0}
    out = {"GP": len(logs)}
    for c in ["PTS","REB","AST","STL","BLK","TOV","PLUS_MINUS"]:
        out[c] = round(pd.to_numeric(logs.get(c, pd.Series(dtype=float)), errors="coerce").fillna(0).mean(), 1)
    for c in ["FG_PCT","FG3_PCT","FT_PCT"]:
        vals = pd.to_numeric(logs.get(c, pd.Series(dtype=float)), errors="coerce").dropna()
        out[c] = round(float(vals.mean()), 3) if len(vals) else 0.0
    return out

def _name_tokens(name):
    return {tok for tok in str(name).lower().replace(".", " ").replace("-", " ").split() if len(tok) >= 3}

def _remove_self_comparisons(player_name, comps):
    """Never compare a player to himself. Also removes near matches by last/name token overlap."""
    player_tokens = _name_tokens(player_name)
    clean = []
    for comp in comps:
        comp_tokens = _name_tokens(comp)
        if str(comp).lower() == str(player_name).lower():
            continue
        # Avoid things like selected Donovan Mitchell being compared to Donovan Mitchell.
        if player_tokens and comp_tokens and player_tokens.issubset(comp_tokens):
            continue
        if comp not in clean:
            clean.append(comp)
    backup = ["Walt Frazier", "Isiah Thomas", "Dwyane Wade", "Kawhi Leonard", "Dirk Nowitzki", "Kevin Garnett", "Jimmy Butler", "Chauncey Billups", "Robert Horry", "Shane Battier"]
    for b in backup:
        if b not in clean and not (_name_tokens(player_name) and _name_tokens(player_name).issubset(_name_tokens(b))):
            clean.append(b)
        if len(clean) >= 6:
            break
    return clean[:6]


def player_resume_profile(player_name, team_name=""):
    """Narrative starting point before this playoff run: expectations, spotlight, and how far perception can move.

    ``baseline`` / ``ceiling`` still drive the fan legacy score math; copy is for humans only.
    """
    n = player_name.lower()
    team = str(team_name)
    team_nick = fan_nick(team) if team else "this team"

    profiles = {
        "lebron": {
            "baseline": 94, "ceiling": 100, "role": "all-time legend",
            "resume": "LeBron walks into the playoffs with the rarest kind of baggage: rings, Finals mileage, and a decade of being the player every broadcast centers.",
            "team_context": "For the Lakers, another title is not about inventing a story—it is about adding another late-career banner chapter people will argue about for years.",
            "comps": ["Michael Jordan", "Kareem Abdul-Jabbar", "Magic Johnson", "Larry Bird", "Kobe Bryant", "Tim Duncan"]
        },
        "brunson": {
            "baseline": 68, "ceiling": 96, "role": "lead guard",
            "resume": "Brunson is already the face of how the Knicks score in the half court: the late-clock initiator fans trust when the Garden gets loud.",
            "team_context": "A longer run cements him next to the names New York remembers at guard—Frazier, Monroe, and the modern stars who owned spring at MSG.",
            "comps": ["Walt Frazier", "Earl Monroe", "Chauncey Billups", "Damian Lillard", "Isiah Thomas", "Allen Iverson"]
        },
        "towns": {
            "baseline": 61, "ceiling": 91, "role": "scoring big",
            "resume": "Towns arrives as a proven offensive big: spacing, touch, and the ability to bend a defense without needing a gimmick.",
            "team_context": "For the Knicks, a deep push ties him to the franchise's big-man lineage; the chapter gets louder if he authors a few unmistakable playoff nights.",
            "comps": ["Patrick Ewing", "Willis Reed", "Chris Bosh", "Dirk Nowitzki", "Anthony Davis", "Pau Gasol"]
        },
        "anunoby": {
            "baseline": 50, "ceiling": 82, "role": "two-way wing",
            "resume": "OG is known for winning basketball: guarding the other team's best wing and doing the small things that show up in close games.",
            "team_context": "In New York, the story is simple—become the defender and connector fans replay when they talk about this run.",
            "comps": ["Kawhi Leonard", "Andre Iguodala", "Tayshaan Prince", "Shane Battier", "Scottie Pippen", "Bruce Bowen"]
        },
        "bridges": {
            "baseline": 48, "ceiling": 82, "role": "two-way wing",
            "resume": "Bridges brings ironman minutes, switchable defense, and the kind of reliability coaches lean on when the rotation shortens.",
            "team_context": "For the Knicks, he levels up if he is the guy taking the toughest assignment and still cashing the shots that quiet the road crowd.",
            "comps": ["Andre Iguodala", "Tayshaan Prince", "Shane Battier", "Khris Middleton", "Jimmy Butler", "Kawhi Leonard"]
        },
        "hart": {
            "baseline": 44, "ceiling": 76, "role": "winning role star",
            "resume": "Hart already feels like part of the Knicks' personality—extra possessions, noise on the glass, and the energy that travels.",
            "team_context": "His Knicks chapter grows through winning plays: rebounds that hurt, loose balls, and fourth-quarter sequences people text about.",
            "comps": ["Charles Oakley", "Anthony Mason", "Draymond Green", "Shane Battier", "Marcus Smart", "Andre Iguodala"]
        },
        "cunningham": {
            "baseline": 56, "ceiling": 95, "role": "franchise guard",
            "resume": "Cade is the hub: every possession runs through his reads, pace, and willingness to carry creation when the game tightens.",
            "team_context": "For Detroit, each extra round is a step toward the guard conversation this city cares about—Isiah, Dumars, Billups—not as a clone, but as a new chapter.",
            "comps": ["Isiah Thomas", "Joe Dumars", "Chauncey Billups", "Grant Hill", "Luka Doncic", "Shai Gilgeous-Alexander"]
        },
        "embiid": {
            "baseline": 76, "ceiling": 98, "role": "MVP center",
            "resume": "Embiid enters with MVP-level gravity: the defense bends around him, and the offense lives in the space he creates.",
            "team_context": "For Philadelphia, the open question has always been May and June—how far they go is what changes how this Embiid era gets talked about.",
            "comps": ["Moses Malone", "Hakeem Olajuwon", "Shaquille O'Neal", "Nikola Jokic", "Patrick Ewing", "David Robinson"]
        },
        "davis": {
            "baseline": 78, "ceiling": 96, "role": "championship defensive big",
            "resume": "Davis already has a ring and a body of work built on rim protection, switchability, and nights where he looks like the best two-way big on the floor.",
            "team_context": "Another Lakers deep run sharpens the simple argument: where he ranks among the great bigs of this generation.",
            "comps": ["Kevin Garnett", "David Robinson", "Hakeem Olajuwon", "Tim Duncan", "Dwight Howard", "Pau Gasol"]
        },
    }

    for key, prof in profiles.items():
        if key in n:
            return prof

    # General named stars / high baselines
    if any(x in n for x in ["mitchell", "tatum", "brown", "durant", "booker", "george", "shai", "gilgeous", "edwards", "jokic", "giannis", "luka", "doncic"]):
        return {"baseline": 66, "ceiling": 95, "role": "established star",
                "resume": f"{player_name} is one of the established stars carrying major postseason expectations—every round is a referendum on whether he can be the closer.",
                "team_context": f"For {team_nick}, the story is whether he is the reason they advance when the defense loads up and the crowd gets nervous.",
                "comps": ["Dwyane Wade", "Kevin Durant", "Kawhi Leonard", "James Harden", "Damian Lillard", "Jimmy Butler"]}
    if any(x in n for x in ["maxey", "garland", "mobley", "holmgren", "wembanyama", "reaves", "gobert"]):
        return {"baseline": 54, "ceiling": 89, "role": "high-impact core player",
                "resume": f"{player_name} is already a core piece people recognize; this postseason could be the stretch where he becomes a household playoff name.",
                "team_context": f"For {team_nick}, a breakthrough run turns him from 'important' into 'the guy we tell stories about when we talk about this spring.'",
                "comps": ["Kyrie Irving", "Klay Thompson", "Pau Gasol", "Draymond Green", "Ben Wallace", "Jrue Holiday"]}
    if any(x in n for x in ["mcbride", "robinson", "clarkson", "shamet", "alvarado", "lowry", "drummond", "sasser", "stewart", "strus", "okoro", "conley", "divincenzo", "dort", "wallace", "hartenstein"]):
        return {"baseline": 34, "ceiling": 73, "role": "rotation playoff contributor",
                "resume": f"{player_name} earns his spotlight in the margins—defense, timely shooting, rebounding, or steady minutes when stars sit.",
                "team_context": f"For {team_nick}, he becomes part of the lore if fans can point to a series and say, 'We don't get there without him.'",
                "comps": ["Robert Horry", "Shane Battier", "Derek Fisher", "Bruce Bowen", "Steve Kerr", "Andre Iguodala"]}
    return {"baseline": 40, "ceiling": 78, "role": "playoff contributor",
            "resume": f"{player_name} walks in without a long playoff track record yet—this run is a chance to attach his name to winning moments.",
            "team_context": f"For {team_nick}, it matters if his best nights line up with the games that swing the series.",
            "comps": ["Robert Horry", "Andre Iguodala", "Chauncey Billups", "Jimmy Butler", "Kyle Lowry", "Shane Battier"]}

def player_legacy_archetype(player_name):
    prof = player_resume_profile(player_name)
    return prof["role"], _remove_self_comparisons(player_name, prof["comps"])

def player_legacy_ceiling(player_name, team_name=""):
    return player_resume_profile(player_name, team_name)["ceiling"]

def player_legacy_floor(player_name):
    return player_resume_profile(player_name)["baseline"]

def player_specific_tier(score, player_name, team_name=""):
    prof = player_resume_profile(player_name, team_name)
    baseline = prof["baseline"]
    ceiling = prof["ceiling"]
    span = max(1, ceiling - baseline)
    pct = (score - baseline) / span
    if pct >= 0.88:
        return f"{player_name} would land in rare national-storyline territory at this line"
    if pct >= 0.68:
        return f"{player_name} would look like he authored a defining spring at this line"
    if pct >= 0.45:
        return f"{player_name} would clearly move the needle in how fans describe the run"
    if pct >= 0.22:
        return f"{player_name} would nudge perception—solid, but not a full narrative rewrite yet"
    return f"{player_name} would mostly look like the player people already expected"

def legacy_score_from_inputs(
    pts,
    reb,
    ast,
    stl,
    blk,
    fg,
    three,
    plus_minus,
    rounds_won,
    title_won=False,
    player_name="",
    team_name="",
    clutch_momentum=0.0,
    turnover_trend=0.0,
    bench_support=0.0,
):
    prof = player_resume_profile(player_name, team_name)
    baseline = prof["baseline"]
    ceiling = prof["ceiling"]
    # Fan-model score: career baseline plus this playoff stat blend (internal weights only).
    scoring = pts * 0.42
    all_around = reb * 0.22 + ast * 0.30 + stl * 0.70 + blk * 0.55
    efficiency = max(0, (fg - 0.43) * 24) + max(0, (three - 0.34) * 10)
    impact = plus_minus * 0.22
    winning = rounds_won * 4.2 + (7.0 if title_won else 0)
    fan_intangibles = clutch_momentum * 0.7 + bench_support * 0.55 + turnover_trend * 0.45
    raw = baseline + scoring + all_around + efficiency + impact + winning + fan_intangibles
    return round(max(0, min(ceiling, raw)), 1)

def legacy_tier(score):
    # Kept for compatibility; UI uses player_specific_tier().
    if score >= 92:
        return "inner-circle postseason talk"
    if score >= 82:
        return "defining-spring territory"
    if score >= 72:
        return "clear needle-mover"
    if score >= 60:
        return "meaningful buzz"
    if score >= 48:
        return "quiet shift"
    return "little movement in the story"

def _scenario_meaning(player, team, score, _scenario_label, rounds, title):
    prof = player_resume_profile(player, team)
    comps = _remove_self_comparisons(player, prof["comps"])
    tier = player_specific_tier(score, player, team)
    nick = fan_nick(team)
    if title:
        team_hist = (
            f"A title for {nick} would hang {player}'s line next to the franchise's biggest banners—think the gravity of names like {comps[0]} and {comps[1]}, not as a clone, but as the neighborhood of pressure."
        )
        nba_hist = f"League-wide, a ring writes a championship chapter people do not forget. {tier}"
    elif rounds >= 3:
        team_hist = f"A Finals trip would make this one of the {nick} seasons people still reference—especially if {player} keeps producing at this clip."
        nba_hist = (
            f"Around the league, people start mentioning players like {comps[1]} and {comps[2]} when they describe the kind of impact he carried—not a perfect comp, but the shape of the role."
        )
    elif rounds >= 2:
        team_hist = f"Conference finals basketball would stamp {player} as a central figure in this {nick} chapter, not just a good regular-season story."
        nba_hist = f"The bar-talk comps drift toward names like {comps[2]} and {comps[3]}: guys who mattered when the possessions got ugly."
    elif rounds >= 1:
        team_hist = f"Winning this round ties {player}'s numbers to a series people will actually remember when they talk about {nick} in May."
        nba_hist = f"League-wide, the leap is still mostly about team advancement—unless he keeps a loud enough line to invite {comps[3]}- or {comps[4]}-type comparisons in role."
    else:
        team_hist = prof["team_context"]
        nba_hist = prof["resume"]
    return team_hist, nba_hist

def _legacy_path_label(target_series_wins, base_series_wins, title_won):
    """Human label for a row in the active-team legacy ladder (series wins = playoff rounds won)."""
    if title_won:
        return "If they win the NBA championship (four series wins)"
    if target_series_wins == base_series_wins:
        if base_series_wins == 0:
            return "Projected from sliders — no series wins on the board yet"
        if base_series_wins == 1:
            return "Projected from sliders — one series win already banked"
        if base_series_wins == 2:
            return "Projected from sliders — two series wins (Conference Finals territory)"
        if base_series_wins == 3:
            return "Projected from sliders — three series wins (NBA Finals)"
        return f"Projected from sliders — {base_series_wins} series wins on the board"
    if target_series_wins == 1:
        return "If they reach one series win this postseason"
    if target_series_wins == 2:
        return "If they reach two series wins (Conference Finals path)"
    if target_series_wins == 3:
        return "If they reach three series wins (NBA Finals path)"
    return f"If they reach {target_series_wins} series wins"


def build_legacy_path(
    player,
    team,
    pts,
    reb,
    ast,
    stl,
    blk,
    fg,
    three,
    plus_minus,
    base_series_wins=0,
    clutch_momentum=0.0,
    turnover_trend=0.0,
    bench_support=0.0,
):
    """Ladder of legacy scores from the team's current series-win count through a title.

    ``base_series_wins`` should match the merged bracket (what is already clinched).
    """
    base_series_wins = max(0, min(4, int(base_series_wins)))
    if base_series_wins >= 4:
        sc = legacy_score_from_inputs(
            pts,
            reb,
            ast,
            stl,
            blk,
            fg,
            three,
            plus_minus,
            4,
            True,
            player,
            team,
            clutch_momentum,
            turnover_trend,
            bench_support,
        )
        tier = player_specific_tier(sc, player, team)
        team_hist, nba_hist = _scenario_meaning(player, team, sc, "champions", 4, True)
        return pd.DataFrame(
            [
                {
                    "Playoff picture": "Championship already clinched — legacy at the banner moment",
                    "Legacy score": sc,
                    "Fan read": tier,
                    "Franchise angle": team_hist,
                    "League-wide read": nba_hist,
                }
            ]
        )
    rows = []
    for tw in range(base_series_wins, 4):
        label = _legacy_path_label(tw, base_series_wins, False)
        sc = legacy_score_from_inputs(
            pts,
            reb,
            ast,
            stl,
            blk,
            fg,
            three,
            plus_minus,
            tw,
            False,
            player,
            team,
            clutch_momentum,
            turnover_trend,
            bench_support,
        )
        tier = player_specific_tier(sc, player, team)
        team_hist, nba_hist = _scenario_meaning(player, team, sc, label, tw, False)
        rows.append(
            {
                "Playoff picture": label,
                "Legacy score": sc,
                "Fan read": tier,
                "Franchise angle": team_hist,
                "League-wide read": nba_hist,
            }
        )
    if base_series_wins < 4:
        tw = 4
        label = _legacy_path_label(tw, base_series_wins, True)
        sc = legacy_score_from_inputs(
            pts,
            reb,
            ast,
            stl,
            blk,
            fg,
            three,
            plus_minus,
            tw,
            True,
            player,
            team,
            clutch_momentum,
            turnover_trend,
            bench_support,
        )
        tier = player_specific_tier(sc, player, team)
        team_hist, nba_hist = _scenario_meaning(player, team, sc, label, tw, True)
        rows.append(
            {
                "Playoff picture": label,
                "Legacy score": sc,
                "Fan read": tier,
                "Franchise angle": team_hist,
                "League-wide read": nba_hist,
            }
        )
    return pd.DataFrame(rows)


def legacy_takeaways(
    player,
    team,
    pts,
    reb,
    ast,
    stl,
    blk,
    fg,
    three,
    plus_minus,
    base_series_wins=0,
    clutch_momentum=0.0,
    turnover_trend=0.0,
    bench_support=0.0,
):
    prof = player_resume_profile(player, team)
    _, comps = player_legacy_archetype(player)
    base_series_wins = max(0, min(4, int(base_series_wins)))
    base = legacy_score_from_inputs(
        pts,
        reb,
        ast,
        stl,
        blk,
        fg,
        three,
        plus_minus,
        base_series_wins,
        False,
        player,
        team,
        clutch_momentum,
        turnover_trend,
        bench_support,
    )
    title = legacy_score_from_inputs(
        pts,
        reb,
        ast,
        stl,
        blk,
        fg,
        three,
        plus_minus,
        4,
        True,
        player,
        team,
        clutch_momentum,
        turnover_trend,
        bench_support,
    )
    nick = fan_nick(team)
    return [
        f"Through {nick}: {prof['resume']}",
        f"Current legacy impact is **locked through whatever the bracket already says** ({base_series_wins} series win(s) on record); the ladder below is only about what still can change.",
        f"What this run could mean for the franchise story: {prof['team_context']}",
        f"If you need a mental picture, think of players like {', '.join(comps[:4])} — different careers, but the kind of names that come up in the same conversations.",
        f"With these sliders, {player} moves from **{player_specific_tier(base, player, team)}** at today's win total to **{player_specific_tier(title, player, team)}** if {nick} raise a banner. That is the fan forecast arc — not a prediction.",
    ]


def _best_worst_playoff_game_rows(logs):
    """Return (best_row, worst_row) Series by PTS from chronological playoff logs."""
    prep = _prepare_chrono_playoff_logs(logs)
    if prep is None or prep.empty or "PTS" not in prep.columns:
        return None, None
    pts = pd.to_numeric(prep["PTS"], errors="coerce")
    if pts.dropna().empty:
        return None, None
    try:
        i_hi = int(pts.idxmax())
        i_lo = int(pts.idxmin())
        return prep.loc[i_hi], prep.loc[i_lo]
    except Exception:
        return None, None


def _legacy_round_by_round_summary(logs, team_tri):
    """Per-series playoff splits in postseason order (First Round chunk, then Second, …)."""
    df = _prepare_chrono_playoff_logs(logs)
    if df is None or df.empty:
        return []
    team_tri = (team_tri or "").upper()
    chunks = _series_chunks_playoff_order(df, team_tri)
    rnd_names = ["First Round", "Second Round", "Conference Finals", "NBA Finals"]
    out = []
    for i, (opp_tri, seg) in enumerate(chunks):
        lab = rnd_names[i] if i < len(rnd_names) else f"Round {i + 1}"
        sm = summarize_playoff_logs(seg)
        opp_full = ALIAS_TO_TEAM.get(opp_tri, opp_tri or "—")
        out.append(
            {
                "Round": lab,
                "Opponent": opp_full,
                "GP": sm.get("GP", 0),
                "PTS": sm.get("PTS", 0),
                "REB": sm.get("REB", 0),
                "AST": sm.get("AST", 0),
                "STL": sm.get("STL", 0),
                "BLK": sm.get("BLK", 0),
                "TOV": sm.get("TOV", 0),
                "FG_PCT": sm.get("FG_PCT", 0),
                "FG3_PCT": sm.get("FG3_PCT", 0),
                "FT_PCT": sm.get("FT_PCT", 0),
                "PLUS_MINUS": sm.get("PLUS_MINUS", 0),
            }
        )
    return out


def legacy_takeaways_eliminated(player, team_name, pts, reb, ast, stl, blk, fg, three, plus_minus, exit_line):
    """Narrative bullets for completed runs — no hypothetical Finals arc."""
    prof = player_resume_profile(player, team_name)
    _, comps = player_legacy_archetype(player)
    nick = fan_nick(team_name)
    sw = _count_series_wins_for_team(team_name)
    final = legacy_score_from_inputs(pts, reb, ast, stl, blk, fg, three, plus_minus, sw, False, player, team_name)
    tier = player_specific_tier(final, player, team_name)
    team_hist, nba_hist = _scenario_meaning(player, team_name, final, "complete", sw, False)
    comps_txt = ", ".join(comps[:4])
    return [
        f"This playoff run is **complete** for {nick}. **{player}** is judged here only through the actual exit: **{exit_line}** — not through fantasy Conference Finals or Finals sliders.",
        f"**Final legacy score (fan model, actual games only):** {final} · {tier}",
        f"**What the tape-backed line suggests:** {prof['resume']}",
        f"**Franchise read (based on how far they really got):** {team_hist}",
        f"**League-wide read (no future rounds invented):** {nba_hist}",
        f"**What the run did or did not prove:** if the best nights lined up with swing games, fans will remember it; if not, the summer narrative becomes about health, fit, and whether the role expanded when the defense loaded up.",
        f"**Offseason / future implications:** contract years, injury management, and whether {nick} need a cleaner secondary creator often decide how this chapter ages — not one more hypothetical Finals game log.",
        f"**Historical neighborhood (from what actually happened):** mental comps drift toward names like {comps_txt} — imperfect mirrors, but the shape of the role and pressure.",
    ]


def render_legacy_tracker_page(team_name):
    """Legacy Tracker: frozen postmortem for eliminated teams; live forecast + sliders for active teams."""
    render_matchup_header(team_name)
    nick = fan_nick(team_name)
    is_elim = _is_home_eliminated(team_name)
    team_tri = (TEAM_ALIASES.get(team_name) or "").upper()
    series_wins_bracket = _count_series_wins_for_team(team_name)

    if is_elim:
        st.subheader(f"Legacy Tracker · {nick} — completed playoff postmortem")
        try:
            exit_line = _elimination_exit_line(team_name)
        except Exception:
            exit_line = TEAM_PROFILES.get(team_name, {}).get("first_round_result") or "Playoff exit"
        render_mode_banner(
            team_name,
            "COMPLETED RUN · NO FUTURE-ROUND SIMULATIONS",
            f"<b>{html.escape(team_name)}</b> is out of the title chase as the bracket currently reads "
            f"(<b>{html.escape(exit_line)}</b>). Legacy here is a <b>postmortem</b> only: actual box scores through the exit, "
            "round-by-round splits, best/worst nights, and a final interpretation — "
            "<b>no</b> Conference Finals or NBA Finals projections and <b>no</b> championship sliders.",
            variant="postmortem",
        )
    else:
        st.subheader(f"Legacy Tracker · {nick} — live forecast (future outcomes can still change the story)")
        render_mode_banner(
            team_name,
            "LIVE FORECAST MODE",
            f"<b>Section A</b> locks <b>current legacy impact</b> to real playoff logs plus "
            f"<b>{series_wins_bracket}</b> series win(s) already on the bracket. "
            f"<b>Section B</b> is a <b>fan simulator</b>: move sliders to stress-test scoring, efficiency, "
            f"defense feel, clutch, turnovers, and bench lift — then read the ladder for what happens if "
            f"{html.escape(nick)} keep climbing.",
            variant="live",
        )

    player_pool = current_roster_names(team_name, limit=15)
    player = st.selectbox("Choose player", player_pool)
    logs = playoff_game_logs_for_player(player)
    current = summarize_playoff_logs(logs)

    if logs is None or logs.empty:
        st.warning(
            "NBA API did not return current playoff game logs for this player. "
            "Eliminated postmortems still work from safe averages; active-team sliders default to reasonable baselines."
        )
    else:
        st.success(f"Loaded {current['GP']} current playoff games for {player} from NBA API.")
        show_cols = [
            c
            for c in [
                "GAME_DATE",
                "MATCHUP",
                "WL",
                "MIN",
                "PTS",
                "REB",
                "AST",
                "STL",
                "BLK",
                "TOV",
                "FG_PCT",
                "FG3_PCT",
                "FT_PCT",
                "PLUS_MINUS",
            ]
            if c in logs.columns
        ]
        render_fan_stat_table(logs[show_cols], team_name)

    pts0 = float(current.get("PTS", 20.0) or 20.0)
    reb0 = float(current.get("REB", 6.0) or 6.0)
    ast0 = float(current.get("AST", 4.0) or 4.0)
    stl0 = float(current.get("STL", 1.0) or 1.0)
    blk0 = float(current.get("BLK", 0.5) or 0.5)
    pm0 = float(current.get("PLUS_MINUS", 0.0) or 0.0)
    fg0 = float(current.get("FG_PCT", 0.460) or 0.460)
    th0 = float(current.get("FG3_PCT", 0.360) or 0.360)

    if is_elim:
        pts, reb, ast, stl, blk = pts0, reb0, ast0, stl0, blk0
        fg, three, plus_minus = fg0, th0, pm0
        final_score = legacy_score_from_inputs(
            pts, reb, ast, stl, blk, fg, three, plus_minus, series_wins_bracket, False, player, team_name
        )

        st.markdown("### 1 · Final playoff stat summary (actual games)")
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        m1.metric("Games", current.get("GP", 0))
        m2.metric("PTS", current.get("PTS", 0))
        m3.metric("REB", current.get("REB", 0))
        m4.metric("AST", current.get("AST", 0))
        m5.metric("STL", current.get("STL", 0))
        m6.metric("BLK", current.get("BLK", 0))
        m7.metric("TOV", current.get("TOV", 0))
        c8, c9, c10 = st.columns(3)
        c8.metric("FG%", current.get("FG_PCT", 0))
        c9.metric("3PT%", current.get("FG3_PCT", 0))
        c10.metric("FT%", current.get("FT_PCT", 0))
        st.metric(
            "Final legacy score (fan model · actual exit)",
            f"{final_score}",
            help=f"Uses {series_wins_bracket} series win(s) on the bracket and this postseason stat line — no invented future rounds.",
        )

        st.markdown("### 2 · Round-by-round actual performance")
        rr = _legacy_round_by_round_summary(logs, team_tri)
        if rr:
            render_fan_stat_table(pd.DataFrame(rr), team_name)
        else:
            st.caption("Series splits need matchup rows in the game log — showing full-run averages only above.")

        st.markdown("### 3 · Best game / worst game (by points)")
        best_r, worst_r = _best_worst_playoff_game_rows(logs)
        b1, b2 = st.columns(2)
        with b1:
            if best_r is not None:
                st.markdown(
                    f"**Best night:** {safe_float(best_r.get('PTS')):.0f} PTS vs {_matchup_opponent_tri(best_r.get('MATCHUP'), team_tri)} "
                    f"({html.escape(str(best_r.get('GAME_DATE', '')))})"
                )
            else:
                st.caption("No best game row available.")
        with b2:
            if worst_r is not None:
                st.markdown(
                    f"**Tough night:** {safe_float(worst_r.get('PTS')):.0f} PTS vs {_matchup_opponent_tri(worst_r.get('MATCHUP'), team_tri)} "
                    f"({html.escape(str(worst_r.get('GAME_DATE', '')))})"
                )
            else:
                st.caption("No worst game row available.")

        st.markdown("### 4 · Final legacy interpretation")
        st.caption(exit_line)
        st.plotly_chart(
            px.bar(
                pd.DataFrame(
                    [
                        {
                            "What is locked": f"Actual exit after {series_wins_bracket} series win(s)",
                            "Legacy score": final_score,
                            "Mode": "Postmortem (no future ladder)",
                        }
                    ]
                ),
                x="What is locked",
                y="Legacy score",
                color="Mode",
                title=f"{player}: legacy frozen at real elimination point",
            ),
            use_container_width=True,
        )
        elim_lines = legacy_takeaways_eliminated(
            player, team_name, pts, reb, ast, stl, blk, fg, three, plus_minus, exit_line
        )
        st.markdown("**Narrative read (no future rounds)**")
        for line in elim_lines[:5]:
            st.write(f"• {line}")
        st.markdown("### 5 · What the playoff run did or did not prove")
        st.write(f"• {elim_lines[5]}")
        st.markdown("### 6 · Offseason / future implications for this player")
        st.write(f"• {elim_lines[6]}")
        st.markdown("### 7 · Historical / franchise comparison (actual outcomes only)")
        st.write(f"• {elim_lines[7]}")

        st.info(
            "Fan toy, not an official ranking. Eliminated mode **never** blends hypothetical Finals numbers — "
            "only games played and bracket wins before the exit."
        )
        return

    # ----- Active team: locked actuals + forward simulator -----
    locked_score = legacy_score_from_inputs(
        pts0, reb0, ast0, stl0, blk0, fg0, th0, pm0, series_wins_bracket, False, player, team_name
    )

    if series_wins_bracket >= 4:
        crown_score = legacy_score_from_inputs(
            pts0, reb0, ast0, stl0, blk0, fg0, th0, pm0, 4, True, player, team_name
        )
        st.markdown("### Champion snapshot — no forward ladder needed")
        st.success(
            f"The bracket already shows **four** series wins for **{team_name}**. Legacy here is about how the crowning run *looked*, not what might happen next."
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Games (playoffs)", current.get("GP", 0))
        m2.metric("PTS", current.get("PTS", 0))
        m3.metric("Legacy score (title run)", crown_score)
        m4.metric("Ceiling (fan model)", player_legacy_ceiling(player, team_name))
        st.info(
            "There is nothing left to simulate on the bracket path — use **Player Playoff Tracker** for game-by-game story, "
            "or pick an eliminated team to see the postmortem layout."
        )
        return

    st.markdown("### A · Locked — current legacy impact (real logs + bracket)")
    st.caption(
        f"Bracket shows **{series_wins_bracket}** series win(s) so far for {team_name}. "
        "These averages and the score below do not use the simulator sliders."
    )
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Games", current.get("GP", 0))
    m2.metric("PTS", current.get("PTS", 0))
    m3.metric("REB", current.get("REB", 0))
    m4.metric("AST", current.get("AST", 0))
    m5.metric("STL", current.get("STL", 0))
    m6.metric("BLK", current.get("BLK", 0))
    a1, a2, a3 = st.columns(3)
    a1.metric("Legacy score (locked)", f"{locked_score}")
    a2.metric("Ceiling (fan model)", player_legacy_ceiling(player, team_name))
    a3.metric("Room to title ceiling", round(float(player_legacy_ceiling(player, team_name)) - locked_score, 1))

    st.markdown("### B · Fan simulator (stat line + intangibles · ladder from today forward)")
    with st.container(border=True):
        st.caption(
            f"Sliders default to this player’s **actual playoff averages**. Move them to stress-test scoring, efficiency, defense feel, "
            f"clutch nights, turnover trend, and bench rescue — the ladder uses **{series_wins_bracket}** series win(s) as the floor, then adds hypothetical rounds."
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            pts = st.slider("Scoring (PPG)", 0.0, 45.0, pts0, 0.5)
            reb = st.slider("Rebounding (RPG)", 0.0, 20.0, reb0, 0.5)
            ast = st.slider("Playmaking (APG)", 0.0, 15.0, ast0, 0.5)
        with c2:
            stl = st.slider("Defense activity — steals per game", 0.0, 4.0, stl0, 0.1)
            blk = st.slider("Defense activity — blocks per game", 0.0, 5.0, blk0, 0.1)
            plus_minus = st.slider("Efficiency / impact proxy — avg plus-minus", -20.0, 20.0, pm0, 0.5)
        with c3:
            fg = st.slider("Shooting efficiency — FG%", 0.300, 0.700, fg0, 0.005)
            three = st.slider("Shooting efficiency — 3PT%", 0.200, 0.550, th0, 0.005)
        d1, d2, d3 = st.columns(3)
        with d1:
            clutch_momentum = st.slider(
                "Clutch / late-game lift (narrative tilt)",
                -5.0,
                5.0,
                0.0,
                0.5,
                help="Positive if you think the player is winning closing minutes beyond the box; negative if crunch-time fades show up.",
            )
        with d2:
            turnover_trend = st.slider(
                "Ball security vs turnovers",
                -5.0,
                5.0,
                0.0,
                0.5,
                help="Positive if you expect cleaner possessions; negative if live-ball turnovers spike.",
            )
        with d3:
            bench_support = st.slider(
                "Bench / role-player rescue around this player",
                -5.0,
                5.0,
                0.0,
                0.5,
                help="Positive if supporting cast lifts pressure off the star; negative if the rotation thins when it matters.",
            )

    path = build_legacy_path(
        player,
        team_name,
        pts,
        reb,
        ast,
        stl,
        blk,
        fg,
        three,
        plus_minus,
        base_series_wins=series_wins_bracket,
        clutch_momentum=clutch_momentum,
        turnover_trend=turnover_trend,
        bench_support=bench_support,
    )
    sim_now = float(path.iloc[0]["Legacy score"]) if not path.empty else locked_score
    title_score = float(path.iloc[-1]["Legacy score"]) if not path.empty else locked_score

    x1, x2, x3, x4 = st.columns(4)
    x1.metric("Simulator · first rung", sim_now)
    x2.metric("If they win the title (model)", title_score)
    x3.metric("Delta to banner outcome", round(title_score - sim_now, 1))
    x4.metric("Ceiling (fan model)", player_legacy_ceiling(player, team_name))

    st.plotly_chart(
        px.bar(
            path,
            x="Playoff picture",
            y="Legacy score",
            color="Fan read",
            title=f"{player}: ladder from today’s bracket position (not a prediction)",
        ),
        use_container_width=True,
    )
    st.dataframe(path, use_container_width=True)

    st.markdown("### Interpretation")
    for line in legacy_takeaways(
        player,
        team_name,
        pts,
        reb,
        ast,
        stl,
        blk,
        fg,
        three,
        plus_minus,
        base_series_wins=series_wins_bracket,
        clutch_momentum=clutch_momentum,
        turnover_trend=turnover_trend,
        bench_support=bench_support,
    ):
        st.write(f"• {line}")

    st.info(
        "Fan toy, not an official ranking. **Section A** is actual playoff logs plus bracket wins; **Section B** layers hypotheticals. "
        "Real legacy still lives in signature games, matchups, health, and hardware."
    )


# --- Player Playoff Story Hub (narrative + impact layer on raw logs) ---

def _prior_nba_season_label(season_str):
    """'2025-26' -> '2024-25' for YoY playoff comparison."""
    try:
        parts = str(season_str).strip().split("-")
        if len(parts) != 2:
            return None
        y_start = int(parts[0])
        tail = parts[1].strip()
        if len(tail) == 2:
            y_end = int(str(y_start)[:2] + tail)
        else:
            y_end = int(tail)
        return f"{y_start - 1}-{str(y_end - 1)[-2:]}"
    except Exception:
        return None


def _round_narrative_weight(round_name):
    r = (round_name or "").lower()
    if "final" in r and "conference" not in r:
        return 38
    if "conference" in r:
        return 28
    if "second" in r:
        return 16
    if "first" in r:
        return 8
    return 12


@st.cache_data(ttl=1800)
def _cached_playoff_gamelog(player_id, season):
    if not NBA_STATS_AVAILABLE or not player_id:
        return pd.DataFrame()
    try:
        return playergamelog.PlayerGameLog(
            player_id=int(player_id),
            season=season,
            season_type_all_star="Playoffs",
            timeout=25,
        ).get_data_frames()[0]
    except Exception:
        return pd.DataFrame()


def _prepare_chrono_playoff_logs(logs):
    """Normalize playoff logs to strict chronological order: oldest game first.

    nba_api often returns newest-first; ambiguous dates are tie-broken with GAME_ID
    so Series 1 == first postseason series and timeline reversals stay consistent.
    """
    if logs is None or logs.empty:
        return pd.DataFrame()
    df = logs.copy()
    if "GAME_DATE" in df.columns:
        try:
            df["_dt"] = pd.to_datetime(df["GAME_DATE"], errors="coerce", format="mixed")
        except Exception:
            df["_dt"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
    else:
        df["_dt"] = pd.NaT

    if "GAME_ID" in df.columns:
        df["_gid_sort"] = df["GAME_ID"].astype(str)
    else:
        df["_gid_sort"] = ""

    has_dt = bool(df["_dt"].notna().any()) if "_dt" in df.columns else False
    has_gid = "_gid_sort" in df.columns and df["_gid_sort"].astype(str).str.len().gt(0).any()
    if has_dt and has_gid:
        df = df.sort_values(["_dt", "_gid_sort"], ascending=[True, True], na_position="last", kind="mergesort")
    elif has_dt:
        df = df.sort_values("_dt", ascending=True, na_position="last", kind="mergesort")
    elif has_gid:
        df = df.sort_values("_gid_sort", ascending=True, kind="mergesort")
    else:
        df = df.iloc[::-1].reset_index(drop=True)

    for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "MIN", "PLUS_MINUS", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "OREB", "DREB"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["FG_PCT", "FG3_PCT", "FT_PCT"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.reset_index(drop=True)


def _matchup_opponent_tri(matchup, team_tri):
    tris = re.findall(r"\b[A-Z]{3}\b", str(matchup or "").upper())
    team_tri = (team_tri or "").upper()
    if team_tri and tris:
        for t in tris:
            if t != team_tri:
                return t
    if len(tris) >= 2:
        return tris[1]
    return tris[0] if tris else "—"


def _series_chunks_chrono(df, team_tri):
    """Split into contiguous series by opponent. df must be oldest-game-first."""
    if df.empty:
        return []
    team_tri = (team_tri or "").upper()
    out = []
    cur_opp = None
    start = 0
    n = len(df)
    for pos in range(n):
        row = df.iloc[pos]
        opp = _matchup_opponent_tri(row.get("MATCHUP"), team_tri)
        if cur_opp is None:
            cur_opp = opp
        elif opp != cur_opp:
            out.append((cur_opp, df.iloc[start:pos].copy()))
            cur_opp = opp
            start = pos
    out.append((cur_opp, df.iloc[start:n].copy()))
    return out


def _series_chunks_playoff_order(df, team_tri):
    """Series 1 = earliest postseason series, then Series 2, … (by first game in each chunk)."""
    chunks = _series_chunks_chrono(df, team_tri)
    if len(chunks) <= 1:
        return chunks

    def _chunk_start_key(item):
        _, seg = item
        if seg is None or seg.empty:
            return (pd.Timestamp.max, "z")
        s = seg
        if "_dt" in s.columns and s["_dt"].notna().any():
            s2 = s.sort_values(["_dt", "_gid_sort"] if "_gid_sort" in s.columns else ["_dt"], ascending=[True, True], na_position="last", kind="mergesort")
            r0 = s2.iloc[0]
            ts = r0["_dt"]
            gid = str(r0.get("_gid_sort", r0.get("GAME_ID", "")))
            return (ts, gid)
        if "_gid_sort" in s.columns:
            return (pd.Timestamp.max, str(s["_gid_sort"].astype(str).min()))
        if "GAME_ID" in s.columns:
            return (pd.Timestamp.max, str(s["GAME_ID"].astype(str).min()))
        return (pd.Timestamp.max, "z")

    return sorted(chunks, key=_chunk_start_key)


def _df_newest_first_for_display(df):
    """Rows for fan-facing feeds: latest game first (newest developments on top)."""
    if df is None or df.empty:
        return df
    if "_dt" in df.columns and df["_dt"].notna().any():
        cols = ["_dt"]
        asc = [False]
        if "_gid_sort" in df.columns:
            cols.append("_gid_sort")
            asc.append(False)
        return df.sort_values(cols, ascending=asc, na_position="last", kind="mergesort").reset_index(drop=True)
    if "_gid_sort" in df.columns and df["_gid_sort"].astype(str).str.len().gt(0).any():
        return df.sort_values("_gid_sort", ascending=False, kind="mergesort").reset_index(drop=True)
    return df.iloc[::-1].reset_index(drop=True)


def _true_shooting_pct(df):
    """League-style TS% from game log totals (not poss-adjusted)."""
    if df.empty:
        return None
    pts = df["PTS"].sum() if "PTS" in df.columns else 0
    fga = df["FGA"].sum() if "FGA" in df.columns else 0
    fta = df["FTA"].sum() if "FTA" in df.columns else 0
    denom = 2 * (fga + 0.44 * fta)
    if denom <= 0:
        if "FG_PCT" in df.columns and "PTS" in df.columns:
            return float(df["FG_PCT"].mean()) * 0.55 + 0.25
        return None
    return float(pts / denom)


def _game_impact_score(row):
    pts = safe_float(row.get("PTS"))
    stl = safe_float(row.get("STL"))
    blk = safe_float(row.get("BLK"))
    pm = safe_float(row.get("PLUS_MINUS"))
    reb = safe_float(row.get("REB"))
    ast = safe_float(row.get("AST"))
    return pts + 0.45 * reb + 0.55 * ast + 2.1 * stl + 2.0 * blk + 0.35 * pm


def _consistency_rating(pts_series):
    pts_series = pd.to_numeric(pts_series, errors="coerce").dropna()
    if len(pts_series) < 2:
        return None, "Not enough games yet for a volatility read."
    mu = float(pts_series.mean())
    if mu <= 0.5:
        return None, "Scoring load is too thin to grade consistency."
    cv = float(pts_series.std(ddof=0) / mu)
    score = int(round(max(0, min(100, 100 * (1 - min(cv, 1.2) / 1.2)))))
    if score >= 78:
        tag = "High — night-to-night variance is low relative to scoring volume."
    elif score >= 55:
        tag = "Solid — some swing games, but nothing wildly erratic."
    else:
        tag = "Volatile — the stat line is spiky game to game (common for high-usage creators and shooters on tight windows)."
    return score, tag


def _momentum_reading(df):
    if df.empty or "PTS" not in df.columns or len(df) < 3:
        return "Early sample — momentum reads stabilize after a few games."
    y = df["PTS"].astype(float).values
    x = np.arange(1, len(y) + 1, dtype=float)
    slope = float(np.polyfit(x, y, 1)[0])
    early = float(y[: max(1, len(y) // 3)].mean())
    late = float(y[-max(1, len(y) // 3) :].mean())
    if slope > 1.25 and late > early + 2:
        return f"Sharpening — scoring is trending up across the run (roughly +{slope:.1f} PPG per game played vs a flat line)."
    if slope < -1.1 and late < early - 2:
        return f"Cooling — defenses are squeezing looks or the shot diet is shifting (trend ~{slope:.1f} PPG per game vs a flat line)."
    return "Steady — production is landing in a tight band without a clear drift."


def _bounce_back_games(df):
    if df.empty or "WL" not in df.columns:
        return 0
    w = df["WL"].astype(str).tolist()
    n = 0
    for i in range(1, len(w)):
        if w[i - 1].upper().startswith("L") and w[i].upper().startswith("W"):
            n += 1
    return n


def _pp_hub_pressure_legacy_narratives(
    team_name,
    player,
    seed,
    rnd,
    status,
    opp,
    pressure_base,
    rep,
    stakes,
    elim_pressure,
    cur_summary,
    df,
    prof,
):
    """Plain-language copy for Player Playoff Hub · section 3 (pressure, stakes, perception, legacy)."""
    nick = fan_nick(team_name)
    last = player.rsplit(" ", 1)[-1] if player else "They"
    rnd_disp = rnd or "the playoffs"
    rl = (rnd or "").lower()
    pts = float(cur_summary.get("PTS") or 0)
    pm = safe_float(cur_summary.get("PLUS_MINUS"))
    gp = int(cur_summary.get("GP") or (len(df) if df is not None else 0))
    bounces = _bounce_back_games(df) if df is not None else 0
    has_loss = False
    if df is not None and not df.empty and "WL" in df.columns:
        has_loss = any(str(x).upper().startswith("L") for x in df["WL"].astype(str).tolist())

    v_p = max(0, min(100, int(pressure_base)))
    if v_p >= 82:
        heat = "Pressure is extremely high right now"
    elif v_p >= 68:
        heat = "Pressure is very high"
    elif v_p >= 52:
        heat = "Pressure is real and rising"
    elif v_p >= 38:
        heat = "There is steady playoff heat on this group"
    else:
        heat = "The emotional temperature is a notch lower than a headline series, but the games still matter"

    seed_bits = []
    if seed <= 2:
        seed_bits.append(
            f"{nick} entered the postseason with real title-or-deep-run expectations—every loss gets picked apart on national TV"
        )
    elif seed <= 4:
        seed_bits.append(
            f"as a top-four seed, {nick} are supposed to look like a threat, not just happy to be here"
        )
    else:
        seed_bits.append(
            f"from the {seed} seed, {nick} are often written off early—until they win, then the spotlight flips overnight"
        )

    if "nba final" in rl or ("final" in rl and "conference" not in rl):
        seed_bits.append(
            "the Finals shrink the story to a handful of stars and moments everyone replays for years"
        )
    elif "conference" in rl and "final" in rl:
        seed_bits.append(
            "conference finals basketball is where reputations get stamped—win or lose, people remember who showed"
        )
    elif "second" in rl:
        seed_bits.append(
            "the second round is where matchups, scouting, and shot quality separate good teams from great ones"
        )
    else:
        seed_bits.append(
            "even early rounds swing fast; there is no truly quiet game in a seven-game series"
        )

    if pts >= 24:
        seed_bits.append(
            f"{last} is carrying a heavy scoring load in this sample ({pts:.1f} PPG over {gp} games), so fans naturally tie the result to his nights"
        )
    elif pts >= 18:
        seed_bits.append(
            f"{last} is still a visible part of the box score ({pts:.1f} PPG), so the crowd notices when the offense flows through him"
        )

    if status == "Active" and opp:
        seed_bits.append(f"with {fan_nick(opp)} on the other side, every game is a referendum on who can impose their style")

    pressure = f"{heat} ({v_p} on our 0–100 scale). " + " ".join(seed_bits[:3])

    if seed <= 2:
        expectations = (
            f"Realistic read: people expect {nick} to play deep into May and feel like a championship threat. "
            f"An early exit would feel disappointing after the regular season they put together."
        )
    elif seed <= 4:
        expectations = (
            f"Realistic read: fans expect {nick} to win a series and push whoever they draw next. "
            f"A second-round exit can still sting because it closes the window on this roster's best punch."
        )
    else:
        expectations = (
            f"Realistic read: from seed {seed}, {nick} get room to play free—but every round they steal rewrites the story. "
            f"A quick exit still hurts because it ends the year without a signature playoff chapter."
        )
    if status != "Active":
        expectations += " With the run over, this is about whether the finish matched what reasonable people expected going in."

    v_rep = max(0, min(100, int(rep)))
    if v_rep >= 72:
        swing = "How much this playoff run could change public perception: a lot. "
    elif v_rep >= 52:
        swing = "How much this playoff run could change public perception: a meaningful amount. "
    else:
        swing = "How much this playoff run could change public perception: some, mostly around consistency and big-game moments. "
    if pm >= 4:
        swing += (
            f"In this log, {last} has often been on the right side of the margin—nights like that turn into 'he showed up when it mattered.'"
        )
    elif pm <= -3:
        swing += (
            f"In this log, the team margin on {last}'s minutes has been shaky—one cold shooting night gets framed as 'disappearing,' fair or not."
        )
    else:
        swing += (
            "Playoff TV and social chatter move fast: a loud scoring night or a quiet one can swing the conversation for a week."
        )

    v_st = max(0, min(100, int(stakes)))
    if v_st >= 78:
        stakes_txt = (
            f"What's at stake this postseason for {nick}: a chance to play for a title—or the ache of falling just short after raising expectations."
        )
    elif v_st >= 60:
        stakes_txt = (
            f"What's at stake for {nick}: proving this core belongs with the league's elite, not just the regular-season leaderboard."
        )
    else:
        stakes_txt = (
            f"What's at stake for {nick}: building proof for next summer—who stays, who goes, and how this era gets remembered."
        )
    if status != "Active":
        stakes_txt = (
            f"With the run finished, what's at stake now is how this postseason gets filed: growth, disappointment, or something in between."
        )

    v_el = max(0, min(100, int(elim_pressure)))
    if bounces >= 2:
        elim = (
            f"Series urgency is elevated ({v_el} on our 0–100 scale). {nick} have already had to answer after losses in this sample—"
            "dropping another game can hand the opponent all the emotional momentum."
        )
    elif has_loss and bounces == 0:
        elim = (
            f"Series urgency is real ({v_el} on our 0–100 scale). They've taken losses without a bounce-back win in this log yet—"
            "the next game starts to feel like a must-win even when the math still allows room."
        )
    elif has_loss:
        elim = (
            f"Series urgency sits around {v_el} on our 0–100 scale: they've traded wins and losses, so the next game can swing who controls the series tone."
        )
    else:
        elim = (
            f"Series urgency is moderate ({v_el} on our 0–100 scale) while the ledger in this log stays clean—but one off night resets the entire feel of the matchup."
        )

    legacy_default = (
        f"A deep run with {nick} becomes one of the signature chapters people use to describe this era of the franchise—"
        "especially if the best players author clear moments in close games."
    )
    legacy_body = (prof or {}).get("team_context") or legacy_default
    if not isinstance(legacy_body, str) or len(legacy_body.strip()) < 8:
        legacy_body = legacy_default

    return {
        "pressure": pressure,
        "expectations": expectations,
        "reputation": swing,
        "stakes": stakes_txt,
        "elimination": elim,
        "legacy": legacy_body,
    }


def _franchise_playoff_touchstones(team_name):
    return {
        "New York Knicks": [
            ("Carmelo Anthony", "volume scoring identity", "2010s high-usage scoring runs"),
            ("Patrick Ewing", "interior two-way anchor", "the classic Knicks postseason big workload"),
            ("Jalen Brunson", "modern lead-guard control", "the current era's half-court shot diet"),
        ],
        "Los Angeles Lakers": [
            ("Kobe Bryant", "late-clock shotmaking", "Lakers perimeter takeover history"),
            ("Shaquille O'Neal", "rim pressure", "interior dominance chapters"),
            ("LeBron James", "playoff IQ + two-way responsibility", "the late-career Lakers chapter"),
        ],
        "Philadelphia 76ers": [
            ("Allen Iverson", "isolation scoring burden", "Philly guard scoring mythology"),
            ("Joel Embiid", "MVP-level interior gravity", "the modern half-court hub"),
            ("Julius Erving", "transition charisma", "the older-school Finals-era wing"),
        ],
        "Oklahoma City Thunder": [
            ("Russell Westbrook", "relentless pace + usage", "OKC's emotional playoff identity"),
            ("Kevin Durant", "efficient high-volume scoring", "the early Thunder Finals window"),
            ("Shai Gilgeous-Alexander", "compressed-space creation", "the modern OKC engine"),
        ],
        "Detroit Pistons": [
            ("Isiah Thomas", "possession command", "Bad Boys guard leadership"),
            ("Chauncey Billups", "clutch calm", "the 2004 steady-hand model"),
            ("Ben Wallace", "defensive backbone", "rim protection without needing shots"),
        ],
        "Cleveland Cavaliers": [
            ("LeBron James", "everything offense", "the return-era Cleveland standard"),
            ("Kyrie Irving", "shot-making variance", "late-clock shot creation"),
            ("Mark Price", "precision guard play", "the pre-2000s Cleveland creator mold"),
        ],
        "Minnesota Timberwolves": [
            ("Kevin Garnett", "defensive tone-setter", "the soul-of-the-team playoff archetype"),
            ("Kevin Love", "glass + outlet pressure", "the rebounding big template"),
            ("Anthony Edwards", "explosive wing scoring", "the current Wolves shot diet"),
        ],
        "San Antonio Spurs": [
            ("Tim Duncan", "two-way big fundamentals", "the Spurs dynasty anchor"),
            ("Tony Parker", "paint touch + tempo", "the mid-2000s guard pressure"),
            ("Kawhi Leonard", "defensive eraser + efficient scoring", "the 2014 two-way wing model"),
        ],
    }.get(team_name, [
        ("Franchise legends", "playoff identity", "the historical bar fans use in barbershop debates"),
        ("Recent stars", "modern shot diet", "what today's coverage compares you to"),
        ("Role archetypes", "winning plays", "the non-box-score memory makers"),
    ])


def _historical_comparison_lines(player, team_name, cur, prev_summary, prof, role_lower):
    lines = []
    nick = fan_nick(team_name)
    ppg = cur.get("PTS") or 0
    ts = cur.get("TS_PCT")
    stl = cur.get("STL") or 0
    blk = cur.get("BLK") or 0
    d_stk = stl + blk

    icons = _franchise_playoff_touchstones(team_name)
    if icons:
        if "knicks" in team_name.lower() and ppg >= 22 and "brunson" not in player.lower():
            lines.append(
                f"At **{ppg:.1f} PPG**, you're in the Knicks-fan memory lane where people whisper **Carmelo Anthony**-type scoring responsibility — not a comp of style, but of how much the offense lives on one player's nightly output."
            )
        elif "knicks" in team_name.lower() and "brunson" in player.lower():
            lines.append(
                f"For {nick}, this is the **lead-guard playoff chapter** fans wanted when the front office bet on shot creation — {ppg:.1f} PPG is the engine number people will cite if the run keeps advancing."
            )

    if d_stk >= 2.4 and ("wing" in role_lower or "two-way" in role_lower):
        lines.append(
            f"Defensive counting stats ({stl:.1f} STL / {blk:.1f} BLK per game) read like **high-minute wing disruption** — the profile people reach for when they say *Draymond-adjacent influence* without claiming a perfect comp."
        )
    elif d_stk >= 1.8:
        lines.append(
            f"Steals/blocks combined at **{d_stk:.1f} per game** is real playoff activity on the ball — enough to swing possessions even when the scoring line is quieter."
        )

    if ts and ts >= 0.59 and ppg >= 22:
        lines.append(
            f"Efficiency is carrying weight: **{ts * 100:.1f}% TS** on meaningful volume mirrors the **Jimmy Butler 2020 Finals** archetype — tough shot diet, high trust, low waste — even if the matchup context is different."
        )
    elif ts and ts <= 0.52 and ppg >= 22:
        lines.append(
            f"The run is **high-usage with middling TS ({ts * 100:.1f}%)** — the kind of line that ages well if the team keeps winning, and harshly if the shot diet tightens later in the bracket."
        )

    if prev_summary and prev_summary.get("GP", 0) >= 3:
        dppg = ppg - (prev_summary.get("PTS") or 0)
        if dppg >= 4:
            lines.append(
                f"Versus last postseason's sample, scoring is **up ~{dppg:.1f} PPG** — a clear **step-forward** playoff profile if it holds through deeper rounds."
            )
        elif dppg <= -4:
            lines.append(
                f"Compared with last postseason's line, scoring is **down ~{-dppg:.1f} PPG** — worth watching whether that is matchup math, role change, or a cold stretch."
            )

    comps = _remove_self_comparisons(player, prof.get("comps") or [])
    if comps:
        lines.append(
            f"NBA-wide bar talk (not a model): names like **{comps[0]}**, **{comps[1]}**, and **{comps[2]}** sit in the *neighborhood of role outcome* your stat shape is flirting with this spring."
        )

    if not lines:
        lines.append(
            f"The numbers are still writing the story — once the sample grows, this block tightens around **{nick}** history and the player comps that actually fit the shape of the run."
        )
    return lines[:5]


def _narrative_storylines(player, team_name, cur, reg, prev_summary, prof):
    stories = []
    ppg = cur.get("PTS") or 0
    pm = cur.get("PLUS_MINUS") or 0
    gp = cur.get("GP") or 0

    def _num_reg(k):
        v = reg.get(k)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    rppg = _num_reg("PTS")

    if prev_summary and prev_summary.get("GP", 0) >= 3:
        if ppg < (prev_summary.get("PTS") or 0) - 2 and pm >= 1:
            stories.append(
                "**Redemption arc (texture):** the counting line dipped versus last spring, but plus/minus is still carrying green — the run can still *feel* like a cleaner story if the winning keeps coming."
            )
        if ppg > (prev_summary.get("PTS") or 0) + 3:
            stories.append(
                "**Answering last year:** the scoring average jumped in a real way — the kind of postseason jump fans treat as *validation*, not noise."
            )

    if rppg is not None and ppg > rppg + 4:
        stories.append(
            "**Playoff lift:** production is meaningfully above regular-season scoring — the classic *he saved it for spring* shape (whether that is sustainable is the drama)."
        )
    if rppg is not None and ppg + 2 < rppg and gp >= 4:
        stories.append(
            "**Squeezed by the game:** playoff scoring sits under the regular-season baseline — often matchup or foul trouble, sometimes a role shift — worth reading next to wins and plus/minus, not in a vacuum."
        )

    baseline = prof.get("baseline", 45)
    if baseline >= 66 and ppg >= 26:
        stories.append(
            "**Superstar validation mode:** the expectations were already enormous — this is where every game becomes a referendum on whether you can be *the* reason a deep run happens."
        )
    elif baseline <= 42 and ppg >= 13:
        stories.append(
            "**Underdog emergence:** expectations started lower, but the playoff line is loud enough that people are redrawing the depth chart in real time."
        )

    if prof.get("baseline", 0) >= 72 or any(x in player.lower() for x in ["lebron", "lowry", "conley", "george"]):
        stories.append(
            "**Veteran stewardship:** minutes and decision-making matter as much as peaks — the postseason is grading you on trust and shot quality as much as counting stats."
        )

    if pm <= -3 and ppg >= 18:
        stories.append(
            "**Proving the process:** high personal production with rough team on/off in the box can mean tough stagger lineups or garbage-time noise — still worth tracking as the series shortens."
        )

    if not stories:
        stories.append(
            "**Series truth:** playoff basketball rewards the player who can repeat the same winning habits on tired legs — the storyline here is still forming; the next two games usually decide how fans remember the chapter."
        )
    dedup = []
    for s in stories:
        if s not in dedup:
            dedup.append(s)
    return dedup[:6]


def render_player_playoff_story_hub(team_name, profile):
    """Narrative + impact hub for a player's postseason (stats + story + legacy texture)."""
    st.markdown('<div class="pp-wrap">', unsafe_allow_html=True)
    st.subheader("Player Playoff Hub · journey, series texture, and legacy pressure")
    st.caption(
        f"Built for **{fan_nick(team_name)}** fans. Game logs come from NBA.com via **nba_api**; clutch and quarter reads use **honest proxies** where play-by-play splits are not in this feed."
    )

    plist = current_roster_names(team_name)
    c_sel1, c_sel2 = st.columns([1.1, 1])
    with c_sel1:
        player = st.selectbox("Player", plist, key="pp_hub_player")
    with c_sel2:
        season = st.selectbox("Season", [CURRENT_NBA_SEASON, "2024-25", "2023-24"], index=0, key="pp_hub_season")

    if not NBA_STATS_AVAILABLE:
        st.error("nba_api stats endpoints unavailable.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    pid = get_player_id(player)
    if not pid:
        st.warning(f"Could not resolve NBA player id for **{player}**.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    logs_raw = _cached_playoff_gamelog(pid, season)
    if logs_raw.empty:
        st.warning(f"No playoff game log returned for **{player}** in **{season}**. Try another season or verify the player reached the postseason.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = _prepare_chrono_playoff_logs(logs_raw)
    team_tri = ""
    if "TEAM_ABBREVIATION" in df.columns and len(df):
        team_tri = str(df["TEAM_ABBREVIATION"].iloc[0]).upper()
    if not team_tri:
        team_tri = TEAM_ALIASES.get(team_name, "")

    cur_summary = summarize_playoff_logs(df)
    cur_summary["TS_PCT"] = _true_shooting_pct(df)
    cur_summary["GP"] = int(len(df))

    prev_season = _prior_nba_season_label(season)
    prev_summary = None
    if prev_season:
        prev_df = _prepare_chrono_playoff_logs(_cached_playoff_gamelog(pid, prev_season))
        if not prev_df.empty:
            prev_summary = summarize_playoff_logs(prev_df)
            prev_summary["TS_PCT"] = _true_shooting_pct(prev_df)
            prev_summary["GP"] = int(len(prev_df))

    prof = player_resume_profile(player, team_name)
    role_lower = str(prof.get("role", "")).lower()
    reg_avg = season_averages(player)

    seed = int(profile.get("seed") or 8)
    rnd = profile.get("round") or "Playoffs"
    status = profile.get("status") or "Active"
    opp = profile.get("current_opponent")

    # --- Hero ---
    logo = TEAM_LOGOS.get(team_name, "")
    hs = headshot(player)
    wl_record = ""
    if "WL" in df.columns:
        w = int((df["WL"].astype(str).str.upper().str.startswith("W")).sum())
        l = int((df["WL"].astype(str).str.upper().str.startswith("L")).sum())
        wl_record = f"{w}-{l} in the log"

    hero_badges = []
    if status == "Active":
        hero_badges.append(f"{rnd}")
    else:
        hero_badges.append("Postseason complete / eliminated context")
    hero_badges.append(f"Seed {seed}")
    if opp:
        hero_badges.append(f"Board: vs {fan_nick(opp)}")

    badge_html = "".join(f"<span class='pp-badge'>{html.escape(b)}</span>" for b in hero_badges[:4])
    if cur_summary.get("PTS", 0) >= 25:
        badge_html += "<span class='pp-badge gold'>High scoring load</span>"
    if (cur_summary.get("STL", 0) + cur_summary.get("BLK", 0)) >= 2.5:
        badge_html += "<span class='pp-badge fire'>Two-way activity</span>"
    for lbl, cls in player_fan_badges(cur_summary)[:3]:
        badge_html += f"<span class='fan-badge {cls}' style='font-size:10px;padding:3px 8px'>{html.escape(lbl)}</span>"

    st.markdown(
        f"""<div class='pp-hero team-branded'>
  <div><img src='{hs}' width='104' style='border-radius:16px;border:2px solid var(--team-primary,rgba(248,250,252,.35));object-fit:cover;background:#0b1224;'/></div>
  <div>
    <h2>{html.escape(player)} · {html.escape(season)} playoffs</h2>
    <div class='sub'>{html.escape(prof.get('role', 'Rotation'))} · {html.escape(fan_nick(team_name))} · {html.escape(wl_record)} · {int(cur_summary.get('GP',0))} games</div>
    <div class='pp-badges'>{badge_html}</div>
  </div>
  <div style='justify-self:end;'><img src='{logo}' width='56' alt=''/></div>
</div>""",
        unsafe_allow_html=True,
    )

    # --- 1 · Current run ---
    team_section_header("1 · Current playoff run", "🏀")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("PPG", f"{cur_summary.get('PTS', 0):.1f}")
    m2.metric("RPG", f"{cur_summary.get('REB', 0):.1f}")
    m3.metric("APG", f"{cur_summary.get('AST', 0):.1f}")
    ts_disp = cur_summary.get("TS_PCT")
    m4.metric("TS%", f"{ts_disp * 100:.1f}%" if ts_disp else "—")
    m5.metric("+/-", f"{cur_summary.get('PLUS_MINUS', 0):+.1f}")

    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("<div class='pp-card'><h4>Efficiency & turnover texture</h4>", unsafe_allow_html=True)
        fg = cur_summary.get("FG_PCT") or 0
        tp = cur_summary.get("FG3_PCT") or 0
        ft = cur_summary.get("FT_PCT") or 0
        tov = cur_summary.get("TOV") or 0
        st.markdown(
            f"<p class='pp-muted'>FG <b>{fg * 100:.1f}%</b> · 3P <b>{tp * 100:.1f}%</b> · FT <b>{ft * 100:.1f}%</b> · TOV <b>{tov:.1f}</b> per game.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p class='pp-muted'>TS% uses makes/attempts from the log when available; it is not opponent-adjusted.</p>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with c_b:
        st.markdown("<div class='pp-card'><h4>Playoff highs / lows (box)</h4>", unsafe_allow_html=True)
        if "PTS" in df.columns:
            imax = int(df["PTS"].idxmax())
            imin = int(df["PTS"].idxmin())
            rmax = df.loc[imax]
            rmin = df.loc[imin]
            st.markdown(
                f"<p class='pp-muted'><b>High:</b> {safe_float(rmax.get('PTS')):.0f} PTS vs {_matchup_opponent_tri(rmax.get('MATCHUP'), team_tri)} on {html.escape(str(rmax.get('GAME_DATE','')))} "
                f"(+/- {safe_float(rmax.get('PLUS_MINUS')):+.0f}).<br/>"
                f"<b>Low:</b> {safe_float(rmin.get('PTS')):.0f} PTS vs {_matchup_opponent_tri(rmin.get('MATCHUP'), team_tri)} on {html.escape(str(rmin.get('GAME_DATE','')))}.</p>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='pp-card'><h4>Clutch texture (proxies — no quarter splits in this feed)</h4>", unsafe_allow_html=True)
    wins = df[df["WL"].astype(str).str.upper().str.startswith("W")] if "WL" in df.columns else df
    loss = df[df["WL"].astype(str).str.upper().str.startswith("L")] if "WL" in df.columns else pd.DataFrame()
    wppg = float(wins["PTS"].mean()) if not wins.empty and "PTS" in wins.columns else None
    lppg = float(loss["PTS"].mean()) if not loss.empty and "PTS" in loss.columns else None
    win_txt = f"{wppg:.1f}" if wppg is not None else "—"
    loss_txt = f" · in losses: <b>{lppg:.1f}</b> PPG" if lppg is not None else ""
    st.markdown(
        f"<p class='pp-muted'>In logged wins: <b>{win_txt}</b> PPG average{loss_txt}. "
        f"Bounce-back wins after a loss in this run: <b>{_bounce_back_games(df)}</b>.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 2 · Series ---
    team_section_header("2 · Series-by-series breakdown", "📊")
    st.caption("Series 1 is the **first** playoff matchup in this log (earliest games), then Series 2 for the next opponent, and so on.")
    chunks = _series_chunks_playoff_order(df, team_tri)
    if not chunks:
        st.info("Could not split series from matchups.")
    else:
        for idx, (opp_tri, seg) in enumerate(chunks, start=1):
            opp_name = ALIAS_TO_TEAM.get(opp_tri, opp_tri)
            label = f"Series {idx} · vs {opp_name}"
            w = int((seg["WL"].astype(str).str.upper().str.startswith("W")).sum()) if "WL" in seg.columns else 0
            el = int((seg["WL"].astype(str).str.upper().str.startswith("L")).sum()) if "WL" in seg.columns else 0
            sm = summarize_playoff_logs(seg)
            sm["TS_PCT"] = _true_shooting_pct(seg)
            mom = _momentum_reading(seg)
            cons, cons_note = _consistency_rating(seg["PTS"]) if "PTS" in seg.columns else (None, "—")
            st.markdown(f"<div class='pp-card'><h4>{html.escape(label)} · {w}-{el} in log</h4>", unsafe_allow_html=True)
            ts_part = f"{(sm.get('TS_PCT') * 100):.1f}%" if sm.get("TS_PCT") is not None else "—"
            st.markdown(
                f"<p class='pp-muted'><b>Line:</b> {sm.get('PTS',0):.1f} / {sm.get('REB',0):.1f} / {sm.get('AST',0):.1f} · "
                f"STL/BLK {sm.get('STL',0):.1f}/{sm.get('BLK',0):.1f} · TS% {ts_part}</p>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<p class='pp-muted'><b>Momentum:</b> {mom}</p>", unsafe_allow_html=True)
            if cons is not None:
                st.markdown(
                    f"<p class='pp-muted'><b>Consistency rating:</b> {cons}/100 — {cons_note}</p>",
                    unsafe_allow_html=True,
                )
            if len(seg) >= 2:
                seg_scored = seg.copy()
                seg_scored["_impact"] = seg_scored.apply(_game_impact_score, axis=1)
                top = seg_scored.sort_values("_impact", ascending=False).head(2)
                bits = []
                for _, rr in top.iterrows():
                    bits.append(
                        f"{safe_float(rr.get('PTS')):.0f} PTS ({str(rr.get('GAME_DATE',''))}) vs {_matchup_opponent_tri(rr.get('MATCHUP'), team_tri)}"
                    )
                st.markdown("<p class='pp-muted'><b>Biggest games (impact blend):</b> " + " · ".join(bits) + "</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 3 · Pressure & legacy ---
    team_section_header("3 · Pressure & legacy", "🎯")
    pressure_base = min(100, 28 + max(0, 10 - seed) * 4 + _round_narrative_weight(rnd) + min(22, int(cur_summary.get("PTS", 0)) * 2))
    rep = min(100, int(prof.get("baseline", 50) + min(18, abs(safe_float(cur_summary.get("PLUS_MINUS"))) * 2)))
    stakes = min(100, 35 + _round_narrative_weight(rnd) + (12 if status == "Active" else 0))
    elim_pressure = min(100, 22 + _bounce_back_games(df) * 14 + (10 if any(str(x).upper().startswith("L") for x in df.get("WL", [])) else 0))

    nar = _pp_hub_pressure_legacy_narratives(
        team_name,
        player,
        seed,
        rnd,
        status,
        opp,
        pressure_base,
        rep,
        stakes,
        elim_pressure,
        cur_summary,
        df,
        prof,
    )

    def meter_bar(label, val, klass, body_text):
        v = max(0, min(100, int(val)))
        safe_cls = klass if klass in ("", "gold", "ember") else ""
        return (
            f"<div class='pp-card'><h4>{html.escape(label)}</h4>"
            f"<div class='pp-meter'><span class='{safe_cls}' style='width:{v}%'></span></div>"
            f"<p class='pp-muted'>{html.escape(body_text)}</p></div>"
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(meter_bar("Pressure level", pressure_base, "", nar["pressure"]), unsafe_allow_html=True)
        st.markdown(
            f"<div class='pp-card'><h4>Playoff expectations</h4><p class='pp-muted'>{html.escape(nar['expectations'])}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            meter_bar(
                "How much this run could change perception",
                rep,
                "gold",
                nar["reputation"],
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(meter_bar("What's at stake this postseason", stakes, "ember", nar["stakes"]), unsafe_allow_html=True)
        st.markdown(
            meter_bar(
                "Elimination & bounce-back pressure",
                elim_pressure,
                "gold",
                nar["elimination"],
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='pp-card'><h4>What this playoff run could mean historically</h4><p class='pp-muted'>"
            + html.escape(nar["legacy"])
            + "</p></div>",
            unsafe_allow_html=True,
        )

    # --- 4 · Historical comparisons ---
    team_section_header("4 · Historical comparison engine", "📚")
    for line in _historical_comparison_lines(player, team_name, cur_summary, prev_summary, prof, role_lower):
        with st.container(border=True):
            st.markdown(line)
    if prev_summary:
        st.caption(f"Prior playoff sample: **{prev_season}** ({prev_summary.get('GP', 0)} games) used only when the API returned a log.")

    # --- 5 · Clutch impact ---
    team_section_header("5 · Clutch impact", "⏱️")
    df_c = df.copy()
    df_c["_impact"] = df_c.apply(_game_impact_score, axis=1)
    df_c = df_c.sort_values("_impact", ascending=False)
    st.markdown("<div class='pp-card'><h4>Late-game / takeover proxies</h4>", unsafe_allow_html=True)
    st.markdown(
        "<p class='pp-muted'>Quarter splits are not in standard season game logs here — instead we rank <b>playoff takeover games</b> by a weighted blend of points, playmaking, stocks, and plus/minus.</p>",
        unsafe_allow_html=True,
    )
    if not df_c.empty:
        top3 = df_c.head(3)
        lines = []
        for _, rr in top3.iterrows():
            lines.append(
                f"{html.escape(str(rr.get('GAME_DATE','')))}: {safe_float(rr.get('PTS')):.0f} PTS, "
                f"+/- {safe_float(rr.get('PLUS_MINUS')):+.0f} vs {_matchup_opponent_tri(rr.get('MATCHUP'), team_tri)}"
            )
        st.markdown("<p class='pp-muted'><b>Top takeover games:</b><br/>" + "<br/>".join(lines) + "</p>", unsafe_allow_html=True)
    takeover = min(100, int(38 + 2.2 * (cur_summary.get("PTS", 0)) + 4.5 * (cur_summary.get("STL", 0) + cur_summary.get("BLK", 0)) + 1.1 * max(0, cur_summary.get("PLUS_MINUS", 0))))
    st.markdown(
        f"<p class='pp-muted'><b>Playoff takeover rating:</b> {takeover}/100 — "
        f"big scoring nights plus steals, blocks, and winning margin in this log push this number up.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 6 · Narratives ---
    team_section_header("6 · Narrative storylines", "📰")
    for s in _narrative_storylines(player, team_name, cur_summary, reg_avg, prev_summary, prof):
        with st.container(border=True):
            st.markdown(s)

    # --- 7 · Visuals ---
    team_section_header("7 · Progression & raw log", "📈")
    tcol1, tcol2 = st.columns((1, 1))
    with tcol1:
        st.markdown("<div class='pp-card'><h4>Game-by-game progression</h4>", unsafe_allow_html=True)
        chart_df = df.copy()
        chart_df["Game #"] = np.arange(1, len(chart_df) + 1)
        if "PLUS_MINUS" in chart_df.columns and "PTS" in chart_df.columns:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=chart_df["Game #"], y=chart_df["PTS"], name="PTS", mode="lines+markers", line=dict(color="#0ea5e9")),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(
                    x=chart_df["Game #"],
                    y=chart_df["PLUS_MINUS"],
                    name="+/-",
                    mode="lines+markers",
                    line=dict(color="#6366f1", dash="dot"),
                    marker=dict(size=7),
                ),
                secondary_y=True,
            )
            fig.update_yaxes(title_text="PTS", secondary_y=False)
            fig.update_yaxes(title_text="+/-", secondary_y=True, zeroline=True, zerolinewidth=1, zerolinecolor="#94a3b8")
        else:
            fig = go.Figure()
            if "PTS" in chart_df.columns:
                fig.add_trace(go.Scatter(x=chart_df["Game #"], y=chart_df["PTS"], name="PTS", mode="lines+markers", line=dict(color="#0ea5e9")))
        fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=40, b=36),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(title=""),
            xaxis=dict(title="Chronological playoff game #"),
            paper_bgcolor="#fafafa",
            plot_bgcolor="#fafafa",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with tcol2:
        st.markdown("<div class='pp-card'><h4>Playoff timeline</h4>", unsafe_allow_html=True)
        st.caption("Newest games first — scroll down for earlier rounds. Series cards above stay in playoff order (Series 1 = first matchup).")
        items = []
        df_tl = _df_newest_first_for_display(df)
        for _, rr in df_tl.iterrows():
            wl = str(rr.get("WL", "—"))
            items.append(
                f"<div class='pp-tl-item'><b>{html.escape(str(rr.get('GAME_DATE','')))}</b> · {html.escape(wl)} · "
                f"{safe_float(rr.get('PTS')):.0f} PTS · {_matchup_opponent_tri(rr.get('MATCHUP'), team_tri)}</div>"
            )
        st.markdown("<div class='pp-timeline'>" + "".join(items) + "</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    stat_opts = [c for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "PLUS_MINUS", "MIN"] if c in df.columns]
    if stat_opts:
        stat = st.selectbox("Overlay single-stat line", stat_opts, index=0, key="pp_hub_stat")
        cdf = df.copy()
        cdf["Game #"] = np.arange(1, len(cdf) + 1)
        st.plotly_chart(
            px.line(cdf, x="Game #", y=stat, markers=True, title=f"{player} · {stat} by playoff game"),
            use_container_width=True,
        )

    show_cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS"] if c in df.columns]
    with st.expander("Full playoff game log (table)"):
        df_tbl = _df_newest_first_for_display(df)
        st.dataframe(df_tbl[show_cols], use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================================
# Analysis / visualization helpers
# ==========================================================
def create_boxscore_df(game_box):
    rows = []
    for side in ["homeTeam", "awayTeam"]:
        t = game_box.get(side, {})
        tri = t.get("teamTricode", "")
        for p in t.get("players", []):
            stt = p.get("statistics", {})
            rows.append({"Team":tri,"Player":p.get("name",""),"MIN":stt.get("minutes",""),"PTS":stt.get("points",0),"REB":stt.get("reboundsTotal",0),"AST":stt.get("assists",0),"STL":stt.get("steals",0),"BLK":stt.get("blocks",0),"TO":stt.get("turnovers",0),"PF":stt.get("foulsPersonal",0),"FGM":stt.get("fieldGoalsMade",0),"FGA":stt.get("fieldGoalsAttempted",0),"3PM":stt.get("threePointersMade",0),"3PA":stt.get("threePointersAttempted",0),"+/-":stt.get("plusMinusPoints",0)})
    return pd.DataFrame(rows)

def min_to_float(v):
    try:
        if isinstance(v, str) and ":" in v:
            m, s = v.split(":"); return float(m) + float(s)/60
        return float(v)
    except Exception: return 0.0

def estimated_lineup(box_df, alias, team_name):
    df = box_df[box_df["Team"] == alias].copy() if not box_df.empty else pd.DataFrame()
    if df.empty:
        names = estimated_starters_from_api(team_name)
        return pd.DataFrame([{"Team":alias,"Player":p,"MIN":"0:00","PTS":0,"REB":0,"AST":0,"STL":0,"BLK":0,"PF":0,"FGM":0,"FGA":0} for p in names])
    df["MIN_FLOAT"] = df["MIN"].apply(min_to_float)
    return df.sort_values("MIN_FLOAT", ascending=False).head(5)

def player_temp(r):
    fga = safe_float(r.get("FGA")); fgm = safe_float(r.get("FGM")); pts = safe_float(r.get("PTS"))
    pct = fgm/fga if fga else 0
    if pts >= 18 and pct >= .50: return "🔥"
    if fga >= 8 and pct <= .30: return "❄️"
    return ""

def win_prob(margin, period, is_home):
    w = {1:1.2, 2:1.8, 3:2.8, 4:4.5}.get(max(1,min(safe_int(period,1),4)), 4.5)
    return int(max(1, min(99, round(50 + margin*w + (2.5 if is_home else 0)))))

def shot_df_from_pbp(actions, alias):
    rows=[]; rng=np.random.default_rng(17)
    for a in actions:
        tri = a.get("teamTricode") or ""
        if tri != alias: continue
        desc = a.get("description", "") or ""
        d = desc.lower()
        if not any(x in d for x in ["miss", "made", "makes", "layup", "dunk", "3pt", "shot"]): continue
        made = ("made" in d or "makes" in d) and "miss" not in d
        player = a.get("personName") or a.get("playerName") or "Unknown"
        if "3pt" in d or "three" in d:
            x, y = float(rng.uniform(-22,22)), float(rng.uniform(22,31))
        elif "layup" in d or "dunk" in d:
            x, y = float(rng.uniform(-5,5)), float(rng.uniform(1,8))
        else:
            x, y = float(rng.uniform(-16,16)), float(rng.uniform(8,22))
        rows.append({"Player":player,"Made":made,"x":x,"y":y,"Description":desc})
    return pd.DataFrame(rows)

def draw_court(shots, title):
    fig=go.Figure()
    fig.update_layout(title=title,height=620,plot_bgcolor="#c68642",paper_bgcolor="#f3d3a3",font=dict(color="#111827"),xaxis=dict(range=[-27,27],visible=False),yaxis=dict(range=[0,50],visible=False),legend=dict(orientation="h"),margin=dict(l=20,r=20,t=55,b=20))
    line=dict(color="#5c2e0e",width=3)
    for shape in [dict(type="rect",x0=-25,y0=0,x1=25,y1=47),dict(type="rect",x0=-8,y0=0,x1=8,y1=19),dict(type="circle",x0=-6,y0=-1,x1=6,y1=11),dict(type="circle",x0=-23.75,y0=0,x1=23.75,y1=47.5)]:
        fig.add_shape(**shape,line=line)
    fig.add_shape(type="line",x0=-22,y0=0,x1=-22,y1=14,line=line); fig.add_shape(type="line",x0=22,y0=0,x1=22,y1=14,line=line)
    if not shots.empty:
        made=shots[shots["Made"]==True]; miss=shots[shots["Made"]==False]
        fig.add_trace(go.Scatter(x=made["x"],y=made["y"],mode="markers",name="Made O",text=made["Description"],marker=dict(symbol="circle-open",color="#0047FF",size=18,line=dict(width=5,color="#0047FF"))))
        fig.add_trace(go.Scatter(x=miss["x"],y=miss["y"],mode="markers",name="Missed X",text=miss["Description"],marker=dict(symbol="x",color="#E00000",size=17,line=dict(width=5,color="#E00000"))))
    return fig

def is_top_play(desc):
    d=(desc or "").lower()
    if any(x in d for x in ["free throw", "personal foul", "timeout", "substitution", "violation", "delay"]): return False
    return any(x in d for x in ["dunk", "alley", "3pt", "three", "steal", "block", "fast break", "putback", "driving layup", "go-ahead", "ties", "step back"])

def explain_play(desc, team):
    d=(desc or "").lower()
    if "3pt" in d or "three" in d: return f"It was a high-value shot that changed spacing and scoreboard pressure for {team}."
    if "dunk" in d or "layup" in d or "alley" in d: return f"It showed efficient rim pressure for {team}."
    if "steal" in d: return "It created a turnover and a chance to run."
    if "block" in d: return "It protected the rim and stopped a quality look."
    return "It was one of the highest-impact plays available in the play-by-play feed."

def top_plays_from_game_id(game_id, team_name, limit=5):
    alias=TEAM_ALIASES[team_name]
    actions=get_playbyplay_by_game_id(game_id) if game_id else []
    rows=[]
    for a in actions:
        if (a.get("teamTricode") or "") != alias: continue
        desc=a.get("description","") or ""
        if not is_top_play(desc): continue
        rows.append({"Period":a.get("period",""),"Clock":a.get("clock",""),"Top Play":desc,"Why it mattered":explain_play(desc,team_name)})
    if rows: return pd.DataFrame(rows[-limit:])
    return pd.DataFrame(FALLBACK_TOP_PLAYS.get(team_name, [{"Game":"Previous game","Top Play":f"{team_name}'s key plays will appear here when play-by-play data is available.","Why it mattered":"Fallback shown because the API did not return detailed play-by-play for the previous game."}]))

def previous_game_top_plays(team_name):
    _, s = series_for_team(team_name)
    if s and s.get("games"):
        last=s["games"][-1]
        df=top_plays_from_game_id(last.get("GameID",""), team_name)
        if "Game" not in df.columns:
            df.insert(0,"Game",last.get("Game","Previous Game"))
        return df
    return pd.DataFrame(FALLBACK_TOP_PLAYS.get(team_name, []))

def game_story(team_name, margin, prob, box_df):
    alias = TEAM_ALIASES[team_name]
    nick = fan_nick(team_name)
    if box_df.empty:
        return [f"{nick} box score is still loading in the feed — numbers snap in as the league publishes rows."]
    df = box_df[box_df["Team"] == alias]
    lines = []
    if margin > 0:
        lines.append(f"{nick} hold a +{margin} edge on the board — the next stretch is about fouls, turnovers, and who gets the clean look.")
    elif margin == 0:
        lines.append("Score is knotted — the next mini-run swings noise in the building and how tight the whistles feel.")
    else:
        lines.append(f"{nick} trail by {abs(margin)} — the counter usually starts with a clean stop chain, then a quality shot in rhythm.")
    lines.append(
        f"Rotation totals in this feed: {int(df['PTS'].sum())} pts, {int(df['REB'].sum())} reb, {int(df['AST'].sum())} ast for {nick}."
    )
    lines.append("Next winning stretch: extra-pass threes, no live-ball giveaways, and the defensive glass to kill extra possessions.")
    return lines

def matchup_advantages(team, opp):
    t_starters = estimated_starters_from_api(team)
    o_starters = estimated_starters_from_api(opp)
    positions=["PG","SG","SF","PF","C"]
    rows=[]
    for i,pos in enumerate(positions):
        tp=t_starters[i] if i < len(t_starters) else "TBD"
        op=o_starters[i] if i < len(o_starters) else "TBD"
        if "TBD" in [tp, op]:
            adv="TBD"; why="NBA API roster data was incomplete for this position."
        elif any(x in tp for x in ["Brunson","Mitchell","Shai","Edwards","LeBron","Embiid","Wembanyama","Cunningham","Maxey","Towns","Davis"]):
            adv=team; why=f"{tp} grades as one of the higher-impact current rotation players in this matchup."
        elif any(x in op for x in ["Brunson","Mitchell","Shai","Edwards","LeBron","Embiid","Wembanyama","Cunningham","Maxey","Towns","Davis"]):
            adv=opp; why=f"{op} gives {opp} the bigger star-impact edge at this spot."
        else:
            adv="Close"; why="This spot depends on current form, shooting, defense, matchup choices, and foul trouble."
        rows.append({"Position":pos, team:tp, opp:op, "Advantage":adv, "Why":why})
    return pd.DataFrame(rows)


# ==========================================================
# Matchup intelligence / series analysis engine
# ==========================================================
def _intel_parse_points_from_score(score_str, team, opp):
    """Extract each team's point total from common score strings (best-effort)."""
    if not score_str:
        return None, None
    s = re.sub(r"\([^)]*\)", "", str(score_str))
    chunks = [c.strip() for c in re.split(r",\s*", s) if c.strip()]
    found = {}
    for ch in chunks:
        m = re.search(r"(\d{2,3})\s*$", ch)
        if not m:
            continue
        pts = int(m.group(1))
        label = ch[: m.start()].strip().lower()
        for tm in (team, opp):
            tl = tm.lower()
            last = tm.split()[-1].lower()
            alias = TEAM_ALIASES.get(tm, "").lower()
            if tl in label or last in label or alias in label:
                found[tm] = pts
    if team in found and opp in found:
        return found[team], found[opp]
    nums = re.findall(r"\b(\d{2,3})\b", s)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return None, None


def _intel_margin_series(games, team, opp):
    """Per game: margin from team's perspective (positive = team won by that many)."""
    rows = []
    for g in games or []:
        w = g.get("Winner")
        tp, op = _intel_parse_points_from_score(g.get("Score", ""), team, opp)
        if w == team and tp is not None and op is not None:
            rows.append(tp - op)
        elif w == opp and tp is not None and op is not None:
            rows.append(-(tp - op))
        elif w == team:
            rows.append(8)
        elif w == opp:
            rows.append(-8)
    return rows


def _intel_injury_signal(team_name, opp_name):
    """Rough availability pressure for narrative (counts + one headline name)."""
    teams = [team_name, opp_name]
    out = {"team_out": 0, "team_q": 0, "opp_out": 0, "opp_q": 0, "headline": None}
    for i, tm in enumerate(teams):
        df, _ = get_injury_report(tm)
        if df is None or df.empty:
            continue
        for _, r in df.head(5).iterrows():
            stt = str(r.get("Status", "")).lower()
            pl = str(r.get("Player", ""))
            if "out" in stt:
                if i == 0:
                    out["team_out"] += 1
                else:
                    out["opp_out"] += 1
                if not out["headline"]:
                    out["headline"] = (tm, pl, "out")
            elif any(x in stt for x in ("question", "doubt", "game time")):
                if i == 0:
                    out["team_q"] += 1
                else:
                    out["opp_q"] += 1
                if not out["headline"]:
                    out["headline"] = (tm, pl, "questionable")
    return out


def _intel_variant(seed, options):
    h = sum(ord(c) for c in str(seed)) % len(options)
    return options[h]


MATCHUP_INTEL_PAIR_HOOKS = {
    frozenset({"New York Knicks", "Philadelphia 76ers"}): "**Brunson pick-and-roll** vs **Embiid drop depth** decides whether Philly gets clean weak-side threes or New York lives at the line.",
    frozenset({"Oklahoma City Thunder", "Los Angeles Lakers"}): "**Thunder transition** vs **Lakers early help back** — the first four minutes off misses usually set the night's pace.",
    frozenset({"Detroit Pistons", "Cleveland Cavaliers"}): "**Detroit offensive rebounding** vs **Cleveland's help-and-recover timing** can override cold half-court stretches.",
    frozenset({"San Antonio Spurs", "Minnesota Timberwolves"}): "**Wembanyama rim deterrence** vs **Edwards downhill pressure** forces the defense to pick between early doubles and one-on-one survival.",
}


def intel_games_opponent_and_record(team_name):
    """Resolve opponent, game rows, wins, and round label for analysis."""
    prof = TEAM_PROFILES[team_name]
    _, s = series_for_team(team_name)
    games = []
    opp = None
    round_label = prof.get("round", "Playoffs")
    if s:
        opp = s["b"] if team_name == s["a"] else s["a"]
        games = list(s.get("games") or [])
        round_label = s.get("round", round_label)
        tw = int(s.get("a_wins", 0)) if team_name == s["a"] else int(s.get("b_wins", 0))
        ow = int(s.get("b_wins", 0)) if team_name == s["a"] else int(s.get("a_wins", 0))
        return s, opp, games, tw, ow, round_label, "current"
    if prof.get("status") == "Eliminated":
        opp = prof.get("first_round_opponent")
        games = [dict(g) for g in FIRST_ROUND_GAME_SCORES.get(team_name, [])]
        tw = sum(1 for g in games if g.get("Winner") == team_name)
        ow = sum(1 for g in games if g.get("Winner") == opp)
        return None, opp, games, tw, ow, "First round (series complete)", "eliminated"
    _, s2 = second_round_series_for_team(team_name)
    if s2:
        opp = s2["b"] if team_name == s2["a"] else s2["a"]
        games = list(s2.get("games") or [])
        round_label = s2.get("round", round_label)
        tw = int(s2.get("a_wins", 0)) if team_name == s2["a"] else int(s2.get("b_wins", 0))
        ow = int(s2.get("b_wins", 0)) if team_name == s2["a"] else int(s2.get("a_wins", 0))
        return s2, opp, games, tw, ow, round_label, "current"
    opp = prof.get("current_opponent") or prof.get("first_round_opponent")
    return None, opp, [], 0, 0, round_label, "waiting"


def build_matchup_intelligence_sections(team_name):
    """Return nine analyst-style sections; inputs are series + profiles + injuries."""
    s, opp, games, tw, ow, rnd, mode = intel_games_opponent_and_record(team_name)
    if not opp or opp not in TEAM_PROFILES:
        return None, "We need a locked opponent for your sidebar team — try again once the bracket ties this matchup."

    t_prof = TEAM_PROFILES[team_name]
    o_prof = TEAM_PROFILES[opp]
    margins = _intel_margin_series(games, team_name, opp)
    inj = _intel_injury_signal(team_name, opp)
    last_w = games[-1].get("Winner") if games else None
    prev_w = games[-2].get("Winner") if len(games) > 1 else None
    blowouts_for = sum(1 for m in margins if m >= 15)
    blowouts_against = sum(1 for m in margins if m <= -15)
    close_games = sum(1 for m in margins if abs(m) <= 7)
    avg_abs = int(sum(abs(m) for m in margins) / len(margins)) if margins else 0

    t_strengths = t_prof.get("strengths", [])
    t_concerns = t_prof.get("concerns", [])
    o_strengths = o_prof.get("strengths", [])
    o_concerns = o_prof.get("concerns", [])
    t_star = (t_prof.get("starters") or [""])[0]
    o_star = (o_prof.get("starters") or [""])[0]
    x_name = (t_prof.get("subs") or t_prof.get("starters", [""]))[0] if t_prof.get("subs") else (t_prof.get("starters") or ["Rotation"])[-1]

    seed = f"{team_name}|{opp}|{tw}{ow}|{len(games)}"
    Y = fan_nick(team_name)
    O = fan_nick(opp)

    # --- 1. Key matchup advantage (your team's broadcast) ---
    if tw > ow:
        if margins:
            adv_body = _intel_variant(
                seed + "adv",
                [
                    f"You're seeing **{Y}** turn **{t_strengths[0] if t_strengths else 'your identity'}** into wins — **{tw}-{ow}** on {O}. What you want on film review is {O} never getting comfortable early-clock.",
                    f"The ledger **{tw}-{ow}** matches what you've felt: **{t_strengths[1] if len(t_strengths) > 1 else (t_strengths[0] if t_strengths else 'execution')}** is winning the physical battle for {Y}.",
                    f"Up **{tw}-{ow}**, you're dictating terms — especially **{t_strengths[0] if t_strengths else 'star creation'}** — and making {O} take tougher late-clock shots.",
                ],
            )
        else:
            adv_body = _intel_variant(
                seed + "advnom",
                [
                    f"Bracket says you're up **{tw}-{ow}** — even before full box parsing, it passes the eye test: **{t_strengths[0] if t_strengths else 'your best habits'}** are showing in winning minutes.",
                    f"You're ahead **{tw}-{ow}** where it counts. {O} has to steal **first good look** after misses — you feel that swing in the building.",
                    f"**{tw}-{ow}** favors {Y}; what you hope {O} never solves is taking away **{t_strengths[0] if t_strengths else 'paint touches'}** without giving up the arc.",
                ],
            )
    elif ow > tw:
        if margins:
            adv_body = _intel_variant(
                seed + "advo",
                [
                    f"Tough spot: **{O}** leads **{ow}-{tw}** leaning on **{o_strengths[0] if o_strengths else 'their best habits'}**. Your comeback map: fewer clean looks for **{o_star.split()[-1] if o_star else 'their star'}** and more **extra possessions**.",
                    f"The **{ow}-{tw}** scoreboard reflects {O} winning the **{o_strengths[0] if o_strengths else 'scheme'}** battle. Honest counter for {Y} fans: attack **{o_concerns[0] if o_concerns else 'their weak-side help'}** until it cracks.",
                    f"{O} has controlled **{ow}-{tw}** by making you defend **{o_strengths[1] if len(o_strengths) > 1 else (o_strengths[0] if o_strengths else 'multiple actions')}** without fouling — still doable, just louder in the huddle.",
                ],
            )
        else:
            adv_body = _intel_variant(
                seed + "advonm",
                [
                    f"{O} sits **{ow}-{tw}** — you need a cleaner **{t_strengths[0] if t_strengths else 'half-court'}** night and to stress **{o_concerns[0] if o_concerns else 'their turnover risk'}**.",
                    f"Trailing **{ow}-{tw}**, you're chasing **{o_strengths[0] if o_strengths else 'their best nights'}** with sharper **shot selection** and fewer **live-ball turnovers** — boring, but that's the door back in.",
                    f"The **{ow}-{tw}** hole means hunting **early switches** before {O} sets its **drop/tag** comfort zone.",
                ],
            )
    elif games:
        adv_body = _intel_variant(
            seed + "adv_even",
            [
                f"Deadlocked **{tw}-{ow}** — you win the night when **{t_strengths[0] if t_strengths else 'transition'}** turns into real points and you kill live-ball turnovers.",
                f"**{tw}-{ow}** is a **shot-quality race** for {Y} fans: your **{t_strengths[0] if t_strengths else 'spacing'}** vs their **{o_strengths[0] if o_strengths else 'rim protection'}**.",
                f"Next game is a swing — you want **{t_strengths[0] if t_strengths else 'your pace'}**; {O} wants a **{o_strengths[0] if o_strengths else 'grind'}** mud fight.",
            ],
        )
    else:
        adv_body = (
            f"Games aren't in the log yet — your preview heart still starts with **{t_strengths[0] if t_strengths else 'half-court execution'}** "
            f"vs **{o_strengths[0] if o_strengths else 'their set defense'}** once Game 1 posts."
        )

    hook = MATCHUP_INTEL_PAIR_HOOKS.get(frozenset({team_name, opp}))
    if hook:
        adv_body = adv_body.rstrip() + " " + hook
    if blowouts_for >= 1 and any("rebound" in (x or "").lower() for x in t_strengths):
        adv_body += f" You should feel good about **{Y} owning the glass** when help stays home."
    if blowouts_for >= 1 and any("pace" in (x or "").lower() or "transition" in (x or "").lower() for x in t_strengths):
        adv_body += f" **Transition runs** off stops have been your separator — keep pushing that edge."

    # --- 2. Biggest tactical concern ---
    concern_bits = []
    if inj.get("headline"):
        tm_h, pl_h, tag_h = inj["headline"]
        concern_bits.append(
            f"**{pl_h}** ({tm_h}) flagged **{tag_h}** — worth knowing so you're not blindsided at tip"
        )
    if inj["team_out"] or inj["team_q"]:
        concern_bits.append(
            f"your own room has stress (**{inj['team_out']}** out / **{inj['team_q']}** questionable signals)"
        )
    concern_bits.append(
        f"{O} can hurt you where you're thin: **{t_concerns[0] if t_concerns else 'slow rotations'}** vs their **{o_strengths[0] if o_strengths else 'shot creation'}**"
    )
    concern_body = "What should worry you most: " + " and ".join(concern_bits[:2]) + "."

    # --- 3. X-factor ---
    x_body = _intel_variant(
        seed + "xf",
        [
            f"**{x_name}** is your sneaky swing piece — when starters sit, {O} often loses juice if **{o_concerns[-1] if o_concerns else 'their depth'}** gets tested in foul trouble.",
            f"Keep eyes on **{x_name}** — these series flip when a non-headline guy bankrolls **spacing, extra possessions, or defensive plays** in a six-minute second-quarter stretch.",
            f"If **{x_name}** hits and avoids getting hunted, your stars stay fresher for late **pick-and-roll** possessions.",
        ],
    )

    # --- 4. Most important adjustment ---
    if blowouts_against >= 2:
        adj = f"You've been blown out multiple times — the fix you want to see is **early help rules + transition get-backs** so **{o_star.split()[-1] if o_star else O}** stops getting runway."
    elif blowouts_for >= 2:
        adj = f"You've shown you can **run away** from {O} — expect them to **slow the game**, shrink transition, and try to strand you in **late-clock isolations**."
    elif close_games >= max(2, len(margins) - 1) and margins:
        adj = f"**{close_games}** nail-biters (avg ~{avg_abs} pts) — your path is **ATO execution, SLOB/BLOB clarity, and winning the first six minutes after halftime**."
    else:
        adj = _intel_variant(
            seed + "adj",
            [
                f"Rotation chess — **rebounding vs switching** — whoever forces the other into **backup coverages** first usually owns the middle quarters.",
                f"Watch for a **PnR coverage tweak** on **{o_star.split()[-1] if o_star else O}** when your three goes cold.",
                f"**Side PnR placement** and **weak-side tag timing** — {O} wants **{t_star.split()[-1] if t_star else 'your star'}** off the nail without free corners.",
            ],
        )

    # --- 5. Defensive matchup problems ---
    def_body = _intel_variant(
        seed + "def",
        [
            f"You have to solve how {O} runs **{o_strengths[0] if o_strengths else 'star touches'}** in **spread PnR** — weak-side help is getting stretched and skips are turning into **clean threes**.",
            f"The stress point is **{o_star}** attacking **{t_concerns[0] if t_concerns else 'your point of attack'}** — help opens **ORBs and dump-offs** that hurt on the second side.",
            f"{O}'s **{o_strengths[1] if len(o_strengths) > 1 else (o_strengths[0] if o_strengths else 'size')}** forces you to pick: **switch mismatches** or **over-help rebound holes**.",
        ],
    )

    # --- 6. Momentum shift ---
    if last_w == team_name and prev_w == team_name:
        mom_txt = f"You're rolling — **back-to-back** wins for {Y} until {O} lands a **counterpunch quarter**."
        mom_class = "up"
    elif last_w == opp and prev_w == opp:
        mom_txt = f"{O} is stacking Ws — you need a **tone-setting defensive first quarter** next time out to flip how this feels on the couch."
        mom_class = "down"
    elif last_w == team_name:
        mom_txt = f"You took the last one — ride **possession quality** and **defensive rebounding** into the next tip."
        mom_class = "up"
    elif last_w == opp:
        mom_txt = f"{O} answered last — expect **scheme tweaks** and **extra physicality on screens** early; that's your cue to punch first."
        mom_class = "down"
    else:
        mom_txt = f"Momentum resets until the next result — **Game 1 (or next game)** sets whistle tone and pace for {Y} fans."
        mom_class = "flat"

    # --- 7. Clutch-time edge ---
    if not margins:
        clutch = "Once games populate, this reads how **tight vs blowout** nights shape your late-game stress as a fan."
    elif close_games >= len(margins) // 2 + 1:
        clutch = f"This has been a **nail-biter series** for you — clutch belongs to whoever wins **FTs, turnovers, and ORB on late misses**, not just the last shot."
    else:
        clutch = f"Some nights have broken open — for {Y}, clutch is less about one play and more about **avoiding the avalanche quarter** (**live-ball turnovers**, **transition threes**)."

    # --- 8. Pressure meter (higher = more heat on you as a fan) ---
    gp = tw + ow
    diff = tw - ow
    if mode == "eliminated":
        pressure = 88
        p_label = "Season-defining"
        p_note = "Honest mode: the run ended — what broke schematically and what still makes you proud of this group."
    elif gp == 0:
        pressure = 32
        p_label = "Pre-series"
        p_note = "Nerves are normal — the meter sharpens once Game 1 hits the log."
    elif abs(diff) >= 3 and gp >= 3:
        pressure = 22 if diff > 0 else 92
        p_label = "Series separation"
        p_note = (
            f"You've built cushion — enjoy it, but stay sharp; {O} needs a schematic shock, not just makes."
            if diff > 0
            else f"You're in a hole — the believable comeback starts with **defense-first quarters** and **no live-ball gifts**."
        )
    elif diff <= -2 and max(tw, ow) >= 3:
        pressure = 86
        p_label = "Catch-up heat"
        p_note = f"Every trip feels loud — timeouts, fouls, and boards decide how you feel walking out."
    elif diff >= 2 and max(tw, ow) >= 3:
        pressure = 34
        p_label = "Close-out leverage"
        p_note = f"You've got margin — complacency and whistle swings are the real villains now, not talent."
    elif tw == ow and gp >= 4:
        pressure = 58
        p_label = "Chess-match heat"
        p_note = f"Even series — lineups, health, and one hot quarter swing how {Y} fans sleep."
    else:
        pressure = int(40 + min(22, gp * 5) + abs(diff) * 4)
        pressure = min(88, max(24, pressure))
        p_label = "Series calibration"
        p_note = f"Still learning who imposes pace and paint touches early — that's the {Y} fan homework."

    # --- 9. Coaching chess match ---
    chess = _intel_variant(
        seed + "ch",
        [
            f"Timeout chess: {O} toggles **coverage on {t_star.split()[-1] if t_star else 'your star'}**; you counter with **off-ball screens** to hunt **switches**.",
            f"Rotation length — whoever shortens the bench without bleeding minutes usually stabilizes **your glass**.",
            f"Series-long bet: **help at the nail** vs **corner skips** — coaches sell out one to steal the other.",
        ],
    )

    # Star pressure (woven into pressure card)
    star_pressure = _intel_variant(
        seed + "sp",
        [
            f"**{t_star}** carries your heaviest **trap/double** decisions when offense stalls; {O} lives with rotations if it means **contested twos**.",
            f"**{t_star}**'s **usage vs efficiency** trade is the emotional ride — {O} wants late clocks and **bodies at the level**.",
            f"The narrative pressure you feel on **{t_star}** is real because **{o_star}** is the clearest counter-star.",
        ],
    )

    sections = [
        ("1", "Key matchup advantage", "🏆", adv_body, "good", None),
        ("2", "Biggest tactical concern", "⚠️", concern_body, "warn", None),
        ("3", "X-factor player", "✨", x_body, "neutral", None),
        ("4", "Most important adjustment", "🧭", adj, "neutral", None),
        ("5", "Defensive matchup problems", "🛡️", def_body, "warn", None),
        ("6", "Momentum shift", "📈", mom_txt, mom_class, "momentum"),
        ("7", "Clutch-time edge", "⏱️", clutch, "neutral", None),
        ("8", "Pressure meter + star load", "🎯", f"**{p_label}** ({pressure}/100). {p_note} {star_pressure}", "neutral", None),
        ("9", "Coaching chess match", "♟️", chess, "neutral", None),
    ]
    meta = {
        "opp": opp,
        "round": rnd,
        "tw": tw,
        "ow": ow,
        "games_n": len(games),
        "mode": mode,
        "pressure": pressure,
    }
    return meta, sections


def _inject_matchup_intel_css():
    """MI styles use global fan CSS + team CSS variables."""
    return


def render_matchup_intelligence(team_name):
    _inject_matchup_intel_css()
    meta, payload = build_matchup_intelligence_sections(team_name)
    if meta is None:
        st.warning(payload)
        return
    render_mi_intelligence_hero(team_name, meta)
    prof = TEAM_PROFILES.get(team_name) or {}
    anchor = (prof.get("starters") or [None])[0]
    if anchor:
        sa = season_averages(anchor)
        render_player_fan_card(
            anchor,
            team_name,
            role=player_resume_profile(anchor, team_name).get("role", "Rotation"),
            stats={"PTS": sa.get("PTS", 0), "REB": sa.get("REB", 0), "AST": sa.get("AST", 0)},
        )
    for num, title, icon, body, tone, kind in payload:
        if kind == "momentum":
            cls = f"mi-mom-{tone}"
        else:
            cls = {
                "good": "mi-good",
                "warn": "mi-warn",
                "neutral": "mi-neutral",
                "up": "mi-mom-up",
                "down": "mi-mom-down",
                "flat": "mi-mom-flat",
            }.get(tone, "mi-neutral")
        safe_title = html.escape(f"{icon} {title}")
        # Allow bold markdown from body — convert ** to <strong> lightly
        b = str(body)
        b = html.escape(b)
        b = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", b)
        mom_pill = ""
        if kind == "momentum" and tone in ("up", "down", "flat"):
            lbl = {"up": "Swing up", "down": "Swing down", "flat": "Flat"}.get(tone, "")
            mom_pill = f'<span class="mi-mom-pill {tone}">{lbl}</span>'
        extra = ""
        if num == "8":
            pv = max(5, min(100, int(meta.get("pressure", 50))))
            extra = f'<div class="mi-bar" title="Fan stress meter for {html.escape(fan_nick(team_name))} (higher = heavier)"><span style="width:{pv}%"></span></div>'
        st.markdown(
            f"<div class='mi-card {cls}'><div class='mi-num'>SECTION {num}</div>"
            f"<div class='mi-title'>{safe_title}{mom_pill}</div><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )


# ==========================================================
# Rendering helpers
# ==========================================================
def render_matchup_header(team_name, first_round=False):
    p=TEAM_PROFILES[team_name]
    opp=p["first_round_opponent"] if first_round else (p.get("current_opponent") or p["first_round_opponent"])
    round_label="Previous Rounds / First Round Review" if first_round else p["round"]
    header=f"{p['conference']} {round_label}"
    oseed = TEAM_PROFILES.get(opp, {}).get("seed", "—")
    e = html.escape
    st.markdown(
        (
            '<div class="team-match-header"><div style="display:flex;align-items:center;'
            'justify-content:center;gap:20px;flex-wrap:wrap">'
            f'<img src="{e(TEAM_LOGOS[team_name])}" width="88" alt=""/>'
            "<div><h1>"
            f"({p['seed']}) {e(team_name)} <span style='opacity:.5'>vs</span> "
            f"({oseed}) {e(opp)}</h1>"
            f"<h3>{e(p['conference'])} · {e(round_label)}</h3></div>"
            f'<img src="{e(TEAM_LOGOS.get(opp, ""))}" width="88" alt=""/>'
            "</div></div>"
        ),
        unsafe_allow_html=True,
    )

def team_logo_html(team, size=28):
    return f"<img src='{TEAM_LOGOS[team]}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"


def team_section_header(title, icon="🏀"):
    """Colorful section divider using the active team palette."""
    safe = html.escape(str(title))
    st.markdown(f"<div class='team-sec'>{icon} {safe}</div>", unsafe_allow_html=True)


def player_fan_badges(summary, injury_status=None):
    """Return list of (label, css_class) for fan-facing player badges."""
    badges = []
    pts = safe_float(summary.get("PTS", 0))
    pm = safe_float(summary.get("PLUS_MINUS", 0))
    tov = safe_float(summary.get("TOV", 0))
    stl = safe_float(summary.get("STL", 0))
    blk = safe_float(summary.get("BLK", 0))
    gp = safe_float(summary.get("GP", 0))
    if injury_status:
        st_low = str(injury_status).lower()
        if any(x in st_low for x in ("out", "doubt", "question", "injur", "monitor")):
            badges.append(("Injury Watch", "injury"))
    if pts >= 28 or (pts >= 22 and pm >= 3):
        badges.append(("Hot", "hot"))
    if pm >= 5 and pts >= 14:
        badges.append(("Clutch", "clutch"))
    if (stl + blk) >= 2.5 or (pm >= 4 and pts >= 12):
        badges.append(("X-Factor", "xfactor"))
    if pm <= -4 or (pts >= 16 and pm <= -2):
        badges.append(("Needs Bounce Back", "bounce"))
    elif gp >= 3 and pts < 11:
        badges.append(("Needs Bounce Back", "bounce"))
    return badges


def render_player_fan_card(player_name, team_name, role="", stats=None, badges=None, injury_status=None):
    """Visual player card: headshot, logo, role, stat tiles, badges."""
    stats = stats or {}
    if badges is None:
        badges = player_fan_badges(stats, injury_status=injury_status)
    hs = headshot(player_name)
    logo = TEAM_LOGOS.get(team_name, "")
    role_txt = html.escape(role or "Rotation")
    badge_html = "".join(
        f"<span class='fan-badge {html.escape(cls)}'>{html.escape(lbl)}</span>" for lbl, cls in badges
    )
    tiles = []
    for key, label in (
        ("PTS", "PTS"),
        ("REB", "REB"),
        ("AST", "AST"),
        ("STL", "STL"),
        ("BLK", "BLK"),
        ("PLUS_MINUS", "+/-"),
    ):
        val = stats.get(key)
        if val is None or val == "":
            continue
        if key == "PLUS_MINUS":
            disp = f"{safe_float(val):+.1f}"
        elif isinstance(val, (int, float)):
            disp = f"{safe_float(val):.1f}" if key != "PTS" else f"{safe_float(val):.1f}"
        else:
            disp = html.escape(str(val))
        tiles.append(
            f"<div class='fan-stat-tile'><div class='v'>{disp}</div><div class='k'>{label}</div></div>"
        )
    tile_html = "".join(tiles) if tiles else "<span class='fan-player-role'>Stats load on demand</span>"
    st.markdown(
        f"""<div class='fan-player-card'>
  <img class='hs' src='{hs}' alt=''/>
  <div>
    <div class='fan-player-name'>{html.escape(player_name)}</div>
    <div class='fan-player-role'>{role_txt} · {html.escape(fan_nick(team_name))}</div>
    <div class='fan-stat-tiles'>{tile_html}</div>
    <div class='fan-badges'>{badge_html}</div>
  </div>
  <img class='logo' src='{logo}' alt=''/>
</div>""",
        unsafe_allow_html=True,
    )


def _stat_cell_class(col, val, wl=None):
    """CSS class for highlighted stat cells in fan tables."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    v = safe_float(val)
    c = str(col).upper()
    if c == "WL":
        s = str(val).upper()
        if s.startswith("W"):
            return "stat-good"
        if s.startswith("L"):
            return "stat-bad"
        return ""
    if c in ("PTS", "AST"):
        if v >= 28:
            return "stat-good"
        if v >= 18:
            return ""
        if v < 10:
            return "stat-bad"
    if c == "PLUS_MINUS":
        if v >= 8:
            return "stat-good"
        if v <= -6:
            return "stat-bad"
        if v <= -2:
            return "stat-warn"
    if c == "TOV" and v >= 5:
        return "stat-warn"
    if c in ("FG_PCT", "FG3_PCT", "FT_PCT"):
        pct = v * 100 if v <= 1.5 else v
        if pct >= 50:
            return "stat-good"
        if pct < 38:
            return "stat-bad"
    return ""


def render_fan_stat_table(df, team_name=None):
    """HTML stat table with alternating team-color rows and stat highlights."""
    if df is None or df.empty:
        st.caption("No rows to display.")
        return
    cols = list(df.columns)
    thead = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    body_rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        parity = "row-even" if i % 2 == 0 else "row-odd"
        cells = []
        for c in cols:
            raw = row.get(c, "")
            cls = _stat_cell_class(c, raw)
            if isinstance(raw, float):
                if str(c).upper() in ("FG_PCT", "FG3_PCT", "FT_PCT"):
                    disp = f"{raw * 100:.1f}%" if raw == raw else "—"
                elif str(c).upper() == "PLUS_MINUS":
                    disp = f"{raw:+.0f}" if raw == raw else "—"
                else:
                    disp = f"{raw:.1f}" if raw == raw else "—"
            else:
                disp = html.escape(str(raw))
            cells.append(f"<td class='{cls}'>{disp}</td>")
        body_rows.append(f"<tr class='{parity}'>" + "".join(cells) + "</tr>")
    st.markdown(
        f"<div class='fan-stat-table-wrap'><table class='fan-stat-table'><thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def render_fan_page_hero(team_name, title, subtitle="", badge_text=""):
    """Top-of-page hero with team logo and gradient (used across pages)."""
    e = html.escape
    logo = e(TEAM_LOGOS.get(team_name, ""))
    d = "div"
    badge_block = ""
    if badge_text:
        badge_block = (
            f"<{d} style='margin-top:8px'><span style='font-size:10px;font-weight:800;"
            f"padding:4px 10px;border-radius:999px;background:var(--team-accent-soft);"
            f"border:1px solid var(--team-border);color:#f8fafc'>{e(badge_text)}</span></{d}>"
        )
    st.markdown(
        f"<{d} class='live-fan-hero'>"
        f"<img src='{logo}' width='56' alt='' style='filter:drop-shadow(0 4px 14px rgba(0,0,0,.4))'/>"
        f"<{d} style='flex:1;min-width:200px'>"
        f"<{d} style='font-size:1.25rem;font-weight:900;margin:0 0 4px'>{e(title)}</{d}>"
        f"<{d} style='font-size:13px;color:#cbd5e1;line-height:1.45;margin:0'>{e(subtitle)}</{d}>"
        f"{badge_block}</{d}></{d}>",
        unsafe_allow_html=True,
    )


def render_mode_banner(team_name, kicker, body_html, variant="neutral"):
    """Compact team-tinted callout."""
    e = html.escape
    d = "div"
    st.markdown(
        f"<{d} class='mode-banner mode-banner--{e(variant)}'>"
        f"<{d} class='k'>{e(kicker)}</{d}>"
        f"<{d} class='b'>{body_html}</{d}></{d}>",
        unsafe_allow_html=True,
    )


def render_mi_intelligence_hero(team_name, meta):
    """Matchup Intelligence header with both team logos."""
    opp = meta.get("opp", "Opponent")
    e = html.escape
    d = "div"
    st.markdown(
        f"<{d} class='mi-wrap'><{d} class='mi-hero'>"
        f"<img class='logo' src='{e(TEAM_LOGOS.get(team_name, ''))}' alt=''/>"
        f"<{d} style='flex:1;min-width:180px'>"
        f"<{d} style='font-size:1.1rem;font-weight:900;margin:0'>"
        f"Your {e(fan_nick(team_name))} vs {e(fan_nick(opp))}</{d}>"
        f"<{d} style='font-size:13px;color:#94a3b8;margin-top:4px'>"
        f"{e(meta.get('round', 'Playoffs'))} · You at "
        f"<strong style='color:#fff'>{meta['tw']}-{meta['ow']}</strong>"
        f" · {meta['games_n']} games in log</{d}></{d}>"
        f"<img class='logo' src='{e(TEAM_LOGOS.get(opp, ''))}' alt=''/>"
        f"</{d}></{d}>",
        unsafe_allow_html=True,
    )


def render_live_score_banner(favorite_team, away_tri, home_tri, away_score, home_score, status, phase):
    """Team-colored live score strip for Live Game Center."""
    e = html.escape
    is_live = phase == "live"
    live_cls = " live" if is_live else ""
    fav_alias = TEAM_ALIASES.get(favorite_team, "")
    fav_side = "away" if away_tri == fav_alias else ("home" if home_tri == fav_alias else "watching")
    pill_live = " live" if is_live else ""
    d = "div"
    st.markdown(
        f"<{d} class='live-score-banner{live_cls}'>"
        f"<{d} style='font-size:11px;font-weight:800;letter-spacing:.14em;"
        f"text-transform:uppercase;color:var(--team-accent,#fde68a)'>"
        f"{'🔴 LIVE' if is_live else '📺 GAME BOARD'} · {e(fan_nick(favorite_team))}</{d}>"
        f"<{d} class='live-score-big'>{e(away_tri)} {away_score}  —  {e(home_tri)} {home_score}</{d}>"
        f"<{d} style='font-size:13px;color:#cbd5e1;margin-top:6px'>{e(status)}</{d}>"
        f"<{d} class='live-momentum'>"
        f"<span class='live-pill{pill_live}'>Your team ({fav_side})</span>"
        f"<span class='live-pill series'>Playoff companion</span></{d}></{d}>",
        unsafe_allow_html=True,
    )


# ==========================================================
# Next-round advancement helpers
# ==========================================================
def sibling_second_round_key(current_key, second_map):
    """The other second-round series in the same conference (dynamic bracket wiring)."""
    conf = second_map.get(current_key, {}).get("conf")
    if not conf:
        return None
    others = [k for k, s in second_map.items() if k != current_key and s.get("conf") == conf]
    return others[0] if len(others) == 1 else None


@st.cache_data(ttl=75)
def next_round_context_for_team(team_name):
    """Return next-round display context when the team's second-round series is complete
    but conference finals are not yet formed (waiting on the other conference semi).

    Once conference finals (or finals) exist for this team, returns None — the home
    header uses ``series_for_team`` directly for that matchup.
    """
    _, s_active = series_for_team(team_name)
    if s_active and s_active.get("round") in ("Conference Finals", "NBA Finals"):
        return None

    series_map = get_playoff_state_cached(bool(globals().get("USE_DEMO_BACKUP", False)))["second"]
    current_key = None
    current_series = None
    for key, series in series_map.items():
        if team_name in [series.get("a"), series.get("b")]:
            current_key = key
            current_series = series
            break
    if not current_series or not current_series.get("winner"):
        return None
    if current_series.get("winner") != team_name:
        return {
            "advanced": False,
            "eliminated": True,
            "round_label": "Eliminated",
            "opponents": [],
            "opponent_text": current_series.get("winner", "Opponent"),
            "status_text": f"{team_name} was eliminated by {current_series.get('winner')}.",
            "completed_series": current_series,
        }
    paired_key = sibling_second_round_key(current_key, series_map)
    paired = series_map.get(paired_key) if paired_key else None
    if not paired:
        return None
    conf = current_series.get("conf", "")
    round_label = "Eastern Conference Championship" if conf == "East" else "Western Conference Championship"
    if paired.get("winner"):
        opponents = [paired["winner"]]
        opponent_text = paired["winner"]
    else:
        opponents = [paired.get("a"), paired.get("b")]
        opponent_text = f"{paired.get('a')} / {paired.get('b')}"
    opponents = [op for op in opponents if op in TEAM_PROFILES]
    return {
        "advanced": True,
        "eliminated": False,
        "round_label": round_label,
        "opponents": opponents,
        "opponent_text": opponent_text,
        "status_text": f"{team_name} advances to the {round_label} vs {opponent_text}.",
        "completed_series": current_series,
        "paired_series": paired,
    }


def _build_local_series_shell(team_name):
    """Current playoff series view: prefer active second round (bundled/API merge), else first-round history."""
    second_map = get_playoff_state_cached(True).get("second") or {}
    for _k, s in second_map.items():
        if team_name in (s.get("a"), s.get("b")):
            return dict(s)

    for _key, s in FIRST_ROUND_SERIES.items():
        if team_name not in (s.get("a"), s.get("b")):
            continue
        a, b = s["a"], s["b"]
        games_raw = FIRST_ROUND_GAME_SCORES.get(team_name, [])
        games = []
        for idx, r in enumerate(games_raw, start=1):
            gn = r.get("Game", idx)
            if isinstance(gn, int):
                gn = f"Game {gn}"
            games.append({
                "Game": str(gn),
                "Date": str(r.get("Date", "")),
                "Score": str(r.get("Score", "")),
                "Winner": str(r.get("Winner", "")),
                "Matchup": str(r.get("Matchup", "")),
            })
        return {
            "conf": s.get("conf", ""),
            "round": "First Round",
            "a": a,
            "b": b,
            "a_wins": int(s.get("a_wins", 0)),
            "b_wins": int(s.get("b_wins", 0)),
            "winner": s.get("winner"),
            "games": games,
            "source": "Local FIRST_ROUND_SERIES",
        }

    return None


def get_fast_series_snapshot(team_name):
    """Lightweight series snapshot: TEAM_PROFILES + local/bundled series packs only (no network)."""
    profile = TEAM_PROFILES.get(team_name) or {}
    out = {
        "team_name": team_name,
        "opponent": profile.get("current_opponent") or profile.get("first_round_opponent"),
        "series_score": None,
        "round": profile.get("round", "Playoffs"),
        "latest_game": None,
        "source": "TEAM_PROFILES (local)",
    }
    s = _build_local_series_shell(team_name)
    if not s:
        out["series_score"] = "—"
        return out
    a, b = s["a"], s["b"]
    tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
    ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
    out["series_score"] = f"{tw}–{ow}"
    out["opponent"] = b if team_name == a else a
    out["round"] = s.get("round") or out["round"]
    gl = s.get("games") or []
    out["latest_game"] = gl[-1] if gl else None
    out["source"] = str(s.get("source") or "Local series pack")
    return out


def resolve_home_matchup_context_fast(team_name):
    """Home hub context without ``series_for_team`` / bracket builders (instant)."""
    profile = TEAM_PROFILES[team_name]
    s = _build_local_series_shell(team_name)
    snap = get_fast_series_snapshot(team_name)
    if s and s.get("round") in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return {
            "mode": "bracket_series",
            "series": s,
            "round_label": s.get("round"),
            "opponent": opp,
            "opponent_display": opp,
            "advanced": False,
            "bracket_series": True,
            "ctx": None,
            "fast_snapshot": snap,
        }
    opp = snap.get("opponent") or profile.get("current_opponent")
    return {
        "mode": "standard",
        "series": s,
        "round_label": snap.get("round") or profile.get("round", "Playoffs"),
        "opponent": opp,
        "opponent_display": opp,
        "advanced": False,
        "bracket_series": bool(s and s.get("round") == "Second Round"),
        "ctx": None,
        "fast_snapshot": snap,
    }


def resolve_home_matchup_context_impl(team_name):
    """Resolve current matchup / round for the Home Dashboard (no Streamlit output)."""
    profile = TEAM_PROFILES[team_name]
    _k, s = series_for_team(team_name)
    rnd = (s or {}).get("round", "")
    if s and rnd in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return {
            "mode": "bracket_series",
            "series": s,
            "round_label": rnd,
            "opponent": opp,
            "opponent_display": opp,
            "advanced": False,
            "bracket_series": True,
            "ctx": None,
        }
    ctx = next_round_context_for_team(team_name)
    if not ctx or not ctx.get("advanced"):
        opp = profile.get("current_opponent") or profile["first_round_opponent"]
        return {
            "mode": "standard",
            "series": s,
            "round_label": profile.get("round", "Playoffs"),
            "opponent": opp,
            "opponent_display": opp,
            "advanced": False,
            "bracket_series": False,
            "ctx": ctx,
        }
    return {
        "mode": "waiting_cf",
        "series": None,
        "round_label": ctx["round_label"],
        "opponent": None,
        "opponent_display": ctx.get("opponent_text", "TBD"),
        "opponents": ctx.get("opponents", []),
        "advanced": True,
        "bracket_series": False,
        "ctx": ctx,
    }


@st.cache_data(ttl=45)
def resolve_home_matchup_context_cached(team_name: str):
    """Home hub context — bracket shells + opponent fields rarely change minute-to-minute."""
    return resolve_home_matchup_context_impl(team_name)


def resolve_home_matchup_context(team_name):
    return resolve_home_matchup_context_cached(team_name)


# --- Home dashboard: team lens + playoff situation (dynamic ordering / copy) ---

TEAM_DASHBOARD_LENS = {
    "New York Knicks": {
        "hero_kicker": "Eastern bracket · Madison Square Garden playoff noise",
        "identity_axes": ("Brunson half-court engine", "Wing defense & physicality", "Extra possessions on the glass"),
        "pressure_axis": "Late-clock execution in a crowded East field",
        "flagship_hint": "Brunson",
        "legacy_weight": 1,
    },
    "Los Angeles Lakers": {
        "hero_kicker": "Championship window · Finals-orbit expectations",
        "identity_axes": ("LeBron's organizing load", "Anthony Davis rim pressure", "Role shooting around the stars"),
        "pressure_axis": "National spotlight on every closeout and every loss",
        "flagship_hint": "LeBron",
        "legacy_weight": 2,
    },
    "Oklahoma City Thunder": {
        "hero_kicker": "Young core runway · contender validation spring",
        "identity_axes": ("SGA's creation volume", "Defense-to-offense speed", "Depth that shrinks the floor in April"),
        "pressure_axis": "Proving the regular-season dominance holds under playoff tension",
        "flagship_hint": "Gilgeous",
        "legacy_weight": 1,
    },
    "Philadelphia 76ers": {
        "hero_kicker": "Embiid-era pressure · health and margin in the East",
        "identity_axes": ("Embiid interior gravity", "Maxey's speed in space", "Wing scoring around the hub"),
        "pressure_axis": "Every series is a referendum on ceiling when the big is on the floor",
        "flagship_hint": "Embiid",
        "legacy_weight": 1,
    },
    "Detroit Pistons": {
        "hero_kicker": "Young core breakthrough · playoff education in real time",
        "identity_axes": ("Cade's decision-making", "Athleticism on the wing", "Late-game poise under pressure"),
        "pressure_axis": "Learning how tight playoff possessions get against veteran teams",
        "flagship_hint": "Cunningham",
        "legacy_weight": 0,
    },
    "Cleveland Cavaliers": {
        "hero_kicker": "East firepower test · shot-making vs disciplined defense",
        "identity_axes": ("Mitchell's pull-up gravity", "Garland playmaking", "Mobley/Allen rim protection"),
        "pressure_axis": "Half-court scoring against set defenses in a long series",
        "flagship_hint": "Mitchell",
        "legacy_weight": 1,
    },
    "Minnesota Timberwolves": {
        "hero_kicker": "Western physicality · star shot-making in tight windows",
        "identity_axes": ("Edwards downhill pressure", "Gobert rim deterrence", "Spacing around the hub"),
        "pressure_axis": "Turning regular-season defense into repeatable playoff stops",
        "flagship_hint": "Edwards",
        "legacy_weight": 1,
    },
    "San Antonio Spurs": {
        "hero_kicker": "Wembanyama postseason debut · length as the series variable",
        "identity_axes": ("Victor's two-way rim influence", "Guard steadiness", "Turnover control vs pressure"),
        "pressure_axis": "Young legs learning how schemes tighten game to game",
        "flagship_hint": "Wembanyama",
        "legacy_weight": 1,
    },
}


def team_dashboard_lens(team_name):
    base = {
        "hero_kicker": "Playoff track · bracket context",
        "identity_axes": ("Half-court execution", "Defense on the ball", "Turnover margin"),
        "pressure_axis": "Every possession shrinks as the series deepens",
        "flagship_hint": None,
        "legacy_weight": 0,
    }
    if team_name in TEAM_DASHBOARD_LENS:
        base.update(TEAM_DASHBOARD_LENS[team_name])
    return base


def _dashboard_pick_flagship(profile, lens):
    hint = (lens.get("flagship_hint") or "").lower()
    starters = profile.get("starters") or []
    for n in starters:
        if hint and hint in n.lower():
            return n
    return starters[0] if starters else ""


def _dashboard_injury_signal(team_name, profile):
    df, _ = get_injury_report(team_name)
    if df is None or df.empty:
        return "low"
    starters = [str(x).lower() for x in (profile.get("starters") or [])[:6]]
    for _, r in df.iterrows():
        pl = str(r.get("Player", "")).lower()
        st = str(r.get("Status", "")).lower()
        if not starters or not any(s in pl or pl in s for s in starters):
            continue
        if any(x in st for x in ["out", "doubt", "question", "game time"]):
            return "high"
    return "elevated"


def _dashboard_injury_signal_fast(team_name, profile):
    """Ordering signal without ESPN — uses bundled fallback rows only (instant)."""
    fb_list = FALLBACK_INJURY_REPORT.get(team_name, []) or []
    starters = [str(x).lower() for x in (profile.get("starters") or [])[:6]]
    for row in fb_list:
        pl = str(row.get("Player", "")).lower()
        st = str(row.get("Status", "")).lower()
        if not starters or not any(s in pl or pl in s for s in starters):
            continue
        if any(x in st for x in ["out", "doubt", "question", "game"]):
            return "high"
    return "low"


def _dashboard_section_order(
    elimination_trailing,
    injury_level,
    phase_live,
    phase_post,
    pregame_soon,
    closeout_opportunity,
    danger_down_3,
    high_legacy,
):
    if phase_live:
        return ["snapshot", "next_game", "last_game", "injuries", "stars", "momentum", "legacy", "stories", "outlook"]
    if elimination_trailing:
        if injury_level == "high":
            return ["snapshot", "injuries", "stars", "momentum", "stories", "legacy", "next_game", "last_game", "outlook"]
        return ["snapshot", "stars", "injuries", "momentum", "stories", "legacy", "next_game", "last_game", "outlook"]
    if closeout_opportunity or phase_post:
        return ["snapshot", "momentum", "stories", "stars", "injuries", "legacy", "next_game", "last_game", "outlook"]
    if danger_down_3:
        return ["snapshot", "stories", "stars", "momentum", "injuries", "legacy", "next_game", "last_game", "outlook"]
    if injury_level == "high":
        return ["snapshot", "injuries", "stars", "momentum", "legacy", "next_game", "stories", "last_game", "outlook"]
    if pregame_soon:
        return ["snapshot", "next_game", "injuries", "stars", "momentum", "legacy", "stories", "last_game", "outlook"]
    if high_legacy:
        return ["snapshot", "legacy", "stars", "momentum", "injuries", "next_game", "stories", "last_game", "outlook"]
    return ["snapshot", "injuries", "stars", "momentum", "legacy", "next_game", "stories", "last_game", "outlook"]


def build_dashboard_playoff_context(team_name, hctx, series_board=None, skip_live_fetch=False):
    profile = TEAM_PROFILES[team_name]
    lens = team_dashboard_lens(team_name)
    if skip_live_fetch:
        fb = None
        live = None
    else:
        fb = featured_broadcast_state(team_name)
        live = None
        if isinstance(fb, dict) and fb.get("game"):
            live = fb["game"]
    s = hctx.get("series") or series_board
    mode = hctx.get("mode")
    tw = ow = 0
    opp = None
    last_winner = None
    games_played = 0
    series_winner = None
    rnd = profile.get("round", "Playoffs")
    if s:
        a, b = s["a"], s["b"]
        tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
        ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
        opp = b if team_name == a else a
        rnd = s.get("round") or rnd
        games_played = tw + ow
        games = s.get("games") or []
        last = games[-1] if games else None
        last_winner = last.get("Winner") if last else None
        series_winner = s.get("winner")

    elimination_trailing = bool(s and not series_winner and ow == 3 and tw < 4)
    closeout_opportunity = bool(s and not series_winner and tw == 3 and ow < 3)
    sweep_chance = bool(s and not series_winner and tw == 3 and ow == 0)
    danger_down_3 = bool(s and not series_winner and tw == 0 and ow == 3)
    deadlock = bool(s and not series_winner and tw == ow and tw >= 2)

    phase_live = bool(fb and fb.get("game") and fb.get("phase") == "live")
    phase_post = bool(fb and fb.get("game") and fb.get("phase") == "postgame")
    phase_pregame = bool(fb and fb.get("game") and fb.get("phase") == "pregame")
    pregame_soon = bool(fb and fb.get("starting_soon"))

    injury_level = _dashboard_injury_signal_fast(team_name, profile)
    flagship = _dashboard_pick_flagship(profile, lens)
    high_legacy = int(lens.get("legacy_weight") or 0) >= 2

    section_order = _dashboard_section_order(
        elimination_trailing=elimination_trailing,
        injury_level=injury_level,
        phase_live=phase_live,
        phase_post=phase_post,
        pregame_soon=pregame_soon,
        closeout_opportunity=closeout_opportunity,
        danger_down_3=danger_down_3,
        high_legacy=high_legacy,
    )

    return {
        "profile": profile,
        "lens": lens,
        "series": s,
        "tw": tw,
        "ow": ow,
        "opp": opp,
        "round": rnd,
        "last_winner": last_winner,
        "series_winner": series_winner,
        "games_played": games_played,
        "mode": mode,
        "elimination_trailing": elimination_trailing,
        "closeout_opportunity": closeout_opportunity,
        "sweep_chance": sweep_chance,
        "danger_down_3": danger_down_3,
        "deadlock": deadlock,
        "phase_live": phase_live,
        "phase_post": phase_post,
        "phase_pregame": phase_pregame,
        "pregame_soon": pregame_soon,
        "injury_level": injury_level,
        "flagship": flagship,
        "section_order": section_order,
        "fb": fb,
        "live": live,
        "team_name": team_name,
    }


def _dashboard_story_cards(team_name, pctx):
    nick = fan_nick(team_name)
    if _is_home_eliminated(team_name):
        od = get_offseason_outlook(team_name)
        d = od.get("direction") or {}
        tape = od["reflection"]["elimination_cause"]
        if len(tape) > 300:
            tape = tape[:297] + "…"
        pri2 = od["priorities"][1] if len(od.get("priorities", [])) > 1 else (od["priorities"][0] if od.get("priorities") else "Cap and roster alignment")
        return [
            ("Tape room", tape),
            ("Front-office lever", pri2),
            ("Franchise compass", f"{d.get('label', 'Direction')}: {d.get('blurb', '')}"),
        ]
    lens = pctx["lens"]
    ax = lens.get("identity_axes") or ("Execution", "Defense", "Margins")
    tw, ow = pctx["tw"], pctx["ow"]
    on = fan_nick(pctx["opp"]) if pctx["opp"] else "the opponent"
    rnd = pctx.get("round") or "this round"

    if pctx.get("phase_live"):
        return [
            ("Live board", f"The game is on the wire in real time — {nick} rotations and foul trouble matter immediately."),
            ("Tonight's lever", f"{ax[0]} is the cleanest path to controlling pace against {on}."),
            ("Series backdrop", f"The {tw}–{ow} {rnd} ledger still frames what a single night can rewrite."),
        ]
    if pctx.get("elimination_trailing"):
        return [
            ("Elimination math", f"At {tw}–{ow}, {nick} need a win to stay in the series — urgency is structural, not narrative."),
            ("Lineup stress", f"If {ax[1]} slips, the margin for error against {on} basically disappears."),
            ("Legacy texture", lens.get("pressure_axis", "Pressure rises with every empty possession.")),
        ]
    if pctx.get("sweep_chance"):
        return [
            ("Closeout sweep chance", f"Up 3–0, {nick} can end the series on the next clean night — {on} is playing from desperation."),
            ("Dominance check", f"{ax[2]} is how good teams turn a lead into a finished job without letting hope creep back."),
            ("Momentum carry", "A closeout win stacks confidence for the next round's prep window."),
        ]
    if pctx.get("closeout_opportunity"):
        return [
            ("Closeout opportunity", f"Match point territory at {tw}–{ow} — {nick} can punch the next round with one more disciplined night."),
            ("Control variables", f"{ax[0]} against set defenses is usually the swing skill when {on} has to gamble."),
            ("Noise level", lens.get("pressure_axis", "The outside temperature around the team rises whenever a series can end.")),
        ]
    if pctx.get("danger_down_3"):
        return [
            ("Steep hill", f"Down 0–3, {nick} need perfection in four straight — the opponent has room to play loose."),
            ("Supporting lift", f"When the headliners get extra attention, {ax[1]} from the next line matters more."),
            ("Possession quality", "Turnovers and transition defense become the fastest way the night gets away."),
        ]
    if pctx.get("deadlock"):
        return [
            ("Deadlocked series", f"Tied at {tw}–{ow}, {nick} and {on} are in a shot-quality and rebounding race."),
            ("Tactical depth", f"{rnd} tightens — {ax[2]} often decides who gets the extra clean look late."),
            ("Pressure axis", lens.get("pressure_axis", "Every game tilts the math for the rest of the series.")),
        ]
    if pctx.get("injury_level") == "high":
        return [
            ("Availability swing", "The injury board is flashing real rotation risk — substitution patterns can change matchups faster than a scheme tweak."),
            ("Next-man load", f"{ax[1]} from role players becomes a series variable when minutes shift."),
            ("Star burden", f"{ax[0]} has to stay efficient even when the defense loads extra help."),
        ]
    return [
        ("Pressure dial", f"{nick} in the {rnd}: {lens.get('pressure_axis', 'Every game is another proof point on the bracket.')}" ),
        (ax[0], f"How {nick} generate clean looks when {on} shrinks the floor is the recurring exam question."),
        (ax[2], "Second-chance points and transition defense are the quiet swing stats that show up in three-point margins."),
    ]


def _dashboard_emphasis_html(team_name, pctx):
    """Three HTML tiles under the hero: situation tag + identity axis + scoreboard."""
    esc = html.escape
    if _is_home_eliminated(team_name):
        od = get_offseason_outlook(team_name)
        cause = od["reflection"]["elimination_cause"]
        if len(cause) > 240:
            cause = cause[:237] + "…"
        pri = od["priorities"][0] if od.get("priorities") else "Roster and cap decisions"
        d = od.get("direction") or {}
        label = esc(str(d.get("label", "Offseason")))
        blurb = d.get("blurb", "")
        if len(blurb) > 200:
            blurb = blurb[:197] + "…"
        blurb_e = esc(blurb)
        tw, ow = pctx["tw"], pctx["ow"]
        on = esc(fan_nick(pctx["opp"])) if pctx.get("opp") else esc("opponent")
        return f"""<div class="cmd-emph-shell"><div class="cmd-emph-grid">
  <div class="cmd-emph-card"><div class="cmd-emph-k">POSTMORTEM</div><div class="cmd-emph-v">{esc(cause)}</div></div>
  <div class="cmd-emph-card"><div class="cmd-emph-k">OFFSEASON PRIORITY</div><div class="cmd-emph-v">{esc(pri)}</div><div class="cmd-emph-s">Tied to what broke in the playoff tape — not a generic checklist.</div></div>
  <div class="cmd-emph-card"><div class="cmd-emph-k">FRANCHISE COMPASS</div><div class="cmd-emph-v">{label}</div><div class="cmd-emph-s">{blurb_e}</div><div class="cmd-emph-s">Final ledger: {tw}–{ow} vs {on}</div></div>
</div></div>"""

    nick = esc(fan_nick(team_name))
    lens = pctx["lens"]
    ax = lens.get("identity_axes") or ("Execution", "Defense", "Margins")
    tw, ow = pctx["tw"], pctx["ow"]
    on = esc(fan_nick(pctx["opp"])) if pctx["opp"] else esc("the opponent")
    rnd = esc(str(pctx.get("round") or "Playoffs"))

    if pctx.get("phase_live"):
        tag, sub = "LIVE BOARD", "Rotation, fouls, and late-clock shot quality are moving in real time."
    elif pctx.get("elimination_trailing"):
        tag, sub = f"MUST-WIN · {tw}–{ow}", "The series only extends with a win — empty possessions cost twice."
    elif pctx.get("sweep_chance"):
        tag, sub = "SWEEP WINDOW", f"3–0 leverage — {on} is one loss from an early summer."
    elif pctx.get("closeout_opportunity"):
        tag, sub = f"MATCH POINT · {tw}–{ow}", "A disciplined close can end the series and bank rest before the next round."
    elif pctx.get("danger_down_3"):
        tag, sub = "BRACKET HOLE · 0–3", "The comeback path requires four perfect nights in a row."
    elif pctx.get("injury_level") == "high":
        tag, sub = "AVAILABILITY SWING", "Starter-level tags on the report — substitution patterns can flip matchups fast."
    else:
        tag = "SERIES TEMPO"
        sub = f"{fan_nick(team_name)} · {pctx.get('round') or 'Playoffs'} — {lens.get('pressure_axis', 'Pressure tightens as the bracket advances.')}"

    a0, a1, a2 = esc(ax[0]), esc(ax[1]) if len(ax) > 1 else "", esc(ax[2]) if len(ax) > 2 else ""
    hot = " cmd-emph-card--hot" if (pctx.get("phase_live") or pctx.get("elimination_trailing") or pctx.get("danger_down_3")) else ""
    return f"""<div class="cmd-emph-shell"><div class="cmd-emph-grid">
  <div class="cmd-emph-card{hot}"><div class="cmd-emph-k">{esc(tag)}</div><div class="cmd-emph-v">{esc(sub)}</div></div>
  <div class="cmd-emph-card"><div class="cmd-emph-k">Identity lever</div><div class="cmd-emph-v">{a0}</div><div class="cmd-emph-s">{a1}</div></div>
  <div class="cmd-emph-card"><div class="cmd-emph-k">Series board</div><div class="cmd-emph-v">{tw}–{ow} vs {on}</div><div class="cmd-emph-s">{a2}</div></div>
</div></div>"""


def _inject_home_command_center_css():
    st.markdown(
        """
<style>
.cmd-emph-shell { max-width: 1200px; margin: 0 auto 14px auto; }
.cmd-emph-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
.cmd-emph-card {
  border-radius: 14px; padding: 12px 14px; border: 1px solid rgba(148,163,184,0.35);
  background: rgba(15,23,42,0.55); color: #e2e8f0;
}
.cmd-emph-card--hot { border-color: rgba(248,113,113,0.55); background: linear-gradient(135deg, rgba(127,29,29,0.35), rgba(15,23,42,0.85)); }
.cmd-emph-k { font-size: 10px; font-weight: 900; letter-spacing: 0.14em; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px; }
.cmd-emph-v { font-size: 14px; font-weight: 800; color: #f8fafc; line-height: 1.35; }
.cmd-emph-s { font-size: 12px; color: #94a3b8; margin-top: 6px; line-height: 1.35; }
.cmd-shell { max-width: 1200px; margin: 0 auto 8px auto; }
.cmd-hero {
  position: relative;
  border-radius: 20px;
  padding: 20px 18px 18px;
  margin-bottom: 14px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 18px 48px rgba(0,0,0,0.45);
  background: radial-gradient(120% 80% at 10% 0%, rgba(255,255,255,0.07) 0%, transparent 55%),
    linear-gradient(145deg, var(--cmd-bg0,#0b1220) 0%, var(--cmd-bg1,#111827) 45%, #0f172a 100%);
}
.cmd-hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, transparent 38%);
}
.cmd-hero-inner { position: relative; z-index: 1; color: #f8fafc; font-family: system-ui,-apple-system,sans-serif; }
.cmd-kicker { font-size: 11px; font-weight: 800; letter-spacing: 0.2em; text-transform: uppercase; color: #94a3b8; text-align: center; margin-bottom: 8px; }
.cmd-row { display: flex; align-items: center; justify-content: space-between; gap: 16px 24px; flex-wrap: wrap; }
.cmd-logo { width: clamp(72px, 14vw, 112px); height: auto; filter: drop-shadow(0 6px 18px rgba(0,0,0,0.55)); }
.cmd-vs { font-size: 13px; font-weight: 900; color: #64748b; letter-spacing: 0.12em; }
.cmd-center { text-align: center; min-width: min(100%, 260px); flex: 1 1 240px; }
.cmd-opp-logos { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 10px; min-width: 72px; }
.cmd-match { font-size: clamp(1.15rem, 3.2vw, 1.75rem); font-weight: 900; line-height: 1.15; margin: 0 0 6px; }
.cmd-round { display: inline-block; font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); color: #e2e8f0; margin-bottom: 8px; }
.cmd-scoreline { font-size: clamp(1.6rem, 4vw, 2.35rem); font-weight: 950; color: #fbbf24; letter-spacing: 0.06em; margin: 4px 0 10px; }
.cmd-rail { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 4px; }
.cmd-pill { font-size: 11px; font-weight: 800; padding: 5px 11px; border-radius: 999px; background: rgba(15,23,42,0.55); border: 1px solid rgba(148,163,184,0.35); color: #e2e8f0; }
.cmd-pill--accent { border-color: var(--cmd-accent, #38bdf8); color: #f0f9ff; background: var(--cmd-accent-soft, rgba(56,189,248,0.15)); }
.cmd-headline { text-align: center; font-size: 15px; font-weight: 800; color: #f1f5f9; margin: 12px auto 0; max-width: 38rem; line-height: 1.35; }
.cmd-inj { margin-top: 12px; font-size: 11px; color: #cbd5e1; text-align: center; line-height: 1.45; }
.cmd-sec { margin: 18px 0 8px; font-size: 13px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; border-bottom: 1px solid rgba(148,163,184,0.25); padding-bottom: 6px; }
.cmd-tile { background: rgba(15,23,42,0.55); border: 1px solid rgba(71,85,105,0.45); border-radius: 14px; padding: 10px 12px; text-align: center; }
.cmd-tile .v { font-size: 1.35rem; font-weight: 900; color: #f8fafc; }
.cmd-tile .k { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.cmd-next { background: rgba(15,23,42,0.45); border-radius: 14px; padding: 12px 14px; border: 1px solid rgba(71,85,105,0.4); margin-bottom: 12px; }
.cmd-next-title { font-size: 12px; font-weight: 800; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.cmd-grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; }
.home-live-strip {
  max-width: 1200px; margin: 0 auto 14px auto; border-radius: 16px; padding: 14px 16px;
  border: 1px solid rgba(148,163,184,0.45); background: rgba(15,23,42,0.65);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
}
.home-live-strip--live {
  border-color: rgba(248,113,113,0.75);
  background: linear-gradient(125deg, rgba(127,29,29,0.55) 0%, rgba(15,23,42,0.9) 55%, rgba(15,23,42,0.95) 100%);
  animation: homeLivePulse 2.4s ease-in-out infinite;
}
.home-live-strip--soon {
  border-color: rgba(251,191,36,0.65);
  background: linear-gradient(125deg, rgba(120,53,15,0.35) 0%, rgba(15,23,42,0.92) 100%);
}
.home-live-strip--post {
  border-color: rgba(56,189,248,0.45);
  background: linear-gradient(125deg, rgba(12,74,110,0.35) 0%, rgba(15,23,42,0.92) 100%);
}
@keyframes homeLivePulse {
  0%, 100% { box-shadow: 0 12px 40px rgba(220,38,38,0.25); }
  50% { box-shadow: 0 14px 48px rgba(248,113,113,0.45); }
}
.home-live-strip-title { font-size: 13px; font-weight: 900; letter-spacing: 0.14em; text-transform: uppercase; color: #fecaca; margin-bottom: 6px; }
.home-live-strip--soon .home-live-strip-title { color: #fde68a; }
.home-live-strip--post .home-live-strip-title { color: #bae6fd; }
.home-live-strip-score { font-size: 1.5rem; font-weight: 950; color: #f8fafc; letter-spacing: 0.04em; }
.home-live-strip-sub { font-size: 13px; color: #cbd5e1; margin-top: 4px; line-height: 1.35; }
@media (max-width: 700px) {
  .cmd-row { flex-direction: column; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def _home_storyline_headline(team_name, hctx, pctx=None):
    """Hero headline: situation-first copy for the selected team (no 'fan perspective' phrasing)."""
    profile = TEAM_PROFILES[team_name]
    s = hctx.get("series")
    mode = hctx.get("mode")
    nick = fan_nick(team_name)
    lens = (pctx or {}).get("lens") or team_dashboard_lens(team_name)
    pa = lens.get("pressure_axis", "")

    if mode == "waiting_cf" and hctx.get("ctx"):
        return hctx["ctx"].get(
            "status_text",
            f"{nick} cleared the second round while the other semi finishes — the bracket names the next matchup.",
        )
    if not s:
        if profile.get("status") == "Eliminated":
            return f"The postseason run stopped for {nick} — the tape and box scores still carry the story of how it broke."
        return f"{nick} are queued for the next bracket update — the schedule feed still decides when the next chapter opens."

    rnd = s.get("round", "Playoffs")
    a, b = s["a"], s["b"]
    tw = s["a_wins"] if team_name == a else s["b_wins"]
    ow = s["b_wins"] if team_name == a else s["a_wins"]
    opp = b if team_name == a else a
    on = fan_nick(opp)
    last = (s.get("games") or [])[-1] if s.get("games") else None
    lw = last.get("Winner") if last else None

    if s.get("winner") == team_name:
        return f"Series closed: {nick} finish {tw}–{ow} over {on} — the bracket moves on, and this series goes into the yearbook."
    if s.get("winner") and s.get("winner") != team_name:
        return f"{fan_nick(s['winner'])} ends the line here — the offseason questions start with health, roster, and what the film says about {tw}–{ow}."

    if pctx:
        if pctx.get("phase_live"):
            return f"Live board for {nick}: rotations, foul trouble, and late-clock shot quality are moving the {rnd} ledger in real time."
        if pctx.get("elimination_trailing"):
            return f"Must-win night at {tw}–{ow} for {nick} — {on} can close the series; empty possessions cost double."
        if pctx.get("danger_down_3"):
            return f"Down 0–3, {nick} need four straight clean performances while {on} plays with house money."
        if pctx.get("sweep_chance"):
            return f"At 3–0, {nick} can end the series with disciplined execution and force {on} into desperation answers."
        if pctx.get("closeout_opportunity"):
            return f"Match-point territory at {tw}–{ow} for {nick} — one more controlled night banks rest before the next round."
        if pctx.get("injury_level") == "high" and pctx.get("phase_pregame"):
            return f"Pregame availability noise is loud for {nick} — substitution patterns may matter as much as the first play call."

    if tw == ow and tw >= 1:
        return f"Deadlocked {tw}–{ow} with {on} in the {rnd} — {pa or 'Shot quality and rebounding margin decide who seizes the next swing game.'}"
    if lw == team_name and last:
        return f"{nick} took the last one ({last.get('Score','')}) — the chess match with {on} shifts toward whatever worked late."
    if lw and lw != team_name:
        return f"{on} answered last — {nick} need a cleaner opening stretch before the game tightens late."
    if "Final" in rnd or ("Conference" in rnd and "First" not in rnd):
        return f"{rnd}: {nick} vs {on} at {tw}–{ow} — {pa or 'The stakes rise with every night left on the schedule.'}"
    return f"{nick} vs {on}, {tw}–{ow} in the {rnd} — {pa or 'The next result still redraws the series map.'}"


def _home_series_win_probability(team_name, hctx, live):
    """Return integer 0-100 for favorite team; uses live win_prob when in-game."""
    s = hctx.get("series")
    if live:
        home = live.get("homeTeam", {}) or {}
        away = live.get("awayTeam", {}) or {}
        home_tri = home.get("teamTricode", "") or ""
        away_tri = away.get("teamTricode", "") or ""
        alias = TEAM_ALIASES.get(team_name, "")
        is_home = home_tri == alias
        hs, as_ = safe_int(home.get("score", 0)), safe_int(away.get("score", 0))
        margin = (hs - as_) if is_home else (as_ - hs)
        period = safe_int(live.get("period", 0), 0)
        eff_p = max(1, min(4, period)) if period else 1
        phase = _live_broadcast_phase(live)
        if phase == "postgame":
            return 100 if margin > 0 else (0 if margin < 0 else 50)
        if phase == "live":
            return int(win_prob(margin, eff_p, is_home))
        if phase == "pregame":
            return 50
    if not s:
        return 50
    if s.get("winner") == team_name:
        return 100
    if s.get("winner"):
        return 22
    a, b = s["a"], s["b"]
    tw = int(s.get("a_wins", 0) if team_name == a else s.get("b_wins", 0))
    ow = int(s.get("b_wins", 0) if team_name == a else s.get("a_wins", 0))
    diff = tw - ow
    games_played = tw + ow
    base = 50 + diff * 11 + (3 if games_played >= 4 else 0)
    return int(max(12, min(88, base)))


def _home_injury_hero_snippet(team_name, use_live_feed=True):
    """Hero injury line. Live ESPN merge only when ``use_live_feed`` (after user opts in)."""
    if use_live_feed:
        df, _ = get_injury_report(team_name)
        if df is None or df.empty:
            return (
                f"Injury feed for {html.escape(fan_nick(team_name))} loads when available — "
                f"use <strong>Load live API updates</strong> or open <strong>Injury Report</strong> below."
            )
        row = df.iloc[0]
        return (
            f"<strong>{html.escape(team_name)}</strong>: {html.escape(str(row.get('Player', '?')))} "
            f"<span style='opacity:.85'>({html.escape(str(row.get('Status', '?')))})</span>"
        )
    fb_list = FALLBACK_INJURY_REPORT.get(team_name, []) or []
    if not fb_list:
        return (
            "Bundled injury rows not loaded for this team — "
            "<strong>Load live API updates</strong> or open <strong>Injury Report</strong> for ESPN data."
        )
    row = fb_list[0]
    return (
        f"<strong>{html.escape(team_name)}</strong> (bundled): {html.escape(str(row.get('Player', '?')))} "
        f"<span style='opacity:.85'>({html.escape(str(row.get('Status', '?')))})</span>"
    )


def _home_command_center_hero_html(team_name, hctx, pctx=None, injury_use_live=True):
    if pctx is None:
        pctx = build_dashboard_playoff_context(
            team_name, hctx, None, skip_live_fetch=not injury_use_live
        )
    pal = live_hero_palette(team_name)
    esc = html.escape
    profile = TEAM_PROFILES[team_name]
    offseason = _is_home_eliminated(team_name)
    s = hctx.get("series") or (pctx.get("series") if pctx else None)
    live = pctx.get("live")
    fb = pctx.get("fb")
    prob = _home_series_win_probability(team_name, hctx, live)
    prob_display = f"{prob}%"
    headline = _home_storyline_headline(team_name, hctx, pctx)
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    kicker_dom = f"{esc(lens.get('hero_kicker', 'Playoff command center'))} · {esc(fan_nick(team_name))}"
    if offseason:
        kicker_dom = f"OFFSEASON OUTLOOK · {esc(fan_nick(team_name))}"
    inj = _home_injury_hero_snippet(team_name, use_live_feed=injury_use_live)
    if offseason:
        inj = esc(
            "Summer health and availability still swing extension and trade math — open Injury Report below if you want the detailed board."
        )
    left_logo = TEAM_LOGOS.get(team_name, "")

    if hctx.get("mode") == "waiting_cf":
        parts = []
        for op in (hctx.get("opponents") or [])[:2]:
            u = TEAM_LOGOS.get(op, "")
            if u:
                parts.append(f"<img class='cmd-logo' src='{esc(u)}' alt=''/>")
        if not parts:
            parts.append(
                "<span style='font-size:12px;color:#94a3b8;font-weight:700'>TBD</span>"
            )
        right_html = f"<div class='cmd-opp-logos'>{''.join(parts)}</div>"
        matchup = (
            f"{esc(team_name)} <span style='opacity:.55'>vs</span> "
            f"{esc(hctx.get('opponent_display', 'TBD'))}"
        )
        score_txt = "Series TBD"
        rnd = esc(hctx.get("round_label", "Playoffs"))
    else:
        opp = hctx.get("opponent") or profile.get("current_opponent") or "TBD"
        ologo = TEAM_LOGOS.get(opp, "")
        right_html = (
            f"<div class='cmd-opp-logos'><img class='cmd-logo' src='{esc(ologo)}' alt=''/></div>"
        )
        matchup = (
            f"({profile['seed']}) {esc(team_name)} <span style='opacity:.55'>vs</span> "
            f"({TEAM_PROFILES.get(opp, {}).get('seed', '—')}) {esc(opp)}"
        )
        if s and not s.get("winner"):
            a, b = s["a"], s["b"]
            tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
            ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
            score_txt = f"{tw}–{ow}"
        elif s and s.get("winner"):
            a, b = s["a"], s["b"]
            tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
            ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
            score_txt = f"Final {tw}–{ow}"
        else:
            score_txt = "—"
        rnd = esc(
            (s or {}).get("round")
            or hctx.get("round_label")
            or profile.get("round", "Playoffs")
        )
        if offseason:
            rnd = esc("First round · complete — offseason mode")

    next_line = ""
    if live:
        stt = live.get("gameStatusText", "") or ""
        hs = live.get("homeTeam") or {}
        aw = live.get("awayTeam") or {}
        if not isinstance(hs, dict):
            hs = {}
        if not isinstance(aw, dict):
            aw = {}
        next_line = (
            f"{esc(_live_team_full_name(aw.get('teamTricode', ''), aw))} @ "
            f"{esc(_live_team_full_name(hs.get('teamTricode', ''), hs))} · "
            f"{esc(stt[:48])}"
        )
        if fb and fb.get("game") and fb.get("phase") == "pregame":
            sec = fb.get("seconds_to_tip")
            if sec is not None and sec > 0:
                sec = int(sec)
                next_line += f" · Tip window ≈ {sec // 60}m {sec % 60}s"
    else:
        next_line = (
            f"Next on the slate: {esc(fan_nick(team_name))} vs "
            f"{esc(hctx.get('opponent_display', profile.get('current_opponent') or 'opponent TBA'))} "
            f"— tip data when NBA schedule loads."
        )
    if offseason:
        res = profile.get("first_round_result") or "Series complete"
        next_line = (
            f"{esc(res)} — The runway is now the front office: roster fit, picks, extensions, "
            f"and how {esc(fan_nick(team_name))} close the gap in a loaded conference."
        )

    pulse = "Next tip tracking"
    prob_lab = "Tilt meter"
    if fb and fb.get("game"):
        ph = fb.get("phase")
        if ph == "live":
            pulse = "🔴 LIVE — broadcast hub hot"
            prob_lab = "Live game tilt"
        elif fb.get("starting_soon"):
            pulse = "⏳ Starting soon (~1h window)"
            prob_lab = "Series / runway tilt"
        elif ph == "pregame":
            pulse = "📅 Pregame board loaded"
            prob_lab = "Series tilt"
        elif ph == "postgame":
            pulse = "📼 Final — full wrap in hub"
            prob_lab = "Tonight's result tilt"

    if offseason:
        pulse = "Draft · cap · trade board"
        prob_lab = "Playoff ledger"
        prob_display = "closed"

    next_title = "What's next" if offseason else "Next game"

    return f"""
<div class="cmd-shell" style="--cmd-bg0:{pal['bg0']};--cmd-bg1:{pal['bg1']};--cmd-accent:{pal['accent']};--cmd-accent-soft:{pal['accent_soft']};">
<div class="cmd-hero">
  <div class="cmd-hero-inner">
    <div class="cmd-kicker">{kicker_dom}</div>
    <div class="cmd-row">
      <img class="cmd-logo" src="{esc(left_logo)}" alt=""/>
      <div class="cmd-center">
        <div class="cmd-round">{rnd}</div>
        <div class="cmd-match">{matchup}</div>
        <div class="cmd-scoreline">{score_txt}</div>
        <div class="cmd-rail">
          <span class="cmd-pill cmd-pill--accent">{esc(prob_lab)} · {esc(prob_display)}</span>
          <span class="cmd-pill">{esc(pulse)}</span>
        </div>
      </div>
      {right_html}
    </div>
    <div class="cmd-headline">{esc(headline)}</div>
    <div class="cmd-inj">🩹 {inj}</div>
    <div class="cmd-next" style="margin-top:14px">
      <div class="cmd-next-title">{esc(next_title)}</div>
      <div style="font-size:14px;font-weight:700;color:#e2e8f0">{next_line}</div>
    </div>
  </div>
</div>
</div>
"""

def render_home_live_hub_strip(team_name, fb_prefetched=None):
    """Home strip when a merged playoff-window game exists (live / soon / final).

    Pass ``fb_prefetched`` from ``pctx[\"fb\"]`` on Home to avoid a second scoreboard merge.
    """
    fb = fb_prefetched if fb_prefetched is not None else featured_broadcast_state(team_name)
    if fb and fb.get("game"):
        g = fb["game"]
        phase = fb["phase"]
        sec = fb.get("seconds_to_tip")
        soon = fb.get("starting_soon")
        home = g.get("homeTeam", {}) or {}
        away = g.get("awayTeam", {}) or {}
        away_n = _live_team_full_name(_tricode_from_team_dict(away) or away.get("teamTricode", ""), away)
        home_n = _live_team_full_name(_tricode_from_team_dict(home) or home.get("teamTricode", ""), home)
        hs = safe_int(home.get("score", 0))
        aws = safe_int(away.get("score", 0))
        stt = (g.get("gameStatusText") or "")[:56]
        nick = fan_nick(team_name)
        if phase == "live":
            mod = "home-live-strip home-live-strip--live"
            title = "🔴 LIVE NOW · Game in progress"
        elif phase == "pregame" and soon:
            mod = "home-live-strip home-live-strip--soon"
            title = "⏳ GAME STARTING SOON"
        elif phase == "postgame":
            mod = "home-live-strip home-live-strip--post"
            title = "📼 FINAL IN THE FEED"
        else:
            mod = "home-live-strip"
            title = "📅 PREGAME BOARD LOADED"
        sub_bits = [f"{html.escape(away_n)} @ {html.escape(home_n)}"]
        if stt:
            sub_bits.append(html.escape(stt))
        if sec is not None and sec > 0 and phase == "pregame":
            mm, ss = int(sec // 60), int(sec % 60)
            sub_bits.append(f"Tip window ≈ {mm}m {ss}s on the studio clock")
        sub = " · ".join(sub_bits)
        score_line = f"{aws} — {hs}" if phase != "pregame" or (aws + hs) > 0 else "0 — 0"
        st.markdown(
            f"""
<div class="{mod}">
  <div class="home-live-strip-title">{title}</div>
  <div class="home-live-strip-score">{html.escape(score_line)}</div>
  <div class="home-live-strip-sub">{sub}</div>
  <div style="margin-top:10px;font-size:12px;color:#94a3b8">Go to <b>Live Game Center</b> for lineups, injuries, momentum, and the full broadcast layout for {html.escape(nick)}.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        label = "Go to Live Game Center"
        if phase == "live":
            label = "🏀 Live Game Center — LIVE NOW"
        elif phase == "pregame" and soon:
            label = "🏀 Live Game Center — starting soon"
        elif phase == "postgame":
            label = "🏀 Live Game Center — wrap & series"
        if st.button(label, key="home_strip_open_live"):
            st.session_state["page_override"] = "🏀 Live Game Center"
            st.rerun()
        return

    # No merged game row: skip scoreboard detection here (avoids blocking Home on NBA hub calls).
    # Live Game Center still runs full detection when the user opens it.


HOME_DASH_LIVE_UPDATES = "home_dash_live_updates"
HOME_DASH_LOAD_INJ = "home_dash_load_inj"
HOME_DASH_LOAD_STARS = "home_dash_load_stars"
HOME_DASH_LOAD_LEGACY = "home_dash_load_legacy"


def _home_dashboard_fast_context(team_name):
    """Instant Home context (local series shell + no live scoreboard fetch)."""
    hctx = resolve_home_matchup_context_fast(team_name)
    s_active = _build_local_series_shell(team_name)
    pctx = build_dashboard_playoff_context(team_name, hctx, s_active, skip_live_fetch=True)
    return hctx, s_active, pctx


def _home_dashboard_live_data_bundle(team_name):
    """Network-heavy context for Home — resolve matchup + series in parallel, then merge scoreboard."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fh = ex.submit(resolve_home_matchup_context, team_name)
        fs = ex.submit(lambda: series_for_team(team_name))
        hctx = fh.result(timeout=3.5)
        _k, s_active = fs.result(timeout=3.5)
    pctx = build_dashboard_playoff_context(team_name, hctx, s_active, skip_live_fetch=False)
    return hctx, s_active, pctx


def _home_dashboard_perf_footer(t0, sections, fast_mode, api_calls, skipped_note=""):
    elapsed_ms = (pytime.perf_counter() - t0) * 1000
    sec_txt = " → ".join(sections) if sections else "(none)"
    st.markdown(
        "<div style='margin-top:16px;padding:12px 14px;border-radius:12px;border:1px solid rgba(148,163,184,0.35);"
        "background:rgba(15,23,42,0.45);font-size:13px;color:#e2e8f0;line-height:1.5'>"
        f"<div style='font-weight:800;margin-bottom:6px;color:#94a3b8;text-transform:uppercase;font-size:11px;letter-spacing:0.12em'>"
        f"Performance debug</div>"
        f"<div><strong>Page render time</strong>: {elapsed_ms:.0f} ms</div>"
        f"<div><strong>Fast mode</strong>: {'yes (no automatic NBA/ESPN fan-out)' if fast_mode else 'no (live API bundle)'}</div>"
        f"<div><strong>API-style calls (this run)</strong>: {html.escape(str(api_calls))}</div>"
        f"<div><strong>Sections touched</strong>: {html.escape(sec_txt)}</div>"
        f"{skipped_note}"
        "</div>",
        unsafe_allow_html=True,
    )


def render_playoff_command_center(team_name):
    t0 = pytime.perf_counter()
    sections = []
    st.session_state.setdefault(HOME_DASH_LIVE_UPDATES, False)
    live_on = bool(st.session_state.get(HOME_DASH_LIVE_UPDATES, False))
    is_eliminated = _is_home_eliminated(team_name)
    if is_eliminated and st.session_state.get(HOME_DASH_LIVE_UPDATES):
        st.session_state[HOME_DASH_LIVE_UPDATES] = False
        live_on = False
    effective_live = live_on and not is_eliminated

    render_fan_page_hero(team_name, f"{fan_nick(team_name)} Home Dashboard", "Series snapshot, injuries, stars, and offseason outlook when the run is over.", "YOUR TEAM")
    if not is_eliminated:
        with st.expander("Looking for offseason / future outlook sections?", expanded=False):
            st.markdown(
                "Those **six analysis blocks** (season reflection, priorities, future outlook, draft assets, "
                "players who may not return, ideal player types) **only show for eliminated teams**.\n\n"
                "**What to do:** in the **sidebar**, open the team dropdown and pick any roster labeled "
                "**(offseason view)**. That label is driven by the **playoff bracket**: any team that lost a "
                "**completed** series (4–0 through 4–3) in **any round** — e.g. an early exit like **Boston** or **Phoenix**, "
                "or a later one like **Philadelphia**, the **Lakers**, or **Cleveland** if their series is over — "
                "shows that tag automatically.\n\n"
                "Then stay on **🏀 Home Dashboard**: the gold **Postmortem** banner and sections appear **directly under** "
                "the Load live / Fast mode buttons, **above** the big hero card."
            )
    if is_eliminated:
        st.success(
            f"**{fan_nick(team_name)}** — offseason / future outlook mode is on. Scroll for the gold **Postmortem** header and six analysis sections directly below the controls."
        )
    b1, b2, b3 = st.columns([1.35, 1.35, 1.1])
    with b1:
        if is_eliminated:
            st.caption(
                "Live playoff API bundle is hidden for eliminated teams — open **Live Game Center** from the sidebar for league-wide games."
            )
        elif st.button("Load live API updates", key="home_btn_live_apis", disabled=live_on, help="Scoreboard merge, ESPN injuries, and full bracket APIs"):
            st.session_state[HOME_DASH_LIVE_UPDATES] = True
            st.rerun()
    with b2:
        if st.button("Instant dashboard (fast mode)", key="home_btn_fast_mode", disabled=not live_on):
            st.session_state[HOME_DASH_LIVE_UPDATES] = False
            st.session_state.pop(HOME_DASH_LOAD_INJ, None)
            st.session_state.pop(HOME_DASH_LOAD_STARS, None)
            st.session_state.pop(HOME_DASH_LOAD_LEGACY, None)
            st.rerun()
    with b3:
        st.caption("⚡ Fast" if not live_on else "📡 Live")

    _inject_home_command_center_css()
    sections.append("inject_css")

    if is_eliminated:
        render_offseason_future_outlook_sections(team_name)
        sections.append("offseason_outlook_top")

    api_calls = 0
    skip_note = ""

    fast_hctx, fast_s, fast_p = _home_dashboard_fast_context(team_name)
    hero_slot = st.empty()
    emph_slot = st.empty()
    hero_slot.markdown(
        _home_command_center_hero_html(team_name, fast_hctx, fast_p, injury_use_live=False),
        unsafe_allow_html=True,
    )
    emph_slot.markdown(_dashboard_emphasis_html(team_name, fast_p), unsafe_allow_html=True)
    sections.append("hero_first_paint")

    hctx, s_active, pctx = fast_hctx, fast_s, fast_p
    injury_live = False

    if effective_live:
        sections.append("live_bundle_start")
        bundle = None
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            fut = ex.submit(_home_dashboard_live_data_bundle, team_name)
            bundle = fut.result(timeout=8.0)
        except concurrent.futures.TimeoutError:
            bundle = None
            skip_note = (
                "<div style='margin-top:8px;color:#fca5a5'><strong>Live data skipped to keep dashboard fast.</strong> "
                "The live bundle did not finish within 8 seconds — showing cached/local hero above.</div>"
            )
        except Exception as exc:
            bundle = None
            skip_note = (
                "<div style='margin-top:8px;color:#fca5a5'><strong>Live data skipped to keep dashboard fast.</strong> "
                f"{html.escape(repr(exc))}</div>"
            )
        finally:
            try:
                ex.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                ex.shutdown(wait=False)

        if bundle is None:
            st.session_state[HOME_DASH_LIVE_UPDATES] = False
            live_on = False
            injury_live = False
            sections.append("live_bundle_failed")
        else:
            hctx, s_active, pctx = bundle
            api_calls = 1
            injury_live = True
            hero_slot.markdown(
                _home_command_center_hero_html(team_name, hctx, pctx, injury_use_live=not is_eliminated),
                unsafe_allow_html=True,
            )
            emph_slot.markdown(_dashboard_emphasis_html(team_name, pctx), unsafe_allow_html=True)
            sections.append("hero_live_refresh")
            sections.append("live_bundle_ok")
    else:
        sections.append("fast_path")

    profile = pctx["profile"]

    if effective_live and isinstance(pctx.get("fb"), dict) and pctx["fb"].get("game"):
        render_home_live_hub_strip(team_name, pctx.get("fb"))
        sections.append("live_strip")
    elif effective_live:
        sections.append("live_strip_no_row")
    else:
        sections.append("live_strip_skipped_fast")

    sections.append("hero")
    sections.append("emphasis_strip")

    sec1_title = "1 · Postmortem — final series log" if is_eliminated else "1 · Series board"
    st.markdown(f'<div class="cmd-sec">{html.escape(sec1_title)}</div>', unsafe_allow_html=True)
    snap_cols = st.columns(4)
    status_txt = series_status_text(team_name, s_active)
    adv_like = hctx.get("advanced") or hctx.get("bracket_series")
    snap_cols[0].metric("Playoff status", "Advanced" if adv_like else profile.get("status", "—"))
    snap_cols[1].metric("Seed", profile.get("seed", "—"))
    s_disp = hctx.get("series") or s_active
    snap_cols[2].metric(
        "Round on the board",
        (s_disp or {}).get("round") or hctx.get("round_label") or profile.get("round", "—"),
    )
    fb = pctx.get("fb")
    if fb and fb.get("game") and fb.get("phase") == "live":
        edge = "🔴 LIVE on the board"
    elif fb and fb.get("game") and fb.get("starting_soon"):
        edge = "Tip soon — runway"
    elif fb and fb.get("game") and fb.get("phase") == "pregame":
        edge = "Pregame data live"
    elif fb and fb.get("game") and fb.get("phase") == "postgame":
        edge = "Final logged — wrap in hub"
    else:
        edge = "Local / static (no live scoreboard merge)" if not effective_live else "Tracking next tip"
    edge_metric = "Dashboard focus" if is_eliminated else "Tonight's edge"
    if is_eliminated:
        edge = "Offseason · roster, draft & cap"
    snap_cols[3].metric(edge_metric, edge)
    st.markdown(
        f"<div style='font-size:14px;font-weight:600;color:#e2e8f0;margin:6px 0 8px'>{html.escape(status_txt)}</div>",
        unsafe_allow_html=True,
    )
    s_table = hctx.get("series") or s_active
    if s_table and s_table.get("games"):
        st.dataframe(
            pd.DataFrame(s_table["games"]),
            use_container_width=True,
            height=min(220, 38 + 28 * len(s_table["games"])),
        )
    elif hctx.get("advanced"):
        st.info("Through the second round — Conference Finals pairings populate once both semis finish.")
    elif s_table and s_table.get("round") in ("Conference Finals", "NBA Finals"):
        st.caption("Conference Finals / Finals shell is live — game rows fill in as results post.")
    sections.append("series_board")

    st.markdown('<div class="cmd-sec">2 · Runway to tip</div>', unsafe_allow_html=True)
    if is_eliminated:
        with st.expander("Playoff schedule archive (no upcoming tip for this team)", expanded=False):
            with st.container(border=True):
                st.caption(
                    f"{fan_nick(team_name)}'s postseason ended with **{profile.get('first_round_result', 'first-round exit')}**. "
                    "Use **Live Game Center** in the sidebar if you want league-wide games still in progress."
                )
    else:
        with st.container(border=True):
            live = pctx.get("live")
            if live:
                home = live.get("homeTeam", {}) or {}
                away = live.get("awayTeam", {}) or {}
                st.markdown(
                    f"**{_live_team_full_name(away.get('teamTricode',''), away)}** @ **{_live_team_full_name(home.get('teamTricode',''), home)}** · _{live.get('gameStatusText','')}_"
                )
            else:
                opp = profile.get("current_opponent")
                st.info(
                    f"{fan_nick(team_name)} vs {opp or 'opponent TBA'} — "
                    + (
                        "Live scoreboard row appears after **Load live API updates**."
                        if not live_on
                        else "Live tip and countdown post when the NBA schedule feed lists the game."
                    )
                )
    sections.append("runway")

    st.markdown('<div class="cmd-sec">3 · Quick outlook</div>', unsafe_allow_html=True)
    render_team_outlook(team_name, compact_home=True, series_obj=s_active)
    sections.append("outlook_compact")

    st.markdown('<div class="cmd-sec">4 · Series snapshot (instant)</div>', unsafe_allow_html=True)
    fsnap = hctx.get("fast_snapshot") or get_fast_series_snapshot(team_name)
    c1, c2, c3 = st.columns(3)
    c1.metric("Opponent", fsnap.get("opponent") or "—")
    c2.metric("Series (local)", fsnap.get("series_score") or "—")
    c3.metric("Source", (fsnap.get("source") or "—")[:28])
    lg = fsnap.get("latest_game")
    if isinstance(lg, dict) and lg:
        st.caption(
            f"Latest logged row (local pack): {lg.get('Game', '')} · {lg.get('Date', '')} · {lg.get('Score', '')}"
        )
    sections.append("fast_series_snapshot")

    st.markdown('<div class="cmd-sec">5 · Injury snapshot</div>', unsafe_allow_html=True)
    if injury_live:
        df_inj, _ = get_injury_report(team_name)
        if df_inj is not None and not df_inj.empty:
            st.dataframe(df_inj.head(5), use_container_width=True, hide_index=True)
        else:
            st.caption("No injury rows in the merged feed yet.")
        sections.append("injury_snapshot_live")
    else:
        st.info(
            "ESPN injury scrape is **off** in fast mode. Open **Injury Report** below and tap **Fetch** to load."
        )
        sections.append("injury_snapshot_fast_placeholder")

    def sec_injuries():
        with st.container(border=True):
            render_injury_report(
                team_name,
                home_injury_opponents_from_home_ctx(team_name, hctx, s_active),
                show_page_header=False,
                fan_perspective_team=team_name,
                neutral_framing=True,
            )

    def sec_stars():
        starters = list(profile.get("starters", [])[:3])
        anchor = pctx.get("flagship") or (starters[0] if starters else "")
        if anchor and anchor in starters:
            starters.remove(anchor)
            starters.insert(0, anchor)
        elif anchor and starters:
            starters = [anchor] + [x for x in starters if x != anchor][:2]
        elif anchor:
            starters = [anchor]
        for name in starters or ["Rotation"]:
            if name == "Rotation":
                continue
            sa = season_averages(name)
            prof = player_resume_profile(name, team_name)
            render_player_fan_card(
                name,
                team_name,
                role=prof.get("role", "Rotation"),
                stats={
                    "PTS": sa.get("PTS", 0),
                    "REB": sa.get("REB", 0),
                    "AST": sa.get("AST", 0),
                    "STL": sa.get("STL", 0),
                    "BLK": sa.get("BLK", 0),
                },
            )

    def sec_momentum():
        hist = historic_series_context(team_name, s_active)
        if not hist.empty:
            st.markdown(
                f"<div style='font-size:13px;color:#cbd5e1;line-height:1.45'>{hist.iloc[0].get('Historical Context','')}</div>",
                unsafe_allow_html=True,
            )
        m1, m2, m3 = st.columns(3)
        if s_active:
            a, b = s_active["a"], s_active["b"]
            tw = int(s_active["a_wins"]) if team_name == a else int(s_active["b_wins"])
            ow = int(s_active["b_wins"]) if team_name == a else int(s_active["a_wins"])
            m1.metric("Series edge", f"+{tw - ow}" if tw > ow else (f"{tw - ow}" if tw < ow else "Even"))
            m2.metric("Games played", tw + ow)
            m3.metric("Data source", (s_active.get("source") or "—")[:18])
        else:
            m1.metric("Series edge", "—")
            m2.metric("Games played", "—")
            m3.metric("Data", "Awaiting")

    def sec_legacy():
        anchor = pctx.get("flagship") or profile.get("starters", [""])[0]
        if anchor:
            logs = playoff_game_logs_for_player(anchor)
            sm = summarize_playoff_logs(logs)
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{anchor.split()[-1]} PTS", sm.get("PTS", 0))
            c2.metric("REB", sm.get("REB", 0))
            c3.metric("AST", sm.get("AST", 0))
        st.caption("What-if sliders and ceilings: open **Legacy Tracker**.")

    def sec_stories():
        story_cols = st.columns(3)
        for col, (t, b) in zip(story_cols, _dashboard_story_cards(team_name, pctx)):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{t}**")
                    st.caption(b)

    def sec_last_game():
        if s_active and s_active.get("games"):
            last = s_active["games"][-1]
            opp = s_active["b"] if team_name == s_active["a"] else s_active["a"]
            gn = last.get("Game") if isinstance(last.get("Game"), int) else str(last.get("Game", "Game")).replace("Game ", "")
            try:
                gn_i = int(str(gn).replace("Game ", ""))
            except Exception:
                gn_i = len(s_active["games"])
            mvp, why = mvp_for_game(team_name, opp, gn_i, last.get("Winner"))
            st.success(f"**{mvp}** — _{why}_")
            st.caption(f"{last.get('Date','')} · {last.get('Score','')}")
        else:
            st.caption("MVP tag unlocks when the most recent game row hits the log for this matchup.")

    def sec_outlook_full():
        render_team_outlook(team_name, compact_home=False, series_obj=s_active)

    with st.expander("Injury Report (ESPN / merges)", expanded=False):
        if st.button("Fetch injury report", key=f"home_fetch_inj_{team_name}"):
            st.session_state[HOME_DASH_LOAD_INJ] = True
            st.rerun()
        if st.session_state.get(HOME_DASH_LOAD_INJ):
            sec_injuries()
        else:
            st.caption("Loads ESPN scrape and merged tables — only after you click **Fetch**.")

    with st.expander("Top Performers (NBA player stats)", expanded=False):
        if st.button("Load player stats & headshots", key=f"home_fetch_stars_{team_name}"):
            st.session_state[HOME_DASH_LOAD_STARS] = True
            st.rerun()
        if st.session_state.get(HOME_DASH_LOAD_STARS):
            sec_stars()
        else:
            st.caption("Uses career stats + headshot URLs — skipped until you opt in.")

    with st.expander("Momentum", expanded=False):
        sec_momentum()

    with st.expander("Player Storylines", expanded=False):
        sec_stories()

    with st.expander("Detailed Matchup Intelligence", expanded=False):
        sec_last_game()

    with st.expander("Full team outlook & worry list", expanded=False):
        sec_outlook_full()

    with st.expander("Legacy playoff game totals (NBA logs)", expanded=False):
        if st.button("Load playoff game logs", key=f"home_fetch_legacy_{team_name}"):
            st.session_state[HOME_DASH_LOAD_LEGACY] = True
            st.rerun()
        if st.session_state.get(HOME_DASH_LOAD_LEGACY):
            sec_legacy()
        else:
            st.caption("Pulls player playoff game logs — heavy; click **Load** first.")

    st.caption(
        f"Auto-updated bracket series + API where available · Refreshed {datetime.now().strftime('%b %d %I:%M %p')}"
    )
    sections.append("footer_caption")

    live_flag = bool(st.session_state.get(HOME_DASH_LIVE_UPDATES))
    perf_fast = (not live_flag) or is_eliminated
    if is_eliminated:
        api_display = "0 (offseason mode — no automatic live playoff bundle on Home)"
    elif live_flag and api_calls:
        api_display = "1 × live_bundle (resolve_home_matchup + series_for_team + featured_broadcast_state)"
    elif live_flag:
        api_display = "0 (live bundle did not complete)"
    else:
        api_display = "0 automatic on Home (fast mode — optional APIs only via buttons)"

    _home_dashboard_perf_footer(
        t0,
        sections,
        fast_mode=perf_fast,
        api_calls=api_display,
        skipped_note=skip_note,
    )

def home_injury_opponents_from_home_ctx(team_name, hctx, s_active=None):
    """Opponent list for injury merge using existing Home context (avoids extra ``series_for_team``)."""
    if not isinstance(hctx, dict):
        return TEAM_PROFILES.get(team_name, {}).get("current_opponent")
    ctx = hctx.get("ctx")
    if ctx and ctx.get("advanced"):
        return ctx.get("opponents", [])
    if hctx.get("mode") == "waiting_cf":
        ops = hctx.get("opponents") or []
        if ops:
            return ops
    s = s_active or hctx.get("series")
    if s and s.get("round") in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return [opp]
    return TEAM_PROFILES.get(team_name, {}).get("current_opponent")


def home_injury_opponents(team_name):
    ctx = next_round_context_for_team(team_name)
    if ctx and ctx.get("advanced"):
        return ctx.get("opponents", [])
    _, s = series_for_team(team_name)
    if s and s.get("round") in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return [opp]
    return TEAM_PROFILES.get(team_name, {}).get("current_opponent")

def _first_round_synthetic_games(team_a, team_b):
    """Static first-round game rows for bracket cards when API has not attached games."""
    rows = FIRST_ROUND_GAME_SCORES.get(team_a) or FIRST_ROUND_GAME_SCORES.get(team_b) or []
    out = []
    for r in rows:
        gn = r.get("Game", len(out) + 1)
        if isinstance(gn, int):
            gn = f"Game {gn}"
        out.append({
            "Game": str(gn),
            "Date": str(r.get("Date", "")),
            "Score": str(r.get("Score", "")),
            "Winner": str(r.get("Winner", "")),
            "Matchup": str(r.get("Matchup", "")),
        })
    return out


def _bracket_series_for_display(s, round_display_name):
    """Shallow copy of series shell with games filled from static first-round data when needed."""
    view = dict(s)
    games = view.get("games") or []
    if not games and round_display_name == "First Round":
        syn = _first_round_synthetic_games(view.get("a"), view.get("b"))
        if syn:
            view["games"] = syn
    return view


BRACKET_VISUAL_CSS = """
.bracket-wrap {
  background: linear-gradient(160deg, #070d18 0%, #0f172a 45%, #1e1b4b 100%);
  padding: 12px 10px 16px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
  color: #f8fafc;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  max-width: 100%;
  box-sizing: border-box;
}
.bmk-page-head { text-align: center; margin-bottom: 10px; }
.bmk-title {
  font-size: clamp(1.2rem, 2.6vw, 1.6rem);
  font-weight: 900;
  letter-spacing: -0.02em;
  margin: 0 0 4px;
  color: #f8fafc;
}
.bmk-sub {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.3;
  margin: 0 auto;
  max-width: 52rem;
}
.bmk-scroll {
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
  scrollbar-color: rgba(100, 116, 139, 0.55) rgba(15, 23, 42, 0.5);
}
.bmk-grid {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 0;
  min-width: 1580px;
  padding: 0;
  box-sizing: border-box;
}
.bmk-col {
  flex: 1 1 0;
  min-width: 300px;
  max-width: 400px;
  padding: 0 8px;
  border-right: 1px solid rgba(71, 85, 105, 0.38);
  box-sizing: border-box;
}
.bmk-col:last-child { border-right: none; }
.bmk-col--hub {
  min-width: 320px;
  max-width: 420px;
  flex: 1.12 1 0;
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.5) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-radius: 12px;
  margin: 0 2px;
  padding: 8px 10px 10px;
  border: 1px solid rgba(129, 140, 248, 0.35);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
.bmk-col-head {
  text-align: center;
  padding: 6px 2px 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(100, 116, 139, 0.28);
}
.bmk-col-eyebrow {
  display: block;
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #64748b;
  margin-bottom: 2px;
}
.bmk-col[data-conf="east"] .bmk-col-eyebrow { color: #7dd3fc; }
.bmk-col[data-conf="west"] .bmk-col-eyebrow { color: #fcd34d; }
.bmk-col-title {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #e2e8f0;
}
.bmk-col-stack { display: flex; flex-direction: column; gap: 8px; }
.bmk-hub { display: flex; flex-direction: column; gap: 8px; text-align: center; }
.bmk-hub-label {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #c4b5fd;
  margin-bottom: 4px;
}
.bmk-hub-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
}
.bmk-wait-card {
  background: rgba(30, 41, 59, 0.65);
  border: 1px dashed rgba(148, 163, 184, 0.35);
  border-radius: 10px;
  padding: 8px 10px 10px;
  text-align: center;
}
.bmk-wait-card--finals { border-style: solid; border-color: rgba(251, 191, 36, 0.45); }
.bmk-wait-kicker { font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 4px; }
.bmk-wait-title { font-size: 13px; font-weight: 800; color: #f8fafc; line-height: 1.25; }
.bmk-wait-line { margin: 4px 0 0; font-size: 11px; line-height: 1.35; color: #cbd5e1; }
.bmk-card {
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
  padding: 8px 10px 7px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28);
  transition: border-color 0.12s ease, box-shadow 0.12s ease, transform 0.12s ease;
}
.bmk-card:hover {
  transform: translateY(-1px);
  border-color: rgba(148, 163, 184, 0.45);
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);
}
.bmk-card--active { border-color: rgba(56, 189, 248, 0.5); box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.14), 0 4px 16px rgba(0, 0, 0, 0.26); }
.bmk-card--complete { border-color: rgba(52, 211, 153, 0.4); }
.bmk-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 6px;
  margin-bottom: 6px;
}
.bmk-chip-round {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.18);
  padding: 2px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}
.bmk-pill { font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
.bmk-pill--live { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.35); }
.bmk-pill--done { background: rgba(52, 211, 153, 0.18); color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.35); }
.bmk-series-score { font-size: 18px; font-weight: 900; color: #fbbf24; letter-spacing: 0.04em; flex-shrink: 0; white-space: nowrap; }
.bmk-rows { display: flex; flex-direction: column; gap: 4px; }
.bmk-team {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 8px;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.72);
  border: 1px solid rgba(71, 85, 105, 0.36);
  border-left: 3px solid var(--stripe, #64748b);
}
.bmk-team--leading { background: rgba(30, 58, 95, 0.48); border-color: rgba(56, 189, 248, 0.3); }
.bmk-team--winner { background: rgba(22, 78, 58, 0.36); border-color: rgba(52, 211, 153, 0.42); border-left-width: 4px; }
.bmk-team-main { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1 1 auto; }
.bmk-logo { width: 40px; height: 40px; object-fit: contain; flex-shrink: 0; filter: drop-shadow(0 1px 5px rgba(0, 0, 0, 0.4)); }
.bmk-team-text {
  min-width: 0;
  flex: 1 1 auto;
  text-align: left;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: baseline;
  gap: 6px;
}
.bmk-seed { font-size: 10px; font-weight: 700; color: #94a3b8; flex-shrink: 0; white-space: nowrap; }
.bmk-name {
  font-size: 13px;
  font-weight: 800;
  color: #f1f5f9;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  flex: 1 1 auto;
  word-break: normal;
  overflow-wrap: normal;
}
.bmk-team-meta { display: flex; align-items: center; gap: 5px; flex-shrink: 0; margin-left: 4px; }
.bmk-wins { font-size: 18px; font-weight: 900; color: #f8fafc; min-width: 22px; text-align: right; flex-shrink: 0; }
.bmk-won-badge {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6ee7b7;
  background: rgba(16, 185, 129, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.bmk-foot { font-size: 11px; color: #cbd5e1; margin-top: 5px; line-height: 1.25; text-align: left; word-break: break-word; }
.bmk-foot--next { margin-top: 2px; font-size: 10px; color: #94a3b8; line-height: 1.25; }
.bmk-details { margin-top: 5px; border-top: 1px solid rgba(51, 65, 85, 0.52); padding-top: 5px; }
.bmk-details summary { cursor: pointer; font-size: 11px; font-weight: 700; color: #93c5fd; list-style: none; }
.bmk-details summary::-webkit-details-marker { display: none; }
.bmk-log { margin: 4px 0 0; padding-left: 16px; text-align: left; }
@media (min-width: 1600px) {
  .bmk-grid { min-width: 1720px; }
  .bmk-col { min-width: 312px; max-width: 420px; }
}
"""


def bracket_team_accent(team):
    return {
        "New York Knicks": "#f97316",
        "Philadelphia 76ers": "#3b82f6",
        "Detroit Pistons": "#ef4444",
        "Cleveland Cavaliers": "#f472b6",
        "Oklahoma City Thunder": "#38bdf8",
        "Los Angeles Lakers": "#fbbf24",
        "San Antonio Spurs": "#cbd5e1",
        "Minnesota Timberwolves": "#34d399",
        "Boston Celtics": "#22c55e",
        "Atlanta Hawks": "#dc2626",
        "Orlando Magic": "#60a5fa",
        "Toronto Raptors": "#ef4444",
        "Phoenix Suns": "#fb923c",
        "Portland Trail Blazers": "#e11d48",
        "Denver Nuggets": "#facc15",
        "Houston Rockets": "#f87171",
    }.get(team, "#94a3b8")


def _bracket_latest_game_html(s):
    games = s.get("games") or []
    if not games:
        if s.get("winner"):
            return f"Latest: <strong>{html.escape(str(s['winner']))}</strong> won the series."
        return "Latest: <span style='opacity:.75'>No games in feed yet</span>"
    last = games[-1]
    score = html.escape(str(last.get("Score", "—")))
    dt = html.escape(str(last.get("Date", "")))
    win = html.escape(str(last.get("Winner", "")))
    gnum = html.escape(str(last.get("Game", "")))
    return f"Latest: <strong>{gnum}</strong> · {dt} · {score} · <strong>{win}</strong>"


def _bracket_next_game_html(s):
    if s.get("winner"):
        return "Next: <span style='opacity:.7'>—</span>"
    games = s.get("games") or []
    n = len(games) + 1
    return f"Next: <strong>Game {n}</strong> <span style='opacity:.75'>(schedule TBA)</span>"


def _bracket_game_log_items(s):
    games = s.get("games") or []
    rows = []
    for g in games[-8:]:
        rows.append(
            "<li style='margin:4px 0;font-size:12px;color:#e2e8f0'>"
            f"{html.escape(str(g.get('Game','')))} · {html.escape(str(g.get('Date','')))} · "
            f"{html.escape(str(g.get('Score','—')))} — <strong>{html.escape(str(g.get('Winner','')))}</strong></li>"
        )
    return "".join(rows) if rows else "<li style='opacity:.7'>No game rows yet</li>"


def bracket_series_card(s, round_display_name, show_round_chip=False, favorite_team=None):
    s_disp = _bracket_series_for_display(s, round_display_name)
    a, b = s_disp["a"], s_disp["b"]
    aw = int(s_disp.get("a_wins", 0) or 0)
    bw = int(s_disp.get("b_wins", 0) or 0)
    winner = s_disp.get("winner")
    active = not winner
    seed_a = TEAM_PROFILES.get(a, {}).get("seed", "—")
    seed_b = TEAM_PROFILES.get(b, {}).get("seed", "—")
    logo_a = html.escape(TEAM_LOGOS.get(a, ""), quote=True)
    logo_b = html.escape(TEAM_LOGOS.get(b, ""), quote=True)

    def team_row(team, wins, seed, logo_url, is_winner, is_leading):
        stripe = bracket_team_accent(team)
        classes = ["bmk-team"]
        if favorite_team and team == favorite_team:
            classes.append("bmk-team--yours")
        if is_winner:
            classes.append("bmk-team--winner")
        elif active and is_leading:
            classes.append("bmk-team--leading")
        badge = '<span class="bmk-won-badge">Won series</span>' if is_winner else ""
        return (
            f'<div class="{" ".join(classes)}" style="--stripe:{stripe}">'
            f'<div class="bmk-team-main"><img class="bmk-logo" src="{logo_url}" alt="" width="40" height="40"/>'
            f'<div class="bmk-team-text"><span class="bmk-seed">({html.escape(str(seed))})</span>'
            f'<span class="bmk-name">{html.escape(team)}</span></div></div>'
            f'<div class="bmk-team-meta">{badge}<span class="bmk-wins">{wins}</span></div></div>'
        )

    row_a = team_row(a, aw, seed_a, logo_a, winner == a, aw > bw and not winner)
    row_b = team_row(b, bw, seed_b, logo_b, winner == b, bw > aw and not winner)
    pill = (
        '<span class="bmk-pill bmk-pill--live">In progress</span>'
        if active
        else '<span class="bmk-pill bmk-pill--done">Series complete</span>'
    )
    card_mod = "bmk-card--active" if active else "bmk-card--complete"
    if favorite_team and favorite_team in (a, b):
        card_mod += " bmk-card--yours"
    chip = (
        f'<span class="bmk-chip-round">{html.escape(round_display_name)}</span>'
        if show_round_chip
        else ""
    )
    details = (
        f'<details class="bmk-details"><summary>Game log &amp; details</summary>'
        f'<div class="bmk-foot bmk-foot--next">{_bracket_next_game_html(s_disp)}</div>'
        f'<ul class="bmk-log">{_bracket_game_log_items(s_disp)}</ul></details>'
    )
    return (
        f'<div class="bmk-card {card_mod}"><div class="bmk-card-top">{chip}'
        f'<span class="bmk-series-score">{aw}–{bw}</span>{pill}</div>'
        f'<div class="bmk-rows">{row_a}{row_b}</div>'
        f'<div class="bmk-foot">{_bracket_latest_game_html(s_disp)}</div>{details}</div>'
    )


def _cf_waiting_placeholder(conf_full, sr_list):
    esc = html.escape
    if not sr_list:
        return (
            '<div class="bmk-wait-card">'
            f'<div class="bmk-wait-kicker">{esc(conf_full)}</div>'
            '<div class="bmk-wait-title">Waiting for semifinal results</div>'
            '<p class="bmk-wait-line">Semifinals will appear here when loaded.</p></div>'
        )
    decided = [s for s in sr_list if s.get("winner")]
    open_s = [s for s in sr_list if not s.get("winner")]
    kicker = esc(conf_full)
    if len(decided) == 1 and open_s:
        champ = str(decided[0].get("winner") or "")
        u = open_s[0]
        ta, tb = str(u.get("a") or ""), str(u.get("b") or "")
        aw = int(u.get("a_wins", 0) or 0)
        bw = int(u.get("b_wins", 0) or 0)
        title = f"{esc(champ)} await {esc(ta)} / {esc(tb)} winner"
        line = f"{esc(ta)} vs {esc(tb)} — series in progress ({aw}–{bw})."
    elif not decided:
        title = "Waiting for both semifinal winners"
        parts = []
        for semi in sr_list:
            sa, sb = semi.get("a"), semi.get("b")
            oa = int(semi.get("a_wins", 0) or 0)
            ob = int(semi.get("b_wins", 0) or 0)
            parts.append(f"{esc(str(sa))} vs {esc(str(sb))} ({oa}–{ob})")
        line = " · ".join(parts) if parts else "Scores updating…"
    else:
        title = "Conference Finals loading"
        line = "Both semifinals are decided; matchup should appear shortly."
    return (
        f'<div class="bmk-wait-card"><div class="bmk-wait-kicker">{kicker}</div>'
        f'<div class="bmk-wait-title">{title}</div><p class="bmk-wait-line">{line}</p></div>'
    )


def _markdown_safe_bracket_html(html_fragment):
    return "\n".join(line.lstrip() for line in html_fragment.splitlines())


def _bracket_fallback_dataframe(east_fr, east_sr, west_sr, west_fr, east_conf, west_conf, finals):
    rows = []

    def append_rows(column_label, series_list, round_name):
        for s in series_list:
            sd = _bracket_series_for_display(s, round_name)
            games = sd.get("games") or []
            if games:
                lg = games[-1]
                latest = f"{lg.get('Game', '')} {lg.get('Date', '')} {lg.get('Score', '')} → {lg.get('Winner', '')}"
            else:
                latest = "—"
            rows.append(
                {
                    "Column": column_label,
                    "Team A": sd.get("a"),
                    "Team B": sd.get("b"),
                    "Wins": f"{sd.get('a_wins', 0)}–{sd.get('b_wins', 0)}",
                    "Winner": sd.get("winner") or "—",
                    "Latest": latest,
                }
            )

    append_rows("East — First round", east_fr, "First Round")
    append_rows("East — Semifinals", east_sr, "Conference Semifinals")
    append_rows("West — Semifinals", west_sr, "Conference Semifinals")
    append_rows("West — First round", west_fr, "First Round")
    if east_conf and len(east_conf) == 1:
        append_rows("East — Conference finals", list(east_conf.values()), "Conference Finals")
    if west_conf and len(west_conf) == 1:
        append_rows("West — Conference finals", list(west_conf.values()), "Conference Finals")
    if finals and len(finals) == 1:
        append_rows("NBA Finals", list(finals.values()), "NBA Finals")
    return pd.DataFrame(rows)


def render_bracket(favorite_team=None):
    if favorite_team:
        render_fan_page_hero(
            favorite_team,
            "Playoff Bracket",
            f"Full 2026 bracket — {fan_nick(favorite_team)} series highlighted in your colors.",
            "YOUR TEAM",
        )

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=30000, key="bracket_refresh")

    stt = get_playoff_state_cached(True)
    east_fr = stt["east_fr"]
    west_fr = stt["west_fr"]
    east_sr = stt["east_sr"]
    west_sr = stt["west_sr"]
    east_conf = stt["east_cf"]
    west_conf = stt["west_cf"]
    finals = stt["finals"]

    if east_conf and len(east_conf) == 1:
        east_cf_block = bracket_series_card(list(east_conf.values())[0], "Conference Finals", favorite_team=favorite_team)
    else:
        east_cf_block = _cf_waiting_placeholder("Eastern Conference Finals", east_sr)

    if west_conf and len(west_conf) == 1:
        west_cf_block = bracket_series_card(list(west_conf.values())[0], "Conference Finals", favorite_team=favorite_team)
    else:
        west_cf_block = _cf_waiting_placeholder("Western Conference Finals", west_sr)

    if finals and len(finals) == 1:
        finals_block = bracket_series_card(list(finals.values())[0], "NBA Finals", favorite_team=favorite_team)
    else:
        finals_block = (
            '<div class="bmk-wait-card bmk-wait-card--finals">'
            '<div class="bmk-wait-kicker">NBA Finals</div>'
            '<div class="bmk-wait-title">Waiting for conference champions</div>'
            '<p class="bmk-wait-line">Appears when East and West conference finals winners are set.</p></div>'
        )

    center_column = (
        '<div class="bmk-hub">'
        '<div><div class="bmk-hub-label">East — Conference Finals</div>'
        f"{east_cf_block}</div>"
        '<div class="bmk-hub-divider" aria-hidden="true"></div>'
        '<div><div class="bmk-hub-label">West — Conference Finals</div>'
        f"{west_cf_block}</div>"
        '<div class="bmk-hub-divider" aria-hidden="true"></div>'
        '<div><div class="bmk-hub-label">NBA Finals</div>'
        f"{finals_block}</div></div>"
    )

    east_fr_cards = "".join(bracket_series_card(s, "First Round", favorite_team=favorite_team) for s in east_fr)
    east_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals", favorite_team=favorite_team) for s in east_sr)
    west_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals", favorite_team=favorite_team) for s in west_sr)
    west_fr_cards = "".join(bracket_series_card(s, "First Round", favorite_team=favorite_team) for s in west_fr)

    bracket_body = f"""<div class="bmk-page-head">
<h2 class="bmk-title">2026 NBA Playoff Bracket</h2>
<p class="bmk-sub">East on the left, West on the right, conference finals and NBA Finals in the center. Scroll sideways on smaller screens. Open any series for the full game log.</p>
</div>
<div class="bmk-scroll" role="region" aria-label="Playoff bracket">
<div class="bmk-grid">
<div class="bmk-col" data-conf="east">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Eastern Conference</span>
<h3 class="bmk-col-title">First Round</h3>
</div>
<div class="bmk-col-stack">{east_fr_cards}</div>
</div>
<div class="bmk-col" data-conf="east">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Eastern Conference</span>
<h3 class="bmk-col-title">Conference Semifinals (Round 2)</h3>
</div>
<div class="bmk-col-stack">{east_sr_cards}</div>
</div>
<div class="bmk-col bmk-col--hub">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Center</span>
<h3 class="bmk-col-title">Conference &amp; NBA Finals</h3>
</div>
<div class="bmk-col-stack">{center_column}</div>
</div>
<div class="bmk-col" data-conf="west">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Western Conference</span>
<h3 class="bmk-col-title">Conference Semifinals (Round 2)</h3>
</div>
<div class="bmk-col-stack">{west_sr_cards}</div>
</div>
<div class="bmk-col" data-conf="west">
<div class="bmk-col-head">
<span class="bmk-col-eyebrow">Western Conference</span>
<h3 class="bmk-col-title">First Round</h3>
</div>
<div class="bmk-col-stack">{west_fr_cards}</div>
</div>
</div>
</div>"""

    full_html = (
        '<div class="bracket-wrap"><style>'
        + BRACKET_VISUAL_CSS.strip()
        + "</style>"
        + bracket_body
        + "</div>"
    )
    full_html = _markdown_safe_bracket_html(full_html)

    try:
        st.markdown(full_html, unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Playoff Bracket HTML could not render ({exc}). Showing the same data in a table.")
        st.dataframe(
            _bracket_fallback_dataframe(
                east_fr, east_sr, west_sr, west_fr, east_conf, west_conf, finals
            ),
            use_container_width=True,
            hide_index=True,
        )


def latest_game_note(team, series_obj=None):
    if series_obj is not None:
        s = series_obj
    else:
        _, s = series_for_team(team)
    if not s or not s.get("games"):
        return "No completed current-series game is in the log yet — check back after tip."
    last = s["games"][-1]
    result = "won" if last.get("Winner") == team else "lost"
    nick = fan_nick(team)
    if result == "won":
        vibe = "That's a night you can feel good about as a fan — carry the energy into prep for the next one."
    else:
        vibe = "Tough watch — the bounce-back story starts with defense and cleaner possessions next game."
    return (
        f"Last result for {nick}: {last.get('Game','Previous game')} on {last.get('Date','recently')} — "
        f"{last.get('Score','score unavailable')}. You {result} that one. {vibe}"
    )

def render_team_outlook(team, compact_home=False, series_obj=None):
    p = TEAM_PROFILES[team]
    nick = fan_nick(team)
    if compact_home:
        st.markdown(f"##### Quick outlook · {nick}")
        st.markdown(
            f"<div class='big-status' style='margin:0 0 8px'>{series_status_text(team, series_obj)}</div>",
            unsafe_allow_html=True,
        )
        st.info(latest_game_note(team, series_obj))
        tops = p.get("strengths") or []
        if tops:
            st.caption("Strengths — " + " · ".join(str(x) for x in tops[:2]))
        return
    st.subheader(f"Team outlook · {nick} fan lens")
    st.markdown(f"<div class='big-status'>{series_status_text(team, series_obj)}</div>", unsafe_allow_html=True)
    st.info(latest_game_note(team, series_obj))
    st.markdown("### What you should feel good about")
    for s in p["strengths"]:
        if team == "New York Knicks" and "Towns" in s:
            st.success(
                "Karl-Anthony Towns gives you real spacing at the five — the swing factor is keeping him on the floor without foul trouble."
            )
        else:
            st.success(s)
    st.markdown("### Honest worry list (so you're not surprised)")
    for c in p["concerns"]:
        st.warning(c)
    st.markdown("### What a win looks like next game")
    for item in [
        "You win the possession battle — fewer empty trips, no careless live-ball turnovers.",
        "Your main creators still have legs in the fourth because the bench didn't bleed the lead.",
        "You defend without fouling; bonus points if the glass tilts your way late.",
    ]:
        st.write(f"• {item}")

def render_game_countdown(team):
    st.subheader("Game Status / Live Link")
    fb = featured_broadcast_state(team)
    if not fb or not fb.get("game"):
        opp = TEAM_PROFILES[team].get("current_opponent")
        if opp:
            st.info(f"Next matchup: {team} vs {opp}. A scoreboard row lands here when the NBA feed lists it in the ET window.")
        else:
            st.info("No game row in the merged ET window yet.")
        return
    live = fb["game"]
    ph = fb["phase"]
    home = live.get("homeTeam", {}) or {}
    away = live.get("awayTeam", {}) or {}
    status = live.get("gameStatusText", "Scheduled")
    matchup = f"{_live_team_full_name(away.get('teamTricode', ''), away)} at {_live_team_full_name(home.get('teamTricode', ''), home)}"
    if ph == "postgame":
        st.success(f"Final: {matchup}")
        st.write(status)
    elif ph == "live":
        st.error(f"🔴 LIVE NOW: {matchup}")
        st.write(status)
        if st.button("Go to Live Game Center", key="countdown_open_live"):
            st.session_state["page_override"] = "🏀 Live Game Center"
            st.rerun()
    elif ph == "pregame" and fb.get("starting_soon"):
        st.warning(f"Starting soon: {matchup}")
        st.write(status)
        if st.button("Go to Live Game Center", key="countdown_open_pregame"):
            st.session_state["page_override"] = "🏀 Live Game Center"
            st.rerun()
    else:
        st.info(f"Upcoming: {matchup}")
        st.write(status)

def render_lineup_cards(team, box_df):
    alias=TEAM_ALIASES[team]
    lineup=estimated_lineup(box_df, alias, team)
    positions=["PG","SG","SF","PF","C"]
    st.markdown(f"### {team} live lineup / estimated current high-usage lineup")
    cols=st.columns(5)
    for i, (_, r) in enumerate(lineup.iterrows()):
        name=r.get("Player",""); seas=season_averages(name)
        with cols[i]:
            st.markdown("<div class='player-card'>", unsafe_allow_html=True)
            try: st.image(headshot(name), width=95)
            except Exception: pass
            st.markdown(f"**{positions[i] if i < 5 else ''} — {name} {player_temp(r)}**")
            st.caption("Current Game")
            st.write(f"PTS {r.get('PTS',0)} | REB {r.get('REB',0)} | AST {r.get('AST',0)}")
            st.write(f"STL {r.get('STL',0)} | BLK {r.get('BLK',0)}")
            st.caption("Season Avg")
            st.write(f"PTS {seas['PTS']} | REB {seas['REB']} | AST {seas['AST']}")
            st.write(f"STL {seas['STL']} | BLK {seas['BLK']}")
            st.markdown("</div>", unsafe_allow_html=True)


def _live_team_full_name(team_tricode, team_obj):
    t = ALIAS_TO_TEAM.get(team_tricode or "")
    if t:
        return t
    city = (team_obj or {}).get("teamCity") or ""
    nick = (team_obj or {}).get("teamName") or (team_tricode or "?")
    return f"{city} {nick}".strip() or nick


def _live_series_board(away_name, home_name):
    pair = {away_name, home_name}
    use_demo = bool(globals().get("USE_DEMO_BACKUP", False))
    stt = get_playoff_state_cached(use_demo)
    candidates = []
    candidates.extend(stt["second"].values())
    candidates.extend((stt.get("cf") or {}).values())
    candidates.extend((stt.get("finals") or {}).values())
    for s in candidates:
        if not s:
            continue
        if {s.get("a"), s.get("b")} == pair:
            a, b = s["a"], s["b"]
            return f"{TEAM_ALIASES[a]} {s['a_wins']}–{s['b_wins']} {TEAM_ALIASES[b]}", s.get("source") or ""
    return None, None


def _seed_badge(team_name):
    if team_name not in TEAM_PROFILES:
        return "—"
    return f"Seed {TEAM_PROFILES[team_name]['seed']}"


def _injury_hero_lines(team_names, max_each=2):
    lines = []
    for tm in team_names:
        if not tm:
            continue
        df, _src = get_injury_report(tm)
        if df is None or df.empty:
            continue
        bits = []
        for _, r in df.head(max_each).iterrows():
            pl = html.escape(str(r.get("Player", "?")))
            stt = html.escape(str(r.get("Status", "?")))
            bits.append(f"<span class='live-pill' style='font-size:11px'>🩹 {pl}: {stt}</span>")
        if bits:
            lines.append(f"<div style='margin-top:6px'><span style='font-weight:800;color:#e2e8f0'>{html.escape(tm)}</span> {' '.join(bits)}</div>")
    return "".join(lines) if lines else "<div style='margin-top:8px;color:#94a3b8;font-size:12px'>No injury rows from live source · see <b>Injuries</b> tab.</div>"


def get_team_theme(team_name):
    """Brand palette for the selected team — heroes, cards, tables, and accents."""
    default = {
        "primary": "#38bdf8",
        "secondary": "#1e293b",
        "accent": "#38bdf8",
        "bg0": "#0f172a",
        "bg1": "#1e293b",
        "accent_soft": "rgba(56,189,248,.18)",
        "border": "rgba(56,189,248,.35)",
        "card_tint": "#f0f9ff",
        "row_even": "rgba(56,189,248,.06)",
        "row_odd": "#ffffff",
        "good": "#16a34a",
        "warn": "#d97706",
        "bad": "#dc2626",
    }
    palettes = {
        "New York Knicks": {
            "primary": "#006BB6", "secondary": "#F58426", "accent": "#F58426",
            "bg0": "#0a1628", "bg1": "#152642", "accent_soft": "rgba(245,132,38,.22)",
            "border": "rgba(0,107,182,.45)", "card_tint": "#eff6ff", "row_even": "rgba(0,107,182,.08)",
        },
        "Philadelphia 76ers": {
            "primary": "#006BB6", "secondary": "#ED174C", "accent": "#ED174C",
            "bg0": "#0c1220", "bg1": "#1a1f3c", "accent_soft": "rgba(237,23,76,.18)",
            "border": "rgba(0,107,182,.4)", "card_tint": "#f8fafc",
        },
        "Detroit Pistons": {
            "primary": "#C8102E", "secondary": "#1D42BA", "accent": "#C8102E",
            "bg0": "#1a0a0c", "bg1": "#241018", "accent_soft": "rgba(200,16,46,.2)",
            "border": "rgba(200,16,46,.4)", "card_tint": "#fff1f2",
        },
        "Cleveland Cavaliers": {
            "primary": "#860038", "secondary": "#FDBB30", "accent": "#FDBB30",
            "bg0": "#1a0c12", "bg1": "#2a1220", "accent_soft": "rgba(253,187,48,.18)",
            "border": "rgba(134,0,56,.4)", "card_tint": "#fdf4ff",
        },
        "Oklahoma City Thunder": {
            "primary": "#007AC1", "secondary": "#EF3B24", "accent": "#007AC1",
            "bg0": "#0a1524", "bg1": "#122238", "accent_soft": "rgba(0,122,193,.22)",
            "border": "rgba(0,122,193,.4)", "card_tint": "#f0f9ff",
        },
        "Los Angeles Lakers": {
            "primary": "#552583", "secondary": "#FDB927", "accent": "#FDB927",
            "bg0": "#14081f", "bg1": "#251538", "accent_soft": "rgba(253,185,39,.22)",
            "border": "rgba(85,37,131,.5)", "card_tint": "#faf5ff", "row_even": "rgba(85,37,131,.07)",
        },
        "San Antonio Spurs": {
            "primary": "#000000", "secondary": "#C4CED4", "accent": "#C4CED4",
            "bg0": "#0c0c0c", "bg1": "#1c232e", "accent_soft": "rgba(196,206,212,.2)",
            "border": "rgba(196,206,212,.35)", "card_tint": "#f8fafc", "row_even": "rgba(0,0,0,.04)",
        },
        "Minnesota Timberwolves": {
            "primary": "#0C2340", "secondary": "#236192", "accent": "#78BE20",
            "bg0": "#061a18", "bg1": "#0f2d28", "accent_soft": "rgba(120,190,32,.2)",
            "border": "rgba(120,190,32,.35)", "card_tint": "#f0fdf4",
        },
        "Boston Celtics": {
            "primary": "#007A33", "secondary": "#FFFFFF", "accent": "#22c55e",
            "bg0": "#061510", "bg1": "#0f2418", "accent_soft": "rgba(34,197,94,.2)",
            "border": "rgba(0,122,51,.45)", "card_tint": "#f0fdf4", "row_even": "rgba(0,122,51,.07)",
        },
        "Atlanta Hawks": {
            "primary": "#E03A3E", "secondary": "#C1D32F", "accent": "#E03A3E",
            "bg0": "#1a0c0c", "bg1": "#2a1212", "accent_soft": "rgba(224,58,62,.2)",
            "border": "rgba(224,58,62,.4)", "card_tint": "#fff7ed",
        },
        "Orlando Magic": {
            "primary": "#0077C0", "secondary": "#000000", "accent": "#0077C0",
            "bg0": "#0a1420", "bg1": "#122a45", "accent_soft": "rgba(0,119,192,.22)",
            "border": "rgba(0,119,192,.4)", "card_tint": "#eff6ff",
        },
        "Toronto Raptors": {
            "primary": "#CE1141", "secondary": "#000000", "accent": "#CE1141",
            "bg0": "#0f0f12", "bg1": "#1a1520", "accent_soft": "rgba(206,17,65,.18)",
            "border": "rgba(206,17,65,.4)", "card_tint": "#fff1f2",
        },
        "Phoenix Suns": {
            "primary": "#1D1160", "secondary": "#E56020", "accent": "#E56020",
            "bg0": "#1a0f08", "bg1": "#2d1810", "accent_soft": "rgba(229,96,32,.22)",
            "border": "rgba(229,96,32,.4)", "card_tint": "#fff7ed",
        },
        "Portland Trail Blazers": {
            "primary": "#E03A3E", "secondary": "#000000", "accent": "#E03A3E",
            "bg0": "#120808", "bg1": "#221010", "accent_soft": "rgba(224,58,62,.2)",
            "border": "rgba(224,58,62,.4)", "card_tint": "#fff1f2",
        },
        "Denver Nuggets": {
            "primary": "#0E2240", "secondary": "#FEC524", "accent": "#FEC524",
            "bg0": "#0f1724", "bg1": "#1e2a42", "accent_soft": "rgba(254,197,36,.2)",
            "border": "rgba(254,197,36,.35)", "card_tint": "#fffbeb",
        },
        "Houston Rockets": {
            "primary": "#CE1141", "secondary": "#000000", "accent": "#CE1141",
            "bg0": "#140808", "bg1": "#241010", "accent_soft": "rgba(206,17,65,.2)",
            "border": "rgba(206,17,65,.4)", "card_tint": "#fff1f2",
        },
    }
    merged = {**default, **palettes.get(team_name, {})}
    return merged


def inject_team_brand_css(team_name):
    """Inject CSS variables + page tint for the sidebar-selected team."""
    t = get_team_theme(team_name)
    nick = html.escape(fan_nick(team_name))
    st.markdown(
        f"""
<style>
:root {{
  --team-primary: {t['primary']};
  --team-secondary: {t['secondary']};
  --team-accent: {t['accent']};
  --team-bg0: {t['bg0']};
  --team-bg1: {t['bg1']};
  --team-accent-soft: {t['accent_soft']};
  --team-border: {t['border']};
  --team-card-tint: {t['card_tint']};
  --team-row-even: {t['row_even']};
  --team-row-odd: {t['row_odd']};
  --team-good: {t['good']};
  --team-warn: {t['warn']};
  --team-bad: {t['bad']};
}}
div[data-testid="stAppViewContainer"] {{
  background: linear-gradient(180deg, {t['card_tint']} 0%, #f8fafc 120px, #f1f5f9 100%) !important;
}}
section[data-testid="stSidebar"] {{
  border-right: 3px solid {t['primary']} !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def live_hero_palette(favorite_team):
    """Subtle gradient + accent for sticky hero; tuned for contrast on dark backgrounds."""
    t = get_team_theme(favorite_team)
    return {
        "bg0": t["bg0"],
        "bg1": t["bg1"],
        "accent": t["accent"],
        "accent_soft": t["accent_soft"],
    }


def _render_live_game_center_empty(favorite_team, profile):
    """Multi-source-aware empty state: never claim 'no game' if today ET still has a schedule row."""
    ctx = get_live_game_detection_context(favorite_team)
    tier = ctx.get("tier", "no_game_window")
    if tier == "likely_live_feed_gap":
        st.error(ctx.get("message", ""))
    elif tier == "scheduled_today":
        st.warning(ctx.get("message", ""))
    elif tier == "window_off_today":
        st.warning(ctx.get("message", ""))
    else:
        st.warning(ctx.get("message", ""))
    stub = ctx.get("best_stub_game")
    if stub and isinstance(stub, dict):
        ht = stub.get("homeTeam") or {}
        aw = stub.get("awayTeam") or {}
        htr = (ht.get("teamTricode") or "") or _tricode_from_team_dict(ht)
        atr = (aw.get("teamTricode") or "") or _tricode_from_team_dict(aw)
        st.caption(
            f"Closest schedule row: **{_live_team_full_name(atr, aw)} @ {_live_team_full_name(htr, ht)}** · "
            f"_{stub.get('gameStatusText', '')}_ · source mix: live CDN + **scoreboardv2**."
        )
    opp = profile.get("current_opponent")
    if opp:
        st.info(
            f"Playoff profile matchup: **{favorite_team}** vs **{opp}** — detection also checks the opponent row on the same game."
        )
    if USE_DEMO_BACKUP:
        st.caption("Demo backup scores are ON in the sidebar — completed games still sync; live rows need the real schedule in the API.")
    if st.button("Refresh this page", key="live_empty_refresh"):
        st.rerun()
    if tier in ("likely_live_feed_gap", "scheduled_today", "window_off_today"):
        if st.button("Open Live Game Center anyway", key="live_empty_open"):
            st.session_state["page_override"] = "🏀 Live Game Center"
            st.rerun()


def _scoring_run_summary(actions, team_alias, window=40):
    """Lightweight 'run' read from recent play-by-play text (best-effort)."""
    if not actions:
        return None
    tail = actions[-window:]
    team_pts = 0
    opp_pts = 0
    for a in tail:
        tri = a.get("teamTricode") or ""
        desc = (a.get("description") or "").lower()
        if "made" not in desc and "makes" not in desc:
            continue
        if "free throw" in desc:
            pts = 1
        elif "3pt" in desc or "three" in desc:
            pts = 3
        else:
            pts = 2
        if tri == team_alias:
            team_pts += pts
        elif tri:
            opp_pts += pts
    if team_pts == 0 and opp_pts == 0:
        return None
    if team_pts >= opp_pts + 6:
        return f"Recent stretch: **{team_pts}-{opp_pts}** on the scoreboard in the last chunk of tracked plays — rhythm with the offense."
    if opp_pts >= team_pts + 6:
        return f"Opponent heating up in the log (**{opp_pts}-{team_pts}** in recent makes) — next stop changes the feel of the gym."
    return f"Tight trading baskets in the recent play log (**{team_pts}-{opp_pts}**)."


def _live_headline_natural(favorite_team, phase, margin, prob, period, status, opp_short):
    """Broadcast-style line without naming 'the fan perspective'."""
    nick = fan_nick(favorite_team)
    if phase == "postgame":
        if margin > 0:
            return f"{nick} closed the night in the win column — carry that into the series math."
        if margin < 0:
            return f"{nick} ran out of clock in this one — the tape room will point to the late possessions first."
        return f"{nick} leave the floor even — a coin-flip night that still tilts the series conversation."
    if phase == "pregame":
        return f"{nick} vs {opp_short}: lineups tighten, injuries matter, and the first six minutes usually set the whistle tone."
    if period >= 4 and abs(margin) <= 5:
        return f"Fourth-quarter territory — {nick} and {opp_short} trading blows with the season on every possession."
    if prob >= 62:
        return f"{nick} have the edge on the live model — pressure stays on {opp_short} to generate clean looks."
    if prob <= 38:
        return f"{nick} chasing in the model — the counter usually starts with a defensive burst and extra glass."
    return f"{nick} vs {opp_short} — {status or 'In progress'}."


def _pregame_pressure_lines(favorite_team, opp_name, series_line, profile):
    nick = fan_nick(favorite_team)
    rnd = profile.get("round", "Playoffs")
    seed = profile.get("seed", "—")
    lines = [
        f"{nick} walk into tonight with {rnd} stakes on every possession — seed {seed} is just a label once the ball is tossed.",
    ]
    if series_line:
        lines.append(f"The series strip reads {series_line} — another result swings who controls pace and the whistle narrative.")
    if opp_name:
        on = fan_nick(opp_name)
        lines.append(f"{on} pack counters to every switch; late-clock execution against their pressure shows up on tape immediately.")
    lines.append("The legacy conversation tightens with every closeout fourth quarter — tonight's margin sets the tone for the travel day.")
    return lines


def _profile_playoff_sched_hint(team_name, profile):
    p = profile or TEAM_PROFILES.get(team_name) or {}
    opp = p.get("current_opponent")
    if opp and p.get("status") == "Active":
        return (
            f"**Bracket profile (offline):** {team_name} vs **{opp}** — {p.get('round', 'Playoffs')}. "
            "Typical playoff tips are **7:00–8:30 PM ET** when the league has a night game."
        )
    return ""


def _short_matchup_tris(g):
    h = g.get("homeTeam") or {}
    a = g.get("awayTeam") or {}
    at = _tricode_from_team_dict(a) or str(a.get("teamTricode") or "?")
    ht = _tricode_from_team_dict(h) or str(h.get("teamTricode") or "?")
    return f"{at} @ {ht}"


def _live_gc_parse_game_row(game_row, favorite_team):
    """Normalize a scoreboard row for Live Game Center UI."""
    home = game_row.get("homeTeam") or {}
    away = game_row.get("awayTeam") or {}
    home_tri = (home.get("teamTricode") or "") or _tricode_from_team_dict(home)
    away_tri = (away.get("teamTricode") or "") or _tricode_from_team_dict(away)
    home_score = safe_int(home.get("score", 0))
    away_score = safe_int(away.get("score", 0))
    home_name = _live_team_full_name(home_tri, home)
    away_name = _live_team_full_name(away_tri, away)
    fav_alias = TEAM_ALIASES.get(favorite_team, "")
    if fav_alias and fav_alias == home_tri:
        is_fav_home = True
        fav_score, opp_score = home_score, away_score
        opp_name = away_name
    elif fav_alias and fav_alias == away_tri:
        is_fav_home = False
        fav_score, opp_score = away_score, home_score
        opp_name = home_name
    else:
        is_fav_home = favorite_team == home_name
        fav_score = home_score if is_fav_home else away_score
        opp_score = away_score if is_fav_home else home_score
        opp_name = away_name if is_fav_home else home_name
    period = safe_int(game_row.get("period", 0), 0)
    clock = str(game_row.get("gameClock") or "").strip()
    status = str(game_row.get("gameStatusText") or "Unknown").strip()
    phase = _live_broadcast_phase(game_row)
    return {
        "game": game_row,
        "gid": str(game_row.get("gameId") or ""),
        "home": home,
        "away": away,
        "home_tri": home_tri,
        "away_tri": away_tri,
        "home_name": home_name,
        "away_name": away_name,
        "home_score": home_score,
        "away_score": away_score,
        "fav_alias": fav_alias,
        "is_fav_home": is_fav_home,
        "fav_score": fav_score,
        "opp_score": opp_score,
        "opp_name": opp_name,
        "margin": fav_score - opp_score,
        "period": period,
        "clock": clock,
        "status": status,
        "phase": phase,
    }


def _live_gc_detection_banner(det_ctx, has_merged_live, phase):
    """User-facing feed status — never block the rest of the page."""
    tier = (det_ctx or {}).get("tier", "ok")
    msg = (det_ctx or {}).get("message", "")
    if tier == "ok" and has_merged_live:
        if phase == "live":
            st.success("Live scoreboard row detected — refreshing advanced sections below.")
        return
    if tier == "likely_live_feed_gap":
        st.error(msg or "Game may be in progress, but the live feed is delayed.")
    elif tier == "scheduled_today" and not has_merged_live:
        st.warning(msg or "Game scheduled today — live feed not detected yet.")
    elif tier == "window_off_today":
        st.warning(msg)
    elif msg:
        st.info(msg)


def _live_gc_render_status_card(snap):
    """Explain whether we have a scoreboard row, data source, and detection tier."""
    st.markdown("##### Scoreboard detection")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Game row", "yes" if snap.get("game_found") else "no")
    m2.metric("State", str(snap.get("game_status") or "—"))
    src = str(snap.get("data_source") or "—")
    m3.metric("Source", src[:16] + ("…" if len(src) > 16 else ""))
    m4.metric("Tier", str(snap.get("detection_tier") or "—"))
    if snap.get("game_found"):
        away_n = snap.get("away_team") or ""
        home_n = snap.get("home_team") or ""
        gst = snap.get("game_status_text") or "—"
        st.caption(f"Matchup: **{away_n}** @ **{home_n}** · League status text: _{gst}_")
    else:
        dm = snap.get("detection_message") or ""
        if dm:
            st.info(dm)
    errs = snap.get("error_messages") or []
    if errs:
        with st.expander("Fetch notes (non-fatal)", expanded=False):
            for err in errs:
                st.caption(str(err))


def _live_gc_bracket_context_expander_body(team_name):
    _, s = series_for_team(team_name)
    if not s:
        st.caption("No merged playoff series shell for this team in the app bracket yet.")
        return
    st.markdown(series_status_text(team_name, s))
    src = str(s.get("source") or "")
    if "Waiting for API games" in src:
        st.info(
            "This line comes from the **in-app bracket**, which updates when finished games import from the league feed. "
            "If it shows **0–0** during an active series, the bracket feed has not caught up — trust the **scoreboard row** "
            "and **game status** above when present."
        )


def _live_gc_bracket_context_expander(team_name):
    with st.expander("Playoff bracket context", expanded=False):
        _live_gc_bracket_context_expander_body(team_name)


def _render_live_gc_matchup_header(parsed, series_line=None):
    """Logos + score + quarter/clock — renders immediately (no box score required)."""
    e = html.escape
    away_logo = e(TEAM_LOGOS.get(parsed["away_name"], ""))
    home_logo = e(TEAM_LOGOS.get(parsed["home_name"], ""))
    if parsed["period"] and parsed["clock"]:
        clock_txt = f"Q{parsed['period']} · {parsed['clock']}"
    elif parsed["period"]:
        clock_txt = f"Q{parsed['period']}"
    else:
        clock_txt = parsed["status"]
    phase = parsed["phase"]
    badge = "🔴 LIVE" if phase == "live" else ("FINAL" if phase == "postgame" else "📅 PREGAME")
    series_html = f"<div class='live-gc-series'>Series · {e(series_line)}</div>" if series_line else ""
    st.markdown(
        f"<div class='live-gc-board'>"
        f"<div style='text-align:center'><img src='{away_logo}' alt=''/><div style='font-size:12px;font-weight:800'>{e(parsed['away_name'])}</div></div>"
        f"<div style='text-align:center'><div style='font-size:11px;color:#94a3b8'>{badge}</div>"
        f"<div class='live-gc-score'>{parsed['away_score']} — {parsed['home_score']}</div>"
        f"<div class='live-gc-clock'>{e(clock_txt)}</div>{series_html}</div>"
        f"<div style='text-align:center'><img src='{home_logo}' alt=''/><div style='font-size:12px;font-weight:800'>{e(parsed['home_name'])}</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _live_gc_render_fallback_content(
    favorite_team,
    profile,
    opp_name=None,
    include_outlook=True,
    show_bracket_expander=True,
    show_injuries=True,
):
    """When no merged game row: injuries + optional outlook; bracket optional."""
    opp = opp_name or profile.get("current_opponent")
    if opp:
        st.caption(f"Profile matchup: **{favorite_team}** vs **{opp}**")
    if show_bracket_expander:
        _live_gc_bracket_context_expander(favorite_team)
    if show_injuries:
        team_section_header("Injury report", "🩹")
        try:
            render_injury_report(favorite_team, opponent_name=opp, show_page_header=False, fan_perspective_team=favorite_team)
        except Exception as exc:
            st.caption(f"Injury report unavailable ({exc}).")
    if include_outlook:
        team_section_header("Team outlook", "🎯")
        try:
            render_team_outlook(favorite_team, compact_home=True)
        except Exception as exc:
            st.caption(f"Outlook unavailable ({exc}).")
    team_section_header("Recent top plays", "🎬")
    try:
        tp = previous_game_top_plays(favorite_team)
        if tp is not None and not tp.empty:
            st.dataframe(tp, use_container_width=True, hide_index=True)
        else:
            st.caption("Top plays appear when a recent game id exists in the playoff log.")
    except Exception as exc:
        st.caption(f"Top plays unavailable ({exc}).")


def _live_gc_top_performers(box_df, team_name, opp_name, limit=3):
    if box_df is None or box_df.empty:
        st.caption("Top performers load when the box score feed publishes player rows.")
        return
    cols = st.columns(2)
    for col, (label, tm) in zip(
        cols,
        [(fan_nick(team_name), TEAM_ALIASES.get(team_name)), (fan_nick(opp_name or "Opponent"), TEAM_ALIASES.get(opp_name, ""))],
    ):
        with col:
            st.markdown(f"**{label}**")
            sub = box_df[box_df["Team"] == tm] if tm else pd.DataFrame()
            if sub.empty:
                st.caption("No rows yet.")
                continue
            sub = sub.sort_values("PTS", ascending=False).head(limit)
            for _, r in sub.iterrows():
                st.markdown(
                    f"<div class='live-gc-perf'><b>{html.escape(str(r.get('Player','')))}</b> "
                    f"{player_temp(r)} · {safe_int(r.get('PTS'))} PTS · "
                    f"{safe_int(r.get('REB'))} REB · {safe_int(r.get('AST'))} AST · "
                    f"+/- {safe_int(r.get('+/-'))}</div>",
                    unsafe_allow_html=True,
                )


def _live_gc_foul_trouble(box_df, team_name, opp_name):
    if box_df is None or box_df.empty:
        st.caption("Foul trouble updates when personal fouls appear in the box score.")
        return
    any_row = False
    for tm_label, tm in ((fan_nick(team_name), TEAM_ALIASES.get(team_name)), (opp_name or "Opponent", TEAM_ALIASES.get(opp_name or ""))):
        if not tm:
            continue
        trouble = box_df[(box_df["Team"] == tm) & (box_df["PF"].apply(lambda x: safe_int(x) >= 4))]
        if trouble.empty:
            continue
        any_row = True
        st.markdown(f"**{tm_label}**")
        for _, r in trouble.iterrows():
            pf = safe_int(r.get("PF"))
            flag = "🚨 FOUL OUT RISK" if pf >= 5 else "⚠️ IN FOUL TROUBLE"
            st.warning(f"{r.get('Player','?')} — {pf} PF · {flag}")
    if not any_row:
        st.success("No players at 4+ fouls in the current box score feed.")


def _live_gc_whatif_panel(favorite_team, margin, period, is_home, base_prob):
    st.caption("Quick what-if — adjusts the live win-probability model (not Vegas odds).")
    swing = st.slider("Swing margin for your team (+/− points on the board)", -18, 18, 0, key=f"live_gc_swing_{favorite_team}")
    adj_margin = margin + swing
    adj_prob = win_prob(adj_margin, period, is_home)
    c1, c2 = st.columns(2)
    c1.metric("Model win % (now)", f"{base_prob}%")
    c2.metric("Model win % (what-if)", f"{adj_prob}%", delta=f"{adj_prob - base_prob}")
    star = (TEAM_PROFILES.get(favorite_team, {}).get("starters") or ["Your star"])[0]
    extra = st.slider(f"Extra points for {star} (storytelling slider)", 0, 15, 0, key=f"live_gc_star_{favorite_team}")
    if extra:
        st.info(
            f"If {star} adds **{extra}** points of impact, the night tilts toward {fan_nick(favorite_team)} — "
            "open **Legacy Tracker** for full ladder sliders and round-by-round legacy math."
        )


def _live_gc_section(title, icon, fn, *args, **kwargs):
    """Render a Live GC block; failures stay local."""
    team_section_header(title, icon)
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        st.caption(f"{title} could not load right now ({exc}).")


def _live_center_debug_probe():
    """Probe CDN + merged stats slate (yesterday→tomorrow ET); must not raise."""
    errs = []
    n_cdn = -999
    try:
        if NBA_LIVE_AVAILABLE:
            g = get_live_games()
            n_cdn = len(g) if isinstance(g, list) else -1
        else:
            n_cdn = -1
    except Exception as e:
        n_cdn = -1
        errs.append(f"live scoreboard: {e!r}")
    n_stats_window = -999
    try:
        if NBA_STATS_AVAILABLE:
            n_stats_window = len(_merged_stats_games_et_window())
        else:
            n_stats_window = -1
    except Exception as e:
        n_stats_window = -1
        errs.append(f"stats scoreboard (ET window): {e!r}")
    return n_cdn, n_stats_window, errs


def _live_gc_render_debug_panel(favorite_team, fb, det_ctx):
    n_cdn, n_stats, probe_errs = _live_center_debug_probe()
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("NBA_LIVE_AVAILABLE", "yes" if NBA_LIVE_AVAILABLE else "no")
    d2.metric("NBA_STATS_AVAILABLE", "yes" if NBA_STATS_AVAILABLE else "no")
    d3.metric("Live CDN games", str(n_cdn) if n_cdn >= 0 else "err")
    d4.metric("Stats slate (3 ET days)", str(n_stats) if n_stats >= 0 else "err")
    st.write(f"**Team:** {favorite_team} · **detection tier:** `{det_ctx.get('tier')}`")
    if isinstance(fb, dict) and fb.get("_merge_error"):
        st.warning(fb["_merge_error"])
    if probe_errs:
        st.error("\n".join(probe_errs))
    with st.expander("Raw scoreboard pipeline", expanded=False):
        try:
            st.code(_scoreboard_pipeline_debug_report(), language="text")
        except Exception as exc:
            st.write(repr(exc))


def render_live_game_center(favorite_team, profile):
    """Live Game Center — multi-source game detection (`get_current_or_today_game`); heavy widgets load after header."""
    render_fan_page_hero(
        favorite_team,
        "Live Game Center",
        f"Real-time board for {fan_nick(favorite_team)}.",
        "LIVE HUB",
    )

    if st.session_state.get("_live_gc_sel_team") != favorite_team:
        for k in list(st.session_state.keys()):
            if isinstance(k, str) and k.startswith("live_gc__"):
                del st.session_state[k]
        st.session_state["_live_gc_sel_team"] = favorite_team

    snap = get_current_or_today_game(favorite_team)
    det_ctx = snap.get("det_ctx") or {}
    game_row = snap.get("game_row")
    tier = snap.get("detection_tier") or ""

    fb = None
    try:
        fb = featured_broadcast_state(favorite_team)
    except Exception:
        fb = None

    _live_gc_render_status_card(snap)

    if tier == "likely_live_feed_gap":
        st.error(snap.get("detection_message") or "Game may be in progress, but the live feed is delayed.")
    elif tier == "scheduled_today" and snap.get("game_found"):
        st.warning(snap.get("detection_message") or "Game scheduled today — live feed not detected yet.")

    if game_row:
        parsed = _live_gc_parse_game_row(game_row, favorite_team)
        series_line, _src = _live_series_board(parsed["away_name"], parsed["home_name"])

        _render_live_gc_matchup_header(parsed, series_line)
        render_live_score_banner(
            favorite_team,
            parsed["away_tri"],
            parsed["home_tri"],
            parsed["away_score"],
            parsed["home_score"],
            parsed["status"],
            parsed["phase"],
        )

        if parsed["phase"] == "live":
            st.success("**LIVE NOW** — this row is from the merged NBA scoreboard feed.")
        elif parsed["phase"] == "pregame":
            st.info("**GAME TODAY / PREGAME** — opponent and tip/status are from the league scoreboard.")
        else:
            st.info("**FINAL** — full detail below when box score and play-by-play publish.")

        if AUTOREFRESH_AVAILABLE and parsed["phase"] == "live":
            st_autorefresh(interval=12000, key="live_gc_refresh")
            st.caption("Auto-refresh every **12s** while the game is **live**.")

        with st.expander("Series & bracket context", expanded=False):
            try:
                if series_line:
                    st.markdown(f"**Series strip:** {series_line}")
                _live_gc_bracket_context_expander_body(favorite_team)
            except Exception as exc:
                st.caption(str(exc))

        gid = parsed["gid"]
        box_game, box_df, actions = {}, pd.DataFrame(), []
        if gid:
            try:
                box_game = get_live_boxscore(gid) or {}
            except Exception:
                pass
            try:
                box_df = create_boxscore_df(box_game)
            except Exception:
                pass
            try:
                actions = get_live_playbyplay(gid) or []
            except Exception:
                pass

        team_section_header("Momentum & win probability", "📈")
        try:
            prob = win_prob(parsed["margin"], parsed["period"], parsed["is_fav_home"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Win probability (model)", f"{prob}%")
            c2.metric("Your margin", f"{parsed['margin']:+d}")
            c3.metric("Clock", f"Q{parsed['period']}" if parsed["period"] else parsed["status"])
            headline = _live_headline_natural(
                favorite_team,
                parsed["phase"],
                parsed["margin"],
                prob,
                parsed["period"],
                parsed["status"],
                fan_nick(parsed["opp_name"]),
            )
            st.markdown(f"**Broadcast read:** {headline}")
            run = _scoring_run_summary(actions, parsed["fav_alias"])
            if run:
                st.markdown(run)
        except Exception as exc:
            st.caption(str(exc))

        with st.expander("What-if swing (model only)", expanded=False):
            try:
                prob = win_prob(parsed["margin"], parsed["period"], parsed["is_fav_home"])
                _live_gc_whatif_panel(
                    favorite_team, parsed["margin"], parsed["period"], parsed["is_fav_home"], prob
                )
            except Exception as exc:
                st.caption(str(exc))

        with st.expander("Injuries & opponent report", expanded=False):
            try:
                c1, c2 = st.columns(2)
                with c1:
                    render_injury_report(
                        favorite_team,
                        opponent_name=parsed["opp_name"],
                        show_page_header=False,
                        fan_perspective_team=favorite_team,
                    )
                with c2:
                    if parsed["opp_name"]:
                        render_injury_report(
                            parsed["opp_name"],
                            show_page_header=False,
                            neutral_framing=True,
                        )
            except Exception as exc:
                st.caption(str(exc))

        with st.expander("Key players & lineup cards", expanded=False):
            try:
                render_lineup_cards(favorite_team, box_df)
            except Exception as exc:
                st.caption(str(exc))

        with st.expander("Top performers & foul trouble", expanded=False):
            try:
                _live_gc_top_performers(box_df, favorite_team, parsed["opp_name"])
                _live_gc_foul_trouble(box_df, favorite_team, parsed["opp_name"])
            except Exception as exc:
                st.caption(str(exc))

        with st.expander("Game storylines", expanded=False):
            try:
                prob = win_prob(parsed["margin"], parsed["period"], parsed["is_fav_home"])
                for line in game_story(favorite_team, parsed["margin"], prob, box_df):
                    st.write(f"• {line}")
            except Exception as exc:
                st.caption(str(exc))

        with st.expander("Play-by-play highlights & shot chart", expanded=False):
            try:
                if gid:
                    tp = top_plays_from_game_id(gid, favorite_team, limit=10)
                    if tp is not None and not tp.empty:
                        st.dataframe(tp, use_container_width=True, hide_index=True)
                    else:
                        st.caption("Highlights populate when the play-by-play feed returns tagged events.")
                else:
                    st.caption("No game id on this scoreboard row.")
                if actions:
                    shots = shot_df_from_pbp(actions, parsed["fav_alias"])
                    if not shots.empty:
                        st.plotly_chart(
                            draw_court(shots, f"{fan_nick(favorite_team)} shot chart (PBP proxy)"),
                            use_container_width=True,
                        )
                    else:
                        st.caption("Shot chart needs shot-level descriptions in the action feed.")
                else:
                    st.caption("Shot chart loads after play-by-play returns.")
            except Exception as exc:
                st.caption(str(exc))

        with st.expander("Full box score table", expanded=False):
            if box_df is not None and not box_df.empty:
                render_fan_stat_table(box_df, favorite_team)
            else:
                st.caption("Player rows publish when the live box score endpoint responds.")

        if parsed["phase"] == "postgame":
            with st.expander("Postgame notes", expanded=False):
                st.caption("Use **top performers** above for tonight's standout; **Recent top plays** on the Hub uses the playoff game log.")
                try:
                    st.markdown(f"**Bracket:** {series_status_text(favorite_team)}")
                except Exception:
                    pass

        with st.expander("Developer debug", expanded=False):
            _live_gc_render_debug_panel(favorite_team, fb, det_ctx)
        return

    if tier in ("no_game_window", "window_off_today", "unknown"):
        _render_live_game_center_empty(favorite_team, profile)

    if tier == "scheduled_today":
        st.markdown(f"#### Game today · **{fan_nick(favorite_team)}**")
        opp = profile.get("current_opponent")
        if opp:
            st.markdown(f"**Profile opponent:** {opp}")
        with st.expander("Pregame — injuries & storylines", expanded=True):
            try:
                render_injury_report(
                    favorite_team,
                    opponent_name=opp,
                    show_page_header=False,
                    fan_perspective_team=favorite_team,
                )
                if opp:
                    render_injury_report(opp, show_page_header=False, neutral_framing=True)
                strengths = profile.get("strengths") or []
                concerns = profile.get("concerns") or []
                if strengths:
                    st.markdown("**Storylines — strengths**")
                    for s in strengths[:4]:
                        st.write(f"• {s}")
                if concerns:
                    st.markdown("**Storylines — watch list**")
                    for s in concerns[:4]:
                        st.write(f"• {s}")
            except Exception as exc:
                st.caption(str(exc))
        _live_gc_bracket_context_expander(favorite_team)
        _live_gc_render_fallback_content(
            favorite_team,
            profile,
            include_outlook=False,
            show_bracket_expander=False,
            show_injuries=False,
        )
        if st.button("Refresh scoreboard", key="live_gc_refresh_sched"):
            st.rerun()
    elif tier == "likely_live_feed_gap":
        stub = det_ctx.get("best_stub_game")
        if stub:
            try:
                parsed_stub = _live_gc_parse_game_row(stub, favorite_team)
                _render_live_gc_matchup_header(parsed_stub, None)
                render_live_score_banner(
                    favorite_team,
                    parsed_stub["away_tri"],
                    parsed_stub["home_tri"],
                    parsed_stub["away_score"],
                    parsed_stub["home_score"],
                    parsed_stub["status"],
                    parsed_stub["phase"],
                )
            except Exception:
                pass
        if st.button("Refresh scoreboard", key="live_gc_refresh_gap"):
            st.rerun()
        _live_gc_render_fallback_content(favorite_team, profile, include_outlook=False)
    else:
        _live_gc_render_fallback_content(favorite_team, profile, include_outlook=True)

    with st.expander("Developer debug", expanded=False):
        _live_gc_render_debug_panel(favorite_team, fb, det_ctx)



# ==========================================================
# Previous rounds / playoff path helpers
# ==========================================================
FALLBACK_GAME_MVPS = {
    ("New York Knicks", "Atlanta Hawks", 1): ("Jalen Brunson", "Controlled the half court and gave New York the Game 1 tone."),
    ("New York Knicks", "Atlanta Hawks", 2): ("Trae Young", "Late-shot creation and pressure helped Atlanta steal a road game."),
    ("New York Knicks", "Atlanta Hawks", 3): ("Trae Young", "Carried Atlanta's offense in a one-possession finish."),
    ("New York Knicks", "Atlanta Hawks", 4): ("Jalen Brunson", "Reset the series for New York with stronger offensive control."),
    ("New York Knicks", "Atlanta Hawks", 5): ("Karl-Anthony Towns", "Spacing and scoring changed the geometry of the Knicks offense."),
    ("New York Knicks", "Atlanta Hawks", 6): ("Jalen Brunson", "Closed the series with lead-guard control and playoff poise."),
    ("New York Knicks", "Philadelphia 76ers", 1): ("Jalen Brunson", "Set the pace for New York's second-round opener."),
    ("New York Knicks", "Philadelphia 76ers", 2): ("Jalen Brunson", "Protected the late-game margin and pushed the Knicks to a 2-0 series edge."),
    ("Detroit Pistons", "Orlando Magic", 1): ("Paolo Banchero", "Powered Orlando's Game 1 road win."),
    ("Detroit Pistons", "Orlando Magic", 2): ("Cade Cunningham", "Got Detroit's offense organized and tied the series."),
    ("Detroit Pistons", "Orlando Magic", 3): ("Paolo Banchero", "Kept Orlando ahead with star-level shot creation."),
    ("Detroit Pistons", "Orlando Magic", 4): ("Franz Wagner", "Gave Orlando secondary scoring and two-way stability."),
    ("Detroit Pistons", "Orlando Magic", 5): ("Cade Cunningham", "Kept Detroit alive with command of the offense."),
    ("Detroit Pistons", "Orlando Magic", 6): ("Jalen Duren", "Controlled the glass and helped extend the series."),
    ("Detroit Pistons", "Orlando Magic", 7): ("Cade Cunningham", "Delivered the Game 7 control that sent Detroit forward."),
    ("Detroit Pistons", "Cleveland Cavaliers", 1): ("Cade Cunningham", "Organized Detroit's offense and gave the Pistons the series lead."),
    ("Detroit Pistons", "Cleveland Cavaliers", 2): ("Cade Cunningham", "Pushed Detroit to a 2-0 lead with steady lead-option control."),
}

def infer_opponent_from_matchup(matchup, team_name):
    if not matchup or " at " not in str(matchup):
        return "Opponent"
    left, right = str(matchup).split(" at ", 1)
    def short_name(full):
        return full.replace("New York ", "").replace("Philadelphia ", "").replace("Atlanta ", "").replace("Detroit ", "").replace("Cleveland ", "").replace("Oklahoma City ", "").replace("Los Angeles ", "").replace("San Antonio ", "").replace("Minnesota ", "").replace("Portland ", "").replace("Phoenix ", "").strip()
    team_short = short_name(team_name)
    if team_short in left:
        return right
    if team_short in right:
        return left
    return left if right == team_short else right

def mvp_for_game(team_a, team_b, game_num, winner=None):
    for key in [(team_a, team_b, game_num), (team_b, team_a, game_num)]:
        if key in FALLBACK_GAME_MVPS:
            return FALLBACK_GAME_MVPS[key]
    # Generic but still concrete: use the main creator/anchor from winner if known.
    chosen_team = winner if winner in TEAM_PROFILES else team_a
    candidates = TEAM_PROFILES.get(chosen_team, {}).get("starters", [])
    name = candidates[0] if candidates else "Top performer"
    return name, f"Best estimated standout for {chosen_team} based on the game result and team role hierarchy."

def get_current_series_games_for_previous_rounds(team_name):
    _, s = second_round_series_for_team(team_name)
    return _series_games_for_history(team_name, s) if s else []


def _series_games_for_history(team_name, series_dict):
    """Build game rows for history cards from any series shell containing team_name."""
    if not series_dict or not series_dict.get("games"):
        return []
    a, b = series_dict["a"], series_dict["b"]
    opp = b if team_name == a else a
    games = []
    for idx, g in enumerate(series_dict.get("games", []), start=1):
        row = dict(g)
        row["Game"] = row.get("Game") or f"Game {idx}"
        row["Matchup"] = row.get("Matchup") or f"{team_name} vs {opp}"
        mvp, why = mvp_for_game(team_name, opp, idx, row.get("Winner"))
        row["Game MVP"] = row.get("Game MVP") or mvp
        row["MVP Note"] = row.get("MVP Note") or why
        games.append(row)
    return games

def render_series_history_card(team_a, team_b, games, round_label, result_text=None):
    if not games:
        st.info(f"No game results available yet for {team_a} vs {team_b}.")
        return
    a_wins = sum(1 for g in games if g.get("Winner") == team_a)
    b_wins = sum(1 for g in games if g.get("Winner") == team_b)
    st.markdown(f"<div class='history-card'>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1.2,.8,1.2])
    with c1:
        st.image(TEAM_LOGOS.get(team_a,""), width=82)
        st.markdown(f"<div class='history-team'>({TEAM_PROFILES[team_a]['seed']}) {team_a}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='history-score'>{a_wins} - {b_wins}</div>", unsafe_allow_html=True)
        st.caption(round_label)
    with c3:
        st.image(TEAM_LOGOS.get(team_b,""), width=82)
        st.markdown(f"<div class='history-team'>({TEAM_PROFILES[team_b]['seed']}) {team_b}</div>", unsafe_allow_html=True)
    if result_text:
        st.info(result_text)
    for idx, g in enumerate(games, start=1):
        game_num = g.get("Game", f"Game {idx}")
        try:
            n = int(str(game_num).replace("Game", "").strip())
        except Exception:
            n = idx
        if "Game MVP" not in g:
            mvp, why = mvp_for_game(team_a, team_b, n, g.get("Winner"))
        else:
            mvp, why = g.get("Game MVP"), g.get("MVP Note", "Standout performer for this game.")
        st.markdown(f"<div class='game-row'><b>{game_num}</b> · {g.get('Date','Date TBD')} · {g.get('Matchup', team_a+' vs '+team_b)}<br><b>Score:</b> {g.get('Score','Score TBD')}<br><span class='mvp-pill'>Game MVP: {mvp}</span><br><span style='color:#475569'>{why}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_previous_rounds_history(team_name):
    profile = TEAM_PROFILES[team_name]
    first_opp = profile["first_round_opponent"]
    render_fan_page_hero(team_name, "Playoff path so far", "Every round you played — scores, MVPs, and series results.", "PLAYOFF HISTORY")
    team_section_header("Round-by-round results", "📜")
    first_games = []
    for idx, row in enumerate(FIRST_ROUND_GAME_SCORES.get(team_name, []), start=1):
        r = dict(row)
        n = int(r.get("Game", idx)) if str(r.get("Game", idx)).isdigit() else idx
        mvp, why = mvp_for_game(team_name, first_opp, n, r.get("Winner"))
        r["Game"] = f"Game {n}"
        r["Game MVP"] = mvp
        r["MVP Note"] = why
        first_games.append(r)
    render_series_history_card(team_name, first_opp, first_games, "First Round", profile.get("first_round_result"))

    _, s2 = second_round_series_for_team(team_name)
    if s2 and s2.get("games"):
        opp2 = s2["b"] if team_name == s2["a"] else s2["a"]
        second_games = get_current_series_games_for_previous_rounds(team_name)
        sr_note = f"{s2['winner']} wins the series." if s2.get("winner") else None
        render_series_history_card(team_name, opp2, second_games, "Second Round", sr_note)

    stt_paths = get_playoff_state_cached(True)
    for round_label, coll in (("Conference Finals", stt_paths["cf"]), ("NBA Finals", stt_paths["finals"])):
        for _k, s in (coll or {}).items():
            if team_name not in (s.get("a"), s.get("b")):
                continue
            opp = s["b"] if team_name == s["a"] else s["a"]
            games = _series_games_for_history(team_name, s)
            if not games:
                continue
            note = f"{s.get('winner')} wins the {round_label}." if s.get("winner") else None
            render_series_history_card(team_name, opp, games, round_label, note)

# ==========================================================
# Sidebar
# ==========================================================
PAGES={
    "🏀 Home Dashboard":"Home Dashboard",
    "🏀 Live Game Center":"Live Game Center",
    "🏀 Playoff Bracket":"Playoff Bracket",
    "🧠 Matchup Intelligence":"Matchup Intelligence",
    "🏀 Matchup Lineups":"Matchup Lineups",
    "🏀 Player Playoff Tracker":"Player Playoff Tracker",
    "🏀 Legacy Tracker":"Legacy Tracker",
    "🏀 Previous Rounds":"Previous Rounds",
}


def _sidebar_team_label(team_name):
    """Mark eliminated teams so offseason Home sections are easy to find in the picker."""
    try:
        if _is_home_eliminated(team_name):
            return f"📋 {team_name} (offseason view)"
    except Exception:
        if TEAM_PROFILES.get(team_name, {}).get("status") == "Eliminated":
            return f"📋 {team_name} (offseason view)"
    return team_name


_team_keys_sorted = sorted(TEAM_PROFILES.keys())
_default_idx = _team_keys_sorted.index("New York Knicks") if "New York Knicks" in _team_keys_sorted else 0
favorite_team = st.sidebar.selectbox(
    "Choose your 2026 NBA playoff team",
    _team_keys_sorted,
    index=_default_idx,
    format_func=_sidebar_team_label,
    help="Pick any team labeled “(offseason view)” — that means the bracket shows their playoff run is over (any round), not only first-round exits.",
)
st.sidebar.caption(
    "**Where are those sections?** On **🏀 Home Dashboard**, pick a team marked **(offseason view)** above — "
    "that label appears whenever the **merged bracket** shows that club lost a completed series (first round through Finals), "
    "for example Philadelphia, the Lakers, or Cleveland if their series is over."
)
USE_DEMO_BACKUP = st.sidebar.toggle(
    "Use demo backup scores only if NBA API has no game data",
    value=False,
    help="Leave this OFF for true automatic tracking. Turn it ON only when testing or when nba_api is unavailable."
)
profile=TEAM_PROFILES[favorite_team]
inject_team_brand_css(favorite_team)
labels=list(PAGES.keys())
def_label=st.session_state.pop("page_override", "🏀 Home Dashboard")
page_label=st.sidebar.radio("Choose page", labels, index=labels.index(def_label) if def_label in labels else 0)
page=PAGES[page_label]

# ==========================================================
# Pages
# ==========================================================
if page == "Home Dashboard":
    render_playoff_command_center(favorite_team)

elif page == "Playoff Bracket":
    render_bracket(favorite_team)

elif page == "Matchup Intelligence":
    render_matchup_intelligence(favorite_team)

elif page == "Previous Rounds":
    st.header(f"{profile['conference']} Previous Rounds")
    render_matchup_header(favorite_team, first_round=True)
    render_previous_rounds_history(favorite_team)

elif page == "Live Game Center":
    render_live_game_center(favorite_team, profile)

elif page == "Player Playoff Tracker":
    render_matchup_header(favorite_team)
    render_player_playoff_story_hub(favorite_team, profile)

elif page == "Legacy Tracker":
    render_legacy_tracker_page(favorite_team)

elif page == "Matchup Lineups":
    render_matchup_header(favorite_team)
    if profile["status"] != "Active": st.warning("This team is eliminated, so current matchup lineups are not active.")
    else:
        opp=profile["current_opponent"]
        st.subheader("Projected Starter Matchups")
        st.caption("Starter/rotation estimates use NBA API current-season minutes when available. Actual playoff starters can still change by injury, matchup choice, or coaching decision.")
        st.dataframe(matchup_advantages(favorite_team, opp), use_container_width=True)

        st.subheader("Current Rosters from NBA API")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{favorite_team} current roster / rotation**")
            roster = fetch_current_roster(favorite_team)
            rotation = fetch_team_rotation_by_minutes(favorite_team)
            if not rotation.empty:
                st.dataframe(rotation.drop(columns=[c for c in ["MIN_SORT"] if c in rotation.columns]).head(12), use_container_width=True)
            elif not roster.empty:
                st.dataframe(roster, use_container_width=True)
            else:
                st.warning("NBA API roster lookup failed. Showing backup saved names.")
                st.dataframe(pd.DataFrame({"Player": current_roster_names(favorite_team)}), use_container_width=True)
        with c2:
            st.markdown(f"**{opp} current roster / rotation**")
            roster = fetch_current_roster(opp)
            rotation = fetch_team_rotation_by_minutes(opp)
            if not rotation.empty:
                st.dataframe(rotation.drop(columns=[c for c in ["MIN_SORT"] if c in rotation.columns]).head(12), use_container_width=True)
            elif not roster.empty:
                st.dataframe(roster, use_container_width=True)
            else:
                st.warning("NBA API roster lookup failed. Showing backup saved names.")
                st.dataframe(pd.DataFrame({"Player": current_roster_names(opp)}), use_container_width=True)

        st.subheader("Top Bench / Rotation Players")
        bench=[{"Team":favorite_team,"Player":p} for p in estimated_bench_from_api(favorite_team)]+[{"Team":opp,"Player":p} for p in estimated_bench_from_api(opp)]
        st.dataframe(pd.DataFrame(bench), use_container_width=True)

st.divider()
st.caption("Daniel Cohen — NBA Playoff Companion AI | automatic series tracking | previous rounds | live game center | shot chart")
