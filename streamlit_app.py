
from typing import Any
import html
import os
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

# Stable Streamlit widget keys for team/page sidebar (match nba_persistent_state.py).
NBA_TEAM_SELECT_KEY = "favorite_team_sidebar"
NBA_PAGE_RADIO_KEY = "nba_choose_page"
try:
    from nba_persistent_state import NBA_PAGE_RADIO_KEY as _NBA_PAGE_KEY
    from nba_persistent_state import NBA_TEAM_SELECT_KEY as _NBA_TEAM_KEY

    NBA_PAGE_RADIO_KEY = _NBA_PAGE_KEY
    NBA_TEAM_SELECT_KEY = _NBA_TEAM_KEY
except Exception:
    pass

try:
    from suite_workspace import can_show_developer_tools, is_developer_workspace
except ImportError:
    def can_show_developer_tools(*, st: Any = None) -> bool:  # type: ignore[misc]
        return False

    def is_developer_workspace(*, st: Any = None, workspace_id: str | None = None) -> bool:  # type: ignore[misc]
        return False

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
# Page setup (Streamlit UI — only runs inside main())
# ==========================================================
GLOBAL_APP_CSS = """
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
/* Unified fan platform: matchup ribbon, status, skeletons */
.fan-matchup-ribbon {
  display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px;
  padding: 10px 14px; border-radius: 14px; margin: 0 0 14px;
  background: linear-gradient(135deg, var(--team-bg0,#0f172a) 0%, var(--team-bg1,#1e293b) 100%);
  border: 1px solid var(--team-border, rgba(148,163,184,.35));
  color: #f8fafc; font-size: 13px;
}
.fan-matchup-ribbon--elim { opacity: .92; border-color: rgba(148,163,184,.25); }
.fan-matchup-ribbon--wait { border-style: dashed; }
.fan-ribbon-badge {
  font-size: 10px; font-weight: 900; letter-spacing: .1em; text-transform: uppercase;
  padding: 4px 10px; border-radius: 999px;
  background: var(--team-accent-soft, rgba(56,189,248,.2));
  border: 1px solid var(--team-border); color: var(--team-accent,#38bdf8);
}
.fan-ribbon-score { font-size: 1.05rem; font-weight: 900; letter-spacing: -.02em; }
.fan-ribbon-muted { color: #94a3b8; font-size: 12px; }
.fan-skel-wrap { margin: 8px 0 14px; }
.fan-skel-label { font-size: 11px; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
.fan-skel-line {
  height: 12px; border-radius: 8px; margin-bottom: 8px;
  background: linear-gradient(90deg, #e2e8f0 0%, #f1f5f9 45%, #e2e8f0 90%);
  background-size: 200% 100%; animation: fanSkelPulse 1.2s ease-in-out infinite;
}
.fan-skel-line:nth-child(2) { width: 88%; animation-delay: .15s; }
.fan-skel-line:nth-child(3) { width: 72%; animation-delay: .3s; }
@keyframes fanSkelPulse { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
.fan-sec {
  margin: 20px 0 0; padding: 10px 14px 8px;
  border-left: 4px solid var(--team-primary, #38bdf8);
  border-radius: 12px 12px 0 0;
  background: linear-gradient(90deg, var(--team-accent-soft, rgba(56,189,248,.12)), transparent 72%);
}
.fan-sec--live { border-left-color: #ef4444; background: linear-gradient(90deg, rgba(239,68,68,.18), transparent 70%); }
.fan-sec--soon { border-left-color: #f59e0b; background: linear-gradient(90deg, rgba(245,158,11,.16), transparent 70%); }
.fan-sec--elim { border-left-color: #94a3b8; opacity: .95; }
.fan-sec--broadcast { border-left-color: var(--team-accent, #38bdf8); }
.fan-sec-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.fan-sec-icon { font-size: 1.1rem; line-height: 1; }
.fan-sec-title { font-size: 13px; font-weight: 900; letter-spacing: .08em; text-transform: uppercase; color: var(--team-accent, #64748b); }
.fan-sec-cap { font-size: 12px; color: #64748b; margin-top: 4px; line-height: 1.4; font-weight: 600; }
.fan-sec-body {
  border: 1px solid var(--team-border, rgba(148,163,184,.28));
  border-top: none; border-radius: 0 0 16px 16px;
  padding: 14px 16px; margin: 0 0 16px;
  background: linear-gradient(180deg, #fff 0%, var(--team-card-tint, #f8fafc) 100%);
  box-shadow: 0 2px 10px rgba(15,23,42,.06);
}
.fan-sec-body--empty { color: #64748b; font-size: 13px; line-height: 1.45; font-style: italic; }
.fan-energy-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin: 4px 0 8px; }
.fan-energy-card {
  border-radius: 16px; padding: 14px 15px; min-height: 118px;
  background: linear-gradient(165deg, #fff 0%, var(--team-card-tint, #f8fafc) 100%);
  border: 1px solid var(--team-border, rgba(148,163,184,.32));
  box-shadow: 0 8px 22px rgba(15,23,42,.08);
}
.fan-energy-card--hot {
  border-color: var(--team-primary, #38bdf8);
  box-shadow: 0 0 0 1px var(--team-accent-soft, rgba(56,189,248,.2)), 0 10px 26px rgba(15,23,42,.12);
}
.fan-energy-card--spotlight { background: linear-gradient(145deg, var(--team-accent-soft), #fff 55%); }
.fan-energy-k { display: flex; align-items: center; gap: 8px; font-size: 10px; font-weight: 950; letter-spacing: .12em; text-transform: uppercase; color: var(--team-primary, #64748b); margin-bottom: 8px; }
.fan-energy-icon { font-size: 1.05rem; line-height: 1; }
.fan-energy-t { font-size: 14px; font-weight: 900; color: #0f172a; margin-bottom: 6px; line-height: 1.2; }
.fan-energy-b { font-size: 13px; color: #475569; line-height: 1.45; }
.fan-storyline-bar {
  margin-top: 10px; padding: 12px 14px; border-radius: 14px;
  background: linear-gradient(90deg, var(--team-accent-soft), rgba(148,163,184,.08));
  border: 1px solid var(--team-border); font-size: 13px; color: #334155; line-height: 1.45;
}
.os-card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin: 10px 0 14px; }
.os-card {
  border-radius: 16px; padding: 14px; background: #fff;
  border: 1px solid var(--team-border); box-shadow: 0 6px 18px rgba(15,23,42,.07);
}
.os-card-k { font-size: 10px; font-weight: 950; letter-spacing: .1em; text-transform: uppercase; color: var(--team-primary); margin-bottom: 6px; }
.os-card-t { font-size: 14px; font-weight: 900; color: #0f172a; margin-bottom: 6px; }
.os-card-b { font-size: 13px; color: #475569; line-height: 1.42; }
.os-card-b ul { margin: 6px 0 0; padding-left: 18px; }
.home-live-strip--soon { animation: homeSoonPulse 2.6s ease-in-out infinite; }
@keyframes homeSoonPulse {
  0%, 100% { box-shadow: 0 12px 40px rgba(245,158,11,.2); }
  50% { box-shadow: 0 14px 48px rgba(251,191,36,.38); }
}
.home-live-badge {
  display: inline-block; font-size: 10px; font-weight: 950; letter-spacing: .14em;
  padding: 4px 10px; border-radius: 999px; margin-bottom: 8px;
  background: rgba(239,68,68,.35); border: 1px solid rgba(252,165,165,.65); color: #fecaca;
}
.home-live-strip--soon .home-live-badge { background: rgba(245,158,11,.3); border-color: rgba(253,224,71,.55); color: #fde68a; }
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
.pp-stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(108px, 1fr)); gap: 10px; margin: 8px 0 14px; }
.pp-stat-pill {
  text-align: center; padding: 12px 10px; border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, var(--team-card-tint, #f8fafc) 100%);
  border: 1px solid var(--team-border, rgba(148,163,184,.28)); box-shadow: 0 4px 14px rgba(15,23,42,.06);
}
.pp-stat-pill .v { font-size: 1.55rem; font-weight: 950; color: #0f172a; line-height: 1; }
.pp-stat-pill .k { font-size: 9px; font-weight: 900; letter-spacing: .1em; text-transform: uppercase; color: #64748b; margin-top: 4px; }
.pp-stat-pill.hot .v { color: var(--team-primary, #0ea5e9); }
.pp-chase-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; margin: 10px 0 14px; }
.pp-chase-hero {
  display: grid; grid-template-columns: auto 1fr; gap: 16px; align-items: center;
  padding: 16px 18px; border-radius: 18px; margin-bottom: 12px;
  background: linear-gradient(135deg, var(--team-bg0,#0f172a) 0%, var(--team-bg1,#1e293b) 70%);
  border: 1px solid var(--team-border); color: #f8fafc;
  box-shadow: 0 10px 28px rgba(15,23,42,.18);
}
.pp-chase-hero-rank {
  min-width: 72px; text-align: center; padding: 10px; border-radius: 14px;
  background: rgba(255,255,255,.08); border: 1px solid var(--team-border);
}
.pp-chase-hero-rank .num { font-size: 2rem; font-weight: 950; line-height: 1; color: var(--team-accent,#38bdf8); }
.pp-chase-hero-rank .lbl { font-size: 9px; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; color: #94a3b8; margin-top: 4px; }
.pp-chase-hero h3 { margin: 0 0 6px; font-size: 1.05rem; font-weight: 900; }
.pp-chase-hero p { margin: 0; font-size: 13px; color: #cbd5e1; line-height: 1.45; }
.pp-chase-card {
  border-radius: 16px; padding: 14px; background: #fff;
  border: 1px solid var(--team-border); border-left: 5px solid var(--team-primary);
  box-shadow: 0 6px 18px rgba(15,23,42,.07);
}
.pp-chase-card--hero-stat { border-left-width: 6px; background: linear-gradient(180deg, #fff, var(--team-card-tint, #f8fafc)); }
.pp-chase-k { font-size: 10px; font-weight: 950; letter-spacing: .1em; text-transform: uppercase; color: var(--team-primary); }
.pp-chase-gap { font-size: 1.5rem; font-weight: 950; color: #0f172a; margin: 4px 0 2px; line-height: 1.1; }
.pp-chase-target { font-size: 12px; font-weight: 800; color: #64748b; margin-bottom: 6px; }
.pp-chase-rank { font-size: 1.75rem; font-weight: 950; color: #0f172a; margin: 4px 0; }
.pp-chase-b { font-size: 13px; color: #475569; line-height: 1.42; }
.pp-progress { height: 10px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin-top: 8px; position: relative; }
.pp-progress > span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--team-primary), var(--team-accent)); }
.pp-progress-label { display: flex; justify-content: space-between; font-size: 10px; font-weight: 800; color: #64748b; margin-top: 5px; }
.pp-game-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 8px 0 12px; }
.pp-game-card {
  border-radius: 14px; padding: 12px 12px 10px; background: #fff;
  border: 1px solid rgba(148,163,184,.25); box-shadow: 0 2px 8px rgba(15,23,42,.05);
}
.pp-game-card.win { border-left: 4px solid #16a34a; background: linear-gradient(180deg, #fff, #f0fdf4); }
.pp-game-card.loss { border-left: 4px solid #dc2626; background: linear-gradient(180deg, #fff, #fef2f2); }
.pp-game-top { display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: 900; letter-spacing: .06em; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }
.pp-game-wl { padding: 2px 8px; border-radius: 999px; font-size: 9px; }
.pp-game-wl.win { background: #dcfce7; color: #166534; }
.pp-game-wl.loss { background: #fee2e2; color: #991b1b; }
.pp-game-pts { font-size: 1.65rem; font-weight: 950; color: #0f172a; line-height: 1; }
.pp-game-opp { font-size: 12px; font-weight: 800; color: #334155; margin: 4px 0 8px; }
.pp-game-chips { display: flex; flex-wrap: wrap; gap: 5px; }
.pp-game-chip { font-size: 10px; font-weight: 800; padding: 3px 7px; border-radius: 8px; background: #f1f5f9; color: #475569; }
.pp-game-chip.pm-pos { background: #dcfce7; color: #166534; }
.pp-game-chip.pm-neg { background: #fee2e2; color: #991b1b; }
.pp-journey { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 14px; align-items: center; }
.pp-journey-step {
  padding: 9px 14px; border-radius: 999px; font-size: 11px; font-weight: 800;
  background: var(--team-accent-soft); border: 1px solid var(--team-border); color: #334155;
}
.pp-journey-step.active {
  background: linear-gradient(135deg, var(--team-primary), var(--team-accent));
  color: #fff; border-color: transparent; box-shadow: 0 4px 14px rgba(15,23,42,.15);
}
.pp-series-tab-banner {
  padding: 10px 14px; border-radius: 12px; margin-bottom: 10px;
  background: var(--team-accent-soft); border: 1px solid var(--team-border);
  font-size: 12px; font-weight: 800; color: #334155;
}
.fan-player-card img.hs { width: 112px; height: 112px; border-radius: 16px; object-fit: cover;
  border: 3px solid var(--team-primary,#38bdf8); background: #0b1224; box-shadow: 0 8px 24px rgba(0,0,0,.35); }
.pp-journey-arrow { color: #94a3b8; font-weight: 900; font-size: 14px; }
.pp-race-shell {
  grid-column: 1 / -1; border-radius: 18px; padding: 16px 18px; margin-bottom: 4px;
  background: linear-gradient(135deg, #fff 0%, var(--team-card-tint, #f8fafc) 100%);
  border: 1px solid var(--team-border); box-shadow: 0 8px 24px rgba(15,23,42,.08);
}
.pp-race-k { font-size: 10px; font-weight: 950; letter-spacing: .12em; text-transform: uppercase; color: var(--team-primary); margin-bottom: 10px; }
.pp-race-track {
  position: relative; height: 56px; border-radius: 999px; margin: 8px 0 12px;
  background: linear-gradient(90deg, #e2e8f0 0%, #f1f5f9 45%, rgba(234,179,8,.25) 100%);
  border: 1px solid rgba(148,163,184,.35); overflow: visible;
}
.pp-race-fill {
  position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px 0 0 999px;
  background: linear-gradient(90deg, var(--team-primary), var(--team-accent)); opacity: .35;
}
.pp-race-marker {
  position: absolute; top: 50%; transform: translate(-50%, -50%); text-align: center; min-width: 72px; z-index: 2;
}
.pp-race-marker--current { z-index: 3; }
.pp-race-marker-dot {
  width: 14px; height: 14px; border-radius: 50%; margin: 0 auto 4px;
  border: 3px solid #fff; box-shadow: 0 2px 8px rgba(15,23,42,.25);
}
.pp-race-marker--current .pp-race-marker-dot { background: var(--team-primary); width: 18px; height: 18px; }
.pp-race-marker--target .pp-race-marker-dot { background: #ca8a04; }
.pp-race-marker-lbl { font-size: 9px; font-weight: 900; color: #334155; line-height: 1.2; max-width: 88px; }
.pp-race-marker-val { font-size: 11px; font-weight: 950; color: #0f172a; }
.pp-race-meta { display: flex; flex-wrap: wrap; gap: 10px 16px; font-size: 12px; font-weight: 800; color: #475569; }
.pp-race-meta b { color: #0f172a; }
.pp-race-ladder { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 4px; }
.pp-race-ladder-card {
  border-radius: 14px; padding: 12px 14px; background: #fff; border: 1px solid var(--team-border);
  border-top: 3px solid var(--team-accent);
}
.pp-race-ladder-card--next { border-top-color: var(--team-primary); background: linear-gradient(180deg, var(--team-accent-soft), #fff); }
.pp-race-ladder-card--easy { border-top-color: #16a34a; }
.pp-race-ladder-card--hard { border-top-color: #dc2626; }
.pp-race-ladder-card--series { border-top-color: #ca8a04; }
.pp-race-ladder-k { font-size: 9px; font-weight: 950; letter-spacing: .1em; text-transform: uppercase; color: #64748b; }
.pp-race-ladder-v { font-size: 13px; font-weight: 900; color: #0f172a; margin-top: 4px; line-height: 1.35; }
.pp-race-ladder-sub { font-size: 11px; font-weight: 700; color: #64748b; margin-top: 4px; }
.pp-journey-panel { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin: 4px 0 8px; }
.pp-journey-stat {
  border-radius: 14px; padding: 12px 14px; background: #fff; border: 1px solid var(--team-border);
  border-top: 3px solid var(--team-primary);
}
.pp-journey-stat--hot { border-top-color: #dc2626; background: linear-gradient(180deg, #fef2f2, #fff); }
.pp-journey-stat--up { border-top-color: #16a34a; }
.pp-journey-stat--down { border-top-color: #64748b; }
.pp-journey-stat-k { font-size: 9px; font-weight: 950; letter-spacing: .1em; text-transform: uppercase; color: #64748b; }
.pp-journey-stat-v { font-size: 1.15rem; font-weight: 950; color: #0f172a; margin-top: 4px; line-height: 1.2; }
.pp-journey-stat-s { font-size: 11px; font-weight: 800; color: #475569; margin-top: 4px; line-height: 1.35; }
.pp-pulse-strip { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 0 0 8px; }
.pp-pulse-card { border-radius: 14px; padding: 12px; background: linear-gradient(135deg, var(--team-bg1, #1e293b), var(--team-bg0, #0f172a)); color: #f8fafc; border: 1px solid var(--team-border); }
.pp-pulse-k { font-size: 9px; font-weight: 950; letter-spacing: .12em; text-transform: uppercase; color: #94a3b8; }
.pp-pulse-v { font-size: 14px; font-weight: 900; margin-top: 4px; line-height: 1.35; }
.pp-pulse-s { font-size: 11px; font-weight: 700; color: #cbd5e1; margin-top: 4px; }
.pp-stock-up { color: #4ade80; }
.pp-stock-down { color: #f87171; }
.lt-achieve-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 10px 0 14px; }
.lt-achieve {
  border-radius: 14px; padding: 12px; border: 1px solid var(--team-border); background: #fff;
  opacity: .55; filter: grayscale(.35);
}
.lt-achieve--unlocked { opacity: 1; filter: none; border-left: 4px solid #16a34a; background: linear-gradient(145deg, #f0fdf4, #fff); }
.lt-achieve--locked { border-left: 4px solid #94a3b8; }
.lt-achieve-k { font-size: 9px; font-weight: 950; letter-spacing: .08em; text-transform: uppercase; color: #64748b; }
.lt-achieve-v { font-size: 13px; font-weight: 900; color: #0f172a; margin-top: 4px; }
.lt-achieve-s { font-size: 11px; font-weight: 700; color: #64748b; margin-top: 4px; }
.lt-rank-move {
  border-radius: 16px; padding: 14px; margin: 10px 0 14px; background: #fff;
  border: 1px solid var(--team-border); overflow: hidden;
}
.lt-rank-track { display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; align-items: center; margin-top: 10px; }
.lt-rank-node { text-align: center; padding: 10px; border-radius: 12px; background: var(--team-card-tint); border: 1px solid var(--team-border); }
.lt-rank-node--win { background: linear-gradient(145deg, #fef3c7, #fff); border-color: #fbbf24; animation: lt-rank-glow 1.4s ease-in-out infinite alternate; }
.lt-rank-arrow { font-size: 1.4rem; font-weight: 950; color: var(--team-primary); animation: lt-rank-slide 1.1s ease-in-out infinite alternate; }
@keyframes lt-rank-slide { from { transform: translateX(-3px); } to { transform: translateX(6px); } }
@keyframes lt-rank-glow { from { box-shadow: 0 0 0 rgba(251,191,36,0); } to { box-shadow: 0 0 16px rgba(251,191,36,.35); } }
.lt-swing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 10px 0 14px; }
.lt-swing { border-radius: 14px; padding: 12px 14px; border: 1px solid var(--team-border); background: #fff; }
.lt-swing--gain { border-left: 5px solid #16a34a; }
.lt-swing--flat { border-left: 5px solid #64748b; }
.lt-swing--loss { border-left: 5px solid #dc2626; }
.lt-swing-v { font-size: 1.45rem; font-weight: 950; color: #0f172a; margin: 4px 0; }
.lt-swing-s { font-size: 11px; font-weight: 800; color: #64748b; line-height: 1.35; }
.lt-defining {
  border-radius: 14px; padding: 12px 14px; margin: 8px 0 12px;
  background: linear-gradient(90deg, rgba(127,29,29,.08), transparent);
  border: 1px solid rgba(248,113,113,.35); font-size: 13px; font-weight: 800; color: #334155; line-height: 1.45;
}
.hist-week-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; margin: 10px 0 14px; }
.hist-week-card {
  border-radius: 14px; padding: 12px 14px; background: #fff;
  border: 2px dashed var(--team-accent); box-shadow: 0 4px 14px rgba(15,23,42,.06);
}
.hist-week-name { font-size: 13px; font-weight: 950; color: var(--team-primary); margin-bottom: 6px; }
.hist-week-line { font-size: 12px; font-weight: 800; color: #334155; line-height: 1.4; margin-bottom: 4px; }
.pp-chase-pill-hero {
  display: inline-block; margin-top: 8px; padding: 5px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 800; background: rgba(234,179,8,.2); border: 1px solid rgba(253,224,71,.45); color: #fef9c3;
}
.pp-award-strip { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 14px; }
.pp-award {
  flex: 1 1 200px; padding: 10px 12px; border-radius: 14px;
  background: linear-gradient(135deg, var(--team-accent-soft), #fff 60%);
  border: 1px solid var(--team-border); font-size: 12px; line-height: 1.4; color: #334155;
}
.pp-award b { display: block; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--team-primary); margin-bottom: 4px; }
.pp-game-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 8px 0 12px; }
.pp-game-meta { font-size: 12px; color: #475569; margin-top: 4px; }
.pp-compare-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin: 8px 0 12px; }
.pp-compare-card {
  border-radius: 14px; padding: 14px; background: linear-gradient(180deg, #fff, var(--team-card-tint, #f8fafc));
  border: 1px solid var(--team-border); font-size: 13px; line-height: 1.45; color: #334155;
}
.pp-compare-card .icon { font-size: 1.2rem; margin-bottom: 6px; }
/* Legacy Tracker premium */
.lt-meter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 12px 0 16px; }
.lt-meter {
  border-radius: 16px; padding: 14px; background: #fff;
  border: 1px solid var(--team-border); box-shadow: 0 4px 14px rgba(15,23,42,.06);
  position: relative; overflow: hidden;
}
.lt-meter--hof { border-top: 4px solid var(--team-accent); }
.lt-meter-k { font-size: 10px; font-weight: 950; letter-spacing: .1em; text-transform: uppercase; color: var(--team-primary); }
.lt-meter-v { font-size: 1.85rem; font-weight: 950; color: #0f172a; margin: 4px 0; }
.lt-meter-sub { font-size: 11px; font-weight: 800; color: #64748b; margin-bottom: 6px; }
.lt-meter-bar { height: 12px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin-top: 8px; }
.lt-meter-bar > span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--team-primary), var(--team-accent)); }
.lt-tier-badge {
  display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 10px; font-weight: 900;
  letter-spacing: .08em; text-transform: uppercase; margin-top: 6px;
  background: var(--team-accent-soft); border: 1px solid var(--team-border); color: var(--team-primary);
}
.lt-badge-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 14px; }
.lt-badge {
  padding: 10px 14px; border-radius: 12px; font-size: 12px; font-weight: 700; line-height: 1.4;
  background: linear-gradient(135deg, var(--team-accent-soft), #fff 70%);
  border: 1px solid var(--team-border); color: #334155; flex: 1 1 280px;
}
.lt-badge b { color: #0f172a; }
.lt-scenario-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 12px 0; }
.lt-scenario {
  border-radius: 16px; padding: 14px; background: linear-gradient(145deg, var(--team-accent-soft), #fff 55%);
  border: 1px solid var(--team-border); min-height: 140px;
}
.lt-scenario--title { border-left: 5px solid #ca8a04; background: linear-gradient(145deg, rgba(254,243,199,.5), #fff 60%); }
.lt-scenario--finals { border-left: 5px solid var(--team-primary); }
.lt-scenario-k { font-size: 10px; font-weight: 950; letter-spacing: .1em; text-transform: uppercase; color: var(--team-primary); }
.lt-scenario-score { font-size: 1.85rem; font-weight: 950; color: #0f172a; margin: 6px 0; }
.lt-scenario-delta { font-size: 11px; font-weight: 800; color: #16a34a; margin-bottom: 4px; }
.lt-scenario-b { font-size: 12px; color: #475569; line-height: 1.4; }
.lt-compare-face { display: grid; grid-template-columns: 56px 1fr; gap: 10px; align-items: center; margin-bottom: 8px; }
.lt-compare-face img { width: 52px; height: 52px; border-radius: 12px; object-fit: cover; border: 2px solid var(--team-primary); background: #0b1224; }
.lt-touchstone-rank { font-size: 10px; font-weight: 900; color: var(--team-primary); letter-spacing: .08em; text-transform: uppercase; }
.lt-impact-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 10px 0 14px; }
.lt-impact-card {
  border-radius: 14px; padding: 12px 14px; background: #fff; border: 1px solid var(--team-border);
  border-left: 4px solid var(--team-primary);
}
.lt-impact-card--title { border-left-color: #ca8a04; background: linear-gradient(145deg, rgba(254,243,199,.35), #fff); }
.lt-impact-v { font-size: 1.5rem; font-weight: 950; color: #0f172a; margin: 4px 0; }
.lt-impact-sub { font-size: 11px; font-weight: 800; color: #64748b; line-height: 1.35; }
.lt-goat-ladder { display: grid; gap: 8px; margin: 10px 0 14px; }
.lt-goat-row {
  display: grid; grid-template-columns: 36px 1fr auto; gap: 10px; align-items: center;
  padding: 10px 12px; border-radius: 12px; background: #fff; border: 1px solid var(--team-border);
}
.lt-goat-row--you { border: 2px solid var(--team-primary); background: linear-gradient(90deg, var(--team-accent-soft), #fff); }
.lt-goat-rank { font-size: 1.1rem; font-weight: 950; color: var(--team-primary); text-align: center; }
.lt-goat-name { font-size: 13px; font-weight: 900; color: #0f172a; }
.lt-goat-tier { font-size: 10px; font-weight: 800; color: #64748b; }
.lt-goat-score { font-size: 12px; font-weight: 950; color: #0f172a; }
.lt-badge-chip {
  display: inline-flex; align-items: center; gap: 4px; padding: 6px 11px; border-radius: 999px;
  font-size: 10px; font-weight: 950; letter-spacing: .04em; text-transform: uppercase;
  border: 1px solid var(--team-border); background: var(--team-accent-soft); color: var(--team-primary);
}
.lt-badge-chip--gold { background: linear-gradient(135deg, #fef3c7, #fde68a); color: #92400e; border-color: #fcd34d; }
.lt-badge-chip--title { background: linear-gradient(135deg, #fef3c7, #fbbf24); color: #78350f; border-color: #f59e0b; }
.lt-badge-chip--hof { background: linear-gradient(135deg, #e0e7ff, #c7d2fe); color: #3730a3; border-color: #818cf8; }
.lt-run-rank { border-radius: 14px; padding: 12px 14px; margin: 8px 0 12px; background: var(--team-accent-soft); border: 1px solid var(--team-border); font-size: 13px; font-weight: 800; color: #334155; line-height: 1.45; }
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
.fan-player-card img.hs { width: 112px; height: 112px; border-radius: 16px; object-fit: cover;
  border: 3px solid var(--team-primary,#38bdf8); background: #0b1224; box-shadow: 0 8px 24px rgba(0,0,0,.35); }
.fan-player-card img.logo { width: 52px; opacity: .95; }
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
.broadcast-shell {
  border-radius: 22px; padding: 18px; margin: 12px 0 14px; color: #f8fafc;
  background: radial-gradient(circle at 20% 0%, var(--team-accent-soft), transparent 34%),
    linear-gradient(135deg, var(--team-bg0), var(--team-bg1) 56%, #020617);
  border: 1px solid var(--team-border); box-shadow: 0 18px 50px rgba(2,6,23,.38);
}
.broadcast-score-row { display:grid; grid-template-columns: minmax(120px,1fr) minmax(230px,1.2fr) minmax(120px,1fr); gap:14px; align-items:center; }
.broadcast-team { text-align:center; }
.broadcast-team img { width: clamp(68px, 11vw, 104px); height: clamp(68px, 11vw, 104px); object-fit:contain; filter: drop-shadow(0 8px 20px rgba(0,0,0,.45)); }
.broadcast-team-name { font-size: 13px; font-weight: 950; margin-top: 5px; }
.broadcast-status { display:inline-block; font-size: 11px; font-weight: 950; letter-spacing:.12em; text-transform:uppercase; padding:5px 11px; border-radius:999px; border:1px solid rgba(255,255,255,.18); background:rgba(15,23,42,.58); color:#e2e8f0; }
.broadcast-status.live { background:rgba(220,38,38,.24); color:#fecaca; border-color:rgba(248,113,113,.5); animation: homeLivePulse 2.4s ease-in-out infinite; }
.broadcast-status.soon { background:rgba(251,191,36,.22); color:#fde68a; border-color:rgba(251,191,36,.55); }
.broadcast-status.final { background:rgba(56,189,248,.18); color:#bae6fd; border-color:rgba(56,189,248,.45); }
.broadcast-status.pregame { background:rgba(148,163,184,.16); color:#e2e8f0; }
.broadcast-main-score { font-size: clamp(2.4rem, 7vw, 4.3rem); font-weight: 1000; letter-spacing:.04em; line-height:1; margin:8px 0; }
.broadcast-clock { font-size: 14px; color:#cbd5e1; font-weight:800; }
.broadcast-sub { font-size:12px; color:#94a3b8; margin-top:6px; }
.broadcast-metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-top:14px; }
.broadcast-metric { border:1px solid rgba(148,163,184,.28); border-radius:14px; padding:10px 12px; background:rgba(15,23,42,.48); text-align:center; }
.broadcast-metric .k { font-size:10px; font-weight:900; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; }
.broadcast-metric .v { font-size:1.35rem; font-weight:950; color:#fff; margin-top:2px; }
.broadcast-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(245px,1fr)); gap:12px; margin:12px 0; }
.broadcast-card { border:1px solid var(--team-border); border-radius:18px; background:linear-gradient(180deg,#fff,var(--team-card-tint)); padding:12px; box-shadow:0 10px 26px rgba(15,23,42,.10); }
.broadcast-card.dark { background:linear-gradient(135deg,rgba(15,23,42,.92),rgba(30,41,59,.88)); color:#f8fafc; }
.broadcast-card-title { font-size:12px; font-weight:950; color:var(--team-primary); text-transform:uppercase; letter-spacing:.08em; margin-bottom:7px; }
.player-tile { display:flex; gap:10px; align-items:center; border:1px solid rgba(100,116,139,.18); border-radius:14px; padding:9px; background:rgba(255,255,255,.72); margin-bottom:8px; }
.player-tile img { width:58px; height:46px; object-fit:cover; object-position:top center; border-radius:10px; background:#e2e8f0; }
.player-tile .name { font-weight:950; color:#0f172a; line-height:1.15; }
.player-tile .line { font-size:12px; color:#475569; margin-top:2px; }
.player-stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:5px; margin-top:6px; }
.player-stat-grid span { display:block; border-radius:8px; background:var(--team-card-tint); color:#0f172a; text-align:center; padding:4px 3px; font-size:11px; font-weight:800; }
.prob-bar { height:12px; border-radius:999px; background:#e2e8f0; overflow:hidden; margin:8px 0 5px; }
.prob-bar span { display:block; height:100%; background:linear-gradient(90deg,var(--team-primary),var(--team-accent)); border-radius:999px; }
@media (max-width: 720px) { .broadcast-score-row { grid-template-columns:1fr; } }
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
/* Product shell + trust badges (consistency pass) */
.fan-product-shell, .pp-wrap, .cmd-shell, .ml-shell { max-width: 1280px; margin: 0 auto; padding: 0 2px; }
.fan-trust-strip {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  margin: 0 0 14px; padding: 10px 14px; border-radius: 14px;
  background: linear-gradient(180deg, #fff, #f8fafc);
  border: 1px solid rgba(148,163,184,.28);
  box-shadow: 0 2px 8px rgba(15,23,42,.04);
}
.fan-data-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 10px; font-weight: 900; letter-spacing: .06em; text-transform: uppercase;
  padding: 5px 11px; border-radius: 999px; border: 1px solid transparent; white-space: nowrap;
}
.fan-data-badge--official { background: #ecfdf5; color: #047857; border-color: #6ee7b7; }
.fan-data-badge--curated { background: #eff6ff; color: #1d4ed8; border-color: #93c5fd; }
.fan-data-badge--fan_model { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
.fan-data-badge--projected { background: #f5f3ff; color: #6d28d9; border-color: #c4b5fd; }
.fan-data-badge--estimate { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
.fan-trust-note { font-size: 11px; font-weight: 700; color: #64748b; line-height: 1.35; flex: 1 1 180px; }
.fan-card-unified {
  border-radius: 16px; padding: 14px 16px; background: #fff;
  border: 1px solid var(--team-border, rgba(148,163,184,.28));
  box-shadow: 0 4px 14px rgba(15,23,42,.06);
}
@media (max-width: 768px) {
  .fan-energy-grid { grid-template-columns: 1fr; gap: 10px; }
  .fan-energy-card { min-height: auto; }
  .pp-chase-grid, .pp-race-ladder, .pp-pulse-strip { grid-template-columns: 1fr; }
  .pp-journey-panel { grid-template-columns: 1fr 1fr; }
  .pp-chase-hero { grid-template-columns: 1fr; text-align: center; }
  .pp-chase-hero-rank { margin: 0 auto; }
  .pp-stat-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .pp-game-grid { grid-template-columns: 1fr; }
  .pp-race-meta { flex-direction: column; gap: 6px; }
  .pp-race-track { height: 68px; margin-bottom: 16px; }
  .pp-race-marker { min-width: 58px; }
  .pp-race-marker-lbl { font-size: 8px; max-width: 62px; }
  .lt-meter-grid, .lt-impact-grid, .lt-swing-grid, .lt-achieve-grid, .lt-scenario-grid { grid-template-columns: 1fr; }
  .hist-rushmore { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hist-grid, .hist-compare-grid, .hist-milestone-grid { grid-template-columns: 1fr !important; }
  .hist-countdown-grid, .hist-week-grid, .hist-move-grid { grid-template-columns: 1fr; }
  .ml-grid { grid-template-columns: 1fr !important; }
  .ml-bench-grid { grid-template-columns: 1fr !important; }
  .ml-tile-grid { grid-template-columns: 1fr !important; }
  .fan-matchup-ribbon { flex-direction: column; align-items: flex-start; gap: 8px; }
  .live-fan-hero { flex-direction: column !important; text-align: center; align-items: center !important; }
  .fan-trust-strip { flex-direction: column; align-items: flex-start; }
  .fan-trust-note { margin-left: 0; width: 100%; }
  .fan-player-card { flex-direction: column; text-align: center; }
  .fan-player-card img.hs { margin: 0 auto; }
  .cmd-emph-grid { grid-template-columns: 1fr; }
  .os-card-grid { grid-template-columns: 1fr; }
}
</style>
"""

# Sidebar / debug defaults — overwritten in main() when the Streamlit UI runs.
USE_DEMO_BACKUP = True
ENABLE_BRACKET_API_REFRESH = True
SHOW_PERF_DEBUG = False


def _inject_global_app_css():
    st.markdown(GLOBAL_APP_CSS, unsafe_allow_html=True)


def _configure_app_shell():
    """One-time Streamlit page shell (title, global CSS). Called from main() only."""
    import portfolio_polish as pp

    st.set_page_config(page_title="Daniel Cohen — NBA Playoff Companion AI", page_icon="🏀", layout="wide")
    pp.inject_polish_css(st, app_slug="nba")
    _inject_global_app_css()

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

# Curated player IDs for roster lookup (works offline / when stats API has no 2025-26 logs).
PLAYOFF_PLAYER_ID_MAP = {
    "Jalen Brunson": 1628973,
    "Mikal Bridges": 1628969,
    "OG Anunoby": 1628384,
    "O.G. Anunoby": 1628384,
    "Josh Hart": 1628404,
    "Karl-Anthony Towns": 1626157,
    "Miles McBride": 1630540,
    "Mitchell Robinson": 1629011,
    "Jordan Clarkson": 203903,
    "Landry Shamet": 1629013,
    "Jose Alvarado": 1630631,
    "Stephon Castle": 1642264,
    "Devin Vassell": 1630170,
    "Keldon Johnson": 1629640,
    "Harrison Barnes": 203084,
    "Victor Wembanyama": 1641705,
    "Tre Jones": 1630200,
    "Julian Champagnie": 1630577,
    "Zach Collins": 1628380,
    "Malaki Branham": 1631103,
    "Blake Wesley": 1631104,
}

TEAM_PROFILES = {
    "New York Knicks": {"seed":3,"conference":"Eastern Conference","status":"Active","round":"NBA Finals","current_opponent":"San Antonio Spurs","first_round_opponent":"Atlanta Hawks","first_round_result":"Defeated Atlanta Hawks, 4-2","starters":["Jalen Brunson","Mikal Bridges","OG Anunoby","Josh Hart","Karl-Anthony Towns"],"subs":["Miles McBride","Mitchell Robinson","Jordan Clarkson","Landry Shamet","Jose Alvarado"],"strengths":["Brunson shot creation","Towns spacing","OG/Bridges wing defense","Hart rebounding"],"concerns":["Towns foul trouble","bench scoring consistency","overreliance on Brunson late"]},
    "San Antonio Spurs": {"seed":2,"conference":"Western Conference","status":"Active","round":"NBA Finals","current_opponent":"New York Knicks","first_round_opponent":"Portland Trail Blazers","first_round_result":"Defeated Portland Trail Blazers, 4-1","starters":["Stephon Castle","Devin Vassell","Keldon Johnson","Harrison Barnes","Victor Wembanyama"],"subs":["Tre Jones","Julian Champagnie","Zach Collins","Malaki Branham","Blake Wesley"],"strengths":["Wembanyama two-way impact","length","rim protection","young talent"],"concerns":["turnovers","playoff inexperience","foul trouble"]},
}
# Eliminated teams
ELIMINATED_INFO = [
    ("Atlanta Hawks",6,"Eastern Conference","New York Knicks","Lost to New York Knicks, 4-2",["Jalen Johnson","Dyson Daniels","Zaccharie Risacher","Onyeka Okongwu","De'Andre Hunter"],["Bogdan Bogdanovic","Clint Capela","Vit Krejci","Kobe Bufkin","Larry Nance Jr."]),
    ("Boston Celtics",2,"Eastern Conference","Philadelphia 76ers","Lost to Philadelphia 76ers, 4-3",["Jrue Holiday","Derrick White","Jaylen Brown","Jayson Tatum","Kristaps Porzingis"],["Payton Pritchard","Sam Hauser","Al Horford","Luke Kornet","Neemias Queta"]),
    ("Orlando Magic",8,"Eastern Conference","Detroit Pistons","Lost to Detroit Pistons, 4-3",["Jalen Suggs","Kentavious Caldwell-Pope","Franz Wagner","Paolo Banchero","Wendell Carter Jr."],["Cole Anthony","Jonathan Isaac","Anthony Black","Moritz Wagner","Gary Harris"]),
    ("Toronto Raptors",5,"Eastern Conference","Cleveland Cavaliers","Lost to Cleveland Cavaliers, 4-3",["Immanuel Quickley","RJ Barrett","Gradey Dick","Scottie Barnes","Jakob Poeltl"],["Bruce Brown","Kelly Olynyk","Ochai Agbaji","Chris Boucher","Davion Mitchell"]),
    ("Philadelphia 76ers",7,"Eastern Conference","New York Knicks","Lost to New York Knicks, 4-0",["Tyrese Maxey","VJ Edgecombe","Kelly Oubre Jr.","Paul George","Joel Embiid"],["Quentin Grimes","Andre Drummond","Kyle Lowry","Eric Gordon","Caleb Martin"]),
    ("Detroit Pistons",1,"Eastern Conference","Cleveland Cavaliers","Lost to Cleveland Cavaliers, 4-3",["Cade Cunningham","Jaden Ivey","Ausar Thompson","Tobias Harris","Jalen Duren"],["Marcus Sasser","Isaiah Stewart","Simone Fontecchio","Malik Beasley","Ron Holland"]),
    ("Phoenix Suns",8,"Western Conference","Oklahoma City Thunder","Lost to Oklahoma City Thunder, 4-0",["Devin Booker","Bradley Beal","Grayson Allen","Kevin Durant","Jusuf Nurkic"],["Royce O'Neale","Eric Gordon","Bol Bol","Drew Eubanks","Josh Okogie"]),
    ("Portland Trail Blazers",7,"Western Conference","San Antonio Spurs","Lost to San Antonio Spurs, 4-1",["Scoot Henderson","Anfernee Simons","Shaedon Sharpe","Jerami Grant","Deandre Ayton"],["Toumani Camara","Matisse Thybulle","Robert Williams III","Dalano Banton","Kris Murray"]),
    ("Denver Nuggets",3,"Western Conference","Minnesota Timberwolves","Lost to Minnesota Timberwolves, 4-2",["Jamal Murray","Christian Braun","Michael Porter Jr.","Aaron Gordon","Nikola Jokic"],["Reggie Jackson","Peyton Watson","Zeke Nnaji","Julian Strawther","DeAndre Jordan"]),
    ("Houston Rockets",5,"Western Conference","Los Angeles Lakers","Lost to Los Angeles Lakers, 4-2",["Fred VanVleet","Jalen Green","Amen Thompson","Jabari Smith Jr.","Alperen Sengun"],["Dillon Brooks","Tari Eason","Cam Whitmore","Steven Adams","Reed Sheppard"]),
    ("Los Angeles Lakers",4,"Western Conference","Oklahoma City Thunder","Lost to Oklahoma City Thunder, 4-1",["D'Angelo Russell","Austin Reaves","LeBron James","Rui Hachimura","Anthony Davis"],["Gabe Vincent","Jarred Vanderbilt","Max Christie","Christian Wood","Jaxson Hayes"]),
    ("Minnesota Timberwolves",6,"Western Conference","San Antonio Spurs","Lost to San Antonio Spurs, 4-2",["Mike Conley","Anthony Edwards","Jaden McDaniels","Naz Reid","Rudy Gobert"],["Nickeil Alexander-Walker","Donte DiVincenzo","Rob Dillingham","Josh Minott","Luka Garza"]),
    ("Cleveland Cavaliers",4,"Eastern Conference","New York Knicks","Lost to New York Knicks, 4-0",["James Harden","Donovan Mitchell","Max Strus","Evan Mobley","Jarrett Allen"],["Caris LeVert","Isaac Okoro","Georges Niang","Sam Merrill","Dean Wade"]),
    ("Oklahoma City Thunder",1,"Western Conference","San Antonio Spurs","Lost to San Antonio Spurs, 4-2",["Shai Gilgeous-Alexander","Lu Dort","Jalen Williams","Chet Holmgren","Isaiah Hartenstein"],["Cason Wallace","Aaron Wiggins","Isaiah Joe","Jaylin Williams","Kenrich Williams"]),
]
for name, seed, conf, opp, result, starters, subs in ELIMINATED_INFO:
    TEAM_PROFILES[name] = {"seed":seed,"conference":conf,"status":"Eliminated","round":"Lost First Round","current_opponent":None,"first_round_opponent":opp,"first_round_result":result,"starters":starters,"subs":subs,"strengths":["main star creation","transition chances","playoff experience"],"concerns":["series ended in first round","needs depth/defense improvements","late-game consistency"]}

# Standard five-man order for matchup cards and live boards.
LINEUP_SLOTS = ("PG", "SG", "SF", "PF", "C")

# Flexible labels map to slot preference (first = best fit).
FLEX_ROLE_SLOTS = {
    "PG": ("PG",),
    "SG": ("SG",),
    "SF": ("SF",),
    "PF": ("PF",),
    "C": ("C",),
    "Guard": ("PG", "SG"),
    "Wing": ("SG", "SF"),
    "Forward": ("SF", "PF"),
    "Big": ("PF", "C"),
}

# Curated overrides for playoff rotations — checked before profile index and NBA API position.
PLAYER_POSITION_OVERRIDES = {
    # New York Knicks
    "Jalen Brunson": "PG",
    "Mikal Bridges": "SF",
    "OG Anunoby": "SF",
    "Josh Hart": "PF",
    "Karl-Anthony Towns": "C",
    "Miles McBride": "SG",
    "Mitchell Robinson": "C",
    "Jordan Clarkson": "SG",
  # Cleveland Cavaliers
    "James Harden": "PG",
    "Donovan Mitchell": "SG",
    "Max Strus": "SF",
    "Evan Mobley": "PF",
    "Jarrett Allen": "C",
    "Caris LeVert": "SG",
    "Isaac Okoro": "SF",
    "Georges Niang": "PF",
    "Dean Wade": "PF",
    # Detroit Pistons
    "Cade Cunningham": "PG",
    "Jaden Ivey": "SG",
    "Ausar Thompson": "SF",
    "Tobias Harris": "PF",
    "Jalen Duren": "C",
    "Isaiah Stewart": "C",
    # Philadelphia 76ers
    "Tyrese Maxey": "PG",
    "VJ Edgecombe": "SG",
    "Kelly Oubre Jr.": "SF",
    "Paul George": "SF",
    "Joel Embiid": "C",
    "Andre Drummond": "C",
    "Quentin Grimes": "SG",
    # Oklahoma City Thunder
    "Shai Gilgeous-Alexander": "PG",
    "Lu Dort": "SG",
    "Jalen Williams": "SF",
    "Chet Holmgren": "PF",
    "Isaiah Hartenstein": "C",
    "Cason Wallace": "SG",
    "Aaron Wiggins": "SF",
    # Los Angeles Lakers
    "D'Angelo Russell": "PG",
    "Austin Reaves": "SG",
    "LeBron James": "SF",
    "Rui Hachimura": "PF",
    "Anthony Davis": "C",
    "Gabe Vincent": "PG",
    "Jarred Vanderbilt": "PF",
    # San Antonio Spurs
    "Stephon Castle": "PG",
    "Devin Vassell": "SG",
    "Keldon Johnson": "SF",
    "Harrison Barnes": "PF",
    "Victor Wembanyama": "C",
    "Tre Jones": "PG",
    "Zach Collins": "C",
    # Minnesota Timberwolves
    "Mike Conley": "PG",
    "Anthony Edwards": "SG",
    "Jaden McDaniels": "SF",
    "Naz Reid": "PF",
    "Rudy Gobert": "C",
    "Nickeil Alexander-Walker": "SG",
    "Donte DiVincenzo": "SG",
    # Eliminated / other playoff teams (still used in previews)
    "Trae Young": "PG",
    "Jalen Johnson": "PF",
    "Paolo Banchero": "PF",
    "Jayson Tatum": "SF",
    "Jaylen Brown": "SG",
    "Kristaps Porzingis": "C",
    "Jamal Murray": "PG",
    "Nikola Jokic": "C",
    "Fred VanVleet": "PG",
    "Alperen Sengun": "C",
    "Devin Booker": "SG",
    "Kevin Durant": "SF",
}

# Curated current playoff starting five + bench for this app's playoff universe.
# Takes priority over stale TEAM_PROFILES / API roster rows when building matchup boards.
CURRENT_PLAYOFF_LINEUPS = {
    "New York Knicks": {
        "PG": "Jalen Brunson", "SG": "Mikal Bridges", "SF": "OG Anunoby", "PF": "Josh Hart", "C": "Karl-Anthony Towns",
        "bench": ["Miles McBride", "Mitchell Robinson", "Jordan Clarkson", "Landry Shamet", "Jose Alvarado"],
    },
    "Cleveland Cavaliers": {
        "PG": "James Harden", "SG": "Donovan Mitchell", "SF": "Max Strus", "PF": "Evan Mobley", "C": "Jarrett Allen",
        "bench": ["Caris LeVert", "Isaac Okoro", "Georges Niang", "Sam Merrill", "Dean Wade"],
    },
    "Detroit Pistons": {
        "PG": "Cade Cunningham", "SG": "Jaden Ivey", "SF": "Ausar Thompson", "PF": "Tobias Harris", "C": "Jalen Duren",
        "bench": ["Marcus Sasser", "Isaiah Stewart", "Simone Fontecchio", "Malik Beasley"],
    },
    "Philadelphia 76ers": {
        "PG": "Tyrese Maxey", "SG": "VJ Edgecombe", "SF": "Kelly Oubre Jr.", "PF": "Paul George", "C": "Joel Embiid",
        "bench": ["Quentin Grimes", "Andre Drummond", "Kyle Lowry", "Eric Gordon"],
    },
    "Oklahoma City Thunder": {
        "PG": "Shai Gilgeous-Alexander", "SG": "Lu Dort", "SF": "Jalen Williams", "PF": "Chet Holmgren", "C": "Isaiah Hartenstein",
        "bench": ["Cason Wallace", "Aaron Wiggins", "Isaiah Joe", "Jaylin Williams"],
    },
    "Los Angeles Lakers": {
        "PG": "D'Angelo Russell", "SG": "Austin Reaves", "SF": "LeBron James", "PF": "Rui Hachimura", "C": "Anthony Davis",
        "bench": ["Gabe Vincent", "Jarred Vanderbilt", "Max Christie", "Jaxson Hayes"],
    },
    "San Antonio Spurs": {
        "PG": "Stephon Castle", "SG": "Devin Vassell", "SF": "Keldon Johnson", "PF": "Harrison Barnes", "C": "Victor Wembanyama",
        "bench": ["Tre Jones", "Julian Champagnie", "Zach Collins", "Malaki Branham", "Blake Wesley"],
    },
    "Minnesota Timberwolves": {
        "PG": "Mike Conley", "SG": "Anthony Edwards", "SF": "Jaden McDaniels", "PF": "Naz Reid", "C": "Rudy Gobert",
        "bench": ["Nickeil Alexander-Walker", "Donte DiVincenzo", "Rob Dillingham", "Josh Minott"],
    },
}

# Players removed from active playoff rotation in this app universe (still on API rosters).
OUTDATED_PLAYOFF_PLAYERS = {
    "Atlanta Hawks": ["Trae Young"],
    "Cleveland Cavaliers": ["Darius Garland"],
    "New York Knicks": ["Precious Achiuwa"],
    "Detroit Pistons": [],
    "Philadelphia 76ers": [],
    "Oklahoma City Thunder": [],
    "Los Angeles Lakers": [],
    "San Antonio Spurs": ["Jeremy Sochan"],
    "Minnesota Timberwolves": [],
}


def _player_name_key(name):
    return re.sub(r"\s+", " ", str(name or "").strip()).lower()


def _profile_slot_for_player(player_name, team_name):
    """Team-specific starter index from TEAM_PROFILES (PG=0 … C=4)."""
    starters = (TEAM_PROFILES.get(team_name) or {}).get("starters") or []
    key = _player_name_key(player_name)
    for i, p in enumerate(starters):
        if _player_name_key(p) == key and i < len(LINEUP_SLOTS):
            return LINEUP_SLOTS[i]
    return None


def _api_position_to_slots(pos_str):
    """Map NBA.com roster position text to ordered slot candidates."""
    if not pos_str or (isinstance(pos_str, float) and pd.isna(pos_str)):
        return FLEX_ROLE_SLOTS["Forward"]
    s = str(pos_str).upper().strip()
    if s in ("G", "GUARD"):
        return FLEX_ROLE_SLOTS["Guard"]
    if s in ("F", "FORWARD"):
        return FLEX_ROLE_SLOTS["Forward"]
    if s in ("C", "CENTER"):
        return FLEX_ROLE_SLOTS["C"]
    if "CENTER" in s and "FORWARD" in s:
        return ("PF", "C") if s.index("F") < s.index("C") else ("C", "PF")
    if "GUARD" in s and "FORWARD" in s:
        return ("SG", "SF") if s.index("G") < s.index("F") else ("SF", "SG")
    if "G-F" in s or "G/F" in s or (s.startswith("G") and "F" in s):
        return ("SG", "SF")
    if "F-G" in s or "F/G" in s:
        return ("SF", "SG")
    if "F-C" in s or "F/C" in s or (s.startswith("F") and "C" in s):
        return ("PF", "C")
    if "C-F" in s or "C/F" in s:
        return ("C", "PF")
    return FLEX_ROLE_SLOTS["Forward"]


@st.cache_data(ttl=86400)
def _roster_position_lookup(team_name):
    """Player name (lower) -> raw NBA.com position string."""
    roster = fetch_current_roster(team_name)
    out = {}
    if roster is None or roster.empty or "Player" not in roster.columns:
        return out
    for _, row in roster.iterrows():
        out[_player_name_key(row["Player"])] = row.get("Position", "")
    return out


def resolve_player_position_info(player_name, team_name):
    """
    Resolve a player's basketball role for lineup assignment.
    Returns dict: role_label, slot_prefs (tuple), source.
    """
    key = _player_name_key(player_name)
    if not key:
        return {"role_label": "Forward", "slot_prefs": FLEX_ROLE_SLOTS["Forward"], "source": "default"}

    override = PLAYER_POSITION_OVERRIDES.get(player_name)
    if override is None:
        for k, v in PLAYER_POSITION_OVERRIDES.items():
            if _player_name_key(k) == key:
                override = v
                break
    if override:
        slots = FLEX_ROLE_SLOTS.get(override, (override,) if override in LINEUP_SLOTS else FLEX_ROLE_SLOTS["Forward"])
        return {"role_label": override, "slot_prefs": slots, "source": "override"}

    prof_slot = _profile_slot_for_player(player_name, team_name)
    if prof_slot:
        return {"role_label": prof_slot, "slot_prefs": (prof_slot,), "source": "profile"}

    api_pos = _roster_position_lookup(team_name).get(key, "")
    if api_pos:
        slots = _api_position_to_slots(api_pos)
        label = api_pos if isinstance(api_pos, str) else "API"
        return {"role_label": label, "slot_prefs": slots, "source": "api"}

    return {"role_label": "Forward", "slot_prefs": FLEX_ROLE_SLOTS["Forward"], "source": "default"}


def _outdated_player_keys(team_name):
    keys = set()
    for name in OUTDATED_PLAYOFF_PLAYERS.get(team_name, []):
        keys.add(_player_name_key(name))
    return keys


def _is_outdated_playoff_player(name, team_name):
    return _player_name_key(name) in _outdated_player_keys(team_name)


def _rotation_player_pool(team_name, limit=14):
    """Active rotation: curated playoff board → playoff minutes → season minutes → roster API."""
    seen, pool = set(), []
    outdated = _outdated_player_keys(team_name)
    curated = CURRENT_PLAYOFF_LINEUPS.get(team_name) or {}
    for slot in LINEUP_SLOTS:
        name = curated.get(slot)
        if name and _player_name_key(name) not in outdated:
            k = _player_name_key(name)
            if k not in seen:
                pool.append(name)
                seen.add(k)
    for name in curated.get("bench") or []:
        if _player_name_key(name) in outdated:
            continue
        k = _player_name_key(name)
        if k and k not in seen:
            pool.append(name)
            seen.add(k)
    playoff_rot = fetch_playoff_rotation_by_minutes(team_name)
    if playoff_rot is not None and not playoff_rot.empty and "Player" in playoff_rot.columns:
        for name in playoff_rot["Player"].dropna().astype(str).tolist():
            k = _player_name_key(name)
            if k in outdated or k in seen:
                continue
            pool.append(name)
            seen.add(k)
            if len(pool) >= limit:
                return pool[:limit]
    rot = fetch_team_rotation_by_minutes(team_name)
    if rot is not None and not rot.empty and "Player" in rot.columns:
        for name in rot["Player"].dropna().astype(str).tolist():
            k = _player_name_key(name)
            if k in outdated or k in seen:
                continue
            pool.append(name)
            seen.add(k)
            if len(pool) >= limit:
                return pool[:limit]
    prof = TEAM_PROFILES.get(team_name) or {}
    for name in (prof.get("starters") or []) + (prof.get("subs") or []):
        k = _player_name_key(name)
        if k in outdated or k in seen:
            continue
        pool.append(name)
        seen.add(k)
    if len(pool) < 5:
        roster = fetch_current_roster(team_name)
        if roster is not None and not roster.empty and "Player" in roster.columns:
            for name in roster["Player"].dropna().astype(str).tolist():
                k = _player_name_key(name)
                if k in outdated or k in seen:
                    continue
                pool.append(name)
                seen.add(k)
    return pool[:limit] if limit else pool


def _minutes_rank(team_name):
    ranks = {}
    rot = fetch_playoff_rotation_by_minutes(team_name)
    if rot is None or rot.empty:
        rot = fetch_team_rotation_by_minutes(team_name)
    if rot is not None and not rot.empty and "Player" in rot.columns:
        for i, name in enumerate(rot["Player"].dropna().astype(str).tolist()):
            ranks[_player_name_key(name)] = i
    return ranks


def get_lineup_resolution_info(team_name):
    """Metadata for UI: how the current playoff lineup was resolved."""
    curated = CURRENT_PLAYOFF_LINEUPS.get(team_name)
    playoff_rot = fetch_playoff_rotation_by_minutes(team_name)
    has_playoff = playoff_rot is not None and not playoff_rot.empty
    if curated and all(curated.get(s) for s in LINEUP_SLOTS):
        src = "curated playoff override"
    elif has_playoff:
        src = "recent playoff box scores / playoff minutes"
    elif fetch_team_rotation_by_minutes(team_name) is not None and not fetch_team_rotation_by_minutes(team_name).empty:
        src = "current roster API (season minutes)"
    else:
        src = "TEAM_PROFILES fallback"
    rejected = list(OUTDATED_PLAYOFF_PLAYERS.get(team_name) or [])
    active = _rotation_player_pool(team_name, limit=14)
    return {
        "source": src,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M ET"),
        "rejected": rejected,
        "active_rotation": active,
        "resolved_lineup": build_position_lineup(team_name),
    }


def build_position_lineup(team_name, candidate_names=None):
    """
    Build a five-man lineup ordered PG → C using position logic (not minutes order).
    candidate_names: optional restrict pool (e.g. live box score top five).
    """
    curated = CURRENT_PLAYOFF_LINEUPS.get(team_name) or {}
    if not candidate_names and all(curated.get(s) for s in LINEUP_SLOTS):
        lineup = [curated[s] for s in LINEUP_SLOTS]
        if not any(_is_outdated_playoff_player(p, team_name) for p in lineup):
            return lineup

    pool = list(candidate_names) if candidate_names else _rotation_player_pool(team_name)
    if not pool:
        fb = [curated.get(s) or "TBD" for s in LINEUP_SLOTS]
        if any(x != "TBD" for x in fb):
            return fb
        return list((TEAM_PROFILES.get(team_name) or {}).get("starters") or [])[:5] + ["TBD"] * max(
            0, 5 - len((TEAM_PROFILES.get(team_name) or {}).get("starters") or [])
        )

    profile_starters = []
    for s in LINEUP_SLOTS:
        if curated.get(s) and not _is_outdated_playoff_player(curated[s], team_name):
            profile_starters.append(curated[s])
    if len(profile_starters) < 5:
        for p in (TEAM_PROFILES.get(team_name) or {}).get("starters") or []:
            if p not in profile_starters and not _is_outdated_playoff_player(p, team_name):
                profile_starters.append(p)
    ranks = _minutes_rank(team_name)
    slots = {s: None for s in LINEUP_SLOTS}
    assigned = set()
    assignment_meta = {}

    # Phase 1: place profile starters on resolved position slots (not blind list index).
    pool_keys = {_player_name_key(x) for x in pool}
    for p in profile_starters:
        pk = _player_name_key(p)
        if pk not in pool_keys or pk in assigned:
            continue
        info = resolve_player_position_info(p, team_name)
        placed = False
        for slot in info["slot_prefs"]:
            if slots[slot] is None:
                slots[slot] = p
                assigned.add(pk)
                assignment_meta[slot] = {"player": p, "source": info["source"]}
                placed = True
                break
        if not placed:
            for slot in LINEUP_SLOTS:
                if slots[slot] is None:
                    slots[slot] = p
                    assigned.add(pk)
                    assignment_meta[slot] = {"player": p, "source": "profile_fallback"}
                    break

    # Phase 2: fill remaining slots by best position fit + minutes.
    for slot in LINEUP_SLOTS:
        if slots[slot]:
            continue
        best_name, best_score = None, -1.0
        for p in pool:
            pk = _player_name_key(p)
            if pk in assigned:
                continue
            info = resolve_player_position_info(p, team_name)
            prefs = info["slot_prefs"]
            if slot in prefs:
                score = 200.0 - prefs.index(slot) * 40.0
            elif slot == "PG" and info["role_label"] in ("Guard", "G"):
                score = 120.0
            elif slot == "SG" and info["role_label"] in ("Guard", "G", "Wing"):
                score = 100.0
            elif slot == "SF" and info["role_label"] in ("Wing", "Forward", "F"):
                score = 100.0
            elif slot == "PF" and info["role_label"] in ("Forward", "Big", "F"):
                score = 100.0
            elif slot == "C" and info["role_label"] in ("C", "Center", "Big"):
                score = 120.0
            else:
                score = 20.0
            score -= ranks.get(pk, 50) * 0.5
            if info["source"] == "override":
                score += 8.0
            if score > best_score:
                best_score = score
                best_name = p
        if best_name:
            slots[slot] = best_name
            assigned.add(_player_name_key(best_name))
            assignment_meta[slot] = {
                "player": best_name,
                "source": resolve_player_position_info(best_name, team_name)["source"],
            }

    lineup = [slots[s] or "TBD" for s in LINEUP_SLOTS]
    return lineup


def lineup_position_debug_df(team_name, candidate_names=None):
    """Resolved PG–C board for debugging incorrect assignments."""
    meta = get_lineup_resolution_info(team_name)
    pool = list(candidate_names) if candidate_names else _rotation_player_pool(team_name)
    lineup = build_position_lineup(team_name, candidate_names=candidate_names)
    slot_by_player = {_player_name_key(p): LINEUP_SLOTS[i] for i, p in enumerate(lineup) if p and p != "TBD"}
    rows = []
    for p in pool[:14]:
        flag = "outdated" if _is_outdated_playoff_player(p, team_name) else ""
        info = resolve_player_position_info(p, team_name)
        rows.append({
            "Slot": slot_by_player.get(_player_name_key(p), "—"),
            "Player": p,
            "Role": info["role_label"],
            "Pref slots": " → ".join(info["slot_prefs"]),
            "Source": info["source"],
            "Status": flag,
        })
    for p in meta.get("rejected") or []:
        rows.append({
            "Slot": "—",
            "Player": p,
            "Role": "—",
            "Pref slots": "—",
            "Source": "rejected",
            "Status": "outdated",
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    slot_order = {s: i for i, s in enumerate(LINEUP_SLOTS)}
    df["_ord"] = df["Slot"].map(lambda x: slot_order.get(x, 99))
    return df.sort_values(["_ord", "Player"]).drop(columns=["_ord"]).reset_index(drop=True)


def _is_home_eliminated(team_name):
    """True when Home Dashboard should show offseason / future outlook (not live playoff chase mode)."""
    p = TEAM_PROFILES.get(team_name) or {}
    if not p:
        return False
    try:
        if get_team_playoff_status(team_name).get("status") == "eliminated":
            return True
    except Exception:
        pass
    if _dynamic_playoff_eliminated(team_name):
        return True
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
            "went_right": "Atlanta still played meaningful playoff minutes with a younger supporting cast around Jalen Johnson — there were stretches where pace, screening, and shot-making looked like a modern offense.",
            "elimination_cause": "New York controlled the glass and physicality in too many fourth quarters; when the Knicks shrank the floor to Johnson, Atlanta did not generate enough clean secondary shots or enough stops in succession to extend the series.",
            "playoff_strengths": [
                "Johnson’s downhill pressure and passing still bent defenses even when blitzed.",
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
    "Cleveland Cavaliers": {
        "reflection": {
            "went_right": "Cleveland reached the Eastern Conference Finals with a balanced attack — Mitchell's shot-making, Harden's playmaking, and Mobley/Allen's rim protection kept them competitive in a physical East bracket.",
            "elimination_cause": "New York controlled every game of the Eastern Conference Finals — offensive rebounding, wing defense on Mitchell, and late-clock execution never let Cleveland build a closeout path in the 4-0 sweep.",
            "playoff_strengths": [
                "Mitchell's ability to create efficient looks against set defenses.",
                "Mobley and Allen as a switchable, rim-protecting frontcourt pairing.",
                "Harden's pick-and-roll manipulation and veteran decision-making in half-court.",
            ],
            "playoff_weaknesses": [
                "Offensive droughts when the Knicks loaded to the guards and dared role players to beat them.",
                "Bench scoring consistency in games that stretched into the high-90s.",
                "Turnover stretches that fed New York transition runs.",
            ],
        },
        "priorities": [
            "Secondary shot creation when Mitchell is blitzed in late-clock situations.",
            "Wing size and switchability to survive Knicks-style physical matchups.",
            "Bench scoring that does not crater when starters sit in playoff minutes.",
            "Health management for a backcourt that carried heavy usage all spring.",
        ],
        "roster": {
            "summary": "The core is still a legitimate East contender — the summer is about whether Cleveland adds a wing upgrade or consolidates around Mitchell and Mobley.",
            "bullets": [
                "Free agents: evaluate rotation wings and backup bigs on value contracts.",
                "Veterans: Harden's timeline affects how aggressive the front office is on win-now trades.",
                "Trade candidates: redundant guard minutes or expiring contracts could consolidate into a higher-minute two-way wing.",
                "Extensions: Mobley and Mitchell timelines should drive every cap decision.",
                "Young players: Isaac Okoro and Dean Wade development changes how much wing help must be bought.",
                "Cap: Cleveland can still operate near the tax if moves solve specific playoff problems rather than stacking middling deals.",
            ],
        },
        "future": [
            "The East champion is set — Cleveland's next step is turning a conference-finals run into a roster that can survive seven games against the league's best.",
            "New York and Boston are not standing still; every upgrade must answer a specific matchup problem from this May.",
        ],
        "draft_assets": [
            "Future picks are trade chips only if the return is a clear playoff rotation upgrade.",
            "If picks stay home, prioritize switchable wings or movement shooters who can survive playoff minutes.",
        ],
        "archetypes": [
            "Two-way wing with real size who can guard Brunson/Bridges-type matchups.",
            "Bench scorer who can create when Mitchell sits without turning it over.",
            "Stretch big who can pick-and-pop without being hunted every switch.",
        ],
        "direction": {"label": "Contender with questions", "blurb": "Cleveland is not rebuilding — this exit is about closing the gap between conference finals and a banner chase."},
    },
    "Oklahoma City Thunder": {
        "reflection": {
            "went_right": "OKC still looked like the West's most complete regular-season team — SGA's creation, Chet's rim protection, and elite spacing carried them through a sweep and a Lakers series before San Antonio's length arrived.",
            "elimination_cause": "San Antonio's size and Wembanyama's two-way impact won the closeout: the Thunder could not match the Spurs' defensive rebounding and rim deterrence when possessions slowed in the West finals.",
            "playoff_strengths": [
                "SGA's pick-and-roll mastery and free-throw pressure in clutch minutes.",
                "Chet Holmgren's ability to protect the rim without killing spacing.",
                "Depth and pace that overwhelmed Phoenix and Los Angeles in earlier rounds.",
            ],
            "playoff_weaknesses": [
                "Physicality against San Antonio's length — drivers met help earlier than expected.",
                "Non-star minutes against Wembanyama's presence at the rim.",
                "Late-game execution when the Spurs switched everything and dared role players to beat them.",
            ],
        },
        "priorities": [
            "Interior size and rebounding without sacrificing the switch scheme.",
            "Veteran playoff poise in closeout games — experience at the margins.",
            "Secondary creator who can run offense when SGA sits in high-leverage minutes.",
            "Wing depth that can survive cross-matches against 7-footers.",
        ],
        "roster": {
            "summary": "OKC's young core is the asset — the summer is about adding playoff-grade size while keeping the timeline aligned with SGA's prime.",
            "bullets": [
                "Free agents: target rim protection and veteran wing depth on flexible deals.",
                "Veterans: decide which short-contract vets teach winning habits without blocking Wallace/J-Dub minutes.",
                "Trade candidates: consolidate overlapping guard/wing minutes if a true starting-caliber big becomes available.",
                "Extensions: SGA and Chet timelines should drive every major move.",
                "Young players: Cason Wallace and Aaron Wiggins development reduces how much must be bought externally.",
                "Cap: OKC still has flexibility — one correct upgrade could flip a conference-finals exit into a Finals return.",
            ],
        },
        "future": [
            "The Thunder's arrow still points up — this exit is a matchup lesson against length, not a ceiling statement.",
            "San Antonio proved the West is not a one-team race; OKC must answer the Wembanyama problem before next May.",
        ],
        "draft_assets": [
            "OKC can still draft-and-develop if picks stay — prioritize size and shooting variance reducers.",
            "Outgoing pick protections should be audited before chasing a veteran big on the trade market.",
        ],
        "archetypes": [
            "Physical big who can set screens, rebound, and protect the rim in 20 playoff minutes.",
            "Veteran wing who can defend multiple positions without hurting spacing.",
            "Backup creator who limits turnover spikes when SGA rests.",
        ],
        "direction": {"label": "Rising contender", "blurb": "OKC is one or two correct summer moves away from feeling like the West favorite again — the core is too good to overreact."},
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


def _offseason_playoff_recap_banner(team_name):
    """Eliminated-team playoff path recap — series results before offseason modules."""
    prof = TEAM_PROFILES.get(team_name) or {}
    nick = fan_nick(team_name)
    try:
        exit_line = _elimination_exit_line(team_name)
    except Exception:
        exit_line = prof.get("first_round_result") or "Playoff exit"
    fr = prof.get("first_round_result") or "First-round result logged"
    seed = prof.get("seed", "—")
    th = get_team_theme(team_name)
    return f"""
<div style="padding:14px 16px;border-radius:14px;border:1px solid {th['border']};
background:linear-gradient(135deg,{th['bg0']},#0f172a);margin:0 0 14px;color:#f8fafc">
  <div style="font-size:11px;font-weight:900;letter-spacing:.14em;color:{th['accent']};text-transform:uppercase">Playoff recap</div>
  <div style="font-size:1.1rem;font-weight:900;margin:6px 0">{html.escape(nick)} · postseason closed</div>
  <div style="font-size:13px;line-height:1.5;color:#e2e8f0"><b>How it ended:</b> {html.escape(exit_line)}</div>
  <div style="font-size:12px;color:#cbd5e1;margin-top:6px"><b>First round:</b> {html.escape(fr)} · <b>Seed:</b> {html.escape(str(seed))}</div>
</div>
"""


def render_offseason_future_outlook_sections(team_name):
    """Home Dashboard: high-visibility offseason analysis (eliminated teams only)."""
    st.markdown(_offseason_playoff_recap_banner(team_name), unsafe_allow_html=True)
    render_page_trust_strip("offseason", "Front-office read — not official team statements.")
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

    def _os_list(lines):
        return "<ul>" + "".join(f"<li>{html.escape(str(x))}</li>" for x in lines) + "</ul>"

    if render_fan_section("1 · Season reflection", "📋", caption="What worked and what ended the run.", tone="elim"):
        render_fan_section_open()
    _render_offseason_card_grid([
        ("Tape room", "What went right", ref["went_right"]),
        ("Exit story", "Why the season ended", ref["elimination_cause"]),
        ("Strengths", "Playoff strengths on tape", _os_list(ref["playoff_strengths"])),
        ("Gaps", "Weaknesses exposed", _os_list(ref["playoff_weaknesses"])),
    ])
    render_fan_section_close()

    if render_fan_section("2 · Offseason priorities", "🛠️", caption="Roster needs and construction levers.", tone="elim"):
        render_fan_section_open()
    ro = od["roster"]
    _render_offseason_card_grid([
        ("Priority board", "What the roster needs next", _os_list(od["priorities"])),
        ("Construction", "Roster snapshot", f"{html.escape(ro['summary'])}{_os_list(ro['bullets'])}"),
    ])
    render_fan_section_close()

    if render_fan_section("3 · Future direction", "🧭", caption="Window, timeline, and franchise compass.", tone="elim"):
        render_fan_section_open()
    d = od["direction"]
    future_body = " ".join(od["future"][:2])
    if len(od["future"]) > 2:
        future_body += _os_list(od["future"][2:])
    _render_offseason_card_grid([
        ("Compass", d["label"], d["blurb"]),
        ("Outlook", "What comes next", future_body),
    ])
    render_fan_section_close()

    if render_fan_section("4 · Draft & assets", "📦", caption="Picks, swaps, and trade flexibility.", tone="elim"):
        render_fan_section_open()
    _render_offseason_card_grid([
        ("War chest", "Draft & asset outlook", _os_list(od["draft_assets"])),
    ])
    render_fan_section_close()

    if render_fan_section("5 · Roster turnover watch", "🔄", caption="Contracts, free agency, and movement questions.", tone="elim"):
        render_fan_section_open()
    _render_offseason_card_grid([
        ("Movement", "Players who may not return", _os_list(_offseason_players_out_bullets(od))),
    ])
    render_fan_section_close()

    if render_fan_section("6 · Ideal additions", "➕", caption="Archetypes that fit the holes above.", tone="elim"):
        render_fan_section_open()
    _render_offseason_card_grid([
        ("Shopping list", "Player types to target", _os_list(od["archetypes"])),
    ])
    render_fan_section_close()


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
# (see ``get_playoff_state_cached(True)``). It should mirror known results without
# crowning a winner before a team reaches four wins.
SECOND_ROUND_DEMO_BACKUP = {
    "DET-CLE": {"games":[
        {"Game":"Game 1","Date":"May 4","Score":"Pistons 111, Cavaliers 101","Winner":"Detroit Pistons","GameID":"demo-det-cle-g1"},
        {"Game":"Game 2","Date":"May 6","Score":"Pistons 105, Cavaliers 97","Winner":"Detroit Pistons","GameID":"demo-det-cle-g2"},
        {"Game":"Game 3","Date":"May 8","Score":"Cavaliers 112, Pistons 108","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g3"},
        {"Game":"Game 4","Date":"May 10","Score":"Pistons 102, Cavaliers 99","Winner":"Detroit Pistons","GameID":"demo-det-cle-g4"},
        {"Game":"Game 5","Date":"May 12","Score":"Cavaliers 118, Pistons 114","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g5"},
        {"Game":"Game 6","Date":"May 14","Score":"Cavaliers 101, Pistons 98","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g6"},
        {"Game":"Game 7","Date":"May 17","Score":"Cavaliers 109, Pistons 104","Winner":"Cleveland Cavaliers","GameID":"demo-det-cle-g7"},
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
        {"Game":"Game 1","Date":"May 5","Score":"Spurs 104, Timberwolves 102","Winner":"San Antonio Spurs","GameID":"demo-sas-min-g1"},
        {"Game":"Game 2","Date":"May 7","Score":"Timberwolves 110, Spurs 106","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g2"},
        {"Game":"Game 3","Date":"May 9","Score":"Spurs 112, Timberwolves 108","Winner":"San Antonio Spurs","GameID":"demo-sas-min-g3"},
        {"Game":"Game 4","Date":"May 11","Score":"Spurs 114, Timberwolves 105","Winner":"San Antonio Spurs","GameID":"demo-sas-min-g4"},
        {"Game":"Game 5","Date":"May 13","Score":"Timberwolves 109, Spurs 107","Winner":"Minnesota Timberwolves","GameID":"demo-sas-min-g5"},
        {"Game":"Game 6","Date":"May 15","Score":"Spurs 118, Timberwolves 112","Winner":"San Antonio Spurs","GameID":"demo-sas-min-g6"},
    ]},
}

# Emergency/demo backup for conference finals when API has no rows yet.
CONFERENCE_FINALS_DEMO_BACKUP = {
    "CLE-NYK": {"games":[
        {"Game":"Game 1","Date":"May 22","Score":"Knicks 108, Cavaliers 102","Winner":"New York Knicks","GameID":"demo-nyk-cle-g1"},
        {"Game":"Game 2","Date":"May 24","Score":"Knicks 115, Cavaliers 110","Winner":"New York Knicks","GameID":"demo-nyk-cle-g2"},
        {"Game":"Game 3","Date":"May 26","Score":"Knicks 104, Cavaliers 99","Winner":"New York Knicks","GameID":"demo-nyk-cle-g3"},
        {"Game":"Game 4","Date":"May 28","Score":"Knicks 112, Cavaliers 105","Winner":"New York Knicks","GameID":"demo-nyk-cle-g4"},
    ]},
    "OKC-SAS": {"games":[
        {"Game":"Game 1","Date":"May 21","Score":"Thunder 112, Spurs 105","Winner":"Oklahoma City Thunder","GameID":"demo-okc-sas-g1"},
        {"Game":"Game 2","Date":"May 23","Score":"Spurs 118, Thunder 114","Winner":"San Antonio Spurs","GameID":"demo-okc-sas-g2"},
        {"Game":"Game 3","Date":"May 25","Score":"Thunder 121, Spurs 116","Winner":"Oklahoma City Thunder","GameID":"demo-okc-sas-g3"},
        {"Game":"Game 4","Date":"May 27","Score":"Spurs 110, Thunder 107","Winner":"San Antonio Spurs","GameID":"demo-okc-sas-g4"},
        {"Game":"Game 5","Date":"May 29","Score":"Spurs 115, Thunder 108","Winner":"San Antonio Spurs","GameID":"demo-okc-sas-g5"},
        {"Game":"Game 6","Date":"May 31","Score":"Spurs 112, Thunder 104","Winner":"San Antonio Spurs","GameID":"demo-okc-sas-g6"},
    ]},
}

# Single source of truth for NBA Finals Game 1 in this app's playoff universe.
FINALS_GAME1_CANONICAL_SCORE = "Knicks 105, Spurs 95"

# Emergency/demo backup for NBA Finals when API has no rows yet.
NBA_FINALS_DEMO_BACKUP = {
    "NYK-SAS": {"games":[
        {
            "Game": "Game 1",
            "Date": "Jun 3",
            "Score": FINALS_GAME1_CANONICAL_SCORE,
            "Winner": "New York Knicks",
            "GameID": "demo-nyk-sas-g1",
        },
    ]},
}

PLAYOFF_START_DATE = "2026-04-18"
PLAYOFF_END_DATE = "2026-06-30"

# Local schedule fallback for known playoff games. This prevents the Home page
# and Live Game Center from saying "no game" when NBA live feeds lag pregame.
PLAYOFF_SCHEDULE_FALLBACK = [
    {
        "game_id": "fallback-nyk-sas-20260605",
        "date": "2026-06-05",
        "time_et": "20:30",
        "away": "San Antonio Spurs",
        "home": "New York Knicks",
        "round": "NBA Finals",
        "series_key": "NYK-SAS",
        "label": "Spurs at Knicks · Game 2",
        "source": "Local schedule fallback",
    },
    {
        "game_id": "fallback-nyk-sas-20260603",
        "date": "2026-06-03",
        "time_et": "20:00",
        "away": "San Antonio Spurs",
        "home": "New York Knicks",
        "round": "NBA Finals",
        "series_key": "NYK-SAS",
        "label": "Spurs at Knicks · Game 1",
        "source": "Local playoff schedule fallback",
    },
]

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
        {"Game":"Game 1 vs Spurs","Top Play":"Brunson and Towns carried the opening-night offense in a 105–95 Finals Game 1 win.","Why it mattered":"The series opens 1-0 — home court and first-possession tone belong to New York."},
        {"Game":"Game 4 vs Cavaliers","Top Play":"New York closed the East at home to punch the Finals ticket.","Why it mattered":"The conference finals ended 4-0 — the bracket now reads Knicks vs Spurs for the title."},
    ],
    "San Antonio Spurs": [
        {"Game":"Game 6 vs Thunder","Top Play":"Wembanyama's rim protection flipped the West finals on San Antonio's home floor.","Why it mattered":"The Spurs advanced 4-2 — OKC's pace could not survive the length in the closeout game."},
        {"Game":"Game 1 vs Knicks","Top Play":"Castle and Vassell kept the Spurs competitive before the fourth-quarter run.","Why it mattered":"Even in a Game 1 loss, San Antonio showed the length that makes this Finals a possession battle."},
    ],
    "Oklahoma City Thunder": [
        {"Game":"Game 6 vs Spurs","Top Play":"SGA scored 34 but San Antonio's gang rebounding won the closeout.","Why it mattered":"The Thunder's season ended one win shy of the Finals — depth minutes were the margin."},
    ],
    "Cleveland Cavaliers": [
        {"Game":"Game 6 vs Knicks","Top Play":"Mitchell scored 31 in a road elimination game but New York closed the series.","Why it mattered":"Cleveland's run ended in the East finals — the closeout quarter decided the conference champion."},
    ],
    "Minnesota Timberwolves": [
        {"Game":"Game 6 vs Spurs","Top Play":"Anthony Edwards delivered late-game shot creation in a tight finish.","Why it mattered":"It gave Minnesota a fighting chance before the series ended."},
    ],
    "Detroit Pistons": [{"Game":"Game 7 vs Cavaliers","Top Play":"Cade Cunningham kept Detroit competitive in a winner-take-all road game.","Why it mattered":"The young core learned how tight a second-round Game 7 gets."}],
}

# ==========================================================
# API / automatic tracking helpers
# ==========================================================
PLAYOFF_STATE_CACHE_TTL_SEC = 90
PLAYOFF_BRACKET_REFRESH_MS = 60000
LIVE_GC_AUTO_LOAD_STATUSES = frozenset({"live", "starting soon", "final", "scheduled"})
LIVE_GC_ADVANCED_AUTO_STATUSES = frozenset({"live"})

# Full Live Game Center — Layer 1 scoreboard first; heavy tabs load on selection.
LIVE_GC_SAFE_MODE = True
LIVE_GC_FEED_TIMEOUT_SEC = 2.0

# Fast validation path: skip heavy charts, simulations, bracket API sync, and autorefresh.
QA_MODE = False
# Ultra-fast: static/demo snapshot only — no network, no Plotly, minimal HTML (browser QA).
ULTRA_FAST_VALIDATION_MODE = False

# Visible on Cloud (sidebar) — bump when shipping fan UI or deploy wiring fixes.
APP_DEPLOY_BRANCH = "dev"
APP_BUILD_COMMIT = "quality-pass-2026-06-05"

VALIDATION_PLAYOFF_STATE_KEY = "_validation_playoff_stt"
VALIDATION_WARMED_KEY = "_validation_playoff_warmed"

# Developer workspace: when True, Dev Lab appears in the sidebar. When False, use the sidebar toggle.
DEV_MODE = False

PAGE_PERF_KEY = "_nba_page_perf"


def _qa_mode_active():
    try:
        if st.session_state.get("QA_MODE"):
            return True
    except Exception:
        pass
    return bool(globals().get("QA_MODE", False))


def _ultra_fast_active():
    try:
        if st.session_state.get("ULTRA_FAST_VALIDATION_MODE"):
            return True
    except Exception:
        pass
    return bool(globals().get("ULTRA_FAST_VALIDATION_MODE", False))


def _validation_mode_active():
    return _qa_mode_active() or _ultra_fast_active()


def _qa_skip_heavy_ui():
    """Charts, shot maps, legacy simulator, full matchup-intel board."""
    return _validation_mode_active()


def _qa_skip_expensive_apis():
    """Bracket scoreboard loops, live injury pulls, player log fetches where avoidable."""
    return _validation_mode_active()


def _validation_skip_network():
    """No CDN, stats API, ESPN, or player-id lookups."""
    return _ultra_fast_active()


def _validation_full_page_key(page_name):
    return f"_validation_full_{page_name.replace(' ', '_').lower()}"


def _validation_page_deferred(page_name):
    """QA/ultra: heavy body deferred until user expands (ultra defaults deferred)."""
    if _ultra_fast_active():
        return not st.session_state.get(_validation_full_page_key(page_name), False)
    if _qa_mode_active():
        return not st.session_state.get(_validation_full_page_key(page_name), False)
    return False


def _validation_offer_full_page(page_name, *, label="Load full page content"):
    if st.button(label, key=f"val_expand_{_validation_full_page_key(page_name)}"):
        st.session_state[_validation_full_page_key(page_name)] = True
        st.rerun()
    return True


def _warm_validation_playoff_state():
    if not _validation_mode_active():
        return
    if st.session_state.get(VALIDATION_WARMED_KEY):
        return
    t0 = pytime.perf_counter()
    stt = get_playoff_state_cached(True, False)
    st.session_state[VALIDATION_PLAYOFF_STATE_KEY] = stt
    st.session_state[VALIDATION_WARMED_KEY] = True
    st.session_state["_validation_warm_ms"] = (pytime.perf_counter() - t0) * 1000.0


def _get_validation_playoff_state():
    _warm_validation_playoff_state()
    stt = st.session_state.get(VALIDATION_PLAYOFF_STATE_KEY)
    if stt:
        return stt
    return get_playoff_state_cached(True, False)


def _validation_gates_status():
    """What validation modes are skipping (for perf footer / Cloud checks)."""
    return {
        "qa_mode": _qa_mode_active(),
        "ultra_fast": _ultra_fast_active(),
        "api_sync_off": _validation_mode_active(),
        "autorefresh_off": _validation_mode_active(),
        "plotly_skipped": _qa_skip_heavy_ui(),
        "live_gc_safe": _live_gc_safe_mode_active(),
        "lineups_curated": _validation_mode_active(),
        "network_blocked": _validation_skip_network(),
        "playoff_state_session": bool(st.session_state.get(VALIDATION_WARMED_KEY)),
    }




def _sync_validation_mode_globals():
    """Apply persisted fast-load toggles to module globals before heavy startup work."""
    global USE_DEMO_BACKUP, ENABLE_BRACKET_API_REFRESH, QA_MODE, ULTRA_FAST_VALIDATION_MODE
    try:
        QA_MODE = bool(st.session_state.get("QA_MODE", False))
        ULTRA_FAST_VALIDATION_MODE = bool(st.session_state.get("ULTRA_FAST_VALIDATION_MODE", False))
    except Exception:
        QA_MODE = bool(globals().get("QA_MODE", False))
        ULTRA_FAST_VALIDATION_MODE = bool(globals().get("ULTRA_FAST_VALIDATION_MODE", False))
    if _validation_mode_active():
        USE_DEMO_BACKUP = True
        ENABLE_BRACKET_API_REFRESH = False
        _warm_validation_playoff_state()


def _render_validation_mode_banner():
    if not _validation_mode_active():
        return
    g = _validation_gates_status()
    mode = "Lite mode (no network)" if g["ultra_fast"] else "Fast load"
    warm = st.session_state.get("_validation_warm_ms")
    warm_txt = f" · playoff snapshot ready in {warm:.0f} ms" if warm else ""
    st.markdown(
        f"<div style='padding:8px 12px;border-radius:8px;background:#0f172a;color:#e2e8f0;"
        f"font-size:12px;line-height:1.45;margin-bottom:8px'>"
        f"<b>{html.escape(mode)}</b> — API sync off · autorefresh off · Plotly off · "
        f"Live GC safe · curated lineups · session playoff cache{warm_txt}"
        f"{' · <b>no network</b>' if g['network_blocked'] else ''}"
        f" · build <code>{html.escape(str(globals().get('APP_BUILD_COMMIT', '?')))}</code>"
        f" · Home + Matchup Lineups fan UI always on"
        f"</div>",
        unsafe_allow_html=True,
    )


def _live_gc_safe_mode_active():
    return bool(LIVE_GC_SAFE_MODE) or _validation_mode_active()


def _live_gc_game_night_emergency_active():
    """Finals game-night incident path — local-first paint, optional timed feed retry."""
    return bool(LIVE_GC_SAFE_MODE)


def _ensure_game_night_manual_defaults(team_name, profile):
    """Pre-fill Finals G2 teams and series for emergency score entry."""
    nyk, sas = "New York Knicks", "San Antonio Spurs"
    if "manual_live_home_team" not in st.session_state:
        st.session_state["manual_live_home_team"] = nyk
    if "manual_live_away_team" not in st.session_state:
        st.session_state["manual_live_away_team"] = sas
    if "manual_live_series_score" not in st.session_state:
        st.session_state["manual_live_series_score"] = "1 - 0"


def _live_gc_fetch_cdn_timed(timeout_sec=None):
    """CDN scoreboard with hard timeout — skip slow feeds during game night."""
    timeout_sec = timeout_sec if timeout_sec is not None else LIVE_GC_FEED_TIMEOUT_SEC
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fetch_cdn_scoreboard_only)
        try:
            return fut.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            return [], f"timeout (>{timeout_sec:.0f}s)"
        except Exception as exc:
            return [], repr(exc)


def _resolve_live_gc_emergency_local_state(team_name, profile):
    """Instant Layer 1 — local Finals schedule shell, zero network."""
    fb_row = _pick_best_schedule_fallback_row(team_name)
    if not fb_row:
        for row in PLAYOFF_SCHEDULE_FALLBACK:
            if str(row.get("date")) == "2026-06-05":
                fb_row = _fallback_schedule_game_row(row)
                break
    if not fb_row:
        opp, round_name, series_text = _live_gc_profile_context(team_name, profile)
        return {
            "layer": 1,
            "priority": "static",
            "source_label": "Emergency game-night (local)",
            "feed_banner": "Emergency game-night mode active — live feed unavailable, using manual/local score.",
            "parsed": None,
            "game_row": None,
            "snap": {"game_found": False, "detection_tier": "emergency_local"},
            "manual": None,
            "live_count": 0,
            "errors": [],
            "updated_at": datetime.now(timezone.utc),
            "top_scorer": None,
            "cdn_ok": False,
            "round_name": round_name,
            "series_text": series_text,
            "opp": opp,
        }
    parsed = _live_gc_parse_game_row(fb_row, team_name)
    phase = parsed.get("phase", "pregame")
    gs = _layer1_snap_game_status(fb_row, phase)
    sec = _seconds_to_tipoff(fb_row)
    fb_banner = ""
    if sec is not None and -4.5 * 3600 < sec < 0:
        fb_banner = "Game may be in progress — enter score above if the live feed is down."
    elif phase == "pregame":
        fb_banner = "Game 2 scheduled — enter live score above when tipoff starts."
    return {
        "layer": 1,
        "priority": "fallback",
        "source_label": "Emergency game-night (local)",
        "feed_banner": fb_banner,
        "parsed": parsed,
        "game_row": fb_row,
        "snap": {"game_found": True, "game_status": gs, "detection_tier": "emergency_local"},
        "manual": None,
        "live_count": 0,
        "errors": [],
        "updated_at": datetime.now(timezone.utc),
        "top_scorer": None,
        "cdn_ok": False,
    }


def dev_lab_visible():
    """Dev Lab is hidden from normal users unless DEV_MODE or the developer toggle is on."""
    try:
        from suite_workspace import can_show_developer_tools

        return can_show_developer_tools(st=st)
    except ImportError:
        pass
    if DEV_MODE:
        return True
    try:
        return bool(st.session_state.get("dev_lab_enabled", False))
    except Exception:
        return False

def safe_int(x, default=0):
    try: return int(x or default)
    except Exception: return default

def safe_float(x, default=0.0):
    try: return float(x or default)
    except Exception: return default

@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def fetch_completed_games_recent(days_back=30, days_forward=1, api_refresh=False):
    """Opt-in completed game pull for the custom playoff bracket.

    This function uses TWO NBA.com-backed nba_api methods:
      1) scoreboardv2 by date, which is good for specific completed dates.
      2) leaguegamefinder for the full 2025-26 Playoffs, which is better when
         scoreboardv2 returns empty on Streamlit Cloud or misses older games.

    Runs when auto-sync is enabled (default). Merged playoff state uses this feed first;
    bundled fallback scores apply only when the API returns no games for that series.
    """
    if not api_refresh or not NBA_STATS_AVAILABLE:
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
                df = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=6).get_data_frames()[0]
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
            timeout=8,
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


def _peek_sidebar_page_key():
    """Best-effort page key before sidebar radio (override or last visit)."""
    ov = st.session_state.get("page_override")
    if ov:
        label = PAGE_LABEL_ALIASES.get(str(ov), str(ov))
        return PAGES.get(label)
    last = st.session_state.get("page_label_last")
    if last:
        if last in PAGES:
            return PAGES[last]
        label = PAGE_LABEL_ALIASES.get(str(last), str(last))
        return PAGES.get(label)
    return None


def _is_lgc_route_early():
    """Detect Live Game Center before heavy sidebar / playoff setup."""
    try:
        qp = str(st.query_params.get("page", "") or "").lower().replace("-", "_")
        if qp in ("live_game_center", "live_gc", "lgc"):
            return True
    except Exception:
        pass
    return _peek_sidebar_page_key() == "Live Game Center"


def _get_lgc_local_playoff_state():
    """Local/demo bracket snapshot for Live Game Center — no NBA bracket API sync."""
    return get_playoff_state_cached(True, False)


def _set_lgc_route_skip_bracket_api(active: bool):
    globals()["_LGC_ROUTE_SKIP_BRACKET_API"] = bool(active)


def _lgc_route_skip_bracket_api_active():
    return bool(globals().get("_LGC_ROUTE_SKIP_BRACKET_API"))


def get_playoff_refresh_settings():
    """Sidebar-aware flags: NBA API first, bundled demo rows only when the feed is empty."""
    use_demo = bool(globals().get("USE_DEMO_BACKUP", True))
    api_refresh = bool(globals().get("ENABLE_BRACKET_API_REFRESH", True))
    if _lgc_route_skip_bracket_api_active():
        use_demo = True
        api_refresh = False
    if _validation_mode_active():
        use_demo = True
        api_refresh = False
    elif st.session_state.get("portfolio_demo_mode") or st.session_state.get("portfolio_screenshot_mode"):
        use_demo = True
        api_refresh = False
    return use_demo, api_refresh


def get_merged_playoff_state(use_demo_backup=None, api_refresh=None):
    """Single entry point for bracket, Home, history, Legacy, and matchup headers."""
    if use_demo_backup is None or api_refresh is None:
        d_demo, d_api = get_playoff_refresh_settings()
        use_demo_backup = d_demo if use_demo_backup is None else use_demo_backup
        api_refresh = d_api if api_refresh is None else api_refresh
    else:
        d_demo, d_api = use_demo_backup, api_refresh
    if _validation_mode_active() and not d_api and d_demo:
        return _get_validation_playoff_state()
    return get_playoff_state_cached(use_demo_backup, api_refresh)


def first_round_series_for_team(team_name, stt=None):
    """First-round series shell for ``team_name`` from unified playoff state."""
    if stt is None:
        stt = get_merged_playoff_state()
    for _k, s in (stt.get("first") or {}).items():
        if team_name in (s.get("a"), s.get("b")):
            return _k, s
    return None, None


def tick_playoff_state_autorefresh(page_key, interval_ms=None):
    """Rerun the app on a timer so series scores and advancement stay current without code edits."""
    if _validation_mode_active():
        return
    if page_key == "live_game_center":
        return
    if st.session_state.get("portfolio_demo_mode") or st.session_state.get("portfolio_screenshot_mode"):
        return
    if not AUTOREFRESH_AVAILABLE:
        return
    st_autorefresh(interval=interval_ms or PLAYOFF_BRACKET_REFRESH_MS, key=f"playoff_autorefresh_{page_key}")


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
    second = get_merged_playoff_state()["second"]
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
        if any(g.get("Source") == "NBA API" for g in cleaned):
            s["source"] = "NBA API"
        elif any(g.get("Source") == "Static fallback" for g in cleaned):
            s["source"] = "Static fallback"
        elif any(g.get("Source") == "Demo backup" for g in cleaned):
            s["source"] = "Demo backup"
        else:
            s["source"] = "Waiting for API games" if not cleaned else "Bracket state"
    return series


def _static_first_round_games_for_pair(team_a, team_b):
    """Static first-round game rows (used when API has not attached games for a pair)."""
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


@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def build_first_round_series_cached(use_demo_backup=True, api_refresh=True):
    """First-round series: NBA API game logs first, static scores/games when the feed is empty."""
    dynamic = {}
    for key, meta in FIRST_ROUND_SERIES.items():
        dynamic[key] = {
            "conf": meta["conf"],
            "round": "First Round",
            "a": meta["a"],
            "b": meta["b"],
            "a_wins": 0,
            "b_wins": 0,
            "winner": None,
            "games": [],
        }

    for g in fetch_completed_games_recent(api_refresh=api_refresh):
        key = series_key_for_pair(g.get("Home"), g.get("Away"), FIRST_ROUND_SERIES)
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

    if use_demo_backup:
        for key, shell in dynamic.items():
            if shell.get("games"):
                continue
            static_games = _static_first_round_games_for_pair(shell["a"], shell["b"])
            if static_games:
                shell["games"] = [dict(g, Source="Static fallback") for g in static_games]

    result = clean_and_recount_series(dynamic)

    if use_demo_backup:
        for key, shell in result.items():
            static = FIRST_ROUND_SERIES.get(key, {})
            sa = int(static.get("a_wins", 0) or 0)
            sb = int(static.get("b_wins", 0) or 0)
            static_winner = static.get("winner")
            if max(sa, sb) != 4 or min(sa, sb) >= 4:
                continue
            if _series_has_confirmed_winner(shell):
                continue
            shell["a_wins"] = sa
            shell["b_wins"] = sb
            shell["winner"] = static_winner
            if not shell.get("games"):
                shell["games"] = [
                    dict(g, Source="Static fallback")
                    for g in _static_first_round_games_for_pair(shell["a"], shell["b"])
                ]
            shell["source"] = "Static fallback (series scores)"

    return result

@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def build_second_round_series_cached(use_demo_backup=False, api_refresh=False):
    """Build second-round series automatically from NBA API data.

    If use_demo_backup=False, no scores are hard-coded for the current round.
    The bracket waits for the API to report completed games.
    """
    dynamic = {k: {**v, "a_wins":0, "b_wins":0, "winner":None, "games":[]} for k, v in SECOND_ROUND_SERIES_TEMPLATE.items()}

    api_games = fetch_completed_games_recent(api_refresh=api_refresh)
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

    # Optional local playoff cache only if the API has not produced any games for that series.
    if use_demo_backup:
        for key, backup in SECOND_ROUND_DEMO_BACKUP.items():
            if key in dynamic and not dynamic[key].get("games"):
                dynamic[key]["games"] = [dict(g, Source="Demo backup") for g in backup.get("games", [])]

    return clean_and_recount_series(dynamic)

def build_second_round_series():
    use_demo, api_refresh = get_playoff_refresh_settings()
    return build_second_round_series_cached(use_demo, api_refresh)


@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def build_conference_finals_series_cached(use_demo_backup=False, api_refresh=False):
    """East/West Conference Finals shells from second-round winners + API games.

    No hard-coded CF pairings: each conference finals matchup is the two teams
    that won the conference's second-round series, discovered from completed games.
    """
    second = build_second_round_series_cached(use_demo_backup, api_refresh)
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
        for g in fetch_completed_games_recent(api_refresh=api_refresh):
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
        if use_demo_backup and not shell.get("games"):
            backup = CONFERENCE_FINALS_DEMO_BACKUP.get(key)
            if backup:
                shell["games"] = [dict(g, Source="Demo backup") for g in backup.get("games", [])]
        out[key] = shell
    return clean_and_recount_series(out)


def build_conference_finals_series():
    use_demo, api_refresh = get_playoff_refresh_settings()
    return build_conference_finals_series_cached(use_demo, api_refresh)


def _cf_champion_for_conference(cf_map, conf):
    for s in cf_map.values():
        if s.get("conf") == conf and s.get("winner"):
            return s.get("winner")
    return None


@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def build_nba_finals_series_cached(use_demo_backup=False, api_refresh=False):
    """NBA Finals shell once both conference champions exist; games from API only."""
    cf = build_conference_finals_series_cached(use_demo_backup, api_refresh)
    east_ch = _cf_champion_for_conference(cf, "East")
    west_ch = _cf_champion_for_conference(cf, "West")
    if not east_ch or not west_ch:
        return {}
    a, b = sorted([east_ch, west_ch], key=lambda t: (TEAM_PROFILES.get(t, {}).get("seed", 99), t))
    key = canonical_series_key(east_ch, west_ch)
    shell = {"conf": "NBA Finals", "round": "NBA Finals", "a": a, "b": b, "a_wins": 0, "b_wins": 0, "winner": None, "games": []}
    for g in fetch_completed_games_recent(api_refresh=api_refresh):
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
    if use_demo_backup and not shell.get("games"):
        backup = NBA_FINALS_DEMO_BACKUP.get(key)
        if backup:
            shell["games"] = [dict(g, Source="Demo backup") for g in backup.get("games", [])]
    return clean_and_recount_series({key: shell})


def build_nba_finals_series():
    use_demo, api_refresh = get_playoff_refresh_settings()
    return build_nba_finals_series_cached(use_demo, api_refresh)


def sibling_second_round_key(current_key, second_map):
    """The other second-round series in the same conference (dynamic bracket wiring)."""
    conf = second_map.get(current_key, {}).get("conf")
    if not conf:
        return None
    others = [k for k, s in second_map.items() if k != current_key and s.get("conf") == conf]
    return others[0] if len(others) == 1 else None


def _next_round_context_from_state(team_name, stt):
    """Next-round advancement context using an existing playoff state snapshot (no re-fetch)."""
    for coll_name in ("cf", "finals"):
        for _k, s_active in (stt.get(coll_name) or {}).items():
            if team_name in (s_active.get("a"), s_active.get("b")):
                return None

    series_map = stt.get("second") or {}
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
    round_label = "Eastern Conference Finals" if conf == "East" else "Western Conference Finals"
    if paired.get("winner"):
        opponents = [paired["winner"]]
        opponent_text = paired["winner"]
        status_text = f"{team_name} vs {opponent_text} - {round_label}"
    else:
        opponents = [paired.get("a"), paired.get("b")]
        opponent_text = f"{paired.get('a')}/{paired.get('b')} winner"
        status_text = f"{team_name} await {paired.get('a')}/{paired.get('b')} winner"
    opponents = [op for op in opponents if op in TEAM_PROFILES]
    return {
        "advanced": True,
        "eliminated": False,
        "round_label": round_label,
        "opponents": opponents,
        "opponent_text": opponent_text,
        "status_text": status_text,
        "completed_series": current_series,
        "paired_series": paired,
    }


def _all_playoff_series_with_keys_from_state(stt):
    rows = []
    for coll_name in ("finals", "cf", "second", "first"):
        for key, s in (stt.get(coll_name) or {}).items():
            if s:
                rows.append((coll_name, key, s))
    return rows


def _playoff_status_from_state(team_name, stt):
    """Derive one team's playoff status from a unified state snapshot."""
    profile = TEAM_PROFILES.get(team_name) or {}
    series_rows = _all_playoff_series_with_keys_from_state(stt)
    team_series = [(coll, key, s) for coll, key, s in series_rows if team_name in (s.get("a"), s.get("b"))]

    def _status_row(**kwargs):
        series = kwargs.get("series")
        rec = kwargs.get("series_record")
        if not rec and series and team_name in (series.get("a"), series.get("b")):
            tw, ow, _ = _team_series_record(team_name, series)
            kwargs["series_record"] = f"{tw}-{ow}"
        src = kwargs.get("data_source", "")
        if "NBA API" in str(src):
            kwargs["source_kind"] = "API"
        elif "Static" in str(src) or "static" in str(src).lower():
            kwargs["source_kind"] = "static"
        elif "Demo" in str(src) or "fallback" in str(src).lower():
            kwargs["source_kind"] = "fallback"
        elif src == "TEAM_PROFILES" or "TEAM_PROFILES" in str(src):
            kwargs["source_kind"] = "static"
        else:
            kwargs["source_kind"] = "bracket"
        return kwargs

    if not team_series:
        return _status_row(
            team=team_name,
            current_round=profile.get("round", "Playoffs"),
            status="active" if profile.get("status") == "Active" else "eliminated",
            current_opponent=profile.get("current_opponent") or profile.get("first_round_opponent") or "",
            series_wins=0,
            elimination_reason="" if profile.get("status") == "Active" else profile.get("first_round_result", ""),
            data_source="TEAM_PROFILES",
            series=None,
        )

    lost = None
    for _coll, _key, s in team_series:
        if _team_lost_confirmed_series(team_name, s):
            if lost is None or _round_depth(s) > _round_depth(lost):
                lost = s
    if lost:
        tw, ow, opp = _team_series_record(team_name, lost)
        rd = str(lost.get("round") or "Playoffs")
        return _status_row(
            team=team_name,
            current_round=rd,
            status="eliminated",
            current_opponent=opp,
            series_wins=_count_series_wins_for_team(team_name, stt),
            elimination_reason=f"Lost {rd} to {opp}, {tw}-{ow}; opponent reached 4 wins.",
            data_source=lost.get("source", "Bracket state"),
            series_record=f"{tw}-{ow}",
            series=lost,
        )

    active = [
        s for _coll, _key, s in team_series
        if not _series_has_confirmed_winner(s) and _round_depth(s) == max(_round_depth(x[2]) for x in team_series)
    ]
    if active:
        s = active[0]
        tw, ow, opp = _team_series_record(team_name, s)
        return _status_row(
            team=team_name,
            current_round=s.get("round", profile.get("round", "Playoffs")),
            status="active",
            current_opponent=opp,
            series_wins=_count_series_wins_for_team(team_name, stt),
            elimination_reason="",
            data_source=s.get("source", "Bracket state"),
            series_record=f"{tw}-{ow}",
            series=s,
        )

    won = [s for _coll, _key, s in team_series if _series_has_confirmed_winner(s) and s.get("winner") == team_name]
    last_won = max(won, key=_round_depth) if won else None
    next_ctx = _next_round_context_from_state(team_name, stt)
    if next_ctx and next_ctx.get("advanced"):
        status = "awaiting opponent" if len(next_ctx.get("opponents") or []) != 1 else "advanced"
        return _status_row(
            team=team_name,
            current_round=next_ctx.get("round_label", "Next Round"),
            status=status,
            current_opponent=next_ctx.get("opponent_text", "TBD"),
            series_wins=_count_series_wins_for_team(team_name, stt),
            elimination_reason="",
            data_source=(next_ctx.get("completed_series") or {}).get("source", "Bracket advancement"),
            series=next_ctx.get("completed_series"),
        )
    if last_won:
        return _status_row(
            team=team_name,
            current_round=last_won.get("round", "Playoffs"),
            status="advanced",
            current_opponent="TBD",
            series_wins=_count_series_wins_for_team(team_name, stt),
            elimination_reason="",
            data_source=last_won.get("source", "Bracket state"),
            series=last_won,
        )

    return _status_row(
        team=team_name,
        current_round=profile.get("round", "Playoffs"),
        status="active",
        current_opponent=profile.get("current_opponent") or profile.get("first_round_opponent") or "",
        series_wins=_count_series_wins_for_team(team_name, stt),
        elimination_reason="",
        data_source="TEAM_PROFILES fallback",
        series=None,
    )


def _build_team_status_map(stt):
    return {team: _playoff_status_from_state(team, stt) for team in TEAM_PROFILES}


def get_team_playoff_status(team_name, stt=None):
    """Read team status from the unified playoff state (preferred over ad-hoc profile fields)."""
    if stt is None:
        stt = get_merged_playoff_state()
    cached = (stt.get("team_status") or {}).get(team_name)
    if cached:
        return cached
    return _playoff_status_from_state(team_name, stt)


def _round_short_label(round_label):
    rd = str(round_label or "")
    if "NBA Finals" in rd:
        return "NBA Finals"
    if "Conference Finals" in rd or "Conf Finals" in rd:
        return "Conf Finals"
    if "Second Round" in rd or "Semifinal" in rd:
        return "Round 2"
    if "First Round" in rd:
        return "Round 1"
    if "Eliminated" in rd:
        return "Eliminated"
    return rd[:32] if rd else "Playoffs"


def get_display_matchup(team_name, stt=None):
    """Fan-facing matchup context — same round, opponent, score, and status on every page."""
    if stt is None:
        stt = get_merged_playoff_state()
    pst = get_team_playoff_status(team_name, stt)
    profile = TEAM_PROFILES.get(team_name) or {}
    status = str(pst.get("status") or "active")
    round_label = pst.get("current_round") or profile.get("round", "Playoffs")
    opponent = pst.get("current_opponent") or profile.get("first_round_opponent") or ""
    series_record = pst.get("series_record") or "—"
    series = pst.get("series")
    if (not series_record or series_record == "—") and series and team_name in (series.get("a"), series.get("b")):
        tw, ow, _ = _team_series_record(team_name, series)
        series_record = f"{tw}–{ow}"
    status_badge = {
        "eliminated": "OUT · offseason outlook",
        "active": "IN THE HUNT",
        "advanced": "ADVANCED",
        "awaiting opponent": "AWAITING OPPONENT",
    }.get(status, status.replace("_", " ").upper())
    return {
        "team": team_name,
        "team_nick": fan_nick(team_name),
        "opponent": opponent,
        "opponent_nick": fan_nick(opponent) if opponent and opponent not in ("TBD", "") else "TBD",
        "round": round_label,
        "round_short": _round_short_label(round_label),
        "status": status,
        "status_badge": status_badge,
        "eliminated": status == "eliminated",
        "series_record": series_record,
        "series_wins": int(pst.get("series_wins", 0) or 0),
        "source": pst.get("data_source") or "",
        "source_kind": pst.get("source_kind") or "",
        "pst": pst,
        "series": series,
    }


def get_effective_team_profile(team_name, stt=None):
    """Team profile overlaid with unified bracket state — round, opponent, and status stay current."""
    base = dict(TEAM_PROFILES.get(team_name) or {})
    try:
        dm = get_display_matchup(team_name, stt)
        status = str(dm.get("status") or "active")
        if dm.get("eliminated") or status == "eliminated":
            base["status"] = "Eliminated"
            base["round"] = dm.get("round") or "Lost in playoffs"
            base["current_opponent"] = None
        elif status == "awaiting opponent":
            base["status"] = "Active"
            base["round"] = dm.get("round") or base.get("round", "Playoffs")
            base["current_opponent"] = None
        else:
            base["status"] = "Active"
            base["round"] = dm.get("round") or base.get("round", "Playoffs")
            opp = dm.get("opponent")
            if opp and opp not in ("TBD", ""):
                base["current_opponent"] = opp
    except Exception:
        pass
    return base


@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def get_playoff_state_cached(use_demo_backup: bool = True, api_refresh: bool = True):
    """Single cached playoff engine: every round, team status, and series scores in one snapshot."""
    first = build_first_round_series_cached(use_demo_backup, api_refresh)
    second = build_second_round_series_cached(use_demo_backup, api_refresh)
    cf = build_conference_finals_series_cached(use_demo_backup, api_refresh)
    nf = build_nba_finals_series_cached(use_demo_backup, api_refresh)
    east_fr = [dict(s) for s in first.values() if s.get("conf") == "East"]
    west_fr = [dict(s) for s in first.values() if s.get("conf") == "West"]
    east_sr = [s for s in second.values() if s.get("conf") == "East"]
    west_sr = [s for s in second.values() if s.get("conf") == "West"]
    east_cf = {k: v for k, v in (cf or {}).items() if v.get("conf") == "East"}
    west_cf = {k: v for k, v in (cf or {}).items() if v.get("conf") == "West"}
    stt = {
        "first": first,
        "second": second,
        "cf": cf or {},
        "finals": nf or {},
        "east_fr": east_fr,
        "west_fr": west_fr,
        "east_sr": east_sr,
        "west_sr": west_sr,
        "east_cf": east_cf if east_cf else None,
        "west_cf": west_cf if west_cf else None,
        "use_demo_backup": use_demo_backup,
        "api_refresh": api_refresh,
    }
    stt["team_status"] = _build_team_status_map(stt)
    return stt


ROUND_DEPTH_FOR_EXIT = {
    "NBA Finals": 4,
    "Conference Finals": 3,
    "Second Round": 2,
    "First Round": 1,
}


def _series_has_confirmed_winner(series):
    """A playoff series is complete only when one side has four wins."""
    if not series:
        return False
    a_wins = int(series.get("a_wins", 0) or 0)
    b_wins = int(series.get("b_wins", 0) or 0)
    winner = series.get("winner")
    if winner == series.get("a"):
        return a_wins == 4 and b_wins < 4
    if winner == series.get("b"):
        return b_wins == 4 and a_wins < 4
    return False


def _team_series_record(team_name, series):
    if team_name == series.get("a"):
        return int(series.get("a_wins", 0) or 0), int(series.get("b_wins", 0) or 0), series.get("b")
    if team_name == series.get("b"):
        return int(series.get("b_wins", 0) or 0), int(series.get("a_wins", 0) or 0), series.get("a")
    return 0, 0, None


def _team_lost_confirmed_series(team_name, series):
    if team_name not in (series.get("a"), series.get("b")):
        return False
    if not _series_has_confirmed_winner(series):
        return False
    team_wins, opp_wins, _opp = _team_series_record(team_name, series)
    return opp_wins == 4 and team_wins < 4 and series.get("winner") != team_name


def _iter_playoff_series_shells_merged(stt=None):
    """All playoff series shells from the unified cached playoff state."""
    if stt is None:
        use_demo, api_refresh = get_playoff_refresh_settings()
        stt = get_playoff_state_cached(use_demo, api_refresh)
    for coll in ("finals", "cf", "second", "first"):
        for s in (stt.get(coll) or {}).values():
            if s:
                yield s


def _last_elimination_series_for_team(team_name):
    """Deepest completed series on the bracket where ``team_name`` lost (any round)."""
    best = None
    best_depth = -1
    for s in _iter_playoff_series_shells_merged():
        if team_name not in (s.get("a"), s.get("b")):
            continue
        if not _team_lost_confirmed_series(team_name, s):
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


def _count_series_wins_for_team(team_name, stt=None):
    """How many completed playoff series ``team_name`` has won (requires confirmed 4-win series)."""
    if not team_name:
        return 0
    n = 0
    try:
        for s in _iter_playoff_series_shells_merged(stt):
            if team_name not in (s.get("a"), s.get("b")):
                continue
            if _series_has_confirmed_winner(s) and s.get("winner") == team_name:
                n += 1
    except Exception:
        return 0
    return n


def validate_playoff_factual_accuracy(stt=None):
    """
    Data validation guard for playoff results and game standouts.
    Returns a list of human-readable error strings (empty when clean).
    """
    errors = []
    if stt is None:
        stt = get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)

    active_static = [t for t, p in TEAM_PROFILES.items() if p.get("status") == "Active"]
    if set(active_static) != {"New York Knicks", "San Antonio Spurs"}:
        errors.append(f"static Active teams expected Knicks+Spurs, got {active_static}")

    finals = stt.get("finals") or {}
    if not finals:
        errors.append("NBA Finals shell missing from merged playoff state")
    else:
        for _k, s in finals.items():
            teams = {s.get("a"), s.get("b")}
            if teams != {"New York Knicks", "San Antonio Spurs"}:
                errors.append(f"Finals matchup must be Knicks vs Spurs, got {teams}")

    cf = stt.get("cf") or {}
    cle_nyk = cf.get("CLE-NYK")
    if cle_nyk:
        nyk = "New York Knicks"
        cle = "Cleveland Cavaliers"
        if cle_nyk.get("winner") != nyk:
            errors.append(f"East CF winner must be Knicks, got {cle_nyk.get('winner')}")
        tw, ow, _opp = _team_series_record(nyk, cle_nyk)
        if not (tw == 4 and ow == 0):
            errors.append(f"Knicks vs Cavaliers CF must be 4-0, engine shows {tw}-{ow}")

    cf_scores = {g.get("Score") for g in (cle_nyk or {}).get("games") or [] if g.get("Score")}
    for _fk, fs in (finals or {}).items():
        teams = {fs.get("a"), fs.get("b")}
        if teams == {"New York Knicks", "San Antonio Spurs"}:
            games = fs.get("games") or []
            if games and str(games[0].get("Score", "")) != FINALS_GAME1_CANONICAL_SCORE:
                errors.append(
                    f"Finals G1 score must be {FINALS_GAME1_CANONICAL_SCORE!r}, "
                    f"got {games[0].get('Score')!r}"
                )
        for g in fs.get("games") or []:
            sc = g.get("Score")
            if sc and sc in cf_scores:
                errors.append(f"Finals game score duplicates East CF row: {sc!r}")
            if sc in ("Knicks 118, Spurs 112", "Knicks 108, Spurs 102"):
                errors.append(f"Finals game uses retired incorrect score: {sc!r}")

    for team_name in ("New York Knicks", "San Antonio Spurs"):
        prof = TEAM_PROFILES.get(team_name) or {}
        for name in (prof.get("starters") or []) + (prof.get("subs") or []):
            if _is_outdated_playoff_player(name, team_name):
                errors.append(f"{team_name}: active profile lists outdated player {name!r}")

    for s in _iter_playoff_series_shells_merged(stt):
        a, b = s.get("a"), s.get("b")
        games = s.get("games") or []
        calc_a = sum(1 for g in games if g.get("Winner") == a)
        calc_b = sum(1 for g in games if g.get("Winner") == b)
        if int(s.get("a_wins", 0) or 0) != calc_a:
            errors.append(f"{a} vs {b}: a_wins {s.get('a_wins')} != game-log wins {calc_a}")
        if int(s.get("b_wins", 0) or 0) != calc_b:
            errors.append(f"{a} vs {b}: b_wins {s.get('b_wins')} != game-log wins {calc_b}")
        if _series_has_confirmed_winner(s):
            w = s.get("winner")
            ww = calc_a if w == a else calc_b if w == b else 0
            if ww != 4:
                errors.append(f"{a} vs {b}: winner {w} must have 4 game-log wins, has {ww}")

        for idx, g in enumerate(games, start=1):
            winner = g.get("Winner")
            win_side = winner if winner in (a, b) else None
            for name in (g.get("Game MVP"),):
                if name and not _validate_game_standout_candidate(name, a, b, win_side):
                    errors.append(
                        f"{a} vs {b} game {idx}: standout {name!r} not valid for winner/participating roster"
                    )
            mvp, _why = mvp_for_game(a, b, idx, winner)
            if mvp and not _validate_game_standout_candidate(mvp, a, b, win_side):
                errors.append(f"{a} vs {b} game {idx}: resolved standout {mvp!r} failed validation")

    team_status = stt.get("team_status") or {}
    for team_name, prof in TEAM_PROFILES.items():
        pst = team_status.get(team_name) or {}
        engine_elim = str(pst.get("status", "")).lower() == "eliminated"
        static_elim = prof.get("status") == "Eliminated"
        if engine_elim != static_elim:
            errors.append(f"{team_name}: engine eliminated={engine_elim} vs static Eliminated={static_elim}")
    for elim in ELIMINATED_INFO:
        if elim[0] == "Cleveland Cavaliers" and "4-2" in str(elim[4]):
            errors.append("Cleveland static elimination text still says 4-2")
        if elim[0] == "Atlanta Hawks" and "Trae Young" in (elim[5] or []):
            errors.append("Atlanta static roster still lists Trae Young as active")

    return errors


def infer_next_round_series(round_name, conf=None):
    """Return series dict(s) for Conference Finals or NBA Finals (from cached playoff state)."""
    use_demo, api_refresh = get_playoff_refresh_settings()
    stt = get_playoff_state_cached(use_demo, api_refresh)
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
    use_demo, api_refresh = get_playoff_refresh_settings()
    stt = get_playoff_state_cached(use_demo, api_refresh)
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


@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def get_team_context_cached(team_name: str, use_demo_backup: bool = True, api_refresh: bool = True):
    """Central lightweight team context reused by pages without rewalking bracket state."""
    profile = get_effective_team_profile(team_name)
    stt = get_playoff_state_cached(use_demo_backup, api_refresh)
    current_key, current_series = None, None
    for coll_name in ("finals", "cf", "second"):
        for key, s in (stt.get(coll_name) or {}).items():
            if team_name in (s.get("a"), s.get("b")):
                current_key, current_series = key, s
                break
        if current_series:
            break
    return {
        "team_name": team_name,
        "profile": profile,
        "playoff_state": stt,
        "series_key": current_key,
        "series": current_series,
        "logo": TEAM_LOGOS.get(team_name, ""),
        "theme": get_team_theme(team_name) if "get_team_theme" in globals() else {},
    }


@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def get_series_snapshot_cached(team_name: str, use_demo_backup: bool = True, api_refresh: bool = True):
    """Central series snapshot for fast page headers and summaries."""
    ctx = get_team_context_cached(team_name, use_demo_backup, api_refresh)
    s = ctx.get("series")
    profile = ctx.get("profile") or {}
    if not s:
        return {
            "team_name": team_name,
            "opponent": profile.get("current_opponent") or profile.get("first_round_opponent"),
            "round": profile.get("round", "Playoffs"),
            "series_score": "—",
            "latest_game": None,
            "source": "local team profile",
        }
    a, b = s["a"], s["b"]
    tw = int(s["a_wins"]) if team_name == a else int(s["b_wins"])
    ow = int(s["b_wins"]) if team_name == a else int(s["a_wins"])
    return {
        "team_name": team_name,
        "opponent": b if team_name == a else a,
        "round": s.get("round", profile.get("round", "Playoffs")),
        "series_score": f"{tw}-{ow}",
        "latest_game": (s.get("games") or [None])[-1],
        "source": s.get("source", "local bracket"),
    }


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
    if _series_has_confirmed_winner(s):
        if s.get("winner") == team_name:
            return f"{rnd}: You won the series {team_w}-{opp_w} over {fan_nick(opp)}{source_note}"
        return f"{rnd}: {fan_nick(opp)} won the series {opp_w}-{team_w}; {fan_nick(team_name)} are eliminated{source_note}"
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


def _live_gc_debug_enabled():
    return bool(globals().get("SHOW_PERF_DEBUG", False))


def _live_gc_trace(event, **fields):
    """Append Live Game Center diagnostics (session-only; shown when Show performance debug is on)."""
    if not _live_gc_debug_enabled():
        return
    log = st.session_state.setdefault("live_gc_trace", [])
    log.append({"t": pytime.perf_counter(), "event": str(event), **fields})
    if len(log) > 250:
        st.session_state["live_gc_trace"] = log[-250:]


def _live_gc_trace_clear():
    if _live_gc_debug_enabled():
        st.session_state["live_gc_trace"] = []


def _live_gc_log_error(errors, tag, exc):
    """Record technical failures for the debug panel only."""
    if exc is None:
        return
    msg = exc if isinstance(exc, str) else repr(exc)
    if _live_gc_debug_enabled():
        errors.append(f"{tag}: {msg}")


def _live_gc_fan_msg(key, **fmt):
    """Fan-facing status text — never expose raw API exceptions."""
    templates = {
        "feed_delayed": "Live feed is delayed.",
        "feed_delayed_stats": "Live feed is delayed — showing league stats score until the live board syncs.",
        "feed_delayed_partial": "Live feed is delayed — score may take a moment to update.",
        "last_known": "Using last known score — live feed is delayed. Tap Refresh to try again.",
        "no_game": (
            "No live game in the feed right now. Try **Refresh** closer to tipoff, "
            "or use **Emergency score entry** below."
        ),
        "detail_unavailable": "Detailed stats are temporarily unavailable.",
    }
    text = templates.get(key, "Live feed is delayed.")
    if fmt:
        try:
            return text.format(**fmt)
        except Exception:
            return text
    return text


def _format_live_gc_age(dt):
    """Short relative time for last-known score labeling."""
    if not dt:
        return ""
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(str(dt).replace("Z", "+00:00"))
        sec = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
        if sec < 45:
            return "just now"
        if sec < 3600:
            return f"{max(1, int(sec // 60))} min ago"
        return f"{max(1, int(sec // 3600))} hr ago"
    except Exception:
        return ""


def _cache_data_fingerprint(fn):
    """Best-effort Streamlit cache stats for debug panel."""
    try:
        info = fn.cache_info()
        return {"hits": info.hits, "misses": info.misses, "size": info.curr_size, "max": info.max_size}
    except Exception:
        return None


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
        rows = []
        seen = set()
        for team in TEAM_PROFILES:
            for g in _fallback_schedule_games_for_team(team):
                gid = str(g.get("gameId") or "")
                if gid and gid not in seen:
                    seen.add(gid)
                    rows.append(normalize_scoreboard_game(dict(g)))
        return rows


def _get_live_games_traced():
    """CDN scoreboard with cache-hit detection + timing (debug only)."""
    before = _cache_data_fingerprint(get_live_games)
    t0 = pytime.perf_counter()
    games = get_live_games()
    ms = (pytime.perf_counter() - t0) * 1000.0
    after = _cache_data_fingerprint(get_live_games)
    cache_hit = bool(before and after and after.get("hits", 0) > before.get("hits", 0))
    _live_gc_trace(
        "cdn_scoreboard.ScoreBoard",
        ms=round(ms, 1),
        cache_hit=cache_hit,
        count=len(games) if isinstance(games, list) else 0,
        status="empty" if not games else "ok",
    )
    return games


@st.cache_data(ttl=15)
def fetch_cdn_scoreboard_only():
    """CDN live scoreboard only — no local schedule fallback (Layer 1 fast path)."""
    if not NBA_LIVE_AVAILABLE:
        return [], "nba_live_unavailable"
    last_exc = None
    for attempt in range(2):
        try:
            try:
                games = scoreboard.ScoreBoard(timeout=5).get_dict().get("scoreboard", {}).get("games", []) or []
            except TypeError:
                games = scoreboard.ScoreBoard().get_dict().get("scoreboard", {}).get("games", []) or []
            return games, None
        except Exception as exc:
            last_exc = exc
    return [], repr(last_exc)


@st.cache_data(ttl=18)
def _scoreboard_stats_today_et():
    """Single-date stats board (today ET) — used only when CDN misses on Layer 1."""
    return _scoreboard_v2_games_for_date(_nba_et_date_today())


LIVE_GC_LAST_KNOWN_TTL_SEC = 10800  # 3 hours — covers a full game if the feed drops mid-game


def _live_gc_last_known_key(team_name):
    return f"live_gc_last_known_{team_name}"


def _live_gc_save_last_known(team_name, parsed, game_row, source_label):
    if not team_name or not parsed or not game_row:
        return
    if _is_live_gc_shell_row(game_row):
        return
    st.session_state[_live_gc_last_known_key(team_name)] = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "parsed": dict(parsed),
        "game_row": dict(game_row) if isinstance(game_row, dict) else game_row,
        "source_label": source_label,
    }


def _live_gc_load_last_known(team_name):
    raw = st.session_state.get(_live_gc_last_known_key(team_name))
    if not isinstance(raw, dict):
        return None
    saved_at = raw.get("saved_at")
    if saved_at:
        try:
            ts = datetime.fromisoformat(str(saved_at).replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - ts).total_seconds() > LIVE_GC_LAST_KNOWN_TTL_SEC:
                return None
        except Exception:
            pass
    return raw


def _is_live_gc_shell_row(game_row):
    if not isinstance(game_row, dict):
        return True
    gid = str(game_row.get("gameId") or "")
    return bool(game_row.get("_fallback_schedule")) or gid.startswith("fallback-") or gid.startswith("manual-")


def _live_gc_suspicious_zero_zero_live(parsed):
    """Live Q1+ with 0–0 is usually a stale CDN row — do not treat as real scoreboard."""
    if not isinstance(parsed, dict):
        return False
    if parsed.get("phase") != "live":
        return False
    period = safe_int(parsed.get("period", 0), 0)
    if period < 1:
        return False
    return safe_int(parsed.get("away_score", 0), 0) == 0 and safe_int(parsed.get("home_score", 0), 0) == 0


def _live_gc_row_needs_stats_enrich(game_row):
    """CDN row present but scores/clock may be stale — merge stats-today."""
    if not isinstance(game_row, dict) or _is_live_gc_shell_row(game_row):
        return True
    home = game_row.get("homeTeam") or {}
    away = game_row.get("awayTeam") or {}
    hs = safe_int(home.get("score", 0))
    aws = safe_int(away.get("score", 0))
    phase = _live_broadcast_phase(game_row)
    clock = str(game_row.get("gameClock") or "").strip()
    period = safe_int(game_row.get("period", 0), 0)
    if phase == "live" and hs == 0 and aws == 0:
        return True
    if phase == "live" and period >= 1 and not clock:
        return True
    return False


def _layer1_snap_game_status(game_row, phase):
    """Map scoreboard row → home/Live GC status string."""
    sec = _seconds_to_tipoff(game_row) if game_row else None
    if phase == "live":
        return "live"
    if phase == "postgame":
        return "final"
    if phase == "pregame" and sec is not None and 0 <= sec <= 3600:
        return "starting soon"
    return "scheduled"


def _layer1_state_to_home_snap(state):
    """Convert Layer 1 resolver output to the legacy home-card snap shape."""
    if not state or not state.get("parsed"):
        return None
    p = state["parsed"]
    game_row = state.get("game_row") or {}
    phase = p.get("phase") or _live_broadcast_phase(game_row)
    sec = _seconds_to_tipoff(game_row) if game_row else None
    gstat = _layer1_snap_game_status(game_row, phase)
    return {
        "game_found": True,
        "game_status": gstat,
        "phase": phase,
        "game_row": game_row,
        "home_team": p.get("home_name"),
        "away_team": p.get("away_name"),
        "home_score": p.get("home_score"),
        "away_score": p.get("away_score"),
        "period": p.get("period"),
        "clock": p.get("clock"),
        "game_status_text": p.get("status"),
        "game_id": p.get("gid"),
        "data_source": state.get("source_label"),
        "detection_tier": (state.get("snap") or {}).get("detection_tier"),
        "detection_message": state.get("feed_banner") or "",
        "seconds_to_tipoff": sec,
        "countdown": _format_countdown(sec),
        "starting_soon": gstat == "starting soon",
        "error_messages": state.get("errors") or [],
    }


@st.cache_data(ttl=28)
def get_home_layer1_snapshot_cached(team_name):
    """CDN-first game snapshot for Home (cached ~28s — avoids duplicate CDN hits per rerun)."""
    profile = get_effective_team_profile(team_name)
    try:
        return _layer1_state_to_home_snap(_resolve_live_gc_layer1_fast(team_name, profile))
    except Exception:
        return None


def get_home_layer1_snapshot(team_name):
    """CDN-first game snapshot for Home Dashboard (no box score / PBP)."""
    return get_home_layer1_snapshot_cached(team_name)


def _live_gc_profile_context(team_name, profile):
    """Series/matchup labels from unified bracket state (not static profile fields)."""
    dm = get_display_matchup(team_name)
    opp = str(dm.get("opponent") or "").strip()
    round_name = dm.get("round") or (profile or {}).get("round") or "Playoffs"
    series_record = str(dm.get("series_record") or "").strip()
    if opp and opp not in ("TBD", ""):
        if series_record and series_record not in ("—", "-", ""):
            parts = series_record.replace("-", "–").split("–")
            if len(parts) == 2:
                tw, ow = parts[0].strip(), parts[1].strip()
                series_text = f"{fan_nick(team_name)} {tw}–{ow} {fan_nick(opp)}"
            else:
                series_text = f"{fan_nick(team_name)} vs {fan_nick(opp)}"
        else:
            series_text = f"{fan_nick(team_name)} vs {fan_nick(opp)}"
    elif dm.get("status") == "awaiting opponent":
        series_text = f"{fan_nick(team_name)} · awaiting opponent"
    else:
        series_text = fan_nick(team_name)
    return opp, round_name, series_text


def _pick_best_team_game_from_pool(games, team_name):
    """Choose best CDN/stats row for sidebar team from a list."""
    if not games or not team_name:
        return None
    profile = get_effective_team_profile(team_name)
    dm = get_display_matchup(team_name)
    opponent = dm.get("opponent") or profile.get("current_opponent")
    if opponent in ("TBD", ""):
        opponent = profile.get("current_opponent")
    candidates = []
    for g in games:
        gn = normalize_scoreboard_game(dict(g))
        if _is_live_gc_shell_row(gn):
            continue
        if _game_involves_team(gn, team_name) or (opponent and _game_involves_team(gn, opponent)):
            candidates.append(gn)
        elif _game_involves_team_loose(gn, team_name) or (opponent and _game_involves_team_loose(gn, opponent)):
            candidates.append(gn)
    if not candidates:
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
            return (2, sec, 0)
        if phase == "postgame":
            return (4, -sec if sec else 0, 0)
        return (5, sec, 0)

    candidates.sort(key=sort_key)
    return candidates[0]


def _live_gc_top_scorer_snapshot(game_row, team_name):
    """Top scorer from CDN gameLeaders when present — no box score API."""
    if not isinstance(game_row, dict):
        return None
    alias = (TEAM_ALIASES.get(team_name) or "").upper()
    leaders = game_row.get("gameLeaders") or {}
    best = None
    for side_key in ("homeLeaders", "awayLeaders"):
        side = leaders.get(side_key) or {}
        pts_leader = side.get("points") or side.get("Points")
        if not isinstance(pts_leader, dict):
            continue
        tri = (pts_leader.get("teamTricode") or "").upper()
        if alias and tri and tri != alias:
            continue
        name = pts_leader.get("name") or pts_leader.get("playerName") or pts_leader.get("familyName") or ""
        if not name:
            parts = [pts_leader.get("firstName"), pts_leader.get("familyName")]
            name = " ".join(str(x) for x in parts if x).strip()
        pts = safe_int(pts_leader.get("points") or pts_leader.get("value"), 0)
        if name and (best is None or pts > best.get("pts", 0)):
            best = {"name": str(name), "pts": pts, "reb": safe_int(pts_leader.get("rebounds"), 0), "ast": safe_int(pts_leader.get("assists"), 0)}
    return best


def _resolve_live_gc_layer1_fast(team_name, profile):
    """
    Layer 1 resolver: CDN first → stats today only → last known score.
    Never returns bracket 0–0 shells over a detected live/partial feed.
    """
    errors = []
    manual = _manual_live_override_snapshot(team_name)
    if manual:
        row = _manual_to_game_row(manual)
        parsed = _live_gc_parse_game_row(row, team_name)
        return {
            "layer": 1,
            "priority": "manual",
            "source_label": "Emergency score entry",
            "feed_banner": "",
            "parsed": parsed,
            "game_row": row,
            "snap": {"game_status": parsed["phase"], "game_found": True},
            "manual": manual,
            "live_count": None,
            "errors": errors,
            "updated_at": datetime.now(timezone.utc),
            "top_scorer": None,
            "cdn_ok": True,
        }

    game_night = _live_gc_game_night_emergency_active()
    force_feed = bool(st.session_state.pop("live_gc_force_feed_retry", False))
    if game_night and not force_feed:
        return _resolve_live_gc_emergency_local_state(team_name, profile)

    t0 = pytime.perf_counter()
    if game_night:
        cdn_games, cdn_err = _live_gc_fetch_cdn_timed()
    else:
        cdn_games, cdn_err = fetch_cdn_scoreboard_only()
    cdn_ms = (pytime.perf_counter() - t0) * 1000.0
    live_count = len(cdn_games) if isinstance(cdn_games, list) else 0
    if cdn_err:
        _live_gc_log_error(errors, "cdn", cdn_err)
    _live_gc_trace("layer1.cdn", ms=round(cdn_ms, 1), count=live_count, error=cdn_err)

    game_row = _pick_best_team_game_from_pool(cdn_games, team_name)
    source_label = "NBA CDN live scoreboard"
    feed_banner = ""
    cdn_ok = game_row is not None and not cdn_err

    stats_row = None
    stats_live_signal = False
    need_stats = not game_night and (game_row is None or cdn_err or _live_gc_row_needs_stats_enrich(game_row))
    if need_stats:
        t1 = pytime.perf_counter()
        try:
            flat = _scoreboard_stats_today_et() if NBA_STATS_AVAILABLE else []
            if not isinstance(flat, list):
                flat = []
            stats_row = _pick_best_team_game_from_pool(flat, team_name)
            if stats_row:
                stats_live_signal = _coarse_live_signal_v2(stats_row) or _live_broadcast_phase(stats_row) == "live"
        except Exception as exc:
            _live_gc_log_error(errors, "stats_today", exc)
        _live_gc_trace(
            "layer1.stats_today",
            ms=round((pytime.perf_counter() - t1) * 1000.0, 1),
            found=bool(stats_row),
            live_signal=stats_live_signal,
        )

    if game_row and stats_row and not _is_live_gc_shell_row(stats_row):
        game_row = _merge_scoreboard_games(game_row, stats_row)
        source_label = "NBA CDN + stats (today)"
    elif game_row is None and stats_row and not _is_live_gc_shell_row(stats_row):
        game_row = stats_row
        source_label = "NBA stats scoreboard (today)"
        if cdn_err or not cdn_games:
            feed_banner = _live_gc_fan_msg("feed_delayed_stats")
        elif stats_live_signal:
            feed_banner = _live_gc_fan_msg("feed_delayed_partial")

    last_known = _live_gc_load_last_known(team_name)

    if game_row and not _is_live_gc_shell_row(game_row):
        parsed = _live_gc_parse_game_row(game_row, team_name)
        if _live_gc_suspicious_zero_zero_live(parsed) and last_known and isinstance(last_known.get("parsed"), dict):
            parsed = dict(last_known["parsed"])
            saved_at = last_known.get("saved_at")
            try:
                lk_dt = (
                    datetime.fromisoformat(str(saved_at).replace("Z", "+00:00"))
                    if saved_at
                    else datetime.now(timezone.utc)
                )
            except Exception:
                lk_dt = datetime.now(timezone.utc)
            feed_banner = feed_banner or _live_gc_fan_msg("last_known")
            return {
                "layer": 1,
                "priority": "stale",
                "source_label": "Using last known score",
                "feed_banner": feed_banner,
                "parsed": parsed,
                "game_row": last_known.get("game_row"),
                "snap": {"game_found": True, "game_status": parsed.get("phase", "live"), "detection_tier": "zero_zero_guard"},
                "manual": None,
                "live_count": live_count,
                "errors": errors,
                "updated_at": lk_dt,
                "last_known_at": lk_dt,
                "top_scorer": None,
                "cdn_ok": cdn_ok,
            }
        top_scorer = _live_gc_top_scorer_snapshot(game_row, team_name)
        if not _live_gc_suspicious_zero_zero_live(parsed):
            _live_gc_save_last_known(team_name, parsed, game_row, source_label)
        phase = parsed.get("phase", "pregame")
        gs = _layer1_snap_game_status(game_row, phase)
        return {
            "layer": 1,
            "priority": "api",
            "source_label": source_label,
            "feed_banner": feed_banner,
            "parsed": parsed,
            "game_row": game_row,
            "snap": {
                "game_found": True,
                "game_status": gs,
                "detection_tier": "ok" if not feed_banner else "likely_live_feed_gap",
            },
            "manual": None,
            "live_count": live_count,
            "errors": errors,
            "updated_at": datetime.now(timezone.utc),
            "top_scorer": top_scorer,
            "cdn_ok": cdn_ok,
        }

    if last_known and isinstance(last_known.get("parsed"), dict):
        parsed = dict(last_known["parsed"])
        saved_at = last_known.get("saved_at")
        try:
            lk_dt = (
                datetime.fromisoformat(str(saved_at).replace("Z", "+00:00"))
                if saved_at
                else datetime.now(timezone.utc)
            )
        except Exception:
            lk_dt = datetime.now(timezone.utc)
        feed_banner = feed_banner or _live_gc_fan_msg("last_known")
        return {
            "layer": 1,
            "priority": "stale",
            "source_label": "Using last known score",
            "feed_banner": feed_banner,
            "parsed": parsed,
            "game_row": last_known.get("game_row"),
            "snap": {"game_found": True, "game_status": parsed.get("phase", "live"), "detection_tier": "stale_cache"},
            "manual": None,
            "live_count": live_count,
            "errors": errors,
            "updated_at": lk_dt,
            "last_known_at": lk_dt,
            "top_scorer": None,
            "cdn_ok": False,
        }

    if stats_row and stats_live_signal and not _is_live_gc_shell_row(stats_row):
        parsed = _live_gc_parse_game_row(stats_row, team_name)
        feed_banner = _live_gc_fan_msg("feed_delayed_stats")
        _live_gc_save_last_known(team_name, parsed, stats_row, source_label)
        return {
            "layer": 1,
            "priority": "api",
            "source_label": source_label,
            "feed_banner": feed_banner,
            "parsed": parsed,
            "game_row": stats_row,
            "snap": {"game_found": True, "game_status": "live", "detection_tier": "likely_live_feed_gap"},
            "manual": None,
            "live_count": live_count,
            "errors": errors,
            "updated_at": datetime.now(timezone.utc),
            "top_scorer": _live_gc_top_scorer_snapshot(stats_row, team_name),
            "cdn_ok": False,
        }

    fb_row = _pick_best_schedule_fallback_row(team_name)
    if fb_row:
        parsed = _live_gc_parse_game_row(fb_row, team_name)
        phase = parsed.get("phase", "pregame")
        gs = _layer1_snap_game_status(fb_row, phase)
        sec = _seconds_to_tipoff(fb_row)
        fb_banner = ""
        det_tier = "scheduled_today"
        if sec is not None and -4.5 * 3600 < sec < 0:
            det_tier = "likely_live_feed_gap"
            fb_banner = "Game may be in progress, but the live feed is delayed."
        elif phase == "pregame":
            fb_banner = "Game scheduled today — live feed not detected yet."
        _live_gc_trace("layer1.schedule_fallback", game_id=fb_row.get("gameId"), status=gs)
        return {
            "layer": 1,
            "priority": "fallback",
            "source_label": fb_row.get("_source") or "Local schedule fallback",
            "feed_banner": fb_banner,
            "parsed": parsed,
            "game_row": fb_row,
            "snap": {
                "game_found": True,
                "game_status": gs,
                "detection_tier": det_tier,
            },
            "manual": None,
            "live_count": live_count,
            "errors": errors,
            "updated_at": datetime.now(timezone.utc),
            "top_scorer": None,
            "cdn_ok": False,
        }

    if game_night:
        return _resolve_live_gc_emergency_local_state(team_name, profile)

    opp, round_name, series_text = _live_gc_profile_context(team_name, profile)
    if cdn_err and not stats_row:
        det_msg = _live_gc_fan_msg("feed_delayed")
    elif not cdn_games and not stats_row:
        det_msg = _live_gc_fan_msg("no_game")
    else:
        det_msg = _live_gc_fan_msg("feed_delayed")
    return {
        "layer": 1,
        "priority": "static",
        "source_label": "Live feed unavailable",
        "feed_banner": det_msg,
        "parsed": None,
        "game_row": None,
        "snap": {"game_found": False, "detection_tier": "no_game_window"},
        "manual": None,
        "live_count": live_count,
        "errors": errors,
        "updated_at": datetime.now(timezone.utc),
        "top_scorer": None,
        "cdn_ok": False,
        "round_name": round_name,
        "series_text": series_text,
        "opp": opp,
    }


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
    t0 = pytime.perf_counter()
    profile = get_effective_team_profile(team_name) or {}
    opponent = profile.get("current_opponent")
    by_gid = {}
    for g in _get_live_games_traced() if _live_gc_debug_enabled() else get_live_games():
        gid = str(g.get("gameId") or "")
        if gid:
            by_gid[gid] = dict(g)
    for d in _nba_calendar_dates_window(1):
        before = _cache_data_fingerprint(_scoreboard_v2_games_for_date) if _live_gc_debug_enabled() else None
        dt0 = pytime.perf_counter()
        day_games = _scoreboard_v2_games_for_date(d)
        if _live_gc_debug_enabled():
            after = _cache_data_fingerprint(_scoreboard_v2_games_for_date)
            cache_hit = bool(before and after and after.get("hits", 0) > before.get("hits", 0))
            _live_gc_trace(
                "stats_scoreboard.date",
                date=d.isoformat(),
                ms=round((pytime.perf_counter() - dt0) * 1000.0, 1),
                cache_hit=cache_hit,
                count=len(day_games),
            )
        for g in day_games:
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
    fallback = _fallback_schedule_games_for_team(team_name)
    result = strict or loose or fallback
    if _live_gc_debug_enabled():
        _live_gc_trace(
            "gather_team_scoreboard",
            team=team_name,
            ms=round((pytime.perf_counter() - t0) * 1000.0, 1),
            strict=len(strict),
            loose=len(loose),
            fallback=len(fallback),
            merged_games=len(by_gid),
            returned=len(result),
        )
    if strict:
        return strict
    if loose:
        return loose
    return fallback


@st.cache_data(ttl=22)
def _merged_stats_games_et_window():
    """All stats scoreboard games for yesterday→tomorrow Eastern (deduped by gameId). CDN not used."""
    if not NBA_STATS_AVAILABLE:
        rows = []
        seen = set()
        for team in TEAM_PROFILES:
            for g in _fallback_schedule_games_for_team(team):
                gid = str(g.get("gameId") or "")
                if gid and gid not in seen:
                    seen.add(gid)
                    rows.append(normalize_scoreboard_game(dict(g)))
        return rows
    merged = {}
    try:
        for d in _nba_calendar_dates_window(1):
            for g in _scoreboard_v2_games_for_date(d):
                gid = str((g or {}).get("gameId") or "")
                if gid:
                    merged[gid] = dict(g)
        rows = [normalize_scoreboard_game(dict(x)) for x in merged.values()]
        for team in TEAM_PROFILES:
            for g in _fallback_schedule_games_for_team(team):
                gid = str(g.get("gameId") or "")
                if gid and gid not in merged:
                    rows.append(normalize_scoreboard_game(dict(g)))
        return rows
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


def _fallback_schedule_tipoff_utc(row):
    et = _nba_et_zone()
    try:
        d = datetime.strptime(str(row.get("date")), "%Y-%m-%d").date()
        hh, mm = [int(x) for x in str(row.get("time_et", "19:30")).split(":", 1)]
        if et:
            return datetime.combine(d, time(hh, mm), tzinfo=et).astimezone(timezone.utc)
        return datetime.combine(d, time(hh + 4, mm), tzinfo=timezone.utc)
    except Exception:
        return None


def _fallback_schedule_game_row(row):
    away = row.get("away")
    home = row.get("home")
    tip = _fallback_schedule_tipoff_utc(row)
    now = datetime.now(timezone.utc)
    if tip:
        sec = (tip - now).total_seconds()
    else:
        sec = None
    if sec is not None and sec < -4.5 * 3600:
        game_status = 3
        status_text = "Final status pending league feed"
    elif sec is not None and sec <= 0:
        game_status = 1
        status_text = "Scheduled today - live feed may be delayed"
    else:
        game_status = 1
        if sec is not None and sec <= 3600:
            mins = max(1, int(round(sec / 60)))
            status_text = f"Game starting soon - {mins} min"
        else:
            status_text = "Scheduled"
    return {
        "gameId": row.get("game_id", ""),
        "gameStatus": game_status,
        "gameStatusText": status_text,
        "period": 0,
        "gameClock": "",
        "gameTimeUTC": tip.isoformat().replace("+00:00", "Z") if tip else None,
        "gameEt": row.get("time_et", ""),
        "seriesText": row.get("round", ""),
        "_source": row.get("source", "Local playoff schedule fallback"),
        "_game_date_est": row.get("date", ""),
        "_fallback_schedule": True,
        "homeTeam": {
            "teamId": TEAM_IDS.get(home, 0),
            "teamTricode": TEAM_ALIASES.get(home, ""),
            "teamName": fan_nick(home),
            "teamCity": " ".join(str(home).split()[:-1]),
            "score": 0,
        },
        "awayTeam": {
            "teamId": TEAM_IDS.get(away, 0),
            "teamTricode": TEAM_ALIASES.get(away, ""),
            "teamName": fan_nick(away),
            "teamCity": " ".join(str(away).split()[:-1]),
            "score": 0,
        },
    }


def _fallback_schedule_games_for_team(team_name, days_each_side=1):
    if not team_name:
        return []
    today = _nba_et_date_today()
    out = []
    for row in PLAYOFF_SCHEDULE_FALLBACK:
        if team_name not in (row.get("home"), row.get("away")):
            continue
        try:
            d = datetime.strptime(str(row.get("date")), "%Y-%m-%d").date()
        except Exception:
            continue
        if abs((d - today).days) <= days_each_side:
            out.append(_fallback_schedule_game_row(row))
    return out


def _pick_best_schedule_fallback_row(team_name):
    """Best local schedule row when CDN/stats have no game (pregame shell)."""
    games = _fallback_schedule_games_for_team(team_name, days_each_side=1)
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
    return games[0]


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
    profile = get_effective_team_profile(team_name) or {}
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


def _format_countdown(seconds):
    if seconds is None:
        return ""
    try:
        sec = int(seconds)
    except Exception:
        return ""
    if sec < 0:
        mins = abs(sec) // 60
        return f"tip was about {mins} min ago"
    mins = sec // 60
    hrs = mins // 60
    rem = mins % 60
    if hrs:
        return f"{hrs}h {rem}m"
    return f"{max(1, mins)}m"


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
            opp = get_effective_team_profile(team_name).get("current_opponent")
            pool = []
            merged = {}
            for g in _merged_stats_games_et_window():
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
    seconds_to_tip = _seconds_to_tipoff(game_row) if game_row else None
    starting_soon = bool(seconds_to_tip is not None and 0 <= seconds_to_tip <= 3600)
    fallback_schedule = bool(isinstance(game_row, dict) and game_row.get("_fallback_schedule"))
    if phase == "live":
        gstat = "live"
    elif phase == "postgame":
        gstat = "final"
    elif phase == "pregame":
        if starting_soon:
            gstat = "starting soon"
        elif fallback_schedule and seconds_to_tip is not None and seconds_to_tip < 0:
            gstat = "scheduled"
        else:
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
        if fallback_schedule and seconds_to_tip is not None and seconds_to_tip < 0 and seconds_to_tip > -4.5 * 3600:
            det_ctx["tier"] = "likely_live_feed_gap"
            det_ctx["likely_feed_gap"] = True
            det_ctx["message"] = "Game may be in progress, but the live feed is delayed."
        elif fallback_schedule:
            det_ctx["tier"] = "scheduled_today"
            det_ctx["likely_feed_gap"] = False
            det_ctx["message"] = "Game scheduled today — live feed not detected yet."
        else:
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
        "tipoff_time_utc": _tipoff_utc_dt(game_row).isoformat() if game_row and _tipoff_utc_dt(game_row) else None,
        "seconds_to_tipoff": seconds_to_tip,
        "countdown": _format_countdown(seconds_to_tip),
        "starting_soon": starting_soon,
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


def get_current_or_upcoming_game(team_name: str):
    """Public detector for Home + Live Game Center: scheduled, starting soon, live, final, unavailable."""
    return get_current_or_today_game(team_name)


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


@st.cache_data(ttl=86400)
def fetch_current_roster(team_name, season=CURRENT_NBA_SEASON):
    """Return current NBA.com roster for a team. Falls back safely if NBA API is unavailable."""
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    tid = TEAM_IDS.get(team_name)
    if not tid:
        return pd.DataFrame()
    try:
        df = commonteamroster.CommonTeamRoster(team_id=tid, season=season, timeout=6).get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        # CommonTeamRoster columns usually include PLAYER, NUM, POSITION, HEIGHT, WEIGHT, AGE, EXP, SCHOOL, PLAYER_ID
        rename = {"PLAYER": "Player", "POSITION": "Position", "NUM": "Number", "PLAYER_ID": "PlayerID"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        keep = [c for c in ["Player", "Position", "Number", "PlayerID", "AGE", "EXP", "SCHOOL"] if c in df.columns]
        return df[keep].drop_duplicates(subset=["Player"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=86400)
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
            timeout=7,
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


@st.cache_data(ttl=3600)
def fetch_playoff_rotation_by_minutes(team_name, season=CURRENT_NBA_SEASON):
    """Playoff minutes leaders — best signal for who is actually playing now."""
    if not NBA_STATS_AVAILABLE:
        return pd.DataFrame()
    tid = TEAM_IDS.get(team_name)
    if not tid:
        return pd.DataFrame()
    try:
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            season_type_all_star="Playoffs",
            team_id_nullable=tid,
            per_mode_detailed="Totals",
            timeout=5,
        ).get_data_frames()[0]
        if df.empty:
            return pd.DataFrame()
        cols = [c for c in ["PLAYER_NAME", "PLAYER_ID", "GP", "MIN", "PTS", "REB", "AST"] if c in df.columns]
        out = df[cols].copy().rename(columns={"PLAYER_NAME": "Player", "PLAYER_ID": "PlayerID"})
        if "MIN" in out.columns:
            out["MIN_SORT"] = pd.to_numeric(out["MIN"], errors="coerce").fillna(0)
            out = out.sort_values("MIN_SORT", ascending=False)
        outdated = _outdated_player_keys(team_name)
        out = out[~out["Player"].astype(str).map(lambda n: _player_name_key(n)).isin(outdated)]
        return out.drop_duplicates(subset=["Player"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86400)
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

@st.cache_data(ttl=86400)
def estimated_starters_from_api(team_name):
    """Five-man lineup ordered PG → C using position overrides, profile slots, and NBA roster data."""
    return build_position_lineup(team_name)

@st.cache_data(ttl=86400)
def estimated_bench_from_api(team_name, start=5, end=12):
    starters = {_player_name_key(p) for p in estimated_starters_from_api(team_name)}
    bench = [n for n in _rotation_player_pool(team_name, limit=18) if _player_name_key(n) not in starters]
    for s in TEAM_PROFILES.get(team_name, {}).get("subs", []):
        if _player_name_key(s) not in starters and s not in bench:
            bench.append(s)
    want = max(0, end - start)
    return bench[:want] if want else TEAM_PROFILES.get(team_name, {}).get("subs", [])


@st.cache_data(ttl=86400)
def get_roster_cached(team_name: str):
    """Central roster context: names first, API tables cached and reused by lineups/player pages."""
    return {
        "names": current_roster_names(team_name),
        "starters": estimated_starters_from_api(team_name),
        "bench": estimated_bench_from_api(team_name),
        "rotation": fetch_team_rotation_by_minutes(team_name),
        "roster": fetch_current_roster(team_name),
    }

@st.cache_data(ttl=86400)
def _player_ids_from_csv():
    """Load full-name → player_id from bundled player.csv (no network)."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player.csv")
    if not os.path.isfile(csv_path):
        return {}
    out = {}
    try:
        df = pd.read_csv(csv_path, usecols=["PERSON_ID", "DISPLAY_FIRST_LAST"])
        for _, row in df.iterrows():
            name = str(row.get("DISPLAY_FIRST_LAST", "")).strip()
            pid = row.get("PERSON_ID")
            if name and pd.notna(pid):
                out[name] = int(pid)
    except Exception:
        pass
    return out


def _resolve_player_id_local(name):
    if not name:
        return None
    hit = PLAYOFF_PLAYER_ID_MAP.get(name)
    if hit:
        return hit
    csv_map = _player_ids_from_csv()
    if name in csv_map:
        return csv_map[name]
    key = _player_name_key(name)
    for full, pid in csv_map.items():
        if _player_name_key(full) == key:
            return pid
    return None


@st.cache_data(ttl=86400)
def get_player_id(name):
    local = _resolve_player_id_local(name)
    if local:
        return local
    if _validation_skip_network():
        return None
    if not NBA_STATS_AVAILABLE:
        return None
    try:
        matches = [p for p in nba_players.get_players() if p["full_name"] == name]
        return matches[0]["id"] if matches else None
    except Exception:
        return None

@st.cache_data(ttl=86400)
def season_averages(name):
    # Prefer cached team rotation rows; this avoids one playercareerstats API call per card.
    for tm, prof in TEAM_PROFILES.items():
        local_names = (prof.get("starters") or []) + (prof.get("subs") or [])
        if name not in local_names:
            continue
        rot = fetch_team_rotation_by_minutes(tm)
        if rot is not None and not rot.empty and "Player" in rot.columns:
            hit = rot[rot["Player"].astype(str).str.lower() == str(name).lower()]
            if not hit.empty:
                r = hit.iloc[0]
                gp = max(float(r.get("GP", 1) or 1), 1)
                out = {}
                for k in ["PTS", "REB", "AST", "STL", "BLK"]:
                    out[k] = round(float(r.get(k, 0) or 0) / gp, 1)
                return out
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

@st.cache_data(ttl=604800)
def headshot(name):
    if _validation_skip_network():
        return ""
    pid = get_player_id(name)
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png" if pid else "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"

@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=3600)
def playoff_game_logs_for_player(name, season=CURRENT_NBA_SEASON, team_name=None):
    """Return current playoff game logs for selected player (API + bracket fallback)."""
    if not team_name:
        for tm, prof in TEAM_PROFILES.items():
            pool = (prof.get("starters") or []) + (prof.get("subs") or [])
            if name in pool:
                team_name = tm
                break
    if not team_name:
        team_name = (
            st.session_state.get("favorite_team")
            or st.session_state.get("_nba_persist_team")
            or "New York Knicks"
        )
    return fetch_playoff_gamelog(name, team_name, season)

@st.cache_data(ttl=3600)
def summarize_playoff_logs_cached(logs):
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


def summarize_playoff_logs(logs):
    return summarize_playoff_logs_cached(logs)

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
            "team_context": "A longer run cements him next to the names New York remembers at guard: Walt Frazier, Earl Monroe, and the modern stars who owned spring at MSG.",
            "comps": ["Walt Frazier", "Willis Reed", "Patrick Ewing", "Earl Monroe", "Carmelo Anthony", "Bernard King"]
        },
        "towns": {
            "baseline": 61, "ceiling": 91, "role": "scoring big",
            "resume": "Towns arrives as a proven offensive big: spacing, touch, and the ability to bend a defense without needing a gimmick.",
            "team_context": "For the Knicks, a deep push ties him to the franchise's big-man lineage; the chapter gets louder if he authors a few unmistakable playoff nights.",
            "comps": ["Patrick Ewing", "Willis Reed", "Dave DeBusschere", "Charles Oakley", "Chris Bosh", "Pau Gasol"]
        },
        "anunoby": {
            "baseline": 50, "ceiling": 82, "role": "two-way wing",
            "resume": "OG is known for winning basketball: guarding the other team's best wing and doing the small things that show up in close games.",
            "team_context": "In New York, the story is simple—become the defender and connector fans replay when they talk about this run.",
            "comps": ["Kawhi Leonard", "Andre Iguodala", "Tayshaun Prince", "Shane Battier", "Scottie Pippen", "Bruce Bowen"]
        },
        "bridges": {
            "baseline": 48, "ceiling": 82, "role": "two-way wing",
            "resume": "Bridges brings ironman minutes, switchable defense, and the kind of reliability coaches lean on when the rotation shortens.",
            "team_context": "For the Knicks, he levels up if he is the guy taking the toughest assignment and still cashing the shots that quiet the road crowd.",
            "comps": ["Andre Iguodala", "Tayshaun Prince", "Shane Battier", "Khris Middleton", "Jimmy Butler", "Kawhi Leonard"]
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
        "edwards": {
            "baseline": 68, "ceiling": 97, "role": "franchise scoring guard",
            "resume": "Edwards brings the playoff star package Minnesota has waited on: downhill pressure, shot-making confidence, and the personality to own the room.",
            "team_context": "For Minnesota, the live question is whether he becomes the greatest Timberwolves playoff figure since Kevin Garnett, or eventually pushes into a higher tier.",
            "comps": ["Kevin Garnett", "Dwyane Wade", "Kobe Bryant", "Michael Jordan", "Jimmy Butler", "Clyde Drexler"]
        },
        "wembanyama": {
            "baseline": 62, "ceiling": 98, "role": "franchise anchor big",
            "resume": "Wembanyama enters as the rare two-way big who can erase shots, stretch a defense, and still carry late-clock creation when the game slows down.",
            "team_context": "For San Antonio, a deep run is measured against Tim Duncan and David Robinson — top-five Spurs playoff impact is the realistic bar if the rim deterrence matches the hype.",
            "comps": ["Tim Duncan", "David Robinson", "Hakeem Olajuwon", "Kareem Abdul-Jabbar", "Anthony Davis", "Patrick Ewing"]
        },
        "castle": {
            "baseline": 52, "ceiling": 88, "role": "lead guard",
            "resume": "Castle is the possession hub: pace, downhill reads, and the willingness to absorb traps so Wembanyama can play in space.",
            "team_context": "A long Spurs run puts Castle in the Tony Parker conversation for trust and Finals-stage creation — top-five guard in franchise playoff memory if the half-court holds.",
            "comps": ["Tony Parker", "Manu Ginobili", "Chris Paul", "Jason Kidd", "Tyrese Maxey", "Derrick White"]
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

def specific_legacy_comparison(player, team, pts, fg, three, plus_minus, rounds, title, score):
    """Ground legacy copy in real names and realistic tiers instead of generic greatness language."""
    n = str(player or "").lower()
    nick = fan_nick(team)
    role = player_resume_profile(player, team).get("role", "playoff contributor")
    efficient = fg >= 0.47 and three >= 0.36
    weak = fg < 0.42 or plus_minus < -2
    huge = pts >= 35
    star_line = pts >= 28

    if "brunson" in n:
        if title and huge and efficient:
            return "If Brunson averages 35+ with strong efficiency and wins the championship, this becomes more than a great playoff run. It puts him near the Frazier/Reed/Ewing tier of defining Knicks figures, with a real top-three Knick argument if the Finals stage is his."
        if title and star_line:
            return "A championship with Brunson as the clear engine would move him from modern Knicks star into the Walt Frazier, Willis Reed, Patrick Ewing conversation for most important playoff figures in franchise history."
        if rounds >= 3 and star_line:
            return "A Finals trip on this line would put Brunson above the Carmelo Anthony and Bernard King style of beloved scoring chapter and closer to a franchise-defining guard tier."
        if weak:
            return "The team success would still matter, but weak efficiency keeps the leap closer to modern Knicks star than Frazier/Reed/Ewing territory."
        return "This strengthens Brunson's place among modern Knicks stars; the jump into top-five franchise talk needs either a title or a truly outrageous scoring run."

    if "towns" in n:
        if title and efficient and plus_minus >= 2:
            return "A title with Towns spacing the floor and punishing mismatches would make him a championship big in New York's story: not Patrick Ewing's role, but a Dave DeBusschere/Chris Bosh/Pau Gasol type second-star chapter with real weight."
        if title:
            return "A ring makes Towns part of Knicks big-man history, but the tier depends on whether he looks like a centerpiece or the elite spacing big who unlocked the offense."
        if rounds >= 3 and efficient:
            return "Conference Finals production with this efficiency pushes Towns toward the franchise's serious big-man conversation, somewhere between spacing star and championship-level second option."
        if weak:
            return "If the efficiency slips, the comparison stays closer to useful playoff big than Willis Reed or Ewing territory, even if the team keeps winning."
        return "This profile builds the case for Towns as the spacing big who changed New York's offense, with Bosh/Gasol-style second-star comparisons more realistic than franchise centerpiece claims."

    if "lebron" in n or n.strip() == "james":
        if title:
            return "Another Lakers title this late would not create a new LeBron tier; it would sharpen the Jordan/Kareem debate and add one more answer against Kobe, Magic, and Tim Duncan longevity arguments."
        if rounds >= 3:
            return "A Finals trip still matters because it adds late-career proof to the all-time resume, but without the ring it is more GOAT-debate evidence than a debate-ender."
        return "For LeBron, early rounds rarely change the all-time table. The legacy movement comes from another Finals run or title-level control."

    if "edwards" in n:
        if title and star_line and efficient:
            return "A title with Edwards as the lead scorer would put him above every Timberwolves playoff figure except the deepest Kevin Garnett arguments, while inviting Wade/Kobe-style young champion comparisons."
        if rounds >= 3 and star_line:
            return "A Finals-level run on this line would make Edwards the greatest Minnesota playoff figure since Garnett and start a real conversation about whether he can pass KG in franchise postseason memory."
        if weak:
            return "The athletic moments would travel, but inefficient scoring keeps the comparison closer to Jimmy Butler-style competitive force than Jordan/Kobe/Wade territory."
        return "This keeps building Edwards as Minnesota's post-KG playoff face; the top-tier leap needs either the Finals stage or a title."

    if "wembanyama" in n or "wemby" in n:
        if title and plus_minus >= 2:
            return "A championship with Wembanyama as the defensive hub would place him in the Tim Duncan tier for San Antonio — top-three Spurs playoff impact with David Robinson as the only other big-man comp at that height."
        if rounds >= 3 and star_line:
            return "A Finals run on this line starts a real top-five Spurs postseason argument: behind Duncan, in the Robinson/Manu conversation for two-way gravity, not just highlight blocks."
        if weak:
            return "The highlights travel, but foul trouble or turnovers keep the read closer to a talented young big than a Duncan/Robinson chapter."
        return "This run builds Wembanyama toward the Duncan standard — the leap into top-three franchise playoff history needs sustained rim deterrence plus a deep series win."

    if "castle" in n:
        if title:
            return "A title with Castle running the offense would make him the best Spurs lead guard since Tony Parker in a championship year — not Manu's creativity, but real Finals trust."
        if rounds >= 3:
            return "A deep run puts Castle in the Tony Parker lane for modern Spurs fans: top-five guard in franchise playoff memory if the creation holds under pressure."
        return "Castle's chapter is still forming — the Parker/Manu guard comps open up only if the playmaking survives playoff traps."

    if "gilgeous" in n or ("shai" in n and "thunder" in team.lower()):
        if title:
            return "A Thunder title would lock Shai into the Kevin Durant tier for OKC playoff history — top-two guard scorer with a real banner, ahead of the Westbrook volume years in impact-per-possession talk."
        if rounds >= 3:
            return "A Finals trip keeps Shai in the top-three Thunder playoff guard conversation with Durant and Payton — the exact rank depends on efficiency in the biggest games."
        return "Shai is already in the Durant/Westbrook neighborhood for OKC; the next step is a Finals stage, not just another scoring month."

    if "mitchell" in n and team == "Cleveland Cavaliers":
        if title:
            return "A Cavaliers title with Mitchell as the engine would put him beside Kyrie Irving in franchise playoff memory — top-three guard scorer with a ring, not just a loud regular season."
        if rounds >= 3:
            return "A deep run on this line moves Mitchell toward the Kyrie/Mark Price guard tier — top-five Cavs playoff scorer if the efficiency survives traps."
        return "Mitchell's Cavs case is still a scoring-star climb; the Irving comp needs a conference-final or Finals stage, not just one hot series."

    if any(x in role for x in ["contributor", "role", "wing", "rotation"]):
        comps = _remove_self_comparisons(player, player_resume_profile(player, team).get("comps", []))
        c0 = comps[0] if comps else "Robert Horry"
        c1 = comps[1] if len(comps) > 1 else "Shane Battier"
        if title and plus_minus >= 2:
            return f"A title would make {player} part of the {nick} rotation lore: more {c0}/{c1} type winning-piece value than superstar ranking talk."
        if rounds >= 3:
            return f"This is the kind of run that makes role players memorable: not top-five franchise territory, but a real {c0}-style 'we do not get there without him' chapter."
        return f"For a role player, the legacy jump is about trusted playoff possessions. Think {c0} or {c1} comparisons in role, not GOAT language."

    if title and score >= 90:
        return f"A championship with this profile pushes {player} into top-five {nick} playoff-run conversation, with the exact rank depending on Finals moments and matchup difficulty."
    if title:
        return f"A ring gives {player} a real franchise-history chapter, but the claim is grounded as a title-run cornerstone rather than automatic greatest-player talk."
    if rounds >= 3:
        return f"A Finals trip makes this a top-10 style {nick} playoff run if the production holds, especially if the biggest games match the box score."
    if weak:
        return "Team success helps the resume, but weak efficiency or impact keeps the individual leap modest."
    return f"This moves {player} into a stronger {nick} playoff conversation without forcing an unrealistic all-time claim."


def _scenario_meaning(player, team, score, _scenario_label, rounds, title):
    prof = player_resume_profile(player, team)
    comps = _remove_self_comparisons(player, prof["comps"])
    tier = player_specific_tier(score, player, team)
    nick = fan_nick(team)
    if title:
        team_hist = specific_legacy_comparison(player, team, 30, 0.47, 0.36, 3, rounds, title, score)
        nba_hist = f"League-wide comparison lane: {', '.join(comps[:3])}. {tier}"
    elif rounds >= 3:
        team_hist = specific_legacy_comparison(player, team, 28, 0.46, 0.35, 2, rounds, title, score)
        nba_hist = (
            f"Around the league, the cleaner comp lane is {comps[1]} and {comps[2]}: not identical players, but the kind of impact tier being tested."
        )
    elif rounds >= 2:
        team_hist = specific_legacy_comparison(player, team, 24, 0.45, 0.35, 1, rounds, title, score)
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


@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=3600)
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
    import portfolio_polish as pp
    import portfolio_demo as pdemo

    pdemo.apply_page_demo(st, "Legacy Tracker")
    _page_perf_tick("legacy_start")
    if _validation_mode_active():
        _render_validation_mode_banner()
    inject_team_brand_css(team_name)
    render_matchup_header(team_name)
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state() if _validation_mode_active() else None)
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
        if not pp.is_capture_mode(st):
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

    render_page_trust_strip("legacy")
    render_fan_product_shell_open()

    player_pool = current_roster_names(team_name, limit=15)
    if pp.is_demo_mode(st) and "Jalen Brunson" in player_pool:
        st.session_state.setdefault("legacy_tracker_player", "Jalen Brunson")
    player = st.selectbox("Choose player", player_pool, key="legacy_tracker_player")
    if _qa_skip_expensive_apis() and not pp.is_demo_mode(st):
        logs = None
        current = {
            "GP": 0,
            "PTS": 18.0,
            "REB": 6.0,
            "AST": 3.0,
            "STL": 0.8,
            "BLK": 0.4,
            "FG_PCT": 0.45,
            "FG3_PCT": 0.34,
            "PLUS_MINUS": 0.0,
        }
        st.caption("QA mode: NBA game-log API skipped — metrics are placeholders for layout testing.")
    else:
        logs = playoff_game_logs_for_player(player, team_name=team_name)
        current = summarize_playoff_logs(logs)

    if (logs is None or logs.empty) and pp.is_demo_mode(st) and player == "Jalen Brunson":
        logs = demo_playoff_gamelog_from_bracket(player, team_name, CURRENT_NBA_SEASON)
        if logs is not None and not logs.empty:
            current = summarize_playoff_logs(logs)
        else:
            current = pdemo.brunson_demo_stats()
        if not pp.is_screenshot_mode(st):
            st.caption("Portfolio demo: showing realistic Brunson playoff snapshot for screenshot-ready legacy comparison.")
    elif logs is None or logs.empty:
        st.warning(
            "NBA API did not return current playoff game logs for this player. "
            "Eliminated postmortems still work from safe averages; active-team sliders default to reasonable baselines."
        )
    else:
        if not pp.is_capture_mode(st):
            st.success(f"Loaded {current['GP']} current playoff games for {player} from NBA API.")
        _sync_ami_legacy_stat_gap(player, team_name, logs)
        with st.expander(f"Full playoff game log ({current['GP']} games)", expanded=False):
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
            prep_logs = _prepare_chrono_playoff_logs(logs)
            render_fan_stat_table(_df_newest_first_for_display(prep_logs)[show_cols], team_name)

    if (logs is not None and not getattr(logs, "empty", True)) and not st.session_state.get("_ami_stat_gap_context"):
        _sync_ami_legacy_stat_gap(player, team_name, logs)

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
        if not _qa_skip_heavy_ui():
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
        hist_line = specific_legacy_comparison(
            player, team_name, pts, fg, three, plus_minus, series_wins_bracket, False, final
        )
        st.write(f"• {hist_line}")
        if elim_lines[7] and elim_lines[7] != hist_line:
            st.caption(elim_lines[7])

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

    if render_fan_section(
        "A · Locked legacy impact",
        "🔒",
        caption=f"Real playoff logs + {series_wins_bracket} series win(s) on the bracket — no simulator sliders.",
        tone="broadcast",
    ):
        render_fan_section_open()
    ceiling = float(player_legacy_ceiling(player, team_name))
    st.markdown(
        _lt_legacy_meters(player, team_name, locked_score, ceiling, series_wins_bracket, int(current.get("GP", 0) or 0)),
        unsafe_allow_html=True,
    )
    title_est = legacy_score_from_inputs(
        pts0, reb0, ast0, stl0, blk0, fg0, th0, pm0, 4, True, player, team_name
    )
    st.markdown(
        _lt_badge_row_html(
            _lt_earned_badges(player, team_name, locked_score, ceiling, series_wins_bracket, title_est, locked_score, pts0)
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_pp_stat_pills_html(current, hot_keys={"PTS", "REB", "AST"}), unsafe_allow_html=True)
    st.markdown(_lt_today_read_card(player, team_name, pts0, fg0, th0, pm0, series_wins_bracket, locked_score), unsafe_allow_html=True)
    render_fan_section_close()

    with st.expander("Franchise bar — who sets the tier", expanded=False):
        st.markdown(_lt_franchise_compare_faces(player, team_name), unsafe_allow_html=True)

    if _qa_skip_heavy_ui() and not pp.is_demo_mode(st):
        st.info("QA mode: legacy simulator sliders and path charts are skipped.")
        return

    if render_fan_section("B · Fan simulator — shape the playoff story", "🎮", caption="Career-mode sliders — if they average X the rest of the run.", tone="default"):
        render_fan_section_open()
    with st.container(border=True):
        if not pp.is_capture_mode(st):
            st.caption(
                "Move the core stat sliders and watch the story change. The model starts from the series already won on the bracket, then asks what this profile would mean if the run keeps going."
            )
        c1, c2, c3 = st.columns(3)
        with c1:
            pts = st.slider("Scoring / points per game", 0.0, 45.0, pts0, 0.5)
            reb = st.slider("Rebounding (RPG)", 0.0, 20.0, reb0, 0.5)
            ast = st.slider("Assists per game / playmaking", 0.0, 15.0, ast0, 0.5)
        with c2:
            stl = st.slider("Steals per game", 0.0, 4.0, stl0, 0.1)
            blk = st.slider("Blocks per game", 0.0, 5.0, blk0, 0.1)
            plus_minus = st.slider("Average plus-minus / overall impact", -20.0, 20.0, pm0, 0.5)
        with c3:
            fg = st.slider("Shooting efficiency", 0.300, 0.700, fg0, 0.005)
            three = st.slider("Three-point shooting efficiency", 0.200, 0.550, th0, 0.005)
    render_fan_section_close()

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
    )
    sim_now = float(path.iloc[0]["Legacy score"]) if not path.empty else locked_score
    title_score = float(path.iloc[-1]["Legacy score"]) if not path.empty else locked_score

    x1, x2, x3, x4 = st.columns(4)
    x1.metric("Story now", sim_now)
    x2.metric("If they win it all", title_score)
    x3.metric("Banner jump", round(title_score - sim_now, 1))
    x4.metric("Personal ceiling", player_legacy_ceiling(player, team_name))

    if render_fan_section("Legacy impact — title & franchise ladder", "🏆", caption="Move sliders above — badges, unlocks, and rank movement update live.", tone="broadcast"):
        render_fan_section_open()
    entry = next(
        (x for x in franchise_history_data(team_name).get("legends", []) if str(x.get("name", "")).lower() == player.lower()),
        {},
    )
    chrono = _prepare_chrono_playoff_logs(logs) if logs is not None and not logs.empty else pd.DataFrame()
    title_pts_proj = _pp_projected_title_pts(entry, chrono, team_name)
    lose_pts_proj = float(entry.get("pts", 0) or 0) + pts * max(2, min(5, _pp_chase_games_left_est(team_name)))
    lose_finals_score = legacy_score_from_inputs(
        pts, reb, ast, stl, blk, fg, three, plus_minus, series_wins_bracket, False, player, team_name
    )
    lose_finals_score = round(lose_finals_score + max(1.0, (title_score - sim_now) * 0.15), 1)
    next_game_score = legacy_score_from_inputs(
        pts, reb, ast, stl, blk, fg, three, plus_minus + 0.8, series_wins_bracket, False, player, team_name
    )
    st.markdown(
        _lt_impact_panel_html(player, team_name, locked_score, ceiling, sim_now, title_score, pts, series_wins_bracket),
        unsafe_allow_html=True,
    )
    st.markdown(
        _lt_achievements_html(
            _lt_achievement_unlocks(player, team_name, sim_now, title_score, series_wins_bracket, pts, locked_score)
        ),
        unsafe_allow_html=True,
    )
    if logs is not None and not logs.empty:
        st.markdown(_lt_career_defining_game_html(player, logs, team_tri), unsafe_allow_html=True)
    st.markdown(_lt_rank_movement_html(player, team_name, entry, title_pts_proj, lose_pts_proj), unsafe_allow_html=True)
    st.markdown(
        _lt_legacy_swing_html(sim_now, title_score, lose_finals_score, next_game_score),
        unsafe_allow_html=True,
    )
    st.markdown(
        _lt_badge_row_html(
            _lt_earned_badges(player, team_name, sim_now, ceiling, series_wins_bracket, title_score, sim_now, pts)
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_lt_goat_ladder_html(player, team_name, sim_now), unsafe_allow_html=True)
    st.markdown(
        _lt_playoff_run_rank_html(player, team_name, series_wins_bracket, int(current.get("GP", 0) or 0), sim_now),
        unsafe_allow_html=True,
    )
    render_fan_section_close()

    with st.expander("Legacy path chart & full ladder", expanded=pp.is_demo_mode(st) or pp.is_screenshot_mode(st)):
        if not _qa_skip_heavy_ui() or pp.is_demo_mode(st):
            st.plotly_chart(
                px.bar(
                    path,
                    x="Playoff picture",
                    y="Legacy score",
                    color="Fan read",
                    title=f"{player}: how the story climbs if the run keeps going",
                ),
                use_container_width=True,
            )
        st.dataframe(path, use_container_width=True, hide_index=True)

    def _scenario_score(wins, title=False):
        return legacy_score_from_inputs(
            pts, reb, ast, stl, blk, fg, three, plus_minus, wins, title, player, team_name
        )

    def _legacy_profile_read(score, wins, title=False):
        return specific_legacy_comparison(
            player,
            team_name,
            pts,
            fg,
            three,
            plus_minus,
            wins,
            title,
            score,
        )

    next_wins = min(4, series_wins_bracket + 1)
    cf_wins = max(next_wins, 3)
    title_wins = 4
    scenarios = [
        ("Win the next round", next_wins, False),
        ("Win the Conference Finals", cf_wins, False),
        ("Win the NBA Finals", title_wins, True),
    ]
    if not pp.skip_heavy_work(st):
        if render_fan_section("What-if scenario cards", "🎯", caption="Next round · Conference Finals · title — legacy score jump.", tone="broadcast"):
            render_fan_section_open()
        scenario_html = []
        for label, wins, title in scenarios:
            sc = _scenario_score(wins, title)
            delta = round(sc - sim_now, 1)
            cls = "lt-scenario--title" if title else ("lt-scenario--finals" if "Finals" in label else "lt-scenario")
            read = _legacy_profile_read(sc, wins, title)
            if len(read) > 160:
                read = read[:157] + "…"
            scenario_html.append(
                f"<div class='lt-scenario {cls}'><div class='lt-scenario-k'>{html.escape(label)}</div>"
                f"<div class='lt-scenario-score'>{sc}</div>"
                f"<div class='lt-scenario-delta'>+{delta} legacy pts vs today</div>"
                f"<div class='lt-scenario-b'>{html.escape(read)}</div></div>"
            )
        st.markdown("<div class='lt-scenario-grid'>" + "".join(scenario_html) + "</div>", unsafe_allow_html=True)
        render_fan_section_close()

    render_fan_product_shell_close()


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
    if _validation_skip_network():
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


_DEMO_PLAYOFF_STAT_BASE = {
    "Jalen Brunson": {"PTS": 28, "REB": 4, "AST": 7, "STL": 1, "BLK": 0, "TOV": 2, "MIN": 37},
    "Karl-Anthony Towns": {"PTS": 22, "REB": 11, "AST": 2, "STL": 0, "BLK": 1, "TOV": 2, "MIN": 34},
    "Mikal Bridges": {"PTS": 14, "REB": 5, "AST": 3, "STL": 1, "BLK": 1, "TOV": 1, "MIN": 36},
    "OG Anunoby": {"PTS": 13, "REB": 5, "AST": 1, "STL": 2, "BLK": 0, "TOV": 1, "MIN": 33},
    "Josh Hart": {"PTS": 11, "REB": 9, "AST": 4, "STL": 1, "BLK": 0, "TOV": 1, "MIN": 32},
    "Victor Wembanyama": {"PTS": 26, "REB": 12, "AST": 3, "STL": 1, "BLK": 3, "TOV": 3, "MIN": 36},
    "Stephon Castle": {"PTS": 18, "REB": 4, "AST": 6, "STL": 1, "BLK": 0, "TOV": 2, "MIN": 34},
    "Devin Vassell": {"PTS": 16, "REB": 4, "AST": 2, "STL": 1, "BLK": 0, "TOV": 1, "MIN": 33},
}


def _parse_team_points_from_score(score_str, team_name):
    """Return (team_pts, opp_pts) from a demo score string like 'Knicks 105, Spurs 95'."""
    if not score_str:
        return None, None
    parts = [p.strip() for p in str(score_str).split(",")]
    team_short = fan_nick(team_name).split()[-1]
    t_pts, o_pts = None, None
    for part in parts:
        m = re.match(r"([A-Za-z .]+)\s+(\d+)", part.strip())
        if not m:
            continue
        label, pts = m.group(1).strip(), int(m.group(2))
        if team_short.lower() in label.lower() or team_name.split()[-1].lower() in label.lower():
            t_pts = pts
        else:
            o_pts = pts
    return t_pts, o_pts


def _demo_stat_line_for_player_game(player_name, team_name, game_idx, wl, team_pts, opp_pts):
    base = dict(_DEMO_PLAYOFF_STAT_BASE.get(player_name) or {"PTS": 10, "REB": 4, "AST": 2, "STL": 1, "BLK": 0, "TOV": 1, "MIN": 22})
    bump = 1 if wl == "W" else -1
    scale = 1.0 + (game_idx % 3) * 0.04 + bump * 0.06
    line = {k: max(0, round(v * scale)) if k != "MIN" else max(12, round(v * scale)) for k, v in base.items()}
    if team_pts and opp_pts:
        margin = team_pts - opp_pts
        line["PLUS_MINUS"] = margin if wl == "W" else -abs(margin)
    else:
        line["PLUS_MINUS"] = 4 if wl == "W" else -4
    fga = max(line["PTS"] // 2, 6)
    line["FGM"] = max(1, round(fga * 0.48))
    line["FGA"] = fga
    line["FG3M"] = max(0, round(line["PTS"] * 0.12))
    line["FG3A"] = max(line["FG3M"], round(line["FG3M"] * 1.6))
    line["FTM"] = max(0, line["PTS"] - line["FGM"] * 2 - line["FG3M"])
    line["FTA"] = max(line["FTM"], line["FTM"] + 2)
    line["FG_PCT"] = round(line["FGM"] / line["FGA"], 3) if line["FGA"] else 0.0
    line["FG3_PCT"] = round(line["FG3M"] / line["FG3A"], 3) if line["FG3A"] else 0.0
    line["FT_PCT"] = round(line["FTM"] / line["FTA"], 3) if line["FTA"] else 0.0
    return line


@st.cache_data(ttl=3600)
def demo_playoff_gamelog_from_bracket(player_name, team_name, season):
    """Synthetic playoff log from merged bracket when NBA API returns empty."""
    if season != CURRENT_NBA_SEASON:
        return pd.DataFrame()
    stt = get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False)
    team_tri = TEAM_ALIASES.get(team_name, "NYK")
    rows = []
    game_num = 0
    for coll in ("first", "second", "cf", "finals"):
        for s in (stt.get(coll) or {}).values():
            if team_name not in (s.get("a"), s.get("b")):
                continue
            opp = s["b"] if team_name == s["a"] else s["a"]
            opp_tri = TEAM_ALIASES.get(opp, "OPP")
            for g in s.get("games") or []:
                game_num += 1
                winner = g.get("Winner")
                wl = "W" if winner == team_name else "L"
                t_pts, o_pts = _parse_team_points_from_score(g.get("Score"), team_name)
                stats = _demo_stat_line_for_player_game(player_name, team_name, game_num, wl, t_pts, o_pts)
                date_raw = g.get("Date") or g.get("GameDate") or ""
                try:
                    game_date = pd.to_datetime(f"{date_raw} 2026", format="mixed").strftime("%b %d, %Y")
                except Exception:
                    game_date = str(date_raw)
                rows.append({
                    "GAME_DATE": game_date,
                    "MATCHUP": f"{team_tri} vs. {opp_tri}" if game_num % 2 else f"{team_tri} @ {opp_tri}",
                    "WL": wl,
                    "MIN": stats["MIN"],
                    "PTS": stats["PTS"],
                    "REB": stats["REB"],
                    "AST": stats["AST"],
                    "STL": stats["STL"],
                    "BLK": stats["BLK"],
                    "TOV": stats["TOV"],
                    "FGM": stats["FGM"],
                    "FGA": stats["FGA"],
                    "FG_PCT": stats["FG_PCT"],
                    "FG3M": stats["FG3M"],
                    "FG3A": stats["FG3A"],
                    "FG3_PCT": stats["FG3_PCT"],
                    "FTM": stats["FTM"],
                    "FTA": stats["FTA"],
                    "FT_PCT": stats["FT_PCT"],
                    "PLUS_MINUS": stats["PLUS_MINUS"],
                    "GAME_ID": g.get("GameID") or f"demo-{game_num}",
                    "TEAM_ABBREVIATION": team_tri,
                })
    return pd.DataFrame(rows)


def fetch_playoff_gamelog(player_name, team_name, season=CURRENT_NBA_SEASON):
    """NBA API log with curated bracket fallback for current-season playoffs."""
    if st.session_state.get("portfolio_demo_mode") or st.session_state.get("portfolio_screenshot_mode"):
        return demo_playoff_gamelog_from_bracket(player_name, team_name, season)
    pid = get_player_id(player_name)
    logs = pd.DataFrame()
    if pid:
        logs = _cached_playoff_gamelog(pid, season)
    if logs is None or logs.empty:
        logs = demo_playoff_gamelog_from_bracket(player_name, team_name, season)
    return logs if logs is not None else pd.DataFrame()


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
        elif "knicks" in team_name.lower() and "towns" in player.lower():
            lines.append(
                f"At **{ppg:.1f} PPG**, Towns is in the Patrick Ewing spacing-big lane for New York — not the same role, but the kind of playoff volume that moves him toward the franchise's top-five postseason scorers if the Finals stage holds."
            )
        elif "spurs" in team_name.lower() and "wembanyama" in player.lower():
            lines.append(
                f"**{ppg:.1f} PPG** with two-way counting stats puts Wembanyama in the Tim Duncan / David Robinson conversation for San Antonio — top-five Spurs playoff impact is the realistic ceiling if rim deterrence matches the scoring."
            )
        elif "spurs" in team_name.lower() and "castle" in player.lower():
            lines.append(
                f"Castle at **{ppg:.1f} PPG** is building a Tony Parker-style trust case — not the same craft yet, but the lead-guard lane for a deep Spurs run."
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


def _pp_stat_pills_html(cur_summary, *, hot_keys=None):
    hot_keys = hot_keys or {"PTS"}
    e = html.escape
    pills = []
    for key, label, fmt in (
        ("PTS", "PPG", "{:.1f}"),
        ("REB", "RPG", "{:.1f}"),
        ("AST", "APG", "{:.1f}"),
        ("TS_PCT", "TS%", "{:.1f}%"),
        ("PLUS_MINUS", "+/-", "{:+.1f}"),
        ("STL", "STL", "{:.1f}"),
        ("BLK", "BLK", "{:.1f}"),
        ("GP", "GP", "{:.0f}"),
    ):
        val = cur_summary.get(key)
        if val is None and key != "GP":
            continue
        if key == "TS_PCT" and val is not None:
            disp = fmt.format(float(val) * 100)
        elif val is not None:
            disp = fmt.format(float(val))
        else:
            disp = "—"
        cls = "pp-stat-pill hot" if key in hot_keys else "pp-stat-pill"
        pills.append(f"<div class='{cls}'><div class='v'>{e(disp)}</div><div class='k'>{e(label)}</div></div>")
    return "<div class='pp-stat-grid'>" + "".join(pills) + "</div>"


def _pp_chase_board_data(player, team_name, df):
    """Structured franchise chase: rank, hero headline, stat gaps with progress."""
    data = franchise_history_data(team_name)
    legends = data.get("legends", [])
    entry = next((x for x in legends if str(x.get("name", "")).lower() == player.lower()), None)
    if not entry:
        return None, [], ""
    sorted_pts = sorted(legends, key=lambda x: -float(x.get("pts", 0) or 0))
    rank = next((i + 1 for i, x in enumerate(sorted_pts) if str(x.get("name", "")).lower() == player.lower()), None)
    stat_specs = [
        ("pts", "Playoff points", "pts", int),
        ("reb", "Playoff rebounds", "REB", int),
        ("g30", "30-point games", "30+ games", int),
        ("g40", "40-point games", "40+ games", int),
        ("ast", "Playoff assists", "AST", int),
    ]
    gaps = []
    for stat, label, short, caster in stat_specs:
        val = float(entry.get(stat, 0) or 0)
        higher = sorted(
            [x for x in legends if str(x.get("name", "")).lower() != player.lower() and float(x.get(stat, 0) or 0) > val],
            key=lambda x: float(x.get(stat, 0) or 0),
        )
        if not higher:
            continue
        target = higher[0]
        target_val = float(target.get(stat, 0) or 0)
        gap = caster(round(target_val - val))
        if gap <= 0:
            continue
        progress = min(0.98, val / max(target_val, 1))
        gaps.append(
            {
                "stat": stat,
                "label": label,
                "short": short,
                "current": caster(val),
                "target_name": target["name"],
                "target_val": caster(target_val),
                "gap": gap,
                "progress": progress,
            }
        )
    hero = ""
    if gaps:
        top = gaps[0]
        hero = f"{top['gap']} {top['short']} to pass {top['target_name']} on the curated board"
    elif rank:
        hero = f"Already at #{rank} on the franchise playoff scoring board — next tier is about Finals-stage proof."
    return rank, gaps, hero


def _sync_ami_legacy_stat_gap(player: str, team_name: str, logs) -> None:
    """Populate _ami_legacy_context / stat_gap for Applied Math from franchise chase board."""
    try:
        from applied_math_context import record_legacy_stat_gap_context

        rank, gaps, hero = _pp_chase_board_data(player, team_name, logs)
        if not gaps:
            return
        primary = gaps[0]
        games_left = _pp_chase_games_left_est(team_name)
        pace = _pp_chase_pace_for_stat(logs, primary["stat"])
        rate = f"{pace:.1f} {primary['short']}/game" if pace else None
        record_legacy_stat_gap_context(
            st.session_state,
            player=player,
            team_name=team_name,
            stat_label=str(primary["label"]),
            stat_key=str(primary["stat"]),
            current_value=primary["current"],
            target_name=str(primary["target_name"]),
            target_value=primary["target_val"],
            gap=primary["gap"],
            games_remaining=int(games_left) if games_left else None,
            rate_needed=rate,
            historical_comparison=str(hero or ""),
            all_gaps=[
                {
                    "stat": g["label"],
                    "current": g["current"],
                    "target": g["target_name"],
                    "target_value": g["target_val"],
                    "gap": g["gap"],
                }
                for g in gaps[:4]
            ],
        )
    except Exception:
        pass


def _pp_chase_pace_for_stat(df, stat):
    if df is None or df.empty:
        return None
    if stat == "pts" and "PTS" in df.columns:
        return float(df["PTS"].mean())
    if stat == "reb" and "REB" in df.columns:
        return float(df["REB"].mean())
    if stat == "ast" and "AST" in df.columns:
        return float(df["AST"].mean())
    if stat == "g30" and "PTS" in df.columns:
        return int((df["PTS"] >= 30).sum()) / max(len(df), 1)
    if stat == "g40" and "PTS" in df.columns:
        return int((df["PTS"] >= 40).sum()) / max(len(df), 1)
    return None


def _pp_chase_games_left_est(team_name):
    mx = get_display_matchup(team_name)
    if mx.get("eliminated"):
        return 0
    s = mx.get("series") or {}
    tw, ow = 0, 0
    if s and team_name in (s.get("a"), s.get("b")):
        tw, ow, _ = _team_series_record(team_name, s)
    return max(0, 7 - int(tw) - int(ow))


def _pp_chase_projected_label(gap, pace, games_left):
    if not pace or pace <= 0 or gap <= 0:
        return "Pace TBD — need more games logged"
    est_games = max(1, int((gap + pace - 0.01) // pace))
    if games_left and est_games <= games_left:
        return f"~{est_games} game(s) at current pace · reachable this series"
    if est_games <= 3:
        return f"~{est_games} game(s) at current pace · next on the board"
    return f"~{est_games} games at current pace · longer chase"


    return f"~{est_games} games at current pace · longer chase"


def _pp_chase_est_games(gap, pace):
    if not pace or pace <= 0 or gap <= 0:
        return None
    return max(1, int((gap + pace - 0.01) // pace))


def _pp_finals_pass_probability(gap, pace, games_left):
    """Fan-model probability of passing target before the run ends (curated estimate)."""
    if not pace or gap <= 0 or games_left <= 0:
        return 0
    est = _pp_chase_est_games(gap, pace) or 99
    if est <= games_left:
        return min(94, int(58 + min(36, (games_left - est + 1) * 9)))
    ratio = games_left / max(est, 1)
    return max(8, min(48, int(ratio * 52)))


def _pp_franchise_pts_rank(team_name, pts_total, player_name=""):
    legends = sorted(franchise_history_data(team_name).get("legends", []), key=lambda x: -float(x.get("pts", 0) or 0))
    for i, leg in enumerate(legends, start=1):
        if str(leg.get("name", "")).lower() == str(player_name).lower():
            return i
    for i, leg in enumerate(legends, start=1):
        if float(pts_total) >= float(leg.get("pts", 0) or 0):
            return i
    return len(legends) + 1


def _pp_projected_title_pts(entry, df, team_name):
    ppg = float(df["PTS"].mean()) if df is not None and not df.empty and "PTS" in df.columns else float(entry.get("ppg", 0) or 0)
    games_left = max(3, min(8, _pp_chase_games_left_est(team_name) + 2))
    return float(entry.get("pts", 0) or 0) + ppg * games_left


def _pp_playoff_stock_label(actual_ppg, board_ppg, pm):
    delta = float(actual_ppg or 0) - float(board_ppg or 0)
    if delta >= 2 or float(pm or 0) >= 3:
        return "up", f"Stock UP · +{delta:.1f} PPG vs board pace"
    if delta <= -2 or float(pm or 0) <= -2:
        return "down", f"Stock DOWN · {delta:.1f} PPG vs board pace"
    return "flat", "Stock STEADY · holding playoff line"


def _pp_team_playoff_pulse_html(team_name, player, df, cur_summary):
    e = html.escape
    data = franchise_history_data(team_name)
    watch = [p for p in data.get("legends", []) if p.get("current_watch")]
    if not watch:
        return ""
    hottest = max(watch, key=lambda x: float(x.get("ppg", 0) or 0))
    riser = max(watch, key=lambda x: float(x.get("g30", 0) or 0) + float(x.get("ppg", 0) or 0) * 0.05)
    entry = next((x for x in watch if str(x.get("name", "")).lower() == player.lower()), None)
    actual_ppg = float(cur_summary.get("PTS") or 0)
    board_ppg = float((entry or {}).get("ppg", actual_ppg) or actual_ppg)
    pm = float(cur_summary.get("PLUS_MINUS") or 0)
    stock_cls, stock_txt = _pp_playoff_stock_label(actual_ppg, board_ppg, pm)
    stock_mod = f" pp-stock-{stock_cls}" if stock_cls in ("up", "down") else ""
    you = " (you)" if str(hottest.get("name", "")).lower() == player.lower() else ""
    riser_you = " (you)" if str(riser.get("name", "")).lower() == player.lower() else ""
    return (
        f"<div class='pp-pulse-strip'>"
        f"<div class='pp-pulse-card'><div class='pp-pulse-k'>Hottest on {e(fan_nick(team_name))}</div>"
        f"<div class='pp-pulse-v'>{e(hottest['name'])}{you}</div>"
        f"<div class='pp-pulse-s'>{hottest.get('ppg', 0):.1f} PPG est. · playoff engine</div></div>"
        f"<div class='pp-pulse-card'><div class='pp-pulse-k'>Biggest riser this run</div>"
        f"<div class='pp-pulse-v'>{e(riser['name'])}{riser_you}</div>"
        f"<div class='pp-pulse-s'>{int(riser.get('g30', 0))}× 30-pt est. · climbing the board</div></div>"
        f"<div class='pp-pulse-card'><div class='pp-pulse-k'>Your playoff stock</div>"
        f"<div class='pp-pulse-v{stock_mod}'>{e(stock_txt.split(' · ')[0])}</div>"
        f"<div class='pp-pulse-s'>{e(stock_txt)}</div></div></div>"
    )


def _pp_chase_journey_panel_html(player, team_name, df, primary, gaps, rank):
    if not primary:
        return ""
    e = html.escape
    gap = primary["gap"]
    pace = _pp_chase_pace_for_stat(df, primary["stat"])
    games_left = _pp_chase_games_left_est(team_name)
    est_games = _pp_chase_est_games(gap, pace)
    gp = int(len(df)) if df is not None and not df.empty else 0
    pass_prob = _pp_finals_pass_probability(gap, pace, games_left)
    pass_date = f"Playoff game ~{gp + est_games}" if est_games and gp else "Need more games logged"
    if games_left and est_games and est_games <= games_left:
        pass_date += f" · Finals window (≤{games_left} games left)"
    entry = next((x for x in franchise_history_data(team_name).get("legends", []) if str(x.get("name", "")).lower() == player.lower()), {})
    title_pts = _pp_projected_title_pts(entry, df, team_name)
    title_rank = _pp_franchise_pts_rank(team_name, title_pts, player)
    rank_now = rank or _pp_franchise_pts_rank(team_name, float(entry.get("pts", 0) or 0), player)
    sorted_gaps = sorted(gaps, key=lambda x: x["gap"])
    milestone = sorted_gaps[0]
    m_prob = _pp_finals_pass_probability(milestone["gap"], _pp_chase_pace_for_stat(df, milestone["stat"]), games_left)
    return (
        f"<div class='pp-journey-panel'>"
        f"<div class='pp-journey-stat'><div class='pp-journey-stat-k'>Projected pass date</div>"
        f"<div class='pp-journey-stat-v'>{e(pass_date)}</div>"
        f"<div class='pp-journey-stat-s'>Pass {e(primary['target_name'].split()[-1])} at current pace</div></div>"
        f"<div class='pp-journey-stat pp-journey-stat--hot'><div class='pp-journey-stat-k'>Finals pass probability</div>"
        f"<div class='pp-journey-stat-v'>{pass_prob}%</div>"
        f"<div class='pp-journey-stat-s'>Fan model · {gap} {e(primary['short'])} left · curated board</div></div>"
        f"<div class='pp-journey-stat pp-journey-stat--up'><div class='pp-journey-stat-k'>If {e(fan_nick(team_name))} win the title</div>"
        f"<div class='pp-journey-stat-v'>#{title_rank} franchise</div>"
        f"<div class='pp-journey-stat-s'>Projected ~{int(title_pts)} PTS · now #{rank_now}</div></div>"
        f"<div class='pp-journey-stat'><div class='pp-journey-stat-k'>Most likely next milestone</div>"
        f"<div class='pp-journey-stat-v'>{milestone['gap']} {e(milestone['short'])}</div>"
        f"<div class='pp-journey-stat-s'>{e(milestone['target_name'])} · {m_prob}% this run</div></div>"
        f"</div>"
    )


def _pp_chase_race_graphic_html(player, team_name, df, primary):
    if not primary:
        return ""
    e = html.escape
    cur_val = primary["current"]
    tgt_val = primary["target_val"]
    tgt_name = primary["target_name"]
    gap = primary["gap"]
    progress = primary["progress"]
    pace = _pp_chase_pace_for_stat(df, primary["stat"])
    games_left = _pp_chase_games_left_est(team_name)
    proj = _pp_chase_projected_label(gap, pace, games_left)
    cur_pct = max(8, min(88, int(progress * 100)))
    tgt_pct = min(96, cur_pct + max(8, int((gap / max(tgt_val, 1)) * 100)))
    hs = e(headshot(player)) if not _validation_skip_network() else ""
    ths = e(headshot(tgt_name)) if not _validation_skip_network() else ""
    hs_tag = f"<img src='{hs}' style='width:28px;height:28px;border-radius:8px;object-fit:cover;display:block;margin:0 auto 2px'/>" if hs else ""
    ths_tag = f"<img src='{ths}' style='width:24px;height:24px;border-radius:8px;object-fit:cover;display:block;margin:0 auto 2px'/>" if ths else ""
    return (
        f"<div class='pp-race-shell'>"
        f"<div class='pp-race-k'>Record race · {e(primary['label'])}</div>"
        f"<div class='pp-race-track'>"
        f"<span class='pp-race-fill' style='width:{cur_pct}%'></span>"
        f"<div class='pp-race-marker pp-race-marker--current' style='left:{cur_pct}%'>"
        f"{hs_tag}<div class='pp-race-marker-dot'></div>"
        f"<div class='pp-race-marker-lbl'>{e(player.split()[-1])}</div>"
        f"<div class='pp-race-marker-val'>{cur_val}</div></div>"
        f"<div class='pp-race-marker pp-race-marker--target' style='left:{tgt_pct}%'>"
        f"{ths_tag}<div class='pp-race-marker-dot'></div>"
        f"<div class='pp-race-marker-lbl'>{e(tgt_name.split()[-1])}</div>"
        f"<div class='pp-race-marker-val'>{tgt_val}</div></div>"
        f"</div>"
        f"<div class='pp-race-meta'>"
        f"<span><b>{gap}</b> {e(primary['short'])} remaining</span>"
        f"<span>{e(proj)}</span>"
        f"<span>Curated {e(fan_nick(team_name))} board</span>"
        f"</div></div>"
    )


def _pp_chase_ladder_html(player, team_name, df, gaps):
    if not gaps:
        return ""
    e = html.escape
    games_left = _pp_chase_games_left_est(team_name)
    sorted_gaps = sorted(gaps, key=lambda x: x["gap"])
    next_rec = sorted_gaps[0]
    easiest = sorted_gaps[0]
    hardest = sorted_gaps[-1]
    next_three = sorted_gaps[:3]
    series_hits = []
    for g in sorted_gaps:
        pace = _pp_chase_pace_for_stat(df, g["stat"])
        if pace and pace > 0 and games_left and g["gap"] <= pace * games_left:
            series_hits.append(g)
    parts = [
        f"<div class='pp-race-ladder-card pp-race-ladder-card--next'>"
        f"<div class='pp-race-ladder-k'>Next record</div>"
        f"<div class='pp-race-ladder-v'>{next_rec['gap']} {e(next_rec['short'])} → pass {e(next_rec['target_name'])}</div>"
        f"<div class='pp-race-ladder-sub'>{e(_pp_chase_projected_label(next_rec['gap'], _pp_chase_pace_for_stat(df, next_rec['stat']), games_left))}</div></div>"
    ]
    three_txt = " · ".join(
        f"{g['gap']} {g['short']} → {g['target_name'].split()[-1]}" for g in next_three
    )
    parts.append(
        f"<div class='pp-race-ladder-card'><div class='pp-race-ladder-k'>Next 3 records</div>"
        f"<div class='pp-race-ladder-v'>{e(three_txt)}</div></div>"
    )
    parts.append(
        f"<div class='pp-race-ladder-card pp-race-ladder-card--easy'>"
        f"<div class='pp-race-ladder-k'>Easiest reach</div>"
        f"<div class='pp-race-ladder-v'>{easiest['gap']} {e(easiest['short'])} → {e(easiest['target_name'])}</div></div>"
    )
    parts.append(
        f"<div class='pp-race-ladder-card pp-race-ladder-card--hard'>"
        f"<div class='pp-race-ladder-k'>Hardest climb</div>"
        f"<div class='pp-race-ladder-v'>{hardest['gap']} {e(hardest['short'])} → {e(hardest['target_name'])}</div></div>"
    )
    if series_hits:
        hit_txt = " · ".join(
            f"{g['gap']} {g['short']} → {g['target_name'].split()[-1]}" for g in series_hits[:4]
        )
        parts.append(
            f"<div class='pp-race-ladder-card pp-race-ladder-card--series'>"
            f"<div class='pp-race-ladder-k'>Within reach this series</div>"
            f"<div class='pp-race-ladder-v'>{e(hit_txt)}</div>"
            f"<div class='pp-race-ladder-sub'>At current pace · up to {games_left} game(s) left on the bracket clock</div></div>"
        )
    else:
        parts.append(
            f"<div class='pp-race-ladder-card pp-race-ladder-card--series'>"
            f"<div class='pp-race-ladder-k'>This series</div>"
            f"<div class='pp-race-ladder-v'>Next tier needs a sustained run — closest is {next_rec['gap']} {e(next_rec['short'])}.</div></div>"
        )
    return "<div class='pp-race-ladder'>" + "".join(parts) + "</div>"


def _pp_progress_bar_html(current, target_val, progress):
    pct = max(6, min(98, int(progress * 100)))
    return (
        f"<div class='pp-progress'><span style='width:{pct}%'></span></div>"
        f"<div class='pp-progress-label'><span>{current}</span><span>{target_val} target</span></div>"
    )


def _pp_franchise_chase_cards_html(player, team_name, df):
    e = html.escape
    rank, gaps, hero = _pp_chase_board_data(player, team_name, df)
    if rank is None and not gaps:
        return ""
    cur_summary = summarize_playoff_logs(df) if df is not None and not df.empty else {}
    parts = []
    if rank:
        parts.append(
            f"<div class='pp-chase-hero'>"
            f"<div class='pp-chase-hero-rank'><div class='num'>#{rank}</div><div class='lbl'>Franchise rank</div></div>"
            f"<div><h3>{e(player)} · what records break next?</h3>"
            f"<p>{e(hero)}</p>"
            f"<span class='pp-chase-pill-hero'>{e(fan_nick(team_name))} franchise chase</span>"
            f"</div></div>"
        )
    primary = gaps[0] if gaps else None
    if primary:
        parts.append(_pp_chase_race_graphic_html(player, team_name, df, primary))
        parts.append(_pp_chase_journey_panel_html(player, team_name, df, primary, gaps, rank))
        parts.append(_pp_chase_ladder_html(player, team_name, df, gaps))
        pulse = _pp_team_playoff_pulse_html(team_name, player, df, cur_summary)
        if pulse:
            parts.append(pulse)
    for g in gaps[1:4]:
        parts.append(
            f"<div class='pp-chase-card pp-chase-card--hero-stat'>"
            f"<div class='pp-chase-k'>{e(g['label'])}</div>"
            f"<div class='pp-chase-gap'>{g['gap']} {e(g['short'])}</div>"
            f"<div class='pp-chase-target'>to pass <b>{e(g['target_name'])}</b> ({g['target_val']})</div>"
            f"{_pp_progress_bar_html(g['current'], g['target_val'], g['progress'])}"
            f"</div>"
        )
    run_g30 = int((df["PTS"] >= 30).sum()) if df is not None and not df.empty and "PTS" in df.columns else 0
    run_g40 = int((df["PTS"] >= 40).sum()) if df is not None and not df.empty and "PTS" in df.columns else 0
    if run_g30 or run_g40:
        rec = []
        if run_g30:
            rec.append(f"{run_g30}× 30-pt")
        if run_g40:
            rec.append(f"{run_g40}× 40-pt")
        parts.append(
            f"<div class='pp-chase-card'><div class='pp-chase-k'>Logged this run</div>"
            f"<div class='pp-chase-b'><b>{' · '.join(rec)}</b> — stacks on curated career totals above.</div></div>"
        )
    return "<div class='pp-chase-grid'>" + "".join(parts) + "</div>" if parts else ""


def _pp_standout_awards_html(df, cur_summary, player, team_name):
    e = html.escape
    awards = []
    g30 = int((df["PTS"] >= 30).sum()) if "PTS" in df.columns and not df.empty else 0
    g40 = int((df["PTS"] >= 40).sum()) if "PTS" in df.columns and not df.empty else 0
    ppg = float(cur_summary.get("PTS") or 0)
    pm = float(cur_summary.get("PLUS_MINUS") or 0)
    if g40:
        awards.append(("40-PT NIGHT", f"{g40} game(s) at 40+ — franchise-memory territory for {e(fan_nick(team_name))} fans."))
    elif g30 >= 2:
        awards.append(("30-PT STREAK", f"{g30} games at 30+ — the kind of volume that moves playoff leaderboards."))
    elif g30 == 1:
        awards.append(("TAKEOVER GAME", "One 30-point eruption already on the log — the signature night fans will replay."))
    if ppg >= 28:
        awards.append(("ENGINE SCORER", f"Averaging {ppg:.1f} PPG — lead-option usage in a deep run."))
    if pm >= 3:
        awards.append(("WINNING MARGIN", f"+{pm:.1f} average plus/minus — the line moves when this player is on the floor."))
    if (cur_summary.get("STL") or 0) + (cur_summary.get("BLK") or 0) >= 2.5:
        awards.append(("TWO-WAY PRESSURE", "Stocks per game are playoff-active — disruption shows up beyond the box score."))
    if not awards:
        awards.append(("RUN FORMING", "The sample is still writing the headline — next two games usually set the chapter tone."))
    return "<div class='pp-award-strip'>" + "".join(
        f"<div class='pp-award'><b>{e(title)}</b>{body}</div>" for title, body in awards[:4]
    ) + "</div>"


def _pp_game_log_cards_html(df, team_tri, *, limit=6):
    e = html.escape
    if df is None or df.empty:
        return ""
    cards = []
    for _, rr in _df_newest_first_for_display(df).head(limit).iterrows():
        wl = str(rr.get("WL", "—")).upper()
        win = wl.startswith("W")
        cls = "pp-game-card win" if win else "pp-game-card loss"
        wl_cls = "pp-game-wl win" if win else "pp-game-wl loss"
        pts = safe_float(rr.get("PTS"))
        pm = safe_float(rr.get("PLUS_MINUS"))
        pm_cls = "pm-pos" if pm >= 0 else "pm-neg"
        opp = _matchup_opponent_tri(rr.get("MATCHUP"), team_tri)
        cards.append(
            f"<div class='{cls}'>"
            f"<div class='pp-game-top'><span>{e(str(rr.get('GAME_DATE','')))}</span>"
            f"<span class='{wl_cls}'>{e(wl)}</span></div>"
            f"<div class='pp-game-pts'>{pts:.0f} <span style='font-size:12px;font-weight:800;color:#64748b'>PTS</span></div>"
            f"<div class='pp-game-opp'>vs {e(opp)}</div>"
            f"<div class='pp-game-chips'>"
            f"<span class='pp-game-chip'>{safe_float(rr.get('REB')):.0f} REB</span>"
            f"<span class='pp-game-chip'>{safe_float(rr.get('AST')):.0f} AST</span>"
            f"<span class='pp-game-chip'>{safe_float(rr.get('MIN')):.0f} MIN</span>"
            f"<span class='pp-game-chip {pm_cls}'>+/- {pm:+.0f}</span>"
            f"</div></div>"
        )
    return "<div class='pp-game-grid'>" + "".join(cards) + "</div>"


def _pp_series_tab_banner_html(label, w, el, sm):
    e = html.escape
    ts = f"{(sm.get('TS_PCT') * 100):.1f}% TS" if sm.get("TS_PCT") is not None else ""
    line = f"{sm.get('PTS', 0):.1f} PPG · {sm.get('REB', 0):.1f} RPG · {sm.get('AST', 0):.1f} APG"
    if ts:
        line += f" · {ts}"
    return (
        f"<div class='pp-series-tab-banner'>{e(label)} · <b>{w}-{el}</b> in log · {e(line)}</div>"
    )


def _pp_journey_strip_html(chunks, rnd_names):
    e = html.escape
    if not chunks:
        return ""
    parts = []
    for idx, (opp_tri, _seg) in enumerate(chunks, start=1):
        opp_name = ALIAS_TO_TEAM.get(opp_tri, opp_tri)
        label = rnd_names[idx - 1] if idx <= len(rnd_names) else f"Round {idx}"
        active = " active" if idx == len(chunks) else ""
        parts.append(f"<span class='pp-journey-step{active}'>{e(label)} vs {e(opp_name)}</span>")
        if idx < len(chunks):
            parts.append("<span class='pp-journey-arrow'>→</span>")
    return "<div class='pp-journey'>" + "".join(parts) + "</div>"


def _pp_compare_cards_html(lines):
    icons = ("🏛️", "⚔️", "📈", "🎯", "⭐")
    cards = []
    for i, line in enumerate(lines[:5]):
        icon = icons[i % len(icons)]
        plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(line))
        cards.append(f"<div class='pp-compare-card'><div class='icon'>{icon}</div>{html.escape(plain)}</div>")
    return "<div class='pp-compare-grid'>" + "".join(cards) + "</div>"


def _pp_premium_hero_html(player, team_name, season, prof, cur_summary, df, hs, logo, hero_badges, mx):
    e = html.escape
    wl_record = ""
    if "WL" in df.columns:
        w = int((df["WL"].astype(str).str.upper().str.startswith("W")).sum())
        l = int((df["WL"].astype(str).str.upper().str.startswith("L")).sum())
        wl_record = f"{w}-{l}"
    _, _, chase_headline = _pp_chase_board_data(player, team_name, df)
    badge_html = "".join(f"<span class='pp-badge team'>{e(b)}</span>" for b in hero_badges[:3])
    if cur_summary.get("PTS", 0) >= 25:
        badge_html += "<span class='pp-badge gold'>Scoring load</span>"
    for lbl, cls in player_fan_badges(cur_summary)[:2]:
        badge_html += f"<span class='fan-badge {cls}' style='font-size:10px;padding:3px 8px'>{e(lbl)}</span>"
    chase_line = f"<div class='pp-chase-pill-hero'>{e(chase_headline)}</div>" if chase_headline else ""
    hs_src = hs or ""
    return f"""<div class='fan-player-card'>
  <img class='hs' src='{e(hs_src)}' alt='' onerror="this.style.opacity='0.35'"/>
  <div>
    <div class='fan-player-name'>{e(player)}</div>
    <div class='fan-player-role'>{e(season)} playoffs · {e(prof.get('role', 'Rotation'))} · {e(fan_nick(team_name))}</div>
    <div class='fan-stat-tiles'>
      <div class='fan-stat-tile'><div class='v'>{cur_summary.get('PTS', 0):.1f}</div><div class='k'>PPG</div></div>
      <div class='fan-stat-tile'><div class='v'>{int(cur_summary.get('GP', 0))}</div><div class='k'>GP</div></div>
      <div class='fan-stat-tile'><div class='v'>{e(wl_record)}</div><div class='k'>W-L</div></div>
    </div>
    {chase_line}
    <div class='fan-badges'>{badge_html}</div>
  </div>
  <img class='logo' src='{e(logo)}' alt=''/>
</div>"""


def _lt_legacy_tier_label(score, ceiling):
    ratio = score / max(ceiling, 1)
    if ratio >= 0.92:
        return "Hall of Fame track"
    if ratio >= 0.78:
        return "Franchise icon tier"
    if ratio >= 0.55:
        return "Deep-run contributor"
    return "Building the case"


def _lt_franchise_rank_pct(player, team_name, locked_score):
    data = franchise_history_data(team_name)
    legends = sorted(data.get("legends", []), key=lambda x: -float(x.get("pts", 0) or 0))
    entry = next((x for x in legends if str(x.get("name", "")).lower() == player.lower()), None)
    if not entry:
        return None, 0
    rank = next((i + 1 for i, x in enumerate(legends) if str(x.get("name", "")).lower() == player.lower()), len(legends))
    pct = max(10, min(92, int(100 - (rank - 1) * max(8, 80 // max(len(legends), 1)))))
    return rank, pct


def _lt_legacy_meters(player, team_name, locked_score, ceiling, series_wins, gp):
    pct = max(8, min(96, int(100 * locked_score / max(ceiling, 1))))
    rank, rank_pct = _lt_franchise_rank_pct(player, team_name, locked_score)
    tier = _lt_legacy_tier_label(locked_score, ceiling)
    rank_txt = f"#{rank}" if rank else "—"
    return f"""<div class='lt-meter-grid'>
  <div class='lt-meter lt-meter--hof'>
    <div class='lt-meter-k'>Legacy score</div>
    <div class='lt-meter-v'>{locked_score:.0f}</div>
    <div class='lt-meter-sub'>Ceiling {ceiling:.0f} · {max(0, ceiling - locked_score):.0f} room</div>
    <div class='lt-meter-bar'><span style='width:{pct}%'></span></div>
    <span class='lt-tier-badge'>{html.escape(tier)}</span>
  </div>
  <div class='lt-meter'>
    <div class='lt-meter-k'>Franchise rank</div>
    <div class='lt-meter-v'>{rank_txt}</div>
    <div class='lt-meter-sub'>Curated playoff board · {html.escape(fan_nick(team_name))}</div>
    <div class='lt-meter-bar'><span style='width:{rank_pct if rank else 40}%'></span></div>
  </div>
  <div class='lt-meter'>
    <div class='lt-meter-k'>Bracket climb</div>
    <div class='lt-meter-v'>{series_wins} / 4</div>
    <div class='lt-meter-sub'>{gp} playoff games logged</div>
    <div class='lt-meter-bar'><span style='width:{max(12, min(88, 20 + series_wins * 18))}%'></span></div>
  </div>
</div>"""


def _lt_franchise_compare_faces(player, team_name):
    """Named franchise touchstones — short bar-setter cards."""
    data = franchise_history_data(team_name)
    entry = next((x for x in data.get("legends", []) if str(x.get("name", "")).lower() == player.lower()), None)
    names = (entry or {}).get("compare_to") or [n for n, _, _ in _franchise_playoff_touchstones(team_name)[:3]]
    cards = []
    e = html.escape
    for nm in names[:3]:
        leg = next((x for x in data.get("legends", []) if x.get("name") == nm), None)
        tier = leg.get("tier", "Franchise bar") if leg else "Reference point"
        img = e(headshot(nm)) if not _validation_skip_network() else ""
        img_tag = f"<img src='{img}' alt=''/>" if img else "<div style='width:52px;height:52px;border-radius:12px;background:#e2e8f0'></div>"
        cards.append(
            f"<div class='lt-scenario lt-scenario--finals'><div class='lt-compare-face'>{img_tag}<div>"
            f"<div style='font-weight:900;color:#0f172a'>{e(nm)}</div>"
            f"<div class='lt-touchstone-rank'>{e(tier)}</div></div></div>"
            f"<div class='lt-scenario-b'>{e((leg or {}).get('accomplishments', 'Sets the tier fans cite in bar talk.')[:120])}</div></div>"
        )
    return "<div class='lt-scenario-grid'>" + "".join(cards) + "</div>"


def _lt_today_read_card(player, team_name, pts, fg, three, pm, wins, score):
    read = specific_legacy_comparison(player, team_name, pts, fg, three, pm, wins, False, score)
    if len(read) > 220:
        read = read[:217] + "…"
    return f"<div class='lt-badge'><b>If playoffs ended today</b><br>{html.escape(read)}</div>"


def _lt_earned_badges(player, team_name, locked_score, ceiling, series_wins, title_score, sim_now, pts):
    badges = []
    ratio = locked_score / max(ceiling, 1)
    rank, _ = _lt_franchise_rank_pct(player, team_name, locked_score)
    banner_jump = float(title_score) - float(sim_now)
    if ratio >= 0.78:
        badges.append(("Franchise Legend", "hof"))
    if series_wins >= 3:
        badges.append(("Deep Run Hero", "gold"))
    if banner_jump >= 12:
        badges.append(("Championship Hero", "title"))
    if pts >= 27 and banner_jump >= 8:
        badges.append(("Finals MVP Track", "title"))
    if rank and rank <= 5:
        badges.append(("Top 5 Franchise Player", "gold"))
    if ratio >= 0.55 and series_wins >= 2:
        badges.append(("Greatest Modern Run", "hof"))
    if not badges:
        badges.append(("Building the Case", ""))
    return badges


def _lt_badge_row_html(badges):
    e = html.escape
    chips = []
    for label, cls in badges[:6]:
        mod = f" lt-badge-chip--{cls}" if cls else ""
        chips.append(f"<span class='lt-badge-chip{mod}'>{e(label)}</span>")
    return "<div class='lt-badge-row'>" + "".join(chips) + "</div>"


def _lt_impact_panel_html(player, team_name, locked_score, ceiling, sim_now, title_score, pts, series_wins):
    e = html.escape
    room = max(1.0, ceiling - sim_now)
    title_pct = max(0, min(99, int(100 * (title_score - sim_now) / room)))
    mvp_boost = round(max(0, (title_score - sim_now) * 0.35 + max(0, pts - 26) * 0.8), 1)
    rank, rank_pct = _lt_franchise_rank_pct(player, team_name, locked_score)
    rank_txt = f"#{rank}" if rank else "—"
    return (
        f"<div class='lt-impact-grid'>"
        f"<div class='lt-impact-card lt-impact-card--title'>"
        f"<div class='lt-meter-k'>Title probability impact</div>"
        f"<div class='lt-impact-v'>{title_pct}%</div>"
        f"<div class='lt-impact-sub'>Of remaining ceiling unlocked if they win it all (+{round(title_score - sim_now, 1)} legacy pts)</div></div>"
        f"<div class='lt-impact-card lt-impact-card--title'>"
        f"<div class='lt-meter-k'>Finals MVP impact</div>"
        f"<div class='lt-impact-v'>+{mvp_boost}</div>"
        f"<div class='lt-impact-sub'>Fan-model bump if {e(player.split()[-1])} authors the signature line at {pts:.1f} PPG</div></div>"
        f"<div class='lt-impact-card'>"
        f"<div class='lt-meter-k'>All-time franchise rank</div>"
        f"<div class='lt-impact-v'>{rank_txt}</div>"
        f"<div class='lt-impact-sub'>Curated playoff board · {rank_pct}% tier meter · {series_wins} series win(s) logged</div></div>"
        f"</div>"
    )


def _lt_goat_ladder_html(player, team_name, locked_score):
    e = html.escape
    data = franchise_history_data(team_name)
    legends = sorted(data.get("legends", []), key=lambda x: -float(x.get("pts", 0) or 0))
    rows = []
    for i, leg in enumerate(legends[:6], start=1):
        est_score = min(100, 42 + float(leg.get("pts", 0) or 0) / 55 + int(leg.get("titles", 0) or 0) * 8)
        is_you = str(leg.get("name", "")).lower() == player.lower()
        cls = " lt-goat-row--you" if is_you else ""
        marker = " ← you" if is_you else ""
        rows.append(
            f"<div class='lt-goat-row{cls}'>"
            f"<div class='lt-goat-rank'>{i}</div>"
            f"<div><div class='lt-goat-name'>{e(leg['name'])}{marker}</div>"
            f"<div class='lt-goat-tier'>{e(leg.get('tier', 'Legend'))}</div></div>"
            f"<div class='lt-goat-score'>{est_score:.0f}</div></div>"
        )
    return "<div class='lt-goat-ladder'>" + "".join(rows) + "</div>"


def _lt_playoff_run_rank_html(player, team_name, series_wins, gp, locked_score):
    e = html.escape
    nick = fan_nick(team_name)
    runs = (FRANCHISE_GREAT_RUNS.get(team_name) or [])[:5]
    rank_hint = "top-tier" if series_wins >= 3 else ("rising" if series_wins >= 2 else "building")
    run_line = runs[0] if runs else f"{nick} playoff memory"
    return (
        f"<div class='lt-run-rank'>"
        f"<b>Playoff run ranking:</b> this {gp}-game sample reads as a <b>{rank_hint}</b> {nick} chapter "
        f"(legacy {locked_score:.0f}). Bar-setter: <i>{e(run_line)}</i> — move the sliders to see where this run lands."
        f"</div>"
    )


FRANCHISE_GREAT_RUNS = {
    "New York Knicks": [
        "1970 Willis Reed Game 7 — emotional championship standard",
        "1999 Allan Houston run — last pre-Brunson deep Finals memory",
        "2025 Brunson era — first Finals trip in a generation",
    ],
    "San Antonio Spurs": [
        "1999 David Robinson + Tim Duncan first title",
        "2003–2007 Duncan dynasty peak",
        "2014 beautiful basketball title",
        "2025 Wembanyama Finals debut",
    ],
}

FRANCHISE_GREAT_GAMES = {
    "New York Knicks": [
        ("1970 Finals G7", "Reed's limp-out — Garden mythology"),
        ("1999 ECF G6", "Allan Houston finger roll sends New York to the Finals"),
        (FINALS_GAME1_CANONICAL_SCORE, "2025 Finals G1 — Brunson steals San Antonio home court"),
    ],
    "San Antonio Spurs": [
        ("2014 Finals G5", "Beautiful ball movement closes the Heat era"),
        ("2007 Finals G4", "Tony Parker Finals MVP seal"),
        (FINALS_GAME1_CANONICAL_SCORE, "2025 Finals G1 — Wembanyama's debut stage (Spurs trail 0–1)"),
    ],
}


def _lt_franchise_rank_from_pts(team_name, pts_total):
    legends = sorted(franchise_history_data(team_name).get("legends", []), key=lambda x: -float(x.get("pts", 0) or 0))
    for i, leg in enumerate(legends, start=1):
        if float(pts_total) >= float(leg.get("pts", 0) or 0):
            return i
    return len(legends) + 1


def _lt_rank_spots_delta(team_name, pts_now, pts_after):
    r0 = _lt_franchise_rank_from_pts(team_name, pts_now)
    r1 = _lt_franchise_rank_from_pts(team_name, pts_after)
    return max(0, r0 - r1)


def _lt_achievement_unlocks(player, team_name, sim_now, title_score, series_wins, pts, locked_score):
    ceiling = float(player_legacy_ceiling(player, team_name))
    ach = [
        ("Deep Run Badge", series_wins >= 2, "Two series wins logged on the bracket"),
        ("Finals Stage", series_wins >= 3, "Reached the championship round in the fan model"),
        ("30-PT Author", pts >= 28, "Scoring line looks like a lead-option Finals profile"),
        ("Banner Path", title_score - sim_now >= 15, "Title run unlocks a major legacy jump"),
        ("Franchise Icon", sim_now / max(ceiling, 1) >= 0.78, "Crossed franchise icon tier on the meter"),
        ("Ceiling Hunter", sim_now >= locked_score + 8, "Simulator pushed the story past today's lock"),
    ]
    return ach


def _lt_achievements_html(achievements):
    e = html.escape
    cards = []
    for label, unlocked, hint in achievements:
        cls = "lt-achieve lt-achieve--unlocked" if unlocked else "lt-achieve lt-achieve--locked"
        status = "UNLOCKED" if unlocked else "LOCKED"
        cards.append(
            f"<div class='{cls}'><div class='lt-achieve-k'>{status}</div>"
            f"<div class='lt-achieve-v'>{e(label)}</div>"
            f"<div class='lt-achieve-s'>{e(hint)}</div></div>"
        )
    return "<div class='lt-achieve-grid'>" + "".join(cards) + "</div>"


def _lt_career_defining_game_html(player, logs, team_tri):
    e = html.escape
    if logs is None or logs.empty or "PTS" not in logs.columns:
        return ""
    df = logs.copy()
    if "_impact" not in df.columns:
        df["_impact"] = df.apply(_game_impact_score, axis=1)
    row = df.loc[int(df["_impact"].idxmax())]
    pts = safe_float(row.get("PTS"))
    opp = _matchup_opponent_tri(row.get("MATCHUP"), team_tri)
    return (
        f"<div class='lt-defining'><b>Career-defining game alert:</b> "
        f"{e(str(row.get('GAME_DATE', '')))} · {pts:.0f} PTS vs {e(opp)} "
        f"(+/- {safe_float(row.get('PLUS_MINUS')):+.0f}) — the night fans will cite if this run becomes legend.</div>"
    )


def _lt_rank_movement_html(player, team_name, entry, title_pts, lose_pts):
    e = html.escape
    now_pts = float(entry.get("pts", 0) or 0)
    r_now = _lt_franchise_rank_from_pts(team_name, now_pts)
    r_win = _lt_franchise_rank_from_pts(team_name, title_pts)
    r_lose = _lt_franchise_rank_from_pts(team_name, lose_pts)
    win_spots = max(0, r_now - r_win)
    lose_spots = max(0, r_now - r_lose)
    return (
        f"<div class='lt-rank-move'><div class='lt-meter-k'>Franchise ranking movement (curated PTS board)</div>"
        f"<div class='lt-rank-track'>"
        f"<div class='lt-rank-node'><div class='lt-goat-rank'>#{r_now}</div><div class='lt-goat-tier'>Today</div></div>"
        f"<div class='lt-rank-arrow'>→</div>"
        f"<div class='lt-rank-node lt-rank-node--win'><div class='lt-goat-rank'>#{r_win}</div>"
        f"<div class='lt-goat-tier'>Win title · +{win_spots} spot(s)</div></div>"
        f"</div>"
        f"<div class='lt-impact-sub' style='margin-top:8px'>Lose Finals: #{r_lose} · "
        f"{'no rank movement' if lose_spots == 0 else f'+{lose_spots} spot(s)'} · fan-model estimate</div></div>"
    )


def _lt_legacy_swing_html(sim_now, title_score, lose_finals_score, next_game_score):
    swings = [
        ("Win the NBA Finals", title_score - sim_now, title_score, "gain"),
        ("Lose the Finals", lose_finals_score - sim_now, lose_finals_score, "flat" if abs(lose_finals_score - sim_now) < 8 else "loss"),
        ("Win next game only", next_game_score - sim_now, next_game_score, "gain" if next_game_score > sim_now else "flat"),
    ]
    cards = []
    for label, delta, score, kind in swings:
        cls = f"lt-swing lt-swing--{kind}"
        sign = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
        cards.append(
            f"<div class='{cls}'><div class='lt-scenario-k'>{html.escape(label)}</div>"
            f"<div class='lt-swing-v'>{sign} legacy</div>"
            f"<div class='lt-swing-s'>Story lands at {score:.1f} on the fan model</div></div>"
        )
    return "<div class='lt-swing-grid'>" + "".join(cards) + "</div>"


def render_player_playoff_story_hub(team_name, profile):
    """Narrative + impact hub for a player's postseason (stats + story + legacy texture)."""
    _page_perf_tick("player_tracker_start")
    if _validation_mode_active():
        _render_validation_mode_banner()
    inject_team_brand_css(team_name)
    st.markdown('<div class="fan-product-shell pp-wrap">', unsafe_allow_html=True)
    render_fan_page_hero(
        team_name,
        "Player Playoff Tracker",
        f"Follow {fan_nick(team_name)} players through the bracket — milestones, game logs, and franchise chase boards.",
        "PLAYOFF JOURNEY",
    )
    render_page_trust_strip("player_tracker")

    plist = current_roster_names(team_name)
    c_sel1, c_sel2 = st.columns([1.1, 1])
    with c_sel1:
        player = st.selectbox("Player", plist, key="pp_hub_player")
    with c_sel2:
        season = st.selectbox("Season", [CURRENT_NBA_SEASON, "2024-25", "2023-24"], index=0, key="pp_hub_season")

    pid = get_player_id(player)
    logs_raw = fetch_playoff_gamelog(player, team_name, season)
    if logs_raw.empty:
        if not pid:
            st.warning(
                f"Could not resolve NBA player id for **{player}** and no curated playoff log is available."
            )
        else:
            st.warning(
                f"No playoff game log returned for **{player}** in **{season}**. "
                "Try another season or verify the player reached the postseason."
            )
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
    _sync_ami_legacy_stat_gap(player, team_name, df)

    prev_season = _prior_nba_season_label(season)
    prev_summary = None

    prof = player_resume_profile(player, team_name)
    role_lower = str(prof.get("role", "")).lower()
    reg_avg = None

    mx = get_display_matchup(team_name)
    seed = int(profile.get("seed") or 8)
    rnd = mx.get("round") or "Playoffs"
    status = "Eliminated" if mx["eliminated"] else "Active"
    opp = mx.get("opponent")

    # --- Hero ---
    logo = TEAM_LOGOS.get(team_name, "")
    hs = headshot(player)
    hero_badges = []
    if status == "Active":
        hero_badges.append(f"{rnd}")
    else:
        hero_badges.append("Postseason complete / eliminated context")
    hero_badges.append(f"Seed {seed}")
    if opp:
        hero_badges.append(f"Board: vs {fan_nick(opp)}")

    st.markdown(
        _pp_premium_hero_html(player, team_name, season, prof, cur_summary, df, hs, logo, hero_badges, mx),
        unsafe_allow_html=True,
    )
    if render_fan_section(
        "Franchise chase board",
        "🏛️",
        caption="Rank, points/rebounds to next legend, and records within reach — the first thing fans should see.",
        tone="broadcast",
    ):
        render_fan_section_open()
    chase_html = _pp_franchise_chase_cards_html(player, team_name, df)
    if chase_html:
        st.markdown(chase_html, unsafe_allow_html=True)
    else:
        st.caption("Franchise chase cards appear when this player is on the curated history board.")
    render_fan_section_close()

    st.markdown(_pp_standout_awards_html(df, cur_summary, player, team_name), unsafe_allow_html=True)

    if render_fan_section("Playoff averages", "🏀", caption="Core counting stats for this postseason sample.", tone="default"):
        render_fan_section_open()
    st.markdown(_pp_stat_pills_html(cur_summary), unsafe_allow_html=True)
    render_fan_section_close()

    with st.expander("Efficiency splits & highs/lows", expanded=False):
        c_a, c_b = st.columns(2)
        with c_a:
            fg = cur_summary.get("FG_PCT") or 0
            tp = cur_summary.get("FG3_PCT") or 0
            ft = cur_summary.get("FT_PCT") or 0
            tov = cur_summary.get("TOV") or 0
            st.markdown(
                f"FG **{fg * 100:.1f}%** · 3P **{tp * 100:.1f}%** · FT **{ft * 100:.1f}%** · TOV **{tov:.1f}** per game."
            )
        with c_b:
            if "PTS" in df.columns:
                imax = int(df["PTS"].idxmax())
                imin = int(df["PTS"].idxmin())
                rmax = df.loc[imax]
                rmin = df.loc[imin]
                st.markdown(
                    f"**High:** {safe_float(rmax.get('PTS')):.0f} PTS vs {_matchup_opponent_tri(rmax.get('MATCHUP'), team_tri)} · "
                    f"**Low:** {safe_float(rmin.get('PTS')):.0f} PTS"
                )

    # --- 2 · Series ---
    chunks = _series_chunks_playoff_order(df, team_tri)
    rnd_names = ["First Round", "Second Round", "Conference Finals", "NBA Finals"]
    if chunks:
        st.markdown(_pp_journey_strip_html(chunks, rnd_names), unsafe_allow_html=True)
    with st.expander("Round-by-round series tabs & game logs", expanded=False):
        if not chunks:
            st.info("Could not split series from matchups.")
        else:
            tab_labels = []
            for idx, (opp_tri, seg) in enumerate(chunks, start=1):
                opp_name = ALIAS_TO_TEAM.get(opp_tri, opp_tri)
                round_label = rnd_names[idx - 1] if idx <= len(rnd_names) else f"Round {idx}"
                tab_labels.append(f"{round_label} vs {opp_name}")
            tabs = st.tabs(tab_labels)
            for tab, ((opp_tri, seg), label) in zip(tabs, zip(chunks, tab_labels)):
                with tab:
                    w = int((seg["WL"].astype(str).str.upper().str.startswith("W")).sum()) if "WL" in seg.columns else 0
                    el = int((seg["WL"].astype(str).str.upper().str.startswith("L")).sum()) if "WL" in seg.columns else 0
                    sm = summarize_playoff_logs(seg)
                    sm["TS_PCT"] = _true_shooting_pct(seg)
                    st.markdown(_pp_series_tab_banner_html(label, w, el, sm), unsafe_allow_html=True)
                    st.markdown(_pp_stat_pills_html(sm, hot_keys={"PTS", "PLUS_MINUS"}), unsafe_allow_html=True)
                    st.markdown(_pp_game_log_cards_html(seg, team_tri, limit=8), unsafe_allow_html=True)

    with st.expander("Pressure meters & legacy texture", expanded=False):
        pressure_base = min(100, 28 + max(0, 10 - seed) * 4 + _round_narrative_weight(rnd) + min(22, int(cur_summary.get("PTS", 0)) * 2))
        rep = min(100, int(prof.get("baseline", 50) + min(18, abs(safe_float(cur_summary.get("PLUS_MINUS"))) * 2)))
        stakes = min(100, 35 + _round_narrative_weight(rnd) + (12 if status == "Active" else 0))
        elim_pressure = min(100, 22 + _bounce_back_games(df) * 14 + (10 if any(str(x).upper().startswith("L") for x in df.get("WL", [])) else 0))
        nar = _pp_hub_pressure_legacy_narratives(
            team_name, player, seed, rnd, status, opp,
            pressure_base, rep, stakes, elim_pressure, cur_summary, df, prof,
        )

        def meter_bar(label, val, klass, body_text):
            v = max(0, min(100, int(val)))
            safe_cls = klass if klass in ("", "gold", "ember") else ""
            return (
                f"<div class='pp-card'><h4>{html.escape(label)}</h4>"
                f"<div class='pp-meter'><span class='{safe_cls}' style='width:{v}%'></span></div>"
                f"<p class='pp-muted'>{html.escape(body_text[:140])}</p></div>"
            )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(meter_bar("Pressure level", pressure_base, "", nar["pressure"]), unsafe_allow_html=True)
            st.markdown(meter_bar("Reputation swing", rep, "gold", nar["reputation"]), unsafe_allow_html=True)
        with c2:
            st.markdown(meter_bar("Stakes", stakes, "ember", nar["stakes"]), unsafe_allow_html=True)
            st.markdown(meter_bar("Elimination pressure", elim_pressure, "gold", nar["elimination"]), unsafe_allow_html=True)

    with st.expander("Franchise comparison cards (named bar talk)", expanded=False):
        if prev_season and not _qa_skip_expensive_apis() and st.checkbox(
            f"Compare to {prev_season} postseason (loads extra API call)",
            value=False,
            key=f"pp_prev_yoy_{player}",
        ):
            prev_df = _prepare_chrono_playoff_logs(_cached_playoff_gamelog(pid, prev_season))
            if not prev_df.empty:
                prev_summary = summarize_playoff_logs(prev_df)
                prev_summary["TS_PCT"] = _true_shooting_pct(prev_df)
                prev_summary["GP"] = int(len(prev_df))
        comp_lines = _historical_comparison_lines(player, team_name, cur_summary, prev_summary, prof, role_lower)
        st.markdown(_pp_compare_cards_html(comp_lines), unsafe_allow_html=True)

    with st.expander("Takeover games & bonus storylines", expanded=False):
        if reg_avg is None:
            reg_avg = season_averages(player)
        df_c = df.copy()
        df_c["_impact"] = df_c.apply(_game_impact_score, axis=1)
        df_c = df_c.sort_values("_impact", ascending=False)
        if not df_c.empty:
            for _, rr in df_c.head(3).iterrows():
                st.caption(
                    f"{rr.get('GAME_DATE','')}: {safe_float(rr.get('PTS')):.0f} PTS, "
                    f"+/- {safe_float(rr.get('PLUS_MINUS')):+.0f} vs {_matchup_opponent_tri(rr.get('MATCHUP'), team_tri)}"
                )
        for s in _narrative_storylines(player, team_name, cur_summary, reg_avg, prev_summary, prof)[:3]:
            st.markdown(s)

    if render_fan_section("Progression & game log", "📈", caption="Game log cards load first — charts on demand.", tone="default"):
        render_fan_section_open()
    if _qa_skip_heavy_ui():
        st.caption("QA mode: Plotly progression charts skipped — game log cards above remain for factual checks.")
        show_cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS"] if c in df.columns]
        with st.expander("Full playoff game log (table)", expanded=False):
            df_tbl = _df_newest_first_for_display(df)
            st.dataframe(df_tbl[show_cols], use_container_width=True)
        render_fan_section_close()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown(_pp_game_log_cards_html(df, team_tri, limit=8), unsafe_allow_html=True)
    with st.expander("Load progression charts (Plotly)", expanded=False):
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
    with st.expander("Full playoff game log (table)", expanded=False):
        df_tbl = _df_newest_first_for_display(df)
        st.dataframe(df_tbl[show_cols], use_container_width=True)

    render_fan_section_close()
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
    top = df.sort_values("MIN_FLOAT", ascending=False).head(5)
    on_court = top["Player"].dropna().astype(str).tolist()
    ordered = build_position_lineup(team_name, candidate_names=on_court)
    by_name = {row["Player"]: row for _, row in top.iterrows()}
    rows = []
    for p in ordered:
        if p in by_name:
            rows.append(by_name[p].to_dict())
        elif p != "TBD":
            rows.append({"Team": alias, "Player": p, "MIN": "0:00", "PTS": 0, "REB": 0, "AST": 0, "STL": 0, "BLK": 0, "PF": 0, "FGM": 0, "FGA": 0})
    return pd.DataFrame(rows) if rows else top

def player_temp(r):
    fga = safe_float(r.get("FGA")); fgm = safe_float(r.get("FGM")); pts = safe_float(r.get("PTS"))
    pct = fgm/fga if fga else 0
    if pts >= 18 and pct >= .50: return "🔥"
    if fga >= 8 and pct <= .30: return "❄️"
    return ""

def win_prob(margin, period, is_home):
    w = {1:1.2, 2:1.8, 3:2.8, 4:4.5}.get(max(1,min(safe_int(period,1),4)), 4.5)
    return int(max(1, min(99, round(50 + margin*w + (2.5 if is_home else 0)))))


def live_win_probability(team_name, opp_name, margin, period, is_home, box_df=None):
    """Broadcast model: score/time first, then small home/seed/momentum nudges."""
    base = win_prob(margin, period, is_home)
    team_seed = safe_int((TEAM_PROFILES.get(team_name) or {}).get("seed"), 8)
    opp_seed = safe_int((TEAM_PROFILES.get(opp_name) or {}).get("seed"), 8)
    seed_adj = max(-4, min(4, (opp_seed - team_seed) * 0.8))
    momentum_adj = 0
    try:
        if box_df is not None and not box_df.empty:
            alias = TEAM_ALIASES.get(team_name, "")
            opp_alias = TEAM_ALIASES.get(opp_name, "")
            plus = pd.to_numeric(box_df[box_df["Team"] == alias]["+/-"], errors="coerce").fillna(0).max()
            opp_plus = pd.to_numeric(box_df[box_df["Team"] == opp_alias]["+/-"], errors="coerce").fillna(0).max()
            momentum_adj = max(-3, min(3, (float(plus) - float(opp_plus)) / 8.0))
    except Exception:
        momentum_adj = 0
    return int(max(1, min(99, round(base + seed_adj + momentum_adj))))

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
        rows.append({"Player":player,"Made":made,"x":x,"y":y,"Period":a.get("period",""),"Clock":a.get("clock",""),"Description":desc})
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

def _top_plays_from_actions(actions, team_name, limit=5):
    alias = TEAM_ALIASES[team_name]
    rows = []
    for a in actions or []:
        if (a.get("teamTricode") or "") != alias:
            continue
        desc = a.get("description", "") or ""
        if not is_top_play(desc):
            continue
        rows.append(
            {
                "Period": a.get("period", ""),
                "Clock": a.get("clock", ""),
                "Top Play": desc,
                "Why it mattered": explain_play(desc, team_name),
            }
        )
    if rows:
        return pd.DataFrame(rows[-limit:])
    return pd.DataFrame()


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

@st.cache_data(ttl=86400)
def matchup_advantages(team, opp):
    t_starters = estimated_starters_from_api(team)
    o_starters = estimated_starters_from_api(opp)
    positions = list(LINEUP_SLOTS)
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


def _lineup_stat_num(stats, key):
    try:
        return float(stats.get(key, 0))
    except Exception:
        return 0.0


def _lineup_player_html(player, team, pos, side_label=""):
    esc = html.escape
    stats = season_averages(player)
    logo = TEAM_LOGOS.get(team, "")
    stat_line = (
        f"<span>{_lineup_stat_num(stats, 'PTS'):.1f} PTS</span>"
        f"<span>{_lineup_stat_num(stats, 'REB'):.1f} REB</span>"
        f"<span>{_lineup_stat_num(stats, 'AST'):.1f} AST</span>"
    )
    return f"""
<div class="ml-player ml-player--{esc(side_label)}">
  <div class="ml-player-top">
    <img class="ml-headshot" src="{esc(headshot(player))}" alt=""/>
    <img class="ml-mini-logo" src="{esc(logo)}" alt=""/>
  </div>
  <div class="ml-pos">{esc(pos)} · {esc(fan_nick(team))}</div>
  <div class="ml-name">{esc(player)}</div>
  <div class="ml-stats">{stat_line}</div>
</div>
"""


@st.cache_data(ttl=86400)
def _lineup_badge_for_matchup(team_player, opp_player, pos, team, opp):
    t = season_averages(team_player)
    o = season_averages(opp_player)
    t_pts, o_pts = _lineup_stat_num(t, "PTS"), _lineup_stat_num(o, "PTS")
    t_reb, o_reb = _lineup_stat_num(t, "REB"), _lineup_stat_num(o, "REB")
    t_ast, o_ast = _lineup_stat_num(t, "AST"), _lineup_stat_num(o, "AST")
    t_def, o_def = _lineup_stat_num(t, "STL") + _lineup_stat_num(t, "BLK"), _lineup_stat_num(o, "STL") + _lineup_stat_num(o, "BLK")
    star_names = [
        "Brunson", "Maxey", "LeBron", "Davis", "Edwards", "Towns", "Embiid", "Mitchell",
        "Shai", "Gilgeous", "Wembanyama", "Castle", "Cunningham", "Tatum", "Brown", "Anunoby", "Hart",
    ]
    pair = f"{team_player} {opp_player}"
    if any(x in pair for x in star_names):
        label = "Star Matchup"
    elif pos in ("PF", "C") and abs(t_reb - o_reb) >= 1.5:
        label = "Rebounding Edge"
    elif abs(t_pts - o_pts) >= 4:
        label = "Scoring Edge"
    elif t_def + o_def >= 2.4:
        label = "Defensive Battle"
    elif pos in ("PG", "SG") and abs(t_ast - o_ast) >= 1.5:
        label = "Playmaking Edge"
    else:
        label = "X-Factor"

    t_score = t_pts * 1.0 + t_reb * 0.55 + t_ast * 0.65 + t_def * 1.8
    o_score = o_pts * 1.0 + o_reb * 0.55 + o_ast * 0.65 + o_def * 1.8
    if abs(t_score - o_score) < 2.5:
        adv = "Toss-up"
        adv_team = "Close"
    elif t_score > o_score:
        adv = f"{fan_nick(team)} edge"
        adv_team = team
    else:
        adv = f"{fan_nick(opp)} edge"
        adv_team = opp

    if label == "Star Matchup":
        why = f"{team_player} and {opp_player} can both bend the first defensive coverage. The pace of this spot shapes the whole preview."
    elif label == "Rebounding Edge":
        why = "This is where extra possessions can swing the middle quarters, especially if misses turn into kick-out threes."
    elif label == "Scoring Edge":
        why = "The cleanest shot creator at this position can force help and open the next pass."
    elif label == "Defensive Battle":
        why = "Stops, deflections, and rim contests matter as much as the box-score line here."
    elif label == "Playmaking Edge":
        why = "Ball pressure and decision-making decide whether the offense gets organized or has to freelance late."
    else:
        why = "This spot may not lead the broadcast, but one hot stretch or foul-trouble twist can change the matchup math."
    return label, adv, adv_team, why


def _inject_matchup_lineups_css(team, opp):
    t = get_team_theme(team)
    o = get_team_theme(opp)
    st.markdown(
        f"""
<style>
.ml-shell {{
  --ml-primary:{t['primary']}; --ml-secondary:{t['secondary']}; --ml-opp:{o['primary']}; --ml-opp2:{o['secondary']};
  --ml-bg0:{t['bg0']}; --ml-bg1:{t['bg1']}; --ml-border:{t['border']};
}}
.ml-hero {{
  border-radius:24px; padding:22px; margin:8px 0 18px;
  background:
    radial-gradient(circle at 15% 15%, {t['accent_soft']}, transparent 30%),
    radial-gradient(circle at 85% 20%, {o['accent_soft']}, transparent 30%),
    linear-gradient(135deg, {t['bg0']}, {t['bg1']});
  border:1px solid {t['border']}; color:#f8fafc; box-shadow:0 18px 42px rgba(0,0,0,.24);
}}
.ml-hero-row {{ display:flex; align-items:center; justify-content:space-between; gap:18px; flex-wrap:wrap; }}
.ml-hero-team {{ display:flex; align-items:center; gap:12px; min-width:210px; }}
.ml-hero-logo {{ width:82px; height:82px; object-fit:contain; filter:drop-shadow(0 10px 18px rgba(0,0,0,.45)); }}
.ml-hero-name {{ font-size:1.45rem; font-weight:950; line-height:1.05; }}
.ml-hero-meta {{ font-size:12px; color:#cbd5e1; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
.ml-vs {{ font-size:2.2rem; font-weight:950; color:{t['accent']}; text-shadow:0 0 18px rgba(255,255,255,.18); }}
.ml-headline {{ margin-top:16px; font-size:1.25rem; font-weight:900; line-height:1.25; }}
.ml-sub {{ margin-top:6px; font-size:13px; color:#cbd5e1; max-width:900px; }}
.ml-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(310px,1fr)); gap:14px; margin:8px 0 20px; }}
.ml-card {{
  border-radius:20px; padding:14px; background:linear-gradient(180deg,#ffffff,#f8fafc);
  border:1px solid rgba(148,163,184,.35); box-shadow:0 10px 28px rgba(15,23,42,.10);
}}
.ml-card--team-edge {{ box-shadow:0 0 0 2px {t['primary']}33, 0 12px 28px rgba(15,23,42,.12); }}
.ml-card--opp-edge {{ box-shadow:0 0 0 2px {o['primary']}33, 0 12px 28px rgba(15,23,42,.12); }}
.ml-bench-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:8px 0 18px; }}
.ml-bench-col {{ border-radius:18px; padding:12px; background:rgba(15,23,42,.92); border:1px solid rgba(148,163,184,.28); }}
.ml-bench-col h4 {{ margin:0 0 10px; font-size:13px; color:{t['accent']}; letter-spacing:.08em; text-transform:uppercase; }}
.ml-bench-card {{ border-radius:14px; padding:10px; margin-bottom:8px; background:#0f172a; border:1px solid rgba(148,163,184,.22); display:flex; gap:10px; align-items:center; }}
.ml-xf-badge {{ background:linear-gradient(135deg,#f59e0b,#ea580c); color:#0f172a; }}
.ml-card-top {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px; }}
.ml-position {{ font-size:11px; font-weight:950; letter-spacing:.12em; text-transform:uppercase; color:#64748b; }}
.ml-badge {{ padding:5px 10px; border-radius:999px; font-size:10px; font-weight:950; letter-spacing:.06em; text-transform:uppercase; color:#0f172a; background:{t['accent']}; }}
.ml-match {{ display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:10px; }}
.ml-player {{ border-radius:16px; padding:10px; min-height:188px; background:#fff; border:1px solid rgba(148,163,184,.25); }}
.ml-player--team {{ border-top:5px solid {t['primary']}; }}
.ml-player--opp {{ border-top:5px solid {o['primary']}; }}
.ml-player-top {{ position:relative; min-height:82px; }}
.ml-headshot {{ width:100px; height:78px; object-fit:cover; object-position:top center; border-radius:14px; background:#e2e8f0; border:2px solid rgba(255,255,255,.85); }}
.ml-broadcast-strip {{
  display:flex; flex-wrap:wrap; align-items:center; gap:10px 16px; margin:0 0 14px; padding:10px 14px;
  border-radius:14px; background:rgba(15,23,42,.92); border:1px solid rgba(148,163,184,.35); color:#e2e8f0;
}}
.ml-broadcast-strip span {{ font-size:10px; font-weight:950; letter-spacing:.14em; text-transform:uppercase; color:{t['accent']}; }}
.ml-broadcast-tag {{ padding:4px 10px; border-radius:999px; font-size:10px; font-weight:900; background:{t['accent_soft']}; color:#0f172a; }}
.ml-mini-logo {{ position:absolute; right:0; top:0; width:34px; height:34px; object-fit:contain; filter:drop-shadow(0 3px 8px rgba(0,0,0,.25)); }}
.ml-pos {{ font-size:10px; font-weight:900; color:#64748b; text-transform:uppercase; letter-spacing:.08em; margin-top:6px; }}
.ml-name {{ font-size:16px; line-height:1.05; font-weight:950; color:#0f172a; margin-top:3px; }}
.ml-stats {{ display:flex; flex-wrap:wrap; gap:5px; margin-top:8px; }}
.ml-stats span {{ font-size:10px; font-weight:900; color:#334155; background:#f1f5f9; border-radius:999px; padding:4px 7px; }}
.ml-card-vs {{ font-size:12px; font-weight:950; color:#64748b; }}
.ml-adv {{ margin-top:12px; border-radius:14px; padding:10px 12px; background:linear-gradient(90deg,{t['accent_soft']},rgba(148,163,184,.10)); border:1px solid rgba(148,163,184,.25); }}
.ml-adv-title {{ font-size:12px; font-weight:950; color:#0f172a; }}
.ml-adv-body {{ font-size:12px; line-height:1.45; color:#475569; margin-top:3px; }}
.ml-tile-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:8px 0 18px; }}
.ml-tile {{ border-radius:16px; padding:13px; background:rgba(15,23,42,.86); color:#f8fafc; border:1px solid rgba(148,163,184,.28); }}
.ml-tile-k {{ font-size:10px; font-weight:950; color:{t['accent']}; letter-spacing:.12em; text-transform:uppercase; }}
.ml-tile-v {{ font-size:14px; font-weight:900; margin-top:5px; line-height:1.25; }}
.ml-tile-s {{ font-size:12px; color:#cbd5e1; line-height:1.35; margin-top:5px; }}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=86400)
def _matchup_edge_tiles(team, opp):
    tp = TEAM_PROFILES.get(team, {})
    op = TEAM_PROFILES.get(opp, {})
    t_strengths = tp.get("strengths") or []
    o_strengths = op.get("strengths") or []
    t_concerns = tp.get("concerns") or []
    o_concerns = op.get("concerns") or []
    return [
        ("Shot creation", t_strengths[0] if t_strengths else "Half-court creation", o_concerns[0] if o_concerns else "Can the defense keep the ball out of the paint?"),
        ("Wing defense", t_strengths[2] if len(t_strengths) > 2 else "Perimeter resistance", o_strengths[2] if len(o_strengths) > 2 else "Who wins the matchup-hunting minutes?"),
        ("Rebounding", t_strengths[3] if len(t_strengths) > 3 else "Extra possessions", "The glass decides whether good defensive trips actually end."),
        ("Rim pressure", o_strengths[0] if o_strengths else "Paint touches", t_concerns[0] if t_concerns else "Foul trouble can flip the rotation."),
        ("Shooting", t_strengths[1] if len(t_strengths) > 1 else "Spacing", "The cleaner catch-and-shoot team gets the easiest runs."),
    ]


def _lineup_xfactor_candidates(team_name, opp):
    """Curated rotation names most likely to swing a playoff game."""
    out = []
    for tm in (team_name, opp):
        curated = CURRENT_PLAYOFF_LINEUPS.get(tm) or {}
        for slot in ("SG", "SF", "PF"):
            name = curated.get(slot)
            if name and not _is_outdated_playoff_player(name, tm):
                out.append((tm, name, slot))
        for name in (curated.get("bench") or [])[:2]:
            if name and not _is_outdated_playoff_player(name, tm):
                out.append((tm, name, "bench"))
    return out[:6]


def _lineups_use_curated_board(team_name):
    """Use curated playoff rotation when a board exists (Finals accuracy + fewer API calls)."""
    return bool(CURRENT_PLAYOFF_LINEUPS.get(team_name))


def _curated_bench_list(team_name, limit=5):
    return list((CURRENT_PLAYOFF_LINEUPS.get(team_name) or {}).get("bench") or [])[:limit]


def render_matchup_lineups_page(team_name, profile):
    _page_perf_tick("lineups_start")
    if _validation_mode_active():
        _render_validation_mode_banner()
    inject_team_brand_css(team_name)
    mx = get_display_matchup(team_name)
    render_fan_page_hero(
        team_name,
        "Matchup Lineups",
        f"{mx['round_short']} · {mx['team_nick']} vs {mx['opponent_nick']} — position-by-position playoff boards.",
        "MATCHUP BOARD",
    )
    render_page_trust_strip("lineups")
    render_fan_product_shell_open()
    render_playoff_matchup_ribbon(team_name)
    hctx = resolve_home_matchup_context_fast(team_name)
    possible = hctx.get("opponents") or []
    default_opp = hctx.get("opponent") or hctx.get("opponent_display") or profile.get("current_opponent")
    opponents = [op for op in possible if op in TEAM_PROFILES] or ([default_opp] if default_opp in TEAM_PROFILES else [])
    if not opponents:
        st.info("The next opponent is not settled enough for lineup cards yet. The matchup board will fill in once the bracket names a team.")
        return
    opp = opponents[0]
    if len(opponents) > 1:
        opp = st.selectbox("Preview possible opponent", opponents, format_func=lambda x: f"{team_name} vs {x}")

    _inject_matchup_lineups_css(team_name, opp)
    t_logo = TEAM_LOGOS.get(team_name, "")
    o_logo = TEAM_LOGOS.get(opp, "")
    series_obj = hctx.get("series") or _build_local_series_shell(team_name)
    round_label = hctx.get("round_label") or (series_obj or {}).get("round") or profile.get("round", "Playoffs")
    status = (hctx.get("ctx") or {}).get("status_text") or series_status_text(team_name, series_obj)
    if _lineups_use_curated_board(team_name):
        t_starters = _curated_starters_list(team_name)
        o_starters = _curated_starters_list(opp)
    else:
        t_starters = estimated_starters_from_api(team_name)
        o_starters = estimated_starters_from_api(opp)
    lead_t = t_starters[0] if t_starters and t_starters[0] != "TBD" else fan_nick(team_name)
    lead_o = o_starters[0] if o_starters and o_starters[0] != "TBD" else fan_nick(opp)
    headline = f"{lead_t} vs {lead_o} sets the first pressure point"
    if len(t_starters) > 1 and len(o_starters) > 1:
        headline = f"{lead_t} vs {lead_o} controls the pace, but the wing and big battles decide the margins"

    st.markdown(
        f"""
<div class="ml-shell">
  <div class="ml-broadcast-strip">
    <span>Broadcast matchup graphic</span>
    <span class="ml-broadcast-tag">PG–C boards</span>
    <span class="ml-broadcast-tag">Headshots + team colors</span>
    <span class="ml-broadcast-tag">Curated playoff rotation</span>
  </div>
  <div class="ml-hero">
    <div class="ml-hero-row">
      <div class="ml-hero-team">
        <img class="ml-hero-logo" src="{html.escape(t_logo)}" alt=""/>
        <div><div class="ml-hero-meta">Selected team</div><div class="ml-hero-name">{html.escape(team_name)}</div></div>
      </div>
      <div class="ml-vs">VS</div>
      <div class="ml-hero-team" style="justify-content:flex-end;text-align:right">
        <div><div class="ml-hero-meta">{html.escape(str(round_label))}</div><div class="ml-hero-name">{html.escape(opp)}</div></div>
        <img class="ml-hero-logo" src="{html.escape(o_logo)}" alt=""/>
      </div>
    </div>
    <div class="ml-headline">{html.escape(headline)}</div>
    <div class="ml-sub">{html.escape(status)}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if globals().get("SHOW_PERF_DEBUG", False):
        t_meta = get_lineup_resolution_info(team_name)
        o_meta = get_lineup_resolution_info(opp)
        with st.expander("Debug: lineup resolution", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{team_name}** — `{t_meta['source']}`")
                st.write("Resolved:", " · ".join(f"{s}: {p}" for s, p in zip(LINEUP_SLOTS, t_meta["resolved_lineup"])))
                if t_meta["rejected"]:
                    st.write("Rejected/outdated:", ", ".join(t_meta["rejected"]))
                st.dataframe(lineup_position_debug_df(team_name), use_container_width=True, hide_index=True)
            with c2:
                st.markdown(f"**{opp}** — `{o_meta['source']}`")
                st.write("Resolved:", " · ".join(f"{s}: {p}" for s, p in zip(LINEUP_SLOTS, o_meta["resolved_lineup"])))
                if o_meta["rejected"]:
                    st.write("Rejected/outdated:", ", ".join(o_meta["rejected"]))
                st.dataframe(lineup_position_debug_df(opp), use_container_width=True, hide_index=True)
            st.caption("Active rotation = players eligible for matchup cards. Outdated names are excluded even if the API still lists them.")

    if render_fan_section("Starting lineup matchups", "📋", caption="Estimated playoff preview boards by position.", tone="default"):
        render_fan_section_open()
    positions = list(LINEUP_SLOTS)
    cards = []
    swing = None
    swing_gap = -1
    for i, pos in enumerate(positions):
        tp = t_starters[i] if i < len(t_starters) else "TBD"
        op = o_starters[i] if i < len(o_starters) else "TBD"
        if "TBD" in (tp, op):
            badge, adv, adv_team, why = "Rotation Watch", "TBD", "Close", "Official lineup data is still incomplete for this spot."
        else:
            badge, adv, adv_team, why = _lineup_badge_for_matchup(tp, op, pos, team_name, opp)
            t_pts = _lineup_stat_num(season_averages(tp), "PTS")
            o_pts = _lineup_stat_num(season_averages(op), "PTS")
            gap = abs(t_pts - o_pts)
            if gap > swing_gap:
                swing_gap = gap
                swing = (pos, tp, op, badge, why)
        card_mod = "ml-card"
        if adv_team == team_name:
            card_mod += " ml-card--team-edge"
        elif adv_team == opp:
            card_mod += " ml-card--opp-edge"
        cards.append(
            f"""
<div class="{card_mod}">
  <div class="ml-card-top"><div class="ml-position">{html.escape(pos)} vs {html.escape(pos)}</div><div class="ml-badge">{html.escape(badge)}</div></div>
  <div class="ml-match">
    {_lineup_player_html(tp, team_name, pos, "team")}
    <div class="ml-card-vs">vs</div>
    {_lineup_player_html(op, opp, pos, "opp")}
  </div>
  <div class="ml-adv"><div class="ml-adv-title">{html.escape(adv)}</div><div class="ml-adv-body">{html.escape(why)}</div></div>
</div>
"""
        )
    st.markdown('<div class="ml-shell"><div class="ml-grid">' + "".join(cards) + "</div></div>", unsafe_allow_html=True)

    if swing:
        pos, tp, op, badge, why = swing
        render_fan_section_header("Biggest matchup swing", "⚔️", caption="The position duel most likely to move the series.", tone="broadcast")
        st.markdown(
            f"""
<div class="ml-shell"><div class="ml-tile">
  <div class="ml-tile-k">{html.escape(pos)} · {html.escape(badge)}</div>
  <div class="ml-tile-v">{html.escape(tp)} vs {html.escape(op)}</div>
  <div class="ml-tile-s">{html.escape(why)}</div>
</div></div>
""",
            unsafe_allow_html=True,
        )

    with st.expander("Bench battle & tactical edges", expanded=False):
        render_fan_section_header("Bench battle", "🪑", caption="Second-unit minutes that can flip a quarter.", tone="default")
        bench_cols_html = []
        for tm in (team_name, opp):
            cards_b = []
            for p in (_curated_bench_list(tm, 4) if _lineups_use_curated_board(tm) else estimated_bench_from_api(tm)[:4]):
                stats = season_averages(p)
                badge = "Bench Spark" if _lineup_stat_num(stats, "PTS") >= 8 else "Rotation Trust"
                cards_b.append(
                    f"""<div class="ml-bench-card">
  <img class="ml-headshot" style="width:58px;height:48px" src="{html.escape(headshot(p))}" alt=""/>
  <div><div style="font-size:10px;font-weight:900;color:#94a3b8">{html.escape(badge)}</div>
  <div style="font-size:14px;font-weight:900;color:#f8fafc">{html.escape(p)}</div>
  <div style="font-size:11px;color:#cbd5e1">{_lineup_stat_num(stats, 'PTS'):.1f} PTS · {_lineup_stat_num(stats, 'REB'):.1f} REB · {_lineup_stat_num(stats, 'AST'):.1f} AST</div></div>
</div>"""
                )
            bench_cols_html.append(
                f"""<div class="ml-bench-col"><h4>{html.escape(fan_nick(tm))} bench</h4>{"".join(cards_b) or "<div style='color:#94a3b8;font-size:12px'>Rotation TBD</div>"}</div>"""
            )
        st.markdown('<div class="ml-shell"><div class="ml-bench-grid">' + "".join(bench_cols_html) + "</div></div>", unsafe_allow_html=True)

        render_fan_section_header("Key tactical edges", "📐", caption="Schematic advantages beyond the box score.", tone="default")
        edge_html = []
        for label, value, sub in _matchup_edge_tiles(team_name, opp):
            edge_html.append(
                f"""<div class="ml-tile"><div class="ml-tile-k">{html.escape(label)}</div><div class="ml-tile-v">{html.escape(str(value))}</div><div class="ml-tile-s">{html.escape(str(sub))}</div></div>"""
            )
        st.markdown('<div class="ml-shell"><div class="ml-tile-grid">' + "".join(edge_html) + "</div></div>", unsafe_allow_html=True)

        render_fan_section_header("X-factor players", "✨", caption="Rotation names who can swing a possession battle.", tone="default")
        x_html = []
        for tm, p, slot in _lineup_xfactor_candidates(team_name, opp):
            stats = season_averages(p)
            x_html.append(
                f"""<div class="ml-tile"><div class="ml-tile-k ml-xf-badge">X-Factor · {html.escape(slot)} · {html.escape(fan_nick(tm))}</div>
            <div style="display:flex;gap:10px;align-items:center;margin-top:6px">
            <img class="ml-headshot" style="width:58px;height:48px" src="{html.escape(headshot(p))}" alt=""/>
            <div><div class="ml-tile-v">{html.escape(p)}</div>
            <div class="ml-tile-s">{_lineup_stat_num(stats, 'PTS'):.1f} PTS · {_lineup_stat_num(stats, 'REB'):.1f} REB — swing role if the starters trade blows.</div></div></div></div>"""
            )
        st.markdown('<div class="ml-shell"><div class="ml-tile-grid">' + "".join(x_html) + "</div></div>", unsafe_allow_html=True)

    render_fan_section_header("Who has the edge?", "🏁", caption="Position-by-position lean and toss-ups.", tone="broadcast")
    adv_df = matchup_advantages(team_name, opp)
    team_edges = int((adv_df["Advantage"] == team_name).sum()) if not adv_df.empty else 0
    opp_edges = int((adv_df["Advantage"] == opp).sum()) if not adv_df.empty else 0
    close_edges = max(0, len(adv_df) - team_edges - opp_edges)
    verdict = f"{fan_nick(team_name)} have the cleaner position-by-position edge." if team_edges > opp_edges else (
        f"{fan_nick(opp)} show more obvious individual edges on paper." if opp_edges > team_edges else "This reads like a possession-margin matchup: shot quality, fouls, and the bench minutes decide it."
    )
    st.markdown(
        f"""
<div class="ml-shell"><div class="ml-tile-grid">
  <div class="ml-tile"><div class="ml-tile-k">{html.escape(fan_nick(team_name))} edges</div><div class="ml-tile-v">{team_edges}</div><div class="ml-tile-s">Projected starter spots with a clear lean.</div></div>
  <div class="ml-tile"><div class="ml-tile-k">{html.escape(fan_nick(opp))} edges</div><div class="ml-tile-v">{opp_edges}</div><div class="ml-tile-s">Projected starter spots with a clear lean.</div></div>
  <div class="ml-tile"><div class="ml-tile-k">Toss-ups</div><div class="ml-tile-v">{close_edges}</div><div class="ml-tile-s">Where coaching, health, and form can flip the night.</div></div>
</div>
<div class="ml-tile" style="margin-top:10px"><div class="ml-tile-k">Matchup verdict</div><div class="ml-tile-v">{html.escape(verdict)}</div><div class="ml-tile-s">The board is visual by design: use the cards for the story, then open the raw rotation table only if you want the data underneath.</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("Raw rotation data", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            rotation = fetch_team_rotation_by_minutes(team_name)
            if not rotation.empty:
                st.dataframe(rotation.drop(columns=[c for c in ["MIN_SORT"] if c in rotation.columns]).head(12), use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame({"Player": current_roster_names(team_name, limit=12)}), use_container_width=True, hide_index=True)
        with c2:
            rotation = fetch_team_rotation_by_minutes(opp)
            if not rotation.empty:
                st.dataframe(rotation.drop(columns=[c for c in ["MIN_SORT"] if c in rotation.columns]).head(12), use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame({"Player": current_roster_names(opp, limit=12)}), use_container_width=True, hide_index=True)

    render_fan_section_close()
    render_fan_product_shell_close()


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
    mx = get_display_matchup(team_name)
    prof = TEAM_PROFILES[team_name]
    s = mx.get("series")
    if not s:
        _, s = series_for_team(team_name)
    games = []
    opp = mx.get("opponent") or None
    round_label = mx.get("round") or prof.get("round", "Playoffs")
    if s:
        opp = s["b"] if team_name == s["a"] else s["a"]
        games = list(s.get("games") or [])
        round_label = s.get("round", round_label)
        tw = int(s.get("a_wins", 0)) if team_name == s["a"] else int(s.get("b_wins", 0))
        ow = int(s.get("b_wins", 0)) if team_name == s["a"] else int(s.get("a_wins", 0))
        if _team_lost_confirmed_series(team_name, s):
            return s, opp, games, tw, ow, f"{round_label} (series complete)", "eliminated"
        return s, opp, games, tw, ow, round_label, "current"
    if _is_home_eliminated(team_name):
        fr = _build_local_series_shell(team_name)
        if fr and fr.get("round") == "First Round":
            opp = fr["b"] if team_name == fr["a"] else fr["a"]
            games = list(fr.get("games") or [])
            tw = int(fr.get("a_wins", 0)) if team_name == fr["a"] else int(fr.get("b_wins", 0))
            ow = int(fr.get("b_wins", 0)) if team_name == fr["a"] else int(fr.get("a_wins", 0))
            return fr, opp, games, tw, ow, "First round (series complete)", "eliminated"
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
        if _series_has_confirmed_winner(s2) and s2.get("winner") == team_name:
            ctx = next_round_context_for_team(team_name)
            if ctx and ctx.get("advanced"):
                return s2, ctx.get("opponents", [None])[0] or ctx.get("opponent_text"), games, tw, ow, ctx.get("round_label", "Next Round"), "advanced"
        if _team_lost_confirmed_series(team_name, s2):
            return s2, opp, games, tw, ow, f"{round_label} (series complete)", "eliminated"
        return s2, opp, games, tw, ow, round_label, "current"
    opp = prof.get("current_opponent") or prof.get("first_round_opponent")
    return None, opp, [], 0, 0, round_label, "waiting"


@st.cache_data(ttl=900)
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
        adj = f"You've been hit hard more than once — the next response has to start with **getting back, loading up early, and taking away runway** from **{o_star.split()[-1] if o_star else O}**."
    elif blowouts_for >= 2:
        adj = f"You've shown you can **break this open** — expect {O} to slow the night down, kill transition, and make every bucket feel like a grind."
    elif close_games >= max(2, len(margins) - 1) and margins:
        adj = f"**{close_games}** nail-biters (avg ~{avg_abs} pts) — the swing is simple: cleaner timeout plays, sharper sideline sets, and winning the first six minutes after halftime."
    else:
        adj = _intel_variant(
            seed + "adj",
            [
                f"The rotation battle is really **rebounding vs switching** — whoever forces the first uncomfortable lineup usually owns the middle quarters.",
                f"Watch how you guard **{o_star.split()[-1] if o_star else O}** when the shot goes cold; that is where panic or poise shows up.",
                f"{O} wants to pull **{t_star.split()[-1] if t_star else 'your star'}** into help decisions without giving up free corners.",
            ],
        )

    # --- 5. Defensive matchup problems ---
    def_body = _intel_variant(
        seed + "def",
        [
            f"You have to solve how {O} gets to **{o_strengths[0] if o_strengths else 'its best action'}** — the help is getting stretched, and the next pass is becoming a clean three.",
            f"The stress point is **{o_star}** attacking **{t_concerns[0] if t_concerns else 'your point of attack'}** — help opens **ORBs and dump-offs** that hurt on the second side.",
            f"{O}'s **{o_strengths[1] if len(o_strengths) > 1 else (o_strengths[0] if o_strengths else 'size')}** forces an ugly choice: live with a mismatch or send help and risk the glass.",
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
            f"Out of timeouts, watch how {O} guards **{t_star.split()[-1] if t_star else 'your star'}** — the counter is movement before the ball even gets there.",
            f"The bench question is brutal: shorten the rotation for trust, or keep fresh legs and risk the scoreboard wobble.",
            f"The series-long bet is help versus corners — coaches will give up one thing to steal the thing that hurts most.",
        ],
    )

    # Star pressure (woven into pressure card)
    star_pressure = _intel_variant(
        seed + "sp",
        [
            f"**{t_star}** is where the offense goes when the building gets tight; {O} is trying to turn those touches into tough twos.",
            f"**{t_star}** carrying more of the offense is the emotional ride — heroic when it hits, exhausting when the clock gets late.",
            f"The narrative pressure you feel on **{t_star}** is real because **{o_star}** is the clearest counter-star.",
        ],
    )

    sections = [
        ("1", "Where you can win this series", "🏆", adv_body, "good", None),
        ("2", "What should worry you", "⚠️", concern_body, "warn", None),
        ("3", "X-factor player", "✨", x_body, "neutral", None),
        ("4", "The move that changes the series", "🧭", adj, "neutral", None),
        ("5", "Where the defense feels stress", "🛡️", def_body, "warn", None),
        ("6", "Where the momentum sits", "📈", mom_txt, mom_class, "momentum"),
        ("7", "Who owns the tense minutes", "⏱️", clutch, "neutral", None),
        ("8", "Pressure check", "🎯", f"**{p_label}** ({pressure}/100). {p_note} {star_pressure}", "neutral", None),
        ("9", "Coaches' next move", "♟️", chess, "neutral", None),
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
    if _validation_mode_active():
        _render_validation_mode_banner()
    prof = TEAM_PROFILES.get(team_name) or {}
    mx = get_display_matchup(team_name, _get_validation_playoff_state() if _validation_mode_active() else None)
    render_fan_page_hero(
        team_name,
        "Matchup Intelligence",
        f"Fast preview first: {mx['team_nick']} vs {mx['opponent_nick']}. Load the full scouting board when you want the deeper read.",
        "SCOUTING BOARD",
    )
    render_page_trust_strip("matchup_intel")
    render_playoff_matchup_ribbon(team_name)
    if _qa_skip_heavy_ui():
        st.info(
            "QA mode: full scouting board, injury intel, and historical matchup analytics are skipped. "
            "Turn off QA mode in the sidebar to load the full board."
        )
        return
    axes = team_dashboard_lens(team_name).get("identity_axes") or prof.get("strengths", [])
    cols = st.columns(3)
    for col, label in zip(cols, list(axes)[:3]):
        with col:
            st.markdown(
                f"<div class='mi-card mi-neutral'><div class='mi-num'>FAST READ</div><div class='mi-title'>{html.escape(str(label))}</div><div class='mi-body'>Cached team context. Full injury and matchup intelligence loads only on request.</div></div>",
                unsafe_allow_html=True,
            )
    load_key = f"load_matchup_intel_{team_name}"
    if not st.session_state.get(load_key):
        render_loading_skeleton(2, "Scouting board on deck")
        if st.button("Load full matchup intelligence", key=load_key + "_btn"):
            st.session_state[load_key] = True
            st.rerun()
        return

    meta, payload = build_matchup_intelligence_sections(team_name)
    if meta is None:
        st.warning(payload)
        return
    try:
        from applied_math_context import record_matchup_intelligence_context

        opp_name = str(meta.get("opp") or prof.get("current_opponent") or "")
        inj = _intel_injury_signal(team_name, opp_name)
        inj_txt = ""
        if inj.get("headline"):
            h = inj["headline"]
            inj_txt = f"{h[1]} ({h[2]})" if len(h) >= 3 else str(h)
        summaries = []
        for _num, _title, _icon, body, _tone, _kind in payload[:4]:
            text = re.sub(r"\*\*", "", str(body))[:220]
            if text:
                summaries.append(text)
        t_star = (prof.get("starters") or [""])[0]
        o_prof = TEAM_PROFILES.get(opp_name) or {}
        o_star = (o_prof.get("starters") or [""])[0]
        pst = st.session_state.get("playoff_team_state") or {}
        sp = pst.get("series_win_probability") or pst.get("series_prob")
        series_prob = f"{float(sp):.0f}%" if sp is not None else None
        record_matchup_intelligence_context(
            st.session_state,
            team_name=team_name,
            opponent=opp_name,
            meta=meta,
            section_summaries=summaries,
            injury_summary=inj_txt,
            key_players=[p for p in (t_star, o_star) if p],
            series_probability=series_prob,
        )
    except Exception:
        pass
    render_mi_intelligence_hero(team_name, meta)
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
        render_fan_section_header(title, icon, caption=f"Scouting slice {num}", tone="default")
        render_fan_section_open()
        st.markdown(
            f"<div class='mi-card {cls}'><div class='mi-num'>SECTION {num}</div>"
            f"<div class='mi-title'>{safe_title}{mom_pill}</div><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )
        render_fan_section_close()


# ==========================================================
# Rendering helpers
# ==========================================================
def render_matchup_header(team_name, first_round=False):
    p=TEAM_PROFILES[team_name]
    if first_round:
        opp=p["first_round_opponent"]
        round_label="Previous Rounds / First Round Review"
    else:
        pst = get_team_playoff_status(team_name)
        hctx = resolve_home_matchup_context_fast(team_name)
        if pst.get("status") == "eliminated":
            opp = pst.get("current_opponent") or p.get("first_round_opponent")
            round_label = f"Eliminated · {pst.get('current_round', 'Playoffs')}"
        else:
            opp = (
                pst.get("current_opponent")
                or hctx.get("opponent")
                or hctx.get("opponent_display")
                or p.get("current_opponent")
                or p["first_round_opponent"]
            )
            round_label = pst.get("current_round") or hctx.get("round_label") or p["round"]
    header=f"{p['conference']} {round_label}"
    oseed = TEAM_PROFILES.get(opp, {}).get("seed", "—")
    e = html.escape
    opp_logo = TEAM_LOGOS.get(opp, "")
    _page_perf_mark_first_paint()
    st.markdown(
        (
            '<div class="team-match-header"><div style="display:flex;align-items:center;'
            'justify-content:center;gap:20px;flex-wrap:wrap">'
            f'<img src="{e(TEAM_LOGOS[team_name])}" width="88" alt=""/>'
            "<div><h1>"
            f"({p['seed']}) {e(team_name)} <span style='opacity:.5'>vs</span> "
            f"({oseed}) {e(opp)}</h1>"
            f"<h3>{e(p['conference'])} · {e(round_label)}</h3></div>"
            f'<img src="{e(opp_logo)}" width="88" alt=""/>'
            "</div></div>"
        ),
        unsafe_allow_html=True,
    )

def team_logo_html(team, size=28):
    return f"<img src='{TEAM_LOGOS[team]}' width='{size}' style='vertical-align:middle;margin-right:8px;'>"


def render_fan_section_header(title, icon="🏀", caption=None, tone="default"):
    e = html.escape
    cap = f"<div class='fan-sec-cap'>{e(caption)}</div>" if caption else ""
    st.markdown(
        f"<div class='fan-sec fan-sec--{e(tone)}'>"
        f"<div class='fan-sec-row'><span class='fan-sec-icon'>{e(icon)}</span>"
        f"<span class='fan-sec-title'>{e(title)}</span></div>{cap}</div>",
        unsafe_allow_html=True,
    )


def render_fan_section(title, icon="🏀", caption=None, tone="default", *, loading=False, empty=None):
    render_fan_section_header(title, icon, caption, tone)
    if loading:
        render_loading_skeleton(2, caption or "Loading…")
        return False
    if empty:
        st.markdown(f'<div class="fan-sec-body fan-sec-body--empty">{html.escape(empty)}</div>', unsafe_allow_html=True)
        return False
    return True


def render_fan_section_open():
    st.markdown('<div class="fan-sec-body">', unsafe_allow_html=True)


def render_fan_section_close():
    st.markdown("</div>", unsafe_allow_html=True)


DATA_SOURCE_LABELS = {
    "official": "Official data",
    "curated": "Curated board",
    "fan_model": "Fan model",
    "projected": "Projected",
    "estimate": "Estimate",
}

PAGE_TRUST_PROFILES = {
    "home": [
        ("official", "Bracket & series scores"),
        ("curated", "Fan briefing tiles"),
    ],
    "live_gc": [
        ("official", "CDN / stats scoreboard"),
    ],
    "bracket": [
        ("official", "NBA.com bracket sync"),
        ("curated", "Demo fallback when API empty"),
    ],
    "lineups": [
        ("curated", "Finals rotation board"),
        ("estimate", "Season averages in expanders"),
    ],
    "player_tracker": [
        ("official", "Playoff game logs"),
        ("curated", "Franchise chase board"),
        ("projected", "Milestone pace"),
        ("fan_model", "Pass probability"),
    ],
    "legacy": [
        ("official", "Playoff game logs"),
        ("fan_model", "Legacy score & sliders"),
    ],
    "team_history": [
        ("curated", "Franchise leader estimates"),
        ("projected", "Milestone countdown"),
    ],
    "previous_rounds": [
        ("official", "Bracket engine"),
        ("curated", "Demo rows when needed"),
    ],
    "offseason": [
        ("fan_model", "Front-office analysis"),
    ],
    "matchup_intel": [
        ("estimate", "Scouting synthesis"),
    ],
}


def data_source_badge_html(kind, label=None):
    e = html.escape
    kind = kind if kind in DATA_SOURCE_LABELS else "estimate"
    text = label or DATA_SOURCE_LABELS[kind]
    return f"<span class='fan-data-badge fan-data-badge--{e(kind)}'>{e(text)}</span>"


def render_page_trust_strip(page_key, extra_note=""):
    """Visible source labels so fans know what is official vs modeled."""
    import portfolio_polish as pp

    if not pp.show_trust_strip(st):
        return
    profile = PAGE_TRUST_PROFILES.get(page_key, [("estimate", "Mixed sources")])
    badges = []
    for item in profile:
        if isinstance(item, tuple):
            kind, lbl = item
        else:
            kind, lbl = item, None
        badges.append(data_source_badge_html(kind, lbl))
    note_html = ""
    if extra_note:
        note_html = f"<span class='fan-trust-note'>{html.escape(extra_note)}</span>"
    st.markdown(
        f"<div class='fan-trust-strip'>{''.join(badges)}{note_html}</div>",
        unsafe_allow_html=True,
    )


def render_fan_product_shell_open():
    st.markdown('<div class="fan-product-shell">', unsafe_allow_html=True)


def render_fan_product_shell_close():
    st.markdown("</div>", unsafe_allow_html=True)


def _team_live_game_watch(team_name):
    try:
        return get_current_or_upcoming_game(team_name)
    except Exception:
        return None


def _live_gc_should_auto_load(snap):
    if not snap or not snap.get("game_found"):
        return False
    return str(snap.get("game_status") or "") in LIVE_GC_AUTO_LOAD_STATUSES


def team_section_header(title, icon="🏀", caption=None, tone="default"):
    render_fan_section_header(title, icon, caption, tone)


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


def team_fan_identity(team_name):
    """Short, fan-facing identity lines for heroes and story cards."""
    nick = fan_nick(team_name)
    defaults = {
        "tagline": f"{nick} playoff pulse",
        "stakes": "Every possession changes the mood of the series.",
        "texture": "Pressure, momentum, matchups, and the moments fans remember.",
    }
    identities = {
        "New York Knicks": {
            "tagline": "MSG pressure cooker",
            "stakes": "Every Brunson touch feels louder because New York expects this run to matter.",
            "texture": "Physical defense, late-clock nerve, and the Garden waiting to explode.",
        },
        "San Antonio Spurs": {
            "tagline": "Built on poise",
            "stakes": "The future is arriving fast, but playoff habits still have to hold under noise.",
            "texture": "Discipline, length, half-court patience, and Wembanyama gravity.",
        },
        "Los Angeles Lakers": {
            "tagline": "Legacy lights",
            "stakes": "In Laker colors, every spring becomes a referendum on banners and stars.",
            "texture": "Championship pressure, veteran counters, and late-game shotmaking.",
        },
        "Cleveland Cavaliers": {
            "tagline": "Guard heat, playoff proof",
            "stakes": "Cleveland's guards have the keys; the series turns on whether the half court stays sharp.",
            "texture": "Mitchell pressure, Garland rhythm, Mobley/Allen protection, and tense fourth quarters.",
        },
        "Detroit Pistons": {
            "tagline": "Young team, loud moment",
            "stakes": "Detroit is trying to turn belief into a real playoff identity right now.",
            "texture": "Cade control, transition force, and whether the young group can close clean.",
        },
    }
    return {**defaults, **identities.get(team_name, {})}


def fan_story_callout(team_name, title, body, badge="STORYLINE"):
    """Compact TV-style story card for the biggest emotional angle."""
    e = html.escape
    ident = team_fan_identity(team_name)
    st.markdown(
        f"""
<div class="team-card" style="margin:10px 0 14px;border-left:5px solid var(--team-accent);">
  <div style="font-size:10px;font-weight:900;letter-spacing:.14em;color:var(--team-accent);text-transform:uppercase">{e(badge)}</div>
  <div style="font-size:1.08rem;font-weight:950;color:#0f172a;margin-top:3px">{e(title)}</div>
  <div style="font-size:14px;line-height:1.5;color:#334155;margin-top:6px">{body}</div>
  <div style="font-size:12px;color:#64748b;margin-top:8px">{e(ident["tagline"])} · {e(ident["texture"])}</div>
</div>
""",
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
@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)
def next_round_context_for_team(team_name):
    """Return next-round display context when the team's second-round series is complete
    but conference finals are not yet formed (waiting on the other conference semi).

    Once conference finals (or finals) exist for this team, returns None — the home
    header uses ``series_for_team`` directly for that matchup.
    """
    stt = get_merged_playoff_state()
    return _next_round_context_from_state(team_name, stt)


def _round_depth(series):
    rd = str((series or {}).get("round") or "")
    depth = ROUND_DEPTH_FOR_EXIT.get(rd, 0)
    if depth == 0 and "first" in rd.lower():
        depth = 1
    return depth


def _all_playoff_series_with_keys(use_demo_backup=None, api_refresh=None):
    stt = get_merged_playoff_state(use_demo_backup, api_refresh)
    return _all_playoff_series_with_keys_from_state(stt)


def playoff_status_for_team(team_name, use_demo_backup=None, api_refresh=None):
    """Single source of truth for active / advanced / awaiting / eliminated UI labels."""
    stt = get_merged_playoff_state(use_demo_backup, api_refresh)
    return get_team_playoff_status(team_name, stt)


def playoff_status_debug_dataframe(use_demo_backup=None, api_refresh=None):
    stt = get_merged_playoff_state(use_demo_backup, api_refresh)
    rows = []
    for team in sorted(TEAM_PROFILES):
        st_row = get_team_playoff_status(team, stt)
        rows.append({
            "Team": team,
            "Current round": st_row.get("current_round", ""),
            "Status": st_row.get("status", ""),
            "Opponent": st_row.get("current_opponent", ""),
            "Series score": st_row.get("series_record", "—"),
            "Series wins": st_row.get("series_wins", 0),
            "Source": st_row.get("source_kind", ""),
            "Detail": st_row.get("data_source", ""),
            "Elimination": st_row.get("elimination_reason", ""),
        })
    return pd.DataFrame(rows)


def render_loading_skeleton(lines=3, label="Loading…"):
    """Lightweight placeholder while heavy sections fetch."""
    e = html.escape
    body = "".join('<div class="fan-skel-line"></div>' for _ in range(max(1, int(lines))))
    st.markdown(
        f'<motion class="fan-skel-wrap"><div class="fan-skel-label">{e(label)}</div>{body}</div>'.replace("motion", "div"),
        unsafe_allow_html=True,
    )


def render_playoff_matchup_ribbon(team_name, stt=None):
    """Broadcast-style matchup strip — same labels on every fan page."""
    mx = get_display_matchup(team_name, stt)
    e = html.escape
    variant = "elim" if mx["eliminated"] else ("wait" if mx["status"] in ("awaiting opponent", "advanced") else "live")
    opp_txt = f"vs {e(mx['opponent_nick'])}" if mx.get("opponent_nick") and mx["opponent_nick"] != "TBD" else ""
    score_txt = e(mx["series_record"]) if mx["series_record"] and mx["series_record"] != "—" else ""
    score_block = f'<span class="fan-ribbon-score">{score_txt}</span>' if score_txt else ""
    st.markdown(
        f'<div class="fan-matchup-ribbon fan-matchup-ribbon--{variant}">'
        f'<span class="fan-ribbon-badge">{e(mx["status_badge"])}</span>'
        f'<span><b>{e(mx["round_short"])}</b> · {opp_txt}</span>'
        f'{score_block}'
        f'<span class="fan-ribbon-muted">{mx["series_wins"]} series won · bracket sync</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    _page_perf_mark_first_paint()


def render_playoff_state_debug_expander(location_key="playoff_state"):
    """Developer-only playoff engine table (gated by Show performance debug)."""
    if not globals().get("SHOW_PERF_DEBUG", False):
        return
    with st.expander("Playoff state debug (developer)", expanded=False):
        use_demo, api_on = get_playoff_refresh_settings()
        st.caption(
            f"Unified bracket engine · API sync {'on' if api_on else 'off'} · "
            f"fallback when empty {'on' if use_demo else 'off'} · "
            "elimination only when opponent has exactly 4 wins."
        )
        st.dataframe(
            playoff_status_debug_dataframe(use_demo, api_on),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Source: API = live NBA.com logs · fallback = demo backup · static = Round 1 archive.")


def _build_local_series_shell(team_name):
    """Current playoff series view: active bracket round first; skip completed semis when advanced."""
    stt = get_merged_playoff_state()
    pst = get_team_playoff_status(team_name, stt)
    if pst.get("status") == "eliminated":
        return pst.get("series")
    _sk, active = series_for_team(team_name)
    if active:
        return dict(active)
    if pst.get("status") in ("awaiting opponent", "advanced"):
        return None
    second_map = stt.get("second") or {}
    for _k, s in second_map.items():
        if team_name in (s.get("a"), s.get("b")):
            if not _series_has_confirmed_winner(s):
                return dict(s)
    for _key, s in (stt.get("first") or {}).items():
        if team_name in (s.get("a"), s.get("b")):
            return dict(s)
    return None


def get_fast_series_snapshot(team_name):
    """Lightweight series snapshot from merged playoff state (cached API + fallback)."""
    profile = TEAM_PROFILES.get(team_name) or {}
    pst = get_team_playoff_status(team_name)
    out = {
        "team_name": team_name,
        "opponent": pst.get("current_opponent") or profile.get("current_opponent") or profile.get("first_round_opponent"),
        "series_score": None,
        "round": pst.get("current_round") or profile.get("round", "Playoffs"),
        "latest_game": None,
        "source": pst.get("data_source") or "Merged playoff state",
    }
    s = pst.get("series") or _build_local_series_shell(team_name)
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
    pst = get_team_playoff_status(team_name)
    if pst.get("status") == "eliminated":
        opp = pst.get("current_opponent") or profile.get("first_round_opponent")
        return {
            "mode": "eliminated",
            "series": pst.get("series"),
            "round_label": pst.get("current_round") or "Eliminated",
            "opponent": opp,
            "opponent_display": opp or "Opponent",
            "advanced": False,
            "bracket_series": False,
            "ctx": None,
            "fast_snapshot": get_fast_series_snapshot(team_name),
        }
    ctx = next_round_context_for_team(team_name)
    if ctx and ctx.get("eliminated"):
        return {
            "mode": "eliminated",
            "series": None,
            "round_label": "Eliminated",
            "opponent": ctx.get("opponent_text"),
            "opponent_display": ctx.get("opponent_text", "Opponent"),
            "advanced": False,
            "bracket_series": False,
            "ctx": ctx,
            "fast_snapshot": {
                "team_name": team_name,
                "opponent": ctx.get("opponent_text", "Opponent"),
                "series_score": "complete",
                "round": "Eliminated",
                "latest_game": (ctx.get("completed_series") or {}).get("games", [])[-1] if (ctx.get("completed_series") or {}).get("games") else None,
                "source": "bracket advancement",
            },
        }
    if ctx and ctx.get("advanced"):
        return {
            "mode": "waiting_cf",
            "series": None,
            "round_label": ctx["round_label"],
            "opponent": ctx.get("opponents", [None])[0] if len(ctx.get("opponents", [])) == 1 else None,
            "opponent_display": ctx.get("opponent_text", "TBD"),
            "opponents": ctx.get("opponents", []),
            "advanced": True,
            "bracket_series": False,
            "ctx": ctx,
            "fast_snapshot": {
                "team_name": team_name,
                "opponent": ctx.get("opponent_text", "TBD"),
                "series_score": "awaiting matchup" if len(ctx.get("opponents", [])) != 1 else "next round set",
                "round": ctx.get("round_label", "Playoffs"),
                "latest_game": (ctx.get("completed_series") or {}).get("games", [])[-1] if (ctx.get("completed_series") or {}).get("games") else None,
                "source": "bracket advancement",
            },
        }
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
    opp = (
        snap.get("opponent")
        or pst.get("current_opponent")
        or profile.get("current_opponent")
    )
    return {
        "mode": "standard",
        "series": s,
        "round_label": snap.get("round") or pst.get("current_round") or profile.get("round", "Playoffs"),
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
    if ctx and ctx.get("eliminated"):
        return {
            "mode": "eliminated",
            "series": None,
            "round_label": "Eliminated",
            "opponent": ctx.get("opponent_text"),
            "opponent_display": ctx.get("opponent_text", "Opponent"),
            "advanced": False,
            "bracket_series": False,
            "ctx": ctx,
        }
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
    profile = get_effective_team_profile(team_name)
    lens = team_dashboard_lens(team_name)
    if skip_live_fetch:
        fb = None
        live = None
    else:
        fb = featured_broadcast_state(team_name)
        live = None
        if isinstance(fb, dict) and fb.get("game"):
            live = fb["game"]
    mode = hctx.get("mode")
    s = None if mode == "waiting_cf" else (hctx.get("series") or series_board)
    tw = ow = 0
    opp = None
    last_winner = None
    games_played = 0
    series_winner = None
    rnd = hctx.get("round_label") or profile.get("round", "Playoffs")
    if mode == "waiting_cf":
        opp = hctx.get("opponent") or hctx.get("opponent_display")
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
        "future_opponents": hctx.get("opponents", []),
        "opponent_display": hctx.get("opponent_display"),
    }


def _home_fan_excitement_cards(team_name, pctx, s_active, hctx):
    """Why fans should care — each card answers a different question (no series score repeat)."""
    nick = fan_nick(team_name)
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    ax = lens.get("identity_axes") or ("Execution", "Defense", "Margins")
    prof = TEAM_PROFILES.get(team_name) or {}
    opp = pctx.get("opp") or prof.get("current_opponent")
    on = fan_nick(opp) if opp else "the opponent"
    strengths = prof.get("strengths") or []
    concerns = prof.get("concerns") or []

    if _is_home_eliminated(team_name):
        od = get_offseason_outlook(team_name)
        return [
            ("What broke", od["reflection"]["elimination_cause"][:280]),
            ("Front-office lever", (od.get("priorities") or ["Roster and cap alignment"])[0]),
            ("What fans still chase", (od.get("direction") or {}).get("blurb", "The next chapter starts with honest tape review.")),
        ]

    if hctx.get("advanced"):
        opps = [fan_nick(o) for o in (hctx.get("opponents") or [])]
        opp_txt = " / ".join(opps) if opps else "the bracket"
        return [
            ("Matchup edge", f"{ax[0]} is the skill that travels — {nick} prep now tracks how it plays against {opp_txt}."),
            ("Storyline entering the next round", f"Cleared the last round; the question is whether {ax[1]} holds up when the stage gets louder."),
            ("Pressure point", lens.get("pressure_axis", "Every possession gets graded on the biggest stage left.")),
        ]

    last = (s_active.get("games") or [])[-1] if s_active else None
    game_n = len(s_active.get("games") or []) + 1 if s_active else 2
    last_note = ""
    if last:
        last_note = f" After Game {len(s_active.get('games') or [])}, "
    return [
        (
            "Matchup advantage",
            strengths[0] if strengths else f"{ax[0]} against {on}'s length is the cleanest path to clean looks.",
        ),
        (
            f"Biggest storyline entering Game {game_n}",
            f"{last_note}{nick} need {ax[2]} to stick — {on} will test whether the opener was noise or identity."
            if last
            else f"{nick} open the series hunting early rhythm before {on} settle into their defensive shell.",
        ),
        (
            "X-factor",
            concerns[0] if concerns else f"When {ax[1]} slips, bench minutes and foul discipline decide the night.",
        ),
    ]


def _home_player_spotlight(team_name, s_active, pctx):
    """Last-game standout + player to watch next — who is driving the outcome?"""
    prof = TEAM_PROFILES.get(team_name) or {}
    starters = list(prof.get("starters") or [])
    anchor = pctx.get("flagship") or (starters[0] if starters else "")
    last_mvp, last_why = "", ""
    if s_active and s_active.get("games"):
        last = s_active["games"][-1]
        opp = s_active["b"] if team_name == s_active["a"] else s_active["a"]
        gn = last.get("Game") if isinstance(last.get("Game"), int) else str(last.get("Game", "1")).replace("Game ", "")
        try:
            gn_i = int(str(gn).replace("Game ", ""))
        except Exception:
            gn_i = len(s_active["games"])
        last_mvp, last_why = mvp_for_game(team_name, opp, gn_i, last.get("Winner"))

    watch = anchor
    watch_why = "Lead guard burden rises when the defense loads the ball."
    if last_mvp and last_mvp != anchor:
        watch = anchor or last_mvp
        watch_why = f"{last_mvp} set the last game's tone; {watch or 'the star'} has to answer the counter-scheme next."
    elif anchor == "Jalen Brunson" or "Brunson" in str(anchor):
        watch_why = "Late-clock creation and foul-drawing keep New York's offense honest when the game tightens."
    elif anchor and "Wembanyama" in str(anchor):
        watch_why = "Rim protection and spacing gravity force the offense to pick its poison every trip."

    rising = ""
    for name in starters[1:4]:
        if name and name != last_mvp:
            rising = name
            break
    return last_mvp, last_why, watch, watch_why, rising


def _home_watch_next_keys(team_name, pctx, s_active):
    """Three keys for the next game — what should fans watch for?"""
    nick = fan_nick(team_name)
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    ax = lens.get("identity_axes") or ("Half-court execution", "Switchable defense", "Glass margin")
    opp = pctx.get("opp")
    on = fan_nick(opp) if opp else "the opponent"
    prof = TEAM_PROFILES.get(team_name) or {}
    game_n = len(s_active.get("games") or []) + 1 if s_active else 1
    return [
        ("Opening-quarter pace", f"Does {nick} set the physical tone before {on} lean on length and rim protection?"),
        ("Swing matchup", f"{ax[0]} vs {on}'s best wing — whoever wins that duel controls the shot diet."),
        ("Bench battle", f"{(prof.get('subs') or ['Second unit'])[0]} minutes — where hidden {ax[2]} swings live."),
    ]


def _home_franchise_stakes(team_name):
    """Historical context — what is at stake?"""
    nick = fan_nick(team_name)
    if team_name == "New York Knicks":
        return (
            "FRANCHISE STAKES: First Finals since '99 — Brunson is already in the Ewing/Frazier scoring conversation. "
            "Win the banner and this run vaults past the Melo-era what-ifs; lose and it still rewrites Garden history."
        )
    if team_name == "San Antonio Spurs":
        return (
            "FRANCHISE STAKES: Wembanyama's Duncan-1999 parallel is live after a Game 1 loss (105–95) — "
            "one title here accelerates a young core into the Robinson-to-Duncan handoff story fans have waited for."
        )
    if _is_home_eliminated(team_name):
        od = get_offseason_outlook(team_name)
        return (od.get("direction") or {}).get("blurb", f"{nick} shift from postseason heartbreak to offseason blueprint.")
    return f"{nick} are still writing the yearbook entry for this postseason — every remaining game moves the franchise needle."


def _home_series_storyline(team_name, s_active, pctx):
    """Why the series is unfolding this way — not just the scoreboard."""
    if not s_active or not s_active.get("games"):
        return "The series opens on scheme and nerves — the first answer usually sets the possession battle for the rest of the week."
    nick = fan_nick(team_name)
    opp = s_active["b"] if team_name == s_active["a"] else s_active["a"]
    on = fan_nick(opp)
    last = s_active["games"][-1]
    lw = last.get("Winner")
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    ax = lens.get("identity_axes") or ("execution", "defense", "margins")
    if lw == team_name:
        return (
            f"{nick} grabbed first possession of the narrative — {ax[0]} and {ax[2]} flipped the late game. "
            f"{on} have to adjust{' before Game 2' if len(s_active['games']) == 1 else ''} or the series stays on New York's terms."
        )
    return (
        f"{on} stole the opener's identity battle — {nick} need cleaner {ax[1]} and fewer empty trips "
        f"before the margin becomes structural."
    )


def _home_finals_hero_palette(team_name, opponent):
    """Dual-team Finals broadcast palette (Knicks blue/orange + Spurs silver/black)."""
    nyk = get_team_theme("New York Knicks")
    sas = get_team_theme("San Antonio Spurs")
    home = nyk if team_name == "New York Knicks" else sas
    away = sas if team_name == "New York Knicks" else nyk
    return {
        "bg0": home["bg0"],
        "bg1": away["bg1"],
        "accent": home["accent"],
        "accent2": away["accent"],
        "accent_soft": home["accent_soft"],
        "accent_soft2": away["accent_soft"],
        "primary": home["primary"],
        "primary2": away["primary"],
        "finals": True,
    }


def _home_matchup_swing_line(team_name, pctx, s_active):
    """Biggest matchup swing — distinct from series score copy."""
    opp = pctx.get("opp") or (TEAM_PROFILES.get(team_name) or {}).get("current_opponent")
    on = fan_nick(opp) if opp else "the opponent"
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    ax = lens.get("identity_axes") or ("Half-court engine", "Wing defense", "Glass margin")
    if team_name == "New York Knicks" and opp == "San Antonio Spurs":
        return (
            "MATCHUP BOARD: Wembanyama's help vs Brunson's pull-up — "
            "when New York wins the paint-touch war, the Knicks get 40+ corner threes; when San Antonio shrinks the floor, it's a turnover series."
        )
    if team_name == "San Antonio Spurs" and opp == "New York Knicks":
        return (
            "MATCHUP BOARD: Towns spacing vs Wemby deterrence — "
            "clean Knicks catch-and-shoot looks mean Castle runs all night; packed paint turns it into a Castle vs Hart chess match."
        )
    return f"{ax[0]} against {on}'s best counter — whoever owns that duel controls the shot diet for Game 2."


def _home_series_tactical_why(team_name, s_active, pctx):
    """Scheme-level why — distinct from narrative storyline bar above the ledger."""
    if not s_active or not s_active.get("games"):
        return "Opening possession battle: who sets the physical tone and forces the first schematic answer?"
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    ax = lens.get("identity_axes") or ("half-court engine", "wing defense", "glass margin")
    prof = TEAM_PROFILES.get(team_name) or {}
    opp = s_active["b"] if team_name == s_active["a"] else s_active["a"]
    on = fan_nick(opp)
    if team_name == "New York Knicks" and opp == "San Antonio Spurs":
        return (
            "STUDIO TAKE: Brunson-Towns PnR vs Wembanyama drop is the whole series — "
            "Knicks win Game 1 (105–95) because the paint-touch battle flipped; San Antonio has to blitz or Brunson cooks on pull-ups."
        )
    if team_name == "San Antonio Spurs" and opp == "New York Knicks":
        return (
            "STUDIO TAKE: Pop's drop vs Towns spacing is the lever — "
            "Spurs trail 0–1 but Wembanyama deterrence still sets the terms; Castle must punish Brunson blitzes in transition."
        )
    return (
        f"Scheme question: does {ax[0]} travel against {on}'s length, or does {on} shrink the floor "
        f"before {(prof.get('starters') or ['the star'])[0]} gets clean looks?"
    )


def _home_watch_next_brief(team_name, pctx, watch_keys):
    """Single fan-facing watch line — likely next development."""
    prof = TEAM_PROFILES.get(team_name) or {}
    opp = pctx.get("opp") or prof.get("current_opponent")
    on = fan_nick(opp) if opp else "the opponent"
    if team_name == "New York Knicks" and opp == "San Antonio Spurs":
        return (
            "WATCH LIST: First six minutes of Brunson-Towns PnR vs Wemby drop — "
            "if New York sets the physical tone early, San Antonio has to abandon the paint pack and live with Hart corner threes."
        )
    if team_name == "San Antonio Spurs" and opp == "New York Knicks":
        return (
            "WATCH LIST: Castle push pace after Knicks misses — "
            "8+ transition points in Q1 means San Antonio stole the game's tempo before Thibs can shorten the rotation."
        )
    if len(watch_keys) > 1:
        return watch_keys[1][1]
    return f"First-quarter pace and {(prof.get('subs') or ['bench'])[0]} minutes — whoever sets the physical tone forces the first schematic answer against {on}."


def _home_game1_to_game2_shift(team_name, s_active, pctx):
    """What changed from Game 1 to Game 2 — coaching and possession texture."""
    games = (s_active or {}).get("games") or []
    if len(games) < 1:
        return "Game 1 sets the schematic baseline — expect both staffs to hunt the weak-side matchup that got punished in the opener."
    nick = fan_nick(team_name)
    opp = s_active["b"] if team_name == s_active["a"] else s_active["a"]
    on = fan_nick(opp)
    last = games[-1]
    won = last.get("Winner") == team_name
    lens = pctx.get("lens") or team_dashboard_lens(team_name)
    ax = lens.get("identity_axes") or ("half-court engine", "wing defense", "glass margin")
    if team_name == "New York Knicks" and opp == "San Antonio Spurs":
        if won:
            return (
                "INSIDE THE TAPE: Game 1 validated Thibs' switch plan — Hart/Bridges on Castle, Towns sealing Wemby. "
                "Game 2 chess: expect San Antonio to load the ball on Brunson and force McBride/Robinson minutes to matter."
            )
        return (
            "INSIDE THE TAPE: San Antonio owned the rim in Game 1 — Knicks need cleaner Towns touches before "
            "Wembanyama's length becomes the default coverage and Brunson sees three bodies every pull-up."
        )
    if won:
        return f"{nick} carried Game 1 identity — {on} adjust coverages on {ax[0]}; {nick} counter with pace and {ax[2]}."
    return f"{on} stole Game 1's shot diet — {nick} staff has to simplify early actions and stress {ax[1]} before the hole deepens."


def _home_coaching_adjustment_line(team_name, pctx, s_active):
    """Coaching chess — distinct from matchup swing."""
    prof = TEAM_PROFILES.get(team_name) or {}
    opp = pctx.get("opp") or prof.get("current_opponent")
    on = fan_nick(opp) if opp else "the opponent"
    games = len((s_active or {}).get("games") or [])
    if team_name == "New York Knicks":
        return (
            "WHITE BOARD: After Game 1, expect Pop to blitz Brunson and force Towns into foul-trouble sequences — "
            "Thibs' counter is Hart/Bridges switching onto Castle and living with contested pull-ups over turnovers."
        )
    if team_name == "San Antonio Spurs":
        return (
            "WHITE BOARD: Game 2 likely brings more drop vs Towns and tag-and-switch on Brunson — "
            "Castle's pace when the Knicks miss long rebounds is San Antonio's cleanest path back into the series."
        )
    return f"Staff vs staff: {on} will test {(prof.get('concerns') or ['bench minutes'])[0]} — rotation length decides who owns the adjustment war."


def _home_pressure_players_line(team_name, pctx, s_active):
    """Who is under the microscope next — not the same as player to watch."""
    prof = TEAM_PROFILES.get(team_name) or {}
    starters = prof.get("starters") or []
    flagship = pctx.get("flagship") or (starters[0] if starters else "Star")
    second = starters[1] if len(starters) > 1 else "Wing"
    games = len((s_active or {}).get("games") or [])
    if team_name == "New York Knicks":
        return (
            "ON THE HOT SEAT: Brunson (efficiency vs blitzes), Towns (fouls vs Wemby), Bridges (track Castle clean) — "
            "the Knicks stole Game 1; now every empty Brunson possession gets magnified on national TV."
        )
    if team_name == "San Antonio Spurs":
        return (
            "ON THE HOT SEAT: Wembanyama (stay upright vs Towns), Castle (turnovers vs Hart traps), Barnes (corner 3 volume) — "
            "Pop's counter only works if Barnes makes the Knicks pay for loading up on Victor."
        )
    return f"Pressure board: {flagship} must answer the scouting report; {second} owns the swing matchup when the star sits."


def _home_rising_player_line(team_name, pctx, s_active, rising):
    """Who is rising — analyst voice with matchup specifics."""
    if not rising:
        prof = TEAM_PROFILES.get(team_name) or {}
        sub = (prof.get("subs") or ["Second unit"])[0]
        return f"No clear riser yet — watch {sub} minutes when the starter sits; that's where the hidden swing lives."
    nick = fan_nick(team_name)
    if team_name == "New York Knicks" and rising:
        return (
            f"{rising} is earning stagger minutes — the broadcast angle is whether {nick} trust him to guard Castle "
            f"or hide him on Barnes when Wembanyama sits."
        )
    if team_name == "San Antonio Spurs" and rising:
        return (
            f"{rising} is the bench story — if San Antonio steals a quarter, it's usually because {rising} "
            f"survived the Knicks' switching chaos without turning it over."
        )
    return f"{rising} — role expansion spot; the staff is testing whether he can repeat Game 1 winning habits on tired legs."


def _home_game2_change_line(team_name, pctx, s_active):
    """What the next game could change — without repeating the series ledger."""
    nick = fan_nick(team_name)
    opp = pctx.get("opp")
    on = fan_nick(opp) if opp else "the opponent"
    games = len((s_active or {}).get("games") or [])
    nxt = games + 1
    prof = TEAM_PROFILES.get(team_name) or {}
    if games == 1:
        return (
            f"Game {nxt} flips home-court math: a {nick} win forces {on} to answer on the road; "
            f"a Spurs bounce-back steals the pressure Brunson carried in the opener. "
            f"{(prof.get('concerns') or ['Bench minutes'])[0].capitalize()} will show up early."
        )
    return (
        f"Game {nxt} rewrites the possession battle — adjustments to switching, rebounding, and "
        f"who absorbs the star usage matter more than another standings-style recap."
    )


def _render_fan_energy_grid(cards):
    """HTML grid of fan-energy cards: list of (icon, title, body, variant)."""
    e = html.escape
    parts = ['<div class="fan-energy-grid">']
    for item in cards:
        icon, title, body = item[0], item[1], item[2]
        variant = item[3] if len(item) > 3 else ""
        cls = "fan-energy-card"
        if variant:
            cls += f" fan-energy-card--{e(variant)}"
        parts.append(
            f'<div class="{cls}">'
            f'<div class="fan-energy-k"><span class="fan-energy-icon">{e(icon)}</span>{e(title)}</div>'
            f'<div class="fan-energy-b">{e(body)}</div></div>'
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _render_offseason_card_grid(items):
    """Offseason module cards: list of (kicker, title, body_html_or_text)."""
    e = html.escape
    chunks = ['<div class="os-card-grid">']
    for kicker, title, body in items:
        body_e = body if "<" in str(body) else e(str(body))
        chunks.append(
            f'<div class="os-card"><div class="os-card-k">{e(kicker)}</div>'
            f'<div class="os-card-t">{e(title)}</div><div class="os-card-b">{body_e}</div></div>'
        )
    chunks.append("</div>")
    st.markdown("".join(chunks), unsafe_allow_html=True)


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

    if pctx.get("mode") == "waiting_cf":
        opponents = [fan_nick(op) for op in (pctx.get("future_opponents") or [])]
        opp_txt = " / ".join(opponents) if opponents else str(pctx.get("opponent_display") or "the bracket")
        return [
            ("Next-round lens", f"{nick} are through; the next matchup is now the story, with {opp_txt} setting the prep board."),
            ("Style question", f"{ax[0]} travels into the next round, but the matchup will decide how much help pressure comes from {ax[1]}."),
            ("Pressure point", lens.get("pressure_axis", "The deeper the bracket gets, the more every empty possession shows up.")),
        ]
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

    if pctx.get("mode") == "waiting_cf":
        opps = [fan_nick(op) for op in (pctx.get("future_opponents") or [])]
        opp_txt = " / ".join(opps) if opps else str(pctx.get("opponent_display") or "opponent TBD")
        tag, sub = "NEXT ROUND WATCH", f"{nick} are through. Prep shifts to {opp_txt} while the bracket settles."
    elif pctx.get("phase_live"):
        tag, sub = "LIVE BOARD", "Rotation, fouls, and late-clock shot quality are moving in real time."
    elif pctx.get("elimination_trailing"):
        tag, sub = "MUST-WIN NIGHT", "The series only extends with a win — empty possessions cost twice."
    elif pctx.get("sweep_chance"):
        tag, sub = "SWEEP WINDOW", f"3–0 leverage — {on} is one loss from an early summer."
    elif pctx.get("closeout_opportunity"):
        tag, sub = "MATCH POINT", "A disciplined close can end the series and bank rest before the next round."
    elif pctx.get("danger_down_3"):
        tag, sub = "BRACKET HOLE · 0–3", "The comeback path requires four perfect nights in a row."
    elif pctx.get("injury_level") == "high":
        tag, sub = "AVAILABILITY SWING", "Starter-level tags on the report — substitution patterns can flip matchups fast."
    else:
        tag = "SERIES TEMPO"
        sub = f"{fan_nick(team_name)} · {pctx.get('round') or 'Playoffs'} — {lens.get('pressure_axis', 'Pressure tightens as the bracket advances.')}"

    a0, a1, a2 = esc(ax[0]), esc(ax[1]) if len(ax) > 1 else "", esc(ax[2]) if len(ax) > 2 else ""
    hot = " cmd-emph-card--hot" if (pctx.get("phase_live") or pctx.get("elimination_trailing") or pctx.get("danger_down_3")) else ""
    s_obj = pctx.get("series")
    last_game = (s_obj.get("games") or [])[-1] if s_obj else None
    if pctx.get("mode") == "waiting_cf":
        board_label = "Next matchup"
        board_value = esc(pctx.get("opponent_display") or "Awaiting opponent")
    elif last_game and last_game.get("Score"):
        board_label = "Last game box score"
        board_value = esc(str(last_game.get("Score", "")))
    else:
        board_label = "Next tip"
        board_value = esc(pctx.get("opponent_display") or on)
    return f"""<div class="cmd-emph-shell"><div class="cmd-emph-grid">
  <div class="cmd-emph-card{hot}"><div class="cmd-emph-k">{esc(tag)}</div><div class="cmd-emph-v">{esc(sub)}</div></div>
  <div class="cmd-emph-card"><div class="cmd-emph-k">Identity lever</div><div class="cmd-emph-v">{a0}</div><div class="cmd-emph-s">{a1}</div></div>
  <div class="cmd-emph-card"><div class="cmd-emph-k">{board_label}</div><div class="cmd-emph-v">{board_value}</div><div class="cmd-emph-s">{a2}</div></div>
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
.cmd-hero--finals {
  border: 1px solid rgba(255,255,255,0.18);
  box-shadow: 0 22px 56px rgba(0,0,0,0.55), 0 0 40px var(--cmd-accent-soft, rgba(245,132,38,.15));
  background:
    radial-gradient(ellipse 55% 80% at 8% 20%, var(--cmd-accent-soft), transparent 55%),
    radial-gradient(ellipse 50% 75% at 92% 25%, var(--cmd-accent-soft2, rgba(200,16,46,.12)), transparent 50%),
    linear-gradient(135deg, var(--cmd-bg0) 0%, #0f172a 42%, var(--cmd-bg1) 100%);
}
.cmd-finals-badge {
  display: inline-block; margin-bottom: 10px; padding: 5px 14px; border-radius: 999px;
  font-size: 10px; font-weight: 950; letter-spacing: .16em; text-transform: uppercase;
  color: #fff7ed; border: 1px solid rgba(255,255,255,.22);
  background: linear-gradient(90deg, var(--cmd-primary, #006BB6), var(--cmd-primary2, #C4CED4));
}
.cmd-scoreline--finals {
  background: linear-gradient(90deg, #fde68a, #fbbf24, #f59e0b);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.cmd-emph-card--finals { border-color: var(--cmd-accent, #f59e0b); }
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
.cmd-subscore { font-size: 13px; font-weight: 700; color: #cbd5e1; margin: -6px 0 10px; letter-spacing: 0.02em; }
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
        if _is_home_eliminated(team_name):
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
        return f"Deadlocked in the {rnd} — {pa or 'Shot quality and rebounding margin decide who seizes the next swing game.'}"
    if lw == team_name and last:
        return (
            f"{nick} carry the last night's momentum — {on} have to answer what worked late "
            f"before the chess match shifts again."
        )
    if lw and lw != team_name:
        return f"{on} answered last — {nick} need a cleaner opening stretch before the game tightens late."
    if "Final" in rnd or ("Conference" in rnd and "First" not in rnd):
        return f"{rnd} chess match with {on} — {pa or 'The stakes rise with every night left on the schedule.'}"
    return f"{nick} in the {rnd} — {pa or 'The next result still redraws the series map.'}"


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
                f"Availability for {html.escape(fan_nick(team_name))} loads when you ask for the live board."
            )
        row = df.iloc[0]
        return (
            f"<strong>{html.escape(team_name)}</strong>: {html.escape(str(row.get('Player', '?')))} "
            f"<span style='opacity:.85'>({html.escape(str(row.get('Status', '?')))})</span>"
        )
    fb_list = FALLBACK_INJURY_REPORT.get(team_name, []) or []
    if not fb_list:
        return (
            "Availability is tucked away until you ask for the live board."
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
    profile_early = TEAM_PROFILES[team_name]
    opp_early = hctx.get("opponent") or profile_early.get("current_opponent")
    rnd_early = (hctx.get("series") or {}).get("round") or profile_early.get("round", "")
    is_finals = "NBA Finals" in str(rnd_early) and opp_early in TEAM_PROFILES
    pal = _home_finals_hero_palette(team_name, opp_early) if is_finals else live_hero_palette(team_name)
    esc = html.escape
    profile = TEAM_PROFILES[team_name]
    offseason = _is_home_eliminated(team_name)
    s = hctx.get("series") or (pctx.get("series") if pctx else None)
    live = pctx.get("live")
    fb = pctx.get("fb")
    prob = _home_series_win_probability(team_name, hctx, live)
    prob_display = f"{prob}%"
    _show_prob = bool(
        st.session_state.get("portfolio_demo_mode") or st.session_state.get("portfolio_screenshot_mode")
    )
    prob_html = (
        f'<div class="cmd-prob-pill">Series win probability: <strong>{esc(prob_display)}</strong>'
        f" · Championship stage outlook active</div>"
        if _show_prob
        else ""
    )
    headline = _home_storyline_headline(team_name, hctx, pctx)
    box_score_html = ""
    if s and s.get("games") and not offseason:
        lg = s["games"][-1]
        if lg.get("Score"):
            box_score_html = (
                f"<div class='cmd-subscore'>{esc(lg.get('Game', 'Last game'))}: "
                f"{esc(lg.get('Score', ''))}</div>"
            )
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
    if fb and fb.get("game"):
        ph = fb.get("phase")
        if ph == "live":
            pulse = "🔴 LIVE — broadcast hub hot"
        elif fb.get("starting_soon"):
            pulse = "⏳ Starting soon (~1h window)"
        elif ph == "pregame":
            pulse = "📅 Pregame board loaded"
        elif ph == "postgame":
            pulse = "📼 Final — full wrap in hub"

    if offseason:
        pulse = "Draft · cap · trade board"

    next_title = "What's next" if offseason else "Next game"
    finals_badge = ""
    hero_cls = "cmd-hero"
    score_cls = "cmd-scoreline"
    shell_vars = (
        f"--cmd-bg0:{pal['bg0']};--cmd-bg1:{pal['bg1']};"
        f"--cmd-accent:{pal['accent']};--cmd-accent-soft:{pal['accent_soft']};"
    )
    if is_finals:
        hero_cls = "cmd-hero cmd-hero--finals"
        score_cls = "cmd-scoreline cmd-scoreline--finals"
        shell_vars += (
            f"--cmd-accent-soft2:{pal.get('accent_soft2', pal['accent_soft'])};"
            f"--cmd-primary:{pal.get('primary', pal['accent'])};"
            f"--cmd-primary2:{pal.get('primary2', pal['accent'])};"
        )
        finals_badge = '<div class="cmd-finals-badge">NBA Finals · Championship Stage</div>'

    return f"""
<div class="cmd-shell" style="{shell_vars}">
<div class="{hero_cls}">
  <div class="cmd-hero-inner">
    <div class="cmd-kicker">{kicker_dom}</div>
    {finals_badge}
    <div class="cmd-row">
      <img class="cmd-logo" src="{esc(left_logo)}" alt=""/>
      <div class="cmd-center">
        <div class="cmd-round">{rnd}</div>
        <div class="cmd-match">{matchup}</div>
        <div class="{score_cls}">{score_txt}</div>
        {box_score_html}
        <div class="cmd-rail">
          <span class="cmd-pill">{esc(pulse)}</span>
        </div>
      </div>
      {right_html}
    </div>
    <div class="cmd-headline">{esc(headline)}</div>
    {prob_html}
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
        badge = ""
        if phase == "live":
            mod = "home-live-strip home-live-strip--live"
            title = "🔴 LIVE NOW · Game in progress"
            badge = '<div class="home-live-badge">ON AIR · LIVE</div>'
        elif phase == "pregame" and soon:
            mod = "home-live-strip home-live-strip--soon"
            title = "⏳ GAME STARTING SOON"
            badge = '<div class="home-live-badge">TIPOFF SOON</div>'
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
  {badge}
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
            label = "🔴 Live Game Center — LIVE NOW"
        elif phase == "pregame" and soon:
            label = "⏱️ Live Game Center — starting soon"
        elif phase == "postgame":
            label = "📡 Live Game Center — wrap & series"
        if st.button(label, key="home_strip_open_live"):
            st.session_state["page_override"] = "🔴 Live Game Center"
            st.rerun()
        return

    # CDN-first fallback when featured merge has no row (still no box score / PBP on Home).
    try:
        snap = get_home_layer1_snapshot(team_name)
    except Exception:
        snap = None
    if snap and snap.get("game_found"):
        status = str(snap.get("game_status") or "")
        phase = snap.get("phase") or "pregame"
        away_name = snap.get("away_team") or ""
        home_name = snap.get("home_team") or ""
        aws, hs = snap.get("away_score", 0), snap.get("home_score", 0)
        nick = fan_nick(team_name)
        if status == "live":
            mod, title, label = "home-live-strip home-live-strip--live", "🔴 LIVE NOW · Game in progress", "🔴 Live Game Center — LIVE NOW"
        elif status == "starting soon":
            mod, title, label = "home-live-strip home-live-strip--soon", "⏳ GAME STARTING SOON", "⏱️ Live Game Center — starting soon"
        elif status == "final":
            mod, title, label = "home-live-strip home-live-strip--post", "📼 FINAL IN THE FEED", "📡 Live Game Center — wrap & series"
        else:
            mod, title, label = "home-live-strip", "📅 GAME SCHEDULED TODAY", "Go to Live Game Center"
        score_line = f"{aws} — {hs}" if status in ("live", "final") or (aws + hs) > 0 else (snap.get("countdown") or "Tipoff today")
        st.markdown(
            f'<div class="{mod}"><div class="home-live-strip-title">{html.escape(title)}</div>'
            f'<div class="home-live-strip-score">{html.escape(str(score_line))}</div>'
            f'<div class="home-live-strip-sub">{html.escape(away_name)} @ {html.escape(home_name)}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button(label, key="home_strip_open_live_l1"):
            st.session_state["page_override"] = "🔴 Live Game Center"
            st.rerun()
        return


def render_home_current_game_card(team_name):
    """Prominent Home card for scheduled/starting-soon/live games (CDN-first Layer 1)."""
    if st.session_state.get("portfolio_demo_mode") or st.session_state.get("portfolio_screenshot_mode"):
        return
    manual = _manual_live_override_snapshot(team_name)
    if manual and st.session_state.get("manual_live_enabled"):
        home_name = manual["home_name"]
        away_name = manual["away_name"]
        status = str(manual.get("status", "live")).lower()
        snap = {
            "game_found": True,
            "game_status": status,
            "home_team": home_name,
            "away_team": away_name,
            "away_score": manual["away_score"],
            "home_score": manual["home_score"],
            "game_status_text": manual.get("status", "Manual"),
            "phase": manual.get("phase", "live"),
            "data_source": "Emergency score entry",
        }
    else:
        try:
            snap = get_home_layer1_snapshot(team_name)
        except Exception:
            return
        if not snap or not snap.get("game_found"):
            return
        status = str(snap.get("game_status") or "")
        if status not in ("scheduled", "starting soon", "live", "final"):
            return
    game = snap.get("game_row") or {}
    home = game.get("homeTeam") or {}
    away = game.get("awayTeam") or {}
    home_name = snap.get("home_team") or _live_team_full_name(_tricode_from_team_dict(home), home)
    away_name = snap.get("away_team") or _live_team_full_name(_tricode_from_team_dict(away), away)
    if team_name not in (home_name, away_name):
        return
    phase = snap.get("phase") or _live_broadcast_phase(game)
    countdown = snap.get("countdown") or ""
    sec = snap.get("seconds_to_tipoff")
    if (
        AUTOREFRESH_AVAILABLE
        and status in ("starting soon", "live")
        and not _live_gc_game_night_emergency_active()
    ):
        st_autorefresh(interval=45000 if status == "starting soon" else 30000, key=f"home_game_watch_refresh_{team_name}")

    series_line, _series_src = _live_series_board(away_name, home_name)
    mx = get_display_matchup(team_name)
    rnd = mx.get("round_short") or (game.get("seriesText") or "Playoffs")
    game_n = _live_gc_next_game_number(team_name)
    finals_tag = f" · Game {game_n}" if "Finals" in str(rnd) else ""

    if status == "live":
        title = f"LIVE NOW{finals_tag}"
        tone = "home-live-strip home-live-strip--live"
        score = f"{snap.get('away_score', 0)} — {snap.get('home_score', 0)}"
        subtitle = f"{away_name} @ {home_name} · {snap.get('game_status_text') or 'In progress'}"
        button_label = "Go to Live Game Center — LIVE NOW"
    elif status == "final":
        title = "FINAL IN THE FEED"
        tone = "home-live-strip home-live-strip--post"
        score = f"{snap.get('away_score', 0)} — {snap.get('home_score', 0)}"
        subtitle = f"{away_name} @ {home_name} · recap loading from live hub"
        button_label = "Go to Live Game Center — recap"
    elif status == "starting soon":
        title = f"GAME STARTING SOON{finals_tag}"
        tone = "home-live-strip home-live-strip--soon"
        score = f"Starts in {countdown}"
        subtitle = f"{away_name} @ {home_name} · {snap.get('game_status_text') or 'Tipoff approaching'}"
        button_label = f"{fan_nick(away_name)} vs {fan_nick(home_name)} — Starting Soon"
    else:
        title = f"GAME SCHEDULED TONIGHT{finals_tag}"
        tone = "home-live-strip"
        score = countdown or "Tipoff today"
        subtitle = f"{away_name} @ {home_name} · game scheduled today — live feed not detected yet"
        button_label = "Go to Live Game Center"

    if status == "live":
        badge = '<div class="home-live-badge">ON AIR · LIVE</div>'
    elif status == "starting soon":
        badge = '<div class="home-live-badge">TIPOFF SOON</div>'
    else:
        badge = ""
    st.markdown(
        f"""
<div class="{tone}">
  {badge}
  <div class="home-live-strip-title">{html.escape(title)}</div>
  <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
    <div style="text-align:center"><img src="{html.escape(TEAM_LOGOS.get(away_name, ''))}" width="58"/><div style="font-size:12px;font-weight:900">{html.escape(away_name)}</div></div>
    <div style="text-align:center;flex:1;min-width:220px">
      <div class="home-live-strip-score">{html.escape(score)}</div>
      <div class="home-live-strip-sub">{html.escape(subtitle)}</div>
      <div class="home-live-strip-sub">Round: {html.escape(str(rnd))} · Series: {html.escape(series_line or mx.get('series_record') or 'Knicks lead 1–0')}</div>
      <div class="home-live-strip-sub">Last: {html.escape(FINALS_GAME1_CANONICAL_SCORE)} · Source: {html.escape(str(snap.get('data_source') or 'scoreboard'))}</div>
    </div>
    <div style="text-align:center"><img src="{html.escape(TEAM_LOGOS.get(home_name, ''))}" width="58"/><div style="font-size:12px;font-weight:900">{html.escape(home_name)}</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button(button_label, key=f"home_current_game_open_{team_name}", type="primary"):
        st.session_state["page_override"] = "🔴 Live Game Center"
        st.session_state[f"live_gc__load_{team_name}"] = True
        st.rerun()

    with st.expander("Pregame context: injuries, key players, stakes", expanded=status in ("starting soon", "live")):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Expected key players**")
            for nm in (TEAM_PROFILES.get(team_name, {}).get("starters") or [])[:3]:
                st.write(f"• {nm}")
        with c2:
            opp = home_name if team_name == away_name else away_name
            st.markdown("**Opponent keys**")
            for nm in (TEAM_PROFILES.get(opp, {}).get("starters") or [])[:3]:
                st.write(f"• {nm}")
        with c3:
            st.markdown("**What is at stake**")
            st.write(f"• {series_line or 'Winner takes control of the live series math.'}")
            st.write("• The bracket should not crown anyone until the fourth win is final.")
        st.markdown("**Injury monitor**")
        inj_rows = (FALLBACK_INJURY_REPORT.get(team_name, []) or []) + (FALLBACK_INJURY_REPORT.get(home_name if team_name == away_name else away_name, []) or [])
        if inj_rows:
            st.dataframe(pd.DataFrame(inj_rows).head(6), use_container_width=True, hide_index=True)
        else:
            st.caption("No fallback injury rows stored; open Live Game Center for the full injury fetch.")


HOME_DASH_LIVE_UPDATES = "home_dash_live_updates"
HOME_DASH_LOAD_INJ = "home_dash_load_inj"
HOME_DASH_LOAD_STARS = "home_dash_load_stars"
HOME_DASH_LOAD_LEGACY = "home_dash_load_legacy"
LIVE_GC_VALIDATION_LOG_KEY = "live_gc_validation_log"


def _home_dashboard_fast_context(team_name):
    """Instant Home context (local series shell + no live scoreboard fetch)."""
    hctx = resolve_home_matchup_context_fast(team_name)
    s_active = _build_local_series_shell(team_name)
    pctx = build_dashboard_playoff_context(team_name, hctx, s_active, skip_live_fetch=True)
    return hctx, s_active, pctx


def _home_dashboard_live_data_bundle(team_name):
    """Network-heavy context for Home — resolve matchup + series in parallel, then merge scoreboard."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fh = ex.submit(resolve_home_matchup_context_fast, team_name)
        fs = ex.submit(lambda: series_for_team(team_name))
        hctx = fh.result(timeout=3.5)
        _k, s_active = fs.result(timeout=3.5)
    pctx = build_dashboard_playoff_context(team_name, hctx, s_active, skip_live_fetch=False)
    return hctx, s_active, pctx


def _home_dashboard_section_tick(section_ms, last_t, name):
    """Record ms since previous tick; returns updated last_t."""
    now = pytime.perf_counter()
    section_ms[name] = (now - last_t) * 1000.0
    return now


def _page_perf_begin(page_name):
    st.session_state[PAGE_PERF_KEY] = {
        "page": page_name,
        "t0": pytime.perf_counter(),
        "last_t": pytime.perf_counter(),
        "sections": {},
        "first_paint_ms": None,
        "total_ms": None,
    }


def _page_perf_tick(name):
    perf = st.session_state.get(PAGE_PERF_KEY)
    if not perf:
        return
    now = pytime.perf_counter()
    perf["sections"][name] = (now - perf["last_t"]) * 1000.0
    perf["last_t"] = now


def _page_perf_mark_first_paint():
    perf = st.session_state.get(PAGE_PERF_KEY)
    if not perf or perf.get("first_paint_ms") is not None:
        return
    perf["first_paint_ms"] = (pytime.perf_counter() - perf["t0"]) * 1000.0


def _page_perf_merge_sections(section_ms):
    if not section_ms:
        return
    perf = st.session_state.get(PAGE_PERF_KEY)
    if perf:
        perf["sections"].update(section_ms)


def _page_perf_finish():
    perf = st.session_state.get(PAGE_PERF_KEY)
    if perf:
        perf["total_ms"] = (pytime.perf_counter() - perf["t0"]) * 1000.0


def _page_perf_startup_tick(phase_name, t_ref):
    """Record main() startup phase ms into the active page perf bucket."""
    perf = st.session_state.get(PAGE_PERF_KEY)
    if not perf:
        return pytime.perf_counter()
    now = pytime.perf_counter()
    perf.setdefault("sections", {})[f"startup_{phase_name}"] = (now - t_ref) * 1000.0
    return now


def _render_page_perf_report(page_name, team_name=""):
    if not (globals().get("SHOW_PERF_DEBUG", False) or _validation_mode_active()):
        return
    perf = st.session_state.get(PAGE_PERF_KEY) or {}
    total_ms = perf.get("total_ms")
    if total_ms is None:
        total_ms = (pytime.perf_counter() - perf.get("t0", pytime.perf_counter())) * 1000.0
    fp_ms = perf.get("first_paint_ms")
    sections = perf.get("sections") or {}
    ranked = sorted(sections.items(), key=lambda kv: kv[1], reverse=True)
    title = "Ultra-fast validation timing" if _ultra_fast_active() else ("QA performance" if _qa_mode_active() else "Page performance")
    with st.expander(title, expanded=_validation_mode_active()):
        st.caption(f"**{html.escape(page_name)}** · {html.escape(team_name)}")
        st.caption(f"First paint: **{fp_ms:.0f} ms**" if fp_ms is not None else "First paint: (not marked — add hero/ribbon)")
        st.caption(f"Total render: **{total_ms:.0f} ms**")
        if _validation_mode_active():
            gates = _validation_gates_status()
            st.caption(
                "Gates: "
                + ", ".join(
                    k.replace("_", " ")
                    for k, v in gates.items()
                    if v and k not in ("qa_mode", "ultra_fast")
                )
            )
        if ranked:
            st.markdown("**Slowest sections (ms)**")
            for i, (name, ms) in enumerate(ranked[:5], 1):
                st.caption(f"{i}. {html.escape(name)} — **{ms:.0f}**")


def _validation_facts_block(team_name):
    stt = _get_validation_playoff_state()
    mx = get_display_matchup(team_name, stt)
    pst = get_team_playoff_status(team_name, stt)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Round", mx.get("round_short") or "—")
    c2.metric("Opponent", mx.get("opponent_nick") or "TBD")
    c3.metric("Series", mx.get("series_record") or "—")
    c4.metric("Status", mx.get("status_badge") or "—")
    st.caption(f"Data: demo playoff snapshot · source {pst.get('data_source', 'demo')}")


def _render_ultra_snapshot_home(team_name):
    _render_validation_mode_banner()
    ident = team_fan_identity(team_name)
    render_fan_page_hero(team_name, f"{fan_nick(team_name)} Playoff Pulse", ident["stakes"], "YOUR TEAM")
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state())
    _validation_facts_block(team_name)


def _render_ultra_snapshot_bracket(team_name):
    _render_validation_mode_banner()
    render_fan_page_hero(team_name, "Playoff Bracket", "Compact bracket facts for validation.", "YOUR TEAM")
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state())
    stt = _get_validation_playoff_state()
    st.dataframe(
        _bracket_fallback_dataframe(
            stt["east_fr"], stt["east_sr"], stt["west_sr"], stt["west_fr"],
            stt.get("east_cf") or {}, stt.get("west_cf") or {}, stt.get("finals") or {},
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_ultra_snapshot_lineups(team_name, profile):
    _render_validation_mode_banner()
    mx = get_display_matchup(team_name, _get_validation_playoff_state())
    render_fan_page_hero(team_name, "Matchup Lineups", f"{mx['round_short']} · {mx['team_nick']} vs {mx['opponent_nick']}", "MATCHUP BOARD")
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state())
    opp = profile.get("current_opponent") or mx.get("opponent") or "Opponent"
    for side, tm in ((fan_nick(team_name), team_name), (fan_nick(opp), opp)):
        board = CURRENT_PLAYOFF_LINEUPS.get(tm) or {}
        lineup = [board.get(s, "TBD") for s in LINEUP_SLOTS]
        st.markdown(f"**{html.escape(side)}:** " + " · ".join(html.escape(n) for n in lineup))


def _render_ultra_snapshot_tracker(team_name, profile):
    _render_validation_mode_banner()
    render_matchup_header(team_name)
    anchor = (profile.get("starters") or ["—"])[0]
    st.subheader(f"Player Playoff Tracker · {html.escape(anchor)}")
    st.caption("Ultra-fast: no game-log API or charts — expand for full tracker.")
    _validation_facts_block(team_name)


def _render_ultra_snapshot_legacy(team_name):
    _render_validation_mode_banner()
    render_matchup_header(team_name)
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state())
    st.subheader(f"Legacy Tracker · {fan_nick(team_name)}")
    st.caption("Ultra-fast: no game logs, Plotly, or simulator — expand for full legacy board.")
    _validation_facts_block(team_name)


def _render_ultra_snapshot_history(team_name):
    _render_validation_mode_banner()
    data = franchise_history_data(team_name)
    render_fan_page_hero(team_name, f"{fan_nick(team_name)} Franchise Playoff Legends", data.get("context", ""), "TEAM HISTORY LEADERS")
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state())
    for p in sorted(data.get("legends", []), key=lambda x: int(x.get("rank", 99)))[:6]:
        st.markdown(f"**{p.get('rank')}. {html.escape(p.get('name', ''))}** — {html.escape(p.get('tier', ''))}")


def _render_ultra_snapshot_previous(team_name):
    _render_validation_mode_banner()
    stt = _get_validation_playoff_state()
    profile = TEAM_PROFILES[team_name]
    render_fan_page_hero(team_name, "Playoff path so far", "Series results from demo snapshot.", "PLAYOFF HISTORY")
    render_playoff_matchup_ribbon(team_name, stt)
    for coll, label in (("first", "First Round"), ("second", "Second Round"), ("cf", "Conference Finals"), ("finals", "NBA Finals")):
        for _k, s in (stt.get(coll) or {}).items():
            if team_name not in (s.get("a"), s.get("b")):
                continue
            tw, ow, opp = _team_series_record(team_name, s)
            st.markdown(
                f"**{label}:** {tw}–{ow} vs {html.escape(fan_nick(opp))} · winner={html.escape(str(s.get('winner') or 'TBD'))}"
            )
    if not any(team_name in (s.get("a"), s.get("b")) for c in ("first", "second", "cf", "finals") for s in (stt.get(c) or {}).values()):
        st.caption(profile.get("first_round_result") or "No series shell for this team in snapshot.")


def _home_dashboard_perf_footer(
    t0, sections, fast_mode, api_calls, skipped_note="", section_ms=None
):
    import portfolio_polish as pp

    if pp.is_capture_mode(st):
        return
    if skipped_note:
        st.markdown(skipped_note, unsafe_allow_html=True)
    if not globals().get("SHOW_PERF_DEBUG", False):
        return
    elapsed_ms = (pytime.perf_counter() - t0) * 1000
    sec_txt = " → ".join(sections) if sections else "(none)"
    with st.expander("Page status (developer)", expanded=False):
        st.caption(f"Loaded in {elapsed_ms:.0f} ms.")
        st.caption("Quick view is on." if fast_mode else "Live view is on.")
        st.caption(f"Feed checks this run: {html.escape(str(api_calls))}")
        st.caption(f"Sections ready: {html.escape(sec_txt)}")
        if section_ms:
            ranked = sorted(section_ms.items(), key=lambda kv: kv[1], reverse=True)
            top3 = ranked[:3]
            st.markdown("**Top 3 slowest sections (ms)**")
            for i, (name, ms) in enumerate(top3, 1):
                st.caption(f"{i}. {html.escape(name)} — **{ms:.0f}** ms")
            if len(ranked) > 3:
                st.caption(
                    "Next: "
                    + ", ".join(f"{html.escape(k)}={v:.0f}" for k, v in ranked[3:6])
                )


def render_playoff_command_center(team_name):
    import portfolio_polish as pp
    import portfolio_demo as pdemo

    pdemo.apply_page_demo(st, "Home Dashboard")
    t0 = pytime.perf_counter()
    sections = []
    section_ms = {}
    _t_tick = t0
    if pp.is_screenshot_mode(st) or pp.is_demo_mode(st):
        pp.render_hero_banner(
            st,
            f"{fan_nick(team_name)} Playoff Command Center",
            "Live bracket context, matchup pulse, and fan-facing playoff intelligence.",
        )
    if not pp.is_screenshot_mode(st):
        pp.render_executive_summary(
            st,
            "Central playoff dashboard for your team — scores, matchup context, and next actions.",
            "Gives fans a single command center during the playoff run without hunting across pages.",
            "Hero matchup tile, live scoreboard hooks, emphasis cards, and quick navigation to bracket and games.",
        )
    if _validation_mode_active():
        _render_validation_mode_banner()
        st.session_state[HOME_DASH_LIVE_UPDATES] = False
    st.session_state.setdefault(HOME_DASH_LIVE_UPDATES, False)
    live_on = bool(st.session_state.get(HOME_DASH_LIVE_UPDATES, False))
    is_eliminated = _is_home_eliminated(team_name)
    if is_eliminated and st.session_state.get(HOME_DASH_LIVE_UPDATES):
        st.session_state[HOME_DASH_LIVE_UPDATES] = False
        live_on = False
    effective_live = live_on and not is_eliminated

    if not pp.is_capture_mode(st):
        ident = team_fan_identity(team_name)
        render_fan_page_hero(
            team_name,
            f"{fan_nick(team_name)} Playoff Pulse",
            f"{ident['stakes']} {ident['texture']}",
            "YOUR TEAM",
        )
    render_page_trust_strip("home", "Scores from the bracket engine · tiles are analyst-style briefing, not live play-by-play.")
    render_fan_product_shell_open()

    api_calls = 0
    skip_note = ""
    fast_hctx, fast_s, fast_p = _home_dashboard_fast_context(team_name)
    hero_slot = st.empty()
    emph_slot = st.empty()
    game_watch_slot = st.empty()
    hero_slot.markdown(
        _home_command_center_hero_html(team_name, fast_hctx, fast_p, injury_use_live=False),
        unsafe_allow_html=True,
    )
    emph_slot.markdown(_dashboard_emphasis_html(team_name, fast_p), unsafe_allow_html=True)
    sections.append("hero_first_paint")
    _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "hero_first_paint")

    if is_eliminated:
        st.success(
            f"**{fan_nick(team_name)} postmortem is live.** The run is over, so the page shifts from tonight's nerves to what this season means next."
        )
    if not pp.is_capture_mode(st):
        b1, b2, b3 = st.columns([1.35, 1.35, 1.1])
        with b1:
            if is_eliminated:
                st.caption(
                    "This team is in wrap-up mode. Open **Live Game Center** for games still being played."
                )
            elif st.button("Go live", key="home_btn_live_apis", disabled=live_on, help="Pull in the latest scoreboard and injury updates."):
                st.session_state[HOME_DASH_LIVE_UPDATES] = True
                st.rerun()
        with b2:
            if st.button("Back to quick view", key="home_btn_fast_mode", disabled=not live_on):
                st.session_state[HOME_DASH_LIVE_UPDATES] = False
                st.session_state.pop(HOME_DASH_LOAD_INJ, None)
                st.session_state.pop(HOME_DASH_LOAD_STARS, None)
                st.session_state.pop(HOME_DASH_LOAD_LEGACY, None)
                st.rerun()
        with b3:
            st.caption("Quick view" if not live_on else "Live feed on")

    _inject_home_command_center_css()
    sections.append("inject_css")

    if not is_eliminated and not _validation_mode_active() and not pp.skip_heavy_work(st):
        with game_watch_slot.container():
            render_home_current_game_card(team_name)
        sections.append("current_game_watch")
        _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "current_game_watch")
    else:
        sections.append("current_game_watch_skipped_eliminated")

    if is_eliminated:
        render_offseason_future_outlook_sections(team_name)
        sections.append("offseason_outlook_top")
        _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "offseason_outlook_top")

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
                "<div style='margin-top:8px;color:#fca5a5'><strong>Keeping the page fast.</strong> "
                "The live feed took too long, so the local game story stays on screen.</div>"
            )
        except Exception as exc:
            bundle = None
            skip_note = (
                "<div style='margin-top:8px;color:#fca5a5'><strong>Live feed did not load.</strong> "
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
            _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "live_bundle")
    else:
        sections.append("fast_path")

    profile = pctx["profile"]
    current_series_obj = None if hctx.get("advanced") else s_active

    if effective_live and isinstance(pctx.get("fb"), dict) and pctx["fb"].get("game"):
        render_home_live_hub_strip(team_name, pctx.get("fb"))
        sections.append("live_strip")
    elif effective_live:
        sections.append("live_strip_no_row")
    else:
        sections.append("live_strip_skipped_fast")

    sections.append("hero")
    sections.append("emphasis_strip")

    sec1_title = "1 · How the run ended" if is_eliminated else "1 · Where the series stands"
    if render_fan_section(
        sec1_title,
        "📊",
        caption="Series ledger and game log — scoreboard lives in the hero above.",
        tone="elim" if is_eliminated else "default",
    ):
        render_fan_section_open()
    snap_cols = st.columns(3)
    s_disp = hctx.get("series") or current_series_obj
    pst_home = get_team_playoff_status(team_name)
    snap_cols[0].metric("Seed", profile.get("seed", "—"))
    snap_cols[1].metric(
        "Current chapter",
        pst_home.get("current_round")
        or (s_disp or {}).get("round")
        or hctx.get("round_label")
        or profile.get("round", "—"),
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
        edge = "Tracking next tip" if effective_live else "Game log below"
    if is_eliminated:
        edge = "Offseason · roster, draft & cap"
    snap_cols[2].metric("Tonight's edge" if not is_eliminated else "Page focus", edge)
    s_table = hctx.get("series") or current_series_obj
    if s_table and s_table.get("games"):
        st.dataframe(
            pd.DataFrame(s_table["games"]),
            use_container_width=True,
            height=min(220, 38 + 28 * len(s_table["games"])),
        )
    elif hctx.get("advanced"):
        st.info((hctx.get("ctx") or {}).get("status_text", "Through the completed series — the next matchup is the focus now."))
    elif s_table and s_table.get("round") in ("Conference Finals", "NBA Finals"):
        st.caption("Conference Finals / Finals shell is live — game rows fill in as results post.")
    if not is_eliminated and current_series_obj:
        st.markdown(
            f'<div class="fan-storyline-bar">{html.escape(_home_series_storyline(team_name, current_series_obj, pctx))}</div>',
            unsafe_allow_html=True,
        )
    sections.append("series_board")
    _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "series_board")
    render_fan_section_close()

    if not is_eliminated:
        last_mvp, last_why, watch, watch_why, rising = _home_player_spotlight(
            team_name, current_series_obj, pctx
        )
        exc = _home_fan_excitement_cards(team_name, pctx, current_series_obj, hctx)
        watch_keys = _home_watch_next_keys(team_name, pctx, current_series_obj)

        if render_fan_section(
            "2 · Fan energy board",
            "🔥",
            caption="Why this series matters — each tile answers a different question (no scoreboard repeat).",
            tone="broadcast",
        ):
            render_fan_section_open()
        _render_fan_energy_grid([
            ("🎯", "Why is it unfolding this way?", _home_series_tactical_why(team_name, current_series_obj, pctx), "hot"),
            ("🔄", "What changed Game 1 → Game 2?", _home_game1_to_game2_shift(team_name, current_series_obj, pctx), "hot"),
            ("⚔️", "Biggest matchup advantage", _home_matchup_swing_line(team_name, pctx, current_series_obj), ""),
            ("🔥", "Who is under pressure?", _home_pressure_players_line(team_name, pctx, current_series_obj), "spotlight"),
            ("📋", "Coaching adjustment that matters", _home_coaching_adjustment_line(team_name, pctx, current_series_obj), ""),
            ("⭐", "Player to watch", f"{watch} — {watch_why}" if watch else "Rotation leader loads from curated board.", "spotlight"),
            ("📈", "Who is rising?", _home_rising_player_line(team_name, pctx, current_series_obj, rising), ""),
            ("🏛️", "Historical stakes", _home_franchise_stakes(team_name), ""),
            ("👀", "What should fans watch next?", _home_watch_next_brief(team_name, pctx, watch_keys), ""),
        ])
        if last_mvp:
            st.caption(f"**Last game standout:** {last_mvp} — _{last_why}_")
        sections.append("fan_energy_board")
        _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "fan_energy_board")
        render_fan_section_close()

        if render_fan_section(
            "3 · Keys for the next tip",
            "👀",
            caption="Three possessions to track — plus live runway when Go live is on.",
            tone="soon" if effective_live else "default",
        ):
            render_fan_section_open()
        for title, detail in watch_keys[1:]:
            st.markdown(f"- **{title}:** {detail}")
        if effective_live:
            live = pctx.get("live")
            if live:
                home = live.get("homeTeam", {}) or {}
                away = live.get("awayTeam", {}) or {}
                st.markdown(
                    f"**Runway:** **{_live_team_full_name(away.get('teamTricode',''), away)}** @ "
                    f"**{_live_team_full_name(home.get('teamTricode',''), home)}** · _{live.get('gameStatusText','')}_"
                )
            else:
                opp = hctx.get("opponent_display") if hctx.get("advanced") else profile.get("current_opponent")
                st.caption(
                    f"Next tip: {fan_nick(team_name)} vs {opp or 'opponent TBA'} — live feed loads when the board posts."
                )
        sections.append("watch_next")
        _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "watch_next")
        render_fan_section_close()

    if render_fan_section("6 · Who's available", "🩹", caption="Injury snapshot when live mode is on.", tone="default"):
        render_fan_section_open()
    if injury_live:
        df_inj, _ = get_injury_report(team_name)
        if df_inj is not None and not df_inj.empty:
            st.dataframe(df_inj.head(5), use_container_width=True, hide_index=True)
        else:
            st.caption("No injury rows in the merged feed yet.")
        sections.append("injury_snapshot_live")
    else:
        st.info(
            "Injuries stay tucked away in quick view. Tap **Go live** when you want the latest availability check."
        )
        sections.append("injury_snapshot_fast_placeholder")
    render_fan_section_close()

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
        hist = historic_series_context(team_name, current_series_obj)
        if not hist.empty:
            st.markdown(
                f"<div style='font-size:13px;color:#cbd5e1;line-height:1.45'>{hist.iloc[0].get('Historical Context','')}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("Historical matchup context loads when the bracket posts a comparable series.")

    def sec_legacy():
        anchor = pctx.get("flagship") or profile.get("starters", [""])[0]
        if anchor:
            logs = playoff_game_logs_for_player(anchor, CURRENT_NBA_SEASON, team_name)
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

    def sec_outlook_full():
        render_team_outlook(team_name, compact_home=False, series_obj=current_series_obj)

    _t_tick = _home_dashboard_section_tick(section_ms, _t_tick, "sections_1_to_5")
    with st.expander("Who's available", expanded=False):
        if st.button("Fetch injury report", key=f"home_fetch_inj_{team_name}"):
            st.session_state[HOME_DASH_LOAD_INJ] = True
            st.rerun()
        if st.session_state.get(HOME_DASH_LOAD_INJ):
            sec_injuries()
        else:
            st.caption("Tap **Fetch injury report** when you want the latest availability check.")

    with st.expander("Faces of the run", expanded=False):
        if st.button("Load players & photos", key=f"home_fetch_stars_{team_name}"):
            st.session_state[HOME_DASH_LOAD_STARS] = True
            st.rerun()
        if st.session_state.get(HOME_DASH_LOAD_STARS):
            sec_stars()
        else:
            st.caption("Tap once to bring in player cards and photos.")

    with st.expander("Historical matchup context", expanded=False):
        sec_momentum()

    with st.expander("Player Storylines", expanded=False):
        sec_stories()

    with st.expander("Full team outlook", expanded=False):
        sec_outlook_full()

    with st.expander("Player playoff receipts", expanded=False):
        if st.button("Load playoff game logs", key=f"home_fetch_legacy_{team_name}"):
            st.session_state[HOME_DASH_LOAD_LEGACY] = True
            st.rerun()
        if st.session_state.get(HOME_DASH_LOAD_LEGACY):
            sec_legacy()
        else:
            st.caption("Tap **Load playoff game logs** to see the deeper player ledger.")

    st.caption(
        f"Updated {datetime.now().strftime('%b %d %I:%M %p')} · Playoff story refreshes as new results land."
    )
    sections.append("footer_caption")
    render_playoff_state_debug_expander("home")
    sections.append("playoff_status_debug_optional")

    live_flag = bool(st.session_state.get(HOME_DASH_LIVE_UPDATES))
    perf_fast = (not live_flag) or is_eliminated
    if is_eliminated:
        api_display = "none in postmortem mode"
    elif live_flag and api_calls:
        api_display = "live feed checked"
    elif live_flag:
        api_display = "live feed missed"
    else:
        api_display = "quick view only"

    section_ms["page_total"] = (pytime.perf_counter() - t0) * 1000.0
    _page_perf_merge_sections(section_ms)
    render_fan_product_shell_close()
    _home_dashboard_perf_footer(
        t0,
        sections,
        fast_mode=perf_fast,
        api_calls=api_display,
        skipped_note=skip_note,
        section_ms=section_ms,
    )

def home_injury_opponents_from_home_ctx(team_name, hctx, s_active=None):
    """Opponent list for injury merge using existing Home context (avoids extra ``series_for_team``)."""
    eff = get_effective_team_profile(team_name)
    if not isinstance(hctx, dict):
        return eff.get("current_opponent")
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
    return eff.get("current_opponent")


def home_injury_opponents(team_name):
    ctx = next_round_context_for_team(team_name)
    if ctx and ctx.get("advanced"):
        return ctx.get("opponents", [])
    _, s = series_for_team(team_name)
    if s and s.get("round") in ("Conference Finals", "NBA Finals"):
        opp = s["b"] if team_name == s["a"] else s["a"]
        return [opp]
    return get_effective_team_profile(team_name).get("current_opponent")

def _first_round_synthetic_games(team_a, team_b):
    """First-round game rows from merged state, then static archive."""
    stt = get_merged_playoff_state()
    for s in (stt.get("first") or {}).values():
        if {s.get("a"), s.get("b")} == {team_a, team_b} and s.get("games"):
            return list(s["games"])
    return _static_first_round_games_for_pair(team_a, team_b)


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
    _page_perf_tick("bracket_start")
    if favorite_team:
        render_fan_page_hero(
            favorite_team,
            "Playoff Bracket",
            f"Full 2026 bracket — {fan_nick(favorite_team)} series highlighted in your colors.",
            "YOUR TEAM",
        )

    render_page_trust_strip("bracket")
    use_demo, api_on = get_playoff_refresh_settings()
    import portfolio_polish as _pp_bracket
    if (use_demo or api_on) and not _pp_bracket.skip_heavy_work(st):
        st.caption(f"Auto-refresh every {PLAYOFF_BRACKET_REFRESH_MS // 1000}s when sync is on.")
    render_playoff_matchup_ribbon(favorite_team, _get_validation_playoff_state() if _validation_mode_active() else None)
    _page_perf_tick("bracket_ribbon")
    stt = get_merged_playoff_state()
    _page_perf_tick("playoff_state")
    if _validation_page_deferred("bracket"):
        st.dataframe(
            _bracket_fallback_dataframe(
                stt["east_fr"], stt["east_sr"], stt["west_sr"], stt["west_fr"],
                stt.get("east_cf") or {}, stt.get("west_cf") or {}, stt.get("finals") or {},
            ),
            use_container_width=True,
            hide_index=True,
        )
        _validation_offer_full_page("bracket", label="Load full Playoff Bracket HTML")
        return
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
    render_playoff_state_debug_expander("bracket")


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
        if series_obj:
            st.markdown(
                f"<div class='big-status' style='margin:0 0 8px'>{series_status_text(team, series_obj)}</div>",
                unsafe_allow_html=True,
            )
            st.info(latest_game_note(team, series_obj))
        else:
            st.info("The current question is matchup prep: which strengths travel, which counters matter, and who drives the next round.")
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
            st.session_state["page_override"] = "🔴 Live Game Center"
            st.rerun()
    elif ph == "pregame" and fb.get("starting_soon"):
        st.warning(f"Starting soon: {matchup}")
        st.write(status)
        if st.button("Go to Live Game Center", key="countdown_open_pregame"):
            st.session_state["page_override"] = "🔴 Live Game Center"
            st.rerun()
    else:
        st.info(f"Upcoming: {matchup}")
        st.write(status)

def render_lineup_cards(team, box_df):
    alias=TEAM_ALIASES[team]
    lineup=estimated_lineup(box_df, alias, team)
    positions=list(LINEUP_SLOTS)
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
    stt = get_merged_playoff_state()
    candidates = []
    candidates.extend((stt.get("finals") or {}).values())
    candidates.extend((stt.get("cf") or {}).values())
    candidates.extend(stt["second"].values())
    candidates.extend(stt["first"].values())
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
            st.session_state["page_override"] = "🔴 Live Game Center"
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


def _broadcast_status_label(phase, status, snap=None):
    txt = str(status or "").strip()
    if phase == "live":
        lower = txt.lower()
        if "half" in lower:
            return "Halftime"
        return "Live Now"
    if phase == "postgame":
        return "Final"
    if snap and snap.get("game_status") == "starting soon":
        return "Starting Soon"
    return "Pregame"


def _broadcast_phase_class(phase, snap=None):
    if phase == "live":
        return "live"
    if phase == "postgame":
        return "final"
    if snap and snap.get("game_status") == "starting soon":
        return "soon"
    return "pregame"


def _broadcast_clock_label(parsed, snap=None):
    if parsed.get("phase") == "live":
        if parsed.get("period") and parsed.get("clock"):
            return f"Q{parsed['period']} · {parsed['clock']}"
        if parsed.get("period"):
            return f"Q{parsed['period']}"
    if parsed.get("phase") == "postgame":
        return "Final"
    if snap and snap.get("countdown"):
        return f"Tipoff in {snap.get('countdown')}"
    return parsed.get("status") or "Pregame"


def _box_stat(row, key):
    return safe_int((row or {}).get(key, 0))


def _shooting_line(row):
    fgm, fga = _box_stat(row, "FGM"), _box_stat(row, "FGA")
    tpm, tpa = _box_stat(row, "3PM"), _box_stat(row, "3PA")
    if fga:
        return f"{fgm}/{fga} FG · {tpm}/{tpa} 3P"
    return "shooting pending"


def _player_tile_html(row, team_name=None, badge=""):
    name = str((row or {}).get("Player") or "Player")
    pts, reb, ast = _box_stat(row, "PTS"), _box_stat(row, "REB"), _box_stat(row, "AST")
    stl, blk, tov = _box_stat(row, "STL"), _box_stat(row, "BLK"), _box_stat(row, "TO")
    pm = _box_stat(row, "+/-")
    badge_html = f"<div style='font-size:10px;font-weight:900;color:var(--team-primary);text-transform:uppercase'>{html.escape(badge)}</div>" if badge else ""
    return f"""
<div class="player-tile">
  <img src="{html.escape(headshot(name))}" alt=""/>
  <div style="flex:1;min-width:0">
    {badge_html}
    <div class="name">{html.escape(name)}</div>
    <div class="line">{pts} PTS · {reb} REB · {ast} AST · +/- {pm:+d}</div>
    <div class="line">{stl} STL · {blk} BLK · {tov} TO · {_shooting_line(row)}</div>
  </div>
</div>
"""


def _estimated_player_tile_html(name, badge="Estimated lineup"):
    return f"""
<div class="player-tile">
  <img src="{html.escape(headshot(name))}" alt=""/>
  <div style="flex:1;min-width:0">
    <div style='font-size:10px;font-weight:900;color:var(--team-primary);text-transform:uppercase'>{html.escape(badge)}</div>
    <div class="name">{html.escape(name)}</div>
    <div class="line">Projected active group · live on-court feed unavailable</div>
  </div>
</div>
"""


def _top_box_rows(box_df, alias, stat="PTS", limit=3):
    if box_df is None or box_df.empty or not alias:
        return []
    sub = box_df[box_df["Team"].astype(str) == str(alias)].copy()
    if sub.empty or stat not in sub.columns:
        return []
    sub[stat] = pd.to_numeric(sub[stat], errors="coerce").fillna(0)
    return sub.sort_values(stat, ascending=False).head(limit).to_dict("records")


def _render_broadcast_header(team_name, parsed, snap, series_line, prob):
    phase = parsed.get("phase")
    status_label = _broadcast_status_label(phase, parsed.get("status"), snap)
    status_cls = f" {_broadcast_phase_class(phase, snap)}"
    clock = _broadcast_clock_label(parsed, snap)
    source = str((snap or {}).get("data_source") or "scoreboard")
    st.markdown(
        f"""
<div class="broadcast-shell">
  <div class="broadcast-score-row">
    <div class="broadcast-team">
      <img src="{html.escape(TEAM_LOGOS.get(parsed['away_name'], ''))}" alt=""/>
      <div class="broadcast-team-name">{html.escape(parsed['away_name'])}</div>
    </div>
    <div style="text-align:center">
      <div class="broadcast-status{status_cls}">{html.escape(status_label)}</div>
      <div class="broadcast-main-score">{parsed['away_score']} - {parsed['home_score']}</div>
      <div class="broadcast-clock">{html.escape(clock)}</div>
      <div class="broadcast-sub">Series: {html.escape(series_line or 'updating')} · {html.escape(str(parsed.get('status') or ''))}</div>
    </div>
    <div class="broadcast-team">
      <img src="{html.escape(TEAM_LOGOS.get(parsed['home_name'], ''))}" alt=""/>
      <div class="broadcast-team-name">{html.escape(parsed['home_name'])}</div>
    </div>
  </div>
  <div class="broadcast-metrics">
    <div class="broadcast-metric"><div class="k">Win Probability</div><div class="v">{prob}%</div></div>
    <div class="broadcast-metric"><div class="k">Selected Team</div><div class="v">{html.escape(fan_nick(team_name))}</div></div>
    <div class="broadcast-metric"><div class="k">Margin</div><div class="v">{parsed['margin']:+d}</div></div>
    <div class="broadcast-metric"><div class="k">Feed</div><div class="v" style="font-size:1rem">{html.escape(source[:22])}</div></div>
  </div>
  <div class="broadcast-sub" style="text-align:center;margin-top:10px">Model starts with score margin, quarter, home/away, and seed strength; player-card sections add box-score context as it publishes.</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _win_probability_story(team_name, parsed, prob, box_df=None):
    nick = fan_nick(team_name)
    opp = fan_nick(parsed.get("opp_name"))
    margin = int(parsed.get("margin", 0))
    if margin < 0:
        need = abs(margin)
        return (
            f"{nick} trail by {need}. The path back starts with two clean defensive trips, no live-ball turnovers, "
            f"and cutting the gap under 10 before {opp} can set the half-court shell."
        )
    if margin > 0:
        return (
            f"{nick} lead by {margin}. The lead is only safe if the defensive glass holds and the offense avoids empty early-clock jumpers."
        )
    return f"{nick} and {opp} are even. The next 6-0 run probably decides who controls the substitutions."


def _live_gc_path_analysis(team_name, profile, parsed, prob):
    """Team-centric comeback or closeout analysis — no 'fan perspective' phrasing."""
    margin = int(parsed.get("margin", 0))
    period = safe_int(parsed.get("period", 1), 1)
    is_home = bool(parsed.get("is_fav_home"))
    prof = profile or TEAM_PROFILES.get(team_name) or {}
    strengths = prof.get("strengths") or []
    concerns = prof.get("concerns") or []
    nick = fan_nick(team_name)
    opp = fan_nick(parsed.get("opp_name"))

    if margin < 0:
        st.markdown(f"#### What's still working")
        for s in strengths[:3]:
            st.markdown(f"- {s}")
        st.markdown(f"#### What must improve")
        for c in concerns[:3]:
            st.markdown(f"- {c}")
        st.markdown(f"#### Win probability if the deficit shrinks")
        rows = []
        for target in (-15, -10, -5, 0):
            if target > margin:
                label = f"Cut deficit to {abs(target)}" if target else "Tie the game"
                rows.append({"Scenario": label, "Model win %": f"{win_prob(target, period, is_home)}%"})
        if rows:
            render_fan_stat_table(pd.DataFrame(rows), team_name)
        st.caption(f"The model still gives {nick} a path if stops stack and the margin moves toward even before {opp} can slow the pace.")
    elif margin > 0:
        st.markdown(f"#### What's working")
        for s in strengths[:3]:
            st.markdown(f"- {s}")
        st.markdown(f"#### Win probability if the lead grows")
        rows = []
        for target in (10, 15, 20, 25):
            if target > margin:
                rows.append({"Scenario": f"Grow lead to {target}", "Model win %": f"{win_prob(target, period, is_home)}%"})
        if rows:
            render_fan_stat_table(pd.DataFrame(rows), team_name)
        st.markdown(f"#### What to avoid")
        for c in concerns[:3]:
            st.markdown(f"- {c}")
        st.caption(f"A {margin}-point cushion helps, but {nick} only protect it with disciplined closeouts and zero live-ball turnovers.")
    else:
        st.markdown(f"#### Even game — keys on both sides")
        for s in strengths[:2]:
            st.markdown(f"- Working: {s}")
        for c in concerns[:2]:
            st.markdown(f"- Watch: {c}")
        st.caption(f"{nick} and {opp} are tied — the next run probably decides who controls the rotation.")


def _live_gc_fetch_box_df_cached(gid, section_ms):
    """Fetch box score once per tab visit; traced in section_ms."""
    if not gid:
        return pd.DataFrame()
    t0 = pytime.perf_counter()
    try:
        box_game = _live_gc_fetch_boxscore(gid)
        box_df = create_boxscore_df(box_game) if box_game else pd.DataFrame()
    except Exception:
        box_df = pd.DataFrame()
    section_ms["boxscore"] = (pytime.perf_counter() - t0) * 1000.0
    return box_df


def _live_gc_fetch_actions_cached(gid, section_ms):
    if not gid:
        return []
    t0 = pytime.perf_counter()
    try:
        actions = _live_gc_fetch_playbyplay(gid) or []
    except Exception as exc:
        _live_gc_log_error(section_ms.setdefault("layer3_errors", []), "playbyplay", exc)
        actions = []
    section_ms["playbyplay"] = (pytime.perf_counter() - t0) * 1000.0
    return actions


def _render_live_gc_tabbed_sections(team_name, profile, parsed, state, prob, section_ms):
    """Tabbed Live Game Center — heavy API calls only inside the selected tab."""
    gid = parsed.get("gid") or ""
    can_fetch = bool(gid and not str(gid).startswith(("fallback-", "manual-")))
    tab_opts = [
        "Live Score",
        "Win Probability",
        "Box Score",
        "Shot Chart",
        "Top Plays",
        "Injuries / Foul Trouble",
        "Keys to Success",
    ]
    selected = st.radio(
        "Live Game Center sections",
        tab_opts,
        horizontal=True,
        key=f"live_gc_tab_{team_name}_{gid or 'local'}",
        label_visibility="collapsed",
    )
    st.caption("Scoreboard stays pinned above — detailed stats load only in the tab you open.")

    game_row = state.get("game_row") or {}
    actions_inline = game_row.get("actions") or [] if isinstance(game_row, dict) else []

    if selected == "Live Score":
        top = state.get("top_scorer")
        if top and top.get("name"):
            st.markdown(
                _player_tile_html(
                    {"Player": top["name"], "PTS": top["pts"], "REB": top.get("reb", 0), "AST": top.get("ast", 0)},
                    badge="Game leader (CDN)",
                ),
                unsafe_allow_html=True,
            )
        if parsed.get("phase") == "live":
            st.info(_live_headline_natural(
                team_name, parsed["phase"], parsed["margin"], prob, parsed["period"],
                parsed["status"], fan_nick(parsed["opp_name"]),
            ))
        if actions_inline:
            run_txt = _scoring_run_summary(actions_inline, parsed.get("fav_alias"), window=40)
            if run_txt:
                st.caption(run_txt)
        with st.expander("Rotation estimate", expanded=False):
            _render_lineup_board(team_name, parsed["opp_name"], pd.DataFrame())
        with st.expander("Series & bracket context", expanded=False):
            _live_gc_bracket_context_expander_body(team_name)

    elif selected == "Win Probability":
        st.markdown("<div class='broadcast-grid'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            _render_probability_command(team_name, parsed, prob, box_df=None)
        with c2:
            _render_live_matchup_swing(team_name, parsed["opp_name"], None, parsed)
        st.markdown("</div>", unsafe_allow_html=True)

    elif selected == "Box Score":
        if not can_fetch:
            st.caption(_live_gc_fan_msg("detail_unavailable"))
            _render_lineup_board(team_name, parsed["opp_name"], pd.DataFrame())
            return
        box_df = _live_gc_fetch_box_df_cached(gid, section_ms)
        if box_df is not None and not box_df.empty:
            _render_styled_box_score(team_name, parsed["opp_name"], box_df)
            _render_top_performer_cards(team_name, parsed["opp_name"], box_df)
        else:
            st.caption("Box score has not published yet — check back after the first timeout.")

    elif selected == "Shot Chart":
        if not can_fetch:
            st.caption(_live_gc_fan_msg("detail_unavailable"))
            return
        actions = _live_gc_fetch_actions_cached(gid, section_ms)
        if not actions:
            st.caption("Play-by-play has not published yet.")
            return
        try:
            shots = shot_df_from_pbp(actions, parsed["fav_alias"])
            if not shots.empty:
                st.plotly_chart(draw_court(shots, f"{fan_nick(team_name)} shot chart"), use_container_width=True)
            else:
                st.caption("Shot locations populate when the action feed includes make/miss coordinates.")
        except Exception as exc:
            _live_gc_log_error(section_ms.setdefault("layer3_errors", []), "shot_chart", exc)
            st.caption(_live_gc_fan_msg("detail_unavailable"))

    elif selected == "Top Plays":
        if not can_fetch:
            plays = FALLBACK_TOP_PLAYS.get(team_name, [])[:6]
            if plays:
                st.dataframe(pd.DataFrame(plays), use_container_width=True, hide_index=True)
            else:
                st.caption("Top plays populate when play-by-play is available.")
            return
        actions = _live_gc_fetch_actions_cached(gid, section_ms)
        if actions:
            try:
                tp = _top_plays_from_actions(actions, team_name, limit=10)
                if tp is not None and not tp.empty:
                    st.dataframe(tp, use_container_width=True, hide_index=True)
                else:
                    st.caption("Highlight tags have not appeared in the feed yet.")
            except Exception as exc:
                _live_gc_log_error(section_ms.setdefault("layer3_errors", []), "top_plays", exc)
                st.caption(_live_gc_fan_msg("detail_unavailable"))
        else:
            st.caption("Play-by-play has not published yet.")

    elif selected == "Injuries / Foul Trouble":
        if can_fetch:
            box_df = _live_gc_fetch_box_df_cached(gid, section_ms)
            st.markdown("#### Foul trouble")
            _live_gc_foul_trouble(box_df, team_name, parsed["opp_name"])
        else:
            st.caption("Foul trouble updates when the box score publishes.")
        st.markdown("#### Injury report")
        try:
            c1, c2 = st.columns(2)
            with c1:
                render_injury_report(
                    team_name,
                    opponent_name=parsed["opp_name"],
                    show_page_header=False,
                    fan_perspective_team=team_name,
                    neutral_framing=True,
                )
            with c2:
                if parsed.get("opp_name"):
                    render_injury_report(
                        parsed["opp_name"],
                        show_page_header=False,
                        neutral_framing=True,
                    )
        except Exception as exc:
            _live_gc_log_error(section_ms.setdefault("layer3_errors", []), "injuries", exc)
            st.caption(_live_gc_fan_msg("detail_unavailable"))

    elif selected == "Keys to Success":
        _live_gc_path_analysis(team_name, profile, parsed, prob)
        st.markdown("---")
        st.markdown("#### Current keys to the game")
        if parsed.get("phase") == "live":
            st.markdown(
                f"<div class='broadcast-card dark'><div style='font-size:14px;line-height:1.55'>"
                f"{html.escape(_live_headline_natural(team_name, parsed['phase'], parsed['margin'], prob, parsed['period'], parsed['status'], fan_nick(parsed['opp_name'])))}"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        for line in game_story(team_name, parsed["margin"], prob, pd.DataFrame()):
            st.write(f"• {line}")


def _render_probability_command(team_name, parsed, prob, box_df=None):
    margin = int(parsed.get("margin", 0))
    period = safe_int(parsed.get("period", 1), 1)
    is_home = bool(parsed.get("is_fav_home"))
    st.markdown(
        f"""
<div class="broadcast-card">
  <div class="broadcast-card-title">Win Probability Command Center</div>
  <div style="font-size:1.8rem;font-weight:950;color:#0f172a">{prob}%</div>
  <div class="prob-bar"><span style="width:{max(1, min(99, prob))}%"></span></div>
  <div style="font-size:13px;color:#334155;line-height:1.45">{html.escape(_win_probability_story(team_name, parsed, prob, box_df))}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    scenario_rows = []
    if margin < 0:
        for target in [-15, -10, -5, 0]:
            if target > margin:
                scenario_rows.append({"Scenario": f"Cut deficit to {abs(target)}" if target else "Tie the game", "Model win %": f"{win_prob(target, period, is_home)}%", "Margin": target})
    else:
        for target in [10, 15, 20, 25, 30]:
            if target > margin:
                scenario_rows.append({"Scenario": f"Grow lead to {target}", "Model win %": f"{win_prob(target, period, is_home)}%", "Margin": target})
    if scenario_rows:
        render_fan_stat_table(pd.DataFrame(scenario_rows), team_name)


def _render_top_performer_cards(team_name, opp_name, box_df):
    fav_alias = TEAM_ALIASES.get(team_name, "")
    opp_alias = TEAM_ALIASES.get(opp_name, "")
    st.markdown('<div class="broadcast-grid">', unsafe_allow_html=True)
    cols = st.columns(2)
    for col, label, alias in ((cols[0], fan_nick(team_name), fav_alias), (cols[1], fan_nick(opp_name), opp_alias)):
        with col:
            rows = _top_box_rows(box_df, alias, "PTS", 3)
            st.markdown(f"<div class='broadcast-card-title'>{html.escape(label)} top performers</div>", unsafe_allow_html=True)
            if rows:
                for idx, row in enumerate(rows, start=1):
                    st.markdown(_player_tile_html(row, badge="Leading scorer" if idx == 1 else "Box score leader"), unsafe_allow_html=True)
            else:
                names = estimated_starters_from_api(team_name if alias == fav_alias else opp_name)[:3]
                for nm in names:
                    st.markdown(_estimated_player_tile_html(nm, "Projected key player"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_lineup_board(team_name, opp_name, box_df):
    fav_alias = TEAM_ALIASES.get(team_name, "")
    opp_alias = TEAM_ALIASES.get(opp_name, "")
    cols = st.columns(2)
    for col, label, alias, tm in ((cols[0], fan_nick(team_name), fav_alias, team_name), (cols[1], fan_nick(opp_name), opp_alias, opp_name)):
        with col:
            st.markdown(f"<div class='broadcast-card-title'>{html.escape(label)} lineup</div>", unsafe_allow_html=True)
            lineup = estimated_lineup(box_df if box_df is not None else pd.DataFrame(), alias, tm)
            is_est = box_df is None or box_df.empty
            if lineup is not None and not lineup.empty:
                for _, row in lineup.head(5).iterrows():
                    if is_est:
                        st.markdown(_estimated_player_tile_html(str(row.get("Player", ""))), unsafe_allow_html=True)
                    else:
                        st.markdown(_player_tile_html(row, badge="Active rotation estimate"), unsafe_allow_html=True)
            else:
                st.caption("Lineup estimate unavailable.")


def _render_styled_box_score(team_name, opp_name, box_df):
    if box_df is None or box_df.empty:
        st.caption("Box score has not published yet.")
        return
    leaders = []
    for stat, label in [("PTS", "Scoring"), ("REB", "Rebounding"), ("AST", "Playmaking"), ("+/-", "Plus-minus")]:
        if stat in box_df.columns:
            tmp = box_df.copy()
            tmp[stat] = pd.to_numeric(tmp[stat], errors="coerce").fillna(0)
            r = tmp.sort_values(stat, ascending=False).iloc[0]
            leaders.append({"Category": label, "Leader": r.get("Player", ""), "Team": r.get("Team", ""), "Value": safe_int(r.get(stat))})
    if leaders:
        render_fan_stat_table(pd.DataFrame(leaders), team_name)
    show_cols = [c for c in ["Team", "Player", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TO", "PF", "FGM", "FGA", "3PM", "3PA", "+/-"] if c in box_df.columns]
    render_fan_stat_table(box_df[show_cols].sort_values(["Team", "PTS"], ascending=[True, False]), team_name)


def _render_live_matchup_swing(team_name, opp_name, box_df, parsed):
    nick = fan_nick(team_name)
    opp_nick = fan_nick(opp_name)
    if box_df is None or box_df.empty:
        st.markdown(
            f"<div class='broadcast-card'><div class='broadcast-card-title'>Key Matchup Swing</div>"
            f"<div style='font-size:13px;color:#334155;line-height:1.45'>{html.escape(nick)} need the first clean run from the starting group. The live box score will identify whether guard creation, rebounding, or turnovers are driving the game once player rows publish.</div></div>",
            unsafe_allow_html=True,
        )
        return
    alias = TEAM_ALIASES.get(team_name, "")
    opp_alias = TEAM_ALIASES.get(opp_name, "")
    fav = box_df[box_df["Team"] == alias]
    opp = box_df[box_df["Team"] == opp_alias]
    fav_to = pd.to_numeric(fav.get("TO", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    opp_to = pd.to_numeric(opp.get("TO", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    fav_reb = pd.to_numeric(fav.get("REB", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    opp_reb = pd.to_numeric(opp.get("REB", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    if fav_to > opp_to + 2:
        text = f"{nick} are leaking possessions. The fastest path to stabilizing is fewer live-ball turnovers and a simpler first action."
    elif fav_reb < opp_reb - 4:
        text = f"{opp_nick} are tilting the glass. {nick} need gang rebounding before the transition game can breathe."
    elif parsed.get("margin", 0) >= 0:
        text = f"{nick} are holding the scoreboard position. Keep forcing contested half-court looks and avoid bailout fouls."
    else:
        text = f"{nick} need a cleaner two-way stretch: one stop chain, one paint touch, one open three."
    st.markdown(
        f"<div class='broadcast-card'><div class='broadcast-card-title'>Key Matchup Swing</div>"
        f"<div style='font-size:13px;color:#334155;line-height:1.45'>{html.escape(text)}</div></div>",
        unsafe_allow_html=True,
    )


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
    if not render_fan_section(title, icon, tone="broadcast"):
        return
    render_fan_section_open()
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        st.caption(f"{title} could not load right now ({exc}).")
    render_fan_section_close()


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


def _render_live_game_center_previous(favorite_team, profile):
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

        if can_show_developer_tools(st=st):
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

    if can_show_developer_tools(st=st):
        with st.expander("Developer debug", expanded=False):
            _live_gc_render_debug_panel(favorite_team, fb, det_ctx)



# ==========================================================
# Previous rounds / playoff path helpers
# ==========================================================
FALLBACK_GAME_MVPS = {
    ("New York Knicks", "Atlanta Hawks", 1): ("Jalen Brunson", "Controlled the half court and gave New York the Game 1 tone."),
    ("New York Knicks", "Atlanta Hawks", 2): ("Jalen Johnson", "Late-game shot creation and pressure helped Atlanta steal a road game."),
    ("New York Knicks", "Atlanta Hawks", 3): ("Jalen Johnson", "Carried Atlanta's offense in a one-possession finish."),
    ("New York Knicks", "Cleveland Cavaliers", 1): ("Jalen Brunson", "Set the tone with half-court control in the East finals opener."),
    ("New York Knicks", "Cleveland Cavaliers", 2): ("Jalen Brunson", "Extended the Knicks' control on the road in Game 2."),
    ("New York Knicks", "Cleveland Cavaliers", 3): ("Karl-Anthony Towns", "Spacing and interior scoring broke Cleveland's help rules."),
    ("New York Knicks", "Cleveland Cavaliers", 4): ("Jalen Brunson", "Closed the East with late-clock poise in the sweep."),
    ("New York Knicks", "Atlanta Hawks", 4): ("Jalen Brunson", "Reset the series for New York with stronger offensive control."),
    ("New York Knicks", "Atlanta Hawks", 5): ("Karl-Anthony Towns", "Spacing and scoring changed the geometry of the Knicks offense."),
    ("New York Knicks", "Atlanta Hawks", 6): ("Jalen Brunson", "Closed the series with lead-guard control and playoff poise."),
    ("New York Knicks", "Philadelphia 76ers", 1): ("Jalen Brunson", "Set the pace for New York's second-round opener."),
    ("New York Knicks", "Philadelphia 76ers", 2): ("Jalen Brunson", "Protected the late-game margin and pushed the Knicks to a 2-0 series edge."),
    ("New York Knicks", "San Antonio Spurs", 1): ("Jalen Brunson", "Set the Finals tone with late-clock poise and a fourth-quarter pullaway at the Garden."),
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

def _eligible_standout_players_for_team(team_name):
    """Active rotation names eligible for game standout credit on ``team_name``."""
    pool, seen = [], set()
    curated = CURRENT_PLAYOFF_LINEUPS.get(team_name) or {}
    for slot in LINEUP_SLOTS:
        name = curated.get(slot)
        if name and not _is_outdated_playoff_player(name, team_name):
            k = _player_name_key(name)
            if k not in seen:
                seen.add(k)
                pool.append(name)
    for name in curated.get("bench") or []:
        if name and not _is_outdated_playoff_player(name, team_name):
            k = _player_name_key(name)
            if k not in seen:
                seen.add(k)
                pool.append(name)
    prof = TEAM_PROFILES.get(team_name) or {}
    for name in (prof.get("starters") or []) + (prof.get("subs") or []):
        if name and not _is_outdated_playoff_player(name, team_name):
            k = _player_name_key(name)
            if k not in seen:
                seen.add(k)
                pool.append(name)
    return pool


def _standout_player_team(name, team_a, team_b):
    if _player_name_key(name) in {_player_name_key(p) for p in _eligible_standout_players_for_team(team_a)}:
        return team_a
    if _player_name_key(name) in {_player_name_key(p) for p in _eligible_standout_players_for_team(team_b)}:
        return team_b
    return None


def _validate_game_standout_candidate(name, team_a, team_b, winner=None):
    """Game standout must be active on a participating team; prefer the winning side."""
    credited = _standout_player_team(name, team_a, team_b)
    if not credited:
        return False
    if winner in (team_a, team_b) and credited != winner:
        return False
    return True


def mvp_for_game(team_a, team_b, game_num, winner=None):
    win_team = winner if winner in (team_a, team_b) else None
    for key in [(team_a, team_b, game_num), (team_b, team_a, game_num)]:
        if key in FALLBACK_GAME_MVPS:
            name, why = FALLBACK_GAME_MVPS[key]
            if _validate_game_standout_candidate(name, team_a, team_b, win_team):
                return name, why
    if win_team:
        pool = _eligible_standout_players_for_team(win_team)
        if pool:
            return pool[0], f"Rotation leader credited for {win_team} in this result."
    return "", ""


def _sanitize_standout_fields(team_a, team_b, game_num, winner, mvp, why):
    """Drop invented standouts; keep only roster-valid names on the winning team."""
    if mvp and _validate_game_standout_candidate(mvp, team_a, team_b, winner if winner in (team_a, team_b) else None):
        return mvp, why or ""
    fresh_mvp, fresh_why = mvp_for_game(team_a, team_b, game_num, winner)
    return fresh_mvp, fresh_why

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
        mvp, why = _sanitize_standout_fields(a, b, idx, row.get("Winner"), row.get("Game MVP"), row.get("MVP Note"))
        if not mvp:
            mvp, why = mvp_for_game(team_name, opp, idx, row.get("Winner"))
        row["Game MVP"] = mvp
        row["MVP Note"] = why
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
        mvp, why = _sanitize_standout_fields(
            team_a, team_b, n, g.get("Winner"), g.get("Game MVP"), g.get("MVP Note")
        )
        if not mvp:
            mvp, why = mvp_for_game(team_a, team_b, n, g.get("Winner"))
        standout_line = f"Game standout: {mvp}" if mvp else "Game standout: not assigned"
        why_line = f"<br><span style='color:#475569'>{why}</span>" if why else ""
        st.markdown(
            f"<div class='game-row'><b>{game_num}</b> · {g.get('Date','Date TBD')} · {g.get('Matchup', team_a+' vs '+team_b)}"
            f"<br><b>Score:</b> {g.get('Score','Score TBD')}<br><span class='mvp-pill'>{standout_line}</span>{why_line}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

def render_previous_rounds_history(team_name):
    if _ultra_fast_active() and _validation_page_deferred("previous_rounds"):
        _render_ultra_snapshot_previous(team_name)
        _validation_offer_full_page("previous_rounds", label="Load full Previous Rounds cards")
        return
    _page_perf_tick("previous_start")
    if _validation_mode_active():
        _render_validation_mode_banner()
    profile = TEAM_PROFILES[team_name]
    stt = get_merged_playoff_state()
    _page_perf_tick("playoff_state")
    render_fan_page_hero(team_name, "Playoff path so far", "Every round you played — scores, MVPs, and series results.", "PLAYOFF HISTORY")
    render_page_trust_strip("previous_rounds")
    render_playoff_matchup_ribbon(team_name, stt)
    if _validation_page_deferred("previous_rounds"):
        for coll, label in (("first", "First Round"), ("second", "Second Round"), ("cf", "Conference Finals"), ("finals", "NBA Finals")):
            for _k, s in (stt.get(coll) or {}).items():
                if team_name not in (s.get("a"), s.get("b")):
                    continue
                tw, ow, opp = _team_series_record(team_name, s)
                st.markdown(
                    f"**{label}:** {tw}–{ow} vs {html.escape(fan_nick(opp))} · winner={html.escape(str(s.get('winner') or 'TBD'))}"
                )
        _validation_offer_full_page("previous_rounds", label="Load full Previous Rounds cards")
        return
    if render_fan_section("Round-by-round results", "📜", caption="Every series you played this postseason."):
        render_fan_section_open()
    fr_shell = None
    for _k, s in (stt.get("first") or {}).items():
        if team_name in (s.get("a"), s.get("b")):
            fr_shell = s
            break
    if fr_shell:
        first_opp = fr_shell["b"] if team_name == fr_shell["a"] else fr_shell["a"]
        first_games = _series_games_for_history(team_name, fr_shell)
        fr_note = (
            f"{fr_shell.get('winner')} wins the series."
            if _series_has_confirmed_winner(fr_shell)
            else profile.get("first_round_result")
        )
        render_series_history_card(team_name, first_opp, first_games, "First Round", fr_note)
    else:
        first_opp = profile["first_round_opponent"]
        first_games = _series_games_for_history(team_name, {"a": team_name, "b": first_opp, "games": _static_first_round_games_for_pair(team_name, first_opp)})
        render_series_history_card(team_name, first_opp, first_games, "First Round", profile.get("first_round_result"))

    _, s2 = second_round_series_for_team(team_name)
    if s2 and s2.get("games"):
        opp2 = s2["b"] if team_name == s2["a"] else s2["a"]
        second_games = get_current_series_games_for_previous_rounds(team_name)
        sr_note = f"{s2['winner']} wins the series." if s2.get("winner") else None
        render_series_history_card(team_name, opp2, second_games, "Second Round", sr_note)

    for round_label, coll in (("Conference Finals", stt.get("cf") or {}), ("NBA Finals", stt.get("finals") or {})):
        for _k, s in (coll or {}).items():
            if team_name not in (s.get("a"), s.get("b")):
                continue
            opp = s["b"] if team_name == s["a"] else s["a"]
            games = _series_games_for_history(team_name, s)
            if not games:
                continue
            note = f"{s.get('winner')} wins the {round_label}." if s.get("winner") else None
            render_series_history_card(team_name, opp, games, round_label, note)
    render_fan_section_close()


# ==========================================================
# Fail-safe Live Game Center override
# ==========================================================
def _local_live_gc_series_context(team_name, profile):
    """Layer 1 context from merged playoff state (cached API + fallback)."""
    pst = get_team_playoff_status(team_name)
    opp = pst.get("current_opponent") or profile.get("current_opponent") or ""
    round_name = pst.get("current_round") or profile.get("round") or "Playoffs"
    series = pst.get("series")
    if not series:
        _k, series = series_for_team(team_name)
    if series:
        a, b = series.get("a"), series.get("b")
        opp = b if team_name == a else a
        tw = series.get("a_wins", 0) if team_name == a else series.get("b_wins", 0)
        ow = series.get("b_wins", 0) if team_name == a else series.get("a_wins", 0)
        series_text = f"{fan_nick(team_name)} {tw} - {ow} {fan_nick(opp)}"
        return opp, round_name, series_text, series.get("source", "local bracket shell")
    series_text = f"{fan_nick(team_name)} vs {fan_nick(opp) if opp else 'Opponent'}"
    return opp, round_name, series_text, "local profile"


def _render_live_gc_layer1(team_name, profile):
    """Legacy local shell. Kept for fallback/debug, not the primary broadcast view."""
    opp, round_name, series_text, source = _local_live_gc_series_context(team_name, profile)
    logo = TEAM_LOGOS.get(team_name, "")
    opp_logo = TEAM_LOGOS.get(opp, "") if opp else ""
    st.markdown(
        f"""
<div class="live-gc-board">
  <div style="text-align:center">
    <img src="{html.escape(logo)}" alt=""/>
    <div style="font-size:12px;font-weight:900">{html.escape(team_name)}</div>
  </div>
  <div style="text-align:center;min-width:220px">
    <div style="font-size:11px;color:#94a3b8;font-weight:900;letter-spacing:.12em">GAME ROOM</div>
    <div class="live-gc-score">{html.escape(series_text)}</div>
    <div class="live-gc-clock">{html.escape(round_name)} · source: {html.escape(source)}</div>
  </div>
  <div style="text-align:center">
    <img src="{html.escape(opp_logo)}" alt=""/>
    <div style="font-size:12px;font-weight:900">{html.escape(opp or 'Opponent')}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected team", fan_nick(team_name))
    c2.metric("Opponent", fan_nick(opp) if opp else "TBD")
    c3.metric("Round", round_name)
    c4.metric("Game room", "open")
    st.caption("Local matchup shell. Live broadcast details appear above when a scoreboard row is available.")
    return opp, round_name, series_text, source


def _live_gc_fetch_boxscore(game_id):
    """Box score fetch with optional timing trace (deferred — not on scoreboard critical path)."""
    if not game_id:
        return {}
    before = _cache_data_fingerprint(get_live_boxscore) if _live_gc_debug_enabled() else None
    t0 = pytime.perf_counter()
    data = get_live_boxscore(game_id) or {}
    if _live_gc_debug_enabled():
        after = _cache_data_fingerprint(get_live_boxscore)
        cache_hit = bool(before and after and after.get("hits", 0) > before.get("hits", 0))
        _live_gc_trace(
            "live_boxscore",
            game_id=str(game_id),
            ms=round((pytime.perf_counter() - t0) * 1000.0, 1),
            cache_hit=cache_hit,
            status="empty" if not data else "ok",
        )
    return data


def _live_gc_fetch_playbyplay(game_id):
    if not game_id:
        return []
    before = _cache_data_fingerprint(get_live_playbyplay) if _live_gc_debug_enabled() else None
    t0 = pytime.perf_counter()
    actions = get_live_playbyplay(game_id) or []
    if _live_gc_debug_enabled():
        after = _cache_data_fingerprint(get_live_playbyplay)
        cache_hit = bool(before and after and after.get("hits", 0) > before.get("hits", 0))
        _live_gc_trace(
            "live_playbyplay",
            game_id=str(game_id),
            ms=round((pytime.perf_counter() - t0) * 1000.0, 1),
            cache_hit=cache_hit,
            count=len(actions),
        )
    return actions


def _render_live_gc_debug(team_name, opp, layer1_loaded, live_attempted=False, live_count=None, errors=None, state=None, section_ms=None, force=False):
    """Live Game Center diagnostics — no extra API calls; reads session trace + cache stats."""
    if not force and not globals().get("SHOW_PERF_DEBUG", False):
        return
    errors = errors or []
    section_ms = section_ms or {}
    state = state or {}
    snap = state.get("snap") or {}
    with st.expander("Live Game Center diagnostics (developer)", expanded=False):
        st.markdown(
            "**Real-game checklist (verify in browser during a live game):** "
            "score at top · quarter/clock · source · last updated · no fake 0–0 · "
            "page stays responsive on auto-refresh · Layer 2/3 only after buttons."
        )
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Selected team", team_name)
        d2.metric("Alias", TEAM_ALIASES.get(team_name, "—"))
        d3.metric("Opponent", opp or "TBD")
        d4.metric("Resolve priority", state.get("priority") or "—")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("CDN games", "—" if live_count is None else str(live_count))
        e2.metric("Detection tier", snap.get("detection_tier") or "—")
        e3.metric("Data source", str(snap.get("data_source") or state.get("source_label") or "—")[:20])
        e4.metric("Game status", snap.get("game_status") or "—")
        if section_ms:
            st.caption(
                "Section timing (this render): "
                + " · ".join(f"{k}={v:.0f}ms" for k, v in sorted(section_ms.items(), key=lambda x: -x[1]))
            )
        cache_rows = []
        for fn, label in (
            (fetch_cdn_scoreboard_only, "CDN scoreboard (strict)"),
            (_scoreboard_stats_today_et, "Stats scoreboard (today ET)"),
            (get_live_games, "CDN scoreboard (legacy)"),
            (get_live_boxscore, "Live box score"),
            (get_live_playbyplay, "Play-by-play"),
        ):
            fp = _cache_data_fingerprint(fn)
            if fp:
                cache_rows.append({"feed": label, **fp})
        if cache_rows:
            st.markdown("**Cache (Streamlit `@st.cache_data`)**")
            st.dataframe(pd.DataFrame(cache_rows), use_container_width=True, hide_index=True)
        trace = st.session_state.get("live_gc_trace") or []
        if trace:
            st.markdown("**Request trace (this session, latest render)**")
            t0 = trace[0].get("t", 0)
            rows = []
            for ev in trace[-40:]:
                rows.append(
                    {
                        "Δms": round((ev.get("t", 0) - t0) * 1000.0, 1),
                        "event": ev.get("event"),
                        "ms": ev.get("ms"),
                        "status": ev.get("status"),
                        "cache_hit": ev.get("cache_hit"),
                        "count": ev.get("count"),
                        "error": (str(ev.get("error"))[:80] if ev.get("error") else ""),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        l3e = section_ms.get("layer3_errors") or []
        all_err = list(errors) + list(l3e)
        if all_err:
            st.warning("Technical feed notes (debug only): " + " | ".join(str(x) for x in all_err[:8]))
        else:
            st.caption("No technical feed errors recorded for this render.")
        if NBA_LIVE_AVAILABLE:
            st.caption("Live feeds: `nba_api.live` scoreboard / boxscore / playbyplay (CDN).")
        if NBA_STATS_AVAILABLE:
            st.caption("Stats feeds: `ScoreboardV3` then `ScoreboardV2` for yesterday→tomorrow ET.")
        st.caption(
            "Bracket label **Waiting for API games** is from playoff series reconciliation — not the live scoreboard."
        )
        if st.button("Clear Live GC trace", key="live_gc_clear_trace"):
            st.session_state["live_gc_trace"] = []
            st.rerun()


def _fetch_live_gc_snapshot(team_name):
    """Layer 2 fetch wrapper. All API calls stay behind the manual button."""
    errors = []
    live_count = None
    snap = None
    try:
        games = get_live_games()
        live_count = len(games) if isinstance(games, list) else 0
    except Exception as exc:
        live_count = 0
        errors.append(f"live scoreboard: {exc!r}")
    try:
        snap = get_current_or_today_game(team_name)
    except Exception as exc:
        snap = {
            "game_found": False,
            "game_status": "unavailable",
            "game_row": None,
            "error_messages": [repr(exc)],
            "detection_message": "Live data failed to load.",
        }
        errors.append(f"game detection: {exc!r}")
    errors.extend(snap.get("error_messages", []) if isinstance(snap, dict) else [])
    return snap, live_count, errors


def _manual_live_lines(key):
    raw = str(st.session_state.get(key, "") or "").strip()
    return [x.strip() for x in raw.splitlines() if x.strip()]


def _clock_minutes_remaining(clock_txt):
    txt = str(clock_txt or "").strip()
    if not txt:
        return 12.0
    try:
        if ":" in txt:
            m, s = txt.split(":", 1)
            return max(0.0, min(12.0, float(m) + float(s) / 60.0))
        return max(0.0, min(12.0, float(txt)))
    except Exception:
        return 12.0


def _manual_win_prob(margin, period, clock_txt, is_home, status):
    status_l = str(status or "").lower()
    margin = safe_int(margin)
    if status_l == "final":
        if margin > 0:
            return 99
        if margin < 0:
            return 1
        return 50
    period = max(1, min(4, safe_int(period, 1)))
    elapsed = (period - 1) * 12 + (12 - _clock_minutes_remaining(clock_txt))
    progress = max(0.0, min(1.0, elapsed / 48.0))
    leverage = 1.1 + progress * 4.6
    home_bonus = 2.0 if is_home else 0.0
    if status_l == "halftime":
        leverage = max(leverage, 2.0)
    return int(max(1, min(99, round(50 + margin * leverage + home_bonus))))


def _manual_live_override_active():
    """Game-night: apply typed scores without an extra checkbox toggle."""
    if st.session_state.get("manual_live_enabled", False):
        return True
    if not _live_gc_game_night_emergency_active():
        return False
    home_score = safe_int(st.session_state.get("manual_live_home_score", 0), 0)
    away_score = safe_int(st.session_state.get("manual_live_away_score", 0), 0)
    quarter = safe_int(st.session_state.get("manual_live_quarter", 1), 1)
    status = str(st.session_state.get("manual_live_status", "live")).lower()
    if home_score > 0 or away_score > 0:
        return True
    if quarter > 1:
        return True
    if status in ("final", "halftime"):
        return True
    return False


def _manual_live_override_snapshot(team_name):
    if not _manual_live_override_active():
        return None
    home = st.session_state.get("manual_live_home_team") or team_name
    away = st.session_state.get("manual_live_away_team") or TEAM_PROFILES.get(team_name, {}).get("current_opponent") or team_name
    if home == away:
        away = TEAM_PROFILES.get(home, {}).get("current_opponent") or away
    status = st.session_state.get("manual_live_status", "live")
    quarter = safe_int(st.session_state.get("manual_live_quarter", 1), 1)
    clock = str(st.session_state.get("manual_live_clock", "12:00") or "")
    home_score = safe_int(st.session_state.get("manual_live_home_score", 0), 0)
    away_score = safe_int(st.session_state.get("manual_live_away_score", 0), 0)
    if str(status).lower() == "scheduled":
        phase = "pregame"
    elif str(status).lower() == "final":
        phase = "postgame"
    else:
        phase = "live"
    selected_in_game = team_name in (home, away)
    fav_is_home = team_name == home or not selected_in_game
    margin = (home_score - away_score) if fav_is_home else (away_score - home_score)
    opp_name = away if fav_is_home else home
    return {
        "gid": "manual-live-override",
        "home_name": home,
        "away_name": away,
        "home_tri": TEAM_ALIASES.get(home, ""),
        "away_tri": TEAM_ALIASES.get(away, ""),
        "home_score": home_score,
        "away_score": away_score,
        "period": quarter,
        "clock": clock,
        "status": str(status).title(),
        "phase": phase,
        "is_fav_home": fav_is_home,
        "margin": margin,
        "opp_name": opp_name,
        "fav_alias": TEAM_ALIASES.get(team_name if selected_in_game else home, ""),
        "selected_in_game": selected_in_game,
        "series_line": st.session_state.get("manual_live_series_score", ""),
        "top_performers": _manual_live_lines("manual_live_top_performers"),
        "top_plays": _manual_live_lines("manual_live_top_plays"),
        "injuries": _manual_live_lines("manual_live_injuries"),
        "notes": str(st.session_state.get("manual_live_notes", "") or "").strip(),
    }


def _render_manual_probability_command(team_name, parsed, prob):
    status = parsed.get("status", "live")
    margin = safe_int(parsed.get("margin", 0), 0)
    period = safe_int(parsed.get("period", 1), 1)
    clock = parsed.get("clock", "")
    is_home = bool(parsed.get("is_fav_home"))
    st.markdown(
        f"""
<div class="broadcast-card">
  <div class="broadcast-card-title">Manual Win Probability</div>
  <div style="font-size:1.8rem;font-weight:950;color:#0f172a">{prob}%</div>
  <div class="prob-bar"><span style="width:{max(1, min(99, prob))}%"></span></div>
  <div style="font-size:13px;color:#334155;line-height:1.45">
    Manual model uses score margin, quarter, time remaining, home/away, and game status. It is a fan-facing game-state model, not betting odds.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    rows = []
    if margin < 0:
        for target in [-12, -8, -4, 0]:
            if target > margin:
                rows.append({
                    "Scenario": "Tie the game" if target == 0 else f"Cut deficit to {abs(target)}",
                    "Manual win %": f"{_manual_win_prob(target, period, clock, is_home, status)}%",
                    "Margin": target,
                })
    else:
        for target in [5, 10, 15, 20]:
            if target > margin:
                rows.append({
                    "Scenario": f"Grow lead to {target}",
                    "Manual win %": f"{_manual_win_prob(target, period, clock, is_home, status)}%",
                    "Margin": target,
                })
    if rows:
        render_fan_stat_table(pd.DataFrame(rows), team_name)


def _manual_to_game_row(manual):
    """Convert manual override dict into a scoreboard-shaped row for unified parsing."""
    home = {
        "teamTricode": manual.get("home_tri", ""),
        "teamName": fan_nick(manual.get("home_name", "")),
        "teamCity": " ".join(str(manual.get("home_name", "")).split()[:-1]),
        "score": manual.get("home_score", 0),
    }
    away = {
        "teamTricode": manual.get("away_tri", ""),
        "teamName": fan_nick(manual.get("away_name", "")),
        "teamCity": " ".join(str(manual.get("away_name", "")).split()[:-1]),
        "score": manual.get("away_score", 0),
    }
    status = str(manual.get("status", "Live"))
    phase = manual.get("phase", "live")
    if phase == "pregame":
        gstat, period, clock = 1, 0, ""
    elif phase == "postgame":
        gstat, period, clock = 3, 4, ""
    else:
        gstat, period, clock = 2, manual.get("period", 1), manual.get("clock", "")
    return {
        "gameId": manual.get("gid", "manual-live-override"),
        "gameStatus": gstat,
        "gameStatusText": status,
        "period": period,
        "gameClock": clock,
        "_source": "manual override",
        "homeTeam": home,
        "awayTeam": away,
    }


def _bracket_stub_game_row(team_name, profile, opp, snap=None):
    """Best-effort game row from schedule fallback or bracket opponent when APIs are quiet."""
    for row in _fallback_schedule_games_for_team(team_name, days_each_side=2):
        return row
    if not opp:
        opp = (profile or {}).get("current_opponent") or ""
    if not opp:
        return None
    home, away = team_name, opp
    return {
        "gameId": f"fallback-{TEAM_ALIASES.get(home, 'hm')}-{TEAM_ALIASES.get(away, 'aw')}",
        "gameStatus": 1,
        "gameStatusText": (snap or {}).get("detection_message") or "Feed unavailable — bracket schedule shell",
        "period": safe_int((snap or {}).get("period", 0), 0),
        "gameClock": str((snap or {}).get("clock") or ""),
        "_source": "unified playoff engine / schedule fallback",
        "_fallback_schedule": True,
        "homeTeam": {
            "teamTricode": TEAM_ALIASES.get(home, ""),
            "teamName": fan_nick(home),
            "score": safe_int((snap or {}).get("home_score", 0), 0),
        },
        "awayTeam": {
            "teamTricode": TEAM_ALIASES.get(away, ""),
            "teamName": fan_nick(away),
            "score": safe_int((snap or {}).get("away_score", 0), 0),
        },
    }


def _get_current_or_today_game_traced(team_name):
    before = _cache_data_fingerprint(get_current_or_today_game)
    t0 = pytime.perf_counter()
    snap = get_current_or_today_game(team_name)
    ms = (pytime.perf_counter() - t0) * 1000.0
    after = _cache_data_fingerprint(get_current_or_today_game)
    cache_hit = bool(before and after and after.get("hits", 0) > before.get("hits", 0))
    _live_gc_trace(
        "get_current_or_today_game",
        ms=round(ms, 1),
        cache_hit=cache_hit,
        game_found=bool((snap or {}).get("game_found")),
        game_status=(snap or {}).get("game_status"),
        data_source=(snap or {}).get("data_source"),
        detection_tier=(snap or {}).get("detection_tier"),
        game_id=(snap or {}).get("game_id"),
        home_score=(snap or {}).get("home_score"),
        away_score=(snap or {}).get("away_score"),
    )
    return snap


def resolve_live_gc_state(team_name, profile):
    """
    Live Game Center state — Layer 1 CDN-first fast path.
    Bracket 0–0 shells are never returned when a live/stats/last-known row exists.
    """
    return _resolve_live_gc_layer1_fast(team_name, profile)


def _resolve_live_gc_state_legacy(team_name, profile):
    """Legacy full merge resolver (debug / fallback reference only)."""
    t_resolve = pytime.perf_counter()
    errors = []
    manual = _manual_live_override_snapshot(team_name)
    if manual:
        row = _manual_to_game_row(manual)
        parsed = _live_gc_parse_game_row(row, team_name)
        snap = {
            "game_found": True,
            "game_status": "live" if parsed["phase"] == "live" else ("final" if parsed["phase"] == "postgame" else "scheduled"),
            "phase": parsed["phase"],
            "game_row": row,
            "data_source": "manual override",
            "detection_tier": "manual",
            "detection_message": "",
            "countdown": "",
            "starting_soon": False,
        }
        return {
            "priority": "manual",
            "source_label": "Emergency score entry",
            "snap": snap,
            "parsed": parsed,
            "game_row": row,
            "manual": manual,
            "live_count": None,
            "errors": errors,
            "message": "",
        }

    live_count = None
    try:
        games = _get_live_games_traced() if _live_gc_debug_enabled() else get_live_games()
        live_count = len(games) if isinstance(games, list) else 0
    except Exception as exc:
        live_count = 0
        errors.append(f"live scoreboard: {exc!r}")

    snap = None
    try:
        snap = _get_current_or_today_game_traced(team_name) if _live_gc_debug_enabled() else get_current_or_today_game(team_name)
    except Exception as exc:
        errors.append(f"game detection: {exc!r}")
        snap = {
            "game_found": False,
            "game_status": "unavailable",
            "game_row": None,
            "detection_message": "Live data failed to load.",
            "detection_tier": "unknown",
            "data_source": "none",
        }

    if snap:
        errors.extend(snap.get("error_messages", []) if isinstance(snap.get("error_messages"), list) else [])

    if snap and snap.get("game_found") and snap.get("game_row"):
        parsed = _live_gc_parse_game_row(snap["game_row"], team_name)
        src = str(snap.get("data_source") or "NBA API")
        out = {
            "priority": "api",
            "source_label": src,
            "snap": snap,
            "parsed": parsed,
            "game_row": snap["game_row"],
            "manual": None,
            "live_count": live_count,
            "errors": errors,
            "message": snap.get("detection_message") or "",
        }
        if _live_gc_debug_enabled():
            _live_gc_trace(
                "resolve_live_gc_state",
                ms=round((pytime.perf_counter() - t_resolve) * 1000.0, 1),
                priority="api",
                phase=parsed.get("phase"),
                scores=f"{parsed.get('away_score')}-{parsed.get('home_score')}",
            )
        return out

    opp, round_name, series_text, shell_src = _local_live_gc_series_context(team_name, profile)
    stub = _bracket_stub_game_row(team_name, profile, opp, snap)
    if stub:
        parsed = _live_gc_parse_game_row(stub, team_name)
        tier = (snap or {}).get("detection_tier") or "bracket_fallback"
        msg = (snap or {}).get("detection_message") or "Live feed unavailable — showing bracket matchup shell."
        out = {
            "priority": "fallback",
            "source_label": f"Fallback · {shell_src}",
            "snap": snap or {},
            "parsed": parsed,
            "game_row": stub,
            "manual": None,
            "live_count": live_count,
            "errors": errors,
            "message": msg,
            "round_name": round_name,
            "series_text": series_text,
            "tier": tier,
        }
        if _live_gc_debug_enabled():
            _live_gc_trace(
                "resolve_live_gc_state",
                ms=round((pytime.perf_counter() - t_resolve) * 1000.0, 1),
                priority="fallback",
                shell_src=shell_src,
                tier=tier,
            )
        return out

    out = {
        "priority": "static",
        "source_label": "Static message",
        "snap": snap or {},
        "parsed": None,
        "game_row": None,
        "manual": None,
        "live_count": live_count,
        "errors": errors,
        "message": (snap or {}).get("detection_message") or "No game row available. Use manual override or refresh.",
        "round_name": round_name,
        "series_text": series_text,
    }
    if _live_gc_debug_enabled():
        _live_gc_trace(
            "resolve_live_gc_state",
            ms=round((pytime.perf_counter() - t_resolve) * 1000.0, 1),
            priority="static",
            detection_tier=(snap or {}).get("detection_tier"),
        )
    return out


def _live_status_chip(state):
    """Human-readable game status for the always-on shell."""
    if state.get("priority") == "manual":
        ph = (state.get("parsed") or {}).get("phase", "live")
        return "MANUAL · LIVE" if ph == "live" else ("MANUAL · FINAL" if ph == "postgame" else "MANUAL · SCHEDULED")
    snap = state.get("snap") or {}
    gs = str(snap.get("game_status") or "").lower()
    if gs == "live":
        return "LIVE NOW"
    if gs == "final":
        return "FINAL"
    if gs == "starting soon":
        return "STARTING SOON"
    if gs == "scheduled":
        return "SCHEDULED"
    if state.get("priority") == "fallback":
        return "FEED UNAVAILABLE"
    if state.get("priority") == "stale":
        return "LAST KNOWN SCORE"
    return "UNAVAILABLE"


def _format_live_gc_updated_at(dt):
    if not dt:
        return "—"
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        local = dt.astimezone(timezone.utc)
        return local.strftime("%H:%M:%S UTC")
    except Exception:
        return "—"


def _live_gc_connecting_state(team_name, profile, series_text=None):
    """Placeholder state for trust-strip first paint before Layer 1 resolve."""
    _, _rnd, ser = _live_gc_profile_context(team_name, profile)
    return {
        "priority": "shell",
        "source_label": "connecting…",
        "parsed": None,
        "updated_at": datetime.now(timezone.utc),
        "snap": {},
        "series_text": series_text or ser,
    }


def _live_gc_record_validation_tick(team_name, state):
    """Append trust-strip snapshot to Dev Lab session log (game-night diagnostics)."""
    try:
        parsed = state.get("parsed")
        if state.get("priority") == "manual" and state.get("manual"):
            parsed = state["manual"]
        chip = _live_status_chip(state)
        score = "—"
        if parsed and not _live_gc_suspicious_zero_zero_live(parsed):
            aws, hs = safe_int(parsed.get("away_score", 0)), safe_int(parsed.get("home_score", 0))
            if parsed.get("phase") == "pregame" and aws == 0 and hs == 0:
                score = "pregame"
            else:
                score = f"{aws}–{hs}"
        suspicious = bool(parsed and _live_gc_suspicious_zero_zero_live(parsed))
        entry = {
            "time_utc": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "team": team_name,
            "status": chip,
            "score": score,
            "source": str(state.get("source_label") or "—")[:40],
            "priority": state.get("priority"),
            "zero_zero_guard": suspicious,
        }
        log = st.session_state.setdefault(LIVE_GC_VALIDATION_LOG_KEY, [])
        prev = log[-1] if log else {}
        if (
            prev.get("score") != entry["score"]
            or prev.get("status") != entry["status"]
            or prev.get("source") != entry["source"]
        ):
            log.append(entry)
        if len(log) > 50:
            st.session_state[LIVE_GC_VALIDATION_LOG_KEY] = log[-50:]
    except Exception:
        pass


def _render_live_gc_trust_strip(team_name, state):
    """Always-visible Layer 1 metadata: status, score, clock, source, last updated."""
    parsed = state.get("parsed")
    if state.get("priority") == "manual" and state.get("manual"):
        parsed = state["manual"]
    chip = _live_status_chip(state)
    src = str(state.get("source_label") or "—")
    if len(src) > 32:
        src = src[:29] + "…"
    ts = _format_live_gc_updated_at(state.get("updated_at") or state.get("last_known_at"))
    if parsed and not _live_gc_suspicious_zero_zero_live(parsed):
        aws, hs = safe_int(parsed.get("away_score", 0)), safe_int(parsed.get("home_score", 0))
        if parsed.get("phase") == "pregame" and aws == 0 and hs == 0:
            score_txt = "—"
            clock_txt = str(parsed.get("status") or "Pregame")
        else:
            score_txt = f"{aws}–{hs}"
            if parsed.get("period") and parsed.get("clock"):
                clock_txt = f"Q{parsed['period']} · {parsed['clock']}"
            elif parsed.get("period"):
                clock_txt = f"Q{parsed['period']}"
            else:
                clock_txt = str(parsed.get("status") or parsed.get("phase") or "—")
    else:
        score_txt = "—"
        clock_txt = "—" if chip in ("UNAVAILABLE", "FEED UNAVAILABLE") else chip
    st.markdown(
        "<div style='font-size:11px;font-weight:800;letter-spacing:.08em;color:#64748b;"
        "margin:0 0 6px 0'>LIVE SCOREBOARD</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Status", chip)
    c2.metric("Score", score_txt)
    c3.metric("Clock", clock_txt)
    c4.metric("Source", src)
    c5.metric("Last updated", ts)
    _live_gc_record_validation_tick(team_name, state)


def _render_live_gc_layer1(team_name, profile, state):
    """Layer 1 broadcast shell — score, clock, series, win prob, top scorer (CDN-first)."""
    parsed = state.get("parsed")
    if not parsed:
        return
    _opp_l, rnd_l, ser_l = _live_gc_profile_context(team_name, profile)
    series_line = ser_l
    if state.get("series_text"):
        series_line = state["series_text"]
    prob = live_win_probability(
        team_name, parsed["opp_name"], parsed["margin"], parsed["period"], parsed["is_fav_home"]
    )
    banner = str(state.get("feed_banner") or "").strip()
    priority = state.get("priority")
    if priority == "stale":
        age = _format_live_gc_age(state.get("last_known_at") or state.get("updated_at"))
        age_txt = f" (score from {age})" if age else ""
        st.warning(f"{_live_gc_fan_msg('last_known')}{age_txt}")
    elif banner:
        if "delayed" in banner.lower() or "last known" in banner.lower():
            st.warning(banner)
        else:
            st.info(banner)

    _render_live_gc_matchup_header(parsed, series_line)
    render_live_score_banner(
        team_name,
        parsed["away_tri"],
        parsed["home_tri"],
        parsed["away_score"],
        parsed["home_score"],
        parsed["status"],
        parsed["phase"],
    )

    ts = _format_live_gc_updated_at(state.get("updated_at"))
    src = state.get("source_label") or "NBA CDN"
    if priority == "stale":
        age = _format_live_gc_age(state.get("last_known_at") or state.get("updated_at"))
        st.caption(
            f"**Source:** {src} · **Last known score:** {ts}"
            + (f" ({age})" if age else "")
            + f" · Series: **{series_line}**"
        )
    else:
        st.caption(f"**Source:** {src} · **Last updated:** {ts} · Series: **{series_line}**")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Win probability", f"{prob}%")
    try:
        st.session_state["live_win_prob_display"] = float(prob)
        st.session_state["_last_win_prob"] = float(prob)
    except (TypeError, ValueError):
        pass
    m2.metric("Quarter", f"Q{parsed['period']}" if parsed.get("period") else "—")
    m3.metric("Clock", parsed.get("clock") or "—")
    m4.metric("Margin", f"{parsed['margin']:+d}")
    top = state.get("top_scorer")
    if top and top.get("name"):
        m5.metric("Top scorer", f"{top['name'][:18]} · {top['pts']} PTS")
    else:
        m5.metric("Top scorer", "—")

    chip = _live_status_chip(state)
    st.markdown(
        f"<div style='font-size:12px;color:#94a3b8;margin-top:4px'>"
        f"<b>{html.escape(chip)}</b> · {html.escape(rnd_l)}</div>",
        unsafe_allow_html=True,
    )


def _live_gc_next_game_number(team_name):
    """1-based game number in current series (e.g. 2 after Game 1 final)."""
    try:
        _k, s = series_for_team(team_name)
        if s and s.get("games"):
            return len(s["games"]) + 1
    except Exception:
        pass
    return 2


def _render_live_gc_pregame_panel(team_name, profile, parsed, state):
    """Pregame / starting-soon essentials — no box score or PBP APIs."""
    opp = parsed.get("opp_name") or profile.get("current_opponent")
    game_n = _live_gc_next_game_number(team_name)
    _, rnd_l, ser_l = _live_gc_profile_context(team_name, profile)
    series_line, _ = _live_series_board(parsed.get("away_name"), parsed.get("home_name"))
    if not series_line:
        series_line = ser_l
    sec = _seconds_to_tipoff(state.get("game_row") or parsed.get("game") or {})
    countdown = _format_countdown(sec) if sec is not None and sec > 0 else ""
    tip_et = ""
    gr = state.get("game_row") or {}
    if gr.get("gameEt"):
        raw_et = str(gr["gameEt"])
        tip_et = raw_et if "ET" in raw_et.upper() else f"{raw_et} ET"
    elif gr.get("gameTimeUTC"):
        try:
            tz = _nba_et_zone() or timezone.utc
            dt = datetime.fromisoformat(str(gr["gameTimeUTC"]).replace("Z", "+00:00")).astimezone(tz)
            h = dt.hour % 12 or 12
            tip_et = f"{h}:{dt.minute:02d} {'PM' if dt.hour >= 12 else 'AM'} ET"
        except Exception:
            tip_et = "8:30 PM ET"

    st.markdown(f"### {html.escape(rnd_l)} · Game {game_n}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Matchup", f"{fan_nick(parsed['away_name'])} @ {fan_nick(parsed['home_name'])}")
    c2.metric("Series", series_line or ser_l)
    c3.metric("Tipoff", countdown or tip_et or "Tonight")

    st.info(f"**Game 1:** {FINALS_GAME1_CANONICAL_SCORE} — Knicks lead the series **1–0**.")

    if "Finals" in str(rnd_l):
        watch = (
            "Brunson–Towns two-man game vs Wembanyama drop coverage; "
            "San Antonio's transition defense and Castle–Vassell floor spacing."
        )
    else:
        hctx = resolve_home_matchup_context_fast(team_name)
        pctx = build_dashboard_playoff_context(team_name, hctx, None, skip_live_fetch=True)
        watch = _home_watch_next_brief(team_name, pctx, _home_watch_next_keys(team_name, pctx, None))
    st.markdown(f"**What to watch tonight:** {html.escape(watch)}")

    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"**{fan_nick(team_name)} keys**")
        for nm in (TEAM_PROFILES.get(team_name, {}).get("starters") or [])[:4]:
            st.write(f"• {nm}")
    with cols[1]:
        st.markdown(f"**{fan_nick(opp)} keys**")
        for nm in (TEAM_PROFILES.get(opp, {}).get("starters") or [])[:4]:
            st.write(f"• {nm}")

    inj_rows = (FALLBACK_INJURY_REPORT.get(team_name, []) or []) + (FALLBACK_INJURY_REPORT.get(opp, []) or [])
    if inj_rows:
        st.markdown("**Injury monitor** (check official pregame report before tip)")
        st.dataframe(pd.DataFrame(inj_rows).head(6), use_container_width=True, hide_index=True)
    else:
        st.caption("Tap **Injuries / Foul Trouble** after tipoff for live availability, or **Go live** on Home.")

    banner = str(state.get("feed_banner") or "").strip()
    if banner:
        st.warning(banner)


def _render_live_gc_instant_shell(team_name, profile, state):
    """Connecting shell — profile only, no API."""
    opp, round_name, series_text = _live_gc_profile_context(team_name, profile)[:3]
    shell_src = "profile"
    if state.get("series_text"):
        series_text = state["series_text"]
    if state.get("round_name"):
        round_name = state["round_name"]
    logo = TEAM_LOGOS.get(team_name, "")
    opp_logo = TEAM_LOGOS.get(opp, "") if opp else ""
    chip = _live_status_chip(state)
    src = state.get("source_label") or shell_src
    parsed = state.get("parsed")
    score_line = series_text
    if parsed:
        score_line = f"{parsed['away_score']} — {parsed['home_score']}"
    st.markdown(
        f"""
<div class="live-gc-board">
  <div style="text-align:center">
    <img src="{html.escape(logo)}" alt=""/>
    <div style="font-size:12px;font-weight:900">{html.escape(team_name)}</div>
  </div>
  <div style="text-align:center;min-width:240px">
    <div style="font-size:11px;color:#fbbf24;font-weight:950;letter-spacing:.12em">{html.escape(chip)}</div>
    <div class="live-gc-score">{html.escape(score_line)}</div>
    <div class="live-gc-clock">{html.escape(round_name)} · {html.escape(series_text)}</div>
    <div style="font-size:11px;color:#94a3b8;margin-top:4px">Data: {html.escape(src)}</div>
  </div>
  <div style="text-align:center">
    <img src="{html.escape(opp_logo)}" alt=""/>
    <div style="font-size:12px;font-weight:900">{html.escape(opp or 'Opponent')}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected team", fan_nick(team_name))
    c2.metric("Opponent", fan_nick(opp) if opp else "TBD")
    c3.metric("Round", round_name)
    c4.metric("Feed", src[:24])


def _render_manual_live_override_panel(team_name, profile, emphasize=False):
    """Emergency manual score — used when CDN/stats feeds fail during a game."""
    with st.expander("Emergency score entry", expanded=bool(emphasize)):
        st.caption(
            "Turn this on if the live feed is down but you still need a scoreboard during the game. "
            "It replaces the API score at the top until you turn it off."
        )
        st.checkbox(
            "Use emergency score (overrides live feed)",
            key="manual_live_enabled",
        )
        if not st.session_state.get("manual_live_enabled"):
            lk = _live_gc_load_last_known(team_name)
            if lk and isinstance(lk.get("parsed"), dict):
                p = lk["parsed"]
                age = _format_live_gc_age(lk.get("saved_at"))
                st.info(
                    f"Last known from feed: **{p.get('away_score', 0)}–{p.get('home_score', 0)}**"
                    + (f" ({age})" if age else "")
                    + " — enable above to type a newer score manually."
                )
            return
        opp_default = TEAM_PROFILES.get(team_name, {}).get("current_opponent") or team_name
        team_keys = sorted(TEAM_PROFILES.keys())
        c1, c2 = st.columns(2)
        with c1:
            home_idx = team_keys.index(team_name) if team_name in team_keys else 0
            st.selectbox("Home team", team_keys, index=home_idx, key="manual_live_home_team")
        with c2:
            away_idx = team_keys.index(opp_default) if opp_default in team_keys else 0
            st.selectbox("Away team", team_keys, index=away_idx, key="manual_live_away_team")
        c3, c4, c5, c6 = st.columns(4)
        c3.number_input("Home score", 0, 200, 0, key="manual_live_home_score")
        c4.number_input("Away score", 0, 200, 0, key="manual_live_away_score")
        c5.number_input("Quarter", 1, 4, 1, key="manual_live_quarter")
        c6.text_input("Time remaining", "8:42", key="manual_live_clock")
        st.selectbox("Game status", ["live", "scheduled", "final", "halftime"], key="manual_live_status")
        st.text_input("Series score (optional)", "2 - 1", key="manual_live_series_score")
        st.text_area("Top performers (one per line)", key="manual_live_top_performers", height=80)
        st.text_area("Top plays (one per line)", key="manual_live_top_plays", height=80)
        st.text_area("Injury / availability notes (one per line)", key="manual_live_injuries", height=60)
        st.text_input("Extra notes", key="manual_live_notes")


def _render_manual_live_game_center(team_name, parsed):
    st.success("Manual live mode active")
    _render_live_gc_matchup_header(parsed, parsed.get("series_line") or None)
    render_live_score_banner(
        team_name,
        parsed["away_tri"],
        parsed["home_tri"],
        parsed["away_score"],
        parsed["home_score"],
        parsed["status"],
        parsed["phase"],
    )
    if not parsed.get("selected_in_game"):
        st.info("Manual override is showing a league game that does not include the selected sidebar team.")
    prob = _manual_win_prob(parsed["margin"], parsed["period"], parsed["clock"], parsed["is_fav_home"], parsed["status"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Manual win probability", f"{prob}%")
    c2.metric("Quarter", f"Q{parsed['period']}")
    c3.metric("Clock", parsed["clock"] or "—")
    c4.metric("Status", parsed["status"])
    _render_manual_probability_command(team_name, parsed, prob)

    team_section_header("Manual game story", "🎙️")
    margin = safe_int(parsed.get("margin", 0), 0)
    nick = fan_nick(team_name if parsed.get("selected_in_game") else parsed.get("home_name"))
    if str(parsed.get("status", "")).lower() == "final":
        if margin > 0:
            st.success(f"Final recap: {nick} close it out from the manually entered scoreboard. The story is score control, late-game execution, and who owned the final run.")
        elif margin < 0:
            st.warning(f"Final recap: {nick} come up short. The next read is where the comeback stalled: empty possessions, defensive glass, or late-shot creation.")
        else:
            st.info("Final status is set with a tied score. Update the score to complete the recap.")
    elif margin < 0:
        st.warning(f"{nick} need a comeback push: stack stops, cut the gap before the next timeout, and avoid live-ball turnovers.")
    elif margin > 0:
        st.success(f"{nick} have scoreboard control. The job now is protecting the glass, making free throws, and avoiding rushed possessions.")
    else:
        st.info("Tie game. The next two-minute stretch should decide pace, matchups, and crowd pressure.")

    cols = st.columns(3)
    with cols[0]:
        st.markdown("#### Top performers")
        if parsed["top_performers"]:
            for line in parsed["top_performers"]:
                st.markdown(f"<div class='live-gc-perf'>{html.escape(line)}</div>", unsafe_allow_html=True)
        else:
            st.caption("Add top performers in Emergency Score Control.")
    with cols[1]:
        st.markdown("#### Top plays")
        if parsed["top_plays"]:
            st.dataframe(pd.DataFrame({"Top play": parsed["top_plays"]}), use_container_width=True, hide_index=True)
        else:
            st.caption("Add top plays in Emergency Score Control.")
    with cols[2]:
        st.markdown("#### Injury / availability")
        if parsed["injuries"]:
            for line in parsed["injuries"]:
                st.warning(line)
        else:
            st.caption("Add injury notes if needed.")
    if parsed.get("notes"):
        st.info(parsed["notes"])


def _render_safe_emergency_entry(team_name, profile):
    """Minimal emergency score form — no extra API calls."""
    _render_game_night_emergency_entry_top(team_name, profile)


def _render_game_night_emergency_entry_top(team_name, profile):
    """Emergency score controls — always visible at top during game-night mode."""
    st.markdown("#### Emergency score entry")
    st.caption(
        "Enter the live score below — it applies automatically and powers the trust strip, "
        "win probability, and keys to success."
    )
    team_keys = sorted(TEAM_PROFILES.keys())
    c1, c2 = st.columns(2)
    with c1:
        home_idx = team_keys.index("New York Knicks") if "New York Knicks" in team_keys else (
            team_keys.index(team_name) if team_name in team_keys else 0
        )
        st.selectbox("Home", team_keys, index=home_idx, key="manual_live_home_team")
    with c2:
        away_idx = team_keys.index("San Antonio Spurs") if "San Antonio Spurs" in team_keys else (
            team_keys.index(profile.get("current_opponent", team_name)) if profile.get("current_opponent") in team_keys else 0
        )
        st.selectbox("Away", team_keys, index=away_idx, key="manual_live_away_team")
    c3, c4, c5, c6, c7 = st.columns(5)
    c3.number_input("Home pts", 0, 200, 0, key="manual_live_home_score")
    c4.number_input("Away pts", 0, 200, 0, key="manual_live_away_score")
    c5.number_input("Quarter", 1, 4, 1, key="manual_live_quarter")
    c6.text_input("Clock", "8:42", key="manual_live_clock")
    c7.selectbox("Status", ["live", "scheduled", "final", "halftime"], key="manual_live_status")
    st.text_input("Series score", "1 - 0", key="manual_live_series_score")
    st.markdown("---")


def _render_live_gc_safe_board(team_name, profile, state, parsed):
    """Safe mode UI — scoreboard essentials only (no Plotly, box, PBP, or heavy widgets)."""
    e = html.escape
    priority = state.get("priority")
    banner = str(state.get("feed_banner") or "").strip()
    if priority == "stale":
        age = _format_live_gc_age(state.get("last_known_at") or state.get("updated_at"))
        st.warning(f"{_live_gc_fan_msg('last_known')}" + (f" (score from {age})" if age else ""))
    elif banner:
        st.warning(banner) if "delayed" in banner.lower() or "last known" in banner.lower() else st.info(banner)

    opp_l, rnd_l, ser_l = _live_gc_profile_context(team_name, profile)
    series_line, _series_src = _live_series_board(parsed["away_name"], parsed["home_name"])
    if series_line:
        ser_l = series_line
    away_logo = e(TEAM_LOGOS.get(parsed["away_name"], ""))
    home_logo = e(TEAM_LOGOS.get(parsed["home_name"], ""))
    chip = _live_status_chip(state)
    if parsed.get("period") and parsed.get("clock"):
        clock_txt = f"Q{parsed['period']} · {parsed['clock']}"
    elif parsed.get("period"):
        clock_txt = f"Q{parsed['period']}"
    else:
        clock_txt = str(parsed.get("status") or "—")

    st.markdown(
        f"<div class='live-gc-board'>"
        f"<div style='text-align:center'><img src='{away_logo}' alt=''/><div style='font-size:12px;font-weight:800'>{e(parsed['away_name'])}</div></div>"
        f"<div style='text-align:center;min-width:220px'>"
        f"<div style='font-size:11px;color:#fbbf24;font-weight:950'>{e(chip)}</div>"
        f"<div class='live-gc-score'>{parsed['away_score']} — {parsed['home_score']}</div>"
        f"<div class='live-gc-clock'>{e(clock_txt)}</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-top:6px'>Series · {e(ser_l)} · {e(rnd_l)}</div>"
        f"</div>"
        f"<div style='text-align:center'><img src='{home_logo}' alt=''/><div style='font-size:12px;font-weight:800'>{e(parsed['home_name'])}</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    ts = _format_live_gc_updated_at(state.get("updated_at"))
    src = e(state.get("source_label") or "NBA CDN")
    if priority == "stale":
        age = _format_live_gc_age(state.get("last_known_at") or state.get("updated_at"))
        st.caption(f"**Source:** {src} · **Last known score:** {ts}" + (f" ({age})" if age else ""))
    else:
        st.caption(f"**Source:** {src} · **Last updated:** {ts}")

    prob = (
        _manual_win_prob(parsed["margin"], parsed["period"], parsed["clock"], parsed["is_fav_home"], parsed["status"])
        if state.get("priority") == "manual"
        else live_win_probability(
            team_name, parsed["opp_name"], parsed["margin"], parsed["period"], parsed["is_fav_home"]
        )
    )
    c1, c2, c3 = st.columns([1, 2, 2])
    c1.metric("Win probability", f"{prob}%")
    c2.markdown(
        f'<div class="prob-bar" style="margin-top:12px"><span style="width:{max(1, min(99, prob))}%"></span></div>',
        unsafe_allow_html=True,
    )
    c3.metric("Margin", f"{parsed['margin']:+d}")

    story = _live_headline_natural(
        team_name,
        parsed.get("phase", "pregame"),
        parsed.get("margin", 0),
        prob,
        parsed.get("period", 0),
        parsed.get("status", ""),
        fan_nick(parsed.get("opp_name", "")),
    )
    st.markdown(
        f"<div style='font-size:14px;line-height:1.5;margin-top:10px;color:#334155'>{e(story)}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("#### Keys to success")
    st.info(f"**Game 1:** {FINALS_GAME1_CANONICAL_SCORE} — Knicks lead the series **1–0**.")
    if parsed.get("phase") == "live" or state.get("priority") == "manual":
        st.markdown(
            f"<div class='broadcast-card dark'><div style='font-size:14px;line-height:1.55'>"
            f"{e(_live_headline_natural(team_name, parsed.get('phase', 'live'), parsed.get('margin', 0), prob, parsed.get('period', 0), parsed.get('status', ''), fan_nick(parsed.get('opp_name', ''))))}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    for line in game_story(team_name, parsed.get("margin", 0), prob, pd.DataFrame()):
        st.write(f"• {line}")
    opp = parsed.get("opp_name") or profile.get("current_opponent")
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"**{fan_nick(team_name)} keys**")
        for nm in (TEAM_PROFILES.get(team_name, {}).get("starters") or [])[:4]:
            st.write(f"• {nm}")
    with cols[1]:
        st.markdown(f"**{fan_nick(opp)} keys**")
        for nm in (TEAM_PROFILES.get(opp, {}).get("starters") or [])[:4]:
            st.write(f"• {nm}")


def _ensure_emergency_lgc_session_defaults():
    """Pre-fill Finals G2 manual score keys — no roster or engine lookups."""
    if "manual_live_home_team" not in st.session_state:
        st.session_state["manual_live_home_team"] = "New York Knicks"
    if "manual_live_away_team" not in st.session_state:
        st.session_state["manual_live_away_team"] = "San Antonio Spurs"
    if "manual_live_series_score" not in st.session_state:
        st.session_state["manual_live_series_score"] = "1 - 0"
    if "manual_live_quarter" not in st.session_state:
        st.session_state["manual_live_quarter"] = 1
    if "manual_live_clock" not in st.session_state:
        st.session_state["manual_live_clock"] = "12:00"
    if "manual_live_status" not in st.session_state:
        st.session_state["manual_live_status"] = "scheduled"


def _emergency_lgc_parsed_from_session():
    """Build scoreboard dict from session manual entry only."""
    home, away = "New York Knicks", "San Antonio Spurs"
    home_score = safe_int(st.session_state.get("manual_live_home_score", 0), 0)
    away_score = safe_int(st.session_state.get("manual_live_away_score", 0), 0)
    quarter = safe_int(st.session_state.get("manual_live_quarter", 1), 1)
    clock = str(st.session_state.get("manual_live_clock", "12:00") or "")
    status = str(st.session_state.get("manual_live_status", "scheduled"))
    status_l = status.lower()
    if status_l == "scheduled":
        phase = "pregame"
    elif status_l == "final":
        phase = "postgame"
    else:
        phase = "live"
    team_name = home
    margin = home_score - away_score
    return {
        "home_name": home,
        "away_name": away,
        "home_tri": TEAM_ALIASES.get(home, "NYK"),
        "away_tri": TEAM_ALIASES.get(away, "SAS"),
        "home_score": home_score,
        "away_score": away_score,
        "period": quarter,
        "clock": clock,
        "status": status.title(),
        "phase": phase,
        "margin": margin,
        "opp_name": away,
        "is_fav_home": True,
        "series_line": st.session_state.get("manual_live_series_score", "1 - 0"),
    }


def _render_emergency_lgc_trust_strip(parsed):
    """Minimal trust strip — manual/local data only, no engine or CDN."""
    status_l = str(parsed.get("status", "")).lower()
    if status_l == "live":
        chip = "MANUAL · LIVE"
    elif status_l == "final":
        chip = "MANUAL · FINAL"
    elif status_l == "halftime":
        chip = "MANUAL · HALFTIME"
    else:
        chip = "MANUAL · SCHEDULED"
    aws, hs = safe_int(parsed.get("away_score", 0)), safe_int(parsed.get("home_score", 0))
    if parsed.get("phase") == "pregame" and aws == 0 and hs == 0:
        score_txt, clock_txt = "—", status_l.title() or "Pregame"
    else:
        score_txt = f"{aws}–{hs}"
        if parsed.get("period") and parsed.get("clock"):
            clock_txt = f"Q{parsed['period']} · {parsed['clock']}"
        elif parsed.get("period"):
            clock_txt = f"Q{parsed['period']}"
        else:
            clock_txt = str(parsed.get("status") or "—")
    ts = _format_live_gc_updated_at(datetime.now(timezone.utc))
    st.markdown(
        "<div style='font-size:11px;font-weight:800;letter-spacing:.08em;color:#64748b;"
        "margin:0 0 6px 0'>LIVE SCOREBOARD</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Status", chip)
    c2.metric("Score", score_txt)
    c3.metric("Clock", clock_txt)
    c4.metric("Source", "Manual (emergency)")
    c5.metric("Last updated", ts)


def render_live_game_center_emergency_only(boot_t0):
    """Hardcoded Finals G2 shell — zero API, engine, or roster work."""
    t_render = pytime.perf_counter()
    _ensure_emergency_lgc_session_defaults()

    st.markdown(
        "<div style='padding:10px 14px;border-radius:8px;background:#7f1d1d;color:#fef2f2;"
        "font-size:13px;font-weight:700;margin-bottom:10px'>"
        "Emergency game-night mode active — live feed unavailable, using manual/local score."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### NBA Finals · Game 2")
    st.caption("San Antonio Spurs @ New York Knicks · Knicks lead series **1–0**")
    st.info(f"**Game 1:** {FINALS_GAME1_CANONICAL_SCORE} — Knicks lead the series **1–0**.")

    st.markdown("#### Manual score entry")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.number_input("Knicks score", 0, 200, key="manual_live_home_score")
    c2.number_input("Spurs score", 0, 200, key="manual_live_away_score")
    c3.number_input("Quarter", 1, 4, key="manual_live_quarter")
    c4.text_input("Clock", key="manual_live_clock")
    c5.selectbox("Status", ["live", "scheduled", "final", "halftime"], key="manual_live_status")

    parsed = _emergency_lgc_parsed_from_session()
    _render_emergency_lgc_trust_strip(parsed)

    e = html.escape
    clock_txt = (
        f"Q{parsed['period']} · {parsed['clock']}"
        if parsed.get("period") and parsed.get("clock")
        else (f"Q{parsed['period']}" if parsed.get("period") else str(parsed.get("status") or "—"))
    )
    st.markdown(
        f"<div class='live-gc-board'>"
        f"<div style='text-align:center'><div style='font-size:14px;font-weight:800'>{e(parsed['away_name'])}</div></div>"
        f"<div style='text-align:center;min-width:220px'>"
        f"<div style='font-size:11px;color:#fbbf24;font-weight:950'>EMERGENCY · GAME 2</div>"
        f"<div class='live-gc-score'>{parsed['away_score']} — {parsed['home_score']}</div>"
        f"<div class='live-gc-clock'>{e(clock_txt)}</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-top:6px'>Series · {e(parsed.get('series_line') or '1 - 0')} · NBA Finals</div>"
        f"</div>"
        f"<div style='text-align:center'><div style='font-size:14px;font-weight:800'>{e(parsed['home_name'])}</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    prob = _manual_win_prob(
        parsed["margin"], parsed["period"], parsed["clock"], parsed["is_fav_home"], parsed["status"]
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Win probability (Knicks)", f"{prob}%")
    m2.metric("Margin", f"{parsed['margin']:+d}")
    m3.metric("Status", parsed["status"])

    emergency_render_ms = (pytime.perf_counter() - t_render) * 1000.0
    startup_before_lgc = (t_render - boot_t0) * 1000.0
    total_route_ms = (pytime.perf_counter() - boot_t0) * 1000.0

    with st.expander("Route timing (emergency LGC)", expanded=False):
        st.metric("startup_before_lgc", f"{startup_before_lgc:.0f} ms")
        st.metric("emergency_render_ms", f"{emergency_render_ms:.0f} ms")
        st.metric("total_route_ms", f"{total_route_ms:.0f} ms")

    return emergency_render_ms, total_route_ms


def _run_lgc_emergency_route(boot_t0):
    """Minimal sidebar + emergency LGC shell; rerun if user picks another page."""
    pages = dict(PAGES)
    labels = list(pages.keys())
    def_label = PAGE_LABEL_ALIASES.get(
        st.session_state.pop("page_override", None)
        or st.session_state.get("page_label_last")
        or "🔴 Live Game Center",
        "🔴 Live Game Center",
    )
    lgc_idx = labels.index("🔴 Live Game Center") if "🔴 Live Game Center" in labels else 0
    page_label = st.sidebar.radio(
        "Choose page",
        labels,
        index=labels.index(def_label) if def_label in labels else lgc_idx,
    )
    st.session_state["page_label_last"] = page_label
    if pages[page_label] != "Live Game Center":
        st.rerun()
    render_live_game_center_emergency_only(boot_t0)
    try:
        from nba_persistent_state import autosave_nba_state

        autosave_nba_state(st)
    except Exception:
        pass


def render_live_game_center_safe(team_name, profile):
    """TEMPORARY safe mode — Layer 1 only; zero heavy feature execution."""
    lgc_stt = (
        _get_validation_playoff_state()
        if _validation_mode_active()
        else _get_lgc_local_playoff_state()
    )
    profile = get_effective_team_profile(team_name, lgc_stt)
    _live_gc_trace_clear()
    t_page = pytime.perf_counter()
    section_ms = {}
    game_night = _live_gc_game_night_emergency_active()

    if _validation_skip_network():
        _render_validation_mode_banner()
        render_fan_page_hero(team_name, "Live Game Center", "Profile-only scoreboard (no CDN fetch).", "LIVE")
        render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state())
        _validation_facts_block(team_name)
        opp, rnd, ser = _live_gc_profile_context(team_name, profile)[:3]
        st.info(f"**{fan_nick(team_name)}** · {html.escape(rnd)} · {html.escape(ser)} vs {html.escape(fan_nick(opp) if opp else 'TBD')}")
        if _validation_page_deferred("live_gc"):
            _validation_offer_full_page("live_gc", label="Load Live Game Center (CDN scoreboard)")
            return

    if game_night:
        st.markdown(
            "<div style='padding:10px 14px;border-radius:8px;background:#7f1d1d;color:#fef2f2;"
            "font-size:13px;font-weight:700;margin-bottom:10px'>"
            "Emergency game-night mode active — live feed unavailable, using manual/local score."
            "</div>",
            unsafe_allow_html=True,
        )
        _ensure_game_night_manual_defaults(team_name, profile)
        _render_game_night_emergency_entry_top(team_name, profile)
    else:
        mode_lbl = "QA MODE" if _qa_mode_active() and not LIVE_GC_SAFE_MODE else "SAFE MODE"
        st.markdown(
            f"<div style='padding:8px 12px;border-radius:8px;background:#1e293b;color:#f8fafc;"
            f"font-size:13px;font-weight:700;margin-bottom:10px'>"
            f"{mode_lbl} — live scoreboard only (analysis, box score, PBP, and charts disabled)"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Scores and bracket context auto-refresh about every 60 seconds while this page is open.")

    layer1_slot = st.empty()
    with layer1_slot.container():
        _render_live_gc_trust_strip(team_name, _live_gc_connecting_state(team_name, profile))

    if game_night:
        if st.button("Retry live feed (2s max)", key=f"live_gc_safe_refresh_{team_name}", type="secondary"):
            for fn in (fetch_cdn_scoreboard_only, _scoreboard_stats_today_et):
                try:
                    fn.clear()
                except Exception:
                    pass
            st.session_state["live_gc_force_feed_retry"] = True
            st.rerun()
        st.caption("Auto-refresh paused during emergency game-night mode. Box score, PBP, shot chart, and injuries are disabled.")
    elif st.button("Refresh scoreboard", key=f"live_gc_safe_refresh_{team_name}", type="primary"):
        for fn in (fetch_cdn_scoreboard_only, _scoreboard_stats_today_et):
            try:
                fn.clear()
            except Exception:
                pass
        st.rerun()

    t0 = pytime.perf_counter()
    state = _resolve_live_gc_layer1_fast(team_name, profile)
    section_ms["layer1_resolve"] = (pytime.perf_counter() - t0) * 1000.0

    parsed = None
    if state.get("priority") == "manual" and state.get("manual"):
        row = _manual_to_game_row(state["manual"])
        parsed = _live_gc_parse_game_row(row, team_name)
    elif state.get("parsed"):
        parsed = state["parsed"]

    snap = state.get("snap") or {}
    gs_pre = str(snap.get("game_status") or "")
    is_pregame = parsed and (parsed.get("phase") == "pregame" or gs_pre in ("scheduled", "starting soon"))

    with layer1_slot.container():
        _render_live_gc_trust_strip(team_name, state)
        if parsed and is_pregame and state.get("priority") != "manual":
            _render_live_gc_pregame_panel(team_name, profile, parsed, state)
        elif parsed:
            _render_live_gc_safe_board(team_name, profile, state, parsed)
        elif not game_night:
            st.warning(state.get("feed_banner") or _live_gc_fan_msg("no_game"))
            _render_safe_emergency_entry(team_name, profile)
        else:
            st.warning(state.get("feed_banner") or "Enter score above to populate the board.")

    section_ms["total"] = (pytime.perf_counter() - t_page) * 1000.0
    if _live_gc_debug_enabled():
        _render_live_gc_debug(
            team_name,
            profile.get("current_opponent"),
            layer1_loaded=True,
            live_attempted=True,
            live_count=state.get("live_count"),
            errors=state.get("errors"),
            state=state,
            section_ms=section_ms,
        )
        st.caption(f"**Safe mode render:** {section_ms['total']:.0f} ms (Layer 1 resolve: {section_ms.get('layer1_resolve', 0):.0f} ms)")


def render_live_game_center(team_name, profile):
    """CDN-first Live Game Center: Layer 1 (fast) → Layer 2 (analysis) → Layer 3 (heavy, opt-in)."""
    if _ultra_fast_active() and _validation_page_deferred("live_gc"):
        render_live_game_center_safe(team_name, profile)
        return
    if _live_gc_safe_mode_active():
        _page_perf_tick("live_gc_safe")
        return render_live_game_center_safe(team_name, profile)

    _live_gc_trace_clear()
    _page_perf_tick("live_gc_full")
    t_page = pytime.perf_counter()
    section_ms = {}
    if st.session_state.get("_live_gc_sel_team") != team_name:
        for k in list(st.session_state.keys()):
            if isinstance(k, str) and (
                k.startswith("live_gc__")
                or k.startswith("live_gc_depth_")
                or k.startswith("live_gc_layer2_")
                or k.startswith("live_gc_tab_")
            ):
                del st.session_state[k]
        st.session_state["_live_gc_sel_team"] = team_name

    _opp_l, _rnd_l, ser_l = _live_gc_profile_context(team_name, profile)
    layer1_slot = st.empty()
    with layer1_slot.container():
        _render_live_gc_trust_strip(team_name, _live_gc_connecting_state(team_name, profile, ser_l))

    t0 = pytime.perf_counter()
    state = _resolve_live_gc_layer1_fast(team_name, profile)
    section_ms["layer1_resolve"] = (pytime.perf_counter() - t0) * 1000.0
    snap = state.get("snap") or {}
    parsed = state.get("parsed")
    opp = (parsed or {}).get("opp_name") or _opp_l or profile.get("current_opponent")
    if parsed and parsed.get("gid") and parsed.get("gid") != st.session_state.get("_live_gc_gid"):
        for k in list(st.session_state.keys()):
            if isinstance(k, str) and k.startswith("live_gc_depth_"):
                del st.session_state[k]
        st.session_state["_live_gc_gid"] = parsed.get("gid")

    gs_pre = str((snap or {}).get("game_status") or "")
    is_pregame = parsed and (parsed.get("phase") == "pregame" or gs_pre in ("scheduled", "starting soon"))

    with layer1_slot.container():
        _render_live_gc_trust_strip(team_name, state)
        if state.get("priority") == "manual" and state.get("manual"):
            _render_manual_live_game_center(team_name, state["manual"])
        elif parsed and is_pregame:
            _render_live_gc_matchup_header(parsed, ser_l)
            _render_live_gc_pregame_panel(team_name, profile, parsed, state)
        elif parsed:
            _render_live_gc_layer1(team_name, profile, state)
        else:
            _render_live_gc_instant_shell(team_name, profile, {**state, "parsed": None, "series_text": ser_l})

    ident = team_fan_identity(team_name)
    mx = get_display_matchup(team_name)
    render_fan_page_hero(
        team_name,
        "Live Game Center",
        f"{ident['stakes']} {mx['round_short']} · {mx['team_nick']} vs {mx['opponent_nick']} — live score first, analysis second.",
        "GAME NIGHT",
    )
    render_page_trust_strip("live_gc")
    render_playoff_matchup_ribbon(team_name)
    feed_stressed = state.get("priority") in ("static", "stale") or not parsed
    _render_manual_live_override_panel(team_name, profile, emphasize=(state.get("priority") == "static"))

    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("Refresh Live Game Data", key=f"live_gc_refresh_{team_name}", type="primary"):
            for fn in (
                fetch_cdn_scoreboard_only,
                _scoreboard_stats_today_et,
                get_live_games,
                get_current_or_today_game,
                get_live_game_detection_context_cached,
                _pick_featured_game_for_team_cached,
                featured_broadcast_state_cached,
                _merged_stats_games_et_window,
            ):
                try:
                    fn.clear()
                except Exception:
                    pass
            st.rerun()
    with col_b:
        if feed_stressed:
            st.caption("Live feed is struggling — score above is last known or manual. Tap Refresh to retry the league feed.")
        else:
            st.caption("Live scoreboard above refreshes automatically during games. Open a tab below for box score, shot chart, and analysis.")

    if state.get("priority") == "manual" and state.get("manual"):
        section_ms["total"] = (pytime.perf_counter() - t_page) * 1000.0
        _render_live_gc_debug(
            team_name, opp, layer1_loaded=True, live_attempted=True,
            live_count=state.get("live_count"), errors=state.get("errors"),
            state=state, section_ms=section_ms,
        )
        return

    if not parsed:
        st.warning(state.get("feed_banner") or _live_gc_fan_msg("feed_delayed"))
        _live_gc_render_fallback_content(
            team_name, profile, opp_name=opp, include_outlook=False, show_injuries=False
        )
        section_ms["total"] = (pytime.perf_counter() - t_page) * 1000.0
        _render_live_gc_debug(
            team_name, opp, layer1_loaded=True, live_attempted=True,
            live_count=state.get("live_count"), errors=state.get("errors"),
            state=state, section_ms=section_ms,
        )
        return

    gid = parsed.get("gid") or ""
    gs = str((snap or {}).get("game_status") or parsed.get("phase") or "")
    if AUTOREFRESH_AVAILABLE and (
        parsed.get("phase") == "live"
        or str(snap.get("game_status") or "") in ("live", "starting soon")
    ):
        st_autorefresh(
            interval=45000 if str(snap.get("game_status") or "") == "starting soon" else 30000,
            key=f"live_gc_auto_refresh_{team_name}",
        )

    prob = live_win_probability(
        team_name, parsed["opp_name"], parsed["margin"], parsed["period"], parsed["is_fav_home"]
    )

    if is_pregame:
        st.caption("Pregame board above — detailed stats tabs unlock after tipoff.")
        section_ms["total"] = (pytime.perf_counter() - t_page) * 1000.0
        _render_live_gc_debug(
            team_name, opp, layer1_loaded=True, live_attempted=True,
            live_count=state.get("live_count"), errors=state.get("errors"),
            state=state, section_ms=section_ms,
        )
        return

    t0 = pytime.perf_counter()
    _render_live_gc_tabbed_sections(team_name, profile, parsed, state, prob, section_ms)
    section_ms["tabs"] = (pytime.perf_counter() - t0) * 1000.0

    section_ms["total"] = (pytime.perf_counter() - t_page) * 1000.0
    _render_live_gc_debug(
        team_name, opp, layer1_loaded=True, live_attempted=True,
        live_count=state.get("live_count"), errors=state.get("errors"),
        state=state, section_ms=section_ms,
    )


def _render_live_gc_layer2_sections(team_name, profile, parsed, state, prob, section_ms):
    """Layer 2 — secondary analysis (no box score API, no Plotly, no injury scrape)."""
    st.markdown("### Live analysis")
    game_row = state.get("game_row") or {}
    actions = []
    if isinstance(game_row, dict):
        actions = game_row.get("actions") or []

    with st.expander("Win probability & comeback paths", expanded=True):
        st.markdown("<div class='broadcast-grid'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            _render_probability_command(team_name, parsed, prob, box_df=None)
        with c2:
            _render_live_matchup_swing(team_name, parsed["opp_name"], None, parsed)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Momentum & keys to the game", expanded=False):
        nick = fan_nick(team_name)
        margin = safe_int(parsed.get("margin", 0), 0)
        if parsed.get("phase") == "live":
            st.info(_live_headline_natural(
                team_name, parsed["phase"], margin, prob, parsed["period"],
                parsed["status"], fan_nick(parsed["opp_name"]),
            ))
        if actions:
            run_txt = _scoring_run_summary(actions, parsed.get("fav_alias"), window=40)
            if run_txt:
                st.caption(run_txt)
        else:
            st.caption("Momentum detail fills in when play-by-play is loaded (Layer 3).")

    with st.expander("Top performers (CDN leaders)", expanded=False):
        top = state.get("top_scorer")
        if top and top.get("name"):
            st.markdown(
                _player_tile_html(
                    {"Player": top["name"], "PTS": top["pts"], "REB": top.get("reb", 0), "AST": top.get("ast", 0)},
                    badge="CDN game leader",
                ),
                unsafe_allow_html=True,
            )
        st.caption("Full performer cards need Layer 3 box score.")

    with st.expander("Lineups / rotation estimate", expanded=False):
        st.caption("Rotation from playoff profiles — not live on-court tracking.")
        _render_lineup_board(team_name, parsed["opp_name"], pd.DataFrame())

    with st.expander("Game story", expanded=False):
        st.markdown(
            f"<div class='broadcast-card dark'><div style='font-size:14px;line-height:1.55'>"
            f"{html.escape(_live_headline_natural(team_name, parsed['phase'], parsed['margin'], prob, parsed['period'], parsed['status'], fan_nick(parsed['opp_name'])))}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
        for line in game_story(team_name, parsed["margin"], prob, pd.DataFrame()):
            st.write(f"• {line}")


def _render_live_gc_layer3_sections(team_name, profile, parsed, snap, gid, prob, section_ms):
    """Layer 3 — heavy analytics (opt-in): box score, PBP, Plotly, injuries."""
    st.markdown("### Detailed stats")
    l3_errors = section_ms.setdefault("layer3_errors", [])
    box_df = pd.DataFrame()
    if gid:
        t0 = pytime.perf_counter()
        try:
            box_game = _live_gc_fetch_boxscore(gid)
            box_df = create_boxscore_df(box_game) if box_game else pd.DataFrame()
        except Exception:
            box_df = pd.DataFrame()
        section_ms["boxscore"] = (pytime.perf_counter() - t0) * 1000.0

    with st.expander("Full styled box score", expanded=False):
        if box_df is not None and not box_df.empty:
            _render_styled_box_score(team_name, parsed["opp_name"], box_df)
        else:
            st.caption(_live_gc_fan_msg("detail_unavailable"))

    with st.expander("Top performers (box score)", expanded=False):
        if box_df is not None and not box_df.empty:
            _render_top_performer_cards(team_name, parsed["opp_name"], box_df)
        else:
            st.caption("Waiting for box score feed.")

    with st.expander("Play-by-play, top plays & shot chart", expanded=False):
        actions = []
        try:
            t0 = pytime.perf_counter()
            actions = _live_gc_fetch_playbyplay(gid)
            section_ms["playbyplay"] = (pytime.perf_counter() - t0) * 1000.0
        except Exception as exc:
            _live_gc_log_error(l3_errors, "playbyplay", exc)
            st.caption(_live_gc_fan_msg("detail_unavailable"))
        if actions:
            try:
                tp = _top_plays_from_actions(actions, team_name, limit=8)
                if tp is not None and not tp.empty:
                    st.dataframe(tp, use_container_width=True, hide_index=True)
                shots = shot_df_from_pbp(actions, parsed["fav_alias"])
                if not shots.empty:
                    st.plotly_chart(draw_court(shots, f"{fan_nick(team_name)} shot chart"), use_container_width=True)
            except Exception as exc:
                _live_gc_log_error(l3_errors, "shot_chart", exc)
                st.caption(_live_gc_fan_msg("detail_unavailable"))
        else:
            st.caption("Play-by-play has not published yet.")

    with st.expander("Injury report (full scrape)", expanded=False):
        try:
            render_injury_report(
                team_name,
                opponent_name=parsed["opp_name"],
                show_page_header=False,
                fan_perspective_team=team_name,
                neutral_framing=True,
            )
        except Exception as exc:
            _live_gc_log_error(l3_errors, "injuries", exc)
            st.caption(_live_gc_fan_msg("detail_unavailable"))

    with st.expander("Game story (box-score detail)", expanded=False):
        if box_df is not None and not box_df.empty:
            for line in game_story(team_name, parsed["margin"], prob, box_df):
                st.write(f"• {line}")
        else:
            st.caption("Detailed story lines appear when the box score publishes.")

# ==========================================================
# Franchise Playoff Legends / Team History Leaders
# ==========================================================
def _hist_player(rank, name, era, tier, accomplishments, why, pts=0, ppg=0.0, reb=0, ast=0, stl=0, blk=0, threes=0, g30=0, g40=0, gp=0, finals=0, titles=0, compare_to=None, current_watch=False):
    return {
        "rank": rank, "name": name, "era": era, "tier": tier,
        "accomplishments": accomplishments, "why": why,
        "pts": pts, "ppg": ppg, "reb": reb, "ast": ast, "stl": stl, "blk": blk,
        "threes": threes, "g30": g30, "g40": g40, "gp": gp, "finals": finals, "titles": titles,
        "compare_to": compare_to or [], "current_watch": current_watch,
    }


FRANCHISE_HISTORY_DATA = {
    "New York Knicks": {
        "context": "Knicks history is measured in Garden pressure: title-era toughness, Ewing-era longevity, and modern Brunson shot-making.",
        "legends": [
            _hist_player(1, "Patrick Ewing", "1985-2000", "Franchise anchor", "11x All-Star with New York; long playoff centerpiece.", "The Knicks' modern historical bar for two-way volume and repeated deep runs.", 2400, 21.9, 1180, 190, 80, 230, 0, 31, 5, 110, 1, 0),
            _hist_player(2, "Willis Reed", "1964-1974", "Championship captain", "1970 Finals MVP; 1973 champion.", "Reed is the emotional and championship standard every Knicks big chases.", 1350, 17.4, 900, 170, 0, 0, 0, 10, 1, 78, 3, 2),
            _hist_player(3, "Walt Frazier", "1967-1977", "Title guard standard", "Two championships; iconic Game 7 in 1970.", "Frazier owns the guard legacy lane: defense, control, and winning on the biggest stage.", 1750, 20.7, 520, 630, 120, 15, 0, 22, 3, 85, 3, 2),
            _hist_player(4, "Carmelo Anthony", "2011-2017", "Scoring-era face", "2013 scoring champion; carried the modern Garden scoring burden.", "Melo is the reference point for high-volume Knicks playoff shot creation before Brunson.", 560, 28.3, 125, 35, 20, 8, 35, 12, 4, 20, 0, 0),
            _hist_player(5, "Bernard King", "1982-1987", "Scoring peak", "One of the most explosive scoring peaks in franchise history.", "King's playoff scoring bursts remain the short-run standard for Garden eruption games.", 500, 34.8, 75, 30, 14, 4, 0, 11, 5, 15, 0, 0),
            _hist_player(6, "Earl Monroe", "1971-1980", "Title-era artist", "1973 champion; Hall of Fame guard.", "Monroe added flair and late-clock creativity to a team already built on defense.", 980, 15.6, 170, 220, 55, 6, 0, 4, 0, 63, 2, 1),
            _hist_player(7, "Jalen Brunson", "2022-present", "Current history watch", "Modern lead guard; already owns major Knicks playoff scoring nights.", "Brunson is chasing the Melo/King scoring tier and the Frazier guard-history tier.", 760, 31.5, 90, 150, 22, 2, 42, 14, 5, 24, 0, 0, ["Walt Frazier", "Bernard King", "Carmelo Anthony"], True),
            _hist_player(8, "Allan Houston", "1996-2005", "Shot-making wing", "1999 Finals run; one of the franchise's cleanest postseason shooters.", "Houston connects the Ewing era to the later Garden scoring template.", 930, 18.2, 120, 95, 35, 7, 70, 8, 1, 51, 1, 0),
            _hist_player(9, "Dave DeBusschere", "1968-1974", "Title forward glue", "Two championships; elite defensive forward.", "The Knicks' classic role-star model: toughness, rebounding, and winning possessions.", 880, 13.8, 720, 160, 0, 0, 0, 2, 0, 64, 3, 2),
            _hist_player(10, "Karl-Anthony Towns", "2025-present", "Current big watch", "Current frontcourt star with a chance to write a Knicks playoff chapter.", "Towns' franchise case starts with whether his shooting-big skill set travels deep into May.", 120, 19.5, 70, 25, 6, 7, 18, 2, 0, 6, 0, 0, ["Patrick Ewing", "Willis Reed", "Dave DeBusschere"], True),
        ],
    },
    "Los Angeles Lakers": {
        "context": "Lakers history is a banner argument: guards, dominant bigs, and stars judged by how often the run ends in June.",
        "legends": [
            _hist_player(1, "Magic Johnson", "1979-1991, 1996", "Showtime engine", "5 championships; 3 Finals MVPs.", "Magic is the Lakers' playmaking and winning standard.", 3700, 19.5, 1450, 2300, 350, 70, 80, 35, 4, 190, 9, 5),
            _hist_player(2, "Kobe Bryant", "1996-2016", "Modern icon", "5 championships; 2 Finals MVPs.", "Kobe is the late-clock and volume-scoring measuring stick.", 5600, 25.6, 1100, 1040, 310, 140, 290, 88, 13, 220, 7, 5),
            _hist_player(3, "Kareem Abdul-Jabbar", "1975-1989", "Interior dynasty star", "5 Lakers championships; Finals MVP-level longevity.", "Kareem defines elite Lakers big-man production over multiple title windows.", 4200, 22.0, 1600, 550, 170, 390, 0, 45, 6, 190, 8, 5),
            _hist_player(4, "Shaquille O'Neal", "1996-2004", "Peak-force center", "3 straight Finals MVPs.", "Shaq is the franchise's most overwhelming playoff physical force.", 3300, 27.7, 1500, 350, 70, 260, 0, 55, 12, 120, 4, 3),
            _hist_player(5, "Jerry West", "1960-1974", "Logo-era scorer", "1972 champion; 1969 Finals MVP.", "West set the franchise playoff scoring standard before Showtime.", 4400, 29.1, 650, 970, 0, 0, 0, 80, 20, 153, 9, 1),
            _hist_player(6, "LeBron James", "2018-present", "Current legend", "2020 champion and Finals MVP with Los Angeles.", "LeBron's Lakers chapter is about extending a historic career into one more banner chase.", 1250, 26.0, 450, 430, 70, 45, 120, 20, 6, 48, 1, 1, ["Magic Johnson", "Kobe Bryant", "Jerry West"], True),
            _hist_player(7, "Wilt Chamberlain", "1968-1973", "Title-era giant", "1972 champion and Finals MVP.", "Wilt is the rebounding and interior dominance reference for older Lakers runs.", 1450, 15.8, 1800, 300, 0, 0, 0, 8, 1, 92, 4, 1),
            _hist_player(8, "Anthony Davis", "2019-present", "Current two-way big", "2020 champion; elite defensive playoff ceiling.", "Davis is chasing the franchise's big-man defensive lineage.", 950, 25.0, 430, 120, 45, 90, 45, 15, 3, 38, 1, 1, ["Kareem Abdul-Jabbar", "Shaquille O'Neal", "Wilt Chamberlain"], True),
        ],
    },
    "Boston Celtics": {
        "context": "Celtics history is a championship ladder: Russell's rings, Bird's peak, Pierce's longevity, and the Tatum/Brown era trying to stack its own tier.",
        "legends": [
            _hist_player(1, "Bill Russell", "1956-1969", "Dynasty standard", "11 championships; defensive dynasty anchor.", "Russell is the reason Celtics history starts with rings.", 2700, 16.2, 4100, 770, 0, 0, 0, 12, 1, 165, 12, 11),
            _hist_player(2, "Larry Bird", "1979-1992", "Peak superstar", "3 championships; 2 Finals MVPs.", "Bird is the franchise's skill, shot-making, and alpha-forward template.", 3900, 23.8, 1700, 1050, 300, 130, 80, 55, 8, 164, 5, 3),
            _hist_player(3, "John Havlicek", "1962-1978", "Endurance winner", "8 championships; Finals MVP.", "Havlicek is the Celtics' two-way longevity model.", 3800, 22.0, 1250, 1050, 180, 60, 0, 45, 5, 172, 8, 8),
            _hist_player(4, "Paul Pierce", "1998-2013", "Modern captain", "2008 Finals MVP.", "Pierce bridges the post-Bird era to the modern championship standard.", 3200, 20.9, 1100, 650, 210, 95, 230, 35, 5, 150, 2, 1),
            _hist_player(5, "Jayson Tatum", "2017-present", "Current title face", "Finals appearance and championship-tier scoring runs.", "Tatum is climbing toward the Bird/Pierce wing-scorer tier.", 2700, 24.0, 850, 520, 120, 80, 260, 35, 8, 112, 2, 1, ["Larry Bird", "Paul Pierce", "John Havlicek"], True),
            _hist_player(6, "Jaylen Brown", "2016-present", "Current two-way scorer", "Finals MVP-level modern wing run.", "Brown's case is about two-way playoff reliability next to Tatum.", 2100, 20.0, 620, 310, 115, 45, 180, 20, 3, 105, 2, 1, ["Paul Pierce", "John Havlicek", "Larry Bird"], True),
        ],
    },
    "San Antonio Spurs": {
        "context": "Spurs history is big-man excellence plus guard craft: Duncan's titles, Robinson's foundation, and Wembanyama's new ceiling.",
        "legends": [
            _hist_player(1, "Tim Duncan", "1997-2016", "Dynasty anchor", "5 championships; 3 Finals MVPs.", "Duncan is the franchise's entire playoff measuring stick.", 5100, 20.6, 2850, 760, 160, 560, 5, 60, 10, 251, 6, 5),
            _hist_player(2, "David Robinson", "1989-2003", "Foundation star", "2 championships; MVP-level two-way center.", "Robinson made the Spurs a serious playoff franchise before Duncan arrived.", 2200, 18.1, 1300, 280, 150, 310, 0, 20, 3, 123, 2, 2),
            _hist_player(3, "Tony Parker", "2001-2018", "Championship guard", "4 championships; 2007 Finals MVP.", "Parker owns the Spurs guard-scoring and paint-touch legacy.", 4000, 17.9, 520, 1140, 180, 20, 95, 35, 4, 226, 5, 4),
            _hist_player(4, "Manu Ginobili", "2002-2018", "Chaos creator", "4 championships; elite sixth-man playoff impact.", "Manu is the franchise's creativity and pressure-play wild card.", 3100, 14.0, 850, 830, 290, 70, 320, 18, 1, 218, 5, 4),
            _hist_player(5, "Kawhi Leonard", "2011-2018", "Two-way peak", "2014 Finals MVP.", "Kawhi's Spurs chapter is short, but his defensive and Finals peak is enormous.", 1150, 16.5, 580, 150, 130, 45, 90, 8, 2, 70, 2, 1),
            _hist_player(6, "Victor Wembanyama", "2023-present", "Current future watch", "Current franchise centerpiece beginning his playoff file.", "Wembanyama is chasing the Duncan/Robinson big-man standard, not just rookie excitement.", 130, 21.5, 75, 20, 8, 20, 12, 2, 0, 6, 0, 0, ["Tim Duncan", "David Robinson", "Kawhi Leonard"], True),
        ],
    },
    "Oklahoma City Thunder": {
        "context": "Thunder/Sonics history includes Seattle roots and OKC superstars: Payton, Kemp, Durant, Westbrook, and Shai's current climb.",
        "legends": [
            _hist_player(1, "Kevin Durant", "2007-2016", "OKC scoring peak", "2012 Finals run; MVP-level playoff scorer.", "Durant is the Thunder-era scoring standard.", 2850, 28.8, 760, 360, 100, 115, 150, 45, 10, 99, 1, 0),
            _hist_player(2, "Russell Westbrook", "2008-2019", "OKC engine", "Finals run; triple-double pressure.", "Westbrook is the franchise's chaos, pace, and usage icon.", 2600, 25.4, 760, 850, 210, 25, 120, 35, 7, 103, 1, 0),
            _hist_player(3, "Gary Payton", "1990-2003", "Sonics guard legend", "1996 Finals; elite defense and creation.", "Payton connects the franchise's Seattle history to its guard legacy.", 2600, 20.0, 620, 900, 240, 35, 130, 25, 4, 130, 1, 0),
            _hist_player(4, "Shawn Kemp", "1989-1997", "Sonics force", "1996 Finals; explosive frontcourt star.", "Kemp is the franchise's vertical athleticism and power-forward reference.", 1350, 17.3, 920, 120, 95, 115, 5, 10, 1, 78, 1, 0),
            _hist_player(5, "Shai Gilgeous-Alexander", "2019-present", "Current MVP-level guard", "Current Thunder lead creator and title-window face.", "Shai is chasing Durant's scoring tier and Westbrook/Payton's guard legacy.", 760, 30.2, 150, 160, 35, 20, 28, 13, 4, 25, 0, 0, ["Kevin Durant", "Russell Westbrook", "Gary Payton"], True),
        ],
    },
    "Cleveland Cavaliers": {
        "context": "Cavaliers history is LeBron's title peak plus guard shot-making eras trying to build their own playoff identity.",
        "legends": [
            _hist_player(1, "LeBron James", "2003-2010, 2014-2018", "Franchise king", "2016 champion and Finals MVP.", "LeBron is the entire Cavaliers playoff ceiling.", 5400, 30.8, 1500, 1400, 300, 170, 250, 90, 20, 175, 5, 1),
            _hist_player(2, "Kyrie Irving", "2011-2017", "Finals shot-maker", "2016 champion; iconic Game 7 shot.", "Kyrie defines the Cavs' modern guard shot-making bar.", 1300, 23.9, 180, 250, 60, 20, 115, 18, 4, 54, 3, 1),
            _hist_player(3, "Mark Price", "1986-1995", "Precision guard", "All-Star floor general for playoff Cavs teams.", "Price is the pre-LeBron guard standard in Cleveland.", 800, 19.2, 100, 310, 45, 5, 55, 8, 1, 42, 0, 0),
            _hist_player(4, "Donovan Mitchell", "2022-present", "Current scoring watch", "Current playoff shot creator with major scoring nights.", "Mitchell is chasing the Kyrie/Price guard-scoring lane in Cleveland colors.", 620, 29.5, 95, 105, 25, 8, 55, 12, 5, 21, 0, 0, ["Kyrie Irving", "Mark Price", "LeBron James"], True),
            _hist_player(5, "Darius Garland", "2019-present", "Current guard watch", "Current lead-playmaking guard.", "Garland's climb is about pairing scoring with Price-style control.", 260, 19.0, 35, 85, 12, 2, 30, 3, 0, 14, 0, 0, ["Mark Price", "Kyrie Irving"], True),
        ],
    },
    "Detroit Pistons": {
        "context": "Pistons history is guard leadership and defense: Isiah's titles, Billups' calm, and Cade trying to start a new chapter.",
        "legends": [
            _hist_player(1, "Isiah Thomas", "1981-1994", "Bad Boys captain", "2 championships; 1990 Finals MVP.", "Isiah is the Pistons' playoff guard standard.", 3000, 20.4, 600, 1300, 230, 40, 35, 30, 4, 150, 3, 2),
            _hist_player(2, "Chauncey Billups", "2002-2008, 2013-2014", "Going to Work leader", "2004 Finals MVP.", "Billups is the calm, efficient playoff organizer Cade is measured against.", 1700, 18.6, 250, 520, 95, 15, 190, 18, 2, 92, 2, 1),
            _hist_player(3, "Joe Dumars", "1985-1999", "Two-way guard", "1989 Finals MVP; 2 championships.", "Dumars is the Pistons' guard-defense and title-efficiency model.", 2100, 15.6, 300, 650, 160, 20, 80, 10, 1, 135, 3, 2),
            _hist_player(4, "Ben Wallace", "2000-2006, 2009-2012", "Defensive backbone", "2004 champion; elite playoff defender.", "Wallace proves Pistons legends do not need scoring to own a series.", 650, 7.0, 1200, 130, 150, 210, 0, 0, 0, 95, 2, 1),
            _hist_player(5, "Cade Cunningham", "2021-present", "Current guard watch", "Current face of the next Pistons playoff chapter.", "Cade is chasing the Isiah/Billups possession-command lane.", 180, 25.5, 45, 58, 8, 3, 16, 3, 1, 7, 0, 0, ["Isiah Thomas", "Chauncey Billups", "Joe Dumars"], True),
        ],
    },
    "Minnesota Timberwolves": {
        "context": "Wolves history is Garnett's foundation and Edwards trying to turn short bursts into sustained franchise memory.",
        "legends": [
            _hist_player(1, "Kevin Garnett", "1995-2007, 2015-2016", "Franchise soul", "2004 MVP; Western Conference Finals run.", "Garnett is the Wolves' defensive, emotional, and postseason bar.", 1050, 21.0, 650, 240, 65, 75, 10, 12, 2, 50, 0, 0),
            _hist_player(2, "Anthony Edwards", "2020-present", "Current scoring face", "Modern Wolves shot creator with deep-run upside.", "Edwards is chasing Garnett for the clearest Wolves playoff signature.", 980, 28.0, 210, 180, 45, 22, 90, 17, 6, 35, 0, 0, ["Kevin Garnett", "Sam Cassell", "Karl-Anthony Towns"], True),
            _hist_player(3, "Karl-Anthony Towns", "2015-2024", "Stretch-big era", "Multi-time All-Star; key playoff big before New York.", "Towns is a major modern Wolves big even as his Knicks chapter starts separately.", 560, 19.0, 300, 75, 20, 28, 70, 5, 1, 29, 0, 0),
            _hist_player(4, "Sam Cassell", "2003-2005", "2004 guard spark", "Key shot-maker on the 2004 WCF team.", "Cassell is still the short-run guard benchmark for winning Wolves playoff offense.", 350, 18.5, 50, 95, 18, 2, 25, 4, 0, 19, 0, 0),
            _hist_player(5, "Rudy Gobert", "2022-present", "Current defensive anchor", "Current interior defender for deep-run attempts.", "Gobert's Wolves legacy depends on whether the defense survives elite playoff spacing.", 260, 10.5, 285, 28, 12, 35, 0, 0, 0, 25, 0, 0, ["Kevin Garnett"], True),
        ],
    },
    "Philadelphia 76ers": {
        "context": "Sixers history runs through dominant stars: Wilt, Dr. J, Moses, Iverson, and Embiid trying to solve May.",
        "legends": [
            _hist_player(1, "Julius Erving", "1976-1987", "Championship wing", "1983 champion; multiple Finals runs.", "Dr. J is the Sixers' blend of style and winning.", 3600, 22.0, 1200, 700, 260, 220, 15, 45, 7, 165, 4, 1),
            _hist_player(2, "Allen Iverson", "1996-2006, 2009-2010", "Scoring icon", "2001 Finals run; MVP.", "Iverson is the franchise's modern playoff scoring mythology.", 2400, 29.7, 300, 500, 150, 15, 105, 40, 12, 81, 1, 0),
            _hist_player(3, "Moses Malone", "1982-1986", "Title big", "1983 champion and Finals MVP.", "Moses owns the Sixers' most direct modern title-star blueprint.", 1050, 22.0, 690, 70, 35, 70, 0, 12, 2, 48, 1, 1),
            _hist_player(4, "Joel Embiid", "2014-present", "Current MVP center", "MVP-era scoring big; still chasing conference-final breakthrough.", "Embiid is chasing Moses/Wilt-level dominance with a deeper team result.", 1700, 24.8, 760, 210, 55, 115, 80, 20, 4, 68, 0, 0, ["Moses Malone", "Wilt Chamberlain", "Allen Iverson"], True),
            _hist_player(5, "Tyrese Maxey", "2020-present", "Current speed guard", "Current playoff scoring guard next to Embiid.", "Maxey's chase is toward the Iverson guard-scoring lane, with a different style.", 760, 20.5, 120, 175, 32, 10, 95, 8, 1, 37, 0, 0, ["Allen Iverson", "Hal Greer"], True),
        ],
    },
}

FRANCHISE_HISTORY_DATA.update({
    "Denver Nuggets": {
        "context": "Nuggets history now runs through Jokic's title standard, with Murray's playoff shot-making beside the older English/Mutombo/Carmelo eras.",
        "legends": [
            _hist_player(1, "Nikola Jokic", "2015-present", "Championship fulcrum", "2023 champion and Finals MVP.", "Jokic is the franchise's clear playoff ceiling and the standard every future Nugget chases.", 2400, 27.5, 1150, 780, 120, 70, 150, 35, 8, 88, 1, 1, ["Alex English", "Carmelo Anthony"], True),
            _hist_player(2, "Jamal Murray", "2016-present", "Current shot-maker", "Bubble scoring eruption; 2023 title guard.", "Murray owns many of Denver's modern pressure-shot memories.", 1650, 24.8, 270, 360, 65, 20, 210, 25, 7, 67, 1, 1, ["Nikola Jokic", "Carmelo Anthony"], True),
            _hist_player(3, "Alex English", "1980-1990", "Scoring-era icon", "Longtime franchise scoring face.", "English is the pre-Jokic regular-season and playoff scoring reference.", 1450, 24.0, 360, 250, 55, 35, 5, 18, 3, 60, 0, 0),
            _hist_player(4, "Carmelo Anthony", "2003-2011", "Modern scoring star", "2009 Western Conference Finals run.", "Melo lifted Denver into a louder playoff era before the Jokic title window.", 1700, 24.5, 460, 180, 70, 25, 80, 22, 4, 70, 0, 0),
            _hist_player(5, "Dikembe Mutombo", "1991-1996", "Defensive landmark", "1994 upset symbol and elite rim protector.", "Mutombo is the image of Denver's underdog defensive playoff identity.", 520, 12.0, 620, 35, 25, 150, 0, 1, 0, 43, 0, 0),
        ],
    },
    "Houston Rockets": {
        "context": "Rockets history is built around championship centers, Harden's volume era, and a new young core trying to earn its own May credibility.",
        "legends": [
            _hist_player(1, "Hakeem Olajuwon", "1984-2001", "Championship standard", "2 championships; 2 Finals MVPs.", "Hakeem is the Rockets' ultimate playoff tier: defense, footwork, and title proof.", 3750, 25.9, 1620, 430, 240, 470, 5, 55, 12, 145, 3, 2),
            _hist_player(2, "James Harden", "2012-2021", "Volume engine", "Multiple deep runs and historic usage.", "Harden is the modern Rockets offense benchmark, even without the final banner.", 3000, 28.4, 600, 780, 190, 60, 330, 48, 11, 106, 0, 0),
            _hist_player(3, "Moses Malone", "1976-1982", "Interior force", "1981 Finals run; MVP-level rebounding.", "Moses is the pre-Hakeem big-man playoff force.", 1150, 24.0, 760, 70, 35, 80, 0, 15, 3, 48, 1, 0),
            _hist_player(4, "Yao Ming", "2002-2011", "Global franchise star", "Efficient playoff center when healthy.", "Yao's Houston legacy is a peak-and-health question fans still revisit.", 555, 19.8, 275, 42, 8, 42, 0, 5, 0, 28, 0, 0),
            _hist_player(5, "Alperen Sengun", "2021-present", "Current big watch", "Current hub for Houston's young playoff identity.", "Sengun's chase starts with proving his interior creation can anchor a series.", 105, 17.5, 55, 30, 5, 4, 2, 1, 0, 6, 0, 0, ["Hakeem Olajuwon", "Yao Ming"], True),
            _hist_player(6, "Jalen Green", "2021-present", "Current scoring watch", "Current young scoring guard.", "Green needs efficient scoring bursts to join Houston's guard/wing playoff memory.", 115, 19.2, 22, 18, 4, 2, 16, 2, 0, 6, 0, 0, ["James Harden"], True),
        ],
    },
    "Orlando Magic": {
        "context": "Magic history is star-big peaks, Finals what-ifs, and the Banchero/Wagner era trying to create the next real chapter.",
        "legends": [
            _hist_player(1, "Dwight Howard", "2004-2012", "Finals-era anchor", "2009 Finals run; elite defensive center.", "Dwight is Orlando's deepest modern playoff standard.", 1100, 19.0, 850, 90, 45, 150, 0, 12, 2, 58, 1, 0),
            _hist_player(2, "Shaquille O'Neal", "1992-1996", "Original superstar", "1995 Finals run.", "Shaq gave Orlando its first true superstar playoff identity.", 720, 25.0, 420, 65, 20, 85, 0, 10, 3, 29, 1, 0),
            _hist_player(3, "Penny Hardaway", "1993-1999", "Signature guard", "1995 Finals run; elite creator.", "Penny is the Magic's guard-skill and what-if standard.", 760, 21.8, 210, 280, 60, 15, 45, 9, 2, 35, 1, 0),
            _hist_player(4, "Tracy McGrady", "2000-2004", "Scoring peak", "Explosive individual playoff scorer.", "McGrady is Orlando's high-usage scoring reference despite short series exits.", 600, 31.0, 130, 95, 20, 15, 45, 10, 4, 19, 0, 0),
            _hist_player(5, "Paolo Banchero", "2022-present", "Current franchise watch", "Current scoring-forward centerpiece.", "Paolo is chasing the Shaq/Dwight/Penny tier by turning talent into series wins.", 190, 27.0, 60, 28, 5, 6, 12, 4, 1, 7, 0, 0, ["Tracy McGrady", "Penny Hardaway", "Dwight Howard"], True),
            _hist_player(6, "Franz Wagner", "2021-present", "Current wing watch", "Current two-way scoring forward.", "Wagner's chase is about becoming the playoff connector Orlando lacked in prior eras.", 125, 18.0, 35, 25, 6, 3, 10, 1, 0, 7, 0, 0, ["Penny Hardaway", "Hedo Turkoglu"], True),
        ],
    },
    "Toronto Raptors": {
        "context": "Raptors history changed forever in 2019; every new core is measured against Lowry's climb and Kawhi's title peak.",
        "legends": [
            _hist_player(1, "Kyle Lowry", "2012-2021", "Franchise engine", "2019 champion; longest playoff identity.", "Lowry is the Raptors' culture and winning standard.", 1900, 15.5, 620, 820, 175, 25, 220, 12, 1, 125, 1, 1),
            _hist_player(2, "Kawhi Leonard", "2018-2019", "Title peak", "2019 champion and Finals MVP.", "Kawhi owns the highest single-run peak in Raptors history.", 732, 30.5, 220, 85, 40, 20, 55, 14, 4, 24, 1, 1),
            _hist_player(3, "DeMar DeRozan", "2009-2018", "Pre-title scorer", "Multiple playoff runs as lead scorer.", "DeRozan carried the franchise through the climb before the title trade.", 1450, 21.9, 300, 260, 70, 20, 35, 18, 3, 66, 0, 0),
            _hist_player(4, "Pascal Siakam", "2016-2024", "Title forward", "2019 champion; later first option.", "Siakam connects the title team to the next competitive era.", 1100, 18.0, 520, 230, 70, 45, 65, 8, 1, 61, 1, 1),
            _hist_player(5, "Scottie Barnes", "2021-present", "Current two-way watch", "Current franchise forward.", "Barnes' chase is toward the Siakam/Lowry tier if the Raptors return to deep series.", 95, 16.0, 45, 30, 8, 5, 6, 1, 0, 6, 0, 0, ["Pascal Siakam", "Kyle Lowry"], True),
        ],
    },
    "Phoenix Suns": {
        "context": "Suns history is full of brilliant runs without the final banner: Barkley, Nash, Booker, Westphal, and Durant's late chapter.",
        "legends": [
            _hist_player(1, "Charles Barkley", "1992-1996", "Finals-era force", "1993 Finals run; MVP.", "Barkley is the Suns' peak playoff superstar reference.", 1250, 26.6, 650, 230, 90, 40, 35, 22, 5, 47, 1, 0),
            _hist_player(2, "Steve Nash", "1996-1998, 2004-2012", "Seven Seconds engine", "Multiple Western Conference Finals runs.", "Nash is Phoenix's offensive identity standard.", 1500, 18.0, 230, 950, 80, 8, 180, 12, 1, 83, 0, 0),
            _hist_player(3, "Devin Booker", "2015-present", "Current scoring face", "2021 Finals run; elite playoff shot-maker.", "Booker is chasing Barkley's peak and Nash's sustained Suns memory.", 1500, 28.0, 300, 280, 65, 18, 140, 26, 8, 54, 1, 0, ["Charles Barkley", "Steve Nash", "Paul Westphal"], True),
            _hist_player(4, "Kevin Durant", "2023-present", "Current title-chase star", "All-time playoff scorer in a late Suns chapter.", "Durant's Suns legacy depends on whether individual scoring becomes a deep team run.", 420, 27.0, 115, 65, 18, 20, 45, 7, 2, 16, 0, 0, ["Charles Barkley", "Devin Booker"], True),
            _hist_player(5, "Paul Westphal", "1975-1980", "Finals-era guard", "1976 Finals run.", "Westphal is the older Suns guard standard before Nash and Booker.", 900, 22.0, 150, 300, 65, 12, 0, 10, 1, 41, 1, 0),
        ],
    },
    "Portland Trail Blazers": {
        "context": "Blazers history is Walton's title, Clyde's Finals years, Dame's shots, and a young group trying to find the next face.",
        "legends": [
            _hist_player(1, "Bill Walton", "1974-1979", "Championship big", "1977 champion and Finals MVP.", "Walton is Portland's only title standard.", 680, 18.2, 520, 160, 35, 85, 0, 6, 1, 37, 1, 1),
            _hist_player(2, "Clyde Drexler", "1983-1995", "Finals-era wing", "Two Finals runs with Portland.", "Drexler is the Blazers' sustained star-wing standard.", 2700, 22.2, 850, 730, 250, 90, 85, 28, 5, 121, 2, 0),
            _hist_player(3, "Damian Lillard", "2012-2023", "Modern icon", "Series-ending shots; 2019 WCF run.", "Dame owns Portland's modern shot-making mythology.", 1600, 25.7, 260, 380, 55, 18, 190, 24, 7, 61, 0, 0),
            _hist_player(4, "Brandon Roy", "2006-2011", "What-if star", "Iconic playoff scoring moments before injuries.", "Roy is the franchise's most painful modern what-if.", 380, 19.0, 90, 75, 18, 6, 25, 4, 0, 20, 0, 0),
            _hist_player(5, "Scoot Henderson", "2023-present", "Current guard watch", "Young guard starting a playoff file.", "Scoot needs series reps before the Dame/Clyde conversation is real.", 40, 10.0, 15, 18, 4, 1, 3, 0, 0, 4, 0, 0, ["Damian Lillard", "Clyde Drexler"], True),
        ],
    },
    "Atlanta Hawks": {
        "context": "Hawks history is Pettit's title-era greatness, Dominique's scoring, and Trae's modern conference-finals run.",
        "legends": [
            _hist_player(1, "Bob Pettit", "1954-1965", "Title-era giant", "1958 champion; all-time scoring big.", "Pettit is the franchise's championship-era foundation.", 2500, 25.5, 1500, 280, 0, 0, 0, 35, 8, 98, 4, 1),
            _hist_player(2, "Dominique Wilkins", "1982-1994", "Scoring icon", "Legendary playoff scoring duels.", "Dominique is Atlanta's athletic scoring identity.", 1900, 25.4, 520, 210, 85, 35, 40, 28, 6, 75, 0, 0),
            _hist_player(3, "Trae Young", "2018-present", "Current guard face", "2021 Eastern Conference Finals run.", "Trae is chasing Dominique for the clearest modern Hawks playoff identity.", 1200, 26.8, 120, 430, 45, 5, 130, 20, 5, 45, 0, 0, ["Dominique Wilkins", "Bob Pettit"], True),
            _hist_player(4, "Dikembe Mutombo", "1996-2001", "Defensive anchor", "Elite rim protection in Hawks playoff years.", "Mutombo is the defensive counterweight to Atlanta's scoring legends.", 400, 9.0, 520, 25, 25, 120, 0, 0, 0, 44, 0, 0),
            _hist_player(5, "Jalen Johnson", "2021-present", "Current wing watch", "Current two-way forward with upside.", "Johnson's chase starts with becoming the frontcourt bridge Atlanta needs for a deep run.", 90, 15.0, 45, 20, 6, 5, 5, 1, 0, 6, 0, 0, ["Dominique Wilkins"], True),
        ],
    },
})


def _default_franchise_history(team_name):
    prof = TEAM_PROFILES.get(team_name, {})
    starters = prof.get("starters", []) or []
    legends = []
    for idx, (name, role, context) in enumerate(_franchise_playoff_touchstones(team_name), start=1):
        legends.append(_hist_player(idx, name, "Franchise history", role.title(), context, f"{name} is a reference point for how {fan_nick(team_name)} fans talk about playoff impact.", 700 - idx * 60, 18.0 - idx, 180, 140, 35, 20, 20, max(0, 8 - idx), max(0, 2 - idx // 2), 40 - idx * 4))
    for nm in starters[:3]:
        if not any(x["name"] == nm for x in legends):
            legends.append(_hist_player(len(legends) + 1, nm, "Current era", "Current watch", "Current rotation player with a chance to add franchise playoff equity.", f"{nm} needs real series wins and repeat production to enter the franchise-history conversation.", 80, 14.0, 35, 25, 5, 4, 8, 1, 0, 6, current_watch=True))
    return {"context": f"{fan_nick(team_name)} history page uses curated fallback context until a deeper team-specific file is added.", "legends": legends}


def franchise_history_data(team_name):
    return FRANCHISE_HISTORY_DATA.get(team_name) or _default_franchise_history(team_name)


def _history_current_names(team_name):
    try:
        names = current_roster_names(team_name, limit=18)
    except Exception:
        names = []
    fallback = (TEAM_PROFILES.get(team_name, {}).get("starters") or []) + (TEAM_PROFILES.get(team_name, {}).get("subs") or [])
    out, seen = [], set()
    for n in list(names or []) + fallback:
        key = str(n).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(str(n))
    return out


def _is_current_history_player(player_name, current_names):
    p = str(player_name).strip().lower()
    return any(p == str(n).strip().lower() for n in current_names)


def _history_table_df(legends, current_names):
    rows = []
    for p in legends:
        cur = _is_current_history_player(p["name"], current_names) or bool(p.get("current_watch"))
        rows.append({
            "Rank": p["rank"], "Player": p["name"], "Era": p["era"], "Tier": p["tier"],
            "Playoff PTS (est.)": p["pts"], "Playoff PPG (est.)": p["ppg"], "REB (est.)": p["reb"],
            "AST (est.)": p["ast"], "STL (est.)": p["stl"], "BLK (est.)": p["blk"],
            "3PM (est.)": p["threes"], "30-pt games (est.)": p["g30"], "40-pt games (est.)": p["g40"],
            "Playoff GP (est.)": p["gp"], "Finals": p["finals"], "Titles": p["titles"],
            "Current": "Current Player" if cur else "",
        })
    return pd.DataFrame(rows)


def _history_card_html(team_name, p, current=False):
    e = html.escape
    current_badge = "<span class='hist-badge hist-badge-current'>Current Player</span>" if current else ""
    watch_badge = "<span class='hist-badge'>Franchise History Watch</span>" if p.get("current_watch") else ""
    img = e(headshot(p["name"]))
    logo = e(TEAM_LOGOS.get(team_name, ""))
    cls = "hist-card hist-card-current" if current else "hist-card"
    why = str(p.get("why", ""))
    if len(why) > 145:
        why = why[:142] + "..."
    return f"""
<div class="{cls}">
  <div class="hist-rank">#{int(p.get('rank', 0))}</div>
  <div class="hist-img-wrap"><img class="hist-head" src="{img}" alt=""/><img class="hist-logo" src="{logo}" alt=""/></div>
  <div class="hist-name">{e(p['name'])}</div>
  <div class="hist-era">{e(p.get('era', ''))}</div>
  <div class="hist-tier">{e(p.get('tier', ''))}</div>
  <div class="hist-copy"><b>{e(p.get('accomplishments', ''))}</b><br>{e(why)}</div>
  <div class="hist-badges">{current_badge}{watch_badge}</div>
</div>
"""


def _history_sort_col(label):
    return {
        "Total playoff points": "Playoff PTS (est.)",
        "Playoff scoring leaders (total PTS)": "Playoff PTS (est.)",
        "Playoff points per game": "Playoff PPG (est.)",
        "Rebounds": "REB (est.)",
        "Rebound leaders": "REB (est.)",
        "Assists": "AST (est.)",
        "Assist leaders": "AST (est.)",
        "Steals": "STL (est.)",
        "Blocks": "BLK (est.)",
        "Three-pointers": "3PM (est.)",
        "40-point playoff games": "40-pt games (est.)",
        "30-point playoff games": "30-pt games (est.)",
        "Playoff games played": "Playoff GP (est.)",
        "Finals appearances": "Finals",
        "Championships": "Titles",
    }.get(label, "Playoff PTS (est.)")


def _milestone_lines_for_player(player, legends):
    lines = []
    for stat, label, verb in [("pts", "points", "score"), ("ast", "assists", "create"), ("reb", "rebounds", "own the glass"), ("g30", "30-point playoff games", "stack scoring nights"), ("g40", "40-point playoff games", "author explosion games")]:
        val = float(player.get(stat, 0) or 0)
        higher = sorted([x for x in legends if x["name"] != player["name"] and float(x.get(stat, 0) or 0) > val], key=lambda x: float(x.get(stat, 0) or 0))
        if not higher:
            continue
        target = higher[0]
        gap = float(target.get(stat, 0) or 0) - val
        if stat == "pts":
            text = f"Needs about {int(round(gap))} playoff points to pass {target['name']} on this curated franchise scoring board."
        elif stat in ("g30", "g40"):
            text = f"Needs about {int(round(gap))} more {label} to pass {target['name']} and {verb} in franchise memory."
        else:
            text = f"Needs about {int(round(gap))} {label} to pass {target['name']} among these franchise playoff estimates."
        lines.append((label, text, min(0.98, val / max(float(target.get(stat, 1) or 1), 1))))
        if len(lines) >= 3:
            break
    if player.get("finals", 0) == 0:
        lines.append(("Tier jump", "One Conference Finals win or Finals run would move this from a stats chase into a different franchise-history tier.", 0.35))
    return lines[:4]


def _hist_mount_rushmore_html(team_name, legends):
    e = html.escape
    rush = sorted(legends, key=lambda x: (-int(x.get("titles", 0) or 0), int(x.get("rank", 99))))[:4]
    slots = []
    for p in rush:
        img = e(headshot(p["name"])) if not _validation_skip_network() else ""
        img_tag = f"<img src='{img}' alt=''/>" if img else ""
        slots.append(
            f"<div class='hist-rushmore-slot'>{img_tag}"
            f"<div class='hist-rushmore-name'>{e(p['name'])}</div>"
            f"<div class='hist-rushmore-era'>{e(p.get('tier', ''))}</div></div>"
        )
    return "<div class='hist-rushmore'>" + "".join(slots) + "</div>"


def _hist_milestone_countdown_html(team_name, current_entries, legends):
    e = html.escape
    cards = []
    for p in current_entries[:4]:
        for stat, label, verb in [("pts", "points", "score"), ("reb", "rebounds", "board"), ("g30", "30-pt games", "stack"), ("ast", "assists", "create")]:
            val = float(p.get(stat, 0) or 0)
            higher = sorted(
                [x for x in legends if x["name"] != p["name"] and float(x.get(stat, 0) or 0) > val],
                key=lambda x: float(x.get(stat, 0) or 0),
            )
            if not higher:
                continue
            target = higher[0]
            gap = int(round(float(target.get(stat, 0) or 0) - val))
            if gap <= 0:
                continue
            short = f"{gap} more {label}"
            sub = f"{p['name']} passes {target['name']} on the curated board"
            if stat == "pts":
                sub = f"{p['name'].split()[-1]} passes {target['name']} with {gap} more points."
            elif stat == "reb":
                sub = f"{p['name'].split()[-1]} enters top rebound tier with {gap} more boards."
            cards.append(
                f"<div class='hist-countdown'><div class='hist-countdown-num'>{gap}</div>"
                f"<div class='hist-countdown-lbl'>{e(label)} to pass {e(target['name'].split()[-1])}</div>"
                f"<div class='hist-countdown-sub'>{e(sub)}</div></div>"
            )
            break
    return "<div class='hist-countdown-grid'>" + "".join(cards) + "</div>" if cards else ""


def _hist_movement_tracker_html(current_entries, legends):
    e = html.escape
    moves = []
    for p in current_entries[:5]:
        for label, text, progress in _milestone_lines_for_player(p, legends)[:2]:
            moves.append(
                f"<div class='hist-move-card'><b>{e(p['name'])}</b> — {e(text)}"
                f"<div class='hist-progress' style='margin-top:8px'><span style='width:{max(5, min(98, progress * 100)):.0f}%'></span></div></div>"
            )
    return "<div class='hist-move-grid'>" + "".join(moves) + "</div>" if moves else ""


def _hist_greatest_runs_html(team_name):
    e = html.escape
    runs = FRANCHISE_GREAT_RUNS.get(team_name) or []
    if not runs:
        data = franchise_history_data(team_name)
        runs = [f"{p['name']} — {p.get('accomplishments', p.get('tier', ''))}" for p in sorted(data.get("legends", []), key=lambda x: -int(x.get("titles", 0) or 0))[:4]]
    items = "".join(f"<li>{e(r)}</li>" for r in runs[:5])
    return f"<ul class='hist-runs-list'>{items}</ul>"


def _hist_greatest_games_html(team_name):
    e = html.escape
    cards = []
    for score, copy in (FRANCHISE_GREAT_GAMES.get(team_name) or [])[:5]:
        cards.append(
            f"<div class='hist-game-card'><div class='hist-game-score'>{e(score)}</div>"
            f"<div class='hist-game-copy'>{e(copy)}</div></div>"
        )
    mx = get_display_matchup(team_name)
    s = mx.get("series") or {}
    for g in (s.get("games") or [])[:2]:
        score = str(g.get("Score", ""))
        if score and not any(score in c for c, _ in (FRANCHISE_GREAT_GAMES.get(team_name) or [])):
            winner = g.get("Winner", "")
            cards.append(
                f"<div class='hist-game-card'><div class='hist-game-score'>{e(score)}</div>"
                f"<div class='hist-game-copy'>{e(winner)} win · live Finals log</div></div>"
            )
    return "<div class='hist-games-grid'>" + "".join(cards[:6]) + "</div>" if cards else ""


def _hist_player_week_lines(p, legends, team_name):
    lines = []
    name = p["name"]
    val = float(p.get("pts", 0) or 0)
    higher_pts = sorted(
        [x for x in legends if x["name"] != name and float(x.get("pts", 0) or 0) > val],
        key=lambda x: float(x.get("pts", 0) or 0),
    )
    if higher_pts:
        gap = int(round(float(higher_pts[0].get("pts", 0) or 0) - val))
        lines.append(f"{gap} points from {higher_pts[0]['name'].split()[-1]}")
    reb_sorted = sorted(legends, key=lambda x: -float(x.get("reb", 0) or 0))
    rank_reb = next((i + 1 for i, x in enumerate(reb_sorted) if x["name"] == name), None)
    if rank_reb and rank_reb > 10:
        target = reb_sorted[9]
        gap = int(round(float(target.get("reb", 0) or 0) - float(p.get("reb", 0) or 0)))
        if gap > 0:
            lines.append(f"{gap} rebounds from top 10 playoff rebounders")
    if "wembanyama" in name.lower() and team_name == "San Antonio Spurs":
        lines.append("First Spurs playoff triple-double still on the franchise board")
    if "brunson" in name.lower() and team_name == "New York Knicks" and higher_pts:
        lines.append(f"Most likely pass: {higher_pts[0]['name']} on the scoring list this run")
    return lines[:3]


def _hist_active_milestones_week_html(team_name, current_entries, legends):
    e = html.escape
    cards = []
    for p in current_entries[:5]:
        week_lines = _hist_player_week_lines(p, legends, team_name)
        if not week_lines:
            continue
        inner = "".join(f"<div class='hist-week-line'>{e(ln)}</div>" for ln in week_lines)
        cards.append(
            f"<div class='hist-week-card'><div class='hist-week-name'>{e(p['name'])} · this week</div>{inner}</div>"
        )
    return "<div class='hist-week-grid'>" + "".join(cards) + "</div>" if cards else ""


def _comparison_card_html(cur, legend):
    e = html.escape
    ratio_pts = min(1.0, float(cur.get("pts", 0) or 0) / max(float(legend.get("pts", 1) or 1), 1))
    ratio_ppg = min(1.0, float(cur.get("ppg", 0) or 0) / max(float(legend.get("ppg", 1) or 1), 1))
    return f"""
<div class="hist-compare">
  <div class="hist-compare-top">
    <div><img src="{e(headshot(cur['name']))}" alt=""/><b>{e(cur['name'])}</b><span>Current chase</span></div>
    <div class="hist-vs">vs</div>
    <div><img src="{e(headshot(legend['name']))}" alt=""/><b>{e(legend['name'])}</b><span>{e(legend.get('tier','Legend'))}</span></div>
  </div>
  <div class="hist-mini-grid">
    <div><b>{cur.get('ppg', 0):.1f}</b><span>PPG est.</span></div><div><b>{legend.get('ppg', 0):.1f}</b><span>PPG est.</span></div>
    <div><b>{int(cur.get('pts', 0))}</b><span>PTS est.</span></div><div><b>{int(legend.get('pts', 0))}</b><span>PTS est.</span></div>
    <div><b>{int(cur.get('ast', 0))}</b><span>AST est.</span></div><div><b>{int(legend.get('ast', 0))}</b><span>AST est.</span></div>
    <div><b>{int(cur.get('reb', 0))}</b><span>REB est.</span></div><div><b>{int(legend.get('reb', 0))}</b><span>REB est.</span></div>
  </div>
  <div class="hist-meter"><span style="width:{ratio_pts * 100:.0f}%"></span></div>
  <div class="hist-meter-label">Total scoring chase: {ratio_pts * 100:.0f}% of {e(legend['name'])}'s curated estimate</div>
  <div class="hist-meter hist-meter-ppg"><span style="width:{ratio_ppg * 100:.0f}%"></span></div>
  <div class="hist-meter-label">Scoring-rate chase: {ratio_ppg * 100:.0f}% of the estimated PPG mark</div>
</div>
"""


def _inject_history_leaders_css():
    st.markdown(
        """
<style>
.hist-note { color:#475569; font-size:12px; line-height:1.45; margin:4px 0 12px; }
.hist-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:12px 0 16px; }
.hist-card { position:relative; border:1px solid var(--team-border); border-radius:18px; padding:14px; background:linear-gradient(180deg,#fff,var(--team-card-tint)); box-shadow:0 10px 26px rgba(15,23,42,.10); overflow:hidden; min-height:280px; transition:transform .15s ease, box-shadow .15s ease; }
.hist-card:hover { transform:translateY(-2px); box-shadow:0 14px 34px rgba(15,23,42,.14); }
.hist-card-current { border-width:2px; box-shadow:0 0 0 3px var(--team-accent-soft), 0 14px 32px rgba(15,23,42,.16); background:linear-gradient(165deg,var(--team-accent-soft),#fff 48%); }
.hist-leaders-hero { margin:0 0 12px; padding:12px 14px; border-radius:14px; background:linear-gradient(90deg,var(--team-accent-soft),transparent); border:1px solid var(--team-border); font-size:13px; color:#334155; line-height:1.45; }
.hist-rank { position:absolute; top:10px; right:12px; font-weight:950; color:var(--team-primary); font-size:1.1rem; }
.hist-img-wrap { position:relative; width:92px; height:78px; margin-bottom:8px; }
.hist-head { width:92px; height:68px; object-fit:cover; object-position:top center; border-radius:14px; background:#e2e8f0; }
.hist-logo { position:absolute; right:-8px; bottom:0; width:32px; height:32px; object-fit:contain; filter:drop-shadow(0 2px 6px rgba(0,0,0,.25)); }
.hist-name { font-size:1.02rem; font-weight:950; color:#0f172a; line-height:1.15; }
.hist-era { font-size:12px; color:#64748b; font-weight:700; margin-top:2px; }
.hist-tier { display:inline-block; margin-top:7px; font-size:11px; font-weight:900; color:#fff; background:linear-gradient(135deg,var(--team-primary),var(--team-accent)); border-radius:999px; padding:4px 9px; }
.hist-copy { margin-top:9px; color:#334155; font-size:12.5px; line-height:1.42; }
.hist-badges { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.hist-badge { display:inline-block; font-size:10px; font-weight:900; letter-spacing:.04em; text-transform:uppercase; padding:4px 7px; border-radius:999px; color:var(--team-primary); background:var(--team-accent-soft); border:1px solid var(--team-border); }
.hist-badge-current { color:#fff; background:var(--team-primary); }
.hist-section { margin:20px 0 8px; font-size:13px; font-weight:950; letter-spacing:.08em; text-transform:uppercase; color:#475569; border-bottom:1px solid rgba(100,116,139,.28); padding-bottom:7px; }
.hist-milestone-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; margin:10px 0 14px; }
.hist-milestone { border:1px solid rgba(100,116,139,.25); border-left:5px solid var(--team-accent); border-radius:14px; padding:12px; background:#fff; }
.hist-progress { height:8px; background:#e2e8f0; border-radius:999px; overflow:hidden; margin-top:8px; }
.hist-progress span { display:block; height:100%; background:linear-gradient(90deg,var(--team-primary),var(--team-accent)); border-radius:999px; }
.hist-compare-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:12px; margin:12px 0 16px; }
.hist-compare { border:1px solid var(--team-border); border-radius:18px; background:#fff; padding:12px; box-shadow:0 10px 24px rgba(15,23,42,.10); }
.hist-compare-top { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:10px; text-align:center; }
.hist-compare-top img { width:78px; height:58px; border-radius:12px; object-fit:cover; object-position:top center; background:#e2e8f0; display:block; margin:0 auto 4px; }
.hist-compare-top b { display:block; font-size:13px; color:#0f172a; }
.hist-compare-top span { display:block; font-size:11px; color:#64748b; }
.hist-vs { font-weight:950; color:var(--team-primary); }
.hist-mini-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:10px; }
.hist-mini-grid div { background:var(--team-card-tint); border-radius:10px; padding:7px; text-align:center; }
.hist-mini-grid b { display:block; color:#0f172a; }
.hist-mini-grid span { display:block; color:#64748b; font-size:10px; text-transform:uppercase; font-weight:800; }
.hist-meter { height:8px; background:#e2e8f0; border-radius:999px; overflow:hidden; margin-top:10px; }
.hist-meter span { display:block; height:100%; background:linear-gradient(90deg,var(--team-primary),var(--team-accent)); border-radius:999px; }
.hist-meter-ppg span { background:linear-gradient(90deg,#0f172a,var(--team-accent)); }
.hist-meter-label { font-size:11px; color:#64748b; margin-top:4px; }
.hist-rushmore { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:12px 0 16px; }
@media (max-width:720px) { .hist-rushmore { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.hist-rushmore-slot { text-align:center; border-radius:16px; padding:12px 8px; background:linear-gradient(180deg,var(--team-accent-soft),#fff); border:1px solid var(--team-border); }
.hist-rushmore-slot img { width:72px; height:60px; border-radius:12px; object-fit:cover; object-position:top center; background:#e2e8f0; }
.hist-rushmore-name { font-size:12px; font-weight:950; color:#0f172a; margin-top:6px; line-height:1.2; }
.hist-rushmore-era { font-size:10px; font-weight:800; color:#64748b; margin-top:2px; }
.hist-countdown-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; margin:10px 0 14px; }
.hist-countdown { border-radius:14px; padding:12px 14px; background:#fff; border:2px solid var(--team-primary); box-shadow:0 6px 18px rgba(15,23,42,.08); }
.hist-countdown-num { font-size:1.75rem; font-weight:950; color:var(--team-primary); line-height:1; }
.hist-countdown-lbl { font-size:11px; font-weight:900; color:#64748b; margin-top:4px; text-transform:uppercase; letter-spacing:.06em; }
.hist-countdown-sub { font-size:12px; font-weight:800; color:#334155; margin-top:6px; line-height:1.35; }
.hist-move-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:10px; margin:10px 0 14px; }
.hist-move-card { border-radius:14px; padding:12px; border-left:5px solid var(--team-accent); background:#fff; border:1px solid var(--team-border); font-size:13px; font-weight:800; color:#334155; line-height:1.4; }
.hist-runs-list { margin:8px 0 14px; padding:0; list-style:none; }
.hist-runs-list li { padding:10px 12px; margin-bottom:8px; border-radius:12px; background:var(--team-card-tint); border:1px solid var(--team-border); font-size:13px; font-weight:800; color:#334155; line-height:1.4; }
.hist-games-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin:10px 0 14px; }
.hist-game-card { border-radius:14px; padding:12px; background:#fff; border:1px solid var(--team-border); }
.hist-game-score { font-size:1.2rem; font-weight:950; color:#0f172a; }
.hist-game-copy { font-size:12px; font-weight:800; color:#64748b; margin-top:4px; line-height:1.35; }
</style>
""",
        unsafe_allow_html=True,
    )


def render_team_history_leaders_page(team_name):
    if _ultra_fast_active() and _validation_page_deferred("team_history"):
        _render_ultra_snapshot_history(team_name)
        _validation_offer_full_page("team_history", label="Load full Team History board")
        return
    _page_perf_tick("history_start")
    if _validation_mode_active():
        _render_validation_mode_banner()
    inject_team_brand_css(team_name)
    data = franchise_history_data(team_name)
    legends = sorted(data.get("legends", []), key=lambda x: int(x.get("rank", 999)))
    current_names = _history_current_names(team_name)
    current_entries = [p for p in legends if _is_current_history_player(p["name"], current_names) or p.get("current_watch")]
    _inject_history_leaders_css()
    render_fan_page_hero(team_name, f"{fan_nick(team_name)} Franchise Playoff Legends", data.get("context", "Franchise history and current-player chase board."), "TEAM HISTORY LEADERS")
    render_page_trust_strip("team_history")
    render_fan_product_shell_open()
    render_playoff_matchup_ribbon(team_name, _get_validation_playoff_state() if _validation_mode_active() else None)
    mx = get_display_matchup(team_name)
    if not mx["eliminated"]:
        st.caption(
            f"Live bracket: **{mx['round_short']}** · **{mx['series_record']}** vs {mx['opponent_nick']} · "
            f"**{mx['series_wins']}** series won — chase boards update as the run continues."
        )
    if _validation_page_deferred("team_history"):
        for p in sorted(data.get("legends", []), key=lambda x: int(x.get("rank", 99)))[:8]:
            st.markdown(f"**{p.get('rank')}. {html.escape(p.get('name', ''))}** — {html.escape(p.get('tier', ''))}")
        _validation_offer_full_page("team_history", label="Load full Team History board")
        return
    c1, c2 = st.columns(2)
    c1.metric("Legends on board", len(legends))
    c2.metric("Current players highlighted", len(current_entries))
    st.markdown(
        f"<div class='hist-leaders-hero'><b>{html.escape(fan_nick(team_name))} playoff history</b> — "
        f"legends set the bar; current roster names chase milestones on the curated board.</div>",
        unsafe_allow_html=True,
    )

    if current_entries:
        if render_fan_section("Active milestones this week", "📅", caption="What current players can still rewrite on the franchise board — curated estimates.", tone="broadcast"):
            render_fan_section_open()
        week_html = _hist_active_milestones_week_html(team_name, current_entries, legends)
        if week_html:
            st.markdown(week_html, unsafe_allow_html=True)
        render_fan_section_close()

        if render_fan_section("Milestone countdown", "⏱️", caption="How close current players are to the next franchise bar.", tone="broadcast"):
            render_fan_section_open()
        countdown = _hist_milestone_countdown_html(team_name, current_entries, legends)
        if countdown:
            st.markdown(countdown, unsafe_allow_html=True)
        else:
            st.caption("Countdown cards appear when a current player is on the curated board.")
        render_fan_section_close()

        if render_fan_section("Current-player movement tracker", "📈", caption="Live climb on the franchise ladder — curated estimates.", tone="broadcast"):
            render_fan_section_open()
        move_html = _hist_movement_tracker_html(current_entries, legends)
        if move_html:
            st.markdown(move_html, unsafe_allow_html=True)
        render_fan_section_close()

    if render_fan_section("Franchise Mount Rushmore", "🗿", caption="Four faces fans cite first in bar talk.", tone="default"):
        render_fan_section_open()
    st.markdown(_hist_mount_rushmore_html(team_name, legends), unsafe_allow_html=True)
    render_fan_section_close()

    if render_fan_section("Greatest playoff runs", "🏆", caption="Championship-tier chapters that set the franchise bar.", tone="default"):
        render_fan_section_open()
    st.markdown(_hist_greatest_runs_html(team_name), unsafe_allow_html=True)
    render_fan_section_close()

    if render_fan_section("Greatest playoff games", "🎬", caption="Signature nights fans still replay.", tone="default"):
        render_fan_section_open()
    st.markdown(_hist_greatest_games_html(team_name), unsafe_allow_html=True)
    render_fan_section_close()

    if render_fan_section("Franchise legends overview", "🏆", caption="Top franchise playoff icons on the curated board.", tone="default"):
        render_fan_section_open()
    st.markdown("<div class='hist-grid'>" + "".join(_history_card_html(team_name, p, current=(_is_current_history_player(p["name"], current_names) or p.get("current_watch"))) for p in legends[:10]) + "</div>", unsafe_allow_html=True)
    render_fan_section_close()

    with st.expander("Franchise playoff leaders (sortable table)", expanded=False):
        df_hist = _history_table_df(legends, current_names)
        sort_label = st.selectbox(
            "Leaderboard view",
            [
                "Playoff scoring leaders (total PTS)",
                "30-point playoff games",
                "40-point playoff games",
                "Playoff points per game",
                "Rebound leaders",
                "Assist leaders",
                "Steals",
                "Blocks",
                "Three-pointers",
                "Playoff games played",
                "Finals appearances",
                "Championships",
            ],
            key=f"history_sort_{team_name}",
        )
        show_df = df_hist.sort_values(_history_sort_col(sort_label), ascending=False).reset_index(drop=True)
        render_fan_stat_table(show_df, team_name)

    if render_fan_section("Current players climbing the list", "📈", caption="Roster names chasing franchise milestones.", tone="default"):
        render_fan_section_open()
    if current_entries:
        st.markdown("<div class='hist-grid'>" + "".join(_history_card_html(team_name, p, current=True) for p in current_entries) + "</div>", unsafe_allow_html=True)
    else:
        st.info("No current roster player is on this curated top board yet. A deep run is how someone starts forcing their way onto it.")
    render_fan_section_close()

    with st.expander("Deep dive: storylines, comparisons & milestone table", expanded=False):
        if current_entries:
            for p in current_entries:
                st.markdown(f"**{p['name']} history watch**")
                milestone_html = []
                for label, text, progress in _milestone_lines_for_player(p, legends):
                    milestone_html.append(
                        f"<div class='hist-milestone'><b>{html.escape(label.title())}</b><br>"
                        f"<span style='font-size:12px;color:#475569'>{html.escape(text)}</span>"
                        f"<div class='hist-progress'><span style='width:{max(5, min(98, progress * 100)):.0f}%'></span></div></div>"
                    )
                st.markdown("<div class='hist-milestone-grid'>" + "".join(milestone_html) + "</div>", unsafe_allow_html=True)
            rows = []
            for cur in current_entries:
                for label, text, _progress in _milestone_lines_for_player(cur, legends):
                    rows.append({"Player": cur["name"], "Milestone": label.title(), "What is within reach": text, "Data type": "Curated estimate"})
            render_fan_stat_table(pd.DataFrame(rows), team_name)
            cards = []
            by_name = {p["name"]: p for p in legends}
            for cur in current_entries[:3]:
                targets = [by_name[n] for n in cur.get("compare_to", []) if n in by_name] or [p for p in legends[:4] if p["name"] != cur["name"]]
                for target in targets[:2]:
                    cards.append(_comparison_card_html(cur, target))
            if cards:
                st.markdown("<div class='hist-compare-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)
        else:
            st.caption("Deep-dive milestone content appears when a current player is on the franchise board.")

    render_fan_product_shell_close()



# ==========================================================
# Dev Lab (developer / admin workspace)
# ==========================================================

_DEV_LAB_CACHE_FUNCTIONS = (
    (get_playoff_state_cached, "Playoff state engine"),
    (fetch_completed_games_recent, "Completed games (NBA API)"),
    (fetch_cdn_scoreboard_only, "CDN live scoreboard"),
    (_scoreboard_stats_today_et, "Stats scoreboard (today ET)"),
    (get_live_games, "CDN scoreboard (legacy)"),
    (featured_broadcast_state_cached, "Featured broadcast state"),
    (get_team_context_cached, "Team context"),
    (resolve_home_matchup_context_cached, "Home matchup context"),
    (playoff_game_logs_for_player, "Player playoff game logs"),
)


def _dev_lab_cache_stats_dataframe():
    rows = []
    for fn, label in _DEV_LAB_CACHE_FUNCTIONS:
        fp = _cache_data_fingerprint(fn)
        if fp:
            rows.append({"Cache function": label, **fp})
    return pd.DataFrame(rows) if rows else pd.DataFrame({"Cache function": [], "hits": [], "misses": []})


def _dev_lab_bracket_series_dataframe(stt):
    rows = []
    for round_label, coll in (
        ("NBA Finals", "finals"),
        ("Conference Finals", "cf"),
        ("Second Round", "second"),
        ("First Round", "first"),
    ):
        for key, s in (stt.get(coll) or {}).items():
            if not s:
                continue
            rows.append({
                "Round": s.get("round") or round_label,
                "Series key": key,
                "Team A": s.get("a"),
                "Team B": s.get("b"),
                "Score": f"{s.get('a_wins', 0)}–{s.get('b_wins', 0)}",
                "Winner": s.get("winner") or "—",
                "Games": len(s.get("games") or []),
                "Source": s.get("source") or "—",
            })
    return pd.DataFrame(rows)


def _dev_lab_api_probe(label, fn, *args, **kwargs):
    """Run one cached feed with timing for Dev Lab diagnostics."""
    t0 = pytime.perf_counter()
    err = None
    result = None
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        err = repr(exc)
    ms = (pytime.perf_counter() - t0) * 1000.0
    fp = _cache_data_fingerprint(fn)
    count = None
    if isinstance(result, list):
        count = len(result)
    elif isinstance(result, tuple) and result and isinstance(result[0], list):
        count = len(result[0])
    elif isinstance(result, dict):
        count = len(result)
    return {
        "Feed": label,
        "OK": err is None,
        "Ms": round(ms, 1),
        "Rows": count if count is not None else "—",
        "Cache hits": (fp or {}).get("hits", "—"),
        "Cache misses": (fp or {}).get("misses", "—"),
        "Error": (err or "")[:120],
    }


def _dev_lab_lineup_diagnostics(team_name, profile):
    opp = get_display_matchup(team_name).get("opponent") or profile.get("current_opponent")
    rows = []
    for tm in [team_name] + ([opp] if opp and opp in TEAM_PROFILES else []):
        meta = get_lineup_resolution_info(tm)
        starters = estimated_starters_from_api(tm)
        rows.append({
            "Team": tm,
            "Lineup source": meta.get("source", "—"),
            "Updated": meta.get("updated", "—"),
            "Starters": ", ".join(starters[:5]) if starters else "—",
            "Profile round": (TEAM_PROFILES.get(tm) or {}).get("round", "—"),
            "Effective round": get_effective_team_profile(tm).get("round", "—"),
        })
    return pd.DataFrame(rows)


def _render_dev_lab_product_docs():
    """Roadmap / priorities from docs/ — source of truth for product planning."""
    try:
        from product_docs import docs_root, list_doc_files, read_doc, roadmap_snapshot, workflow_checklist
    except ImportError as exc:
        st.warning(f"product_docs module unavailable: {exc}")
        return

    st.subheader("Product documentation (source of truth)")
    st.caption(
        f"Markdown lives in `{docs_root()}`. Required workflow: **docs/WORKFLOW.md**. "
        "Cursor: `.cursor/rules/nba-app-roadmap-docs.mdc`."
    )
    snap = roadmap_snapshot()

    def _metric_short(text: str, limit: int = 36) -> str:
        t = str(text or "—").strip()
        return t if len(t) <= limit else t[: limit - 1] + "…"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Docs last updated", snap.get("last_updated") or "—")
    m2.metric("Active priority", _metric_short(snap.get("active_priority")))
    m3.metric("Current milestone", _metric_short(snap.get("current_milestone")))
    systems = snap.get("systems") or []
    avg_pct = round(sum(s["pct"] for s in systems) / len(systems)) if systems else 0
    m4.metric("Systems avg completion", f"{avg_pct}%", help=f"{len(systems)} tracked systems")

    phase_doc = read_doc("PHASE_STABILITY.md")
    if phase_doc:
        st.markdown("##### Stability phase")
        st.caption("Authoritative charter: `docs/PHASE_STABILITY.md`")
        if st.button("Open PHASE_STABILITY.md", key="dev_open_phase_stability"):
            st.session_state["dev_lab_doc_pick"] = "PHASE_STABILITY.md"
        with st.expander("Live GC game-night checklist (P1)", expanded=False):
            st.markdown(
                "During a **live NBA game** on `dev`, verify:\n"
                "1. Trust strip shows **Status, Score, Clock, Source, Last updated** within ~60s refresh\n"
                "2. Run **2–3 auto-refresh cycles** — page must not freeze\n"
                "3. Score must **not** show fake **0–0** while game is in progress (Q1+ guard)\n"
                "4. If CDN fails: **last-known score** appears with stale banner\n"
                "5. **Emergency score entry** overrides feed until disabled\n"
                "6. Repeat with **LIVE_GC_SAFE_MODE** if full mode regresses\n\n"
                "Track pass/fail in **`docs/VALIDATION_STATUS.md`**."
            )
        log = st.session_state.get(LIVE_GC_VALIDATION_LOG_KEY) or []
        with st.expander("Live GC session log (last visits)", expanded=bool(log)):
            if log:
                st.dataframe(pd.DataFrame(log), use_container_width=True, hide_index=True)
                if st.button("Clear Live GC log", key="dev_clear_lgc_log"):
                    st.session_state.pop(LIVE_GC_VALIDATION_LOG_KEY, None)
                    st.rerun()
            else:
                st.caption("Open **Live Game Center** during a game to populate trust-strip ticks.")

    st.markdown("##### Cloud / repo validation scripts")
    st.code(
        "python scripts/validate_stability_phase.py\npython scripts/audit_lineups.py",
        language="bash",
    )
    if st.button("Open VALIDATION_STATUS.md", key="dev_open_validation_status"):
        st.session_state["dev_lab_doc_pick"] = "VALIDATION_STATUS.md"

    st.markdown("##### Active priority")
    st.info(snap.get("active_priority") or "Set `## Active priority` in docs/SYSTEMS_STATUS.md")

    st.markdown("##### Current milestone")
    st.success(snap.get("current_milestone") or "Set `## Current milestone` in docs/SYSTEMS_STATUS.md")

    st.markdown("##### Major systems — completion %")
    st.caption("From docs/SYSTEMS_STATUS.md — update when shipping or regressing.")
    if systems:
        for row in systems:
            label = f"{row['system']} ({row.get('doc', '')})" if row.get("doc") else row["system"]
            st.progress(row["pct"] / 100.0, text=f"{label} — {row['pct']}%")
    else:
        st.warning("No system rows parsed — check `## System completion` table in SYSTEMS_STATUS.md")

    with st.expander("Workflow checklist (required)", expanded=False):
        for line in workflow_checklist():
            st.markdown(f"- {line}")
        if snap.get("workflow"):
            st.markdown(snap["workflow"][:1200] + ("…" if len(snap.get("workflow", "")) > 1200 else ""))

    freshness = snap.get("freshness") or {}
    if freshness:
        with st.expander("Document freshness", expanded=False):
            fresh_rows = [{"File": k, "Last updated": v or "—"} for k, v in sorted(freshness.items())]
            st.dataframe(pd.DataFrame(fresh_rows), use_container_width=True, hide_index=True)

    blocks = (
        ("Current priorities (full)", snap.get("priorities")),
        ("Next milestones", snap.get("milestones")),
        ("Planned features", snap.get("planned")),
        ("Completed features", snap.get("completed")),
        ("Known issues", snap.get("known_issues")),
    )
    for title, body in blocks:
        with st.expander(title, expanded=False):
            if body:
                st.markdown(body)
            else:
                st.caption(f"No matching section in docs/ yet.")

    if snap.get("vision"):
        with st.expander("App vision (excerpt)", expanded=False):
            st.markdown(snap["vision"])

    st.divider()
    st.markdown("##### Source-of-truth feature docs")
    st.markdown(
        "- **Live Game Center** → `docs/LIVE_GAME_CENTER.md` (safe mode, layers, refresh, reliability)\n"
        "- **Playoff engine** → `docs/PLAYOFF_ENGINE.md` (bracket, advancement, elimination, offseason)"
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Open LIVE_GAME_CENTER.md", key="dev_open_lgc_doc"):
            st.session_state["dev_lab_doc_pick"] = "LIVE_GAME_CENTER.md"
    with c2:
        if st.button("Open PLAYOFF_ENGINE.md", key="dev_open_pe_doc"):
            st.session_state["dev_lab_doc_pick"] = "PLAYOFF_ENGINE.md"

    doc_paths = list_doc_files()
    if not doc_paths:
        st.info("No .md files in docs/ yet.")
        return
    names = [p.name for p in doc_paths]
    default = st.session_state.get("dev_lab_doc_pick", "WORKFLOW.md")
    if default not in names:
        default = names[0]
    pick = st.selectbox("Read full document", names, index=names.index(default), key="dev_lab_doc_pick")
    if pick:
        st.markdown(read_doc(pick))


def render_dev_lab_page(team_name, profile, page_t0=None):
    """Experimental sandbox — diagnostics and feature prototypes isolated from production UX."""
    t0 = page_t0 or pytime.perf_counter()
    use_demo, api_on = get_playoff_refresh_settings()

    st.markdown(
        "<div style='padding:10px 14px;border-radius:10px;background:#1e293b;color:#f8fafc;"
        "border:1px solid #475569;margin-bottom:12px'>"
        "<b>🛠️ Dev Lab</b> — developer workspace. Experiments here do not change production page layouts. "
        "Product roadmap: <b>Product docs</b> tab (reads <code>docs/*.md</code>). "
        "Set <code>DEV_MODE = False</code> to hide this page from the sidebar."
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("DEV_MODE", "ON" if DEV_MODE else "OFF")
    c2.metric("Safe mode (Live GC)", "ON" if LIVE_GC_SAFE_MODE else "OFF")
    c3.metric("API auto-sync", "ON" if api_on else "OFF")
    c4.metric("Demo fallback", "ON" if use_demo else "OFF")

    tab_docs, tab_snap, tab_team, tab_api, tab_cache, tab_live, tab_lineup, tab_bracket, tab_sandbox = st.tabs([
        "Product docs",
        "Playoff state",
        "Team status",
        "API feeds",
        "Cache stats",
        "Live GC",
        "Lineups",
        "Bracket",
        "Sandbox",
    ])

    with tab_docs:
        _render_dev_lab_product_docs()

    stt = get_merged_playoff_state(use_demo, api_on)

    with tab_snap:
        st.subheader("Unified playoff state snapshot")
        st.caption(
            f"TTL {PLAYOFF_STATE_CACHE_TTL_SEC}s · auto-refresh {PLAYOFF_BRACKET_REFRESH_MS // 1000}s on bracket pages · "
            f"source flags: api_refresh={api_on}, use_demo_backup={use_demo}"
        )
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("First-round series", len(stt.get("first") or {}))
        col_b.metric("Second-round series", len(stt.get("second") or {}))
        col_c.metric("Conference finals", len(stt.get("cf") or {}))
        st.dataframe(_dev_lab_bracket_series_dataframe(stt), use_container_width=True, hide_index=True)
        with st.expander("Raw state JSON (selected team context)", expanded=False):
            ctx = get_team_context_cached(team_name, use_demo, api_on)
            slim = {
                "team": team_name,
                "display_matchup": get_display_matchup(team_name, stt),
                "series_for_team": series_for_team(team_name),
                "home_matchup_fast": resolve_home_matchup_context_fast(team_name),
                "effective_profile": get_effective_team_profile(team_name, stt),
            }
            st.json(slim)
        if st.button("Clear playoff state cache", key="dev_clear_playoff_cache"):
            for fn in (get_playoff_state_cached, fetch_completed_games_recent, build_first_round_series_cached,
                       build_second_round_series_cached, build_conference_finals_series_cached, build_nba_finals_series_cached):
                try:
                    fn.clear()
                except Exception:
                    pass
            st.rerun()

    with tab_team:
        st.subheader("Team status table")
        st.dataframe(
            playoff_status_debug_dataframe(use_demo, api_on),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Compare static TEAM_PROFILES vs bracket engine for the selected team.")
        prof_static = TEAM_PROFILES.get(team_name) or {}
        prof_eff = get_effective_team_profile(team_name, stt)
        pst = get_team_playoff_status(team_name, stt)
        compare = pd.DataFrame([
            {"Field": "status", "Static profile": prof_static.get("status"), "Effective profile": prof_eff.get("status"), "Bracket engine": pst.get("status")},
            {"Field": "round", "Static profile": prof_static.get("round"), "Effective profile": prof_eff.get("round"), "Bracket engine": pst.get("current_round")},
            {"Field": "opponent", "Static profile": prof_static.get("current_opponent"), "Effective profile": prof_eff.get("current_opponent"), "Bracket engine": pst.get("current_opponent")},
            {"Field": "series record", "Static profile": "—", "Effective profile": get_display_matchup(team_name, stt).get("series_record"), "Bracket engine": pst.get("series_record")},
        ])
        st.dataframe(compare, use_container_width=True, hide_index=True)

    with tab_api:
        st.subheader("API feed diagnostics")
        probes = [
            _dev_lab_api_probe("Completed games (playoffs)", fetch_completed_games_recent, api_refresh=api_on),
            _dev_lab_api_probe("CDN scoreboard", fetch_cdn_scoreboard_only),
            _dev_lab_api_probe("Stats today (ET)", _scoreboard_stats_today_et),
            _dev_lab_api_probe("Featured broadcast", featured_broadcast_state_cached, team_name),
        ]
        st.dataframe(pd.DataFrame(probes), use_container_width=True, hide_index=True)
        st.caption(f"NBA_LIVE_AVAILABLE={NBA_LIVE_AVAILABLE} · NBA_STATS_AVAILABLE={NBA_STATS_AVAILABLE} · NBA_SCOREBOARD_V3_AVAILABLE={NBA_SCOREBOARD_V3_AVAILABLE}")
        if st.button("Refresh API probes", key="dev_refresh_api_probes"):
            for fn in (fetch_completed_games_recent, fetch_cdn_scoreboard_only, _scoreboard_stats_today_et, featured_broadcast_state_cached):
                try:
                    fn.clear()
                except Exception:
                    pass
            st.rerun()

    with tab_cache:
        st.subheader("Cache statistics")
        st.dataframe(_dev_lab_cache_stats_dataframe(), use_container_width=True, hide_index=True)
        st.caption("Streamlit `@st.cache_data` hit/miss counts for major feeds.")

    with tab_live:
        st.subheader("Live Game Center diagnostics")
        eff = get_effective_team_profile(team_name)
        t1 = pytime.perf_counter()
        state = _resolve_live_gc_layer1_fast(team_name, eff)
        resolve_ms = (pytime.perf_counter() - t1) * 1000.0
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Layer 1 resolve", f"{resolve_ms:.0f} ms")
        m2.metric("Priority", state.get("priority") or "—")
        m3.metric("Source", str(state.get("source_label") or "—")[:24])
        m4.metric("CDN OK", "Yes" if state.get("cdn_ok") else "No")
        parsed = state.get("parsed") or {}
        if parsed:
            st.json({
                "phase": parsed.get("phase"),
                "score": f"{parsed.get('away_score')}–{parsed.get('home_score')}",
                "period": parsed.get("period"),
                "clock": parsed.get("clock"),
                "opp": parsed.get("opp_name"),
            })
        else:
            st.info(state.get("feed_banner") or "No live row parsed for the selected team.")
        opp = parsed.get("opp_name") or eff.get("current_opponent")
        _render_live_gc_debug(
            team_name,
            opp,
            layer1_loaded=True,
            live_attempted=True,
            live_count=state.get("live_count"),
            errors=state.get("errors"),
            state=state,
            section_ms={"layer1_resolve": resolve_ms},
            force=True,
        )
        with st.expander("Live GC trace (session)", expanded=False):
            trace = st.session_state.get("live_gc_trace") or []
            if trace:
                t0_trace = trace[0].get("t", 0)
                trace_rows = [{
                    "Δms": round((ev.get("t", 0) - t0_trace) * 1000.0, 1),
                    "event": ev.get("event"),
                    "ms": ev.get("ms"),
                    "count": ev.get("count"),
                    "error": (str(ev.get("error"))[:80] if ev.get("error") else ""),
                } for ev in trace[-30:]]
                st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
            else:
                st.caption("No live_gc_trace entries yet — open Live Game Center or re-run Layer 1 above.")

    with tab_lineup:
        st.subheader("Lineup diagnostics")
        st.dataframe(_dev_lab_lineup_diagnostics(team_name, profile), use_container_width=True, hide_index=True)
        hctx = resolve_home_matchup_context_fast(team_name)
        st.caption(f"Home matchup mode: **{hctx.get('mode')}** · round: **{hctx.get('round_label')}**")
        with st.expander("Home matchup context (raw)", expanded=False):
            st.json(hctx)

    with tab_bracket:
        st.subheader("Bracket diagnostics")
        st.dataframe(_dev_lab_bracket_series_dataframe(stt), use_container_width=True, hide_index=True)
        for conf, key in (("East", "east_cf"), ("West", "west_cf")):
            cf = stt.get(key)
            if cf:
                st.markdown(f"**{conf} Conference Finals**")
                for k, s in cf.items():
                    st.write(f"{k}: {s.get('a')} vs {s.get('b')} ({s.get('a_wins')}-{s.get('b_wins')})")
            else:
                st.caption(f"{conf} CF shell: waiting on second-round winners or API games.")
        nf = stt.get("finals") or {}
        if nf:
            st.markdown("**NBA Finals**")
            for k, s in nf.items():
                st.write(f"{k}: {s.get('a')} vs {s.get('b')}")
        else:
            st.caption("Finals shell: not formed yet.")

    with tab_sandbox:
        st.subheader("Feature sandbox")
        st.caption("Build and test new widgets here before promoting them to production pages.")
        st.markdown("##### Widget smoke test")
        st.write("Drop experimental Streamlit widgets in this tab during development.")
        demo = st.selectbox("Sandbox control", ["Metric card", "Dataframe", "JSON dump"], key="dev_sandbox_demo")
        if demo == "Metric card":
            st.metric("Sandbox metric", "OK", delta="test")
        elif demo == "Dataframe":
            st.dataframe(pd.DataFrame({"col": [1, 2, 3]}), use_container_width=True)
        else:
            st.json({"sandbox": True, "team": team_name, "page": "Dev Lab"})
        st.markdown("##### Franchise history module")
        hist = franchise_history_data(team_name)
        st.caption(f"Legends on board: {len(hist.get('legends') or [])} · context: {str(hist.get('context', ''))[:80]}…")
        if st.checkbox("Preview history card HTML", key="dev_hist_preview"):
            legends = sorted(hist.get("legends", []), key=lambda x: int(x.get("rank", 999)))[:3]
            current_names = _history_current_names(team_name)
            if legends:
                st.markdown(
                    "<div class='hist-grid'>"
                    + "".join(_history_card_html(team_name, p, current=_is_current_history_player(p["name"], current_names))
                    for p in legends)
                    + "</div>",
                    unsafe_allow_html=True,
                )

    elapsed_ms = (pytime.perf_counter() - t0) * 1000.0
    st.divider()
    st.subheader("Page render timing")
    t1, t2, t3 = st.columns(3)
    t1.metric("Dev Lab render", f"{elapsed_ms:.0f} ms")
    t2.metric("Selected team", team_name)
    t3.metric("Branch target", "dev (see git workflow)")


# ==========================================================
# Sidebar
# ==========================================================
PAGES={
    "🏠 Home Dashboard":"Home Dashboard",
    "🔴 Live Game Center":"Live Game Center",
    "🏆 Playoff Bracket":"Playoff Bracket",
    "📋 Matchup Lineups":"Matchup Lineups",
    "🧠 Matchup Intelligence":"Matchup Intelligence",
    "📈 Player Playoff Tracker":"Player Playoff Tracker",
    "👑 Legacy Tracker":"Legacy Tracker",
    "📚 Team History Leaders":"Team History Leaders",
    "📜 Previous Rounds":"Previous Rounds",
}

PAGE_LABEL_ALIASES = {
    "🏀 Home Dashboard": "🏠 Home Dashboard",
    "🏀 Live Game Center": "🔴 Live Game Center",
    "🏀 Playoff Bracket": "🏆 Playoff Bracket",
    "🏛️ Team History Leaders": "📚 Team History Leaders",
    "🏀 Matchup Lineups": "📋 Matchup Lineups",
    "🧠 Matchup Intelligence": "🧠 Matchup Intelligence",
    "🏀 Player Playoff Tracker": "📈 Player Playoff Tracker",
    "🏀 Legacy Tracker": "👑 Legacy Tracker",
    "🏀 Previous Rounds": "📜 Previous Rounds",
    "🛠️ Dev Lab": "🛠️ Dev Lab",
}

def _sidebar_team_label(team_name, stt=None):
    """Mark eliminated teams so offseason Home sections are easy to find in the picker."""
    try:
        if get_team_playoff_status(team_name, stt).get("status") == "eliminated":
            return f"📋 {team_name} (offseason outlook)"
    except Exception:
        if _is_home_eliminated(team_name):
            return f"📋 {team_name} (offseason outlook)"
    return team_name


# ==========================================================
# Headless / test API — pure logic, no Streamlit UI at import
# ==========================================================
def get_playoff_state_snapshot(use_demo_backup=True, api_refresh=False):
    """Unified playoff bracket snapshot for scripts and unit tests."""
    return get_playoff_state_cached(use_demo_backup=use_demo_backup, api_refresh=api_refresh)


def calculate_win_probability(team_name, opp_name, margin, period, is_home, box_df=None):
    """Win-probability model without UI dependencies."""
    return live_win_probability(team_name, opp_name, margin, period, is_home, box_df=box_df)


def resolve_live_game_state(team_name, profile=None, *, network=True):
    """
    Live Game Center resolver for tests and diagnostics.
    Set network=False to skip CDN/stats fetches (profile context only).
    """
    profile = profile or get_effective_team_profile(team_name)
    if not network:
        opp, rnd, series_text = _live_gc_profile_context(team_name, profile)[:3]
        return {
            "layer": 1,
            "priority": "profile",
            "source_label": "profile (no network)",
            "parsed": None,
            "profile": profile,
            "opponent": opp,
            "round": rnd,
            "series_text": series_text,
        }
    return _resolve_live_gc_layer1_fast(team_name, profile)


def _curated_starters_list(team_name):
    curated = CURRENT_PLAYOFF_LINEUPS.get(team_name) or {}
    prof = TEAM_PROFILES.get(team_name) or {}
    fallback = prof.get("starters") or ["TBD"] * 5
    return [curated.get(s) or fallback[i] for i, s in enumerate(LINEUP_SLOTS)]


def build_lineup_matchups(team_name, opp_name):
    """Position-by-position lineup board data — no Streamlit rendering."""
    if _lineups_use_curated_board(team_name):
        t_starters = _curated_starters_list(team_name)
        o_starters = _curated_starters_list(opp_name)
        t_meta = {"source": "curated playoff board"}
        o_meta = {"source": "curated playoff board"}
        t_bench = _curated_bench_list(team_name, 5)
        o_bench = _curated_bench_list(opp_name, 5)
    elif _validation_mode_active():
        t_starters = _curated_starters_list(team_name)
        o_starters = _curated_starters_list(opp_name)
        t_meta = {"source": "curated playoff override (validation)"}
        o_meta = {"source": "curated playoff override (validation)"}
        t_bench = _curated_bench_list(team_name, 5)
        o_bench = _curated_bench_list(opp_name, 5)
    else:
        t_meta = get_lineup_resolution_info(team_name)
        o_meta = get_lineup_resolution_info(opp_name)
        t_starters = estimated_starters_from_api(team_name)
        o_starters = estimated_starters_from_api(opp_name)
        t_bench = list(estimated_bench_from_api(team_name)[:5])
        o_bench = list(estimated_bench_from_api(opp_name)[:5])
    matchups = []
    for i, pos in enumerate(LINEUP_SLOTS):
        tp = t_starters[i] if i < len(t_starters) else "TBD"
        op = o_starters[i] if i < len(o_starters) else "TBD"
        matchups.append({"position": pos, "team_player": tp, "opp_player": op})
    return {
        "team": team_name,
        "opponent": opp_name,
        "matchups": matchups,
        "team_bench": t_bench,
        "opp_bench": o_bench,
        "team_meta": t_meta,
        "opp_meta": o_meta,
    }


def main():
    """Streamlit app entry — sidebar, routing, and page rendering."""
    global USE_DEMO_BACKUP, ENABLE_BRACKET_API_REFRESH, SHOW_PERF_DEBUG, QA_MODE, ULTRA_FAST_VALIDATION_MODE

    boot_t0 = pytime.perf_counter()
    _configure_app_shell()
    boot_t = boot_t0
    _set_lgc_route_skip_bracket_api(False)

    try:
        from suite_workspace import init_suite_workspace

        init_suite_workspace(st)
    except Exception:
        pass

    try:
        from suite_resume_launch import apply_suite_resume_launch

        apply_suite_resume_launch(st, "nba")
    except Exception:
        pass

    try:
        from applied_math_return_insight import hydrate_investment_ami_return_state, insight_return_query_id

        if insight_return_query_id(st) or str(st.query_params.get("suite_ai_question_id") or "").strip():
            hydrate_investment_ami_return_state(st, "nba")
    except Exception:
        pass

    nba_restored = False
    try:
        from nba_persistent_state import prepare_nba_workspace

        nba_restored = prepare_nba_workspace(st)
    except Exception as exc:
        st.session_state["_nba_restore_error"] = str(exc)[:240]

    _sync_validation_mode_globals()

    try:
        import portfolio_polish as _pp_header
        if not _pp_header.is_screenshot_mode(st):
            try:
                from suite_workspace import get_active_workspace_id, workspace_label as _nba_ws_label

                _pp_header.render_nba_suite_header(
                    st,
                    workspace_label=_nba_ws_label(get_active_workspace_id(st)),
                )
            except Exception:
                _pp_header.render_nba_suite_header(st)
    except Exception:
        pass

    if _is_lgc_route_early():
        _run_lgc_emergency_route(boot_t0)
        return

    try:
        from nba_persistent_state import (
            autosave_nba_state,
            default_reset_nba_session,
        )
        from suite_user_persistence import render_reset_controls, show_persistence_messages

        show_persistence_messages(st)
        render_reset_controls(
            st,
            "nba",
            on_reset=default_reset_nba_session,
            help_text="Clears saved team, page, toggles, local disk, and cloud session. Playoff data caches are not deleted.",
        )
    except Exception:
        pass

    try:
        from suite_command_center_link import render_command_center_sidebar_link

        render_command_center_sidebar_link(st)
    except Exception:
        pass

    import portfolio_polish as pp
    import portfolio_demo as pdemo

    pp.render_sidebar_toggle(st)
    if pp.is_demo_mode(st):
        pdemo.ensure_global_demo_seed(st)

    team_keys_sorted = sorted(TEAM_PROFILES.keys())

    _restore_team = st.session_state.pop("_nba_restore_team", None)
    if _restore_team and _restore_team in team_keys_sorted:
        st.session_state[NBA_TEAM_SELECT_KEY] = _restore_team
        st.session_state["favorite_team"] = _restore_team
    elif NBA_TEAM_SELECT_KEY not in st.session_state:
        _saved_team = st.session_state.get("favorite_team")
        if _saved_team in team_keys_sorted:
            st.session_state[NBA_TEAM_SELECT_KEY] = _saved_team
        elif not nba_restored and "_nba_restore_error" not in st.session_state:
            st.session_state[NBA_TEAM_SELECT_KEY] = (
                "New York Knicks" if "New York Knicks" in team_keys_sorted else team_keys_sorted[0]
            )

    _val_stt = _get_validation_playoff_state() if _validation_mode_active() else None
    _set_lgc_route_skip_bracket_api(_peek_sidebar_page_key() == "Live Game Center")
    _pre_lgc_stt = _get_lgc_local_playoff_state() if _lgc_route_skip_bracket_api_active() else None
    _sidebar_stt = _val_stt or _pre_lgc_stt
    favorite_team = st.sidebar.selectbox(
        "Choose your 2026 NBA playoff team",
        team_keys_sorted,
        key=NBA_TEAM_SELECT_KEY,
        format_func=(lambda tn: _sidebar_team_label(tn, _sidebar_stt)) if _sidebar_stt else _sidebar_team_label,
    )
    st.session_state["favorite_team"] = favorite_team

    st.sidebar.markdown("### Load speed")
    st.sidebar.caption("Use fast load while testing workspace profiles or slow networks.")
    QA_MODE = st.sidebar.toggle(
        "Fast load",
        value=bool(st.session_state.get("QA_MODE", False)),
        key="QA_MODE",
        help="Skips heavy NBA API calls, bracket sync, autorefresh, and defers expensive page sections.",
    )
    ULTRA_FAST_VALIDATION_MODE = st.sidebar.toggle(
        "Lite mode (no network)",
        value=bool(st.session_state.get("ULTRA_FAST_VALIDATION_MODE", False)),
        key="ULTRA_FAST_VALIDATION_MODE",
        help="Fastest startup: demo snapshots and placeholders only — no live API, CDN, or Plotly.",
    )
    _sync_validation_mode_globals()
    if _validation_mode_active():
        _render_validation_mode_banner()
    elif pp.is_demo_mode(st):
        USE_DEMO_BACKUP = True
        ENABLE_BRACKET_API_REFRESH = False
    else:
        USE_DEMO_BACKUP = st.sidebar.toggle(
            "Use playoff fallback when API is empty",
            value=True,
            help="When NBA.com returns no completed games for a series, show bundled local scores so the bracket never looks blank.",
        )
        ENABLE_BRACKET_API_REFRESH = st.sidebar.toggle(
            "Auto-sync bracket from NBA API",
            value=True,
            help="Pull completed playoff games on a timer (about every 60s) so series scores and advancement update without code edits.",
        )

    from suite_analytical_question import render_applied_math_sidebar_entry

    _nba_ami_page = str(
        st.session_state.get("page_label_last")
        or st.session_state.get("page_override")
        or "🏠 Home Dashboard"
    )
    try:
        from applied_math_context import build_nba_applied_math_context, build_source_state
    except Exception:
        build_nba_applied_math_context = None  # type: ignore[misc, assignment]
        build_source_state = None  # type: ignore[misc, assignment]

    render_applied_math_sidebar_entry(
        st,
        source_app="nba",
        source_page=_nba_ami_page,
        session_state=st.session_state,
        developer_mode=can_show_developer_tools(st=st),
        context_extra_builder=(
            (lambda: {"team": favorite_team, "page": _nba_ami_page, "fast_load": True})
            if _validation_mode_active()
            else (
                lambda: build_nba_applied_math_context(_nba_ami_page, st.session_state)
                if build_nba_applied_math_context
                else {"team": favorite_team, "page": _nba_ami_page}
            )
        ),
        source_state_builder=(
            lambda: build_source_state(_nba_ami_page, st.session_state)
            if build_source_state
            else None
        ),
    )

    if is_developer_workspace(st=st) and not DEV_MODE:
        st.sidebar.toggle(
            "Enable Dev Lab (developer)",
            value=False,
            key="dev_lab_enabled",
            help="Show the Dev Lab page for testing features without affecting the main fan experience.",
        )
    elif is_developer_workspace(st=st) and DEV_MODE:
        st.sidebar.caption("🛠️ Dev mode — Dev Lab visible")
    if pp.show_sidebar_debug(st):
        SHOW_PERF_DEBUG = st.sidebar.toggle(
            "Show performance debug",
            value=False,
            help="Shows page timing, playoff state debug table, and cache mode details.",
        )
        st.sidebar.caption(
            f"Deploy {APP_DEPLOY_BRANCH} · build {APP_BUILD_COMMIT[:12]}"
        )
        if _ultra_fast_active():
            st.sidebar.caption(
                "Ultra-fast: no network — fan UI still renders; APIs/plots skipped where gated."
            )
        elif QA_MODE:
            st.sidebar.caption("QA mode: demo bracket + session snapshot; fan UI sections stay visible.")
        if SHOW_PERF_DEBUG:
            render_playoff_state_debug_expander("sidebar")
    else:
        SHOW_PERF_DEBUG = False
    boot_t = _page_perf_startup_tick("sidebar_toggles", boot_t) if st.session_state.get(PAGE_PERF_KEY) else boot_t
    pages = dict(PAGES)
    if dev_lab_visible():
        pages["🛠️ Dev Lab"] = "Dev Lab"
    labels = list(pages.keys())
    _page_restore = st.session_state.pop("page_override", None)
    if _page_restore:
        _alias = PAGE_LABEL_ALIASES.get(_page_restore, _page_restore)
        if _alias in labels:
            st.session_state[NBA_PAGE_RADIO_KEY] = _alias
    elif NBA_PAGE_RADIO_KEY not in st.session_state:
        _last = st.session_state.get("page_label_last")
        if _last in labels:
            st.session_state[NBA_PAGE_RADIO_KEY] = _last
        else:
            st.session_state[NBA_PAGE_RADIO_KEY] = "🏠 Home Dashboard"
    if st.session_state.get(NBA_PAGE_RADIO_KEY) not in labels:
        _last = st.session_state.get(NBA_PAGE_RADIO_KEY)
        _mapped = PAGE_LABEL_ALIASES.get(str(_last), str(_last)) if _last else None
        if _mapped in labels:
            st.session_state[NBA_PAGE_RADIO_KEY] = _mapped
        else:
            st.session_state[NBA_PAGE_RADIO_KEY] = "🏠 Home Dashboard"
    page_label = st.sidebar.radio("Choose page", labels, key=NBA_PAGE_RADIO_KEY)
    st.session_state["_nba_persist_team"] = favorite_team
    st.session_state["page_label_last"] = page_label
    page = pages[page_label]
    _set_lgc_route_skip_bracket_api(page == "Live Game Center")
    _lgc_stt = _get_lgc_local_playoff_state() if page == "Live Game Center" else None
    profile = get_effective_team_profile(
        favorite_team, _val_stt if _validation_mode_active() else _lgc_stt
    )
    inject_team_brand_css(favorite_team)
    app_page_t0 = pytime.perf_counter()
    _page_perf_begin(page)
    perf = st.session_state.get(PAGE_PERF_KEY) or {}
    perf.setdefault("sections", {})["startup_before_page"] = (app_page_t0 - boot_t0) * 1000.0

    playoff_auto_refresh_pages = {
        "Home Dashboard",
        "Live Game Center",
        "Playoff Bracket",
        "Previous Rounds",
        "Legacy Tracker",
        "Matchup Lineups",
        "Matchup Intelligence",
        "Player Playoff Tracker",
        "Dev Lab",
    }
    if page in playoff_auto_refresh_pages:
        tick_playoff_state_autorefresh(page.replace(" ", "_").lower())

    from suite_analytical_question import render_suite_applied_math_insight

    render_suite_applied_math_insight(st, source_app="nba", source_page=page)

    if page == "Home Dashboard":
        render_playoff_command_center(favorite_team)
    elif page == "Playoff Bracket":
        render_bracket(favorite_team)
    elif page == "Team History Leaders":
        render_team_history_leaders_page(favorite_team)
    elif page == "Matchup Intelligence":
        render_matchup_intelligence(favorite_team)
    elif page == "Previous Rounds":
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
        if _is_home_eliminated(favorite_team):
            st.warning("This team is eliminated, so current matchup lineups are not active.")
        else:
            render_matchup_lineups_page(favorite_team, profile)
    elif page == "Dev Lab":
        render_dev_lab_page(favorite_team, profile, page_t0=app_page_t0)

    _page_perf_finish()
    _render_page_perf_report(page, favorite_team)

    if SHOW_PERF_DEBUG and pp.show_sidebar_debug(st):
        elapsed_ms = (pytime.perf_counter() - app_page_t0) * 1000
        with st.expander("Performance debug", expanded=False):
            st.caption(f"Page rendered in {elapsed_ms:.0f} ms.")
            st.caption(f"Page: {page} · Team: {favorite_team}")
            st.caption(f"QA mode: {'on' if QA_MODE else 'off'} · Ultra-fast: {'on' if ULTRA_FAST_VALIDATION_MODE else 'off'}")
            st.caption(f"Playoff fallback when API empty: {'on' if USE_DEMO_BACKUP else 'off'}")
            st.caption(f"Bracket NBA API auto-sync: {'on' if ENABLE_BRACKET_API_REFRESH and not _validation_mode_active() else 'off'}")
            if _validation_mode_active():
                st.caption("Validation gates: " + ", ".join(k for k, v in _validation_gates_status().items() if v))
            st.caption(f"Playoff state cache TTL: {PLAYOFF_STATE_CACHE_TTL_SEC}s · auto-refresh: {PLAYOFF_BRACKET_REFRESH_MS // 1000}s on bracket pages")
            st.caption("Heavy live feeds, player logs, injuries, and raw rotation tables are cached and/or behind buttons or expanders where possible.")

    if not pp.skip_background_persistence(st):
        try:
            sig = (favorite_team, page_label or page)
            if st.session_state.get("_suite_activity_sig") != sig:
                st.session_state["_suite_activity_sig"] = sig
                from nba_activity import log_from_page_context

                log_from_page_context(favorite_team, page, page_label)
        except Exception:
            pass

        try:
            from nba_persistent_state import autosave_nba_state

            autosave_nba_state(st)
        except Exception:
            pass

    if not pp.is_capture_mode(st):
        st.divider()
        st.caption("Daniel Cohen — NBA Playoff Companion AI | live bracket sync | automatic series tracking | previous rounds | live game center")


if __name__ == "__main__":
    main()
