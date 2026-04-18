"""CSV parsers per kind.

Each subclass reads one CSV kind into a dataframe with explicit dtypes, validates
required columns, and returns a :class:`ParsedCSV`. Errors are raised as the
typed exceptions defined here and are caught by the pipeline — parsers
themselves never swallow errors.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from app.core.constants import CSVKind
from app.core.logging_setup import get_logger
from app.import_ import schema as _schema

_log = get_logger(__name__)

_FILENAME_DATE_RE = re.compile(r"(?P<day>\d{2})_(?P<month>\d{2})_(?P<year>\d{4})\.csv$", re.IGNORECASE)


# --- exceptions --------------------------------------------------------------

class ParserError(Exception):
    """Base for typed parser failures."""


class MissingColumnError(ParserError):
    def __init__(self, kind: CSVKind, columns: frozenset[str]):
        self.kind = kind
        self.columns = columns
        super().__init__(f"{kind}: missing required columns {sorted(columns)}")


class SchemaMismatchError(ParserError):
    def __init__(self, kind: CSVKind, detail: str):
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: schema mismatch — {detail}")


class EmptyFileError(ParserError):
    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"empty CSV: {path}")


# --- result type -------------------------------------------------------------

@dataclass
class ParsedCSV:
    df: pd.DataFrame
    kind: CSVKind
    export_date: date
    source_filename: str
    rows_read: int
    rows_dropped: int = 0
    warnings: list[str] = field(default_factory=list)


# --- helpers -----------------------------------------------------------------

def gregorian_days_to_date(days: int | None) -> date | None:
    """Convert FC26 Gregorian-day integer to a :class:`datetime.date`.

    ASSUMPTION: the FC26 epoch follows the proleptic Gregorian calendar with
    day 1 == 0001-01-01 (matches Python's ``date.fromordinal``). If a later
    probe contradicts this, recalibrate here.
    """
    if days is None:
        return None
    try:
        n = int(days)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    try:
        return date.fromordinal(n)
    except (ValueError, OverflowError):
        return None


def _extract_export_date(filename: str) -> date:
    m = _FILENAME_DATE_RE.search(filename)
    if not m:
        raise SchemaMismatchError(  # type: ignore[call-arg]
            "season_overview", f"filename does not contain DD_MM_YYYY: {filename}"
        )
    return date(int(m["year"]), int(m["month"]), int(m["day"]))


# --- base parser -------------------------------------------------------------

class BaseParser:
    kind: CSVKind

    def parse(self, path: Path) -> ParsedCSV:
        if not path.exists() or path.stat().st_size == 0:
            raise EmptyFileError(path)

        dtype = _schema.DTYPES[self.kind]
        try:
            df = pd.read_csv(
                path,
                dtype=dtype,
                na_values=["", "nil"],
                keep_default_na=True,
            )
        except pd.errors.EmptyDataError as e:
            raise EmptyFileError(path) from e

        rows_read = len(df)
        warnings: list[str] = []

        required = _schema.REQUIRED_COLUMNS[self.kind]
        missing = required - set(df.columns)
        if missing:
            raise MissingColumnError(self.kind, frozenset(missing))

        df = self._coerce_dates(df, warnings)
        df = self._post_process(df, warnings)

        export_date = _extract_export_date(path.name)

        return ParsedCSV(
            df=df,
            kind=self.kind,
            export_date=export_date,
            source_filename=path.name,
            rows_read=rows_read,
            rows_dropped=rows_read - len(df),
            warnings=warnings,
        )

    def _coerce_dates(self, df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
        for col in _schema.DATE_COLUMNS.get(self.kind, ()):
            if col not in df.columns:
                continue
            series = df[col]
            df[f"{col}_dt"] = series.map(
                lambda v: gregorian_days_to_date(v) if pd.notna(v) else None
            )
        return df

    def _post_process(self, df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
        return df


# --- concrete parsers --------------------------------------------------------

class SeasonOverviewParser(BaseParser):
    kind: CSVKind = "season_overview"


class StandingsParser(BaseParser):
    kind: CSVKind = "standings"


class PlayersSnapshotParser(BaseParser):
    kind: CSVKind = "players_snapshot"


class WonderkidsParser(BaseParser):
    kind: CSVKind = "wonderkids"


class SeasonStatsParser(BaseParser):
    kind: CSVKind = "season_stats"


class FixturesParser(BaseParser):
    kind: CSVKind = "fixtures"


class TransferHistoryParser(BaseParser):
    kind: CSVKind = "transfer_history"


PARSERS: dict[CSVKind, type[BaseParser]] = {
    "season_overview": SeasonOverviewParser,
    "standings": StandingsParser,
    "players_snapshot": PlayersSnapshotParser,
    "wonderkids": WonderkidsParser,
    "season_stats": SeasonStatsParser,
    "fixtures": FixturesParser,
    "transfer_history": TransferHistoryParser,
}


def parser_for(kind: CSVKind) -> BaseParser:
    return PARSERS[kind]()
