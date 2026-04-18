"""Tests for app.import_ parsers and pipeline."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.core.constants import CSVKind
from app.import_ import schema
from app.import_.discovery import detect_kind, scan
from app.import_.parsers import (
    EmptyFileError,
    MissingColumnError,
    gregorian_days_to_date,
    parser_for,
)
from app.import_.pipeline import import_folder


# --- synthetic row builders --------------------------------------------------

def _synthetic_value(col: str, dtype: str) -> object:
    if dtype == "Int64":
        if col == "playerid":
            return 12345
        if col == "is_generated":
            return 0
        return 1
    if dtype == "boolean":
        return 0
    if col == "export_date":
        return "01_01_2026"
    if col == "birthdate" or col == "playerjointeamdate":
        return None
    return "x"


def _synthetic_row(kind: CSVKind) -> dict[str, object]:
    row: dict[str, object] = {}
    for col in schema.COLUMNS[kind]:
        row[col] = _synthetic_value(col, schema.DTYPES[kind][col])
    # birthdate required for players_snapshot/wonderkids
    if kind in ("players_snapshot", "wonderkids"):
        row["birthdate"] = 739000  # ~2023-09 in proleptic Gregorian
        row["playerid"] = 12345
        row["is_generated"] = 0
        row["overallrating"] = 80
        row["potential"] = 90
        row["age"] = 19
        row["preferredposition1"] = 27
    return row


def _filename_for(kind: CSVKind) -> str:
    suffix = "01_01_2026.csv"
    if kind == "standings":
        return f"STANDINGS_TestLeague_{suffix}"
    if kind == "fixtures":
        return f"FIXTURES_TestCup_{suffix}"
    mapping = {
        "season_overview": "SEASON_OVERVIEW",
        "players_snapshot": "PLAYERS_SNAPSHOT",
        "wonderkids": "WONDERKIDS",
        "season_stats": "SEASON_STATS",
        "transfer_history": "TRANSFER_HISTORY",
    }
    return f"{mapping[kind]}_{suffix}"


def _write_csv(folder: Path, kind: CSVKind) -> Path:
    row = _synthetic_row(kind)
    df = pd.DataFrame([row], columns=list(schema.COLUMNS[kind]))
    path = folder / _filename_for(kind)
    df.to_csv(path, index=False)
    return path


# --- tests -------------------------------------------------------------------

ALL_KINDS: tuple[CSVKind, ...] = (
    "season_overview",
    "standings",
    "players_snapshot",
    "wonderkids",
    "season_stats",
    "fixtures",
    "transfer_history",
)


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_parser_round_trip(tmp_path: Path, kind: CSVKind) -> None:
    path = _write_csv(tmp_path, kind)
    parsed = parser_for(kind).parse(path)
    assert parsed.kind == kind
    assert parsed.rows_read == 1
    assert parsed.export_date == date(2026, 1, 1)
    assert parsed.source_filename == path.name
    required = schema.REQUIRED_COLUMNS[kind]
    assert required.issubset(set(parsed.df.columns))


def test_detect_kind_patterns() -> None:
    assert detect_kind("SEASON_OVERVIEW_01_01_2026.csv") == "season_overview"
    assert detect_kind("STANDINGS_Premier_League_01_01_2026.csv") == "standings"
    assert detect_kind("PLAYERS_SNAPSHOT_01_01_2026.csv") == "players_snapshot"
    assert detect_kind("WONDERKIDS_01_01_2026.csv") == "wonderkids"
    assert detect_kind("SEASON_STATS_01_01_2026.csv") == "season_stats"
    assert detect_kind("FIXTURES_UCL_01_01_2026.csv") == "fixtures"
    assert detect_kind("TRANSFER_HISTORY_01_01_2026.csv") == "transfer_history"
    assert detect_kind("random.csv") is None


def test_missing_required_column(tmp_path: Path) -> None:
    # Build a season_overview CSV without `points`.
    cols = [c for c in schema.SEASON_OVERVIEW_COLUMNS if c != "points"]
    row = {c: _synthetic_value(c, schema.DTYPES["season_overview"][c]) for c in cols}
    df = pd.DataFrame([row], columns=cols)
    path = tmp_path / "SEASON_OVERVIEW_01_01_2026.csv"
    df.to_csv(path, index=False)
    with pytest.raises(MissingColumnError) as exc:
        parser_for("season_overview").parse(path)
    assert "points" in exc.value.columns


def test_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "SEASON_OVERVIEW_01_01_2026.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(EmptyFileError):
        parser_for("season_overview").parse(path)


def test_gregorian_days_helper() -> None:
    assert gregorian_days_to_date(1) == date(1, 1, 1)
    assert gregorian_days_to_date(None) is None
    assert gregorian_days_to_date(0) is None
    assert gregorian_days_to_date(-5) is None


def test_import_folder_all_kinds(tmp_path: Path) -> None:
    for kind in ALL_KINDS:
        _write_csv(tmp_path, kind)
    report = import_folder(tmp_path)
    assert report.ok_count == len(ALL_KINDS)
    assert report.error_count == 0
    for f in report.files:
        assert f.status == "ok"


def test_scan_ignores_unknown(tmp_path: Path) -> None:
    (tmp_path / "unknown.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    _write_csv(tmp_path, "season_overview")
    detected = scan(tmp_path)
    assert len(detected) == 1
    assert detected[0].kind == "season_overview"
    assert detected[0].export_date == date(2026, 1, 1)
