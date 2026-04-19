from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class Topbar(QFrame):
    themeToggled = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("topbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(12)

        # Breadcrumb
        breadcrumb_lyt = QHBoxLayout()
        breadcrumb_lyt.setSpacing(8)
        lbl1 = QLabel("FC26")
        lbl1.setObjectName("breadcrumb")
        lbl2 = QLabel("›")
        lbl2.setObjectName("breadcrumb")
        self.crumb = QLabel("Overview")
        self.crumb.setObjectName("breadcrumb-b")
        breadcrumb_lyt.addWidget(lbl1)
        breadcrumb_lyt.addWidget(lbl2)
        breadcrumb_lyt.addWidget(self.crumb)
        layout.addLayout(breadcrumb_lyt)

        layout.addStretch()

        # Search stub
        search_box = QFrame()
        search_box.setObjectName("search")
        search_box.setMinimumWidth(260)
        search_lyt = QHBoxLayout(search_box)
        search_lyt.setContentsMargins(10, 6, 10, 6)
        search_lyt.setSpacing(8)
        
        search_input = QLineEdit()
        search_input.setObjectName("search-input")
        search_input.setPlaceholderText("Search players, teams, snapshots…")
        search_lyt.addWidget(search_input)
        
        kbd = QLabel("⌘K")
        kbd.setObjectName("search-kbd")
        search_lyt.addWidget(kbd)
        layout.addWidget(search_box)

        # Date chip
        date_btn = QPushButton("28 Sep 2025")
        date_btn.setObjectName("btn--ghost")
        layout.addWidget(date_btn)

        # Theme toggle
        self.theme_btn = QPushButton("Dark")
        self.theme_btn.setObjectName("btn--ghost")
        self.theme_btn.setCheckable(True)
        self.theme_btn.toggled.connect(self._on_theme_toggled)
        layout.addWidget(self.theme_btn)

        # Primary CTA
        import_btn = QPushButton("Import snapshot")
        import_btn.setObjectName("btn--primary")
        layout.addWidget(import_btn)

    def set_title(self, title: str) -> None:
        self.crumb.setText(title)

    def _on_theme_toggled(self, checked: bool) -> None:
        self.theme_btn.setText("Light" if checked else "Dark")
        self.themeToggled.emit(checked)
