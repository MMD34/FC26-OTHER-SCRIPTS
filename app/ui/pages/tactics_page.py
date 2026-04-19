"""Tactical Dashboard page (PT §12.2 / §9.6).

Formation pitch is gated on §15.4 resolution (probe was PARTIAL); we render
an explicit "Formation data unavailable" card per the roadmap fallback.
"""
from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from app.analytics.tactics import home_away_efficiency, team_ratings_profile
from app.domain.season import SeasonOverview
from app.domain.standings import StandingsRow
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase
from app.ui.widgets.chart_panel import ChartPanel, Series
from app.ui.widgets.kpi_tile import KpiTile


def _placeholder(text: str) -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(20, 20, 20, 20)
    lbl = QLabel(text)
    lbl.setObjectName("card-subtitle")
    lay.addWidget(lbl)
    return f


class TacticsPage(PageBase):
    title = "Tactics"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        self._title = QLabel("Tactical Dashboard")
        self._title.setStyleSheet("font-size: 20px; font-weight: 600;")
        outer.addWidget(self._title)

        self._gauges = QGridLayout()
        self._gauges.setSpacing(10)
        outer.addLayout(self._gauges)

        self._dials_layout = QGridLayout()
        outer.addLayout(self._dials_layout)

        self._efficiency = ChartPanel(
            "Home vs Away efficiency", subtitle="goals per match",
            x_axis="bucket", y_axis="goals/match",
        )
        outer.addWidget(self._efficiency, 1)

        self._formation = _placeholder("Formation data unavailable in this build (§15.4 partial).")
        outer.addWidget(self._formation)

        self.refresh()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def refresh(self) -> None:
        self.set_state("loading")
        self._clear_layout(self._gauges)
        self._clear_layout(self._dials_layout)

        overview_df = self.context.cache.load_latest("season_overview")
        if overview_df is None or overview_df.empty:
            self._gauges.addWidget(_placeholder("Import a SEASON_OVERVIEW CSV to view tactics."), 0, 0)
            self._efficiency.set_series([])
            self.set_state("empty")
            return
        overview = SeasonOverview.from_row(overview_df.iloc[0])
        profile = team_ratings_profile(overview)

        gauge_layout = [
            ("Overall", profile["overall"]),
            ("Attack", profile["attack"]),
            ("Midfield", profile["midfield"]),
            ("Defense", profile["defense"]),
            ("Matchday OVR", profile["matchday_overall"]),
            ("Matchday ATT", profile["matchday_attack"]),
            ("Matchday MID", profile["matchday_midfield"]),
            ("Matchday DEF", profile["matchday_defense"]),
        ]
        for i, (label, val) in enumerate(gauge_layout):
            row, col = divmod(i, 4)
            text = "—" if val is None else str(val)
            self._gauges.addWidget(KpiTile(label, text), row, col)

        dial_specs = [
            ("Buildup play", profile["buildupplay"]),
            ("Defensive depth", profile["defensivedepth"]),
        ]
        for i, (label, val) in enumerate(dial_specs):
            text = "—" if val is None else f"{val} / 100"
            self._dials_layout.addWidget(KpiTile(label, text), 0, i)

        # Try to derive home/away efficiency from STANDINGS for the user team.
        standings_df = self.context.cache.load_latest("standings")
        eff = None
        if standings_df is not None and not standings_df.empty:
            user_rows = standings_df[standings_df["teamid"] == overview.user_teamid]
            if not user_rows.empty:
                row = StandingsRow.from_row(user_rows.iloc[0])
                eff = home_away_efficiency(row)
        if eff is None:
            # synthesize from SEASON_OVERVIEW columns
            row = StandingsRow(
                export_date=overview.export_date,
                leagueid=overview.leagueid, leaguename=overview.leaguename,
                teamid=overview.user_teamid, teamname=overview.user_teamname,
                currenttableposition=overview.currenttableposition,
                previousyeartableposition=overview.previousyeartableposition,
                points=overview.points, nummatchesplayed=overview.nummatchesplayed,
                homewins=overview.homewins, homedraws=overview.homedraws,
                homelosses=overview.homelosses,
                awaywins=overview.awaywins, awaydraws=overview.awaydraws,
                awaylosses=overview.awaylosses,
                homegf=overview.homegf, homega=overview.homega,
                awaygf=overview.awaygf, awayga=overview.awayga,
                teamform=overview.teamform, teamlongform=overview.teamlongform,
                lastgameresult=overview.lastgameresult,
                unbeatenleague=overview.unbeatenleague,
                champion=overview.champion,
                team_overallrating=overview.team_overallrating,
            )
            eff = home_away_efficiency(row)

        self._efficiency.set_series([
            Series("GF/match", x=[0, 1],
                   y=[eff["home_gf_per_match"], eff["away_gf_per_match"]],
                   kind="bar", color="#5ad19a"),
            Series("GA/match", x=[0.4, 1.4],
                   y=[eff["home_ga_per_match"], eff["away_ga_per_match"]],
                   kind="bar", color="#ef6f6f", extra={"width": 0.35}),
        ])
        self.set_state("ready")
