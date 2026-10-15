"""Draft management: saving, loading, auto-saving, and history."""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from revendik.config import PathManager
from revendik.models import GrievanceDepot, GrievanceRetrait


class DraftManager:
    """Handles draft storage and auto-backups."""

    def __init__(self, paths: PathManager) -> None:
        self.paths = paths
        self.sauvegardes_dir = self.paths.get_path("sauvegardes")

    def save_depot_draft(self, depot: GrievanceDepot, filepath: str) -> None:
        """Save depot to a specific file path."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(depot.to_dict(), f, ensure_ascii=False, indent=4)

    def load_depot_draft(self, filepath: str) -> GrievanceDepot:
        """Load depot from a draft file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GrievanceDepot.from_dict(data)

    def auto_save_depot(self, depot: GrievanceDepot) -> str:
        """Create a timestamped auto-backup for a depot."""
        no_clean = re.sub(r"[^\w-]", "-", depot.no_grief.strip()) or "sans_numero"
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"depot_{no_clean}_{ts}.json"
        dest = os.path.join(self.sauvegardes_dir, filename)
        self.save_depot_draft(depot, dest)
        return dest

    def save_retrait_draft(self, retrait: GrievanceRetrait, filepath: str) -> None:
        """Save withdrawal to a specific file path."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(retrait.to_dict(), f, ensure_ascii=False, indent=4)

    def load_retrait_draft(self, filepath: str) -> GrievanceRetrait:
        """Load withdrawal from a draft file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GrievanceRetrait.from_dict(data)

    def auto_save_retrait(self, retrait: GrievanceRetrait) -> str:
        """Create a timestamped auto-backup for a withdrawal."""
        first_num = "sans_numero"
        for g in retrait.griefs:
            if g.num.strip():
                first_num = re.sub(r"[^\w-]", "-", g.num.strip())
                break
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"retrait_{first_num}_{ts}.json"
        dest = os.path.join(self.sauvegardes_dir, filename)
        self.save_retrait_draft(retrait, dest)
        return dest

    def list_recent_drafts(self, limit: int = 15) -> List[Dict[str, Any]]:
        """List recent drafts from the sauvegardes folder, newest first."""
        if not os.path.exists(self.sauvegardes_dir):
            return []

        entries = []
        for filename in os.listdir(self.sauvegardes_dir):
            if filename.endswith(".json"):
                full_path = os.path.join(self.sauvegardes_dir, filename)
                mtime = os.path.getmtime(full_path)
                is_retrait = filename.startswith("retrait_")
                is_depot = filename.startswith("depot_")
                kind = "Retrait" if is_retrait else ("Dépôt" if is_depot else "Autre")
                entries.append({
                    "filename": filename,
                    "path": full_path,
                    "mtime": mtime,
                    "date_str": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                    "kind": kind,
                })

        entries.sort(key=lambda x: x["mtime"], reverse=True)
        return entries[:limit]
