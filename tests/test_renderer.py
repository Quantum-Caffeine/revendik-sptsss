"""Unit tests for HTML template rendering."""

import os
import unittest
from revendik.config import PathManager
from revendik.models import GrievanceDepot, GrievanceRetrait, GrievanceRetraitItem, SignatureConfig
from revendik.renderer import TemplateRenderer


class TestRenderer(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = PathManager()
        self.renderer = TemplateRenderer(self.paths)

    def test_render_depot_html(self) -> None:
        depot = GrievanceDepot(
            no_grief="G-2026-999",
            nom="Martin Vachon",
            no_employe="998877",
            titre="Physiothérapeute",
            installation="Hôpital St-Sacrement",
            service="Réadaptation",
            etablissement="Santé-Québec Capitale-Nationale",
            date="14 octobre 2026",
            type_grief="Individuel",
            description="Détail du grief\nDeuxième paragraphe.",
            reclamation="Compensation financière.",
        )
        sig = SignatureConfig(nom="Martin", image="martin.png", css_left=10, css_bottom=5, css_width=180)
        html = self.renderer.render_depot(depot, signature=sig)

        self.assertIn("G-2026-999", html)
        self.assertIn("Martin Vachon", html)
        self.assertIn("Détail du grief<br>Deuxième paragraphe.", html)
        self.assertIn("checked", html)

    def test_render_retrait_html(self) -> None:
        retrait = GrievanceRetrait(
            griefs=[
                GrievanceRetraitItem(num="2026-10", nom="Lucie Belleau", mat="4567"),
                GrievanceRetraitItem(num="2026-11", nom="Marc Tremblay", mat="8910"),
            ],
            motif="L’Employeur a fait droit au grief.",
            date_retrait="14 octobre 2026",
        )
        html = self.renderer.render_retrait(retrait)

        self.assertIn("Avis de retrait de grief(s)", html)
        self.assertIn("Lucie Belleau", html)
        self.assertIn("Marc Tremblay", html)
        self.assertIn("L’Employeur a fait droit au grief.", html)


if __name__ == "__main__":
    unittest.main()
