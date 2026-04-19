from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

class StatusBar(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statusbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(16)

        # Stubs for now
        self.msg_lbl = QLabel("Ready")
        self.msg_lbl.setObjectName("statusbar-label")
        layout.addWidget(self.msg_lbl)

        layout.addStretch()

        self.hash_lbl = QLabel("build: fc26-v2")
        self.hash_lbl.setObjectName("statusbar-label")
        layout.addWidget(self.hash_lbl)

    def show_message(self, message: str) -> None:
        self.msg_lbl.setText(message)
