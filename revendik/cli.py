"""Command-line interface for Revendik-SPTSSS."""

import argparse
import os
import sys
from typing import List, Optional

from revendik.config import AppConfig, PathManager
from revendik.drafts import DraftManager
from revendik.models import GrievanceDepot, GrievanceRetrait
from revendik.pdf import PDFGenerator, detect_browser_info
from revendik.renderer import TemplateRenderer
from revendik.signatures import SignatureManager


def cmd_check_env() -> int:
    """Diagnose environment, templates, and browser availability."""
    print("=== Diagnostic Système Revendik-SPTSSS ===")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")

    paths = PathManager()
    print(f"Dossier racine: {paths.base_dir}")

    # Ensure safe console output on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Check dependencies
    try:
        import jinja2
        print(f"[OK] Jinja2 version: {jinja2.__version__}")
    except ImportError:
        print("[MANQUANT] Jinja2 manquant !")

    try:
        import PIL
        print(f"[OK] Pillow version: {PIL.__version__}")
    except ImportError:
        print("[MANQUANT] Pillow manquant !")

    # Check templates
    gabarit_depot = os.path.join(paths.get_path("gabarits"), "gabarit.html")
    gabarit_retrait = os.path.join(paths.get_path("gabarits"), "gabarit_retrait.html")
    print(f"[{'OK' if os.path.exists(gabarit_depot) else 'MANQUANT'}] Gabarit Dépôt: {gabarit_depot}")
    print(f"[{'OK' if os.path.exists(gabarit_retrait) else 'MANQUANT'}] Gabarit Retrait: {gabarit_retrait}")

    # Check browser
    found, info = detect_browser_info()
    if found:
        print(f"[OK] Navigateur PDF: {info}")
    else:
        print(f"[MANQUANT] Navigateur PDF: {info}")

    return 0 if found else 1


def cmd_list_drafts() -> int:
    """List recent saved drafts."""
    paths = PathManager()
    dm = DraftManager(paths)
    recents = dm.list_recent_drafts(limit=25)
    if not recents:
        print("Aucun brouillon trouvé dans config/sauvegardes.")
        return 0

    print(f"{'TYPE':<10} {'DATE':<18} {'FICHIER'}")
    print("-" * 60)
    for item in recents:
        print(f"{item['kind']:<10} {item['date_str']:<18} {item['filename']}")
    return 0


def cmd_list_signatures() -> int:
    """List available signatures."""
    paths = PathManager()
    sm = SignatureManager(paths)
    sigs = sm.list_signatures()
    if not sigs:
        print("Aucune signature enregistrée dans config/signatures.")
        return 0
    print(f"Signatures ({len(sigs)}):")
    for s in sigs:
        print(f" - {s}")
    return 0


def cmd_render(draft_path: str, output_path: Optional[str] = None) -> int:
    """Render a draft file to PDF."""
    if not os.path.exists(draft_path):
        print(f"Erreur: le fichier brouillon '{draft_path}' n'existe pas.", file=sys.stderr)
        return 1

    paths = PathManager()
    dm = DraftManager(paths)
    sm = SignatureManager(paths)
    renderer = TemplateRenderer(paths)
    pdf_gen = PDFGenerator()

    # Determine whether it's depot or retrait
    basename = os.path.basename(draft_path).lower()
    is_retrait = "retrait" in basename

    if is_retrait:
        retrait = dm.load_retrait_draft(draft_path)
        sig = sm.get_signature(retrait.signature_nom) if retrait.signature_nom else None
        sig_path = sm.get_image_path(sig) if sig else None
        html = renderer.render_retrait(retrait, sig, sig_path)
        out = output_path or os.path.join(paths.get_path("exports_retraits"), retrait.sanitize_filename())
    else:
        depot = dm.load_depot_draft(draft_path)
        sig = sm.get_signature(depot.signature_nom) if depot.signature_nom else None
        sig_path = sm.get_image_path(sig) if sig else None
        html = renderer.render_depot(depot, sig, sig_path)
        out = output_path or os.path.join(paths.get_path("exports_griefs"), depot.sanitize_filename())

    print(f"Génération du PDF vers: {out}")
    pdf_gen.render_and_export(html, out)
    print("PDF généré avec succès !")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="revendik",
        description="Revendik-SPTSSS : Gestion et génération de dépôts et retraits de griefs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # GUI command (default)
    subparsers.add_parser("gui", help="Lancer l'interface graphique (défaut)")

    # check-env
    subparsers.add_parser("check-env", help="Vérifier la configuration système et le moteur PDF")

    # list-drafts
    subparsers.add_parser("list-drafts", help="Lister les brouillons récents")

    # list-signatures
    subparsers.add_parser("list-signatures", help="Lister les signatures disponibles")

    # render
    render_parser = subparsers.add_parser("render", help="Générer un PDF à partir d'un brouillon JSON")
    render_parser.add_argument("draft", help="Chemin vers le fichier brouillon JSON")
    render_parser.add_argument("-o", "--output", help="Chemin du PDF de sortie (optionnel)")

    args = parser.parse_args(argv)

    if args.command == "check-env":
        return cmd_check_env()
    elif args.command == "list-drafts":
        return cmd_list_drafts()
    elif args.command == "list-signatures":
        return cmd_list_signatures()
    elif args.command == "render":
        return cmd_render(args.draft, args.output)
    else:
        # Default: Launch GUI
        from revendik.ui.app import RevendikApp

        app = RevendikApp()
        app.run()
        return 0
