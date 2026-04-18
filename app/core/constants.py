"""Shared constants: thresholds and CSV kinds."""
from __future__ import annotations

from typing import Literal, get_args

GENERATED_PLAYER_THRESHOLD: int = 460000
DEFAULT_WONDERKID_POTENTIAL: int = 85
DEFAULT_WONDERKID_MAX_AGE: int = 21

CSVKind = Literal[
    "season_overview",
    "standings",
    "players_snapshot",
    "wonderkids",
    "season_stats",
    "fixtures",
    "transfer_history",
]

CSV_KINDS: tuple[CSVKind, ...] = get_args(CSVKind)
