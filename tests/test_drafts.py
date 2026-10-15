"""Unit tests for draft saving, loading, and auto-backups."""

import os
import tempfile
import unittest

from revendik.config import PathManager
from revendik.drafts import DraftManager
from revendik.models import GrievanceDepot, GrievanceRetrait, GrievanceRetraitItem


class TestDrafts(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.paths = PathManager(base_dir=self.temp_dir.name)
        self.draft_manager = DraftManager(self.paths)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_and_load_depot_draft(self) -> None:
        depot = GrievanceDepot(
            no_grief="2026-ABC",
            nom="Sylvie Gagnon",
            description="Brouillon test",
        )
        file_path = os.path.join(self.temp_dir.name, "depot_test.json")
        self.draft_manager.save_depot_draft(depot, file_path)

        loaded = self.draft_manager.load_depot_draft(file_path)
        self.assertEqual(loaded.no_grief, "2026-ABC")
        self.assertEqual(loaded.nom, "Sylvie Gagnon")

    def test_auto_save_depot_creates_timestamped_file(self) -> None:
        depot = GrievanceDepot(no_grief="2026-XYZ", nom="Test Auto")
        saved_path = self.draft_manager.auto_save_depot(depot)

        self.assertTrue(os.path.exists(saved_path))
        self.assertIn("depot_2026-XYZ_", os.path.basename(saved_path))

        recents = self.draft_manager.list_recent_drafts()
        self.assertEqual(len(recents), 1)
        self.assertEqual(recents[0]["kind"], "Dépôt")

    def test_save_and_load_retrait_draft(self) -> None:
        retrait = GrievanceRetrait(
            griefs=[GrievanceRetraitItem(num="2026-R1", nom="Gilles", mat="999")],
            motif="Règlement par entente entre les parties.",
        )
        saved_path = self.draft_manager.auto_save_retrait(retrait)
        self.assertTrue(os.path.exists(saved_path))
        loaded = self.draft_manager.load_retrait_draft(saved_path)
        self.assertEqual(len(loaded.griefs), 1)
        self.assertEqual(loaded.griefs[0].nom, "Gilles")


if __name__ == "__main__":
    unittest.main()
