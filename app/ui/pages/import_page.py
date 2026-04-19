"""Import page: drag-drop (folders or multi-file), file picker, report summary."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.logging_setup import get_logger
from app.core.paths import desktop_dir
from app.import_.pipeline import ImportReport, import_files, import_folder
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase

_log = get_logger(__name__)

_STATUS_ICON = {"ok": "✓", "partial": "!", "error": "✗"}
_STATUS_COLOR = {
    "ok": QColor("#2e7d32"),
    "partial": QColor("#b26a00"),
    "error": QColor("#b00020"),
}


class _DropZone(QFrame):
    """Accepts either a folder or a list of files via drag-and-drop."""

    folderDropped = Signal(Path)
    filesDropped = Signal(list)  # list[Path]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)
        lbl = QLabel(
            "Drop a folder or one-or-more CSV files here, or click ‘Pick folder’ below"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.toLocalFile()]
        if not paths:
            event.ignore()
            return

        # Single folder → folder import.
        if len(paths) == 1 and paths[0].is_dir():
            self.folderDropped.emit(paths[0])
            event.acceptProposedAction()
            return

        # Otherwise: expand any folders into their CSV children, accept files.
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


class ImportPage(PageBase):
    title = "Import"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        title = QLabel("Import")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        outer.addWidget(title)

        self._dropzone = _DropZone()
        self._dropzone.folderDropped.connect(self._start_folder_import)
        self._dropzone.filesDropped.connect(self._start_files_import)
        outer.addWidget(self._dropzone)

        controls = QHBoxLayout()
        self._pick_btn = QPushButton("Pick folder…")
        self._pick_btn.clicked.connect(self._pick_folder)
        controls.addWidget(self._pick_btn)
        self._pick_files_btn = QPushButton("Pick files…")
        self._pick_files_btn.clicked.connect(self._pick_files)
        controls.addWidget(self._pick_files_btn)
        self._clear_btn = QPushButton("Clear cache")
        self._clear_btn.clicked.connect(self._clear_cache)
        controls.addWidget(self._clear_btn)
        controls.addStretch(1)
        outer.addLayout(controls)

        self._summary = QLabel("")
        self._summary.setStyleSheet("font-weight: 600;")
        self._summary.setWordWrap(True)
        outer.addWidget(self._summary)

        self._banner = QLabel("")
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet(
            "background:#fff3cd; color:#7a5b00; padding:8px; border-radius:6px;"
        )
        self._banner.setVisible(False)
        outer.addWidget(self._banner)

        self._files = QListWidget()
        outer.addWidget(self._files, 1)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet("font-family: 'Consolas', 'Cascadia Mono', monospace;")
        outer.addWidget(self._log, 1)

        self._pool = QThreadPool.globalInstance()

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
        self._files.clear()
        self._summary.setText("")
        self._banner.setVisible(False)
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
            icon = _STATUS_ICON.get(fr.status, "?")
            kind_label = fr.kind or "unknown"
            text = f"{icon} {fr.path.name} [{kind_label}] rows={fr.rows_read}"
            if fr.error:
                text += f"  — {fr.error}"
            elif fr.warnings:
                text += f"  — {len(fr.warnings)} warning(s)"
            item = QListWidgetItem(text)
            color = _STATUS_COLOR.get(fr.status)
            if color is not None:
                item.setForeground(QBrush(color))
            tooltip_lines = []
            if fr.error:
                tooltip_lines.append(f"Error: {fr.error}")
            tooltip_lines.extend(fr.warnings)
            if tooltip_lines:
                item.setToolTip("\n".join(tooltip_lines))
            self._files.addItem(item)
            if fr.status in ("ok", "partial") and fr.parsed is not None:
                self.context.cache.save(fr.parsed)

        total = len(report.files)
        self._summary.setText(
            f"{total} file(s) detected — "
            f"{report.ok_count} parsed, "
            f"{report.partial_count} partial, "
            f"{report.error_count} failed"
        )
        if report.has_partial or report.error_count:
            self._banner.setText(
                "Some data may be incomplete because the season is still in "
                "progress or some files had unexpected values. Partial files "
                "are still imported — hover each entry for details."
            )
            self._banner.setVisible(True)
        self._append_log(
            f"done: {report.ok_count} ok, {report.partial_count} partial, "
            f"{report.error_count} error(s)"
        )
        if report.ok_count + report.partial_count > 0:
            self.context.notify_changed()

    def _on_failed(self, message: str) -> None:
        self._pick_btn.setEnabled(True)
        self._pick_files_btn.setEnabled(True)
        self._append_log(f"FAILED: {message}")

    def _clear_cache(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear cache?",
            "This will remove all imported snapshots from the session cache. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.context.cache.clear()
            self._summary.setText("")
            self._banner.setVisible(False)
            self._files.clear()
            self._append_log("cache cleared")
            self.context.notify_changed()

    def _append_log(self, line: str) -> None:
        self._log.appendPlainText(line)
