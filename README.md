# Daniel Cohen — NBA Playoff Companion AI

**A fan-first playoff command center** built with Python and Streamlit for the 2026 NBA playoffs: live games, bracket context, matchup intelligence, player stories, franchise history, and offseason outlooks — with account-owned workspace isolation in the Daniel Cohen AI Suite.

**Live demo:** [nba-playoff-companion-ai.streamlit.app](https://nba-playoff-companion-ai-gd4sx677quejdfkvappv6o.streamlit.app)  
**Deploy branch:** `dev` · **Entry point:** `streamlit_app.py`

Built as part of the **Daniel Cohen AI Suite** (shared workspace auth, cloud persistence, and Command Center handoffs).

**Product docs:** [`docs/`](docs/) — vision, pages, and development priorities.

---

## At a Glance

| | |
|---|---|
| **Role** | Full-stack Python sports app — live data ingestion, playoff-native UX, and test-driven persistence |
| **Stack** | Python 3.11+ · Streamlit · pandas · NBA CDN/API feeds · optional Supabase · suite deep links |
| **Scale** | 10+ fan-facing pages · fast-load shell · deferred workspace sync · playoff tracker + legacy |
| **Differentiators** | One favorite team at a time · honest live-state banners · curated playoff rotations · workspace-scoped team/settings state |

---

## For Employers & Reviewers

This project demonstrates product engineering for live sports data: CDN-first scoreboard with graceful fallback, playoff-native navigation for elimination/offseason modes, and **per-account workspace isolation** so Daniel and Ariel (or `coakley11`) never share team selection, tracker state, or settings. Inspect `tests/test_workspace_account_ownership.py` and `nba_persistent_state.py` without running the full UI.

---

## 1. Executive Summary

Most NBA apps are generic stat sites. This app is a **playoff command center for one favorite team**.

NBA Playoff Companion AI answers:

- Where is my team in the bracket?
- What's live right now — and is the data trustworthy?
- How do lineups match up tonight?
- Which players are defining the series?
- What did we accomplish — and what's next if we're out?

The app is designed as a portfolio piece demonstrating **live API integration, fan UX, multiplayer-ready persistence patterns, and suite workspace architecture** — not a box-score dump.

---

## 2. Why This Project Is Different

| Typical NBA app | This platform |
|-----------------|---------------|
| League-wide stats hub | Single-team playoff command center |
| Slow first paint | Fast-load shell with deferred heavy restore |
| Silent API failures | Honest banners + safe mode |
| Shared local state | Account-owned workspace isolation |
| Generic sidebar | Suite auth, workspace badge, Command Center link |

---

## 3. Key Features

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

## 4. Analytics & AI Methods

| Method | Use |
|--------|-----|
| CDN scoreboard ingestion | Live game state with fallback |
| Playoff series modeling | Round labels, elimination detection |
| Lineup intelligence | Curated rotations vs API depth charts |
| Player trend tracking | Playoff performance narratives |
| Activity events | Suite activity feed for Command Center |
| AMI integration (planned) | Structured insight handoff — not yet validated in NBA milestone |

---

## 5. Technical Architecture

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

## 6. Screenshots

| # | Page | Filename (placeholder) | What to show |
|---|------|------------------------|--------------|
| 1 | Home Dashboard | `screenshots/01-home-dashboard.png` | Bracket + matchup story |
| 2 | Live Game Center | `screenshots/02-live-game-center.png` | Scoreboard + box score |
| 3 | Playoff Bracket | `screenshots/03-playoff-bracket.png` | Series state + round labels |
| 4 | Matchup Intelligence | `screenshots/04-matchup-intelligence.png` | Lineup comparison |
| 5 | Legacy Tracker | `screenshots/05-legacy-tracker.png` | Player legacy panel |

---

## 7. Local Setup

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

## 8. Roadmap

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

## 9. Testing

```bash
python -m pytest tests/test_workspace_account_ownership.py tests/test_nba_workspace.py -q
```

Workspace isolation acceptance: selected team, playoff state, tracker, and settings scoped per workspace; foreign `?suite_workspace=` URLs rejected at startup.

---

## Author

Daniel Cohen
