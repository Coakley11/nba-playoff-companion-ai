# Live Game Center — source of truth

**Last updated:** 2026-06-04  
**Code entry:** `render_live_game_center` · `render_live_game_center_safe` · `_resolve_live_gc_layer1_fast`

> If this doc and code disagree, reconcile in the **same change**. See [WORKFLOW.md](./WORKFLOW.md).

---

## Purpose

Fan-facing **in-game command post** for the selected team: score, clock, period, win probability, and (when enabled) analysis, box score, play-by-play, and charts.

---

## Safe mode (authoritative)

| Item | Rule |
|------|------|
| **Flag** | `LIVE_GC_SAFE_MODE` in `streamlit_app.py` (default: `False`) |
| **Detector** | `_live_gc_safe_mode_active()` → when True, **never** run full GC |
| **Entry path** | `render_live_game_center` → immediately delegates to `render_live_game_center_safe` |
| **UI banner** | Dark bar: "SAFE MODE — live scoreboard only (analysis, box score, PBP, and charts disabled temporarily)" |
| **Allowed work** | Layer 1 resolve only, manual refresh button, safe board render, emergency manual game entry |
| **When to enable** | Streamlit Cloud timeouts, API outages, or incident response—document in [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) |
| **When to disable** | Layer 1 stable on Cloud under expected load; full L2/L3 probed on dev |

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
2. Render **instant shell** in `layer1_slot` (connecting state).  
3. `_resolve_live_gc_layer1_fast(team, profile)` — replace slot with real or fallback UI.  
4. Hero + matchup ribbon + manual override panel.  
5. Layer 2/3 only after user action or auto rules above.

**Manual override priority:** If session manual game is set, Layer 1 uses `priority == "manual"` and `_render_manual_live_game_center`.

---

## Layer 1 resolution priority (authoritative)

Order in `_resolve_live_gc_layer1_fast`:

1. **Manual session game** — user-entered home/away/status (Dev Lab or fan override panel).  
2. **CDN live row** — `fetch_cdn_scoreboard_only` / parsed row for favorite team.  
3. **Profile / static fallback** — opponent, round, scheduled messaging when no live row (`priority` static/stale).

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

## Reliability requirements (must hold)

1. **First paint** must not await Layer 2/3 network calls.  
2. **Instant shell** visible before Layer 1 resolve completes.  
3. **Clear empty state** via `_live_gc_fan_msg` / `feed_banner` when no game—never a blank main panel.  
4. **Home Dashboard** deep links set `st.session_state["page_override"] = "🔴 Live Game Center"`.  
5. **Win probability** uses `live_win_probability` / headless `calculate_win_probability`—deterministic for tests.  
6. **Trace** optional: `live_gc_trace` session list; Dev Lab Live GC tab for diagnostics.  
7. **API flags** — behavior when `NBA_LIVE_AVAILABLE`, `NBA_STATS_AVAILABLE`, `NBA_SCOREBOARD_V3_AVAILABLE` are false must degrade gracefully (banner + profile context).

---

## Constants reference (sync with code)

```text
LIVE_GC_SAFE_MODE = False
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

---

## Planned changes (update doc when done)

- [ ] Cloud perf sign-off for full GC (`LIVE_GC_SAFE_MODE` stays False on prod).  
- [ ] Document max concurrent user guidance after load test.  
- [ ] Optional: persist manual game to suite session (dev-only).
