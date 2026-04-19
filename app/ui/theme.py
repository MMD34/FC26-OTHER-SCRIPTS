"""UI theme tokens and QSS loader.

Defines the design tokens (palette, spacing, radii, typography) used across
the app and produces the QSS string consumed by QApplication.setStyleSheet.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field

from app.ui.design.tokens import Palette, LightPalette, Spacing, Radii, Typography as FontTokens, Density
from app.ui.design.qss import build_qss


@dataclass(frozen=True)
class Theme:
    palette: Palette = field(default_factory=Palette)
    spacing: Spacing = field(default_factory=Spacing)
    radii: Radii = field(default_factory=Radii)
    fonts: FontTokens = field(default_factory=FontTokens)


def load_qss(palette: Palette | None = None) -> str:
    """Render the global stylesheet using the supplied palette tokens."""
    return build_qss(palette or Palette(), Density(), FontTokens())


def load_qss_from_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


__all__ = [
    "Palette",
    "LightPalette",
    "Spacing",
    "Radii",
    "FontTokens",
    "Theme",
    "load_qss",
    "load_qss_from_file",
]
