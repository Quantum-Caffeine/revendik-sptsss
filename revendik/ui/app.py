"""Main application GUI orchestrator."""

import os
import platform
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from PIL import Image, ImageTk

from revendik.config import AppConfig, PathManager, open_folder
from revendik.drafts import DraftManager
from revendik.pdf import PDFGenerator, detect_browser_info
from revendik.renderer import TemplateRenderer
from revendik.signatures import SignatureManager
from revendik.ui.dialogs.settings_dialog import SettingsDialog
from revendik.ui.tabs.depot_tab import DepotTab
from revendik.ui.tabs.retrait_tab import RetraitTab
from revendik.ui.tabs.signatures_tab import SignaturesTab
from revendik.ui.theme import Theme, apply_theme


class RevendikApp:
    """Main application controller and top-level window manager."""

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        self.root = root or tk.Tk()
        self.root.title("Revendik-SPTSSS - Gestion des Griefs")

        # Responsive geometry adapting to standard screens
        self.root.geometry("740x820")
        self.root.minsize(620, 520)

        # Core services
        self.paths = PathManager()
        self.config = AppConfig.load(self.paths.config_file)
        self.renderer = TemplateRenderer(self.paths)
        self.pdf_gen = PDFGenerator()
        self.sig_manager = SignatureManager(self.paths)
        self.draft_manager = DraftManager(self.paths)

        # Apply styling
        self.style = apply_theme(self.root)

        # Build UI (Footer packed first so it stays anchored to bottom)
        self._build_menu()
        self._build_footer()
        self._build_main_notebook()

        self.set_status("Application prête. Bienvenue sur Revendik-SPTSSS.")

    def set_status(self, message: str) -> None:
        """Update bottom status bar message."""
        if hasattr(self, "lbl_status") and self.lbl_status:
            self.lbl_status.config(text=message)

    def _build_menu(self) -> None:
        self.menu_bar = tk.Menu(self.root)

        # Menu Fichier
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(
            label="Nouveau Dépôt",
            accelerator="Ctrl+N",
            command=lambda: (self.notebook.select(0), self.tab_depot.reset_form()),
        )
        file_menu.add_command(
            label="Nouveau Retrait",
            command=lambda: (self.notebook.select(1), self.tab_retrait.reset_form()),
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Ouvrir dossier des griefs exportés",
            command=lambda: open_folder(self.paths.get_path("exports_griefs")),
        )
        file_menu.add_command(
            label="Ouvrir dossier des retraits exportés",
            command=lambda: open_folder(self.paths.get_path("exports_retraits")),
        )
        file_menu.add_command(
            label="Ouvrir dossier des sauvegardes / brouillons",
            command=lambda: open_folder(self.paths.get_path("sauvegardes")),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        self.menu_bar.add_cascade(label="Fichier", menu=file_menu)

        # Menu Brouillons Récents
        self.drafts_menu = tk.Menu(self.menu_bar, tearoff=0, postcommand=self._populate_recent_drafts)
        self.menu_bar.add_cascade(label="Brouillons", menu=self.drafts_menu)

        # Menu Outils
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Préférences...", command=self.open_settings)
        tools_menu.add_command(label="Vérifier le moteur PDF...", command=self.check_browser)
        self.menu_bar.add_cascade(label="Outils", menu=tools_menu)

        # Menu Aide
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="À propos de Revendik-SPTSSS", command=self.show_about)
        self.menu_bar.add_cascade(label="Aide", menu=help_menu)

        self.root.config(menu=self.menu_bar)

    def _populate_recent_drafts(self) -> None:
        """Dynamically populate recent drafts in menu."""
        self.drafts_menu.delete(0, tk.END)
        recents = self.draft_manager.list_recent_drafts(limit=10)
        if not recents:
            self.drafts_menu.add_command(label="Aucun brouillon récent", state="disabled")
            return

        for item in recents:
            label = f"[{item['kind']}] {item['filename']} ({item['date_str']})"
            filepath = item["path"]
            kind = item["kind"]

            def _open(fp=filepath, k=kind):
                if k == "Retrait":
                    self.notebook.select(1)
                    self.tab_retrait.load_draft(fp)
                else:
                    self.notebook.select(0)
                    self.tab_depot.load_draft(fp)

            self.drafts_menu.add_command(label=label, command=_open)

    def _build_main_notebook(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=8, pady=(6, 2))

        # Tab 1: Dépôt
        self.tab_depot = DepotTab(
            self.notebook,
            paths=self.paths,
            config=self.config,
            renderer=self.renderer,
            pdf_gen=self.pdf_gen,
            sig_manager=self.sig_manager,
            draft_manager=self.draft_manager,
            set_status=self.set_status,
        )
        self.notebook.add(self.tab_depot, text=" 📝 Nouveau Dépôt ")

        # Tab 2: Retrait
        self.tab_retrait = RetraitTab(
            self.notebook,
            paths=self.paths,
            config=self.config,
            renderer=self.renderer,
            pdf_gen=self.pdf_gen,
            sig_manager=self.sig_manager,
            draft_manager=self.draft_manager,
            set_status=self.set_status,
        )
        self.notebook.add(self.tab_retrait, text=" ↩️ Retrait de Griefs ")

        # Tab 3: Signatures
        self.tab_sig = SignaturesTab(
            self.notebook,
            paths=self.paths,
            config=self.config,
            sig_manager=self.sig_manager,
            on_signatures_changed=self.on_signatures_changed,
            set_status=self.set_status,
        )
        self.notebook.add(self.tab_sig, text=" ✍️ Gestion des Signatures ")

    def _build_footer(self) -> None:
        footer = ttk.Frame(self.root)
        footer.pack(side="bottom", fill="x", padx=8, pady=(0, 4))

        # Status Bar
        self.lbl_status = tk.Label(
            footer,
            text="",
            anchor="w",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#f1f5f9",
            relief="sunken",
            padx=8,
            pady=3,
        )
        self.lbl_status.pack(side="bottom", fill="x", pady=(2, 0))

        # Revendik Logo
        logo_path = os.path.join(self.paths.get_path("images"), "logo_revendik.jpg")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(self.paths.get_path("images"), "logo_revendik.png")

        if os.path.exists(logo_path):
            try:
                img_logo = Image.open(logo_path)
                w_base = 180
                w_percent = w_base / float(img_logo.size[0])
                h_size = int(float(img_logo.size[1]) * float(w_percent))
                img_resized = img_logo.resize((w_base, h_size), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img_resized)
                lbl_logo = ttk.Label(footer, image=self.logo_tk)
                lbl_logo.pack(side="right", padx=4, pady=2)
            except Exception:
                pass

    def on_signatures_changed(self) -> None:
        """Notify child tabs when signatures are modified."""
        self.tab_depot.update_signatures_list()
        self.tab_retrait.update_signatures_list()

    def open_settings(self) -> None:
        """Open Preferences dialog."""
        SettingsDialog(
            self.root,
            paths=self.paths,
            config=self.config,
            sig_manager=self.sig_manager,
            on_save_callback=self._on_settings_saved,
        )

    def _on_settings_saved(self) -> None:
        """Called when settings dialog saves."""
        self.on_signatures_changed()
        self.set_status("Préférences enregistrées.")

    def check_browser(self) -> None:
        """Diagnostic check for PDF rendering browser."""
        found, info = detect_browser_info()
        if found:
            messagebox.showinfo(
                "Moteur PDF Opérationnel",
                f"Navigateur détecté avec succès :\n\n{info}\n\nLa génération de fichiers PDF est pleinement opérationnelle.",
            )
        else:
            messagebox.showwarning(
                "Aucun Navigateur Détecté",
                "Aucun navigateur Chromium/Edge n'a été trouvé.\n\n"
                "Pour générer des PDF, veuillez installer Google Chrome ou Microsoft Edge.",
            )

    def show_about(self) -> None:
        """Display about dialog."""
        messagebox.showinfo(
            "À propos de Revendik-SPTSSS",
            "Revendik-SPTSSS v2.0\n"
            "Application de dépôt et de retrait de griefs pour le SPTSSS.\n\n"
            "Développé pour les professionnelles et professionnels du milieu de la santé et des services sociaux.\n\n"
            "Architecture modulaire refactorisée.",
        )

    def run(self) -> None:
        """Start GUI main event loop."""
        self.root.mainloop()
