"""Verify Phase-0 Sprint 0.3 page state contract.

Every page exposes ``set_state`` via ``PageBase``; invalid states raise; the
``state_changed`` signal fires on transition. No visual assertions — the
default ``_render_state`` is a no-op so the current widget stays visible.
"""
from __future__ import annotations

import sys

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.ui.pages._base import PageBase  # noqa: E402


class _StubContext:
    pass


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_set_state_transitions(qapp: QApplication) -> None:
    page = PageBase.__new__(PageBase)
    PageBase.__init__(page, _StubContext())
    assert page.state == "ready"

    received: list[str] = []
    page.state_changed.connect(received.append)

    page.set_state("loading")
    assert page.state == "loading"
    page.set_state("empty")
    page.set_state("error", error="boom")
    assert page.state_error == "boom"
    page.set_state("ready")

    assert received == ["loading", "empty", "error", "ready"]


def test_invalid_state_raises(qapp: QApplication) -> None:
    page = PageBase.__new__(PageBase)
    PageBase.__init__(page, _StubContext())
    with pytest.raises(ValueError):
        page.set_state("bogus")  # type: ignore[arg-type]
