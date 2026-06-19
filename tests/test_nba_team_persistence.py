"""NBA workspace persistence — team change force save."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nba_persistent_state import persist_nba_team_change
from suite_user_persistence import save_user_state, state_file_path


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


class TestNbaTeamPersistence(unittest.TestCase):
    def test_persist_team_change_writes_ariel_workspace_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            ss = _FakeSessionState({})
            st = _FakeSt(ss)
            with patch("suite_workspace.DATA_DIR", data), patch(
                "suite_user_persistence.DATA_DIR", data
            ), patch("suite_workspace.resolve_workspace_id", return_value="ariel"), patch(
                "suite_cloud_state.save_cloud_full_session", return_value=True
            ):
                ok = persist_nba_team_change(st, "Boston Celtics")
                path = state_file_path("nba", "ariel")
            self.assertTrue(ok)
            self.assertTrue(path.is_file())
            blob = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(blob["state"]["favorite_team"], "Boston Celtics")

    def test_nba_activity_tags_workspace_id(self) -> None:
        with patch("suite_workspace.get_active_workspace_id", return_value="ariel"):
            with patch("suite_activity_client.record_activity") as mock_record:
                from nba_activity import log_from_page_context

                log_from_page_context("Boston Celtics", "Legacy Tracker", "Legacy Tracker")
        mock_record.assert_called_once()
        metrics = mock_record.call_args.kwargs.get("metrics") or mock_record.call_args[1].get("metrics")
        self.assertEqual(metrics.get("workspace_id"), "ariel")


if __name__ == "__main__":
    unittest.main()
