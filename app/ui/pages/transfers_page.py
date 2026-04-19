"""Transfer Planning page (PT §12.2 / §9.7)."""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSplitter, QVBoxLayout

from app.analytics.transfers import (
    aging_quadrant,
    expiring_contracts,
    positional_depth,
    replacement_candidates,
)
from app.domain.season import SeasonOverview
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase
from app.ui.widgets.chart_panel import ChartPanel, Series
from app.ui.widgets.data_table import DataTable
from app.ui.widgets.kpi_tile import KpiTile

_EXPIRING_COLS = ("display_name", "age", "preferredposition1",
                  "overallrating", "potential", "contractvaliduntil")
_REPLACEMENT_COLS = ("display_name", "age", "overallrating", "potential", "teamname")


class TransfersPage(PageBase):
    title = "Transfers"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Transfer Planning")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch(1)
        self._kpi_in = KpiTile("Incoming transfers", "—")
        header.addWidget(self._kpi_in)
        outer.addLayout(header)

        # row 1: aging quadrant + positional depth
        self._aging = ChartPanel("Aging quadrant", subtitle="age × overall",
                                 x_axis="age", y_axis="OVR")
        self._depth = ChartPanel("Positional depth", subtitle="user team",
                                 x_axis="position code", y_axis="count")
        row1 = QGridLayout()
        row1.addWidget(self._aging, 0, 0)
        row1.addWidget(self._depth, 0, 1)
        outer.addLayout(row1, 1)

        # row 2: expiring contracts | replacement finder
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QVBoxLayout()
        left_w = pd.DataFrame()
        left_lbl = QLabel("Expiring contracts (next year)")
        left_lbl.setObjectName("card-subtitle")
        left.addWidget(left_lbl)
        self._expiring = DataTable(left_w, list(_EXPIRING_COLS))
        self._expiring.clicked.connect(self._on_expiring_clicked)
        left.addWidget(self._expiring)
        from PySide6.QtWidgets import QWidget
        left_holder = QWidget()
        left_holder.setLayout(left)
        splitter.addWidget(left_holder)

        right = QVBoxLayout()
        self._rep_lbl = QLabel("Replacement candidates: select a row")
        self._rep_lbl.setObjectName("card-subtitle")
        right.addWidget(self._rep_lbl)
        self._candidates = DataTable(pd.DataFrame(), list(_REPLACEMENT_COLS))
        right.addWidget(self._candidates)
        right_holder = QWidget()
        right_holder.setLayout(right)
        splitter.addWidget(right_holder)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        self._players: pd.DataFrame = pd.DataFrame()
        self._expiring_df: pd.DataFrame = pd.DataFrame()
        self.refresh()

    def _on_expiring_clicked(self, index) -> None:
        if self._expiring_df.empty or self._players.empty:
            return
        row = index.row()
        if not (0 <= row < len(self._expiring_df)):
            return
        target = self._expiring_df.iloc[row]
        cands = replacement_candidates(self._players, target, top_n=10)
        self._rep_lbl.setText(
            f"Replacements for {target.get('display_name', '?')} "
            f"(POS {target.get('preferredposition1')}, OVR {target.get('overallrating')})"
        )
        self._candidates.set_dataframe(cands.reset_index(drop=True), list(_REPLACEMENT_COLS))

    def refresh(self) -> None:
        self.set_state("loading")
        overview_df = self.context.cache.load_latest("season_overview")
        players_df = self.context.cache.load_latest("players_snapshot")
        transfers_df = self.context.cache.load_latest("transfer_history")

        if players_df is None:
            self._players = pd.DataFrame()
            self._expiring_df = pd.DataFrame()
            self._aging.set_series([])
            self._depth.set_series([])
            self._expiring.set_dataframe(pd.DataFrame(), list(_EXPIRING_COLS))
            self._candidates.set_dataframe(pd.DataFrame(), list(_REPLACEMENT_COLS))
            self._kpi_in.set_value("—")
            self.set_state("empty")
            return
        self._players = players_df

        # Aging quadrant
        pts = aging_quadrant(players_df)
        if pts:
            self._aging.set_series([Series(
                "players",
                x=[p.age for p in pts],
                y=[p.overallrating for p in pts],
                kind="scatter", color="#7c9cff",
                extra={"size": 6},
            )])
        else:
            self._aging.set_series([])

        if overview_df is not None and not overview_df.empty:
            overview = SeasonOverview.from_row(overview_df.iloc[0])
            year = overview.season_year
            user_team = overview.user_teamid

            self._expiring_df = expiring_contracts(players_df, current_year=year).reset_index(drop=True)
            self._expiring.set_dataframe(self._expiring_df, list(_EXPIRING_COLS))

            depth = positional_depth(players_df, teamid=user_team)
            if not depth.empty:
                self._depth.set_series([Series(
                    "count",
                    x=[float(i) for i in depth.index.astype(float).tolist()],
                    y=[float(v) for v in depth.tolist()],
                    kind="bar", color="#5ad19a",
                )])
            else:
                self._depth.set_series([])

            if transfers_df is not None and "teamtoid" in transfers_df.columns:
                count = int((transfers_df["teamtoid"] == user_team).sum())
                self._kpi_in.set_value(str(count))
            else:
                self._kpi_in.set_value("—")
        else:
            self._expiring_df = pd.DataFrame()
            self._expiring.set_dataframe(pd.DataFrame(), list(_EXPIRING_COLS))
            self._depth.set_series([])
            self._kpi_in.set_value("—")
        self.set_state("ready")
