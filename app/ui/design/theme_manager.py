"""ThemeManager singleton.

Phase 0 scope: mirror the current ``app.ui.theme.load_qss`` behavior so there
is no visual regression, while giving later phases a single entry point to
install stylesheets and broadcast theme changes. Palette/density token
objects and the QSS builder land in Phase 1 — the manager already exposes
the signal/API they will plug into.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QApplication, QWidget

from app.ui.design.tokens import Palette, LightPalette, Density, Typography
from app.ui.design.qss import build_qss


class ThemeManager(QObject):
    """Singleton installing and broadcasting the active theme."""

    theme_changed = Signal(object)
    density_changed = Signal(object)

    _instance: "Optional[ThemeManager]" = None

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("FC26Analytics", "Theme")
        self._palette: Palette = Palette()
        self._density: Density = Density()
        self._typography: Typography = Typography()
        
        self.load_preferences()

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def current(self) -> Palette:
        return self._palette

    @property
    def density(self) -> Density:
        return self._density

    @property
    def typography(self) -> Typography:
        return self._typography

    def load_preferences(self) -> None:
        is_light = self._settings.value("is_light", False, type=bool)
        density_mode = self._settings.value("density_mode", "cozy", type=str)
        
        self._palette = LightPalette() if is_light else Palette()
        self._density = Density(mode=density_mode) # type: ignore

    def apply(self, app: QApplication, palette: Palette | None = None) -> None:
        self._palette = palette or self._palette
        qss = build_qss(self._palette, self._density, self._typography)
        app.setStyleSheet(qss)
        
        # Walk all top-level widgets to force polish update
        for widget in app.topLevelWidgets():
            self._repolish_recursive(widget)
            
        self.theme_changed.emit(self._palette)

    def set_theme(self, app: QApplication, name: str) -> None:
        is_light = (name == "light")
        self._settings.setValue("is_light", is_light)
        palette = LightPalette() if is_light else Palette()
        self.apply(app, palette)
        
    def set_density(self, app: QApplication, mode: str) -> None:
        self._settings.setValue("density_mode", mode)
        self._density = Density(mode=mode) # type: ignore
        self.apply(app, self._palette)
        self.density_changed.emit(self._density)

    def _repolish_recursive(self, widget: QWidget) -> None:
        style = widget.style()
        if style:
            style.unpolish(widget)
            style.polish(widget)
        for child in widget.children():
            if isinstance(child, QWidget):
                self._repolish_recursive(child)


__all__ = ["ThemeManager"]
