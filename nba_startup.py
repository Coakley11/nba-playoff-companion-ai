"""NBA startup timing diagnostics — Daniel developer mode only."""

from __future__ import annotations

import time as pytime
from typing import Any

_STARTUP_KEY = "_nba_startup_timing"
_DEFER_KEY = "_nba_deferred_workspace_sync"
_SHELL_KEY = "_nba_shell_usable"


def ensure_fast_load_defaults(st: Any) -> None:
    """Default Fast Load on for new sessions so validation is practical."""
    ss = st.session_state
    if "QA_MODE" not in ss:
        ss["QA_MODE"] = True


def should_defer_heavy_startup(st: Any) -> bool:
    """Fast Load / Lite Mode: skip cloud sync and heavy hydration on this rerun."""
    ss = st.session_state
    if ss.get("ULTRA_FAST_VALIDATION_MODE"):
        return True
    if ss.get("QA_MODE"):
        return True
    return False


def should_skip_page_heavy_body(st: Any, page: str) -> bool:
    """Placeholder main content — shell stays interactive."""
    if not should_defer_heavy_startup(st):
        return False
    if page in frozenset({"Legacy Tracker"}):
        return False
    ss = st.session_state
    key = f"_validation_full_{page.replace(' ', '_').lower()}"
    return not bool(ss.get(key, False))


def mark_deferred_workspace_sync(st: Any) -> None:
    st.session_state[_DEFER_KEY] = True


def pop_deferred_workspace_sync(st: Any) -> bool:
    return bool(st.session_state.pop(_DEFER_KEY, False))


def mark_shell_usable(st: Any, boot_t0: float) -> None:
    st.session_state[_SHELL_KEY] = True
    mark_startup_phase(st, "shell_usable", boot_t0)


def is_shell_usable(st: Any) -> bool:
    return bool(st.session_state.get(_SHELL_KEY))


def mark_startup_phase(st: Any, phase: str, boot_t0: float) -> None:
    try:
        from suite_workspace import can_show_developer_tools

        if not can_show_developer_tools(st=st):
            return
    except Exception:
        return
    bucket = st.session_state.setdefault(_STARTUP_KEY, {"boot_t0": boot_t0, "phases": {}})
    bucket["phases"][phase] = (pytime.perf_counter() - boot_t0) * 1000.0


def record_startup_section(st: Any, name: str, ms: float) -> None:
    try:
        from suite_workspace import can_show_developer_tools

        if not can_show_developer_tools(st=st):
            return
    except Exception:
        return
    bucket = st.session_state.setdefault(_STARTUP_KEY, {"phases": {}, "sections": {}})
    bucket.setdefault("sections", {})[name] = ms


def render_startup_diagnostics(st: Any, boot_t0: float) -> None:
    try:
        from suite_workspace import can_show_developer_tools

        if not can_show_developer_tools(st=st):
            return
    except Exception:
        return

    bucket = st.session_state.get(_STARTUP_KEY) or {}
    phases = bucket.get("phases") or {}
    sections = bucket.get("sections") or {}
    total_ms = (pytime.perf_counter() - boot_t0) * 1000.0

    with st.sidebar.expander("Startup timing (dev)", expanded=False):
        st.caption(f"**Total startup:** {total_ms:.0f} ms")
        for label, key in (
            ("Header render", "header"),
            ("Sidebar render", "sidebar"),
            ("Shell usable", "shell_usable"),
            ("Complete", "complete"),
        ):
            val = phases.get(key)
            if val is not None:
                st.caption(f"{label}: {val:.0f} ms")
        for label, key in (
            ("Restore (disk)", "restore"),
            ("Cloud sync", "cloud_sync"),
            ("Playoff state", "playoff_state"),
            ("API calls", "api_calls"),
            ("Player/roster hydration", "player_roster_hydration"),
        ):
            val = sections.get(key)
            if val is not None:
                st.caption(f"{label}: {val:.0f} ms")
        if phases:
            st.caption(
                "Phases: "
                + ", ".join(f"{k}={v:.0f}ms" for k, v in sorted(phases.items()))
            )


def render_fast_load_page_placeholder(st: Any, page: str, team: str) -> None:
    """Safe placeholder while Fast Load keeps heavy sections off the critical path."""
    try:
        from streamlit_app import _render_validation_mode_banner, _validation_offer_full_page  # noqa: WPS433
    except Exception:
        _render_validation_mode_banner = None  # type: ignore[misc, assignment]
        _validation_offer_full_page = None  # type: ignore[misc, assignment]

    if _render_validation_mode_banner:
        _render_validation_mode_banner()
    st.markdown(
        f"### {page}\n"
        f"**Fast load** — shell is ready for **{team}**. "
        "Change team, workspace profile, and settings now; live playoff data loads on demand."
    )
    if _validation_offer_full_page:
        _validation_offer_full_page(page, label="Load full page content")
