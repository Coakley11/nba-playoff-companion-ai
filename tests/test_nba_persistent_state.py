"""NBA persistence — sub-page state and dynamic LGC/matchup keys."""

from __future__ import annotations

import copy
import unittest

from nba_persistent_state import (
    _collect_nba_dynamic_state,
    apply_nba_disk_state,
    apply_nba_session_defaults,
    build_nba_disk_state,
)


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


class TestNbaPersistentState(unittest.TestCase):
    def test_legacy_tracker_player_round_trip(self) -> None:
        ss = _FakeSessionState(
            {
                "favorite_team_sidebar": "Boston Celtics",
                "page_label_last": "Legacy Tracker",
                "legacy_tracker_player": "Jayson Tatum",
                "_nba_persist_team": "Boston Celtics",
            }
        )
        blob = build_nba_disk_state(_FakeSt(ss))
        self.assertEqual(blob["legacy_tracker_player"], "Jayson Tatum")

        out = _FakeSessionState({})
        apply_nba_disk_state(_FakeSt(out), copy.deepcopy(blob))
        self.assertEqual(out["legacy_tracker_player"], "Jayson Tatum")
        self.assertEqual(out["favorite_team_sidebar"], "Boston Celtics")

    def test_dynamic_lgc_and_matchup_keys(self) -> None:
        ss = _FakeSessionState(
            {
                "manual_live_home_score": 98,
                "live_gc_swing_New York Knicks": 6,
                "load_matchup_intel_New York Knicks": True,
                "live_gc_last_known_New York Knicks": {"parsed": {"home_score": 88}},
            }
        )
        dynamic = _collect_nba_dynamic_state(ss)
        self.assertIn("live_gc_swing_New York Knicks", dynamic)
        self.assertIn("load_matchup_intel_New York Knicks", dynamic)

        blob = build_nba_disk_state(_FakeSt(ss))
        self.assertIn("_nba_dynamic", blob)

        out = _FakeSessionState({})
        apply_nba_disk_state(_FakeSt(out), copy.deepcopy(blob))
        self.assertEqual(out["manual_live_home_score"], 98)
        self.assertTrue(out["load_matchup_intel_New York Knicks"])

    def test_reset_clears_dynamic_keys(self) -> None:
        ss = _FakeSessionState(
            {
                "legacy_tracker_player": "Jalen Brunson",
                "live_gc_swing_New York Knicks": 3,
            }
        )
        apply_nba_session_defaults(_FakeSt(ss))
        self.assertNotIn("legacy_tracker_player", ss)
        self.assertNotIn("live_gc_swing_New York Knicks", ss)


if __name__ == "__main__":
    unittest.main()
