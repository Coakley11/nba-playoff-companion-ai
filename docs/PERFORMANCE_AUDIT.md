# Performance audit

**Last updated:** 2026-06-05 · **Branch:** `dev`

Speed is part of stability: factual QA (P5) is impractical when every page takes 10–30+ seconds on Cloud.

---

## Quick start (testing)

1. Open the app on Streamlit Cloud (`dev`).
2. Sidebar → turn on **Ultra-fast validation (no network)** for P5 browser spot-checks (fastest).
3. Or **QA mode (fast testing)** for fuller UI with heavy sections behind **Load full page** buttons.
4. Optional: **Show performance debug** for cache tables.
5. Each page shows a **QA / Ultra-fast performance** expander with:
   - **First paint** (hero + matchup ribbon)
   - **Total render**
   - **Top 5 slowest sections** (ms)

### QA mode skips

| Area | Behavior |
|------|----------|
| Bracket API sync | Forced off (sidebar toggles hidden) |
| 60s autorefresh | Off |
| Playoff engine | One **session snapshot** per run (`_validation_playoff_stt`) |
| Sidebar team labels | Use cached snapshot (no N× rebuild) |
| Live Game Center | Safe path; ultra skips CDN entirely |
| Matchup Intelligence | Fast ribbon only — no full scouting board |
| Legacy Tracker | No Plotly path chart; game log in expander; meters + scenario cards visible |
| Player Playoff Tracker | No Plotly; YoY only via checkbox; pressure/narrative in expanders |
| Matchup Lineups | Curated board when available; full broadcast UI |
| Home Dashboard | Full fan briefing UI (no deferred body) |

### Ultra-fast mode (additional)

| Area | Behavior |
|------|----------|
| Network | Blocked — no CDN, stats API, ESPN, player-id/headshots |
| Page body | Prebuilt snapshot (table/text) until **Load full page** |
| Bracket | Compact dataframe only until expanded |
| Home / Previous / History | Text facts only until expanded |

---

## Page load measurement (browser)

| Page | First paint target | Total target (QA mode) |
|------|-------------------|------------------------|
| Home Dashboard | &lt; 1.5s | &lt; 4s (quick view) |
| Live Game Center | &lt; 2s | &lt; 5s (QA/safe) |
| Playoff Bracket | &lt; 1.5s | &lt; 6s |
| Matchup Lineups | &lt; 1.5s | &lt; 5s |
| Player Playoff Tracker | &lt; 2s | &lt; 8s |
| Legacy Tracker | &lt; 2s | &lt; 6s |
| Team History & Leaders | &lt; 1s | &lt; 4s |
| Previous Rounds | &lt; 1.5s | &lt; 6s |

**Normal mode** (API sync + live Home + full Live GC) will exceed these — profiling focus (P5 polish phase):

| Page | Likely bottleneck (normal mode) | Mitigation direction |
|------|-----------------------------------|----------------------|
| Home Dashboard | Live bundle on **Go live**; injury/star pulls | Keep quick view default; 8s timeout guard |
| Playoff Bracket | `get_playoff_state` API refresh loop | Session cache TTL; sidebar auto-sync toggle |
| Matchup Lineups | `season_averages` per card + headshots | Curated board for Finals teams (`_lineups_use_curated_board`) |
| Player Playoff Tracker | Prior-season log on every load | YoY checkbox; expanders for pressure/narrative |
| Legacy Tracker | Full game log table on load | Log in expander; meters/cards first paint |

Headless script (`scripts/audit_page_performance.py`) shows playoff engine & validation &lt;20 ms; browser cost is Streamlit render + network.

---

## Headless audit script

```bash
python scripts/audit_page_performance.py
python scripts/audit_page_performance.py --team "San Antonio Spurs"
```

Ranks engine paths without Streamlit UI. Re-run after changes to compare regressions.

---

## Top 5 bottlenecks (ranked, typical cold Cloud run)

Approximate from `audit_page_performance.py` + Home perf footer on `dev`. Order may shift with cache warmth.

| Rank | Component | ~ms | Why |
|------|-----------|-----|-----|
| 1 | **`get_playoff_state_cached` / NBA API bracket sync** | 3000–15000+ | `fetch_completed_games_recent` loops scoreboard + gamefinder when API sync on; runs on most pages + 60s autorefresh |
| 2 | **Home “Go live” bundle** | 2000–8000 | `series_for_team` + `featured_broadcast_state` + injury paths (8s timeout cap) |
| 3 | **Live GC Layer 1 resolve** | 1500–5000 | CDN scoreboard + stats-today enrichment per render |
| 4 | **Player Playoff Tracker — game logs + Plotly** | 2000–6000 | `_cached_playoff_gamelog` + 2–3 `st.plotly_chart` per player change |
| 5 | **Matchup Intelligence full board** | 1500–4000 | `build_matchup_intelligence_sections` on button (injury + scouting build) |

**Honorable mentions:** Playoff bracket HTML assembly (~1–3s), `estimated_starters_from_api` / rotation API on lineups (~30–65s cold without QA), Legacy simulator `build_legacy_path` + Plotly (~2–4s).

**QA mode fix:** lineups use `_curated_starters_list` — avoids rotation/roster API entirely.

---

## Cache audit

| Pattern | TTL | Issue | Mitigation |
|---------|-----|-------|------------|
| `get_playoff_state_cached` | 90s | Rebuilt on many pages; autorefresh invalidates feel | QA mode: `api_refresh=False`; keep demo backup |
| `fetch_completed_games_recent` | per call | Heavy when `api_refresh=True` | Sidebar off or QA mode |
| `get_live_games` / CDN | 12–35s | Live GC + Home hit on “Go live” | QA → safe Live GC; quick view default |
| `estimated_starters_from_api` | 86400s | Cold miss still hits rotation APIs | QA → curated lineups |
| `playoff_game_logs_for_player` | 1800s | Player + Legacy pages | QA skips or defers |
| `build_matchup_intelligence_sections` | 900s | Large first load | Button-gated; QA skips entirely |
| Headshots / logos | CDN URLs | Many `<img>` per lineups page | No extra fetch in QA; browser caches |

**Fixed in this pass:** `render_previous_rounds_history` no longer calls `get_merged_playoff_state()` twice.

---

## Critical content first

| Page | Renders first |
|------|----------------|
| All fan pages | `render_fan_page_hero` + `render_playoff_matchup_ribbon` → marks **first paint** |
| Home | Hero HTML + emphasis in `st.empty()` slots before series board |
| Live GC | Instant shell + trust strip before tabs |
| Matchup header pages | Team vs opponent header marks first paint |

Secondary sections (charts, simulators, full intel) load after or are skipped in QA mode.

---

## Related docs

- [PHASE_STABILITY.md](./PHASE_STABILITY.md) — Home perf targets (§2)
- [VALIDATION_STATUS.md](./VALIDATION_STATUS.md) — P5 factual spot-check (use QA mode first)
- [LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md) — Layer 1/2/3, safe mode
