"""Application entry point."""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from app.core.logging_setup import configure_logging, get_logger
from app.core.paths import log_dir
from app.ui.app_window import AppWindow
from app.ui.design import ThemeManager

_SETTINGS_PATH = Path(__file__).parent / "config" / "settings.toml"
_QSS_PATH = Path(__file__).parent / "config" / "theme.qss"
_FONTS_DIR = Path(__file__).resolve().parents[1] / "packaging" / "fonts"


def _load_settings() -> dict:
    if not _SETTINGS_PATH.exists():
        return {}
    with _SETTINGS_PATH.open("rb") as f:
        return tomllib.load(f)


def _register_fonts() -> None:
    if not _FONTS_DIR.is_dir():
        return
    for ttf in _FONTS_DIR.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(ttf))


def main() -> int:
    configure_logging(log_dir())
    log = get_logger(__name__)
    settings = _load_settings()
    log.info("starting FC26 Analytics (theme=%s)", settings.get("app", {}).get("theme", "dark"))

    app = QApplication(sys.argv)
    _register_fonts()
    theme_name = settings.get("app", {}).get("theme", "dark")
    ThemeManager.instance().set_theme(app, theme_name)

    window = AppWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
