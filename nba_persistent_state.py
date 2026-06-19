"""Disk + cloud persistence for NBA Playoff Companion."""

from __future__ import annotations

import copy
from typing import Any

from suite_user_persistence import (
    autosave_if_changed,
    sync_workspace_protocol,
)

APP_ID = "nba"

NBA_TEAM_SELECT_KEY = "favorite_team_sidebar"
NBA_PAGE_RADIO_KEY = "nba_choose_page"

_PERSIST_KEYS = (
    "favorite_team_sidebar",
    "page_override",
    "page_label_last",
    "USE_DEMO_BACKUP",
    "ENABLE_BRACKET_API_REFRESH",
    "dev_lab_enabled",
    "SHOW_PERF_DEBUG",
    "QA_MODE",
    "ULTRA_FAST_VALIDATION_MODE",
    "HOME_DASH_LIVE_UPDATES",
    "manual_live_enabled",
    # Page sub-state
    "legacy_tracker_player",
    "pp_hub_player",
    "pp_hub_season",
    "pp_hub_stat",
    "_live_gc_sel_team",
    "_live_gc_gid",
    # Live Game Center manual override panel
    "manual_live_home_team",
    "manual_live_away_team",
    "manual_live_home_score",
    "manual_live_away_score",
    "manual_live_quarter",
    "manual_live_clock",
    "manual_live_status",
    "manual_live_series_score",
    "manual_live_top_performers",
    "manual_live_top_plays",
    "manual_live_injuries",
    "manual_live_notes",
)

_NBA_DYNAMIC_PREFIXES = (
    "load_matchup_intel_",
    "live_gc_last_known_",
    "live_gc_swing_",
)


def _collect_nba_dynamic_state(ss: dict[str, Any]) -> dict[str, Any]:
    dynamic: dict[str, Any] = {}
    for key in list(ss.keys()):
        sk = str(key)
        if any(sk.startswith(prefix) for prefix in _NBA_DYNAMIC_PREFIXES):
            try:
                dynamic[sk] = copy.deepcopy(ss[key])
            except Exception:
                dynamic[sk] = ss[key]
    return dynamic


def _apply_nba_dynamic_state(st: Any, dynamic: dict[str, Any]) -> None:
    for key, val in dynamic.items():
        try:
            st.session_state[key] = copy.deepcopy(val)
        except Exception:
            st.session_state[key] = val


def build_nba_disk_state(st: Any) -> dict[str, Any]:
    ss = st.session_state
    state: dict[str, Any] = {}
    for key in _PERSIST_KEYS:
        if key in ss:
            state[key] = copy.deepcopy(ss[key])
    team = ss.get("_nba_persist_team")
    if team:
        state["favorite_team"] = str(team)
    dynamic = _collect_nba_dynamic_state(ss)
    if dynamic:
        state["_nba_dynamic"] = dynamic
    return state


def apply_nba_disk_state(st: Any, state: dict[str, Any]) -> None:
    team = state.pop("favorite_team", None)
    if team:
        st.session_state["_nba_restore_team"] = team
        st.session_state["favorite_team"] = team
    dynamic = state.pop("_nba_dynamic", None)
    if isinstance(dynamic, dict):
        _apply_nba_dynamic_state(st, dynamic)
    for key, val in state.items():
        st.session_state[key] = copy.deepcopy(val)
    restored_team = st.session_state.get("_nba_restore_team") or st.session_state.get("favorite_team")
    if restored_team:
        st.session_state[NBA_TEAM_SELECT_KEY] = restored_team
    page_label = st.session_state.get("page_label_last") or st.session_state.get("page_override")
    if page_label:
        st.session_state[NBA_PAGE_RADIO_KEY] = page_label


def apply_nba_session_defaults(st: Any) -> None:
    """Return session keys to app widget defaults without touching playoff caches."""
    ss = st.session_state
    for key in _PERSIST_KEYS:
        ss.pop(key, None)
    for key in ("page_override", "page_label_last", "_nba_restore_team", "_nba_persist_team", "favorite_team"):
        ss.pop(key, None)
    ss.pop(NBA_TEAM_SELECT_KEY, None)
    ss.pop(NBA_PAGE_RADIO_KEY, None)
    for key in list(ss.keys()):
        sk = str(key)
        if any(sk.startswith(prefix) for prefix in _NBA_DYNAMIC_PREFIXES):
            ss.pop(key, None)
    ss.pop("_nba_dynamic", None)


def restore_nba_disk_shell(st: Any) -> bool:
    """Fast disk-only restore for shell widgets — no cloud round-trip."""
    try:
        from suite_user_persistence import _load_raw

        disk_state, _, _ = _load_raw(APP_ID)
    except Exception:
        return False
    if not disk_state:
        return False
    apply_nba_disk_state(st, disk_state)
    return True


def prepare_nba_workspace(st: Any, *, cloud_first: bool = True) -> bool:
    """Authoritative workspace-scoped disk + cloud sync."""
    return sync_workspace_protocol(
        st,
        APP_ID,
        apply_state=lambda st_obj, s: apply_nba_disk_state(st_obj, s),
        cloud_first=cloud_first,
    )


def restore_nba_disk_state_once(st: Any) -> bool:
    """Backward-compatible alias — prefer ``prepare_nba_workspace()`` at startup."""
    return prepare_nba_workspace(st)


def persist_nba_team_change(st: Any, team: str) -> bool:
    """Immediately persist team selection for the active workspace profile."""
    st.session_state["_nba_persist_team"] = team
    st.session_state["favorite_team"] = team
    st.session_state["favorite_team_sidebar"] = team
    page = str(
        st.session_state.get("page_label_last")
        or st.session_state.get("page_override")
        or "NBA Companion"
    ).strip()
    try:
        from nba_activity import log_team_selected

        log_team_selected(team, page=page)
    except Exception:
        pass
    from suite_user_persistence import force_autosave

    return force_autosave(st, APP_ID, build_state=build_nba_disk_state, reason="team_change")


def autosave_nba_state(st: Any) -> None:
    autosave_if_changed(st, APP_ID, build_state=build_nba_disk_state)


def default_reset_nba_session(st: Any) -> None:
    """
    Full NBA reset: session defaults, fresh local disk, and cleared cloud ``full_session``.

    Called from sidebar Reset after ``reset_user_state`` deletes the disk file.
    """
    from suite_user_persistence import finalize_suite_reset

    apply_nba_session_defaults(st)
    fresh = build_nba_disk_state(st)
    finalize_suite_reset(st, APP_ID, fresh, summary="Reset to defaults")
