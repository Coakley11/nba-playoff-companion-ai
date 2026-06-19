"""
Command Center activity hooks — meaningful NBA analysis only.
"""

from __future__ import annotations

from typing import Any


def _active_workspace_id() -> str:
    try:
        from suite_workspace import get_active_workspace_id

        return get_active_workspace_id()
    except Exception:
        return "daniel"


def _record(
    event: str,
    *,
    page: str = "",
    metrics: dict[str, Any] | None = None,
    summary: str = "",
    resume_key: str = "",
    resume_title: str = "",
    resume_subtitle: str = "",
) -> None:
    try:
        from suite_activity_client import record_activity

        payload = dict(metrics or {})
        payload.setdefault("workspace_id", _active_workspace_id())
        team = str(payload.get("team") or "").strip()
        record_activity(
            "nba",
            event,
            page=page or "NBA Companion",
            metrics=payload,
            summary=summary,
            resume_key=resume_key,
            resume_title=resume_title,
            resume_subtitle=resume_subtitle,
            local_state={"team": team, "page": page, "workspace_id": payload["workspace_id"]},
        )
    except Exception:
        pass


def log_team_selected(team: str, *, page: str = "") -> None:
    """Emit when the active workspace team changes — always scoped to workspace profile."""
    team = str(team or "").strip()
    if not team:
        return
    label = str(page or "NBA Companion").strip()
    _record(
        "team_selected",
        page=label,
        metrics={"team": team, "page": label},
        summary=f"Selected {team}",
        resume_key=f"nba:team:{team}",
        resume_title=f"Continue with {team}",
        resume_subtitle=label,
    )


def log_legacy_tracker_player(team: str, player: str, *, page: str = "Legacy Tracker") -> None:
    team = str(team or "").strip()
    player = str(player or "").strip()
    if not team or not player:
        return
    _record(
        "legacy_tracker_focus",
        page=page,
        metrics={"team": team, "player": player, "page": page},
        summary=f"Tracking {player} ({team})",
        resume_key=f"nba:legacy:{team}:{player}",
        resume_title=f"Continue Legacy Tracker — {player}",
        resume_subtitle=team,
    )


def log_settings_changed(team: str, setting: str, *, page: str = "NBA Companion") -> None:
    team = str(team or "").strip()
    setting = str(setting or "").strip()
    if not setting:
        return
    _record(
        "nba_settings_change",
        page=page,
        metrics={"team": team, "setting": setting, "page": page},
        summary=f"Updated {setting}" + (f" ({team})" if team else ""),
        resume_key=f"nba:settings:{team}" if team else "nba:settings",
        resume_title="Return to NBA Companion",
        resume_subtitle=setting,
    )


def log_from_page_context(team: str, page: str, page_label: str = "") -> None:
    """Map completed analysis pages to events — never log passive navigation."""
    label = str(page_label or page or "").strip()
    lower = label.lower()
    team = str(team or "").strip()
    if not team and not label:
        return

    if "injury" in lower:
        _record(
            "injury_analysis",
            page=label,
            metrics={"team": team, "page": label},
            summary=f"Reviewed injury report ({team})" if team else "Reviewed injury report",
            resume_key=f"nba:injury:{team}",
            resume_title=f"Review injury report implications ({team})" if team else "Review injury report",
            resume_subtitle=label,
        )
        return

    if any(k in lower for k in ("matchup", "game outlook", "outlook", "preview")):
        _record(
            "matchup_analysis",
            page=label,
            metrics={"team": team, "page": label},
            summary=f"Analyzed {team} matchup" if team else "Analyzed game matchup",
            resume_key=f"nba:matchup:{team}",
            resume_title=f"Continue {team} matchup analysis" if team else "Continue matchup analysis",
            resume_subtitle=label,
        )
        return

    if "playoff" in lower or "bracket" in lower or "series" in lower:
        _record(
            "playoff_simulation",
            page=label,
            metrics={"team": team, "page": label},
            summary=f"Simulated playoff series ({team})" if team else "Simulated playoff series",
            resume_key=f"nba:playoff:{team}",
            resume_title=f"Continue {team} playoff outlook" if team else "Continue playoff analysis",
            resume_subtitle=label,
        )
        return

    if "compare" in lower or "player" in lower and "vs" in lower:
        _record(
            "player_comparison",
            page=label,
            metrics={"team": team, "page": label},
            summary="Compared players",
            resume_key=f"nba:compare:{team}",
            resume_title="Continue player comparison",
            resume_subtitle=label,
        )
        return

    if "legacy" in lower and "tracker" in lower:
        player = ""
        try:
            import streamlit as st_module  # noqa: WPS433

            player = str(st_module.session_state.get("legacy_tracker_player") or "").strip()
        except Exception:
            pass
        if player:
            log_legacy_tracker_player(team, player, page=label)
        else:
            _record(
                "playoff_tracker_review",
                page=label,
                metrics={"team": team, "page": label},
                summary=f"Opened Legacy Tracker ({team})" if team else "Opened Legacy Tracker",
                resume_key=f"nba:tracker:{team}",
                resume_title="Continue Legacy Tracker",
                resume_subtitle=label,
            )
        return

    if "tracker" in lower or "standings" in lower and "playoff" in lower:
        _record(
            "playoff_tracker_review",
            page=label,
            metrics={"team": team, "page": label},
            summary="Updated playoff tracker",
            resume_key=f"nba:tracker:{team}",
            resume_title="Continue playoff tracker",
            resume_subtitle=label,
        )
        return

    if "live" in lower and "game" in lower:
        _record(
            "game_outlook",
            page=label,
            metrics={"team": team, "page": label},
            summary=f"Generated game outlook ({team})" if team else "Generated game outlook",
            resume_key=f"nba:game:{team}",
            resume_title=f"Continue {team} game analysis" if team else "Continue game analysis",
            resume_subtitle=label,
        )
        return

    if team:
        _record(
            "team_session",
            page=label,
            metrics={"team": team, "page": label},
            summary=f"Working with {team} — {label}",
            resume_key=f"nba:session:{team}",
            resume_title=f"Return to {team}",
            resume_subtitle=label,
        )
