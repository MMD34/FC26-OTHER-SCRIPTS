"""Wonderkid Scout Hub page (PT §11) — Sprint 5.4 redesign.

Filter chips drive a token-styled ``ScatterChart`` (age × potential, colored
by position group) plus a leaderboard list and a table; the right-hand
``DrawerPanel`` reuses the Squad-page attribute layout so the two pages
share one player view component.
"""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSplitter, QVBoxLayout

from app.analytics.wonderkids import filter_wonderkids, origin_label, position_group
from app.core.constants import DEFAULT_WONDERKID_MAX_AGE, DEFAULT_WONDERKID_POTENTIAL
from app.services.app_context import AppContext
from app.ui.charts.scatter import ScatterChart
from app.ui.components import (
    AttributeRow,
    Card,
    DrawerPanel,
    FilterChip,
    Legend,
    SectionTitle,
)
from app.ui.design.theme_manager import ThemeManager
from app.ui.pages._base import PageBase
from app.ui.widgets.data_table import DataTable

_TABLE_COLS = (
    "display_name", "age", "potential", "overallrating",
    "preferredposition1", "teamname", "leaguename", "origin",
)

_GROUP_TOKENS = {"GK": "warn", "DEF": "accent", "MID": "ok", "ATT": "bad"}

_FACE_AXES = (
    ("pacdiv", "Pace"),
    ("shohan", "Shooting"),
    ("paskic", "Passing"),
    ("driref", "Dribbling"),
    ("defspe", "Defending"),
    ("phypos", "Physical"),
)


class WonderkidsPage(PageBase):
    title = "Wonderkids"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        outer.addWidget(SectionTitle("Wonderkid Scout Hub"))

        # Filters: All / Real / Regens.
        filter_row = QFrame()
        filter_row.setObjectName("filters")
        flyt = QHBoxLayout(filter_row)
        flyt.setContentsMargins(0, 0, 0, 0)
        flyt.setSpacing(8)
        self._origin_chips: dict[str, FilterChip] = {}
        for label in ("All", "Real", "Regens"):
            chip = FilterChip(label)
            chip.setChecked(label == "All")
            chip.clicked.connect(lambda _c=False, n=label: self._on_origin_chip(n))
            flyt.addWidget(chip)
            self._origin_chips[label] = chip
        flyt.addStretch(1)
        palette = ThemeManager.instance().current()
        flyt.addWidget(Legend({
            "GK": palette.warn, "DEF": palette.accent,
            "MID": palette.ok, "ATT": palette.bad,
        }))
        outer.addWidget(filter_row)

        # Scatter card
        scatter_card = Card(title="Age × Potential")
        scatter_sub = QLabel("colored by position group")
        scatter_sub.setObjectName("card-subtitle")
        scatter_card.add_widget(scatter_sub)
        self._scatter = ScatterChart(x_axis="age", y_axis="potential")
        scatter_card.add_widget(self._scatter, 1)
        outer.addWidget(scatter_card)

        # Table + drawer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        table_card = Card(title="Wonderkid table")
        self._table = DataTable(pd.DataFrame(), list(_TABLE_COLS))
        self._table.clicked.connect(self._on_row_clicked)
        table_card.add_widget(self._table, 1)
        splitter.addWidget(table_card)

        self._drawer = DrawerPanel(title="Wonderkid detail")
        self._drawer_empty_lbl = QLabel("Select a row to inspect a player.")
        self._drawer_empty_lbl.setObjectName("card-subtitle")
        self._drawer.add_widget(self._drawer_empty_lbl)
        splitter.addWidget(self._drawer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)

        self._df: pd.DataFrame = pd.DataFrame()
        self._origin_filter = "All"
        self.refresh()

    def _on_origin_chip(self, label: str) -> None:
        self._origin_filter = label
        for n, chip in self._origin_chips.items():
            chip.setChecked(n == label)
        self.refresh()

    def _on_row_clicked(self, index) -> None:
        if self._df.empty:
            return
        row = index.row()
        if 0 <= row < len(self._df):
            self._show_player(self._df.iloc[row])

    def _clear_drawer(self) -> None:
        layout = self._drawer.body_layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _show_player(self, player: pd.Series) -> None:
        self._clear_drawer()
        name = str(player.get("display_name") or player.get("playerid") or "—")
        title = QLabel(name)
        title.setObjectName("drawer-title")
        self._drawer.add_widget(title)

        meta_parts: list[str] = []
        team = player.get("teamname")
        if pd.notna(team):
            meta_parts.append(str(team))
        age = player.get("age")
        if pd.notna(age):
            meta_parts.append(f"{int(age)} y/o")
        meta_parts.append(position_group(player.get("preferredposition1")) or "—")
        meta = QLabel(" · ".join(meta_parts))
        meta.setObjectName("card-subtitle")
        self._drawer.add_widget(meta)

        section = QLabel("Attributes")
        section.setObjectName("card-title")
        self._drawer.add_widget(section)
        for axis, label in _FACE_AXES:
            v = player.get(axis)
            try:
                val = int(v) if pd.notna(v) else 0
            except (TypeError, ValueError):
                val = 0
            self._drawer.add_widget(AttributeRow(label, val))

    def refresh(self) -> None:
        self.set_state("loading")
        df = self.context.cache.load_latest("wonderkids")
        if df is None or df.empty:
            df = self.context.cache.load_latest("players_snapshot")
        if df is None or df.empty:
            self._df = pd.DataFrame()
            self._table.set_dataframe(pd.DataFrame(), list(_TABLE_COLS))
            self._scatter.clear()
            self.set_state("empty")
            return

        wk = filter_wonderkids(
            df,
            max_age=DEFAULT_WONDERKID_MAX_AGE,
            min_potential=DEFAULT_WONDERKID_POTENTIAL,
        ).copy()
        if "playerid" in wk.columns:
            wk["origin"] = wk["playerid"].map(origin_label)

        if self._origin_filter != "All" and "origin" in wk.columns:
            target = self._origin_filter.lower().rstrip("s")  # "Regens" -> "regen"
            wk = wk[wk["origin"].fillna("").str.lower().str.startswith(target)]

        self._df = wk.reset_index(drop=True)
        self._table.set_dataframe(self._df, list(_TABLE_COLS))

        self._scatter.clear()
        if "preferredposition1" in wk.columns:
            wk["_group"] = wk["preferredposition1"].map(position_group)
        else:
            wk["_group"] = None
        for group, color_token in _GROUP_TOKENS.items():
            sub = wk[wk["_group"] == group]
            if sub.empty:
                continue
            self._scatter.add_series(
                group,
                x=sub["age"].fillna(0).astype(float).tolist(),
                y=sub["potential"].fillna(0).astype(float).tolist(),
                color_token=color_token,
                size=9,
            )
        self.set_state("ready")
