# App vision — NBA Playoff Companion AI

**Last updated:** 2026-06-03

## Product vision

**Daniel Cohen NBA Playoff Companion AI** is a fan-first Streamlit app for the 2026 NBA playoffs. It answers: *Where is my team in the bracket? Who are we playing? What's live right now? How do lineups match up? What did we accomplish—and what's next if we're out?*

The app is **not** a generic stats site. It is a **playoff command center** for one favorite team at a time, with optional deep dives (bracket, live center, legacy, history).

## Fan experience goals

- **Fast first paint** on Home Dashboard — bracket context and matchup story without waiting on every API.
- **Honest live state** — CDN scoreboard first; clear banners when APIs fail or safe mode is on.
- **Playoff-native language** — series records, round labels, elimination / offseason modes surfaced in copy and navigation.
- **Trustworthy lineups** — curated playoff rotations override stale API depth charts when needed.
- **Emotional continuity** — eliminated teams get postmortem + offseason outlook, not a dead dashboard.

## Suite context

- Part of the **Daniel AI Suite** (Command Center hub).
- Optional **suite persistence**: local disk + Supabase `full_session`, activity events, resume deep links.
- Deploy target: Streamlit Cloud, branch **`dev`**, main file **`streamlit_app.py`**.

## Core product areas

| Area | Primary pages |
|------|----------------|
| Command center | Home Dashboard |
| Live playoffs | Live Game Center, Playoff Bracket |
| Matchup prep | Matchup Lineups, Matchup Intelligence |
| Player stories | Player Playoff Tracker, Legacy Tracker |
| Franchise depth | Team History & Leaders, Previous Rounds |
| Eliminated / future | Home offseason sections, outlook copy |
| Engineering | Dev Lab (diagnostics + product docs) |
