"""Import page (Sprint 5.2 redesign).

Wires the existing pipeline into the new design-system primitives:
- ``Dropzone`` for the drag/drop target,
- ``FileRow`` rows for the parse report (OK / Partial / Error pills),
- ``LogView`` for the streaming log.

No business logic changes — only the view layer is swapped.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.logging_setup import get_logger
from app.core.paths import desktop_dir
from app.import_.pipeline import ImportReport, import_files, import_folder
from app.services.app_context import AppContext
from app.ui.components import (
    Card,
    Dropzone,
    FileRow,
    GhostButton,
    LogView,
    PrimaryButton,
    SectionTitle,
)
from app.ui.pages._base import PageBase

_log = get_logger(__name__)

_STATUS_TO_LEVEL: dict[str, str] = {"ok": "ok", "partial": "warn", "error": "err"}


class _WorkerSignals(QObject):
    finished = Signal(object)  # ImportReport
    failed = Signal(str)


class _ImportWorker(QRunnable):
    def __init__(self, target: Path | list[Path]) -> None:
        super().__init__()
        self.target = target
        self.signals = _WorkerSignals()

    def run(self) -> None:  # type: ignore[override]
        try:
            if isinstance(self.target, list):
                report = import_files(self.target)
            else:
                report = import_folder(self.target)
        except Exception as exc:  # pragma: no cover - defensive
            _log.exception("import worker crashed")
            self.signals.failed.emit(repr(exc))
            return
        self.signals.finished.emit(report)


class _PathAwareDropzone(Dropzone):
    """Dropzone variant that classifies a single dropped folder vs. files."""

    folderDropped = Signal(Path)
    filesDropped = Signal(list)

    def dropEvent(self, event):  # type: ignore[override]
        self.setProperty("drag-hover", False)
        self.style().unpolish(self)
        self.style().polish(self)

        urls = event.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.toLocalFile()]
        if not paths:
            event.ignore()
            return
        if len(paths) == 1 and paths[0].is_dir():
            self.folderDropped.emit(paths[0])
            event.acceptProposedAction()
            return
        files: list[Path] = []
        for p in paths:
            if p.is_dir():
                files.extend(sorted(c for c in p.iterdir() if c.is_file() and c.suffix.lower() == ".csv"))
            elif p.is_file() and p.suffix.lower() == ".csv":
                files.append(p)
        if files:
            self.filesDropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()


class ImportPage(PageBase):
    title = "Import"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        outer.addWidget(SectionTitle("Import Snapshot"))

        # Dropzone + action row
        self._dropzone = _PathAwareDropzone()
        self._dropzone.folderDropped.connect(self._start_folder_import)
        self._dropzone.filesDropped.connect(self._start_files_import)
        outer.addWidget(self._dropzone)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self._pick_btn = PrimaryButton("Pick folder…")
        self._pick_btn.clicked.connect(self._pick_folder)
        actions.addWidget(self._pick_btn)
        self._pick_files_btn = PrimaryButton("Pick files…")
        self._pick_files_btn.clicked.connect(self._pick_files)
        actions.addWidget(self._pick_files_btn)
        self._clear_btn = GhostButton("Clear cache")
        self._clear_btn.clicked.connect(self._clear_cache)
        actions.addWidget(self._clear_btn)
        actions.addStretch(1)
        outer.addLayout(actions)

        # Parse-report card (vertically scrollable list of FileRow)
        self._report_card = Card(title="Parse report")
        self._files_host = QWidget()
        self._files_lyt = QVBoxLayout(self._files_host)
        self._files_lyt.setContentsMargins(0, 0, 0, 0)
        self._files_lyt.setSpacing(6)
        self._files_lyt.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidget(self._files_host)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._report_card.add_widget(scroll, 1)
        outer.addWidget(self._report_card, 1)

        # Log view
        log_card = Card(title="Import log")
        self._log = LogView()
        log_card.add_widget(self._log, 1)
        outer.addWidget(log_card, 1)

        self._pool = QThreadPool.globalInstance()

    # --- helpers ------------------------------------------------------------

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _append_log(self, line: str, level: str = "info") -> None:
        self._log.append_log(line, level=level, timestamp=self._ts())  # type: ignore[arg-type]

    def _clear_files(self) -> None:
        while self._files_lyt.count():
            item = self._files_lyt.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    # --- actions ------------------------------------------------------------

    def _pick_folder(self) -> None:
        start = str(desktop_dir())
        folder = QFileDialog.getExistingDirectory(self, "Select folder", start)
        if folder:
            self._start_folder_import(Path(folder))

    def _pick_files(self) -> None:
        start = str(desktop_dir())
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select CSV files", start, "CSV files (*.csv);;All files (*)"
        )
        if files:
            self._start_files_import([Path(f) for f in files])

    def _start_folder_import(self, folder: Path) -> None:
        self._append_log(f"→ scanning {folder}")
        self._begin_import(folder)

    def _start_files_import(self, files: list[Path]) -> None:
        self._append_log(f"→ importing {len(files)} file(s)")
        self._begin_import(files)

    def _begin_import(self, target: Path | list[Path]) -> None:
        self.set_state("loading")
        self._clear_files()
        self._pick_btn.setEnabled(False)
        self._pick_files_btn.setEnabled(False)
        worker = _ImportWorker(target)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.failed.connect(self._on_failed)
        self._pool.start(worker)

    def _on_finished(self, report: ImportReport) -> None:
        self._pick_btn.setEnabled(True)
        self._pick_files_btn.setEnabled(True)
        for fr in report.files:
            level = _STATUS_TO_LEVEL.get(fr.status, "ok")
            row = FileRow(fr.path.name, status=level)  # type: ignore[arg-type]
            tooltip_lines: list[str] = []
            if fr.kind:
                tooltip_lines.append(f"kind: {fr.kind}")
            if fr.rows_read:
                tooltip_lines.append(f"rows: {fr.rows_read}")
            if fr.error:
                tooltip_lines.append(f"error: {fr.error}")
            tooltip_lines.extend(fr.warnings)
            if tooltip_lines:
                row.setToolTip("\n".join(tooltip_lines))
            self._files_lyt.addWidget(row)
            if fr.status in ("ok", "partial") and fr.parsed is not None:
                self.context.cache.save(fr.parsed)
            log_level = "ok" if fr.status == "ok" else ("warn" if fr.status == "partial" else "err")
            self._append_log(
                f"{fr.status:>7}  {fr.path.name} ({fr.rows_read} rows)",
                level=log_level,
            )

        total = len(report.files)
        self._append_log(
            f"done: {report.ok_count} ok, {report.partial_count} partial, "
            f"{report.error_count} error(s)",
            level="ok" if report.error_count == 0 else "warn",
        )
        if report.ok_count + report.partial_count > 0:
            self.context.notify_changed()
        if report.error_count and not (report.ok_count + report.partial_count):
            self.set_state("error")
        elif total == 0:
            self.set_state("empty")
        else:
            self.set_state("ready")

    def _on_failed(self, message: str) -> None:
        self._pick_btn.setEnabled(True)
        self._pick_files_btn.setEnabled(True)
        self._append_log(f"FAILED: {message}", level="err")
        self.set_state("error", error=message)

    def _clear_cache(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear cache?",
            "This will remove all imported snapshots from the session cache. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.context.cache.clear()
            self._clear_files()
            self._append_log("cache cleared", level="warn")
            self.context.notify_changed()
