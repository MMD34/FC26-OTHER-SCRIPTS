"""Discover and classify CSV files dropped on Desktop."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.core.constants import CSVKind

_DATE_RE = r"(?P<day>\d{2})_(?P<month>\d{2})_(?P<year>\d{4})"

# Order matters: WONDERKIDS before PLAYERS_SNAPSHOT has no effect (distinct prefixes)
# but we keep wonderkids explicit. Patterns anchored with $ on the extension.
_PATTERNS: tuple[tuple[CSVKind, re.Pattern[str]], ...] = (
    ("season_overview", re.compile(rf"^SEASON_OVERVIEW_{_DATE_RE}\.csv$", re.IGNORECASE)),
    ("standings", re.compile(rf"^STANDINGS_(?P<league>.+)_{_DATE_RE}\.csv$", re.IGNORECASE)),
    ("wonderkids", re.compile(rf"^WONDERKIDS_{_DATE_RE}\.csv$", re.IGNORECASE)),
    ("players_snapshot", re.compile(rf"^PLAYERS_SNAPSHOT_{_DATE_RE}\.csv$", re.IGNORECASE)),
    ("season_stats", re.compile(rf"^SEASON_STATS_{_DATE_RE}\.csv$", re.IGNORECASE)),
    ("fixtures", re.compile(rf"^FIXTURES_(?P<comp>.+)_{_DATE_RE}\.csv$", re.IGNORECASE)),
    ("transfer_history", re.compile(rf"^TRANSFER_HISTORY_{_DATE_RE}\.csv$", re.IGNORECASE)),
)


@dataclass(frozen=True)
class DetectedFile:
    path: Path
    kind: CSVKind
    export_date: date


def _match(filename: str) -> tuple[CSVKind, re.Match[str]] | None:
    for kind, pattern in _PATTERNS:
        m = pattern.match(filename)
        if m:
            return kind, m
    return None


def detect_kind(filename: str) -> CSVKind | None:
    matched = _match(filename)
    return matched[0] if matched else None


def scan(folder: Path) -> list[DetectedFile]:
    results: list[DetectedFile] = []
    if not folder.exists():
        return results
    for entry in sorted(folder.iterdir()):
        if not entry.is_file():
            continue
        matched = _match(entry.name)
        if matched is None:
            continue
        kind, m = matched
        try:
            d = date(int(m["year"]), int(m["month"]), int(m["day"]))
        except ValueError:
            continue
        results.append(DetectedFile(path=entry, kind=kind, export_date=d))
    return results
