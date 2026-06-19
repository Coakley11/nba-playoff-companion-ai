"""NBA startup timing diagnostics — Daniel developer mode only."""

from __future__ import annotations

import time as pytime
from typing import Any

_STARTUP_KEY = "_nba_startup_timing"
_DEFER_KEY = "_nba_deferred_workspace_sync"


def should_defer_heavy_startup(st: Any) -> bool:
    """Fast Load / Lite Mode: render shell first, sync cloud later."""
    ss = st.session_state
    if ss.get("ULTRA_FAST_VALIDATION_MODE"):
        return True
    if ss.get("QA_MODE"):
        return True
    return False


def mark_deferred_workspace_sync(st: Any) -> None:
    st.session_state[_DEFER_KEY] = True


def pop_deferred_workspace_sync(st: Any) -> bool:
    return bool(st.session_state.pop(_DEFER_KEY, False))


def mark_startup_phase(st: Any, phase: str, boot_t0: float) -> None:
    """Record elapsed ms from boot to named phase (Daniel dev diagnostics only)."""
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
    """Sidebar expander with startup breakdown — hidden from Ariel/non-dev profiles."""
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

    shell_ms = phases.get("sidebar") or phases.get("header")
    restore_ms = sections.get("restore") or phases.get("post_restore")
    playoff_ms = sections.get("playoff_state")
    api_ms = sections.get("api_calls")
    hydration_ms = sections.get("player_roster_hydration")

    with st.sidebar.expander("Startup timing (dev)", expanded=False):
        st.caption(f"**Total startup:** {total_ms:.0f} ms")
        if shell_ms is not None:
            st.caption(f"Shell (header/sidebar): {shell_ms:.0f} ms")
        if restore_ms is not None:
            st.caption(f"Restore path: {restore_ms:.0f} ms")
        if playoff_ms is not None:
            st.caption(f"Playoff state: {playoff_ms:.0f} ms")
        if api_ms is not None:
            st.caption(f"API calls: {api_ms:.0f} ms")
        if hydration_ms is not None:
            st.caption(f"Player/roster hydration: {hydration_ms:.0f} ms")
        if phases:
            st.caption("Phases: " + ", ".join(f"{k}={v:.0f}ms" for k, v in sorted(phases.items())))
