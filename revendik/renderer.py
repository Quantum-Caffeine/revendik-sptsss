"""HTML rendering using Jinja2 and base64 asset encoding."""

import base64
import os
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader

from revendik.config import PathManager, get_today_date_fr
from revendik.models import GrievanceDepot, GrievanceRetrait, SignatureConfig


def encode_image_base64(image_path: Optional[str]) -> Optional[str]:
    """Encode an image file to a base64 data URI string."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode("utf-8")
            ext = image_path.lower().split(".")[-1]
            mime_type = "image/png" if ext == "png" else "image/jpeg"
            return f"data:{mime_type};base64,{encoded_string}"
    except Exception:
        return None


class TemplateRenderer:
    """Renders Jinja2 HTML templates for Grievance documents."""

    def __init__(self, paths: PathManager) -> None:
        self.paths = paths
        self.gabarits_dir = self.paths.get_path("gabarits")
        self.env = Environment(
            loader=FileSystemLoader(self.gabarits_dir),
            autoescape=False,
        )

    def get_logo_base64(self) -> str:
        """Fetch and encode the primary SPTSSS logo."""
        logo_path = os.path.join(self.paths.get_path("images"), "SPTSSS logo.png")
        return encode_image_base64(logo_path) or ""

    def render_depot(
        self,
        depot: GrievanceDepot,
        signature: Optional[SignatureConfig] = None,
        signature_image_path: Optional[str] = None,
    ) -> str:
        """Render a Dépôt de grief to HTML."""
        sig_b64 = encode_image_base64(signature_image_path) if signature_image_path else ""
        sig_bottom = signature.css_bottom if signature else 2.0
        sig_left = signature.css_left if signature else 0.0
        sig_width = signature.css_width if signature else 200.0

        data: Dict[str, Any] = {
            "no_grief": depot.no_grief,
            "nom_employe": depot.nom,
            "no_employe": depot.no_employe,
            "titre_emploi": depot.titre,
            "installation": depot.installation,
            "service": depot.service,
            "etablissement": depot.etablissement,
            "date_depot": depot.date or get_today_date_fr(),
            "description_grief": depot.description.replace("\n", "<br>"),
            "reclamation_grief": depot.reclamation.replace("\n", "<br>"),
            "logo_base64": self.get_logo_base64(),
            "signature_img_base64": sig_b64 or "",
            "signature_text": depot.nom,
            "sig_bottom": sig_bottom,
            "sig_left": sig_left,
            "sig_width": sig_width,
            "i": "checked" if depot.type_grief == "Individuel" else "",
            "g": "checked" if depot.type_grief == "Groupe" else "",
            "s": "checked" if depot.type_grief == "Syndical" else "",
        }

        template = self.env.get_template("gabarit.html")
        return template.render(data)

    def render_retrait(
        self,
        retrait: GrievanceRetrait,
        signature: Optional[SignatureConfig] = None,
        signature_image_path: Optional[str] = None,
    ) -> str:
        """Render an Avis de retrait de grief(s) to HTML."""
        sig_b64 = encode_image_base64(signature_image_path) if signature_image_path else ""
        sig_bottom = signature.css_bottom if signature else 2.0
        sig_left = signature.css_left if signature else 0.0
        sig_width = signature.css_width if signature else 200.0

        griefs_liste = [
            {"numero": g.num, "nom": g.nom, "matricule": g.mat}
            for g in retrait.griefs
            if g.num.strip() or g.nom.strip()
        ]

        data: Dict[str, Any] = {
            "motif": retrait.motif,
            "date_retrait": retrait.date_retrait or get_today_date_fr(),
            "griefs": griefs_liste,
            "logo_base64": self.get_logo_base64(),
            "signature_img_base64": sig_b64 or "",
            "sig_bottom": sig_bottom,
            "sig_left": sig_left,
            "sig_width": sig_width,
        }

        template = self.env.get_template("gabarit_retrait.html")
        return template.render(data)
