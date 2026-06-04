# Pages & UX — fan-facing surfaces

**Last updated:** 2026-06-03

Sidebar routes are defined in `PAGES` inside `streamlit_app.py`. **Dev Lab** is optional (`DEV_MODE` or sidebar toggle).

---

## Home Dashboard

**Route:** `Home Dashboard` · **Renderer:** `render_playoff_command_center`

**Purpose:** Playoff command center for the selected favorite team—tonight's feel, series context, and optional live refresh.

**UX goals:**
- Hero + fan identity (stakes, tagline).
- Playoff matchup ribbon (round, opponent, series record).
- Current game watch card with jump to Live Game Center.
- **Quick view** default; **Go live** pulls injury/star/legacy bundles (8s timeout guard).
- **Eliminated teams:** offseason outlook sections at top; live toggle disabled.

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

**Purpose:** Position-by-position starters and bench for favorite team vs current opponent.

**UX goals:**
- Curated playoff rotation overrides outdated API players.
- Resolution source caption (curated / playoff minutes / profile).

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
- Player picker, season selector, chart overlays.
- Tie-in to playoff game logs cache.

---

## Legacy Tracker

**Route:** `Legacy Tracker` · **Renderer:** `render_legacy_tracker_page`

**Purpose:** Career playoff legacy chase—rankings, milestones, "what if" framing for active stars.

**See:** [LEGACY_TRACKER.md](./LEGACY_TRACKER.md)

---

## Team History & Leaders

**Route:** `Team History Leaders` · **Renderer:** `render_team_history_leaders_page`

**Purpose:** Franchise playoff legends board + current-player chase vs history.

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

**Purpose:** Structured post-elimination analysis—priorities, cap/roster, players out, direction label.

---

## Dev Lab

**Route:** `Dev Lab` (conditional) · **Renderer:** `render_dev_lab_page`

**Purpose:** Developer workspace—isolated from fan UX. Diagnostics, cache probes, sandbox, **product docs** from `docs/`.

**Visibility:** `DEV_MODE = True` or sidebar "Enable Dev Lab (developer)".
