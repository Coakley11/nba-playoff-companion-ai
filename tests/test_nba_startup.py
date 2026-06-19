"""NBA startup diagnostics — Daniel dev mode only."""

from __future__ import annotations

import unittest
from unittest.mock import patch


class _FakeSessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class _FakeSt:
    def __init__(self, state: _FakeSessionState) -> None:
        self.session_state = state


class TestNbaStartupDiagnostics(unittest.TestCase):
    def test_ariel_does_not_record_timing(self) -> None:
        ss = _FakeSessionState({})
        st = _FakeSt(ss)
        with patch("suite_workspace.can_show_developer_tools", return_value=False):
            from nba_startup import mark_startup_phase

            mark_startup_phase(st, "init", 0.0)
        self.assertNotIn("_nba_startup_timing", ss)

    def test_defer_when_fast_load(self) -> None:
        ss = _FakeSessionState({"QA_MODE": True})
        st = _FakeSt(ss)
        from nba_startup import should_defer_heavy_startup

        self.assertTrue(should_defer_heavy_startup(st))

    def test_default_fast_load_for_new_session(self) -> None:
        ss = _FakeSessionState({})
        st = _FakeSt(ss)
        from nba_startup import ensure_fast_load_defaults

        ensure_fast_load_defaults(st)
        self.assertTrue(ss.get("QA_MODE"))

    def test_resolve_profile_playoff_state_validation(self) -> None:
        from nba_startup import resolve_profile_playoff_state

        stt = {"team_status": {}}
        active = resolve_profile_playoff_state(
            validation_mode=True,
            page="Home Dashboard",
            validation_stt=stt,
            lgc_stt=None,
        )
        self.assertIs(active, stt)

    def test_resolve_profile_playoff_state_lgc_fallback(self) -> None:
        from nba_startup import resolve_profile_playoff_state

        lgc = {"first": {}}
        active = resolve_profile_playoff_state(
            validation_mode=False,
            page="Live Game Center",
            validation_stt=None,
            lgc_stt=lgc,
        )
        self.assertIs(active, lgc)

    def test_resolve_profile_playoff_state_normal_page(self) -> None:
        from nba_startup import resolve_profile_playoff_state

        active = resolve_profile_playoff_state(
            validation_mode=False,
            page="Home Dashboard",
            validation_stt={"x": 1},
            lgc_stt={"y": 2},
        )
        self.assertIsNone(active)

    def test_main_profile_stt_path_no_name_error(self) -> None:
        """Regression: Fast Load + validation must not reference undefined _val_stt."""
        from nba_startup import resolve_profile_playoff_state

        validation_stt = {"team_status": {"Boston Celtics": {"status": "active"}}}
        active = resolve_profile_playoff_state(
            validation_mode=True,
            page="Legacy Tracker",
            validation_stt=validation_stt,
            lgc_stt=None,
        )
        self.assertIs(active, validation_stt)


if __name__ == "__main__":
    unittest.main()
