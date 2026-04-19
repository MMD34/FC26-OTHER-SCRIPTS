"""Smoke test for the UI shell.

Boots a ``QApplication``, routes the active palette through ``ThemeManager``,
and asserts QSS is installed. Phase 0 contract: the app compiles and loads
stylesheets without regression. Later sprints extend this file with
assertions about the new shell.
"""
from __future__ import annotations

import os
import sys

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.ui.design import ThemeManager  # noqa: E402
from app.ui.theme import LightPalette, Palette  # noqa: E402


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_theme_manager_applies_dark_qss(qapp: QApplication) -> None:
    tm = ThemeManager.instance()
    tm.apply(qapp, Palette())
    qss = qapp.styleSheet()
    assert qss, "QApplication stylesheet must not be empty after ThemeManager.apply"
    assert "QWidget" in qss
    assert isinstance(tm.current(), Palette)


def test_theme_manager_swaps_to_light(qapp: QApplication) -> None:
    tm = ThemeManager.instance()
    received: list[object] = []
    tm.theme_changed.connect(received.append)
    tm.apply(qapp, LightPalette())
    assert received, "theme_changed must emit on apply"
    assert isinstance(tm.current(), LightPalette)


def test_design_packages_importable() -> None:
    import app.ui.charts  # noqa: F401
    import app.ui.components  # noqa: F401
    import app.ui.design  # noqa: F401
    import app.ui.shell  # noqa: F401
