"""Tab 1: Formulaire de Dépôt de grief."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional

from revendik.config import AppConfig, PathManager, get_today_date_fr, open_folder
from revendik.drafts import DraftManager
from revendik.models import GrievanceDepot
from revendik.pdf import PDFGenerator
from revendik.renderer import TemplateRenderer
from revendik.signatures import SignatureManager
from revendik.ui.components.scrollable import ScrollableFrame
from revendik.ui.theme import Theme


class DepotTab(ttk.Frame):
    """View and controller for Grievance Submissions (Dépôt)."""

    def __init__(
        self,
        parent: tk.Widget,
        paths: PathManager,
        config: AppConfig,
        renderer: TemplateRenderer,
        pdf_gen: PDFGenerator,
        sig_manager: SignatureManager,
        draft_manager: DraftManager,
        set_status: Callable[[str], None],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.paths = paths
        self.config = config
        self.renderer = renderer
        self.pdf_gen = pdf_gen
        self.sig_manager = sig_manager
        self.draft_manager = draft_manager
        self.set_status = set_status

        self._build_ui()
        self.reset_form()

    def _build_ui(self) -> None:
        # Wrap everything in a smooth scrollable container
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        content = self.scroll_frame.scrollable_content

        # --- Draft Toolbar ---
        tb = ttk.Frame(content)
        tb.pack(fill="x", padx=12, pady=(10, 5))

        btn_load = ttk.Button(tb, text="📁 Charger brouillon", command=self.load_draft)
        btn_load.pack(side="left", padx=(0, 6))

        btn_save = ttk.Button(tb, text="💾 Sauvegarder brouillon", command=self.save_draft)
        btn_save.pack(side="left", padx=6)

        btn_reset = ttk.Button(tb, text="🔄 Réinitialiser", command=self.confirm_reset)
        btn_reset.pack(side="left", padx=6)

        # --- Card 1: Employé & Dossier ---
        f1 = ttk.LabelFrame(content, text=" 👤 Informations Salarié & Dossier ", padding=10)
        f1.pack(fill="x", padx=12, pady=6)

        ttk.Label(f1, text="Numéro de grief * :").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_nogrief = ttk.Entry(f1)
        self.ent_nogrief.grid(row=0, column=1, sticky="ew", pady=3, padx=(5, 0))

        ttk.Label(f1, text="Nom complet * :").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_nom = ttk.Entry(f1)
        self.ent_nom.grid(row=1, column=1, sticky="ew", pady=3, padx=(5, 0))

        ttk.Label(f1, text="No. Employé / Matricule :").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_no_emp = ttk.Entry(f1)
        self.ent_no_emp.grid(row=2, column=1, sticky="ew", pady=3, padx=(5, 0))

        ttk.Label(f1, text="Titre d'emploi :").grid(row=3, column=0, sticky="w", pady=3)
        self.ent_titre = ttk.Entry(f1)
        self.ent_titre.grid(row=3, column=1, sticky="ew", pady=3, padx=(5, 0))
        f1.columnconfigure(1, weight=1)

        # --- Card 2: Lieu & Date ---
        f2 = ttk.LabelFrame(content, text=" 🏥 Lieu, Affectation & Date ", padding=10)
        f2.pack(fill="x", padx=12, pady=6)

        ttk.Label(f2, text="Installation :").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_inst = ttk.Entry(f2)
        self.ent_inst.grid(row=0, column=1, sticky="ew", pady=3, padx=(5, 0))

        ttk.Label(f2, text="Service :").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_serv = ttk.Entry(f2)
        self.ent_serv.grid(row=1, column=1, sticky="ew", pady=3, padx=(5, 0))

        ttk.Label(f2, text="Établissement :").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_etab = ttk.Entry(f2)
        self.ent_etab.grid(row=2, column=1, sticky="ew", pady=3, padx=(5, 0))

        ttk.Label(f2, text="Date de dépôt :").grid(row=3, column=0, sticky="w", pady=3)
        self.ent_date = ttk.Entry(f2)
        self.ent_date.grid(row=3, column=1, sticky="ew", pady=3, padx=(5, 0))
        f2.columnconfigure(1, weight=1)

        # --- Card 3: Type de grief ---
        f3 = ttk.LabelFrame(content, text=" 🏷️ Type de grief ", padding=10)
        f3.pack(fill="x", padx=12, pady=6)
        self.var_type = tk.StringVar(value="Individuel")
        for val in ("Individuel", "Groupe", "Syndical"):
            r = ttk.Radiobutton(f3, text=val, variable=self.var_type, value=val)
            r.pack(side="left", padx=15)

        # --- Card 4: Signature ---
        f4 = ttk.LabelFrame(content, text=" ✍️ Signature de l'agent syndical ", padding=10)
        f4.pack(fill="x", padx=12, pady=6)
        self.combo_sig = ttk.Combobox(f4, state="readonly")
        self.combo_sig.pack(fill="x", expand=True)

        # --- Card 5: Description & Réclamation ---
        f5 = ttk.LabelFrame(content, text=" 📝 Description & Réclamation ", padding=10)
        f5.pack(fill="x", padx=12, pady=6)

        ttk.Label(f5, text="Description du grief (Détails) :").pack(anchor="w", pady=(2, 2))
        self.txt_desc = tk.Text(f5, height=7, wrap="word", relief="solid", borderwidth=1)
        self.txt_desc.pack(fill="x", expand=True, pady=(0, 8))

        ttk.Label(f5, text="Réclamation (Correctifs demandés) :").pack(anchor="w", pady=(2, 2))
        self.txt_recl = tk.Text(f5, height=5, wrap="word", relief="solid", borderwidth=1)
        self.txt_recl.pack(fill="x", expand=True, pady=(0, 4))

        # --- Action Buttons ---
        act_frame = ttk.Frame(content)
        act_frame.pack(fill="x", padx=12, pady=(15, 20))

        self.btn_preview = ttk.Button(
            act_frame,
            text="👁️ Aperçu (Navigateur)",
            command=self.preview_depot,
            style="Action.TButton",
        )
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_generate = ttk.Button(
            act_frame,
            text="📄 GÉNÉRER LE DÉPÔT (PDF)",
            command=self.generate_depot,
            style="Success.TButton",
        )
        self.btn_generate.pack(side="right", fill="x", expand=True, padx=(6, 0))

        self.scroll_frame.bind_child_mousewheel(content)

    def update_signatures_list(self) -> None:
        """Refresh signatures dropdown."""
        sigs = self.sig_manager.list_signatures()
        self.combo_sig["values"] = sigs
        current = self.combo_sig.get()
        if not current and self.config.signature_defaut in sigs:
            self.combo_sig.set(self.config.signature_defaut)
        elif current not in sigs and sigs:
            self.combo_sig.set(sigs[0] if self.config.signature_defaut not in sigs else self.config.signature_defaut)

    def get_model(self) -> GrievanceDepot:
        """Construct model from current form fields."""
        return GrievanceDepot(
            no_grief=self.ent_nogrief.get().strip(),
            nom=self.ent_nom.get().strip(),
            no_employe=self.ent_no_emp.get().strip(),
            titre=self.ent_titre.get().strip(),
            installation=self.ent_inst.get().strip(),
            service=self.ent_serv.get().strip(),
            etablissement=self.ent_etab.get().strip(),
            date=self.ent_date.get().strip(),
            type_grief=self.var_type.get(),
            signature_nom=self.combo_sig.get(),
            description=self.txt_desc.get("1.0", "end-1c").strip(),
            reclamation=self.txt_recl.get("1.0", "end-1c").strip(),
        )

    def populate_form(self, depot: GrievanceDepot) -> None:
        """Populate form with data from model."""
        self._set_entry(self.ent_nogrief, depot.no_grief)
        self._set_entry(self.ent_nom, depot.nom)
        self._set_entry(self.ent_no_emp, depot.no_employe)
        self._set_entry(self.ent_titre, depot.titre)
        self._set_entry(self.ent_inst, depot.installation)
        self._set_entry(self.ent_serv, depot.service)
        self._set_entry(self.ent_etab, depot.etablissement or self.config.etablissement_defaut)
        self._set_entry(self.ent_date, depot.date or get_today_date_fr())
        self.var_type.set(depot.type_grief or "Individuel")
        if depot.signature_nom:
            self.combo_sig.set(depot.signature_nom)
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", depot.description)
        self.txt_recl.delete("1.0", tk.END)
        self.txt_recl.insert("1.0", depot.reclamation)

    @staticmethod
    def _set_entry(entry: ttk.Entry, value: str) -> None:
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def reset_form(self) -> None:
        """Reset form fields to blank / defaults."""
        depot = GrievanceDepot(
            etablissement=self.config.etablissement_defaut,
            date=get_today_date_fr(),
            signature_nom=self.config.signature_defaut,
        )
        self.populate_form(depot)
        self.update_signatures_list()
        self.set_status("Formulaire de dépôt réinitialisé.")

    def confirm_reset(self) -> None:
        """Prompt user before resetting."""
        if messagebox.askyesno("Réinitialiser", "Voulez-vous réinitialiser tous les champs du dépôt ?"):
            self.reset_form()

    def save_draft(self) -> None:
        """Save current form as a draft JSON file."""
        depot = self.get_model()
        suggested_name = f"brouillon_depot_{depot.no_grief.replace('/', '-') or 'nouveau'}.json"
        dest = filedialog.asksaveasfilename(
            initialdir=self.paths.get_path("sauvegardes"),
            initialfile=suggested_name,
            defaultextension=".json",
            filetypes=[("Brouillons Revendik JSON", "*.json")],
        )
        if dest:
            try:
                self.draft_manager.save_depot_draft(depot, dest)
                self.set_status(f"Brouillon sauvegardé : {os.path.basename(dest)}")
                messagebox.showinfo("Succès", "Le brouillon du dépôt a été sauvegardé avec succès !")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")

    def load_draft(self, filepath: Optional[str] = None) -> None:
        """Load draft JSON into form."""
        if not filepath:
            filepath = filedialog.askopenfilename(
                initialdir=self.paths.get_path("sauvegardes"),
                filetypes=[("Brouillons Revendik JSON", "*.json")],
            )
        if filepath and os.path.exists(filepath):
            try:
                depot = self.draft_manager.load_depot_draft(filepath)
                self.populate_form(depot)
                self.set_status(f"Brouillon chargé : {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le brouillon :\n{e}")

    def _render_current_html(self) -> str:
        """Render the current model to HTML string."""
        depot = self.get_model()
        sig_name = self.combo_sig.get()
        sig_config = self.sig_manager.get_signature(sig_name) if sig_name else None
        sig_img_path = self.sig_manager.get_image_path(sig_config) if sig_config else None
        return self.renderer.render_depot(depot, sig_config, sig_img_path)

    def preview_depot(self) -> None:
        """Render and open HTML in default browser for fast visual preview."""
        depot = self.get_model()
        errors = depot.validate()
        if errors:
            msg = "\n".join(f"• {e}" for e in errors)
            if not messagebox.askyesno(
                "Avertissement validation",
                f"Certains champs recommandés sont manquants :\n\n{msg}\n\nContinuer l'aperçu quand même ?",
            ):
                return
        try:
            html = self._render_current_html()
            self.pdf_gen.preview_html(html)
            self.set_status("Aperçu ouvert dans votre navigateur web.")
        except Exception as e:
            messagebox.showerror("Erreur d'aperçu", str(e))

    def generate_depot(self) -> None:
        """Validate, auto-save draft, and generate PDF export."""
        depot = self.get_model()
        errors = depot.validate()
        if errors:
            messagebox.showerror("Validation requise", "\n".join(f"• {e}" for e in errors))
            return

        # Auto-save draft
        try:
            auto_path = self.draft_manager.auto_save_depot(depot)
            self.set_status(f"Sauvegarde automatique créée : {os.path.basename(auto_path)}")
        except Exception:
            pass

        pdf_filename = depot.sanitize_filename()
        pdf_path = os.path.join(self.paths.get_path("exports_griefs"), pdf_filename)

        try:
            html = self._render_current_html()
            self.pdf_gen.render_and_export(html, pdf_path)
            self.set_status(f"Dépôt généré avec succès : {pdf_filename}")

            if messagebox.askyesno(
                "Succès",
                f"Le grief a été généré avec succès :\n{pdf_filename}\n\nOuvrir le dossier d'exportation ?",
            ):
                open_folder(self.paths.get_path("exports_griefs"))
        except Exception as e:
            messagebox.showerror("Erreur de génération", str(e))
