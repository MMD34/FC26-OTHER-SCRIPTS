"""Season Analytics page (PT §12.2) — Sprint 5.7 redesign.

Aggregates the design-system primitives shipped in earlier sprints:
two ``LineChart`` cards (points + ranking progression), a ``BarRow``
home/away split, a tokenized form-curve strip, and three KPI cards for
streak/unbeaten/longest-W. Data binding (``build_analytics_vm``) is
unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.analytics.form import current_streak, decode_team_form, longest_unbeaten
from app.analytics.standings import points_progression
from app.domain.season import SeasonOverview
from app.domain.standings import StandingsRow
from app.services.app_context import AppContext
from app.ui.charts.bar_row import BarRow
from app.ui.charts.line_chart import LineChart
from app.ui.components import Card, SectionTitle, ThreeCol, TwoCol
from app.ui.design.theme_manager import ThemeManager
from app.ui.pages._base import PageBase


@dataclass
class AnalyticsVM:
    points_progression: list[tuple[str, int]]
    ranking_progression: list[tuple[str, int]]
    home_away_split: dict[str, int]
    form_curve: list[int]  # numeric encoding of W=3/D=1/L=0
    streak_label: str
    streak_value: str
    unbeaten: int
    longest_w: int


def _form_curve_numeric(form_str: str | None) -> list[int]:
    decoded = decode_team_form(form_str)
    mapping = {"W": 3, "D": 1, "L": 0}
    return [mapping[c] for c in decoded]


def _longest_w(decoded: str) -> int:
    best = run = 0
    for c in decoded:
        if c == "W":
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def build_analytics_vm(context: AppContext) -> Optional[AnalyticsVM]:
    overview_df = context.cache.load_latest("season_overview")
    if overview_df is None or overview_df.empty:
        return None
    overview = SeasonOverview.from_row(overview_df.iloc[0])

    pts_pairs: list[tuple[str, int]] = []
    rank_pairs: list[tuple[str, int]] = []
    snapshots = context.cache.list_snapshots("season_overview")
    if len(snapshots) >= 2:
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

    return AnalyticsVM(
        points_progression=pts_pairs,
        ranking_progression=rank_pairs,
        home_away_split=home_away,
        form_curve=form_curve,
        streak_label=streak.kind or "—",
        streak_value=str(streak.length),
        unbeaten=unbeaten,
        longest_w=_longest_w(decoded),
    )


def _kpi_card(label: str, value: str) -> Card:
    card = Card()
    lbl = QLabel(label)
    lbl.setObjectName("card-title")
    card.add_widget(lbl)
    val = QLabel(value)
    val.setObjectName("card-value")
    card.add_widget(val)
    return card


def _form_curve_strip(values: list[int]) -> QWidget:
    """Render the W/D/L bars as fixed-height tokenized columns."""
    palette = ThemeManager.instance().current()
    color_for = {3: palette.ok, 1: palette.warn, 0: palette.bad}
    host = QFrame()
    host.setObjectName("form-strip")
    host.setMinimumHeight(60)
    lyt = QHBoxLayout(host)
    lyt.setContentsMargins(0, 0, 0, 0)
    lyt.setSpacing(3)
    if not values:
        empty = QLabel("No form data")
        empty.setObjectName("card-subtitle")
        lyt.addWidget(empty)
        return host
    for v in values:
        col = QFrame()
        col.setStyleSheet(
            f"background-color: {color_for.get(v, palette.dim)};"
            f" border-radius: 2px;"
        )
        col.setMinimumWidth(6)
        # Height proxy: W=full, D=half, L=stub.
        ratio = 1.0 if v == 3 else (0.55 if v == 1 else 0.2)
        col.setMinimumHeight(int(40 * ratio))
        col.setMaximumHeight(int(40 * ratio))
        lyt.addWidget(col, 0, Qt.AlignmentFlag.AlignBottom)
    lyt.addStretch(1)
    return host


class AnalyticsPage(PageBase):
    title = "Analytics"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        outer.addWidget(SectionTitle("Season Analytics"))

        # Row 1: points + ranking line charts
        line_row = TwoCol()
        self._pts_card = Card(title="Points progression")
        self._pts_sub = QLabel("needs ≥2 snapshots")
        self._pts_sub.setObjectName("card-subtitle")
        self._pts_card.add_widget(self._pts_sub)
        self._pts_chart = LineChart(x_axis="snapshot", y_axis="pts")
        self._pts_card.add_widget(self._pts_chart, 1)
        line_row.add_widget(self._pts_card)

        self._rank_card = Card(title="Ranking evolution")
        self._rank_sub = QLabel("lower is better · axis inverted")
        self._rank_sub.setObjectName("card-subtitle")
        self._rank_card.add_widget(self._rank_sub)
        self._rank_chart = LineChart(x_axis="snapshot", y_axis="position", invert_y=True)
        self._rank_card.add_widget(self._rank_chart, 1)
        line_row.add_widget(self._rank_card)
        outer.addWidget(line_row)

        # Row 2: home/away bars + form curve
        bars_row = TwoCol()
        self._ha_card = Card(title="Home vs Away (GF / GA)")
        self._ha_host = QWidget()
        self._ha_lyt = QVBoxLayout(self._ha_host)
        self._ha_lyt.setContentsMargins(0, 0, 0, 0)
        self._ha_lyt.setSpacing(4)
        self._ha_card.add_widget(self._ha_host)
        bars_row.add_widget(self._ha_card)

        self._form_card = Card(title="Form curve")
        self._form_sub = QLabel("W = 3, D = 1, L = 0")
        self._form_sub.setObjectName("card-subtitle")
        self._form_card.add_widget(self._form_sub)
        self._form_host_wrap = QWidget()
        self._form_host_lyt = QVBoxLayout(self._form_host_wrap)
        self._form_host_lyt.setContentsMargins(0, 0, 0, 0)
        self._form_card.add_widget(self._form_host_wrap)
        bars_row.add_widget(self._form_card)
        outer.addWidget(bars_row)

        # Row 3: streak / unbeaten / longest-W KPI cards
        self._kpis_row = ThreeCol()
        outer.addWidget(self._kpis_row)
        outer.addStretch(1)

        self.refresh()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _set_kpis(self, vm: AnalyticsVM | None) -> None:
        layout = self._kpis_row._layout
        self._clear_layout(layout)
        if vm is None:
            return
        layout.addWidget(_kpi_card("Current streak", f"{vm.streak_value} {vm.streak_label}"))
        layout.addWidget(_kpi_card("Unbeaten run", str(vm.unbeaten)))
        layout.addWidget(_kpi_card("Longest W run", str(vm.longest_w)))

    def refresh(self) -> None:
        self.set_state("loading")
        self._pts_chart.clear()
        self._rank_chart.clear()
        self._clear_layout(self._ha_lyt)
        self._clear_layout(self._form_host_lyt)

        vm = build_analytics_vm(self.context)
        if vm is None:
            self._pts_sub.setText("Import a SEASON_OVERVIEW CSV to see analytics.")
            self._set_kpis(None)
            self.set_state("empty")
            return

        # Points
        if vm.points_progression:
            xs = [float(i) for i in range(len(vm.points_progression))]
            ys = [float(v) for _, v in vm.points_progression]
            self._pts_chart.add_series("points", xs, ys, color_token="accent", width=2.0)
            self._pts_sub.setText(" → ".join(d for d, _ in vm.points_progression))
        else:
            self._pts_sub.setText("needs ≥2 snapshots")

        # Ranking
        if vm.ranking_progression:
            xs = [float(i) for i in range(len(vm.ranking_progression))]
            ys = [float(v) for _, v in vm.ranking_progression]
            self._rank_chart.add_series("rank", xs, ys, color_token="warn", width=2.0)
            self._rank_sub.setText("lower is better · axis inverted")
        else:
            self._rank_sub.setText("needs ≥2 snapshots")

        # Home/Away bars
        ha = vm.home_away_split
        max_g = float(max(ha.values()) or 1)
        for label, key, token in (
            ("Home GF", "home_gf", "ok"),
            ("Home GA", "home_ga", "bad"),
            ("Away GF", "away_gf", "ok"),
            ("Away GA", "away_ga", "bad"),
        ):
            self._ha_lyt.addWidget(BarRow(
                label, float(ha[key]), max_value=max_g,
                color_token=token, value_str=str(ha[key]),
            ))

        # Form strip
        self._form_host_lyt.addWidget(_form_curve_strip(vm.form_curve))

        # KPIs
        self._set_kpis(vm)
        self.set_state("ready")
