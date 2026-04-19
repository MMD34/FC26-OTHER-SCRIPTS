"""Transfer Planning page (PT §12.2 / §9.7) — Sprint 5.6 redesign.

Reuses Phase-4 chart primitives (``ScatterChart``, ``BarRow``) and the
design-system layout helpers. The four-tile KPI row matches the HTML
prototype, and the expiring/replacement split uses paired ``Card`` panels
plus the existing ``DataTable``. Data binding (cache + analytics calls)
is unchanged.
"""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout

from app.analytics.transfers import (
    aging_quadrant,
    expiring_contracts,
    positional_depth,
    replacement_candidates,
)
from app.domain.season import SeasonOverview
from app.services.app_context import AppContext
from app.ui.charts.bar_row import BarRow
from app.ui.charts.scatter import ScatterChart
from app.ui.components import Card, FourCol, SectionTitle, TwoCol
from app.ui.pages._base import PageBase
from app.ui.widgets.data_table import DataTable

_EXPIRING_COLS = ("display_name", "age", "preferredposition1",
                  "overallrating", "potential", "contractvaliduntil")
_REPLACEMENT_COLS = ("display_name", "age", "overallrating", "potential", "teamname")


def _kpi_card(label: str, value: str, sub: str = "", tone: str = "") -> Card:
    card = Card()
    lbl = QLabel(label)
    lbl.setObjectName("card-title")
    card.add_widget(lbl)
    val = QLabel(value)
    val.setObjectName("card-value")
    if tone:
        val.setProperty("tone", tone)
    card.add_widget(val)
    if sub:
        s = QLabel(sub)
        s.setObjectName("card-subtitle")
        card.add_widget(s)
    return card


class TransfersPage(PageBase):
    title = "Transfers"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        outer.addWidget(SectionTitle("Transfer Planning"))

        self._tiles_row = FourCol()
        outer.addWidget(self._tiles_row)

        # Aging quadrant + positional depth
        body = TwoCol()
        aging_card = Card(title="Aging quadrant")
        aging_sub = QLabel("age × overall rating")
        aging_sub.setObjectName("card-subtitle")
        aging_card.add_widget(aging_sub)
        self._aging = ScatterChart(x_axis="age", y_axis="OVR")
        aging_card.add_widget(self._aging, 1)
        body.add_widget(aging_card)

        depth_card = Card(title="Positional depth")
        depth_sub = QLabel("user team · squad breadth")
        depth_sub.setObjectName("card-subtitle")
        depth_card.add_widget(depth_sub)
        from PySide6.QtWidgets import QWidget
        self._depth_host = QWidget()
        self._depth_lyt = QVBoxLayout(self._depth_host)
        self._depth_lyt.setContentsMargins(0, 0, 0, 0)
        self._depth_lyt.setSpacing(4)
        depth_card.add_widget(self._depth_host)
        body.add_widget(depth_card)

        outer.addWidget(body)

        # Expiring + replacements split
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_card = Card(title="Expiring contracts")
        sub_lbl = QLabel("click a row → find replacements")
        sub_lbl.setObjectName("card-subtitle")
        left_card.add_widget(sub_lbl)
        self._expiring = DataTable(pd.DataFrame(), list(_EXPIRING_COLS))
        self._expiring.clicked.connect(self._on_expiring_clicked)
        left_card.add_widget(self._expiring, 1)
        splitter.addWidget(left_card)

        right_card = Card(title="Replacement candidates")
        self._rep_sub = QLabel("Select an expiring player to see candidates.")
        self._rep_sub.setObjectName("card-subtitle")
        right_card.add_widget(self._rep_sub)
        self._candidates = DataTable(pd.DataFrame(), list(_REPLACEMENT_COLS))
        right_card.add_widget(self._candidates, 1)
        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        self._players: pd.DataFrame = pd.DataFrame()
        self._expiring_df: pd.DataFrame = pd.DataFrame()
        self.refresh()

    # --- helpers ------------------------------------------------------------

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _set_tiles(self, incoming: int, expiring: int, players_total: int) -> None:
        host_layout = self._tiles_row._layout
        self._clear_layout(host_layout)
        host_layout.addWidget(_kpi_card("Incoming (this window)", str(incoming),
                                        "transfers in"))
        host_layout.addWidget(_kpi_card("Players analysed", str(players_total),
                                        "in cache"))
        host_layout.addWidget(_kpi_card("Expiring ≤ 12mo", str(expiring),
                                        "players at risk", tone="warn"))
        host_layout.addWidget(_kpi_card("Replacement pool", str(max(0, players_total - expiring)),
                                        "candidates"))

    def _on_expiring_clicked(self, index) -> None:
        if self._expiring_df.empty or self._players.empty:
            return
        row = index.row()
        if not (0 <= row < len(self._expiring_df)):
            return
        target = self._expiring_df.iloc[row]
        cands = replacement_candidates(self._players, target, top_n=10)
        self._rep_sub.setText(
            f"Replacements for {target.get('display_name', '?')} · "
            f"POS {target.get('preferredposition1')} · OVR {target.get('overallrating')}"
        )
        self._candidates.set_dataframe(cands.reset_index(drop=True), list(_REPLACEMENT_COLS))

    def refresh(self) -> None:
        self.set_state("loading")
        self._clear_layout(self._depth_lyt)

        overview_df = self.context.cache.load_latest("season_overview")
        players_df = self.context.cache.load_latest("players_snapshot")
        transfers_df = self.context.cache.load_latest("transfer_history")

        if players_df is None:
            self._players = pd.DataFrame()
            self._expiring_df = pd.DataFrame()
            self._aging.clear()
            self._expiring.set_dataframe(pd.DataFrame(), list(_EXPIRING_COLS))
            self._candidates.set_dataframe(pd.DataFrame(), list(_REPLACEMENT_COLS))
            self._set_tiles(0, 0, 0)
            self.set_state("empty")
            return
        self._players = players_df

        # Aging quadrant
        self._aging.clear()
        pts = aging_quadrant(players_df)
        if pts:
            self._aging.add_series(
                "players",
                x=[float(p.age) for p in pts],
                y=[float(p.overallrating) for p in pts],
                color_token="accent",
                size=6,
            )

        incoming_count = 0
        expiring_total = 0
        if overview_df is not None and not overview_df.empty:
            overview = SeasonOverview.from_row(overview_df.iloc[0])
            user_team = overview.user_teamid
            year = overview.season_year

            self._expiring_df = expiring_contracts(players_df, current_year=year).reset_index(drop=True)
            self._expiring.set_dataframe(self._expiring_df, list(_EXPIRING_COLS))
            expiring_total = len(self._expiring_df)

            depth = positional_depth(players_df, teamid=user_team)
            if not depth.empty:
                max_v = float(depth.max() or 1.0) or 1.0
                for code, count in depth.items():
                    self._depth_lyt.addWidget(BarRow(
                        f"POS {code}", float(count), max_value=max_v,
                        color_token="accent", value_str=str(int(count)),
                    ))

            if transfers_df is not None and "teamtoid" in transfers_df.columns:
                incoming_count = int((transfers_df["teamtoid"] == user_team).sum())
        else:
            self._expiring_df = pd.DataFrame()
            self._expiring.set_dataframe(pd.DataFrame(), list(_EXPIRING_COLS))

        self._set_tiles(incoming_count, expiring_total, len(players_df))
        self.set_state("ready")
