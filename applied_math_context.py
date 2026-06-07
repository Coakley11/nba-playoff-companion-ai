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


def record_legacy_stat_gap_context(
    session_state: dict[str, Any],
    *,
    player: str,
    team_name: str,
    stat_label: str,
    stat_key: str,
    current_value: Any,
    target_name: str,
    target_value: Any,
    gap: Any,
    games_remaining: int | None = None,
    rate_needed: str | None = None,
    historical_comparison: str = "",
    all_gaps: list[dict[str, Any]] | None = None,
) -> None:
    """Cache franchise chase / legacy stat-gap data for Applied Math sidebar."""
    rate_str = str(rate_needed or "").strip()
    summary_parts = [
        f"{player} has {current_value} {stat_label}",
        f"target {target_name} has {target_value}",
        f"gap {gap}",
    ]
    if games_remaining is not None:
        summary_parts.append(f"{games_remaining} games left est.")
    if rate_str:
        summary_parts.append(f"needs ~{rate_str}")

    stat_gap = {
        "player": player,
        "comparison": target_name,
        "stat": stat_label,
        "stat_key": stat_key,
        "current_value": current_value,
        "target_value": target_value,
        "gap": gap,
        "games_remaining": games_remaining,
        "rate_needed": rate_str or None,
        "summary": "; ".join(summary_parts),
    }
    legacy_ctx = {
        "player": player,
        "team": team_name,
        "stat_gap": stat_gap,
        "games_remaining": games_remaining,
        "rate_needed": rate_str or None,
        "historical_comparison": historical_comparison or None,
        "chase_gaps": all_gaps or [stat_gap],
    }
    session_state["_ami_stat_gap_context"] = legacy_ctx
    session_state["_ami_legacy_context"] = legacy_ctx
    cache_page_context(session_state, "Legacy Tracker", legacy_ctx)
    cache_page_context(session_state, "Player Playoff Tracker", legacy_ctx)


def record_matchup_intelligence_context(
    session_state: dict[str, Any],
    *,
    team_name: str,
    opponent: str,
    meta: dict[str, Any],
    section_summaries: list[str] | None = None,
    injury_summary: str = "",
    key_players: list[str] | None = None,
    win_probability: str | None = None,
    series_probability: str | None = None,
) -> None:
    """Cache matchup scouting data for Applied Math sidebar."""
    tw = meta.get("tw")
    ow = meta.get("ow")
    ctx: dict[str, Any] = {
        "team": team_name,
        "opponent": opponent,
        "workflow": "Matchup intelligence",
        "series_record": f"{tw}-{ow}" if tw is not None and ow is not None else None,
        "matchup_advantages": section_summaries or [],
        "injury_summary": injury_summary or None,
        "key_players": [p for p in (key_players or []) if p],
        "pressure_score": meta.get("pressure"),
        "games_played": meta.get("games_n"),
    }
    if win_probability:
        ctx["win_probability"] = win_probability
    if series_probability:
        ctx["series_probability"] = series_probability
    session_state["_ami_matchup_context"] = ctx
    cache_page_context(session_state, "Matchup Intelligence", ctx)


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

    if "legacy" in low or "playoff tracker" in low:
        ctx["workflow"] = "Legacy / career context"
        leg = session_state.get("_ami_legacy_context") or session_state.get("_ami_stat_gap_context")
        if isinstance(leg, dict):
            ctx.update(leg)
            if isinstance(leg.get("stat_gap"), dict):
                ctx["stat_gap"] = leg["stat_gap"]

    cached = session_state.get("_ami_context_by_page")
    if isinstance(cached, dict):
        block = cached.get(p)
        if isinstance(block, dict):
            for k, v in block.items():
                if v is not None and v != "" and k not in ctx:
                    ctx[k] = v
    return ctx


def build_source_state(page: str, session_state: dict[str, Any]) -> dict[str, Any]:
    """Serializable snapshot for Return Insight page restore."""
    from datetime import datetime, timezone

    p = str(page or "").strip()
    low = p.lower()
    widget_params: dict[str, Any] = {}
    entity_params: dict[str, Any] = {"page": p}
    filter_params: dict[str, Any] = {}

    team = session_state.get("_nba_persist_team") or session_state.get("favorite_team")
    if team:
        entity_params["team"] = str(team)
        widget_params["favorite_team"] = str(team)

    if "matchup" in low or "injury" in low:
        mi = session_state.get("_ami_matchup_context")
        if isinstance(mi, dict):
            entity_params.update({k: v for k, v in mi.items() if v is not None})
        opp = session_state.get("matchup_opponent") or entity_params.get("opponent")
        if opp:
            entity_params["opponent"] = str(opp)

    if "legacy" in low or "playoff tracker" in low:
        leg = session_state.get("_ami_legacy_context") or session_state.get("_ami_stat_gap_context")
        if isinstance(leg, dict):
            entity_params.update({k: v for k, v in leg.items() if v is not None})

    if "live" in low or "game" in low:
        for k in ("live_win_prob_display", "_last_win_prob", "live_selected_team"):
            if session_state.get(k) is not None:
                widget_params[k] = session_state[k]

    page_label = str(session_state.get("page_label_last") or session_state.get("page_override") or p)
    return {
        "source_app": "nba",
        "source_page": p,
        "page_params": {"page": page_label},
        "entity_params": entity_params,
        "widget_params": widget_params,
        "filter_params": filter_params,
        "chart_params": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def apply_source_state_to_session(session_state: dict[str, Any], source_state: dict[str, Any]) -> None:
    """Map stored source_state into NBA session restore keys."""
    if not source_state:
        return
    ent = dict(source_state.get("entity_params") or {})
    wp = dict(source_state.get("widget_params") or {})
    team = ent.get("team") or wp.get("favorite_team")
    if team:
        session_state["_nba_restore_team"] = str(team)
        session_state["favorite_team"] = str(team)
    page = str(
        source_state.get("source_page")
        or source_state.get("page_params", {}).get("page")
        or ""
    ).strip()
    if page:
        session_state["page_override"] = page
    for k, v in wp.items():
        if v is not None:
            session_state[k] = v

