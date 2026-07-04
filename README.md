# Daniel Cohen — NBA Playoff Companion AI

**A fan-first playoff command center** built with Python and Streamlit for the 2026 NBA playoffs: live games, bracket context, matchup intelligence, player stories, franchise history, and offseason outlooks — with account-owned workspace isolation in the Daniel Cohen AI Suite.

**Live demo:** [nba-playoff-companion-ai.streamlit.app](https://nba-playoff-companion-ai-gd4sx677quejdfkvappv6o.streamlit.app)  
**Deploy branch:** `dev` · **Entry point:** `streamlit_app.py`

Built as part of the **Daniel Cohen AI Suite** (shared workspace auth, cloud persistence, and Command Center handoffs).

**Product docs:** [`docs/`](docs/) — vision, pages, and development priorities.

---

## Executive Summary

Most NBA apps are generic stat sites. This app is a **playoff command center for one favorite team** — 10+ fan-facing pages spanning live game center, bracket tracking, matchup intelligence, player and legacy stories, franchise history, and offseason outlooks, backed by a fast-load shell, CDN scoreboard ingestion, curated playoff rotations, and workspace-scoped persistence in the Daniel Cohen AI Suite.

The goal is to help fans follow their team through the playoffs with trustworthy live context, matchup intelligence, player stories, and postseason continuity — not just box scores.

NBA Playoff Companion AI answers:

- Where is my team in the bracket?
- What's live right now — and is the data trustworthy?
- How do lineups match up tonight?
- Which players are defining the series?
- What did we accomplish — and what's next if we're out?

The app is designed as a portfolio piece demonstrating **live API integration, fan UX, multiplayer-ready persistence patterns, and suite workspace architecture** — not a box-score dump.

---

## Example Questions This App Can Help Answer

**Playoff Context**
- Where is my team in the bracket right now?
- What is the current series score and who do we play next?
- Has my team been eliminated — and what happens on the dashboard after that?

**Live Games**
- What games are live right now?
- Is the scoreboard data current or in safe/demo mode?
- What does the box score look like for the game I'm following?

**Matchups & Lineups**
- How do tonight's likely lineups compare?
- Which rotation players matter most in this matchup?
- Are we relying on curated playoff rotations or stale depth-chart data?

**Players & Legacy**
- Which players are driving this playoff run?
- Who should I track in the Legacy Tracker?
- How is a player's playoff performance trending across rounds?

**Franchise & Offseason**
- What does our playoff history look like?
- What did previous rounds tell us about this team?
- If we're out, what is the offseason outlook?

---

## At a Glance

| | |
|---|---|
| **Role** | Full-stack Python sports app — live data ingestion, playoff-native UX, and test-driven persistence |
| **Stack** | Python 3.11+ · Streamlit · pandas · NBA CDN/API feeds · optional Supabase · suite deep links |
| **Scale** | 10+ fan-facing pages · fast-load shell · deferred workspace sync · playoff tracker + legacy |
| **Differentiators** | One favorite team at a time · honest live-state banners · curated playoff rotations · workspace-scoped team/settings state |

---

## Development Scope

NBA Playoff Companion AI is part of a seven-application analytics suite developed by a single developer.

The project combines live sports data ingestion, software engineering, product design, persistence systems, authentication, cloud deployment, and cross-application workflows into a unified platform — one of several sibling apps (Command Center, Baseball, Music, Investment, AMI, FutureLens) sharing suite infrastructure.

---

## For Employers & Reviewers

This project demonstrates product engineering for live sports data and fan-first UX:

| Skill area | Evidence in NBA |
|------------|----------------|
| **Live data engineering** | CDN scoreboard first, graceful API fallback, honest live-state banners |
| **Product development** | Playoff-native navigation, elimination/offseason modes, fast-load shell |
| **Analytics architecture** | Series modeling, lineup intelligence, player trend tracking |
| **Persistence design** | Deferred workspace sync, disk + cloud restore, activity events |
| **Systems design** | Suite auth, resume launch, workspace-scoped state paths |
| **Cross-application integration** | Command Center deep links, suite activity feed |

Inspect `tests/test_workspace_account_ownership.py` and `nba_persistent_state.py` without running the full UI.

---

## Why This Project Is Different

Most NBA apps try to cover the whole league at once — box scores, standings, and stat tables with no playoff narrative.

NBA Playoff Companion AI was designed as a **single-team playoff command center** — one favorite franchise, one narrative thread, one dashboard that changes meaningfully when your team is live, advancing, or eliminated.

The same platform architecture supports bracket context, live game center, matchup intelligence, player tracking, franchise history, and offseason continuity through a shared persistence, routing, and fan-experience layer.

| Typical NBA app | This platform |
|-----------------|---------------|
| League-wide stats hub | Single-team playoff command center |
| Slow first paint | Fast-load shell with deferred heavy restore |
| Silent API failures | Honest banners + safe mode |
| Surface-level depth charts | Curated playoff rotations when API data is stale |
| Single-purpose pages | Integrated home, live, bracket, matchup, tracker, and legacy flow |
| Generic sidebar | Suite auth, workspace badge, Command Center link |
| Isolated local state | Account-owned workspace isolation + Supabase sync |

NBA Playoff Companion AI is a **fan-first playoff product**, not another league-wide stats site.

---

## Key Features

| Page / Area | Highlights |
|-------------|------------|
| **Home Dashboard** | Bracket context, matchup story, playoff command center |
| **Live Game Center** | CDN scoreboard, box scores, live banners |
| **Playoff Bracket** | Series records, round labels, elimination state |
| **Matchup Intelligence** | Lineup comparison, curated playoff rotations |
| **Player Playoff Tracker** | Per-series player performance |
| **Legacy Tracker** | Career/playoff legacy narratives |
| **Team History & Leaders** | Franchise depth, previous rounds |
| **Offseason outlooks** | Post-elimination continuity |
| **Account & Workspace** | Real Accounts auth, owned workspace, foreign URL rejection |

---

## Analytics & AI Methods

| Method | Use |
|--------|-----|
| CDN scoreboard ingestion | Live game state with fallback |
| Playoff series modeling | Round labels, elimination detection |
| Lineup intelligence | Curated rotations vs API depth charts |
| Player trend tracking | Playoff performance narratives |
| Activity events | Suite activity feed for Command Center |
| AMI integration (planned) | Structured insight handoff — not yet validated in NBA milestone |

---

## Technical Architecture

```
streamlit_app.py           # Main shell, routing, fast-load path
nba_persistent_state.py    # prepare_nba_workspace, disk + cloud sync
nba_startup.py             # Fast-load defaults, deferred restore
suite_workspace.py         # bootstrap_suite_workspace, scoped paths
suite_workspace_registry.py # Account-owned workspace registry
suite_auth.py              # Real Accounts + ownership enforcement
suite_user_persistence.py  # sync_workspace_protocol
docs/                      # Product source of truth (vision, pages)
```

**Persistence paths**

| Layer | Path / key |
|-------|------------|
| Active workspace (account) | `data/workspaces/_active/{owner_user_id}.json` |
| Ownership registry | `data/workspaces/_ownership_registry.json` |
| App state | `data/workspaces/{workspace_id}/nba_user_state.json` |
| Cloud | Supabase scoped via `nba__{workspace}` |

**Startup order (workspace isolation v2)**

1. `bootstrap_suite_workspace(st)` — auth restore → ownership clamp
2. `apply_suite_auth_gate(st)`
3. `apply_suite_resume_launch(st, "nba")`
4. Deferred `prepare_nba_workspace(st)` after fast-load shell

---

## Screenshots

| # | Page | Filename (placeholder) | What to show |
|---|------|------------------------|--------------|
| 1 | Home Dashboard | `screenshots/01-home-dashboard.png` | Bracket + matchup story |
| 2 | Live Game Center | `screenshots/02-live-game-center.png` | Scoreboard + box score |
| 3 | Playoff Bracket | `screenshots/03-playoff-bracket.png` | Series state + round labels |
| 4 | Matchup Intelligence | `screenshots/04-matchup-intelligence.png` | Lineup comparison |
| 5 | Legacy Tracker | `screenshots/05-legacy-tracker.png` | Player legacy panel |

---

## Portfolio Value

NBA Playoff Companion AI shows that you can:

- Ingest **live sports data** with CDN-first scoreboard logic, graceful fallback, and honest failure banners
- Design **fan-first playoff UX** — fast first paint, elimination/offseason modes, and emotional continuity after a team is out
- Model **playoff context** — series records, round labels, lineup intelligence, and player trend narratives
- Implement **deferred persistence** so heavy workspace restore does not block the first screen
- Build **multiplayer-ready state** — account-owned workspaces, disk + cloud sync, and foreign URL rejection
- Integrate **suite-wide workflows** — auth, resume launch, activity events, and Command Center handoffs across a large Streamlit app
- Translate product requirements into **test-driven engineering** (`test_workspace_account_ownership.py`, `test_nba_workspace.py`)

A hiring manager can grasp scope and sophistication in **2–3 minutes** from this README plus the live demo.

---

## Local Setup

### Requirements

- **Python 3.11+**
- `pip install -r requirements.txt`

### Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Enable **Dev Lab** via `DEV_MODE = True` at top of `streamlit_app.py` or the sidebar developer toggle.

### Optional environment variables

| Variable | Purpose |
|----------|---------|
| `SUITE_SUPABASE_URL` | Cloud persistence |
| `SUITE_SUPABASE_ANON_KEY` | Supabase client |
| `SUITE_AUTH_ENABLED` | Real Account sign-in |

### Streamlit Cloud

- **Branch:** `dev`
- **Main file:** `streamlit_app.py`

---

## Roadmap

**Near term**
- [ ] Manual Daniel/Ariel workspace validation (team, tracker, settings isolation)
- [ ] NBA AMI insight panel (separate milestone — not part of workspace isolation)
- [ ] Command Center activity leak cleanup for NBA snapshots

**Medium term**
- [ ] Mobile-optimized Live Game Center layout
- [ ] Richer offseason outlook templates
- [ ] CI matrix with workspace ownership tests on every PR

See [`docs/DEVELOPMENT_PRIORITIES.md`](docs/DEVELOPMENT_PRIORITIES.md) for active work.

---

## Testing

```bash
python -m pytest tests/test_workspace_account_ownership.py tests/test_nba_workspace.py -q
```

Workspace isolation acceptance: selected team, playoff state, tracker, and settings scoped per workspace; foreign `?suite_workspace=` URLs rejected at startup.

---

## Author

Daniel Cohen
