"""Main QMainWindow shell with sidebar routing into a QStackedWidget."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.app_context import AppContext
from app.ui.theme import LightPalette, Palette, load_qss
from app.ui.pages.analytics_page import AnalyticsPage
from app.ui.pages.import_page import ImportPage
from app.ui.pages.overview_page import OverviewPage
from app.ui.pages.squad_page import SquadPage
from app.ui.pages.tactics_page import TacticsPage
from app.ui.pages.transfers_page import TransfersPage
from app.ui.pages.wonderkids_page import WonderkidsPage

from app.ui.shell import Sidebar, Topbar, StatusBar

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
    """The new AppShell replacing legacy chrome."""

    def __init__(self, context: AppContext | None = None) -> None:
        super().__init__()
        self.setWindowTitle("FC26 Analytics")
        self.resize(1280, 800)

        self.context = context or AppContext()

        # Build main layout
        central_widget = QWidget()
        main_lyt = QHBoxLayout(central_widget)
        main_lyt.setContentsMargins(0, 0, 0, 0)
        main_lyt.setSpacing(0)
        self.setCentralWidget(central_widget)

        # 1. Sidebar
        self._sidebar = Sidebar(SIDEBAR_PAGES)
        main_lyt.addWidget(self._sidebar)

        # 2. Right side container (Topbar + Stack + StatusBar)
        right_container = QWidget()
        right_lyt = QVBoxLayout(right_container)
        right_lyt.setContentsMargins(0, 0, 0, 0)
        right_lyt.setSpacing(0)
        main_lyt.addWidget(right_container, 1)

        # Topbar
        self._topbar = Topbar()
        self._topbar.themeToggled.connect(self._toggle_theme)
        right_lyt.addWidget(self._topbar)

        # Stack
        self._stack = QStackedWidget()
        self._pages: list[QWidget] = [
            OverviewPage(self.context),
            AnalyticsPage(self.context),
            SquadPage(self.context),
            WonderkidsPage(self.context),
            TacticsPage(self.context),
            TransfersPage(self.context),
            ImportPage(self.context),
        ]
        for p in self._pages:
            self._stack.addWidget(p)
        right_lyt.addWidget(self._stack, 1)

        # StatusBar
        self._status = StatusBar()
        right_lyt.addWidget(self._status)

        # Wiring
        self._sidebar.pageSelected.connect(self._on_page_selected)
        self.context.dataChanged.connect(self._on_data_changed)

        # Initial state
        self._topbar.set_title(SIDEBAR_PAGES[0])

    def _on_page_selected(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._topbar.set_title(SIDEBAR_PAGES[index])

    def _toggle_theme(self, light_mode: bool) -> None:
        palette = LightPalette() if light_mode else Palette()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(load_qss(palette))

    def _on_data_changed(self) -> None:
        for page in self._pages:
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                refresh()
        self._status.show_message("Data refreshed")
