"""Tests for the lightweight session state module.

These tests intentionally avoid any external frameworks or dependencies to
keep the sandbox self‑contained. Run them with ``python session_test.py``.
"""

from __future__ import annotations

import session_state


def test_set_and_get_session_id():
    session_state.setSessionId("initial")
    assert session_state.getSessionId() == "initial"


def test_start_new_session():
    session_state.setSessionId("old")
    first = session_state.getSessionId()
    new = session_state.startNewSession()
    assert new != first, "startNewSession should generate a new ID"
    assert session_state.getSessionId() == new


if __name__ == "__main__":  # pragma: no cover - manual test runner
    test_set_and_get_session_id()
    test_start_new_session()
    print("All session_state tests passed.")
