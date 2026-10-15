"""Tab 2: Formulaire de Retrait de griefs."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Callable, Dict, List, Optional

from revendik.config import AppConfig, PathManager, get_today_date_fr, open_folder
from revendik.drafts import DraftManager
from revendik.models import MOTIFS_RETRAIT, GrievanceRetrait, GrievanceRetraitItem
from revendik.pdf import PDFGenerator
from revendik.renderer import TemplateRenderer
from revendik.signatures import SignatureManager
from revendik.ui.components.scrollable import ScrollableFrame


class RetraitTab(ttk.Frame):
    """View and controller for Grievance Withdrawals (Retrait)."""

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

        self.grief_rows: List[Dict[str, Any]] = []

        self._build_ui()
        self.reset_form()

    def _build_ui(self) -> None:
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

        # Container for dynamic grief cards
        self.griefs_container = ttk.Frame(content)
        self.griefs_container.pack(fill="x", padx=12, pady=5)

        # Button to add another grievance
        add_btn_frame = ttk.Frame(content)
        add_btn_frame.pack(fill="x", padx=12, pady=5)
        self.btn_add_grief = ttk.Button(
            add_btn_frame,
            text="➕ Ajouter un grief à la liste",
            command=self.add_grief_row,
        )
        self.btn_add_grief.pack(side="left")

        # --- Motif du retrait ---
        motif_frame = ttk.LabelFrame(content, text=" 📋 Motif du retrait ", padding=10)
        motif_frame.pack(fill="x", padx=12, pady=6)
        self.var_motif = tk.StringVar(value=MOTIFS_RETRAIT[0])
        self.combo_motif = ttk.Combobox(
            motif_frame,
            textvariable=self.var_motif,
            values=MOTIFS_RETRAIT,
            state="readonly",
        )
        self.combo_motif.pack(fill="x", expand=True)

        # --- Signature ---
        f_sig = ttk.LabelFrame(content, text=" ✍️ Signature de l'agent syndical ", padding=10)
        f_sig.pack(fill="x", padx=12, pady=6)
        self.combo_sig = ttk.Combobox(f_sig, state="readonly")
        self.combo_sig.pack(fill="x", expand=True)

        # --- Action Buttons ---
        act_frame = ttk.Frame(content)
        act_frame.pack(fill="x", padx=12, pady=(15, 20))

        self.btn_preview = ttk.Button(
            act_frame,
            text="👁️ Aperçu (Navigateur)",
            command=self.preview_retrait,
            style="Action.TButton",
        )
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_generate = ttk.Button(
            act_frame,
            text="📄 GÉNÉRER LE RETRAIT (PDF)",
            command=self.generate_retrait,
            style="Danger.TButton",
        )
        self.btn_generate.pack(side="right", fill="x", expand=True, padx=(6, 0))

        self.scroll_frame.bind_child_mousewheel(content)

    def add_grief_row(
        self,
        item: Optional[GrievanceRetraitItem] = None,
        is_first: bool = False,
    ) -> None:
        """Add a grievance card to the withdrawal form."""
        idx = len(self.grief_rows) + 1
        label_text = f" Grief #{idx} (Obligatoire) " if idx == 1 else f" Grief #{idx} "
        frame = ttk.LabelFrame(self.griefs_container, text=label_text, padding=8)
        frame.pack(fill="x", pady=4)

        # Row 0: N° grief
        ttk.Label(frame, text="N° de grief :").grid(row=0, column=0, sticky="w", pady=2)
        ent_num = ttk.Entry(frame)
        ent_num.grid(row=0, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Row 1: Nom
        ttk.Label(frame, text="Nom complet :").grid(row=1, column=0, sticky="w", pady=2)
        ent_nom = ttk.Entry(frame)
        ent_nom.grid(row=1, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Row 2: Matricule
        ttk.Label(frame, text="Matricule :").grid(row=2, column=0, sticky="w", pady=2)
        ent_mat = ttk.Entry(frame)
        ent_mat.grid(row=2, column=1, sticky="ew", pady=2, padx=(5, 0))

        frame.columnconfigure(1, weight=1)

        row_dict: Dict[str, Any] = {
            "frame": frame,
            "ent_num": ent_num,
            "ent_nom": ent_nom,
            "ent_mat": ent_mat,
        }

        if idx > 1:
            btn_del = ttk.Button(
                frame,
                text="🗑️ Supprimer ce grief",
                command=lambda r=row_dict: self.remove_grief_row(r),
            )
            btn_del.grid(row=3, column=1, sticky="e", pady=(4, 0))
            row_dict["btn_del"] = btn_del

        if item:
            ent_num.insert(0, item.num)
            ent_nom.insert(0, item.nom)
            ent_mat.insert(0, item.mat)

        self.grief_rows.append(row_dict)
        self.scroll_frame.bind_child_mousewheel(frame)

    def remove_grief_row(self, row_dict: Dict[str, Any]) -> None:
        """Remove a grievance card."""
        if len(self.grief_rows) <= 1:
            return
        if row_dict in self.grief_rows:
            self.grief_rows.remove(row_dict)
            row_dict["frame"].destroy()
            self._reindex_rows()

    def _reindex_rows(self) -> None:
        """Update header titles for remaining cards."""
        for i, row in enumerate(self.grief_rows, start=1):
            title = f" Grief #{i} (Obligatoire) " if i == 1 else f" Grief #{i} "
            row["frame"].configure(text=title)

    def clear_grief_rows(self) -> None:
        """Remove all current cards."""
        for row in self.grief_rows:
            row["frame"].destroy()
        self.grief_rows.clear()

    def update_signatures_list(self) -> None:
        """Refresh signatures dropdown."""
        sigs = self.sig_manager.list_signatures()
        self.combo_sig["values"] = sigs
        current = self.combo_sig.get()
        if not current and self.config.signature_defaut in sigs:
            self.combo_sig.set(self.config.signature_defaut)
        elif current not in sigs and sigs:
            self.combo_sig.set(sigs[0] if self.config.signature_defaut not in sigs else self.config.signature_defaut)

    def get_model(self) -> GrievanceRetrait:
        """Construct model from form."""
        items: List[GrievanceRetraitItem] = []
        for row in self.grief_rows:
            num = row["ent_num"].get().strip()
            nom = row["ent_nom"].get().strip()
            mat = row["ent_mat"].get().strip()
            items.append(GrievanceRetraitItem(num=num, nom=nom, mat=mat))

        return GrievanceRetrait(
            griefs=items,
            motif=self.var_motif.get(),
            signature_nom=self.combo_sig.get(),
            date_retrait=get_today_date_fr(),
        )

    def populate_form(self, retrait: GrievanceRetrait) -> None:
        """Populate form from model."""
        self.clear_grief_rows()
        if not retrait.griefs:
            self.add_grief_row(is_first=True)
        else:
            for i, item in enumerate(retrait.griefs):
                self.add_grief_row(item=item, is_first=(i == 0))

        if retrait.motif in MOTIFS_RETRAIT:
            self.var_motif.set(retrait.motif)
        elif retrait.motif:
            self.combo_motif["values"] = list(MOTIFS_RETRAIT) + [retrait.motif]
            self.var_motif.set(retrait.motif)

        if retrait.signature_nom:
            self.combo_sig.set(retrait.signature_nom)

    def reset_form(self) -> None:
        """Reset form to 1 blank row."""
        self.clear_grief_rows()
        self.add_grief_row(is_first=True)
        self.var_motif.set(MOTIFS_RETRAIT[0])
        self.update_signatures_list()
        self.set_status("Formulaire de retrait réinitialisé.")

    def confirm_reset(self) -> None:
        if messagebox.askyesno("Réinitialiser", "Voulez-vous réinitialiser le formulaire de retrait ?"):
            self.reset_form()

    def save_draft(self) -> None:
        """Save current form as draft JSON file."""
        retrait = self.get_model()
        first_num = "sans_numero"
        for g in retrait.griefs:
            if g.num:
                first_num = g.num.replace("/", "-")
                break
        dest = filedialog.asksaveasfilename(
            initialdir=self.paths.get_path("sauvegardes"),
            initialfile=f"brouillon_retrait_{first_num}.json",
            defaultextension=".json",
            filetypes=[("Brouillons Revendik JSON", "*.json")],
        )
        if dest:
            try:
                self.draft_manager.save_retrait_draft(retrait, dest)
                self.set_status(f"Brouillon de retrait sauvegardé : {os.path.basename(dest)}")
                messagebox.showinfo("Succès", "Le brouillon du retrait a été sauvegardé avec succès !")
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
                retrait = self.draft_manager.load_retrait_draft(filepath)
                self.populate_form(retrait)
                self.set_status(f"Brouillon chargé : {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le brouillon :\n{e}")

    def _render_current_html(self) -> str:
        retrait = self.get_model()
        sig_name = self.combo_sig.get()
        sig_config = self.sig_manager.get_signature(sig_name) if sig_name else None
        sig_img_path = self.sig_manager.get_image_path(sig_config) if sig_config else None
        return self.renderer.render_retrait(retrait, sig_config, sig_img_path)

    def preview_retrait(self) -> None:
        """Render and open HTML in default browser for fast visual preview."""
        retrait = self.get_model()
        errors = retrait.validate()
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
            self.set_status("Aperçu de retrait ouvert dans votre navigateur web.")
        except Exception as e:
            messagebox.showerror("Erreur d'aperçu", str(e))

    def generate_retrait(self) -> None:
        """Validate, auto-save draft, and generate PDF export."""
        retrait = self.get_model()
        errors = retrait.validate()
        if errors:
            messagebox.showerror("Validation requise", "\n".join(f"• {e}" for e in errors))
            return

        # Auto-save draft
        try:
            auto_path = self.draft_manager.auto_save_retrait(retrait)
            self.set_status(f"Sauvegarde automatique créée : {os.path.basename(auto_path)}")
        except Exception:
            pass

        pdf_filename = retrait.sanitize_filename()
        pdf_path = os.path.join(self.paths.get_path("exports_retraits"), pdf_filename)

        try:
            html = self._render_current_html()
            self.pdf_gen.render_and_export(html, pdf_path)
            self.set_status(f"Retrait généré avec succès : {pdf_filename}")

            if messagebox.askyesno(
                "Succès",
                f"Le retrait de grief a été généré avec succès :\n{pdf_filename}\n\nOuvrir le dossier d'exportation ?",
            ):
                open_folder(self.paths.get_path("exports_retraits"))
        except Exception as e:
            messagebox.showerror("Erreur de génération", str(e))
