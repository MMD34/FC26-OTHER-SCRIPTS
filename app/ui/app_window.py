"""Main QMainWindow shell (Sprint 3: placeholder central widget + sidebar)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QWidget,
)

SIDEBAR_PAGES: tuple[str, ...] = (
    "Overview",
    "Analytics",
    "Squad",
    "Wonderkids",
    "Tactics",
    "Transfers",
    "Import",
)


class AppWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FC26 Analytics")
        self.resize(1280, 800)

        sidebar = QListWidget()
        sidebar.setFixedWidth(200)
        for name in SIDEBAR_PAGES:
            sidebar.addItem(QListWidgetItem(name))
        sidebar.setCurrentRow(0)
        self._sidebar = sidebar

        central = QLabel("FC26 Analytics — no data imported")
        central.setAlignment(Qt.AlignmentFlag.AlignCenter)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(central)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        container = QWidget()
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)
