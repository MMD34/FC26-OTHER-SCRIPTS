from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame
)
from PySide6.QtCore import Qt

from app.ui.design.theme_manager import ThemeManager

class TweaksPanel(QWidget):
    """Internal dev-only debug panel for theme & density switching."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tweaks-panel")
        
        # We can simulate elevation using QSS or QGraphicsDropShadowEffect, but for now
        # the QSS builder will style this as a basic panel if we give it the right ID/class.
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        title = QLabel("UI Tweaks (Dev)")
        title.setObjectName("section-title")
        layout.addWidget(title)
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setObjectName("card-subtitle")
        
        self.btn_dark = QPushButton("Dark")
        self.btn_dark.setObjectName("btn--ghost")
        self.btn_light = QPushButton("Light")
        self.btn_light.setObjectName("btn--ghost")
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.btn_dark)
        theme_layout.addWidget(self.btn_light)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Density selector
        density_layout = QHBoxLayout()
        density_label = QLabel("Density:")
        density_label.setObjectName("card-subtitle")
        
        self.combo_density = QComboBox()
        self.combo_density.addItems(["compact", "cozy", "comfortable"])
        
        density_layout.addWidget(density_label)
        density_layout.addWidget(self.combo_density)
        density_layout.addStretch()
        layout.addLayout(density_layout)
        
        layout.addStretch()
        
        # Connections
        self.btn_dark.clicked.connect(lambda: self._set_theme("dark"))
        self.btn_light.clicked.connect(lambda: self._set_theme("light"))
        self.combo_density.currentTextChanged.connect(self._set_density)
        
        self._sync_state()

    def _sync_state(self) -> None:
        manager = ThemeManager.instance()
        
        # Set combo box to current density
        idx = self.combo_density.findText(manager.density.mode)
        if idx >= 0:
            self.combo_density.setCurrentIndex(idx)
            
        # Highlight active theme button
        is_light = getattr(manager.current(), 'bg', '') == '#f3f4f8' # crude check
        if is_light:
            self.btn_light.setObjectName("btn--primary")
            self.btn_dark.setObjectName("btn--ghost")
        else:
            self.btn_dark.setObjectName("btn--primary")
            self.btn_light.setObjectName("btn--ghost")
            
        self.btn_dark.style().unpolish(self.btn_dark)
        self.btn_dark.style().polish(self.btn_dark)
        self.btn_light.style().unpolish(self.btn_light)
        self.btn_light.style().polish(self.btn_light)

    def _set_theme(self, name: str) -> None:
        manager = ThemeManager.instance()
        app = self.window().windowHandle()  # Just need any widget reference or QApplication instance
        import PySide6.QtWidgets as QtWidgets
        qapp = QtWidgets.QApplication.instance()
        if qapp:
            manager.set_theme(qapp, name)
        self._sync_state()

    def _set_density(self, mode: str) -> None:
        manager = ThemeManager.instance()
        import PySide6.QtWidgets as QtWidgets
        qapp = QtWidgets.QApplication.instance()
        if qapp:
            manager.set_density(qapp, mode)
