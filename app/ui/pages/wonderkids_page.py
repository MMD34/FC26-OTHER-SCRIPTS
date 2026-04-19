"""Wonderkid Scout Hub page (PT §11)."""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSplitter, QVBoxLayout

from app.analytics.wonderkids import filter_wonderkids, origin_label, position_group
from app.core.constants import DEFAULT_WONDERKID_MAX_AGE, DEFAULT_WONDERKID_POTENTIAL
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase
from app.ui.widgets.chart_panel import ChartPanel, Series
from app.ui.widgets.data_table import DataTable
from app.ui.widgets.player_drawer import PlayerDrawer

_TABLE_COLS = (
    "display_name", "age", "potential", "overallrating",
    "preferredposition1", "teamname", "leaguename", "origin",
)

_GROUP_COLOR = {"GK": "#f3c969", "DEF": "#7c9cff", "MID": "#5ad19a", "ATT": "#ef6f6f"}


class WonderkidsPage(PageBase):
    title = "Wonderkids"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        self._title = QLabel("Wonderkid Scout Hub")
        self._title.setStyleSheet("font-size: 20px; font-weight: 600;")
        outer.addWidget(self._title)

        self._scatter = ChartPanel(
            "Age × Potential", subtitle="colored by position group",
            x_axis="age", y_axis="potential",
        )
        outer.addWidget(self._scatter)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._table = DataTable(pd.DataFrame(), list(_TABLE_COLS))
        self._table.clicked.connect(self._on_row_clicked)
        splitter.addWidget(self._table)

        self._drawer = PlayerDrawer()
        self._drawer.setFloating(False)
        splitter.addWidget(self._drawer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)

        self._df: pd.DataFrame = pd.DataFrame()
        self.refresh()

    def _on_row_clicked(self, index) -> None:
        if self._df.empty:
            return
        row = index.row()
        if 0 <= row < len(self._df):
            self._drawer.show_player(self._df.iloc[row])

    def refresh(self) -> None:
        self.set_state("loading")
        df = self.context.cache.load_latest("wonderkids")
        if df is None or df.empty:
            df = self.context.cache.load_latest("players_snapshot")
        if df is None or df.empty:
            self._df = pd.DataFrame()
            self._table.set_dataframe(pd.DataFrame(), list(_TABLE_COLS))
            self._scatter.set_series([])
            self.set_state("empty")
            return

        wk = filter_wonderkids(
            df,
            max_age=DEFAULT_WONDERKID_MAX_AGE,
            min_potential=DEFAULT_WONDERKID_POTENTIAL,
        ).copy()
        if "playerid" in wk.columns:
            wk["origin"] = wk["playerid"].map(origin_label)
        self._df = wk.reset_index(drop=True)
        self._table.set_dataframe(self._df, list(_TABLE_COLS))

        if "preferredposition1" in wk.columns:
            wk["_group"] = wk["preferredposition1"].map(position_group)
        else:
            wk["_group"] = None
        series: list[Series] = []
        for group, color in _GROUP_COLOR.items():
            sub = wk[wk["_group"] == group]
            if sub.empty:
                continue
            series.append(Series(
                group,
                x=sub["age"].fillna(0).astype(float).tolist(),
                y=sub["potential"].fillna(0).astype(float).tolist(),
                kind="scatter", color=color, extra={"size": 9},
            ))
        self._scatter.set_series(series)
        self.set_state("ready")
