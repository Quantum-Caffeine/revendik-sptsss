"""Data models and validation for Grievance submissions and withdrawals."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SignatureConfig:
    """Signature placement and rendering configuration."""

    nom: str
    image: str
    css_left: float = 0.0
    css_bottom: float = 2.0
    css_width: float = 200.0
    tk_scale: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nom": self.nom,
            "image": self.image,
            "css_left": round(self.css_left, 2),
            "css_bottom": round(self.css_bottom, 2),
            "css_width": round(self.css_width, 2),
            "tk_scale": self.tk_scale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignatureConfig":
        return cls(
            nom=data.get("nom", ""),
            image=data.get("image", ""),
            css_left=float(data.get("css_left", 0.0)),
            css_bottom=float(data.get("css_bottom", 2.0)),
            css_width=float(data.get("css_width", 200.0)),
            tk_scale=float(data.get("tk_scale", 0.5)),
        )


@dataclass
class GrievanceDepot:
    """Model representing a Grievance Submission (Dépôt de grief)."""

    no_grief: str = ""
    nom: str = ""
    no_employe: str = ""
    titre: str = ""
    installation: str = ""
    service: str = ""
    etablissement: str = ""
    date: str = ""
    type_grief: str = "Individuel"  # "Individuel", "Groupe", "Syndical"
    signature_nom: str = ""
    description: str = ""
    reclamation: str = ""

    def validate(self) -> List[str]:
        """Validate required fields. Returns list of error messages."""
        errors: List[str] = []
        if not self.no_grief.strip():
            errors.append("Le numéro de grief est obligatoire.")
        if not self.nom.strip():
            errors.append("Le nom du salarié est obligatoire.")
        return errors

    def sanitize_filename(self) -> str:
        """Return safe filename for the PDF export."""
        clean_no = self.no_grief.strip().replace("/", "-").replace("\\", "-").replace(":", "-")
        return f"Grief_{clean_no}.pdf"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to draft dictionary."""
        return {
            "no_grief": self.no_grief,
            "nom": self.nom,
            "no_employe": self.no_employe,
            "titre": self.titre,
            "installation": self.installation,
            "service": self.service,
            "etablissement": self.etablissement,
            "date": self.date,
            "type": self.type_grief,
            "signature": self.signature_nom,
            "description": self.description,
            "reclamation": self.reclamation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrievanceDepot":
        """Reconstruct model from draft dictionary."""
        return cls(
            no_grief=data.get("no_grief", ""),
            nom=data.get("nom", ""),
            no_employe=data.get("no_employe", ""),
            titre=data.get("titre", ""),
            installation=data.get("installation", ""),
            service=data.get("service", ""),
            etablissement=data.get("etablissement", ""),
            date=data.get("date", ""),
            type_grief=data.get("type", "Individuel"),
            signature_nom=data.get("signature", ""),
            description=data.get("description", ""),
            reclamation=data.get("reclamation", ""),
        )


@dataclass
class GrievanceRetraitItem:
    """Individual grievance line in a withdrawal request."""

    num: str = ""
    nom: str = ""
    mat: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {"num": self.num, "nom": self.nom, "mat": self.mat}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrievanceRetraitItem":
        return cls(
            num=str(data.get("num", data.get("numero", ""))),
            nom=str(data.get("nom", "")),
            mat=str(data.get("mat", data.get("matricule", ""))),
        )


MOTIFS_RETRAIT = [
    "L’Employeur a fait droit au grief.",
    "Règlement par entente entre les parties.",
    "Retrait sans admission de la part du Syndicat.",
]


@dataclass
class GrievanceRetrait:
    """Model representing a Grievance Withdrawal (Retrait de grief)."""

    griefs: List[GrievanceRetraitItem] = field(default_factory=list)
    motif: str = MOTIFS_RETRAIT[0]
    signature_nom: str = ""
    date_retrait: str = ""

    def validate(self) -> List[str]:
        """Validate required withdrawal items."""
        errors: List[str] = []
        valid_items = [g for g in self.griefs if g.num.strip() or g.nom.strip()]
        if not valid_items:
            errors.append("Au moins un grief (numéro et nom) est obligatoire pour le retrait.")
        else:
            first = valid_items[0]
            if not first.num.strip():
                errors.append("Le numéro du premier grief est obligatoire.")
            if not first.nom.strip():
                errors.append("Le nom du salarié pour le premier grief est obligatoire.")
        return errors

    def sanitize_filename(self) -> str:
        """Return safe filename for the withdrawal PDF export."""
        valid_nums = [
            g.num.strip().replace("/", "-").replace("\\", "-").replace(":", "-")
            for g in self.griefs
            if g.num.strip()
        ]
        if not valid_nums:
            valid_nums = ["inconnu"]
        return f"Retrait {', '.join(valid_nums)}.pdf"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to draft dictionary."""
        return {
            "griefs": [g.to_dict() for g in self.griefs],
            "motif": self.motif,
            "signature": self.signature_nom,
            "date": self.date_retrait,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrievanceRetrait":
        """Reconstruct model from draft dictionary."""
        raw_griefs = data.get("griefs", [])
        griefs = [GrievanceRetraitItem.from_dict(g) for g in raw_griefs if isinstance(g, dict)]
        if not griefs:
            griefs = [GrievanceRetraitItem()]
        return cls(
            griefs=griefs,
            motif=data.get("motif", MOTIFS_RETRAIT[0]),
            signature_nom=data.get("signature", ""),
            date_retrait=data.get("date", ""),
        )
