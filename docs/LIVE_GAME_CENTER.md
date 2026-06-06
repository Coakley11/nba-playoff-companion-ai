# Live Game Center — source of truth

**Last updated:** 2026-06-06  
**Code entry:** `render_live_game_center` · `render_live_game_center_safe` · `_resolve_live_gc_layer1_fast`

> If this doc and code disagree, reconcile in the **same change**. See [WORKFLOW.md](./WORKFLOW.md).

---

## Purpose

Fan-facing **in-game command post** for the selected team: score, clock, period, win probability, and (when enabled) analysis, box score, play-by-play, and charts.

---

## Safe mode (authoritative)

| Item | Rule |
|------|------|
| **Flag** | `LIVE_GC_SAFE_MODE` in `streamlit_app.py` (default: **`True`** during Finals Game 2 incident — 2026-06-05) |
| **Detector** | `_live_gc_safe_mode_active()` → when True, **never** run full GC |
| **Entry path** | `render_live_game_center` → immediately delegates to `render_live_game_center_safe` |
| **UI banner** | Red bar: "Emergency game-night mode active — live feed unavailable, using manual/local score." |
| **Allowed work** | Local Finals schedule shell (Game 2), emergency score entry at top, trust strip, win prob, keys to success |
| **Blocked** | CDN/stats on first paint; box score, PBP, shot chart, injury scrape, headshots, advanced charts; Live GC auto-refresh |
| **Feed retry** | Optional "Retry live feed (2s max)" — hard `LIVE_GC_FEED_TIMEOUT_SEC` = **2.0**; falls back to local on timeout |
| **When to enable** | Streamlit Cloud timeouts, API outages, or incident response—document in [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) |
| **When to disable** | Layer 1 stable on Cloud under expected load; full L2/L3 probed on dev |

**Emergency hard route (2026-06-06):** When the selected page is Live Game Center, `main()` returns immediately after shell + disk restore and renders `render_live_game_center_emergency_only()` — no playoff engine, bracket API, roster lookups, or full sidebar setup.

**Emergency game-night mode (2026-06-05):** Finals Game 2 (Knicks vs Spurs). Page paints instantly from `PLAYOFF_SCHEDULE_FALLBACK` + canonical Game 1 (`Knicks 105, Spurs 95`, series 1–0). Manual score entry at top powers trust strip, win probability, and keys to success. No API before first paint.

**Live Game Center route:** Bracket NBA API auto-sync is forced off on the Live Game Center page — local/demo playoff state only (`get_playoff_state_cached(True, False)`); sidebar toggle unchanged on other pages.

**Do not** change safe mode behavior without updating this section.

---

## Layer architecture (authoritative)

| Layer | Responsibility | Load policy |
|-------|----------------|-------------|
| **Layer 1** | CDN scoreboard parse, profile/series context, instant shell, live score banner | **Always** on page open; target &lt; 2s resolve |
| **Layer 2** | Analysis tabs, depth panels, win-prob narrative | On tab select or auto only for statuses in `LIVE_GC_ADVANCED_AUTO_STATUSES` (`live`) |
| **Layer 3** | Heavy charts, deep PBP | Explicit opt-in only |

**Render sequence (full mode, not safe):**

1. Clear per-team session keys when favorite team changes (`live_gc__*`, `live_gc_depth_*`, …).  
2. Render **trust strip** in `layer1_slot` with connecting placeholder (`_live_gc_connecting_state`).  
3. `_resolve_live_gc_layer1_fast(team, profile)` — replace slot with real scoreboard or fallback UI.  
4. **Pregame / starting soon:** `_render_live_gc_pregame_panel` only (no tabbed Layer 2/3 until after tipoff).  
5. **Live / final:** `_render_live_gc_layer1` + tabbed sections on demand.  
6. Hero + matchup ribbon + manual override panel (below pinned scoreboard).  
7. Layer 2/3 tabs only after tipoff (live/final) or explicit tab selection.

**Manual override priority:** If session manual game is set, Layer 1 uses `priority == "manual"` and `_render_manual_live_game_center`.

---

## Layer 1 resolution priority (authoritative)

Order in `_resolve_live_gc_layer1_fast`:

1. **Manual session game** — user-entered home/away/status (Dev Lab or fan override panel).  
2. **CDN live row** — `fetch_cdn_scoreboard_only` / parsed row for favorite team.  
3. **Stats today (ET)** — merge or rescue when CDN row missing or stale.  
4. **Last-known score** — session cache when CDN returns suspicious 0–0 during live Q1+.  
5. **Local schedule fallback** — `PLAYOFF_SCHEDULE_FALLBACK` (e.g. Finals Game 2 at 8:30 PM ET) when feeds are quiet pregame.  
6. **Profile / static fallback** — opponent, round, scheduled messaging when no row at all (`priority` static).

