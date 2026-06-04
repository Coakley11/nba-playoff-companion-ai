"""Disk + cloud persistence for NBA Playoff Companion."""

from __future__ import annotations

import copy
from typing import Any

from suite_user_persistence import (
    autosave_if_changed,
    restore_once,
    save_user_state,
)

APP_ID = "nba"

_PERSIST_KEYS = (
    "favorite_team_sidebar",
    "page_override",
    "page_label_last",
    "USE_DEMO_BACKUP",
    "ENABLE_BRACKET_API_REFRESH",
    "dev_lab_enabled",
    "SHOW_PERF_DEBUG",
    "HOME_DASH_LIVE_UPDATES",
    "manual_live_enabled",
)


def build_nba_disk_state(st: Any) -> dict[str, Any]:
    ss = st.session_state
    state: dict[str, Any] = {}
    for key in _PERSIST_KEYS:
        if key in ss:
            state[key] = copy.deepcopy(ss[key])
    # Persist last sidebar team by storing team name if widget used selectbox value
    team = ss.get("_nba_persist_team")
    if team:
        state["favorite_team"] = str(team)
    return state


def apply_nba_disk_state(st: Any, state: dict[str, Any]) -> None:
    team = state.pop("favorite_team", None)
    if team:
        st.session_state["page_override"] = st.session_state.get("page_override")
        st.session_state["_nba_restore_team"] = team
    for key, val in state.items():
        st.session_state[key] = copy.deepcopy(val)


def apply_nba_session_defaults(st: Any) -> None:
    """Return session keys to app widget defaults without touching playoff caches."""
    ss = st.session_state
    for key in _PERSIST_KEYS:
        ss.pop(key, None)
    for key in ("page_override", "page_label_last", "_nba_restore_team", "_nba_persist_team"):
        ss.pop(key, None)


def restore_nba_disk_state_once(st: Any) -> bool:
    return restore_once(
        st,
        APP_ID,
        apply_state=lambda st_obj, s: apply_nba_disk_state(st_obj, s),
    )


def autosave_nba_state(st: Any) -> None:
    autosave_if_changed(st, APP_ID, build_state=build_nba_disk_state)


def default_reset_nba_session(st: Any) -> None:
    """
    Full NBA reset: session defaults, fresh local disk, and cleared cloud ``full_session``.

    Called from sidebar Reset after ``reset_user_state`` deletes the disk file.
    """
    from suite_user_persistence import _SESSION_RESTORED_PREFIX

    apply_nba_session_defaults(st)

    fresh = build_nba_disk_state(st)
    save_user_state(APP_ID, fresh)

    try:
        from suite_cloud_state import (
            clear_cloud_full_session,
            save_cloud_full_session,
            session_page_summary,
        )

        clear_cloud_full_session(APP_ID)
        page, summary = session_page_summary(APP_ID, fresh)
        save_cloud_full_session(APP_ID, fresh, page=page, summary=summary or "Reset to defaults")
    except Exception:
        pass

    st.session_state[f"{_SESSION_RESTORED_PREFIX}{APP_ID}"] = True
