import os
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PySide6.QtGui import QPixmap

from app.ui.design.theme_manager import ThemeManager

@pytest.fixture
def snapshot_dir(request) -> Path:
    d = Path(__file__).parent / "snapshots"
    d.mkdir(exist_ok=True)
    return d

def test_visual_snapshot_button(qapp: QApplication, snapshot_dir: Path) -> None:
    tm = ThemeManager.instance()
    
    # Render a ghost button
    widget = QWidget()
    layout = QVBoxLayout(widget)
    btn = QPushButton("Ghost Button")
    btn.setObjectName("btn--ghost")
    layout.addWidget(btn)
    
    # We must show it to render, but can keep it offscreen if QT_QPA_PLATFORM is offscreen
    widget.resize(100, 50)
    widget.show()
    
    # Grab pixmap
    pixmap = widget.grab()
    
    snapshot_path = snapshot_dir / "btn_ghost.png"
    if not snapshot_path.exists():
        pixmap.save(str(snapshot_path))
    else:
        baseline = QPixmap(str(snapshot_path))
        assert pixmap.toImage() == baseline.toImage(), "Snapshot mismatch for btn_ghost"

def test_visual_snapshot_chip(qapp: QApplication, snapshot_dir: Path) -> None:
    tm = ThemeManager.instance()
    
    # Render a chip
    widget = QWidget()
    widget.setObjectName("chip--ok")
    widget.resize(80, 24)
    widget.show()
    
    pixmap = widget.grab()
    
    snapshot_path = snapshot_dir / "chip_ok.png"
    if not snapshot_path.exists():
        pixmap.save(str(snapshot_path))
    else:
        baseline = QPixmap(str(snapshot_path))
        assert pixmap.toImage() == baseline.toImage(), "Snapshot mismatch for chip_ok"