Parsed game must expose: phase, scores, period, clock, opponent (`opp_name`), optional `gid` for session cache invalidation.

---

## Refresh rules (authoritative)

| Mechanism | Interval / trigger | Scope |
|-----------|-------------------|--------|
| **Page autorefresh** | `PLAYOFF_BRACKET_REFRESH_MS` = **60_000 ms** | Live GC listed in `playoff_auto_refresh_pages` via `tick_playoff_state_autorefresh` |
| **Manual refresh** | User button "Refresh Live Game Data" | Clears CDN/stats/broadcast caches listed in handler, then `st.rerun()` |
| **Safe mode refresh** | Button "Refresh scoreboard" | Clears `fetch_cdn_scoreboard_only`, `_scoreboard_stats_today_et` |
| **Cache TTL** | `PLAYOFF_STATE_CACHE_TTL_SEC` = **90 s** | Playoff state used for ribbon/context—not a substitute for scoreboard freshness |

**Caption on page:** "Scores and bracket context auto-refresh about every 60 seconds while this page is open."

---

## Trust strip (authoritative — always visible)

Every Live GC render (full, safe, no-feed) must call `_render_live_gc_trust_strip` after Layer 1 resolve:

| Field | Source |
|-------|--------|
| **Status** | `_live_status_chip(state)` |
| **Score** | `parsed` away–home scores, or `—` if no feed row |
| **Clock** | Quarter + clock from `parsed`, or status text |
| **Source** | `state.source_label` |
| **Last updated** | `state.updated_at` (or last-known timestamp if stale) |

Fans must never hunt inside expanders or Layer 2 tabs for basic score metadata.

---

## Reliability requirements (must hold)

1. **Trust strip** visible on every path (including safe mode and feed-unavailable).
2. **No fake 0–0** during live Q1+: `_live_gc_suspicious_zero_zero_live` falls back to last-known score when CDN returns stale zeros.
3. **First paint** must not await Layer 2/3 network calls.
4. **Instant shell** visible before Layer 1 resolve completes.
5. **Clear empty state** via `_live_gc_fan_msg` / `feed_banner` when no game—never a blank main panel.
6. **Home Dashboard** deep links set `st.session_state["page_override"] = "🔴 Live Game Center"`.
7. **Win probability** uses `live_win_probability` / headless `calculate_win_probability`—deterministic for tests.
8. **Trace** optional: `live_gc_trace` session list; Dev Lab Live GC tab for diagnostics.
9. **API flags** — behavior when `NBA_LIVE_AVAILABLE`, `NBA_STATS_AVAILABLE`, `NBA_SCOREBOARD_V3_AVAILABLE` are false must degrade gracefully (banner + profile context).

---

## Constants reference (sync with code)

```text
LIVE_GC_SAFE_MODE = True
LIVE_GC_FEED_TIMEOUT_SEC = 2.0
PLAYOFF_BRACKET_REFRESH_MS = 60000
PLAYOFF_STATE_CACHE_TTL_SEC = 90
LIVE_GC_AUTO_LOAD_STATUSES = live, starting soon, final, scheduled
LIVE_GC_ADVANCED_AUTO_STATUSES = live
```

---

## Home Dashboard integration

- Eliminated teams: Home disables live bundle; Live GC still reachable for *other* games copy.  
- `Go live` on Home does **not** replace Live GC architecture—it loads a bounded live bundle (8s timeout) for hero/injury only.

---

## Testing & diagnostics

| Tool | Use |
|------|-----|
| `resolve_live_game_state(team, network=False)` | Profile-only resolve |
| `resolve_live_game_state(team, network=True)` | Full Layer 1 |
| `scripts/test_live_gc_layer1.py` | Layer 1 regression |
| Dev Lab → Live GC tab | Timing, trace, debug expander |
| Dev Lab → Live GC session log | `_live_gc_record_validation_tick` — trust-strip ticks per visit |

---

## Planned changes (update doc when done)

- [ ] Cloud perf sign-off for full GC (`LIVE_GC_SAFE_MODE` back to False after Game 2).  
- [x] Emergency game-night mode for Finals Game 2 (2026-06-05).  
- [ ] Document max concurrent user guidance after load test.  
- [x] Schedule fallback wired into Layer 1 fast resolver (2026-06-05).  
- [x] Pregame panel + trust-strip-first paint (2026-06-05).
