"""Round-trip tests for SessionCache across all CSV kinds."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.core.constants import CSVKind
from app.import_.parsers import parser_for
from app.services.cache import SessionCache
from tests.test_parsers import ALL_KINDS, _write_csv


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_save_and_load_latest(tmp_path: Path, kind: CSVKind) -> None:
    csv_path = _write_csv(tmp_path, kind)
    parsed = parser_for(kind).parse(csv_path)

    cache = SessionCache(tmp_path / "career.sqlite")
    import_id = cache.save(parsed)
    assert import_id > 0

    loaded = cache.load_latest(kind)
    assert loaded is not None
    assert len(loaded) == parsed.rows_read

    original = parsed.df.drop(columns=[c for c in parsed.df.columns if c.endswith("_dt")])
    assert set(loaded.columns) == set(original.columns)


def test_list_snapshots_two_dates(tmp_path: Path) -> None:
    p1 = _write_csv(tmp_path, "season_overview")
    parsed1 = parser_for("season_overview").parse(p1)

    # Second snapshot with a different export_date in the filename.
    p2 = tmp_path / "SEASON_OVERVIEW_02_01_2026.csv"
    p1.rename(p2)
    parsed2 = parser_for("season_overview").parse(p2)

    cache = SessionCache(tmp_path / "career.sqlite")
    cache.save(parsed1)
    cache.save(parsed2)

    snaps = cache.list_snapshots("season_overview")
    assert date(2026, 1, 1) in snaps
    assert date(2026, 1, 2) in snaps


def test_load_snapshot_by_date(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "standings")
    parsed = parser_for("standings").parse(csv_path)
    cache = SessionCache(tmp_path / "career.sqlite")
    cache.save(parsed)

    df = cache.load_snapshot("standings", date(2026, 1, 1))
    assert df is not None
    assert len(df) == parsed.rows_read

    missing = cache.load_snapshot("standings", date(1999, 1, 1))
    assert missing is None


def test_clear_removes_data(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "season_overview")
    parsed = parser_for("season_overview").parse(csv_path)
    cache = SessionCache(tmp_path / "career.sqlite")
    cache.save(parsed)
    assert cache.load_latest("season_overview") is not None
    cache.clear()
    assert cache.load_latest("season_overview") is None
    assert cache.list_snapshots("season_overview") == []
