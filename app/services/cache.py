"""SQLite-backed session cache for parsed CSV imports.

Layout
------
``imports`` — one row per successful parse.
``rows_<kind>`` — the raw CSV rows for that kind with an ``import_id`` FK.

Derived ``<col>_dt`` date columns produced by the parser are dropped before
persistence (they are re-derivable from the integer Gregorian-day column).
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from app.core.constants import CSVKind
from app.import_.parsers import ParsedCSV


_IMPORTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    export_date TEXT NOT NULL,
    source_filename TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL
)
"""


def _rows_table(kind: CSVKind) -> str:
    return f"rows_{kind}"


class SessionCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as con:
            con.execute(_IMPORTS_SCHEMA)
            con.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    # --- writes -------------------------------------------------------------

    def save(self, parsed: ParsedCSV) -> int:
        df = parsed.df.copy()
        # Drop derived _dt helper columns; they're recomputable on load.
        drop_cols = [c for c in df.columns if c.endswith("_dt")]
        if drop_cols:
            df = df.drop(columns=drop_cols)

        with closing(self._connect()) as con:
            cur = con.execute(
                """
                INSERT INTO imports (kind, export_date, source_filename, imported_at, row_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    parsed.kind,
                    parsed.export_date.isoformat(),
                    parsed.source_filename,
                    datetime.now(UTC).isoformat(timespec="seconds"),
                    len(df),
                ),
            )
            import_id = int(cur.lastrowid)
            df = df.assign(import_id=import_id)
            df.to_sql(_rows_table(parsed.kind), con, if_exists="append", index=False)
            con.commit()
        return import_id

    def clear(self) -> None:
        with closing(self._connect()) as con:
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                con.execute(f"DROP TABLE IF EXISTS {t}")
            con.commit()
            con.execute(_IMPORTS_SCHEMA)
            con.commit()

    # --- reads --------------------------------------------------------------

    def list_snapshots(self, kind: CSVKind) -> list[date]:
        with closing(self._connect()) as con:
            cur = con.execute(
                "SELECT DISTINCT export_date FROM imports WHERE kind = ? ORDER BY export_date",
                (kind,),
            )
            return [date.fromisoformat(r[0]) for r in cur.fetchall()]

    def load_latest(self, kind: CSVKind) -> Optional[pd.DataFrame]:
        with closing(self._connect()) as con:
            cur = con.execute(
                """
                SELECT id FROM imports
                WHERE kind = ?
                ORDER BY datetime(imported_at) DESC, id DESC
                LIMIT 1
                """,
                (kind,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            import_id = int(row[0])
            return self._load_rows(con, kind, import_id)

    def load_snapshot(self, kind: CSVKind, export_date: date) -> Optional[pd.DataFrame]:
        with closing(self._connect()) as con:
            cur = con.execute(
                """
                SELECT id FROM imports
                WHERE kind = ? AND export_date = ?
                ORDER BY datetime(imported_at) DESC, id DESC
                LIMIT 1
                """,
                (kind, export_date.isoformat()),
            )
            row = cur.fetchone()
            if row is None:
                return None
            import_id = int(row[0])
            return self._load_rows(con, kind, import_id)

    @staticmethod
    def _load_rows(
        con: sqlite3.Connection, kind: CSVKind, import_id: int
    ) -> Optional[pd.DataFrame]:
        table = _rows_table(kind)
        cur = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        )
        if cur.fetchone() is None:
            return None
        df = pd.read_sql_query(
            f"SELECT * FROM {table} WHERE import_id = ?",
            con,
            params=(import_id,),
        )
        if "import_id" in df.columns:
            df = df.drop(columns=["import_id"])
        return df


__all__ = ["SessionCache"]
