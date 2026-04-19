"""Tactical Dashboard page (PT §12.2 / §9.6) — Sprint 5.5 redesign.

Wires the existing analytics into the new chart primitives:
- 4-col rating tiles (overall / attack / midfield / defense),
- ``Pitch`` widget with a placeholder formation when probe data is partial,
- ``Dial`` ring widgets for tactical knobs,
- ``BarRow`` stack for home/away efficiency.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.analytics.tactics import home_away_efficiency, team_ratings_profile
from app.domain.season import SeasonOverview
from app.domain.standings import StandingsRow
from app.services.app_context import AppContext
from app.ui.charts.bar_row import BarRow
from app.ui.charts.dial import Dial
from app.ui.charts.pitch import Pitch
from app.ui.components import Card, FourCol, SectionTitle, TwoCol
from app.ui.pages._base import PageBase


_RATING_TILES = (
    ("Overall", "overall", "accent"),
    ("Attack", "attack", "bad"),
    ("Midfield", "midfield", "ok"),
    ("Defense", "defense", "accent_2"),
)


def _rating_tile(label: str, value: int | None, color_token: str) -> Card:
    card = Card()
    lbl = QLabel(label)
    lbl.setObjectName("card-title")
    card.add_widget(lbl)
    val = QLabel("—" if value is None else str(value))
    val.setObjectName("card-value")
    val.setProperty("tone", color_token)
    card.add_widget(val)
    return card


class TacticsPage(PageBase):
    title = "Tactics"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        outer.addWidget(SectionTitle("Tactical Dashboard"))

        self._tiles_row = FourCol()
        outer.addWidget(self._tiles_row)

        body = TwoCol()

        # Left: pitch
        pitch_card = Card(title="Starting XI")
        self._pitch_sub = QLabel("formation data unavailable in this build (§15.4 partial)")
        self._pitch_sub.setObjectName("card-subtitle")
        pitch_card.add_widget(self._pitch_sub)
        self._pitch = Pitch()
        pitch_card.add_widget(self._pitch, 1)
        body.add_widget(pitch_card)

        # Right: dials + efficiency
        right_card = Card(title="Tactical dials")
        self._dials_host = QWidget()
        self._dials_lyt = QVBoxLayout(self._dials_host)
        self._dials_lyt.setContentsMargins(0, 0, 0, 0)
        self._dials_lyt.setSpacing(8)
        right_card.add_widget(self._dials_host)

        eff_title = QLabel("Home vs Away efficiency")
        eff_title.setObjectName("card-title")
        right_card.add_widget(eff_title)
        self._eff_host = QWidget()
        self._eff_lyt = QVBoxLayout(self._eff_host)
        self._eff_lyt.setContentsMargins(0, 0, 0, 0)
        self._eff_lyt.setSpacing(4)
        right_card.add_widget(self._eff_host)
        body.add_widget(right_card)

        outer.addWidget(body, 1)

        self.refresh()

    # --- helpers ------------------------------------------------------------

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _rebuild_tiles(self, profile: dict | None) -> None:
        host_layout = self._tiles_row._layout  # internal QHBoxLayout
        self._clear_layout(host_layout)
        for label, key, color_token in _RATING_TILES:
            value = profile.get(key) if profile else None
            host_layout.addWidget(_rating_tile(label, value, color_token))

    def _dial_row(self, label: str, value: int | None, color_token: str, hint: str) -> QFrame:
        wrap = QFrame()
        lyt = QHBoxLayout(wrap)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(12)
        dial = Dial(value=float(value or 0), max_value=100.0, color_token=color_token)
        dial.setMinimumSize(64, 64)
        dial.setMaximumSize(64, 64)
        lyt.addWidget(dial)
        meta = QVBoxLayout()
        lab = QLabel(label)
        lab.setObjectName("card-title")
        sub = QLabel(hint)
        sub.setObjectName("card-subtitle")
        meta.addWidget(lab)
        meta.addWidget(sub)
        meta.addStretch(1)
        lyt.addLayout(meta, 1)
        return wrap

    # --- main refresh -------------------------------------------------------

    def refresh(self) -> None:
        self.set_state("loading")
        self._clear_layout(self._dials_lyt)
        self._clear_layout(self._eff_lyt)

        overview_df = self.context.cache.load_latest("season_overview")
        if overview_df is None or overview_df.empty:
            self._rebuild_tiles(None)
            empty = QLabel("Import a SEASON_OVERVIEW CSV to view tactics.")
            empty.setObjectName("card-subtitle")
            self._eff_lyt.addWidget(empty)
            self.set_state("empty")
            return
        overview = SeasonOverview.from_row(overview_df.iloc[0])
        profile = team_ratings_profile(overview)
        self._rebuild_tiles(profile)

        # Dials
        dial_specs = [
            ("Buildup play", profile.get("buildupplay"), "accent", "0–100"),
            ("Defensive depth", profile.get("defensivedepth"), "ok", "0–100"),
        ]
        for label, val, token, hint in dial_specs:
            self._dials_lyt.addWidget(self._dial_row(label, val, token, hint))

        # Home vs Away efficiency.
        standings_df = self.context.cache.load_latest("standings")
        eff = None
        if standings_df is not None and not standings_df.empty:
            user_rows = standings_df[standings_df["teamid"] == overview.user_teamid]
            if not user_rows.empty:
                row = StandingsRow.from_row(user_rows.iloc[0])
                eff = home_away_efficiency(row)
        if eff is None:
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

        eff_specs = (
            ("GF/match · Home", eff["home_gf_per_match"], "ok"),
            ("GF/match · Away", eff["away_gf_per_match"], "ok"),
            ("GA/match · Home", eff["home_ga_per_match"], "bad"),
            ("GA/match · Away", eff["away_ga_per_match"], "bad"),
        )
        for label, val, token in eff_specs:
            try:
                v = float(val or 0.0)
            except (TypeError, ValueError):
                v = 0.0
            self._eff_lyt.addWidget(BarRow(label, v, max_value=4.0,
                                           color_token=token, value_str=f"{v:.2f}"))
        self.set_state("ready")
