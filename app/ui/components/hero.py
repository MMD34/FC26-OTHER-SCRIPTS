"""Hero card — port of the HTML `.hero` block (crest, title, form dots, position)."""
from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.components.primitives import Chip


class FormDot(QLabel):
    """A single W/D/L pill in the recent-form row."""

    def __init__(self, kind: str, parent: QWidget | None = None) -> None:
        super().__init__(kind, parent)
        k = (kind or "").upper()
        self.setObjectName(f"form-dot--{k.lower()}" if k in ("W", "D", "L") else "form-dot--unknown")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(20, 20)


class Hero(QFrame):
    """Hero block used on the Overview page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("hero")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        # Crest
        self._crest = QLabel("—")
        self._crest.setObjectName("hero-crest")
        self._crest.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._crest.setFixedSize(64, 64)
        outer.addWidget(self._crest)

        # Center column (title + sub + form dots)
        center = QVBoxLayout()
        center.setSpacing(6)

        self._title = QLabel("No data imported")
        self._title.setObjectName("hero-title")
        center.addWidget(self._title)

        self._sub = QLabel("")
        self._sub.setObjectName("hero-sub")
        center.addWidget(self._sub)

        self._objective = Chip("", variant="accent")
        self._objective.setVisible(False)
        center.addWidget(self._objective, 0, Qt.AlignmentFlag.AlignLeft)

        # Form-dot row
        self._form_row = QFrame()
        self._form_row.setObjectName("hero-form-row")
        self._form_layout = QHBoxLayout(self._form_row)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        self._form_layout.setSpacing(4)
        self._form_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        center.addWidget(self._form_row)

        outer.addLayout(center, 1)

        # Position pill on the right
        self._pos_box = QFrame()
        self._pos_box.setObjectName("hero-pos")
        pos_lyt = QVBoxLayout(self._pos_box)
        pos_lyt.setContentsMargins(12, 8, 12, 8)
        pos_lyt.setSpacing(0)
        pos_lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pos_value = QLabel("—")
        self._pos_value.setObjectName("hero-pos-value")
        self._pos_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pos_unit = QLabel("")
        self._pos_unit.setObjectName("hero-pos-unit")
        self._pos_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pos_lyt.addWidget(self._pos_value)
        pos_lyt.addWidget(self._pos_unit)
        outer.addWidget(self._pos_box)

    def _clear_form(self) -> None:
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def set_data(
        self,
        *,
        crest: str,
        title: str,
        subtitle: str,
        form: Iterable[str] | None,
        position: int | None,
        league_size: int | None,
        objective: str | None,
    ) -> None:
        initials = (crest or "—")[:2].upper()
        self._crest.setText(initials)
        self._title.setText(title or "—")
        self._sub.setText(subtitle or "")

        if objective:
            self._objective.setText(objective)
            self._objective.setVisible(True)
        else:
            self._objective.setVisible(False)

        self._clear_form()
        if form:
            for k in form:
                self._form_layout.addWidget(FormDot(k))
        self._form_layout.addStretch(1)

        if position is not None:
            self._pos_value.setText(str(position))
            unit = _ordinal_suffix(position)
            tail = f"of {league_size}" if league_size else ""
            self._pos_unit.setText(f"{unit} {tail}".strip())
            self._pos_box.setVisible(True)
        else:
            self._pos_box.setVisible(False)


def _ordinal_suffix(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


__all__ = ["Hero", "FormDot"]
