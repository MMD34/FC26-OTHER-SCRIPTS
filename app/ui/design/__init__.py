"""Design-system layer: tokens, QSS builder, ThemeManager.

Populated by Phase 1 sprints. Phase 0 ships only the ThemeManager shim so
later sprints have a home to land in without introducing import errors.
"""
from __future__ import annotations

from app.ui.design.theme_manager import ThemeManager
from app.ui.design.tokens import Palette, LightPalette, Spacing, Radii, Typography, Elevation, Density
from app.ui.design.qss import build_qss

__all__ = [
    "ThemeManager",
    "Palette",
    "LightPalette",
    "Spacing",
    "Radii",
    "Typography",
    "Elevation",
    "Density",
    "build_qss"
]
