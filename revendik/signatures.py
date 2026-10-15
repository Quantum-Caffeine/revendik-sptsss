"""Signature repository and canvas coordinate conversion."""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from PIL import Image

from revendik.config import PathManager
from revendik.models import SignatureConfig

RATIO_PDF = 0.84
CANVAS_BASELINE_Y = 150
CANVAS_OFFSET_X = 10


def sanitize_sig_filename(name: str) -> str:
    """Sanitize name to produce clean base filename."""
    clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", clean)


def coords_to_css(x: float, y: float, orig_w: float, scale: float) -> Tuple[float, float, float]:
    """
    Convert Canvas coordinates (x, y) and scale to CSS values:
    (css_left, css_bottom, css_width).
    """
    left_px = (x - CANVAS_OFFSET_X) * RATIO_PDF
    w_px = (orig_w * scale) * RATIO_PDF
    bottom_px = (CANVAS_BASELINE_Y - y) * RATIO_PDF
    return round(left_px, 2), round(bottom_px, 2), round(w_px, 2)


def css_to_coords(css_left: float, css_bottom: float) -> Tuple[float, float]:
    """Convert CSS values back to Canvas coordinates (x, y)."""
    x = (css_left / RATIO_PDF) + CANVAS_OFFSET_X
    y = CANVAS_BASELINE_Y - (css_bottom / RATIO_PDF)
    return x, y


class SignatureManager:
    """Manages signature assets and metadata."""

    def __init__(self, paths: PathManager) -> None:
        self.paths = paths
        self.sig_dir = self.paths.get_path("signatures")

    def list_signatures(self) -> List[str]:
        """Return names of available signatures."""
        if not os.path.exists(self.sig_dir):
            return []
        names = []
        for filename in sorted(os.listdir(self.sig_dir)):
            if filename.endswith(".json"):
                path = os.path.join(self.sig_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        names.append(data.get("nom", filename[:-5]))
                except Exception:
                    names.append(filename[:-5])
        return names

    def find_file_by_name(self, name: str) -> Optional[str]:
        """Find the JSON file path matching a signature name."""
        if not name or not os.path.exists(self.sig_dir):
            return None
        # Check direct filename
        clean = sanitize_sig_filename(name)
        candidate = os.path.join(self.sig_dir, f"{clean}.json")
        if os.path.exists(candidate):
            return candidate
        # Search all JSON files for matching 'nom'
        for f in os.listdir(self.sig_dir):
            if f.endswith(".json"):
                full = os.path.join(self.sig_dir, f)
                try:
                    with open(full, "r", encoding="utf-8") as jf:
                        d = json.load(jf)
                        if d.get("nom") == name:
                            return full
                except Exception:
                    pass
        return None

    def get_signature(self, name: str) -> Optional[SignatureConfig]:
        """Load signature configuration by name."""
        json_file = self.find_file_by_name(name)
        if json_file and os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return SignatureConfig.from_dict(data)
            except Exception:
                return None
        return None

    def get_image_path(self, sig: SignatureConfig) -> Optional[str]:
        """Get full path to signature PNG image."""
        if not sig or not sig.image:
            return None
        path = os.path.join(self.sig_dir, sig.image)
        return path if os.path.exists(path) else None

    def save_signature(
        self,
        name: str,
        image: Image.Image,
        x: float,
        y: float,
        scale: float,
    ) -> SignatureConfig:
        """Save signature image and calculated JSON configuration."""
        base_name = sanitize_sig_filename(name)
        img_filename = f"{base_name}.png"
        json_filename = f"{base_name}.json"

        img_dest = os.path.join(self.sig_dir, img_filename)
        json_dest = os.path.join(self.sig_dir, json_filename)

        image.save(img_dest, "PNG")

        css_left, css_bottom, css_width = coords_to_css(x, y, image.size[0], scale)
        config = SignatureConfig(
            nom=name,
            image=img_filename,
            css_left=css_left,
            css_bottom=css_bottom,
            css_width=css_width,
            tk_scale=scale,
        )

        with open(json_dest, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=4, ensure_ascii=False)

        return config

    def delete_signature(self, name: str) -> bool:
        """Delete signature configuration and associated image."""
        json_file = self.find_file_by_name(name)
        if not json_file or not os.path.exists(json_file):
            return False

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            img_file = data.get("image")
            if img_file:
                img_path = os.path.join(self.sig_dir, img_file)
                if os.path.exists(img_path):
                    os.remove(img_path)
            os.remove(json_file)
            return True
        except Exception:
            return False

    @staticmethod
    def prepare_imported_image(image_path: str, max_size: int = 800) -> Image.Image:
        """Open, convert to RGBA, and resize if larger than max_size."""
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size
        if max(w, h) > max_size:
            if w > h:
                new_w = max_size
                new_h = int(h * (max_size / w))
            else:
                new_h = max_size
                new_w = int(w * (max_size / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return img
