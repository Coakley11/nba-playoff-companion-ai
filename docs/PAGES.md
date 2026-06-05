# Pages & UX — fan-facing surfaces

**Last updated:** 2026-06-05 · **Build:** `premium-fan-2026-06-05`

Sidebar routes are defined in `PAGES` inside `streamlit_app.py`. **Dev Lab** is optional (`DEV_MODE` or sidebar toggle).

---

## Home Dashboard

**Route:** `Home Dashboard` · **Renderer:** `render_playoff_command_center`

**Purpose:** Playoff command center for the selected favorite team—tonight's feel, series context, and optional live refresh.

**UX goals:**
- **Finals broadcast hero** — dual Knicks/Spurs team colors, series score once, last game box score (canonical `FINALS_GAME1_CANONICAL_SCORE`).
- **Fan energy board** — nine distinct briefing tiles (tactical why, Game 1→2 shift, matchup, pressure, coaching, watch, rising, history, watch-next) — no scoreboard repeat.
- Series log + storyline bar in one section; keys for next tip in a follow-on section.
- Current game watch card with jump to Live Game Center.
- **Quick view** default; **Go live** pulls injury/star/legacy bundles (8s timeout guard).
- **Eliminated teams:** playoff recap banner + card-based offseason modules (priorities, assets, turnover, archetypes); live toggle disabled.

**Data:** Merged playoff state, `resolve_home_matchup_context_fast`, optional live bundle APIs.

---

## Live Game Center

**Route:** `Live Game Center` · **Renderer:** `render_live_game_center` / `render_live_game_center_safe`

**Purpose:** Live (or scheduled/final) game board for the favorite team—scores, period, win probability, depth when enabled.

**UX goals:**
- CDN-first Layer 1 (fast scoreboard).
- Layer 2 analysis and Layer 3 heavy tabs on demand.
- Safe mode banner when `LIVE_GC_SAFE_MODE` is True.
- Auto-refresh ~60s on page open.
- Manual game entry fallback when no feed row.

**See:** [LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md)

---

## Playoff Bracket

**Route:** `Playoff Bracket` · **Renderer:** `render_bracket`

**Purpose:** Full postseason bracket—first round through Finals—with series scores and advancement.

**UX goals:**
- Conference columns, clear winner advancement.
- Demo fallback when API returns empty (sidebar toggle).
- API auto-sync toggle (~60s refresh).

**See:** [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md)

---

## Matchup Lineups

**Route:** `Matchup Lineups` · **Renderer:** `render_matchup_lineups_page`

**Purpose:** TV-style playoff matchup board — PG vs PG through C vs C with headshots, team colors, and bench/X-factor cards.

**UX goals:**
- Broadcast matchup strip + dual-team color hero (logos, headshots).
- Curated playoff rotation overrides outdated API players (e.g. Harrison Barnes PF, no Jeremy Sochan).
- PG–C cards with team/opp edge highlighting, advantage badges, edge summary on first paint.
- **Bench battle, tactical edges, X-factor** collapsed under one expander (defers `season_averages` API calls).
- Section headers match TV broadcast blocks; raw rotation in expander only.

---

## Matchup Intelligence

**Route:** `Matchup Intelligence` · **Renderer:** `render_matchup_intelligence`

**Purpose:** Narrative matchup hub—injuries, keys, fan framing for the series.

**UX goals:**
- Intelligence hero, injury report integration.
- First-round vs later-round header variants.

---

## Player Playoff Tracker

**Route:** `Player Playoff Tracker` · **Renderer:** `render_player_playoff_story_hub`

**Purpose:** Per-player playoff story—logs, trends, milestones for selected player.

**UX goals:**
- Premium player card hero (large headshot, inline PPG/GP/record tiles, playoff badges).
- **Franchise chase hero** — visual **record race lane** (current vs target headshots), next record / next 3 / easiest / hardest / series-within-reach ladder, plus `#rank` banner and progress bars.
- **Standout award strip** — 30/40-pt nights, engine scorer, two-way pressure callouts.
- Playoff average stat pills; **series journey strip** + **round tabs** with per-series game log cards.
- Franchise comparison cards (named Ewing/Frazier/Duncan/Parker-style copy).
- Game log cards first; **Plotly progression charts** in collapsed expander (QA/Ultra still skip charts).

---

## Legacy Tracker

**Route:** `Legacy Tracker` · **Renderer:** `render_legacy_tracker_page`

**Purpose:** Career playoff legacy chase with **specific franchise names** (Ewing, Frazier, Duncan, Parker, etc.) — not generic greatness copy.

**UX goals (2026-06-05 premium pass):**
- Legacy score / ceiling / bracket-climb **meters** + **earned badge chips** (Franchise Legend, Championship Hero, Finals MVP track, etc.).
- **Title probability impact** + **Finals MVP impact** + franchise rank panel (updates with sliders).
- **Franchise GOAT ladder** (top six curated legends; current player highlighted).
- **Playoff run ranking** copy tied to franchise great runs.
- Named franchise **comparison face cards** (headshots where network allows).
- **What-if scenario cards** — next round, Conference Finals, title — with legacy score + named read.
- Simulator sliders remain; Plotly path chart in collapsed expander only.

**See:** [LEGACY_TRACKER.md](./LEGACY_TRACKER.md)

---

## Team History & Leaders

**Route:** `Team History Leaders` · **Renderer:** `render_team_history_leaders_page`

**UX goals (2026-06-05 premium pass):** Mount Rushmore (top four faces), milestone **countdown cards**, current-player **movement tracker**, greatest playoff runs/games, legend cards with headshots/logos, sortable leaderboard, named comparison cards.

**Purpose:** Franchise playoff legends board + sortable leaderboards (30/40-pt games, scoring, rebounds, assists) + current-player chase cards with progress bars.

**See:** [TEAM_HISTORY.md](./TEAM_HISTORY.md)

---

## Previous Rounds

**Route:** `Previous Rounds` · **Renderer:** `render_previous_rounds_history`

**Purpose:** Playoff path so far—each round's results, MVPs, series cards for the favorite team.

**UX goals:**
- Series history cards with scores and round labels.
- Hero: "Playoff path so far".

---

## Offseason outlooks (Home, not separate page)

**Trigger:** `_is_home_eliminated(team)` on Home Dashboard.

**Renderer:** `render_offseason_future_outlook_sections`, `get_offseason_outlook`

**Purpose:** Playoff recap banner plus card-grid offseason modules—season reflection, priorities, future direction, draft/assets, roster turnover, ideal additions (fan-section headers, less wall-of-text).

---

## Dev Lab

**Route:** `Dev Lab` (conditional) · **Renderer:** `render_dev_lab_page`

**Purpose:** Developer workspace—isolated from fan UX. Diagnostics, cache probes, sandbox, **product docs** from `docs/`.

**Visibility:** `DEV_MODE = True` or sidebar "Enable Dev Lab (developer)".
