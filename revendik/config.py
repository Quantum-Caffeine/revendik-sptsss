"""Configuration and path management for Revendik-SPTSSS."""

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


def get_app_dir() -> str:
    """Return the base application directory, supporting PyInstaller bundles."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class PathManager:
    """Manages application directories and files."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = base_dir or get_app_dir()
        self.dirs: Dict[str, str] = {
            "images": os.path.join(self.base_dir, "data", "images"),
            "gabarits": os.path.join(self.base_dir, "data", "gabarits"),
            "signatures": os.path.join(self.base_dir, "config", "signatures"),
            "sauvegardes": os.path.join(self.base_dir, "config", "sauvegardes"),
            "exports_griefs": os.path.join(self.base_dir, "exports", "griefs"),
            "exports_retraits": os.path.join(self.base_dir, "exports", "retraits de grief"),
        }
        self.config_file = os.path.join(self.base_dir, "config", "config.json")
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        """Create necessary directories if they don't already exist."""
        for path in self.dirs.values():
            os.makedirs(path, exist_ok=True)
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)

    def get_path(self, key: str) -> str:
        """Get directory path by key."""
        return self.dirs.get(key, self.base_dir)


@dataclass
class AppConfig:
    """Application user configuration."""

    etablissement_defaut: str = "Santé-Québec - CIUSSS de la Capitale Nationale"
    signature_defaut: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: str) -> "AppConfig":
        """Load configuration from JSON file or return defaults."""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(
                        etablissement_defaut=data.get(
                            "etablissement_defaut", "Santé-Québec - CIUSSS de la Capitale Nationale"
                        ),
                        signature_defaut=data.get("signature_defaut", ""),
                        extra={k: v for k, v in data.items() if k not in ("etablissement_defaut", "signature_defaut")},
                    )
            except Exception:
                pass
        return cls()

    def save(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        data = {
            "etablissement_defaut": self.etablissement_defaut,
            "signature_defaut": self.signature_defaut,
            **self.extra,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


def get_today_date_fr(dt: datetime | None = None) -> str:
    """Format a date in French: 'DD mois YYYY'."""
    mois_fr = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]
    now = dt or datetime.now()
    return f"{now.day} {mois_fr[now.month - 1]} {now.year}"


def open_folder(folder_path: str) -> None:
    """Open folder in native file explorer cross-platform."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    system = platform.system()
    if system == "Windows":
        os.startfile(folder_path)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", folder_path])
    else:
        subprocess.Popen(["xdg-open", folder_path])
