"""
Command Center activity hooks — meaningful NBA analysis only.
"""

from __future__ import annotations

from typing import Any


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

        record_activity(
            "nba",
            event,
            page=page or "NBA Companion",
            metrics=metrics or {},
            summary=summary,
            resume_key=resume_key,
            resume_title=resume_title,
            resume_subtitle=resume_subtitle,
            local_state={"team": metrics.get("team", ""), "page": page},
        )
    except Exception:
        pass


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
