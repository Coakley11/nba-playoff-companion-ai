# NBA Playoff Companion AI

Daniel Cohen **NBA Playoff Companion AI** — a fan-first Streamlit app for the 2026 NBA playoffs: bracket, live games, matchups, player stories, franchise history, and offseason outlooks.

## Product documentation (source of truth)

Planning and architecture live in **[`docs/`](docs/)** — read before major feature work:

- [docs/README.md](docs/README.md) — index
- [docs/APP_VISION.md](docs/APP_VISION.md) — vision & UX goals
- [docs/PAGES.md](docs/PAGES.md) — every fan-facing page
- [docs/DEVELOPMENT_PRIORITIES.md](docs/DEVELOPMENT_PRIORITIES.md) — active work

**Dev Lab → Product docs** tab displays priorities, roadmap, and known issues from these files.

Cursor agents: see [cursor-prompts/](cursor-prompts/) and `.cursor/rules/nba-app-roadmap-docs.mdc`.

## Features

- Home Dashboard (playoff command center)
- Live Game Center
- Playoff Bracket
- Matchup Lineups & Matchup Intelligence
- Player Playoff Tracker & Legacy Tracker
- Team History & Leaders & Previous Rounds
- Offseason outlooks for eliminated teams

## Tech

- Python, Streamlit, pandas
- NBA API / CDN scoreboard feeds (with demo fallback)
- Optional suite persistence (Supabase) via shared modules

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Enable **Dev Lab** via `DEV_MODE = True` at top of `streamlit_app.py` or the sidebar developer toggle.

## Deployment

Streamlit Cloud: branch **`dev`**, main file **`streamlit_app.py`**.

## Author

Daniel Cohen
