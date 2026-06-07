"""Page-specific Applied Math context extractors for NBA."""

from __future__ import annotations

from typing import Any


def cache_page_context(session_state: dict[str, Any], page: str, ctx: dict[str, Any]) -> None:
    if not page or not ctx:
        return
    store = session_state.setdefault("_ami_context_by_page", {})
    if not isinstance(store, dict):
        store = {}
    store[str(page)] = dict(ctx)
    session_state["_ami_context_by_page"] = store


def build_nba_applied_math_context(page: str, session_state: dict[str, Any]) -> dict[str, Any]:
    p = str(page or "").strip()
    low = p.lower()
    ctx: dict[str, Any] = {"page": p}

    team = session_state.get("_nba_persist_team") or session_state.get("favorite_team")
    if team:
        ctx["team"] = str(team)

    pst = session_state.get("playoff_team_state")
    if isinstance(pst, dict):
        opp = str(pst.get("current_opponent") or pst.get("opponent") or "").strip()
        if opp and opp not in ("TBD", "None"):
            ctx["opponent"] = opp
        sp = pst.get("series_win_probability") or pst.get("series_prob")
        if sp is not None:
            try:
                ctx["series_probability"] = f"{float(sp):.0f}%"
            except (TypeError, ValueError):
                ctx["series_probability"] = str(sp)

    if "live" in low or "game" in low:
        ctx["workflow"] = "Live game analysis"
        wp = session_state.get("live_win_prob_display") or session_state.get("_last_win_prob")
        if wp is not None:
            try:
                ctx["win_probability"] = f"{float(wp):.0f}%"
            except (TypeError, ValueError):
                ctx["win_probability"] = str(wp)

    if "matchup" in low or "injury" in low:
        ctx["workflow"] = "Matchup intelligence"
        mi = session_state.get("_ami_matchup_context")
        if isinstance(mi, dict):
            ctx.update(mi)

    if "legacy" in low:
        ctx["workflow"] = "Legacy / career context"
        leg = session_state.get("_ami_legacy_context")
        if isinstance(leg, dict):
            ctx.update(leg)

    stat_ctx = session_state.get("_ami_stat_gap_context")
    if isinstance(stat_ctx, dict):
        ctx.update(stat_ctx)

    cached = session_state.get("_ami_context_by_page")
    if isinstance(cached, dict):
        block = cached.get(p)
        if isinstance(block, dict):
            for k, v in block.items():
                if v is not None and v != "" and k not in ctx:
                    ctx[k] = v
    return ctx
