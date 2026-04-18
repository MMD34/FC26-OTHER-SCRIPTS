"""Filesystem path resolution for the FC26 Analytics app (Windows-oriented)."""
from __future__ import annotations

import os
from pathlib import Path

_APP_DIRNAME = "FC26Analytics"


def desktop_dir() -> Path:
    profile = os.environ.get("USERPROFILE") or str(Path.home())
    return Path(profile) / "Desktop"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        path = Path(base) / _APP_DIRNAME
    else:
        path = Path.home() / ".local" / "share" / _APP_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    path = app_data_dir() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    path = app_data_dir() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path
