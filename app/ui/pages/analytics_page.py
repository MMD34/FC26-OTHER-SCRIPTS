"""Season Analytics page (PT §12.2): grid of charts driven by cache state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from app.analytics.form import current_streak, decode_team_form, longest_unbeaten
from app.analytics.standings import points_progression
from app.domain.season import SeasonOverview
from app.domain.standings import StandingsRow
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase
from app.ui.widgets.chart_panel import ChartPanel, Series


@dataclass
class AnalyticsVM:
    points_progression: list[tuple[str, int]]
    ranking_progression: list[tuple[str, int]]
    home_away_split: dict[str, int]
    form_curve: list[int]  # numeric encoding of W=3/D=1/L=0
    streak_text: str


def _form_curve_numeric(form_str: str | None) -> list[int]:
    decoded = decode_team_form(form_str)
    mapping = {"W": 3, "D": 1, "L": 0}
    return [mapping[c] for c in decoded]


def build_analytics_vm(context: AppContext) -> Optional[AnalyticsVM]:
    overview_df = context.cache.load_latest("season_overview")
    if overview_df is None or overview_df.empty:
        return None
    overview = SeasonOverview.from_row(overview_df.iloc[0])

    pts_pairs: list[tuple[str, int]] = []
    rank_pairs: list[tuple[str, int]] = []
    snapshots = context.cache.list_snapshots("season_overview")
    if len(snapshots) >= 2:
        # Use StandingsRow shape via SEASON_OVERVIEW (has compatible columns).
        rows: list[StandingsRow] = []
        for snap in snapshots:
            sf = context.cache.load_snapshot("season_overview", snap)
            if sf is None or sf.empty:
                continue
            r = sf.iloc[0]
            rows.append(StandingsRow(
                export_date=str(r["export_date"]),
                leagueid=int(r["leagueid"]),
                leaguename=None,
                teamid=int(r["user_teamid"]),
                teamname=None,
                currenttableposition=int(r["currenttableposition"]) if pd.notna(r.get("currenttableposition")) else None,
                previousyeartableposition=None,
                points=int(r["points"]),
                nummatchesplayed=int(r["nummatchesplayed"]),
                homewins=None, homedraws=None, homelosses=None,
                awaywins=None, awaydraws=None, awaylosses=None,
                homegf=None, homega=None, awaygf=None, awayga=None,
                teamform=None, teamlongform=None, lastgameresult=None,
                unbeatenleague=None, champion=None, team_overallrating=None,
            ))
        progression = points_progression(rows)
        pts_pairs = [(idx, int(val)) for idx, val in progression.items()]
        for r in rows:
            if r.currenttableposition is not None:
                rank_pairs.append((r.export_date, int(r.currenttableposition)))
        rank_pairs.sort(key=lambda p: p[0])

    home_away = {
        "home_gf": int(overview.homegf or 0), "home_ga": int(overview.homega or 0),
        "away_gf": int(overview.awaygf or 0), "away_ga": int(overview.awayga or 0),
    }

    form_curve = _form_curve_numeric(overview.teamlongform or overview.teamform)
    decoded = decode_team_form(overview.teamlongform or overview.teamform)
    streak = current_streak(decoded)
    unbeaten = (
        int(overview.unbeatenleague) if overview.unbeatenleague is not None
        else longest_unbeaten(decoded)
    )
    streak_kind = streak.kind or "—"
    streak_text = (
        f"Current streak: {streak.length} {streak_kind} • "
        f"Unbeaten (league): {unbeaten}"
    )

    return AnalyticsVM(
        points_progression=pts_pairs,
        ranking_progression=rank_pairs,
        home_away_split=home_away,
        form_curve=form_curve,
        streak_text=streak_text,
    )


class AnalyticsPage(PageBase):
    title = "Analytics"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        self._title = QLabel("Season Analytics")
        self._title.setStyleSheet("font-size: 20px; font-weight: 600;")
        outer.addWidget(self._title)

        self._grid = QGridLayout()
        self._grid.setSpacing(12)
        outer.addLayout(self._grid, 1)

        self._streak_lbl = QLabel("")
        self._streak_lbl.setObjectName("card-subtitle")
        outer.addWidget(self._streak_lbl)

        self.refresh()

    def _clear_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def refresh(self) -> None:
        self.set_state("loading")
        self._clear_grid()
        vm = build_analytics_vm(self.context)
        if vm is None:
            self._streak_lbl.setText("Import a SEASON_OVERVIEW CSV to see analytics.")
            self.set_state("empty")
            return

        if vm.points_progression:
            xs = list(range(len(vm.points_progression)))
            ys = [v for _, v in vm.points_progression]
            self._grid.addWidget(ChartPanel(
                "Points progression", subtitle=" → ".join(d for d, _ in vm.points_progression),
                x_axis="snapshot", y_axis="pts",
                series=[Series("pts", x=xs, y=ys, kind="line", color="#7c9cff")],
            ), 0, 0)
        else:
            self._grid.addWidget(ChartPanel(
                "Points progression", subtitle="needs ≥2 snapshots",
                x_axis="", y_axis="",
            ), 0, 0)

        if vm.ranking_progression:
            xs = list(range(len(vm.ranking_progression)))
            ys = [v for _, v in vm.ranking_progression]
            self._grid.addWidget(ChartPanel(
                "Ranking evolution", subtitle="lower is better",
                x_axis="snapshot", y_axis="position",
                series=[Series("rank", x=xs, y=ys, kind="line", color="#f3c969")],
                invert_y=True,
            ), 0, 1)
        else:
            self._grid.addWidget(ChartPanel(
                "Ranking evolution", subtitle="needs ≥2 snapshots",
                x_axis="", y_axis="",
            ), 0, 1)

        ha = vm.home_away_split
        self._grid.addWidget(ChartPanel(
            "Home vs Away (GF / GA)", subtitle="latest snapshot",
            x_axis="bucket", y_axis="goals",
            series=[
                Series("GF", x=[0, 1], y=[ha["home_gf"], ha["away_gf"]], kind="bar", color="#5ad19a"),
                Series("GA", x=[0.4, 1.4], y=[ha["home_ga"], ha["away_ga"]], kind="bar", color="#ef6f6f", extra={"width": 0.35}),
            ],
        ), 1, 0)

        self._grid.addWidget(ChartPanel(
            "Form curve", subtitle="W=3 / D=1 / L=0",
            x_axis="match", y_axis="result",
            series=[Series(
                "form", x=list(range(len(vm.form_curve))),
                y=vm.form_curve, kind="line", color="#7c9cff",
            )] if vm.form_curve else [],
        ), 1, 1)

        self._streak_lbl.setText(vm.streak_text)
        self.set_state("ready")
