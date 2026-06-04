# Phase: Stability, correctness & polish

**Last updated:** 2026-06-05 · **Status:** ACTIVE

**Goal:** Move from feature-rich → **stable, polished, trustworthy**. No major new systems until this phase completes.

**Validation tracker:** [VALIDATION_STATUS.md](./VALIDATION_STATUS.md) (manual P1/P2 pass/fail + Home perf timings).

---

## Priority order (do not reorder without doc update)

### 1. Live Game Center reliability — HIGHEST

**Doc:** [LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md)

| Task | Done when |
|------|-----------|
| Trust strip always shows status, score, clock, source, last updated | ✓ `_render_live_gc_trust_strip` on full + safe paths |
| No fake 0–0 over live feed (Q1+ guard + last-known fallback) | ✓ `_live_gc_suspicious_zero_zero_live` in resolver + trust strip |
| Safe mode verified during real games | Dev Lab game-night checklist + manual browser test |
| Layer 1 proven stable on Cloud | No timeout; refresh ≤60s; no fake 0–0 over live feed |
| No new L2/L3 features | Until Layer 1 sign-off |

**Freeze:** No new Live GC tabs, charts, or analysis widgets. Validation-only fixes allowed until game-night sign-off.

**Parallel track (allowed):** Matchup Lineups, Player Playoff Tracker, eliminated-team offseason, Team History, and Legacy Tracker polish — no Live GC feature expansion.

---

### 2. Home Dashboard speed

**Doc:** [PAGES.md](./PAGES.md) (Home Dashboard)

| Task | Done when |
|------|-----------|
| Section-level render timing visible (debug) | Slowest sections identified |
| Quick view first paint &lt; 3s on Cloud | Measured with SHOW_PERF_DEBUG |
| Live bundle stays within 8s timeout | Or graceful fallback without hang |
| Aggressive cache on playoff state + home context | No redundant API on quick view |

**Freeze:** No new Home sections or widgets.

---

### 3. Matchup Lineups accuracy

**Doc:** [PAGES.md](./PAGES.md) (Matchup Lineups)

| Task | Done when |
|------|-----------|
| Curated rotations match expected playoff boards | Spot-check Finals teams |
| Positions correct | LINEUP_SLOTS alignment |
| Stale players filtered | `OUTDATED_PLAYOFF_PLAYERS` + minutes fallback audited |

---

### 4. NBA Finals state correctness

**Doc:** [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md)

| Task | Done when |
|------|-----------|
| Active teams agree: bracket, engine, Home ribbon, Live GC context | `qa_bracket_logic.py` + manual Knicks/Spurs check |
| Eliminated teams always offseason on Home | `_is_home_eliminated` + engine status agree |
| Effective profile matches display matchup | Dev Lab team status table clean |
| Factual accuracy pass (scores, standouts, rosters) | `python scripts/audit_factual_accuracy.py` exits 0 |

**Checklist:** East CF Knicks 4-0 Cavaliers; Finals Knicks vs Spurs; game standouts only from active series rosters (`OUTDATED_PLAYOFF_PLAYERS` respected).

---

### 5. UI/UX polish

| Task | Done when |
|------|-----------|
| Headers consistent (`render_fan_page_hero`) | All main pages |
| Color / hierarchy pass | Broadcast feel, less scroll |
| No regression in docs-first workflow | [WORKFLOW.md](./WORKFLOW.md) |

**Defer:** Large visual redesigns until P1–P4 pass.

---

### 6. Documentation discipline

| Task | Done when |
|------|-----------|
| Every stability fix updates feature doc + KNOWN_ISSUES | Same commit |
| [SYSTEMS_STATUS.md](./SYSTEMS_STATUS.md) % updated realistically | After each system milestone |

---

## Current milestone

**Live Game Center works reliably during an actual game** + **Cloud smoke pass** on `dev`.

Success criteria:

1. During a live NBA game, fan sees real score, clock, status, source, last updated within 60s refresh.
2. Safe mode (`LIVE_GC_SAFE_MODE = True`) still shows trust strip and scoreboard essentials.
3. Cloud: Home + Live GC + Bracket render for active + eliminated team without error.

---

## What we are NOT doing this phase

- New pages or major features (see [ROADMAP.md](./ROADMAP.md) backlog — frozen).
- Command Center or suite-wide expansions (sibling repos).
- Module split of `streamlit_app.py` (deferred to offseason unless required for P1).
