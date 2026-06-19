"""NBA workspace profile isolation — Daniel vs Ariel state separation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nba_persistent_state import apply_nba_disk_state, build_nba_disk_state, prepare_nba_workspace
from suite_user_persistence import save_user_state, state_file_path
from suite_workspace import scoped_cloud_app_id


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


class TestNbaWorkspaceIsolation(unittest.TestCase):
    def test_scoped_cloud_app_id(self) -> None:
        self.assertEqual(scoped_cloud_app_id("nba", "daniel"), "nba")
        self.assertEqual(scoped_cloud_app_id("nba", "ariel"), "nba__ariel")

    def test_daniel_and_ariel_disk_paths_differ(self) -> None:
        daniel = state_file_path("nba", "daniel")
        ariel = state_file_path("nba", "ariel")
        self.assertNotEqual(daniel, ariel)
        self.assertIn("workspaces", str(daniel))
        self.assertIn("ariel", str(ariel))

    def test_separate_teams_persist_per_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            with patch("suite_workspace.DATA_DIR", data), patch("suite_user_persistence.DATA_DIR", data):
                save_user_state(
                    "nba",
                    {
                        "favorite_team": "New York Knicks",
                        "page_label_last": "Legacy Tracker",
                        "legacy_tracker_player": "Jalen Brunson",
                    },
                    workspace_id="daniel",
                )
                save_user_state(
                    "nba",
                    {
                        "favorite_team": "Boston Celtics",
                        "page_label_last": "Playoff Bracket",
                        "legacy_tracker_player": "Jayson Tatum",
                    },
                    workspace_id="ariel",
                )
                daniel_blob = json.loads(state_file_path("nba", "daniel").read_text(encoding="utf-8"))
                ariel_blob = json.loads(state_file_path("nba", "ariel").read_text(encoding="utf-8"))
                self.assertEqual(daniel_blob["state"]["favorite_team"], "New York Knicks")
                self.assertEqual(ariel_blob["state"]["favorite_team"], "Boston Celtics")
                self.assertEqual(daniel_blob["state"]["legacy_tracker_player"], "Jalen Brunson")
                self.assertEqual(ariel_blob["state"]["legacy_tracker_player"], "Jayson Tatum")

    def test_prepare_nba_workspace_applies_disk_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            with patch("suite_workspace.DATA_DIR", data), patch("suite_user_persistence.DATA_DIR", data):
                save_user_state(
                    "nba",
                    build_nba_disk_state(
                        _FakeSt(
                            _FakeSessionState(
                                {
                                    "favorite_team_sidebar": "New York Knicks",
                                    "_nba_persist_team": "New York Knicks",
                                    "page_label_last": "Live Game Center",
                                }
                            )
                        ),
                    ),
                    workspace_id="daniel",
                )
                ss = _FakeSessionState({})
                st = _FakeSt(ss)
                with patch("suite_workspace.resolve_workspace_id", return_value="daniel"):
                    applied = prepare_nba_workspace(st)
                self.assertTrue(applied)
                self.assertEqual(ss.get("favorite_team_sidebar"), "New York Knicks")
                self.assertEqual(ss.get("nba_choose_page"), "Live Game Center")


if __name__ == "__main__":
    unittest.main()
