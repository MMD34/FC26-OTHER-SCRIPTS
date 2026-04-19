from __future__ import annotations

from app.ui.design.tokens import Palette, Density, Typography, Spacing, Radii

def build_qss(palette: Palette, density: Density, typo: Typography) -> str:
    """Build the global QSS stylesheet."""
    
    # Scale padding by density
    def pad(base_val: int) -> int:
        return int(base_val * density.multiplier)

    spacing = Spacing()
    radii = Radii()

    # We re-implement the styles from original load_qss, but using the new tokens
    # and adding some more for the new components if necessary.
    
    base = f"""
QWidget {{
    background-color: {palette.bg};
    color: {palette.text};
    font-family: {typo.sans};
    font-size: {typo.base}px;
}}
QMainWindow {{ background-color: {palette.bg}; }}
QStatusBar {{
    background-color: {palette.panel};
    color: {palette.muted};
    border-top: 1px solid {palette.line};
}}
QListWidget {{
    background-color: {palette.panel};
    border: none;
    padding: {pad(spacing.sm)}px 0;
    outline: 0;
}}
QListWidget::item {{
    padding: {pad(10)}px {pad(16)}px;
    border-left: 3px solid transparent;
}}
QListWidget::item:hover {{ background-color: {palette.panel_2}; }}
QListWidget::item:selected {{
    background-color: {palette.panel_2};
    border-left: 3px solid {palette.accent};
    color: {palette.text};
}}
QFrame#card {{
    background-color: {palette.panel};
    border: 1px solid {palette.line};
    border-radius: {radii.md}px;
}}
QLabel#card-title {{ color: {palette.muted}; font-size: {typo.sm}px; text-transform: uppercase; }}
QLabel#card-value {{ color: {palette.text}; font-size: {typo.lg}px; font-weight: 600; font-family: {typo.display}; }}
QLabel#card-subtitle {{ color: {palette.muted}; font-size: {typo.sm}px; }}
QPushButton {{
    background-color: {palette.panel_2};
    color: {palette.text};
    border: 1px solid {palette.line};
    border-radius: {radii.sm}px;
    padding: {pad(6)}px {pad(14)}px;
}}
QPushButton:hover {{ background-color: {palette.accent}; color: {palette.bg}; }}
QTableView {{
    background-color: {palette.panel};
    alternate-background-color: {palette.panel_2};
    gridline-color: {palette.line};
    selection-background-color: {palette.accent};
    selection-color: {palette.bg};
}}
QHeaderView::section {{
    background-color: {palette.panel_2};
    color: {palette.muted};
    border: none;
    padding: {pad(6)}px {pad(8)}px;
}}
QPlainTextEdit, QLineEdit, QComboBox {{
    background-color: {palette.panel};
    border: 1px solid {palette.line};
    border-radius: {radii.sm}px;
    padding: {pad(4)}px {pad(8)}px;
    color: {palette.text};
}}
QToolBar {{
    background-color: {palette.panel};
    border: none;
    spacing: {pad(spacing.sm)}px;
}}
    """
    
    components = f"""
/* New Components added for Sprint 1.2 */
QWidget#chip--default {{
    background-color: {palette.chip};
    color: {palette.text};
    border-radius: {radii.sm}px;
    padding: {pad(2)}px {pad(8)}px;
}}
QWidget#chip--ok {{
    background-color: {palette.chip_ok};
    color: {palette.ok};
    border-radius: {radii.sm}px;
    padding: {pad(2)}px {pad(8)}px;
}}
QWidget#chip--warn {{
    background-color: {palette.chip_warn};
    color: {palette.warn};
    border-radius: {radii.sm}px;
    padding: {pad(2)}px {pad(8)}px;
}}
QWidget#chip--bad {{
    background-color: {palette.chip_bad};
    color: {palette.bad};
    border-radius: {radii.sm}px;
    padding: {pad(2)}px {pad(8)}px;
}}
QWidget#chip--accent {{
    background-color: {palette.chip_accent};
    color: {palette.accent};
    border-radius: {radii.sm}px;
    padding: {pad(2)}px {pad(8)}px;
}}
QWidget#chip--mono {{
    background-color: {palette.chip};
    color: {palette.muted};
    font-family: {typo.mono};
    border-radius: {radii.sm}px;
    padding: {pad(2)}px {pad(8)}px;
}}
QPushButton#btn--primary {{
    background-color: {palette.accent};
    color: {palette.bg};
    border: none;
    font-weight: 600;
}}
QPushButton#btn--primary:hover {{ background-color: {palette.accent_2}; }}
QPushButton#btn--ghost {{
    background-color: transparent;
    color: {palette.text};
    border: none;
}}
QPushButton#btn--ghost:hover {{ background-color: {palette.panel_2}; }}
    """
    
    return base + components
