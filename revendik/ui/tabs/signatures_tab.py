"""Tab 3: Gestion visuelle des signatures d'agents."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Any, Callable, Dict, Optional
from PIL import Image, ImageTk

from revendik.config import AppConfig, PathManager
from revendik.models import SignatureConfig
from revendik.signatures import SignatureManager, css_to_coords
from revendik.ui.components.scrollable import ScrollableFrame


class SignaturesTab(ttk.Frame):
    """Visual interactive signature positioning and scaling editor."""

    def __init__(
        self,
        parent: tk.Widget,
        paths: PathManager,
        config: AppConfig,
        sig_manager: SignatureManager,
        on_signatures_changed: Callable[[], None],
        set_status: Callable[[str], None],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.paths = paths
        self.config = config
        self.sig_manager = sig_manager
        self.on_signatures_changed = on_signatures_changed
        self.set_status = set_status

        # Canvas image state
        self.img_state: Dict[str, Any] = {
            "original": None,
            "photo": None,
            "x": 10.0,
            "y": 145.0,
            "filepath": None,
            "drag_data": None,
        }

        self._build_ui()
        self.refresh_signatures_dropdown()

    def _build_ui(self) -> None:
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        content = self.scroll_frame.scrollable_content

        # --- Section 1: Signatures existantes ---
        f_existing = ttk.LabelFrame(content, text=" 📂 Signatures enregistrées ", padding=10)
        f_existing.pack(fill="x", padx=12, pady=(10, 6))

        self.combo_signatures = ttk.Combobox(f_existing, state="readonly")
        self.combo_signatures.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_load = ttk.Button(f_existing, text="Charger", command=self.load_selected_signature)
        btn_load.pack(side="left", padx=3)

        btn_default = ttk.Button(
            f_existing, text="Définir par défaut", command=self.set_default_signature
        )
        btn_default.pack(side="left", padx=3)

        btn_delete = ttk.Button(
            f_existing, text="Supprimer", style="Danger.TButton", command=self.delete_selected_signature
        )
        btn_delete.pack(side="left", padx=3)

        # --- Section 2: Canvas d'édition ---
        f_editor = ttk.LabelFrame(content, text=" ✏️ Éditeur visuel et alignement ", padding=10)
        f_editor.pack(fill="both", expand=True, padx=12, pady=6)

        btn_import = ttk.Button(
            f_editor,
            text="🖼️ Importer une nouvelle image...",
            command=self.import_image,
        )
        btn_import.pack(pady=(0, 8))

        # Canvas with baseline guide
        canvas_container = ttk.Frame(f_editor)
        canvas_container.pack(pady=4)

        self.canvas = tk.Canvas(
            canvas_container,
            width=420,
            height=210,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
        )
        self.canvas.pack()

        # Visual baseline guide at y=150
        self.canvas.create_line(10, 150, 410, 150, fill="#94a3b8", width=2)
        self.canvas.create_text(
            12, 155, text="LIGNE DE SIGNATURE (BASELINE)", anchor="nw", fill="#64748b", font=("Segoe UI", 8)
        )
        self.canvas_img_id = self.canvas.create_image(
            self.img_state["x"], self.img_state["y"], anchor="sw"
        )

        # Mouse drag bindings
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)

        # Scale slider
        scale_frame = ttk.Frame(f_editor)
        scale_frame.pack(fill="x", padx=30, pady=8)

        self.scale_var = tk.DoubleVar(value=0.5)
        ttk.Label(scale_frame, text="Taille / Échelle de l'image :").pack(anchor="w")

        self.scale_slider = ttk.Scale(
            scale_frame,
            from_=0.1,
            to=2.0,
            value=0.5,
            orient="horizontal",
            variable=self.scale_var,
            command=self._on_scale_changed,
        )
        self.scale_slider.pack(fill="x", pady=2)

        # Save button
        btn_save = ttk.Button(
            f_editor,
            text="💾 Sauvegarder la signature",
            command=self.save_signature,
            style="Action.TButton",
        )
        btn_save.pack(pady=(12, 5))

        self.scroll_frame.bind_child_mousewheel(content)

    def refresh_signatures_dropdown(self) -> None:
        """Update signatures list."""
        sigs = self.sig_manager.list_signatures()
        self.combo_signatures["values"] = sigs
        if sigs:
            if self.config.signature_defaut in sigs:
                self.combo_signatures.set(self.config.signature_defaut)
            elif not self.combo_signatures.get():
                self.combo_signatures.set(sigs[0])
        else:
            self.combo_signatures.set("")

    def _on_drag_start(self, event: tk.Event) -> None:
        if self.img_state["original"]:
            self.img_state["drag_data"] = {"x": event.x, "y": event.y}

    def _on_drag_motion(self, event: tk.Event) -> None:
        if self.img_state["original"] and self.img_state.get("drag_data"):
            dx = event.x - self.img_state["drag_data"]["x"]
            dy = event.y - self.img_state["drag_data"]["y"]
            self.img_state["x"] += dx
            self.img_state["y"] += dy
            self.canvas.coords(self.canvas_img_id, self.img_state["x"], self.img_state["y"])
            self.img_state["drag_data"] = {"x": event.x, "y": event.y}

    def _on_scale_changed(self, *args) -> None:
        self.update_canvas_image()

    def update_canvas_image(self) -> None:
        """Redraw resized image on canvas at current position."""
        orig: Optional[Image.Image] = self.img_state.get("original")
        if orig:
            w, h = orig.size
            scale = max(0.05, self.scale_var.get())
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            resized = orig.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.img_state["photo"] = ImageTk.PhotoImage(resized)
            self.canvas.coords(self.canvas_img_id, self.img_state["x"], self.img_state["y"])
            self.canvas.itemconfig(self.canvas_img_id, image=self.img_state["photo"])

    def import_image(self) -> None:
        """Prompt user for signature image file and load onto canvas."""
        filepath = filedialog.askopenfilename(
            filetypes=[("Fichiers Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        if filepath:
            try:
                img = self.sig_manager.prepare_imported_image(filepath)
                self.img_state["original"] = img
                self.img_state["filepath"] = filepath
                self.img_state["x"] = 10.0
                self.img_state["y"] = 145.0
                self.scale_var.set(0.5)
                self.update_canvas_image()
                self.set_status(f"Image importée : {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Erreur d'importation", f"Impossible d'ouvrir l'image :\n{e}")

    def load_selected_signature(self) -> None:
        """Load currently selected signature from dropdown into canvas editor."""
        name = self.combo_signatures.get()
        if not name:
            return
        sig = self.sig_manager.get_signature(name)
        if not sig:
            messagebox.showerror("Erreur", f"Signature '{name}' introuvable.")
            return

        img_path = self.sig_manager.get_image_path(sig)
        if not img_path or not os.path.exists(img_path):
            messagebox.showerror("Erreur", f"L'image pour la signature '{name}' est introuvable.")
            return

        try:
            self.img_state["original"] = Image.open(img_path).convert("RGBA")
            self.img_state["filepath"] = img_path
            x, y = css_to_coords(sig.css_left, sig.css_bottom)
            self.img_state["x"] = x
            self.img_state["y"] = y
            self.scale_var.set(sig.tk_scale or 0.5)
            self.update_canvas_image()
            self.set_status(f"Signature '{name}' chargée dans l'éditeur.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger la signature :\n{e}")

    def save_signature(self) -> None:
        """Save current canvas position and scale as named signature."""
        if not self.img_state.get("original"):
            messagebox.showwarning(
                "Image manquante", "Veuillez d'abord importer une image de signature."
            )
            return

        initial = self.combo_signatures.get() or ""
        name = simpledialog.askstring(
            "Sauvegarder", "Nom de la personne / signature :", initialvalue=initial, parent=self
        )
        if not name or not name.strip():
            return
        name = name.strip()

        try:
            config = self.sig_manager.save_signature(
                name=name,
                image=self.img_state["original"],
                x=self.img_state["x"],
                y=self.img_state["y"],
                scale=self.scale_var.get(),
            )
            self.set_status(f"Signature sauvegardée : {name}")
            messagebox.showinfo("Succès", f"La signature '{name}' a été enregistrée avec succès !")
            self.refresh_signatures_dropdown()
            self.combo_signatures.set(name)
            self.on_signatures_changed()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder la signature :\n{e}")

    def delete_selected_signature(self) -> None:
        """Delete currently selected signature."""
        name = self.combo_signatures.get()
        if not name:
            return
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la signature '{name}' ?"):
            if self.sig_manager.delete_signature(name):
                if self.config.signature_defaut == name:
                    self.config.signature_defaut = ""
                    self.config.save(self.paths.config_file)
                self.canvas.itemconfig(self.canvas_img_id, image="")
                self.img_state["original"] = None
                self.refresh_signatures_dropdown()
                self.on_signatures_changed()
                self.set_status(f"Signature '{name}' supprimée.")
                messagebox.showinfo("Succès", f"Signature '{name}' supprimée.")
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer la signature.")

    def set_default_signature(self) -> None:
        """Set current selected signature as application default."""
        name = self.combo_signatures.get()
        if not name:
            messagebox.showwarning("Sélection", "Veuillez sélectionner une signature.")
            return
        self.config.signature_defaut = name
        self.config.save(self.paths.config_file)
        self.on_signatures_changed()
        self.set_status(f"Signature '{name}' définie par défaut.")
        messagebox.showinfo("Succès", f"'{name}' est maintenant la signature par défaut.")
