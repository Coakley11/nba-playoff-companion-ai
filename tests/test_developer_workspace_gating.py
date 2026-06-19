"""Regression: NBA developer sidebar debug workspace gate."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from suite_workspace import can_show_developer_tools, set_active_workspace_id


class _FakeSt:
    def __init__(self, workspace: str, *, dev_query: bool = False) -> None:
        self.session_state: dict = {}
        self.query_params = {"dev": "1"} if dev_query else {}
        set_active_workspace_id(self, workspace)  # type: ignore[arg-type]


class TestDeveloperWorkspaceGating(unittest.TestCase):
    def test_show_sidebar_debug_ariel_blocked(self) -> None:
        import portfolio_polish as pp

        st = _FakeSt("ariel", dev_query=True)
        self.assertFalse(pp.show_sidebar_debug(st))  # type: ignore[arg-type]

    def test_show_sidebar_debug_daniel_dev(self) -> None:
        import portfolio_polish as pp

        st = _FakeSt("daniel", dev_query=True)
        self.assertTrue(pp.show_sidebar_debug(st))  # type: ignore[arg-type]

    def test_dev_lab_visible_ariel_blocked(self) -> None:
        st = _FakeSt("ariel", dev_query=True)
        st.session_state["dev_lab_enabled"] = True
        self.assertFalse(can_show_developer_tools(st=st))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
