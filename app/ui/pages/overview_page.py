"""Season Overview page (PT §12.2).

Hero header (club + season + league + position) and a KPI grid bound to the
latest SEASON_OVERVIEW snapshot. Sparklines per KPI render only when ≥2
SEASON_OVERVIEW snapshots are present in the cache.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from app.analytics.form import decode_team_form
from app.domain.season import SeasonOverview
from app.services.app_context import AppContext
from app.ui.pages._base import PageBase
from app.ui.widgets.sparkline import Sparkline
from app.ui.widgets.stat_card import StatCard


@dataclass
class OverviewVM:
    title: str
    subtitle: str
    kpis: list[tuple[str, str, str | None, list[float] | None]]
    objective_text: str


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
    recent_form = " ".join(short[-5:]) if short else "—"

    pos = overview.currenttableposition
    obj_done = overview.hasachievedobjective
    obj_diff = overview.actualvsexpectations
    if obj_done is None:
        objective_text = "Objective: n/a"
    else:
        status = "ACHIEVED" if obj_done else "in progress"
        delta = "" if obj_diff in (None, 0) else f" (Δ {obj_diff:+d})"
        objective_text = f"Objective: {status}{delta}"

    kpis: list[tuple[str, str, str | None, list[float] | None]] = [
        ("Points", str(overview.points), f"{overview.nummatchesplayed} played", trend("points")),
        ("Wins", str(wins), None, None),
        ("Draws", str(draws), None, None),
        ("Losses", str(losses), None, None),
        ("Goals for", str(gf), None, None),
        ("Goals against", str(ga), None, None),
        ("Goal diff", f"{gd:+d}", None, None),
        ("Recent form", recent_form, "(last 5)", None),
        ("Objective", objective_text, None, None),
    ]

    title = overview.user_teamname or f"Team {overview.user_teamid}"
    subtitle_parts = [
        f"Season {overview.season_year}",
        overview.leaguename or f"League {overview.leagueid}",
    ]
    if pos is not None:
        subtitle_parts.append(f"position #{pos}")
    return OverviewVM(
        title=title,
        subtitle=" • ".join(subtitle_parts),
        kpis=kpis,
        objective_text=objective_text,
    )


class OverviewPage(PageBase):
    title = "Overview"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(12)

        self._title_lbl = QLabel("No data imported")
        self._title_lbl.setStyleSheet("font-size: 22px; font-weight: 600;")
        self._subtitle_lbl = QLabel("")
        self._subtitle_lbl.setObjectName("card-subtitle")

        self._layout.addWidget(self._title_lbl)
        self._layout.addWidget(self._subtitle_lbl)

        self._grid_container = QGridLayout()
        self._grid_container.setSpacing(12)
        self._layout.addLayout(self._grid_container)
        self._layout.addStretch(1)

        self.refresh()

    def _clear_grid(self) -> None:
        while self._grid_container.count():
            item = self._grid_container.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def refresh(self) -> None:
        self.set_state("loading")
        vm = build_overview_vm(self.context)
        self._clear_grid()
        if vm is None:
            self._title_lbl.setText("No data imported")
            self._subtitle_lbl.setText("Import a SEASON_OVERVIEW CSV to see KPIs.")
            self.set_state("empty")
            return
        self._title_lbl.setText(vm.title)
        self._subtitle_lbl.setText(vm.subtitle)
        for i, (label, value, sub, trend_vals) in enumerate(vm.kpis):
            row, col = divmod(i, 4)
            spark = Sparkline(trend_vals) if trend_vals else None
            self._grid_container.addWidget(
                StatCard(label, value, subtitle=sub, trend=spark), row, col
            )
        self.set_state("ready")
