"""Base class for all sidebar pages.

Phase 0 contract (`redisign_roadmap.md` Sprint 0.3):

- Pages expose a ``set_state(state)`` hook with states
  ``"loading" | "empty" | "error" | "ready"``.
- Pages emit explicit states at their data-ready points so later phases can
  swap in tokenized loading/empty/error overlays without touching the data
  flow.
- Phase 0 ships the contract only — the default ``_render_state`` is a
  no-op, so the current widget stays visible (zero visual change).
"""
from __future__ import annotations

from typing import Literal, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from app.services.app_context import AppContext

PageState = Literal["loading", "empty", "error", "ready"]
_VALID_STATES: frozenset[str] = frozenset(
    {"loading", "empty", "error", "ready"}
)


class PageBase(QWidget):
    title: str = "Page"

    state_changed = Signal(str)

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self._state: PageState = "ready"
        self._state_error: Optional[str] = None

    @property
    def state(self) -> PageState:
        return self._state

    @property
    def state_error(self) -> Optional[str]:
        return self._state_error

    def set_state(
        self,
        state: PageState,
        *,
        error: Optional[str] = None,
    ) -> None:
        if state not in _VALID_STATES:
            raise ValueError(
                f"invalid page state {state!r}; "
                f"expected one of {sorted(_VALID_STATES)}"
            )
        self._state = state
        self._state_error = error
        self._render_state()
        self.state_changed.emit(state)

    def _render_state(self) -> None:
        """Hook for subclasses to overlay loading/empty/error visuals.

        Default is a no-op: the current widget tree stays visible. Phase 3
        ships default tokenized overlays; Phase 5 wires pages to use them.
        """

    def refresh(self) -> None:
        """Override to react to AppContext.dataChanged."""


__all__ = ["PageBase", "PageState"]
