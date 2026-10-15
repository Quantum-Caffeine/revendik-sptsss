"""Settings and preferences dialog."""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from revendik.config import AppConfig, PathManager, open_folder
from revendik.pdf import detect_browser_info
from revendik.signatures import SignatureManager


class SettingsDialog(tk.Toplevel):
    """Preferences and diagnostic settings dialog."""

    def __init__(
        self,
        parent: tk.Widget,
        paths: PathManager,
        config: AppConfig,
        sig_manager: SignatureManager,
        on_save_callback: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.paths = paths
        self.config = config
        self.sig_manager = sig_manager
        self.on_save_callback = on_save_callback

        self.title("Préférences - Revendik-SPTSSS")
        self.geometry("540x440")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 8}

        # --- Établissement & Signature ---
        f_general = ttk.LabelFrame(self, text=" ⚙️ Paramètres par défaut ", padding=12)
        f_general.pack(fill="x", **pad)

        ttk.Label(f_general, text="Établissement par défaut :").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_etab = ttk.Entry(f_general, width=38)
        self.ent_etab.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))
        self.ent_etab.insert(0, self.config.etablissement_defaut)

        ttk.Label(f_general, text="Signature par défaut :").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_sig = ttk.Combobox(f_general, state="readonly", width=36)
        self.combo_sig.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))
        sigs = [""] + self.sig_manager.list_signatures()
        self.combo_sig["values"] = sigs
        self.combo_sig.set(self.config.signature_defaut if self.config.signature_defaut in sigs else "")

        f_general.columnconfigure(1, weight=1)

        # --- Détection Navigateur ---
        f_browser = ttk.LabelFrame(self, text=" 🌐 Moteur de conversion PDF ", padding=12)
        f_browser.pack(fill="x", **pad)

        found, info = detect_browser_info()
        color = "#16a34a" if found else "#dc2626"
        symbol = "✓" if found else "✗"

        lbl_status = tk.Label(
            f_browser,
            text=f"{symbol} Statut : {'Navigateur opérationnel' if found else 'Aucun navigateur détecté'}",
            font=("Segoe UI", 9, "bold"),
            fg=color,
        )
        lbl_status.pack(anchor="w")

        lbl_path = ttk.Label(
            f_browser,
            text=info,
            wraplength=480,
            font=("Segoe UI", 8),
        )
        lbl_path.pack(anchor="w", pady=(4, 0))

        # --- Raccourcis dossiers ---
        f_folders = ttk.LabelFrame(self, text=" 📁 Accès rapide aux dossiers ", padding=12)
        f_folders.pack(fill="x", **pad)

        btn_box = ttk.Frame(f_folders)
        btn_box.pack(fill="x")

        ttk.Button(
            btn_box,
            text="Exports Griefs",
            command=lambda: open_folder(self.paths.get_path("exports_griefs")),
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_box,
            text="Exports Retraits",
            command=lambda: open_folder(self.paths.get_path("exports_retraits")),
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_box,
            text="Sauvegardes",
            command=lambda: open_folder(self.paths.get_path("sauvegardes")),
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_box,
            text="Signatures",
            command=lambda: open_folder(self.paths.get_path("signatures")),
        ).pack(side="left", padx=4)

        # --- Actions Dialog ---
        act_box = ttk.Frame(self)
        act_box.pack(side="bottom", fill="x", padx=16, pady=16)

        ttk.Button(act_box, text="Annuler", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(act_box, text="Enregistrer", style="Action.TButton", command=self.save_settings).pack(
            side="right"
        )

    def save_settings(self) -> None:
        """Persist settings to disk and invoke callback."""
        self.config.etablissement_defaut = self.ent_etab.get().strip()
        self.config.signature_defaut = self.combo_sig.get().strip()
        try:
            self.config.save(self.paths.config_file)
            self.on_save_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer les préférences :\n{e}")
