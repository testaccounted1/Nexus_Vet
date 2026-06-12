"""NEXUS — shared utilities: paths and settings."""

import json
import os
import sys
from pathlib import Path


def resource_path(rel: str) -> Path:
    """Locate bundled read-only resources (content/, assets/) whether
    running from source or from a PyInstaller build."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel


def app_data_dir() -> Path:
    """Writable per-user data directory (claim data must never live in
    Program Files). Overridable via NEXUS_DATA_DIR for testing."""
    override = os.environ.get("NEXUS_DATA_DIR")
    if override:
        p = Path(override)
    elif os.name == "nt":
        p = Path(os.environ.get("APPDATA", Path.home())) / "NEXUS"
    else:
        p = Path.home() / ".nexus"
    p.mkdir(parents=True, exist_ok=True)
    return p


_SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {"text_scale": 1.0, "high_contrast": False,
                    "tour_done": False}


def load_settings() -> dict:
    f = app_data_dir() / _SETTINGS_FILE
    if f.exists():
        try:
            return {**DEFAULT_SETTINGS,
                    **json.loads(f.read_text(encoding="utf-8"))}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    (app_data_dir() / _SETTINGS_FILE).write_text(
        json.dumps(settings, indent=2), encoding="utf-8")
