"""Import orchestration: discover CSVs, validate, parse each, aggregate a report."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

from app.core.constants import CSVKind
from app.core.logging_setup import get_logger
from app.import_.discovery import DetectedFile, detect_kind, scan
from app.import_.parsers import ParsedCSV, ParserError, parser_for
from app.import_ import schema as _schema

_log = get_logger(__name__)

FileStatus = Literal["ok", "partial", "error"]


@dataclass
class FileReport:
    path: Path
    kind: CSVKind | None
    status: FileStatus
    rows_read: int = 0
    rows_dropped: int = 0
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    parsed: ParsedCSV | None = None


@dataclass
class ImportReport:
    files: list[FileReport] = field(default_factory=list)
    totals: dict[str, int] = field(default_factory=dict)

    @property
    def ok_count(self) -> int:
        return sum(1 for f in self.files if f.status == "ok")

    @property
    def partial_count(self) -> int:
        return sum(1 for f in self.files if f.status == "partial")

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.files if f.status == "error")

    @property
    def has_partial(self) -> bool:
        return self.partial_count > 0


# --- validation --------------------------------------------------------------

def validate_file(path: Path, kind: CSVKind | None) -> tuple[str, str | None]:
    """Pre-parse sanity check. Returns (classification, reason).

    Classifications: "VALID", "PARTIAL", "INVALID". Only "INVALID" aborts
    the parse — "PARTIAL" still gets parsed and is upgraded to ``ok`` if no
    warnings surface during parsing.
    """
    if not path.exists():
        return "INVALID", "file does not exist"
    if path.stat().st_size == 0:
        return "INVALID", "file is empty"
    if kind is None:
        return "INVALID", "unrecognized filename"
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            header = fh.readline().strip()
    except OSError as exc:
        return "INVALID", f"cannot read file: {exc}"
    if not header:
        return "INVALID", "missing header row"

    cols = {c.strip() for c in header.split(",")}
    required = _schema.REQUIRED_COLUMNS[kind]
    missing = required - cols
    if missing:
        return "INVALID", f"missing required columns: {sorted(missing)}"

    expected = set(_schema.COLUMNS[kind])
    missing_optional = expected - cols - required
    if missing_optional:
        return "PARTIAL", f"missing optional columns: {sorted(missing_optional)}"
    return "VALID", None


# --- parse one ---------------------------------------------------------------

def _parse_one(path: Path, kind: CSVKind | None) -> FileReport:
    classification, reason = validate_file(path, kind)
    if classification == "INVALID" or kind is None:
        _log.warning("validation rejected %s: %s", path.name, reason)
        return FileReport(
            path=path, kind=kind, status="error", error=reason or "invalid file"
        )

    try:
        parsed = parser_for(kind).parse(path)
    except ParserError as exc:
        _log.warning("parse error (%s): %s", path.name, exc)
        return FileReport(path=path, kind=kind, status="error", error=str(exc))
    except Exception as exc:  # defensive: never bubble
        _log.exception("unexpected parser failure for %s", path.name)
        return FileReport(path=path, kind=kind, status="error", error=repr(exc))

    status: FileStatus = "ok"
    warnings = list(parsed.warnings)
    if classification == "PARTIAL":
        status = "partial"
        if reason:
            warnings.insert(0, reason)
    if warnings and status == "ok":
        status = "partial"

    return FileReport(
        path=path,
        kind=kind,
        status=status,
        rows_read=parsed.rows_read,
        rows_dropped=parsed.rows_dropped,
        warnings=warnings,
        parsed=parsed,
    )


def _build_report(file_reports: list[FileReport]) -> ImportReport:
    report = ImportReport(files=file_reports)
    kind_counts: Counter[str] = Counter()
    for f in file_reports:
        if f.status in ("ok", "partial") and f.kind:
            kind_counts[f.kind] += 1
    report.totals = {
        "files_seen": len(file_reports),
        "files_ok": report.ok_count,
        "files_partial": report.partial_count,
        "files_error": report.error_count,
        **{f"kind_{k}": v for k, v in kind_counts.items()},
    }
    return report


def import_folder(folder: Path) -> ImportReport:
    detected = scan(folder)
    _log.info("import_folder: %s → %d candidate files", folder, len(detected))
    reports = [_parse_one(d.path, d.kind) for d in detected]
    return _build_report(reports)


def import_files(paths: Iterable[Path]) -> ImportReport:
    """Parse an arbitrary list of CSV paths (drag-drop of individual files)."""
    reports: list[FileReport] = []
    for p in paths:
        if not p.is_file():
            continue
        kind = detect_kind(p.name)
        if kind is None:
            _log.info("skipping unrecognized file: %s", p.name)
            reports.append(FileReport(
                path=p, kind=None, status="error",
                error="unrecognized filename (not an FC26 export)"
            ))
            continue
        reports.append(_parse_one(p, kind))
    _log.info("import_files: %d files processed", len(reports))
    return _build_report(reports)


# Backwards-compat: _parse_one(DetectedFile) still works if anything calls it.
def _parse_detected(detected: DetectedFile) -> FileReport:
    return _parse_one(detected.path, detected.kind)
