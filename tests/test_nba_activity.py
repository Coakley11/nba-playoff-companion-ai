"""NBA activity logging — workspace-scoped events for Command Center."""

from __future__ import annotations

import unittest
from unittest.mock import patch


class TestNbaActivityLogging(unittest.TestCase):
    def test_log_team_selected_tags_workspace(self) -> None:
        with patch("suite_workspace.get_active_workspace_id", return_value="ariel"):
            with patch("suite_activity_client.record_activity") as mock_record:
                from nba_activity import log_team_selected

                log_team_selected("Boston Celtics", page="Home Dashboard")
        mock_record.assert_called_once()
        self.assertEqual(mock_record.call_args.args[1], "team_selected")
        metrics = mock_record.call_args.kwargs.get("metrics") or mock_record.call_args[1].get("metrics")
        self.assertEqual(metrics.get("workspace_id"), "ariel")
        self.assertEqual(metrics.get("team"), "Boston Celtics")

    def test_log_legacy_tracker_player(self) -> None:
        with patch("suite_workspace.get_active_workspace_id", return_value="ariel"):
            with patch("suite_activity_client.record_activity") as mock_record:
                from nba_activity import log_legacy_tracker_player

                log_legacy_tracker_player("Boston Celtics", "Jayson Tatum")
        mock_record.assert_called_once()
        self.assertEqual(mock_record.call_args.args[1], "legacy_tracker_focus")
        metrics = mock_record.call_args.kwargs.get("metrics") or mock_record.call_args[1].get("metrics")
        self.assertEqual(metrics.get("player"), "Jayson Tatum")

    def test_home_dashboard_logs_team_session(self) -> None:
        with patch("suite_workspace.get_active_workspace_id", return_value="ariel"):
            with patch("suite_activity_client.record_activity") as mock_record:
                from nba_activity import log_from_page_context

                log_from_page_context("Boston Celtics", "Home Dashboard", "🏠 Home Dashboard")
        mock_record.assert_called_once()
        self.assertEqual(mock_record.call_args.args[1], "team_session")


if __name__ == "__main__":
    unittest.main()
