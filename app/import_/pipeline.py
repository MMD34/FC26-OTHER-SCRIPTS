"""Import orchestration: discover CSVs, parse each, aggregate a report."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app.core.constants import CSVKind
from app.core.logging_setup import get_logger
from app.import_.discovery import DetectedFile, scan
from app.import_.parsers import ParsedCSV, ParserError, parser_for

_log = get_logger(__name__)

FileStatus = Literal["ok", "error"]


@dataclass
class FileReport:
    path: Path
    kind: CSVKind
    status: FileStatus
    rows_read: int = 0
    rows_dropped: int = 0
    error: str | None = None
    parsed: ParsedCSV | None = None


@dataclass
class ImportReport:
    files: list[FileReport] = field(default_factory=list)
    totals: dict[str, int] = field(default_factory=dict)

    @property
    def ok_count(self) -> int:
        return sum(1 for f in self.files if f.status == "ok")

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.files if f.status == "error")


def _parse_one(detected: DetectedFile) -> FileReport:
    try:
        parsed = parser_for(detected.kind).parse(detected.path)
    except ParserError as exc:
        _log.warning("parse error (%s): %s", detected.path.name, exc)
        return FileReport(
            path=detected.path, kind=detected.kind, status="error", error=str(exc)
        )
    except Exception as exc:  # defensive: never bubble to caller
        _log.exception("unexpected parser failure for %s", detected.path.name)
        return FileReport(
            path=detected.path, kind=detected.kind, status="error", error=repr(exc)
        )
    return FileReport(
        path=detected.path,
        kind=detected.kind,
        status="ok",
        rows_read=parsed.rows_read,
        rows_dropped=parsed.rows_dropped,
        parsed=parsed,
    )


def import_folder(folder: Path) -> ImportReport:
    detected = scan(folder)
    _log.info("import_folder: %s → %d candidate files", folder, len(detected))
    report = ImportReport()
    for d in detected:
        report.files.append(_parse_one(d))

    kind_counts: Counter[str] = Counter()
    for f in report.files:
        if f.status == "ok":
            kind_counts[f.kind] += 1
    report.totals = {
        "files_seen": len(report.files),
        "files_ok": report.ok_count,
        "files_error": report.error_count,
        **{f"kind_{k}": v for k, v in kind_counts.items()},
    }
    return report
