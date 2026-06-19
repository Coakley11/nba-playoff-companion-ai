"""Team selector persistence — no snap-back on reruns."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nba_persistent_state import (
    NBA_TEAM_SELECT_KEY,
    apply_nba_disk_state,
    build_nba_disk_state,
    clear_nba_startup_restore_flags,
    default_team_for_workspace,
    init_nba_team_selector_state,
    persist_nba_team_change,
    restore_nba_disk_shell,
)
from suite_user_persistence import state_file_path


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


TEAMS = sorted(
    [
        "Atlanta Hawks",
        "Boston Celtics",
        "New York Knicks",
    ]
)


class TestNbaTeamSelectorPersistence(unittest.TestCase):
    def test_default_team_ariel_is_celtics_not_hawks(self) -> None:
        picked = default_team_for_workspace(TEAMS, workspace_id="ariel")
        self.assertEqual(picked, "Boston Celtics")

    def test_default_team_daniel_is_knicks(self) -> None:
        picked = default_team_for_workspace(TEAMS, workspace_id="daniel")
        self.assertEqual(picked, "New York Knicks")

    def test_disk_shell_restore_runs_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            ss = _FakeSessionState({})
            st = _FakeSt(ss)
            with patch("suite_workspace.DATA_DIR", data), patch(
                "suite_user_persistence.DATA_DIR", data
            ), patch("suite_workspace.resolve_workspace_id", return_value="daniel"):
                save_path = state_file_path("nba", "daniel")
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "saved_at": "2026-06-19T12:00:00+00:00",
                            "state": {
                                "favorite_team": "Atlanta Hawks",
                                "favorite_team_sidebar": "Atlanta Hawks",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                first = restore_nba_disk_shell(st)
                ss[NBA_TEAM_SELECT_KEY] = "New York Knicks"
                ss["favorite_team"] = "New York Knicks"
                second = restore_nba_disk_shell(st)
            self.assertTrue(first)
            self.assertTrue(second)
            self.assertEqual(ss[NBA_TEAM_SELECT_KEY], "New York Knicks")

    def test_init_team_selector_does_not_overwrite_user_pick(self) -> None:
        ss = _FakeSessionState(
            {
                NBA_TEAM_SELECT_KEY: "New York Knicks",
                "_nba_team_widget_init": True,
                "_nba_restore_team": "Atlanta Hawks",
            }
        )
        st = _FakeSt(ss)
        init_nba_team_selector_state(st, TEAMS)
        self.assertEqual(ss[NBA_TEAM_SELECT_KEY], "New York Knicks")

    def test_team_change_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            ss = _FakeSessionState({NBA_TEAM_SELECT_KEY: "Atlanta Hawks", "favorite_team": "Atlanta Hawks"})
            st = _FakeSt(ss)
            init_nba_team_selector_state(st, TEAMS)
            ss[NBA_TEAM_SELECT_KEY] = "New York Knicks"
            ss["favorite_team"] = "New York Knicks"
            with patch("suite_workspace.DATA_DIR", data), patch(
                "suite_user_persistence.DATA_DIR", data
            ), patch("suite_workspace.resolve_workspace_id", return_value="daniel"), patch(
                "suite_cloud_state.save_cloud_full_session", return_value=True
            ), patch("nba_activity.log_team_selected"):
                ok = persist_nba_team_change(st, "New York Knicks")
                path = state_file_path("nba", "daniel")
            self.assertTrue(ok)
            blob = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(blob["state"]["favorite_team"], "New York Knicks")
            ss2 = _FakeSessionState({})
            st2 = _FakeSt(ss2)
            restore_nba_disk_shell(st2)
            init_nba_team_selector_state(st2, TEAMS)
            self.assertEqual(ss2[NBA_TEAM_SELECT_KEY], "New York Knicks")

    def test_workspace_switch_clears_team_init(self) -> None:
        ss = _FakeSessionState({NBA_TEAM_SELECT_KEY: "Boston Celtics", "_nba_team_widget_init": True})
        st = _FakeSt(ss)
        clear_nba_startup_restore_flags(st)
        self.assertNotIn("_nba_team_widget_init", ss)
        self.assertNotIn(NBA_TEAM_SELECT_KEY, ss)


if __name__ == "__main__":
    unittest.main()
