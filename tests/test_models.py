"""Unit tests for grievance models and validation."""

import unittest
from revendik.models import GrievanceDepot, GrievanceRetrait, GrievanceRetraitItem, SignatureConfig


class TestModels(unittest.TestCase):
    def test_depot_validation_fails_when_empty(self) -> None:
        depot = GrievanceDepot()
        errors = depot.validate()
        self.assertTrue(len(errors) >= 2)
        self.assertTrue(any("numéro de grief" in e.lower() for e in errors))
        self.assertTrue(any("nom" in e.lower() for e in errors))

    def test_depot_validation_passes_when_valid(self) -> None:
        depot = GrievanceDepot(no_grief="2026-042", nom="Marie Curie")
        self.assertEqual(depot.validate(), [])
        self.assertEqual(depot.sanitize_filename(), "Grief_2026-042.pdf")

    def test_depot_serialization_roundtrip(self) -> None:
        depot = GrievanceDepot(
            no_grief="2026-001",
            nom="Alice Dupont",
            no_employe="E12345",
            titre="Ergothérapeute",
            installation="CLSC Ste-Foy",
            service="Santé Courante",
            etablissement="Santé-Québec",
            date="14 octobre 2026",
            type_grief="Syndical",
            signature_nom="Alice",
            description="Ligne 1\nLigne 2",
            reclamation="Paiement rétroactif",
        )
        data = depot.to_dict()
        loaded = GrievanceDepot.from_dict(data)
        self.assertEqual(loaded.no_grief, "2026-001")
        self.assertEqual(loaded.type_grief, "Syndical")
        self.assertEqual(loaded.description, "Ligne 1\nLigne 2")

    def test_retrait_validation(self) -> None:
        retrait = GrievanceRetrait(griefs=[])
        errors = retrait.validate()
        self.assertTrue(len(errors) > 0)

        retrait_valid = GrievanceRetrait(
            griefs=[GrievanceRetraitItem(num="2026/001", nom="Jean", mat="111")]
        )
        self.assertEqual(retrait_valid.validate(), [])
        self.assertEqual(retrait_valid.sanitize_filename(), "Retrait 2026-001.pdf")

    def test_retrait_serialization_roundtrip(self) -> None:
        retrait = GrievanceRetrait(
            griefs=[
                GrievanceRetraitItem(num="2026-1", nom="User 1", mat="101"),
                GrievanceRetraitItem(num="2026-2", nom="User 2", mat="102"),
            ],
            motif="Règlement par entente entre les parties.",
            signature_nom="Sig1",
        )
        data = retrait.to_dict()
        loaded = GrievanceRetrait.from_dict(data)
        self.assertEqual(len(loaded.griefs), 2)
        self.assertEqual(loaded.griefs[1].nom, "User 2")
        self.assertEqual(loaded.motif, "Règlement par entente entre les parties.")


if __name__ == "__main__":
    unittest.main()
