from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

DensityMode = Literal["compact", "cozy", "comfortable"]


@dataclass(frozen=True)
class Palette:
    bg: str = "#0b0d12"
    panel: str = "#11141b"
    panel_2: str = "#161a23"
    line: str = "#1f2430"
    line_2: str = "#262c3a"
    text: str = "#e7eaf2"
    muted: str = "#8891a4"
    dim: str = "#5b6378"
    accent: str = "#7c9cff"
    accent_2: str = "#a7b8ff"
    ok: str = "#5ad19a"
    warn: str = "#f3c969"
    bad: str = "#ef6f6f"
    chip: str = "#1a1f2a"
    
    # Pre-blended 18% tints for chip backgrounds
    chip_ok: str = "#253f3e"
    chip_warn: str = "#413d35"
    chip_bad: str = "#402d36"
    chip_accent: str = "#2b3550"
    
    # Backwards compatibility attributes
    @property
    def background(self) -> str: return self.bg
    @property
    def surface(self) -> str: return self.panel
    @property
    def surface_alt(self) -> str: return self.panel_2
    @property
    def border(self) -> str: return self.line
    @property
    def text_muted(self) -> str: return self.muted
    @property
    def success(self) -> str: return self.ok
    @property
    def warning(self) -> str: return self.warn
    @property
    def danger(self) -> str: return self.bad


@dataclass(frozen=True)
class LightPalette(Palette):
    bg: str = "#f3f4f8"
    panel: str = "#ffffff"
    panel_2: str = "#f7f8fc"
    line: str = "#e3e6ee"
    line_2: str = "#d9dde8"
    text: str = "#121521"
    muted: str = "#5b6376"
    dim: str = "#8690a4"
    chip: str = "#eef1f7"
    accent: str = "#3858d4"
    accent_2: str = "#6a86ea"
    
    # Pre-blended 18% tints for chip backgrounds
    chip_ok: str = "#d3ebe6"
    chip_warn: str = "#eee9dd"
    chip_bad: str = "#eed9de"
    chip_accent: str = "#cdd5f0"


@dataclass(frozen=True)
class Typography:
    sans: str = '"Inter", "Segoe UI", system-ui, sans-serif'
    mono: str = 'ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas'
    display: str = '"Inter", system-ui, sans-serif'
    
    xs: int = 10
    sm: int = 11
    base: int = 13
    md: int = 15
    lg: int = 22
    xl: int = 26
    hero: int = 56


@dataclass(frozen=True)
class Spacing:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class Radii:
    sm: int = 6
    md: int = 10
    lg: int = 14


@dataclass(frozen=True)
class Elevation:
    # We will use these for QGraphicsDropShadowEffect or QSS equivalents
    drawer: str = "0 8px 32px rgba(0, 0, 0, 0.4)"
    tweaks: str = "0 4px 16px rgba(0, 0, 0, 0.3)"
    toast: str = "0 4px 16px rgba(0, 0, 0, 0.3)"


@dataclass(frozen=True)
class Density:
    mode: DensityMode = "cozy"
    
    @property
    def multiplier(self) -> float:
        if self.mode == "compact":
            return 0.85
        if self.mode == "comfortable":
            return 1.15
        return 1.0


@dataclass(frozen=True)
class Motion:
    fast: str = "150ms ease"
    base: str = "200ms ease"
