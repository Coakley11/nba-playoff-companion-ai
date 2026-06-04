# Playoff engine — source of truth

**Last updated:** 2026-06-04  
**Code entry:** `get_playoff_state_cached` · `get_merged_playoff_state` · `_playoff_status_from_state` · `get_team_playoff_status`

> If this doc and code disagree, reconcile in the **same change**. See [WORKFLOW.md](./WORKFLOW.md).

---

## Purpose

Single **playoff bracket state** (`stt`) powers: bracket UI, per-team status, round/opponent labels, Home ribbon, Live GC context, and elimination/offseason mode.

**Seed data:** `TEAM_PROFILES` (2026 playoff universe).  
**Runtime merge:** NBA completed games + optional demo fallback + static series templates.

---

## Bracket generation (authoritative)

### Pipeline

```
get_playoff_state_cached(use_demo_backup, api_refresh)
  → build_first_round_series_cached
  → build_second_round_series_cached   # winners advance from first
  → build_conference_finals_series_cached
  → build_nba_finals_series_cached
  → assemble stt { first, second, cf, finals, east_*, west_*, team_status, ... }
```

### Series object shape

Each series includes at minimum: `a`, `b`, `conf`, `round`, `a_wins`, `b_wins`, `winner`, `games[]`, `source`.

### Game ingestion

- `fetch_completed_games_recent(api_refresh)` pulls playoff completed games.  
- Wins counted per game: team reaching **4 wins** in a series confirms `winner`.  
- `_series_has_confirmed_winner`: **`a_wins >= 4` or `b_wins >= 4`** (best-of-7).  
- Demo fallback: `DEMO_FIRST_ROUND_SERIES` and templates when API empty and `use_demo_backup=True`.

### Round builders

| Round | Builder | Advancement input |
|-------|---------|-------------------|
| First Round | `build_first_round_series_cached` | Static pairings + API/demo games |
| Second Round | `build_second_round_series_cached` | First-round **winners** per `SECOND_ROUND_SERIES_TEMPLATE` |
| Conference Finals | `build_conference_finals_series_cached` | Second-round winners per conference |
| NBA Finals | `build_nba_finals_series_cached` | East CF winner vs West CF winner |

**Shell series:** When API games not yet available, templates provide `a`/`b` with 0–0 until games populate.

### Cache & refresh

| Constant | Value | Meaning |
|----------|-------|---------|
| `PLAYOFF_STATE_CACHE_TTL_SEC` | 90 | `@st.cache_data` TTL for state builders |
| `PLAYOFF_BRACKET_REFRESH_MS` | 60000 | Sidebar autorefresh on bracket pages |
| Sidebar `api_refresh` | toggle | Passes `api_refresh` into fetch |
| Sidebar `use_demo_backup` | toggle | Merges demo scores when API empty |

---

## Advancement rules (authoritative)

1. **Series win:** First side to **4** game wins (`a_wins` or `b_wins`).  
2. **Winner field:** Set on series when confirmed; drives next-round shell pairing.  
3. **Next round context:** `_next_round_context_from_state` — if team won last series and next opponent known → `advanced` or `awaiting opponent`.  
4. **Display matchup:** `get_display_matchup` — single fan-facing object (round, opponent, series record, badge).  
5. **Effective profile:** `get_effective_team_profile` overlays bracket on `TEAM_PROFILES` for round/opponent/status.

**Status values:** `active`, `eliminated`, `advanced`, `awaiting opponent` (see elimination).

---

## Elimination rules (authoritative)

A team is **`eliminated`** when:

1. `_playoff_status_from_state` finds a series in `team_series` where `_team_lost_confirmed_series(team, series)` is true — opponent reached 4 wins.  
2. Deepest lost series sets elimination round and `elimination_reason` (e.g. "Lost Conference Finals to … 2-4").  
3. `get_display_matchup` → `eliminated: true`, badge **"OUT · offseason outlook"**.  
4. `get_effective_team_profile` → `status: "Eliminated"`, `current_opponent: None`.

**Home check:** `_is_home_eliminated(team)` uses `get_team_playoff_status` or fallback `_dynamic_playoff_eliminated`.

**UI consequences (must not regress):**

- Home: offseason sections via `render_offseason_future_outlook_sections`; **Go live** disabled.  
- Sidebar label: `(offseason outlook)`.  
- Live GC still available for watching league games; copy differs from chase mode.

---

## Offseason logic (authoritative)

| Layer | Behavior |
|-------|----------|
| **Detection** | `status == "eliminated"` from engine OR static profile `Eliminated` |
| **Outlook copy** | `get_offseason_outlook(team)` → `OFFSEASON_OUTLOOK_BY_TEAM` or `_generic_offseason_outlook` |
| **Home render** | `render_offseason_future_outlook_sections` — priorities, roster, players out, direction label |
| **Not a separate route** | Offseason is a **mode** on Home Dashboard, not `PAGES` entry |

Eliminated teams **remain** in `TEAM_PROFILES` for history, legacy, and bracket display as eliminated.

---

## Team status map

`stt["team_status"]` = `{ team_name: _playoff_status_from_state(team, stt) }` built in `get_playoff_state_cached`.

Consumers **must** prefer `get_team_playoff_status(team, stt)` over raw `TEAM_PROFILES` fields for round/opponent/elimination.

---

## Requirements (do not regress)

1. Bracket never blank when `use_demo_backup` enabled and API empty.  
2. Series scores match counted completed games.  
3. Eliminated teams never get active-series "Go live" as primary Home CTA.  
4. `scripts/qa_bracket_logic.py` passes after engine edits.  
5. Headless `get_playoff_state_snapshot()` stays stable for tests.

---

## UI consumers

- Playoff Bracket — `render_bracket`  
- Home — `render_playoff_command_center`, `_is_home_eliminated`  
- Live GC — `_live_gc_profile_context`, matchup ribbon  
- Dev Lab — Playoff state / Bracket tabs  

---

## Planned changes

- [ ] CI gate: `qa_bracket_logic.py` on every `dev` push.  
- [ ] Season-agnostic round labels config (reduce 2026 hard-coding).  
- [ ] Document play-in / tie-breaker if scope expands (currently best-of-7 only).
