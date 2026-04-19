"""CSV parsers per kind.

Fault-tolerant: reads every column as string first, then coerces int/bool
columns defensively (non-numeric cells like ``"TBD"`` or ``" "`` become NaN).
Missing optional columns and partial data never abort the parse — they emit
warnings so the pipeline can classify the file as ``partial``.
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

# Cell values we treat as "no data" across every column.
_NA_SENTINELS: tuple[str, ...] = ("", " ", "nil", "TBD", "tbd", "N/A", "n/a", "None", "none", "-")


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
    """Convert FC26 Gregorian-day integer to a :class:`datetime.date`."""
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
        raise SchemaMismatchError(
            "season_overview", f"filename does not contain DD_MM_YYYY: {filename}"
        )
    return date(int(m["year"]), int(m["month"]), int(m["day"]))


def _coerce_int(series: pd.Series) -> tuple[pd.Series, int]:
    """Coerce a string series to nullable Int64; return (series, null_count).

    ``null_count`` counts values that became null (either recognized sentinels
    like ``TBD`` / ``" "`` or otherwise non-numeric text). Empty original cells
    don't count — we only report what was "something, but not a number".
    """
    stripped = series.astype("string").str.strip()
    non_empty_mask = stripped.notna() & (stripped != "")
    cleaned = stripped.mask(stripped.isin(_NA_SENTINELS))
    numeric = pd.to_numeric(cleaned, errors="coerce")
    nulled = int((non_empty_mask & numeric.isna()).sum())
    return numeric.astype("Int64"), nulled


def _coerce_bool(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip().str.lower()
    cleaned = cleaned.mask(cleaned.isin([s.lower() for s in _NA_SENTINELS]))
    truthy = {"true", "1", "yes", "y", "t"}
    falsy = {"false", "0", "no", "n", "f"}
    return cleaned.map(
        lambda v: True if v in truthy else (False if v in falsy else pd.NA)
    ).astype("boolean")


def _coerce_str(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    return cleaned.mask(cleaned.isin(_NA_SENTINELS))


# --- base parser -------------------------------------------------------------

class BaseParser:
    kind: CSVKind

    def parse(self, path: Path) -> ParsedCSV:
        if not path.exists() or path.stat().st_size == 0:
            raise EmptyFileError(path)

        try:
            df = pd.read_csv(
                path,
                dtype="string",
                keep_default_na=False,
                na_values=[],
                encoding_errors="replace",
            )
        except pd.errors.EmptyDataError as e:
            raise EmptyFileError(path) from e
        except UnicodeDecodeError as e:
            raise SchemaMismatchError(self.kind, f"encoding error: {e}") from e

        rows_read = len(df)
        warnings: list[str] = []

        required = _schema.REQUIRED_COLUMNS[self.kind]
        missing_required = required - set(df.columns)
        if missing_required:
            raise MissingColumnError(self.kind, frozenset(missing_required))

        expected = set(_schema.COLUMNS[self.kind])
        missing_optional = expected - set(df.columns) - required
        if missing_optional:
            warnings.append(
                f"missing optional columns: {sorted(missing_optional)}"
            )
        extra = set(df.columns) - expected
        if extra:
            warnings.append(f"unknown columns ignored: {sorted(extra)}")

        dtypes = _schema.DTYPES[self.kind]
        total_invalid = 0
        for col in df.columns:
            target = dtypes.get(col, "string")
            try:
                if target == "Int64":
                    df[col], nulled = _coerce_int(df[col])
                    if nulled:
                        total_invalid += nulled
                        warnings.append(
                            f"{col}: {nulled} non-numeric value(s) (e.g. 'TBD') "
                            f"coerced to null"
                        )
                elif target == "boolean":
                    df[col] = _coerce_bool(df[col])
                else:
                    df[col] = _coerce_str(df[col])
            except Exception as exc:  # defensive: isolate per-column failures
                _log.warning("coercion failed on %s.%s: %s", self.kind, col, exc)
                warnings.append(f"{col}: coercion failed ({exc!r}); kept as text")

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
