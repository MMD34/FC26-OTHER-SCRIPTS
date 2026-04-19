"""Squad Performance page (PT §12.2)."""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSplitter, QVBoxLayout

from app.analytics.squad import form_leaders, top_by_rating, top_scorers
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase
from app.ui.widgets.chart_panel import ChartPanel, Series
from app.ui.widgets.data_table import DataTable
from app.ui.widgets.filter_bar import FilterBar
from app.ui.widgets.player_drawer import PlayerDrawer

_LEADERBOARD_COLS = ("display_name", "teamname", "overallrating", "leaguegoals",
                     "leagueappearances", "form")


def _bar_series(df: pd.DataFrame, value_col: str, color: str) -> list[Series]:
    if df.empty or value_col not in df.columns:
        return []
    ys = df[value_col].fillna(0).astype(float).tolist()
    xs = list(range(len(ys)))
    return [Series(value_col, x=xs, y=ys, kind="bar", color=color)]


class SquadPage(PageBase):
    title = "Squad"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        self._title = QLabel("Squad Performance")
        self._title.setStyleSheet("font-size: 20px; font-weight: 600;")
        outer.addWidget(self._title)

        self._filter = FilterBar()
        self._filter.add_search("Search players…")
        self._filter.add_combo("position", "Position", ["All", "GK", "DEF", "MID", "ATT"])
        self._filter.add_combo("team", "Team", ["All"])
        outer.addWidget(self._filter)

        # leaderboards row
        self._chart_scorers = ChartPanel("Top scorers", x_axis="rank", y_axis="goals")
        self._chart_rating = ChartPanel("Top rated", x_axis="rank", y_axis="OVR")
        self._chart_form = ChartPanel("Form leaders", x_axis="rank", y_axis="form")

        leaderboards = QGridLayout()
        leaderboards.addWidget(self._chart_scorers, 0, 0)
        leaderboards.addWidget(self._chart_rating, 0, 1)
        leaderboards.addWidget(self._chart_form, 0, 2)
        outer.addLayout(leaderboards)

        # split: table + drawer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._table = DataTable(pd.DataFrame(), list(_LEADERBOARD_COLS))
        self._table.clicked.connect(self._on_row_clicked)
        splitter.addWidget(self._table)
        self._drawer = PlayerDrawer()
        self._drawer.setFloating(False)
        splitter.addWidget(self._drawer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)

        self._filter.searchChanged.connect(lambda _txt: self.refresh())
        self._filter.filterChanged.connect(lambda _k, _v: self.refresh())

        self._players_df: pd.DataFrame = pd.DataFrame()
        self._filtered: pd.DataFrame = pd.DataFrame()
        self.refresh()

    def _on_row_clicked(self, index) -> None:
        if self._filtered.empty:
            return
        row = index.row()
        if 0 <= row < len(self._filtered):
            self._drawer.show_player(self._filtered.iloc[row])

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df
        text = self._filter.search_text().strip().lower()
        if text and "display_name" in out.columns:
            out = out[out["display_name"].fillna("").str.lower().str.contains(text)]
        pos_filter = self._filter.filter_value("position")
        if pos_filter and pos_filter != "All" and "preferredposition1" in out.columns:
            from app.analytics.wonderkids import position_group
            mask = out["preferredposition1"].map(lambda v: position_group(v) == pos_filter)
            out = out[mask.fillna(False)]
        team_filter = self._filter.filter_value("team")
        if team_filter and team_filter != "All" and "teamname" in out.columns:
            out = out[out["teamname"].fillna("") == team_filter]
        return out

    def refresh(self) -> None:
        self.set_state("loading")
        df = self.context.cache.load_latest("players_snapshot")
        if df is None or df.empty:
            self._players_df = pd.DataFrame()
            self._filtered = pd.DataFrame()
            self._table.set_dataframe(pd.DataFrame(), list(_LEADERBOARD_COLS))
            for c in (self._chart_scorers, self._chart_rating, self._chart_form):
                c.set_series([])
            self.set_state("empty")
            return
        self._players_df = df

        # populate team filter once
        team_combo = self._filter._combos.get("team")
        if team_combo is not None and team_combo.count() <= 1 and "teamname" in df.columns:
            for name in sorted({str(t) for t in df["teamname"].dropna().unique()}):
                team_combo.addItem(name)

        filtered = self._apply_filters(df)
        self._filtered = filtered.reset_index(drop=True)
        self._table.set_dataframe(self._filtered, list(_LEADERBOARD_COLS))

        scorers = top_scorers(filtered, n=10)
        rated = top_by_rating(filtered, n=10)
        formed = form_leaders(filtered, n=10)
        self._chart_scorers.set_series(_bar_series(scorers, "leaguegoals", "#5ad19a"))
        self._chart_rating.set_series(_bar_series(rated, "overallrating", "#7c9cff"))
        self._chart_form.set_series(_bar_series(formed, "form", "#f3c969"))
        self.set_state("ready")
