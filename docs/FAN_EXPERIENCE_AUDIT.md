# Fan experience audit — product quality pass

**Last updated:** 2026-06-05 · **Build:** `quality-pass-2026-06-05` · **Branch:** `dev`

Product-quality pass across all fan-facing pages: consistency, trust labels, clutter reduction, mobile stacking, and normal-mode performance (no new pages or Live GC expansion).

---

## Priority 1 — Consistency

| Element | Standard |
|---------|----------|
| Max width | `.fan-product-shell`, `.pp-wrap`, `.cmd-shell`, `.ml-shell` → 1280px centered |
| Cards | `.fan-card-unified` radius/shadow; page-specific grids inherit team CSS vars |
| Headers | `render_fan_page_hero` + `render_fan_section` (icon, caption, tone) |
| Spacing | Trust strip → 14px bottom margin; section open/close wrappers |
| Fonts | Global fan CSS; team accent via `inject_team_brand_css` |
| Icons | Section headers use emoji icons consistently (🏀 broadcast, 📋 boards, etc.) |

**Pages wrapped in product shell:** Home, Player Tracker, Legacy, Matchup Lineups, Team History.

---

## Priority 2 — Trust & accuracy badges

Every major page shows `render_page_trust_strip(page_key)` immediately after the hero (or recap banner for offseason).

| Badge kind | Meaning | Example use |
|------------|---------|-------------|
| **Official** | Bracket engine, NBA API logs, CDN scoreboard | Home scores, Legacy logs, Live GC |
| **Curated board** | App-maintained playoff universe | Lineups rotation, franchise chase |
| **Fan model** | Sliders, legacy score, offseason analysis | Legacy Tracker, eliminated Home |
| **Projected** | Pace / milestone math | Player Tracker pass date, History countdown |
| **Estimate** | Season averages, scouting synthesis | Lineups expanders, Matchup Intel |

Live Game Center keeps the existing metric strip (`_render_live_gc_trust_strip`) for status/score/clock/source — plus the page-level badge row for “CDN / stats scoreboard”.

**Preserved factual anchors:** `FINALS_GAME1_CANONICAL_SCORE` (Knicks 105, Spurs 95), Harrison Barnes PF, no Jeremy Sochan in rotation.

---

## Priority 3 — Fan testing (30-second test)

| Page | Elevated | Trimmed |
|------|----------|---------|
| Home | Fan energy grid, series board, Go live | Duplicate score disclaimers → trust strip |
| Live GC | Score first, depth on demand | No architecture expansion |
| Bracket | Visual bracket + ribbon | Long API caption → one line |
| Lineups | PG–C cards on first paint | Bench/tactical in expander; duplicate source captions |
| Player Tracker | Chase board + journey | “Estimates labeled” pills → trust strip |
| Legacy | Meters, GOAT ladder, swings | Footer fan-model caption → trust strip |
| Team History | Mount Rushmore, countdown, movement | hist-note block + third metric column |
| Previous Rounds | Series history cards | — |
| Offseason (Home) | Card modules | Trust strip on front-office read |

---

## Priority 4 — Mobile (≤768px)

CSS additions in `GLOBAL_APP_CSS`:

- Energy grid, chase grids, legacy grids, lineups grids → single column
- Trust strip stacks vertically; notes full width
- History `.hist-grid`, compare, milestone grids → 1fr
- Player stat grid → 3 columns (readable pills)
- Matchup ribbon stacks

**Spot-check:** Home, Player Tracker, Legacy, Matchup Lineups on narrow viewport.

---

## Priority 5 — Performance

No new deferrals this pass; builds on prior expander work:

- Plotly / YoY / bench-tactical behind expanders
- Home quick view: hero + energy board first paint
- Bracket / Previous Rounds: validation ultra snapshots unchanged
- Build id: `quality-pass-2026-06-05` (sidebar footer)

Run: `python scripts/audit_page_performance.py` with QA or ultra-fast sidebar toggles.

---

## Verification checklist

1. Each page shows trust badges after hero.
2. Knicks Finals Game 1 still reads **105–95**.
3. Spurs lineups show **Harrison Barnes** at PF; no **Jeremy Sochan**.
4. `python -m py_compile streamlit_app.py`
5. `python scripts/audit_lineups.py`
6. `python scripts/audit_factual_accuracy.py`
7. Mobile: cards stack without horizontal scroll on Home / Tracker / Legacy / Lineups.

---

## Files touched

- `streamlit_app.py` — CSS, trust helpers, page wiring, clutter trim
- `docs/FAN_EXPERIENCE_AUDIT.md` (this file)
- `docs/PAGES.md`, `docs/PERFORMANCE_AUDIT.md`, `cursor-prompts/nba_app_tasks.md`
