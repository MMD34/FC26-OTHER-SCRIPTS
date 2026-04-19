"""Season Overview page (PT §12.2).

Sprint 5.1 redesign: hero card (crest, title, form dots, league position) +
6-col KPI grid with feature tile + sparklines. Data binding (build_overview_vm)
is unchanged — the page only swaps its view layer for the redesign primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import QGridLayout, QVBoxLayout

from app.analytics.form import decode_team_form
from app.domain.season import SeasonOverview
from app.services.app_context import AppContext
from app.ui.charts.sparkline import Sparkline
from app.ui.components import Hero, SectionTitle
from app.ui.pages._base import PageBase
from app.ui.widgets.stat_card import StatCard


@dataclass
class OverviewVM:
    title: str
    subtitle: str
    crest: str
    form: list[str]
    position: int | None
    league_size: int | None
    objective: str | None
    kpis: list[tuple[str, str, str | None, list[float] | None]]


def _kpi_history(history: pd.DataFrame, column: str) -> list[float]:
    if history.empty or column not in history.columns:
        return []
    series = pd.to_numeric(history[column], errors="coerce").dropna()
    return [float(v) for v in series.tolist()]


def build_overview_vm(context: AppContext) -> Optional[OverviewVM]:
    df = context.cache.load_latest("season_overview")
    if df is None or df.empty:
        return None
    overview = SeasonOverview.from_row(df.iloc[0])

    snapshots = context.cache.list_snapshots("season_overview")
    history = pd.DataFrame()
    if len(snapshots) >= 2:
        frames = []
        for snap in snapshots:
            sf = context.cache.load_snapshot("season_overview", snap)
            if sf is not None and not sf.empty:
                frames.append(sf.iloc[[0]])
        if frames:
            history = pd.concat(frames, ignore_index=True)

    def trend(col: str) -> list[float] | None:
        vals = _kpi_history(history, col)
        return vals if len(vals) >= 2 else None

    gd = (overview.homegf or 0) + (overview.awaygf or 0) - (
        overview.homega or 0) - (overview.awayga or 0)
    wins = (overview.homewins or 0) + (overview.awaywins or 0)
    draws = (overview.homedraws or 0) + (overview.awaydraws or 0)
    losses = (overview.homelosses or 0) + (overview.awaylosses or 0)
    gf = (overview.homegf or 0) + (overview.awaygf or 0)
    ga = (overview.homega or 0) + (overview.awayga or 0)

    short = decode_team_form(overview.teamshortform or overview.teamform)
    form_recent = short[-5:] if short else []

    pos = overview.currenttableposition
    obj_done = overview.hasachievedobjective
    obj_diff = overview.actualvsexpectations
    if obj_done is None:
        objective = None
    else:
        status = "ACHIEVED" if obj_done else "in progress"
        delta = "" if obj_diff in (None, 0) else f" (Δ {obj_diff:+d})"
        objective = f"Objective · {status}{delta}"

    kpis: list[tuple[str, str, str | None, list[float] | None]] = [
        ("Points", str(overview.points), f"{overview.nummatchesplayed} played", trend("points")),
        ("Wins", str(wins), None, None),
        ("Draws", str(draws), None, None),
        ("Losses", str(losses), None, None),
        ("Goals for", str(gf), f"GA {ga}", None),
        ("Goal diff", f"{gd:+d}", None, None),
    ]

    title = overview.user_teamname or f"Team {overview.user_teamid}"
    crest = title
    subtitle_parts = [
        f"Season {overview.season_year}",
        overview.leaguename or f"League {overview.leagueid}",
    ]
    if overview.nummatchesplayed is not None:
        subtitle_parts.append(f"Matchday {overview.nummatchesplayed}")
    return OverviewVM(
        title=title,
        subtitle=" · ".join(subtitle_parts),
        crest=crest,
        form=form_recent,
        position=pos,
        league_size=None,
        objective=objective,
        kpis=kpis,
    )


class OverviewPage(PageBase):
    title = "Overview"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(14)

        self._heading = SectionTitle("Season Overview")
        self._layout.addWidget(self._heading)

        self._hero = Hero()
        self._layout.addWidget(self._hero)

        self._grid = QGridLayout()
        self._grid.setSpacing(12)
        self._layout.addLayout(self._grid)
        self._layout.addStretch(1)

        self.refresh()

    def _clear_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def refresh(self) -> None:
        self.set_state("loading")
        vm = build_overview_vm(self.context)
        self._clear_grid()
        if vm is None:
            self._hero.set_data(
                crest="—", title="No data imported",
                subtitle="Import a SEASON_OVERVIEW CSV to see KPIs.",
                form=None, position=None, league_size=None, objective=None,
            )
            self.set_state("empty")
            return
        self._hero.set_data(
            crest=vm.crest, title=vm.title, subtitle=vm.subtitle,
            form=vm.form, position=vm.position, league_size=vm.league_size,
            objective=vm.objective,
        )
        # 6-col KPI grid: feature tile (col 0) is wider via column span.
        for i, (label, value, sub, trend_vals) in enumerate(vm.kpis):
            spark = Sparkline(trend_vals) if trend_vals else None
            card = StatCard(label, value, subtitle=sub, trend=spark)
            if i == 0:
                self._grid.addWidget(card, 0, 0, 1, 2)
            else:
                self._grid.addWidget(card, 0, i + 1)
        self.set_state("ready")
