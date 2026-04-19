"""Component library — Phase 3.

Contains all shared, reusable UI primitives, interactive controls, layouts,
and heavy components.
"""
from __future__ import annotations

from app.ui.components.tweaks import TweaksPanel

# Primitives
from app.ui.components.primitives import Chip, Pill, PosBadge, Avatar

# Controls
from app.ui.components.controls import PrimaryButton, GhostButton, IconButton, FilterChip, Tabs, SectionTitle

# Layout helpers
from app.ui.components.layout import Card, TwoCol, ThreeCol, FourCol, Legend

# Heavy components
from app.ui.components.drawer import DrawerPanel, AttributeRow
from app.ui.components.dropzone import Dropzone, FileRow
from app.ui.components.log_view import LogView
from app.ui.components.hero import Hero, FormDot

__all__ = [
    "TweaksPanel",
    "Chip", "Pill", "PosBadge", "Avatar",
    "PrimaryButton", "GhostButton", "IconButton", "FilterChip", "Tabs", "SectionTitle",
    "Card", "TwoCol", "ThreeCol", "FourCol", "Legend",
    "DrawerPanel", "AttributeRow",
    "Dropzone", "FileRow",
    "LogView",
    "Hero", "FormDot",
]
