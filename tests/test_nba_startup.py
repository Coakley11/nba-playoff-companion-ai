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


if __name__ == "__main__":
    unittest.main()
