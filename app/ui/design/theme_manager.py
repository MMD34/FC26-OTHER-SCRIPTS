"""ThemeManager singleton.

Phase 0 scope: mirror the current ``app.ui.theme.load_qss`` behavior so there
is no visual regression, while giving later phases a single entry point to
install stylesheets and broadcast theme changes. Palette/density token
objects and the QSS builder land in Phase 1 — the manager already exposes
the signal/API they will plug into.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.ui.theme import LightPalette, Palette, load_qss


class ThemeManager(QObject):
    """Singleton installing and broadcasting the active theme."""

    theme_changed = Signal(object)

    _instance: "Optional[ThemeManager]" = None

    def __init__(self) -> None:
        super().__init__()
        self._palette: Palette = Palette()

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def current(self) -> Palette:
        return self._palette

    def apply(self, app: QApplication, palette: Palette | None = None) -> None:
        self._palette = palette or self._palette
        app.setStyleSheet(load_qss(self._palette))
        self.theme_changed.emit(self._palette)

    def set_theme(self, app: QApplication, name: str) -> None:
        palette = LightPalette() if name == "light" else Palette()
        self.apply(app, palette)


__all__ = ["ThemeManager"]
