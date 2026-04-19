from __future__ import annotations

from typing import Callable
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
)

def create_svg_icon(svg_str: str, color: str = "currentColor", size: int = 16) -> QIcon:
    # We replace currentColor with the actual color
    # For now, we will just render the SVG to a QPixmap.
    # A real implementation might use QSvgRenderer directly if supported,
    # or generate variants for normal/active states.
    # For simplicity, we just pass the SVG string directly to QPixmap.
    # Note: PySide6 QIcon can accept an SVG file path, but from string it's trickier.
    # Let's use QSvgRenderer.
    renderer = QSvgRenderer(svg_str.encode("utf-8"))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    import PySide6.QtGui as QtGui
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

# Inline SVG stubs from the HTML prototype
ICONS = {
    "Overview": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/><rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/></svg>',
    "Analytics": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 13 L6 8 L9 10 L14 3"/><circle cx="14" cy="3" r="1.2"/></svg>',
    "Squad": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="6" cy="5" r="2.5"/><circle cx="12" cy="6" r="2"/><path d="M2 13c0-2.2 1.8-4 4-4s4 1.8 4 4"/><path d="M9.5 13c0-1.9 1.1-3 2.5-3s2.5 1.1 2.5 3"/></svg>',
    "Wonderkids": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 1.5 L10 6 L14.5 6.5 L11.25 9.5 L12 14 L8 11.7 L4 14 L4.75 9.5 L1.5 6.5 L6 6 Z"/></svg>',
    "Tactics": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="12" height="12" rx="1.5"/><path d="M2 8 H14"/><circle cx="8" cy="8" r="1.5"/></svg>',
    "Transfers": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 5 H12 M9 2 L12 5 L9 8"/><path d="M14 11 H4 M7 14 L4 11 L7 8"/></svg>',
    "Import": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 10 V2 M5 5 L8 2 L11 5"/><path d="M2 13 H14"/></svg>',
}


class NavItem(QFrame):
    clicked = Signal(int)

    def __init__(self, index: int, label: str, badge: str | None = None) -> None:
        super().__init__()
        self.setObjectName("nav-item")
        self._index = index
        self._label_str = label
        self._active = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(11)

        self._icon_label = QLabel()
        if label in ICONS:
            # For simplicity, we just set a fixed pixmap for the icon
            # A more robust solution might tint it based on active state.
            pixmap = create_svg_icon(ICONS[label]).pixmap(16, 16)
            self._icon_label.setPixmap(pixmap)
        self._icon_label.setFixedSize(16, 16)
        layout.addWidget(self._icon_label)

        self._lbl = QLabel(label)
        self._lbl.setObjectName("nav-label")
        layout.addWidget(self._lbl)

        if badge:
            badge_lbl = QLabel(badge)
            badge_lbl.setObjectName("chip--mono")
            layout.addWidget(badge_lbl)
        else:
            layout.addStretch()

        self.setProperty("active", False)

    def mousePressEvent(self, event):
        self.clicked.emit(self._index)
        super().mousePressEvent(event)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setProperty("active", active)
        self._lbl.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self._lbl.style().unpolish(self._lbl)
        self._lbl.style().polish(self._lbl)

    def collapse(self, collapsed: bool) -> None:
        self._lbl.setVisible(not collapsed)
        # Hiding the badge too if it exists
        if self.layout().count() > 2:
            item = self.layout().itemAt(2).widget()
            if item:
                item.setVisible(not collapsed)
        
        if collapsed:
            self.layout().setContentsMargins(8, 10, 8, 10)
        else:
            self.layout().setContentsMargins(12, 8, 12, 8)


class Sidebar(QFrame):
    pageSelected = Signal(int)

    def __init__(self, pages: tuple[str, ...]) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(232)
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand block
        brand = QFrame()
        brand.setObjectName("brand")
        brand_lyt = QHBoxLayout(brand)
        brand_lyt.setContentsMargins(16, 18, 16, 18)
        brand_lyt.setSpacing(10)
        
        mark = QLabel("FC")
        mark.setObjectName("brand-mark")
        mark.setFixedSize(28, 28)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_lyt.addWidget(mark)

        self.brand_text_box = QVBoxLayout()
        self.brand_text_box.setSpacing(2)
        t1 = QLabel("FC26 Analytics")
        t1.setObjectName("brand-text")
        t2 = QLabel("Career Manager Suite")
        t2.setObjectName("brand-sub")
        self.brand_text_box.addWidget(t1)
        self.brand_text_box.addWidget(t2)
        brand_lyt.addLayout(self.brand_text_box)
        layout.addWidget(brand)

        # Section Title
        self.sec_title = QLabel("Career")
        self.sec_title.setObjectName("sb-section-title")
        self.sec_title.setContentsMargins(18, 14, 18, 6)
        layout.addWidget(self.sec_title)

        # Nav items
        nav_container = QFrame()
        nav_lyt = QVBoxLayout(nav_container)
        nav_lyt.setContentsMargins(8, 4, 8, 4)
        nav_lyt.setSpacing(1)
        
        self._nav_items: list[NavItem] = []
        
        # Hardcode some badges for realism from prototype
        badges = {"Squad": "248", "Wonderkids": "64", "Import": "1"}

        for i, name in enumerate(pages):
            item = NavItem(i, name, badges.get(name))
            item.clicked.connect(self._on_nav_clicked)
            nav_lyt.addWidget(item)
            self._nav_items.append(item)
            
        layout.addWidget(nav_container)
        layout.addStretch()

        # Footer
        footer = QFrame()
        footer.setObjectName("sb-footer")
        footer_lyt = QVBoxLayout(footer)
        footer_lyt.setContentsMargins(12, 12, 12, 12)
        footer_lyt.setSpacing(8)

        self.career_card = QFrame()
        self.career_card.setObjectName("career-card")
        cc_lyt = QHBoxLayout(self.career_card)
        cc_lyt.setContentsMargins(10, 10, 10, 10)
        
        cc_text = QVBoxLayout()
        cc_text.setSpacing(2)
        cc_t1 = QLabel("Newcastle FC")
        cc_t1.setObjectName("career-title")
        cc_t2 = QLabel("Season 2025 · 1 snapshot")
        cc_t2.setObjectName("career-sub")
        cc_text.addWidget(cc_t1)
        cc_text.addWidget(cc_t2)
        cc_lyt.addLayout(cc_text)
        
        status_dot = QLabel()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet("background-color: #5ad19a; border-radius: 4px;")
        cc_lyt.addWidget(status_dot, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        footer_lyt.addWidget(self.career_card)

        self.toggle_btn = QPushButton("Collapse")
        self.toggle_btn.setObjectName("btn--ghost")
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        footer_lyt.addWidget(self.toggle_btn)
        
        layout.addWidget(footer)

        if self._nav_items:
            self.set_active_index(0)

    def _on_nav_clicked(self, index: int) -> None:
        self.set_active_index(index)
        self.pageSelected.emit(index)

    def set_active_index(self, index: int) -> None:
        for i, item in enumerate(self._nav_items):
            item.set_active(i == index)

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self.setFixedWidth(60 if self._collapsed else 232)
        
        # Hide/show elements based on collapse state
        for i in range(self.brand_text_box.count()):
            widget = self.brand_text_box.itemAt(i).widget()
            if widget:
                widget.setVisible(not self._collapsed)
                
        self.sec_title.setVisible(not self._collapsed)
        self.career_card.setVisible(not self._collapsed)
        
        for item in self._nav_items:
            item.collapse(self._collapsed)
            
        self.toggle_btn.setText("" if self._collapsed else "Collapse")
