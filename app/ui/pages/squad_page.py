"""Squad Performance page (PT §12.2) — Sprint 5.3 redesign.

Replaces the PyQtGraph leaderboards with token-driven ``BarRow`` lists,
swaps the QDockWidget player view for the design-system ``DrawerPanel``
populated with ``AttributeRow`` mini-bars, and rebuilds the filter row
using ``FilterChip`` + a section title. Data binding (analytics calls
on the cache) is unchanged.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.analytics.squad import form_leaders, top_by_rating, top_scorers
from app.analytics.wonderkids import position_group
from app.services.app_context import AppContext
from app.ui.charts.bar_row import BarRow
from app.ui.components import (
    AttributeRow,
    Card,
    DrawerPanel,
    FilterChip,
    SectionTitle,
    ThreeCol,
)
from app.ui.pages._base import PageBase
from app.ui.widgets.data_table import DataTable

_LEADERBOARD_COLS = ("display_name", "teamname", "overallrating", "leaguegoals",
                     "leagueappearances", "form")

_FACE_AXES = (
    ("pacdiv", "Pace"),
    ("shohan", "Shooting"),
    ("paskic", "Passing"),
    ("driref", "Dribbling"),
    ("defspe", "Defending"),
    ("phypos", "Physical"),
)


def _bar_color(group: str) -> str:
    return {"GK": "warn", "DEF": "accent", "MID": "ok", "ATT": "bad"}.get(group, "accent")


def _populate_bar_card(card: Card, df: pd.DataFrame, value_col: str, color_token: str) -> None:
    # Clear previous body widgets (header is at index 0).
    while card.main_layout.count() > 1:
        item = card.main_layout.takeAt(1)
        w = item.widget()
        if w is not None:
            w.deleteLater()
    if df.empty or value_col not in df.columns:
        empty = QLabel("No data")
        empty.setObjectName("card-subtitle")
        card.add_widget(empty)
        return
    max_val = float(pd.to_numeric(df[value_col], errors="coerce").max() or 1.0) or 1.0
    for _, row in df.iterrows():
        name = str(row.get("display_name") or row.get("playerid") or "—")
        try:
            val = float(row.get(value_col) or 0.0)
        except (TypeError, ValueError):
            val = 0.0
        card.add_widget(BarRow(name[:18], val, max_value=max_val,
                               color_token=color_token, value_str=str(int(val))))


class SquadPage(PageBase):
    title = "Squad"

    def __init__(self, context: AppContext) -> None:
        super().__init__(context)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        outer.addWidget(SectionTitle("Squad Performance"))

        # Filter row: position chips + search + team combo.
        filter_row = QFrame()
        filter_row.setObjectName("filters")
        flyt = QHBoxLayout(filter_row)
        flyt.setContentsMargins(0, 0, 0, 0)
        flyt.setSpacing(8)

        self._pos_chips: dict[str, FilterChip] = {}
        for label in ("All", "GK", "DEF", "MID", "ATT"):
            chip = FilterChip(label)
            chip.setChecked(label == "All")
            chip.clicked.connect(lambda _checked=False, name=label: self._on_pos_chip(name))
            flyt.addWidget(chip)
            self._pos_chips[label] = chip

        flyt.addStretch(1)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search players…")
        self._search.setMaximumWidth(220)
        self._search.textChanged.connect(lambda _t: self.refresh())
        flyt.addWidget(self._search)

        self._team_combo = QComboBox()
        self._team_combo.addItem("All teams")
        self._team_combo.currentTextChanged.connect(lambda _t: self.refresh())
        flyt.addWidget(self._team_combo)

        outer.addWidget(filter_row)

        # Leaderboard row (3-col)
        leaderboards = ThreeCol()
        self._scorers_card = Card(title="Top scorers (squad)")
        self._rated_card = Card(title="Top rated (OVR)")
        self._form_card = Card(title="Form leaders")
        leaderboards.add_widget(self._scorers_card)
        leaderboards.add_widget(self._rated_card)
        leaderboards.add_widget(self._form_card)
        outer.addWidget(leaderboards)

        # Table + drawer split
        splitter = QSplitter(Qt.Orientation.Horizontal)

        table_card = Card(title="Squad table")
        self._table = DataTable(pd.DataFrame(), list(_LEADERBOARD_COLS))
        self._table.clicked.connect(self._on_row_clicked)
        table_card.add_widget(self._table, 1)
        splitter.addWidget(table_card)

        self._drawer = DrawerPanel(title="Player detail")
        self._drawer_empty_lbl = QLabel("Select a row to inspect a player.")
        self._drawer_empty_lbl.setObjectName("card-subtitle")
        self._drawer.add_widget(self._drawer_empty_lbl)
        splitter.addWidget(self._drawer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)

        self._players_df: pd.DataFrame = pd.DataFrame()
        self._filtered: pd.DataFrame = pd.DataFrame()
        self._active_pos: str = "All"
        self.refresh()

    # --- filter helpers -----------------------------------------------------

    def _on_pos_chip(self, label: str) -> None:
        self._active_pos = label
        for name, chip in self._pos_chips.items():
            chip.setChecked(name == label)
        self.refresh()

    def _on_row_clicked(self, index) -> None:
        if self._filtered.empty:
            return
        row = index.row()
        if 0 <= row < len(self._filtered):
            self._show_player(self._filtered.iloc[row])

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df
        text = self._search.text().strip().lower()
        if text and "display_name" in out.columns:
            out = out[out["display_name"].fillna("").str.lower().str.contains(text)]
        if self._active_pos != "All" and "preferredposition1" in out.columns:
            mask = out["preferredposition1"].map(lambda v: position_group(v) == self._active_pos)
            out = out[mask.fillna(False)]
        team = self._team_combo.currentText()
        if team and team != "All teams" and "teamname" in out.columns:
            out = out[out["teamname"].fillna("") == team]
        return out

    # --- drawer rendering ---------------------------------------------------

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
        pos = position_group(player.get("preferredposition1"))
        if pos:
            meta_parts.append(pos)
        meta = QLabel(" · ".join(meta_parts) or "—")
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

        section2 = QLabel("Career")
        section2.setObjectName("card-title")
        self._drawer.add_widget(section2)
        for col, label in (
            ("overallrating", "OVR"),
            ("potential", "POT"),
            ("leagueappearances", "Apps"),
            ("leaguegoals", "Goals"),
            ("form", "Form"),
        ):
            v = player.get(col)
            if pd.notna(v):
                try:
                    val = int(v)
                except (TypeError, ValueError):
                    val = 0
                self._drawer.add_widget(AttributeRow(label, val, max_val=99))

    # --- main refresh -------------------------------------------------------

    def refresh(self) -> None:
        self.set_state("loading")
        df = self.context.cache.load_latest("players_snapshot")
        if df is None or df.empty:
            self._players_df = pd.DataFrame()
            self._filtered = pd.DataFrame()
            self._table.set_dataframe(pd.DataFrame(), list(_LEADERBOARD_COLS))
            for c in (self._scorers_card, self._rated_card, self._form_card):
                _populate_bar_card(c, pd.DataFrame(), "", "accent")
            self.set_state("empty")
            return
        self._players_df = df

        # populate team combo once
        if self._team_combo.count() <= 1 and "teamname" in df.columns:
            for name in sorted({str(t) for t in df["teamname"].dropna().unique()}):
                self._team_combo.addItem(name)

        filtered = self._apply_filters(df)
        self._filtered = filtered.reset_index(drop=True)
        self._table.set_dataframe(self._filtered, list(_LEADERBOARD_COLS))

        scorers = top_scorers(filtered, n=8)
        rated = top_by_rating(filtered, n=8)
        formed = form_leaders(filtered, n=8)
        _populate_bar_card(self._scorers_card, scorers, "leaguegoals", "ok")
        _populate_bar_card(self._rated_card, rated, "overallrating", "accent")
        _populate_bar_card(self._form_card, formed, "form", "warn")
        self.set_state("ready")
