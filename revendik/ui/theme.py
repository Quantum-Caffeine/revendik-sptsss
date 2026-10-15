"""Visual theme, colors, and styles for Revendik-SPTSSS."""

import tkinter as tk
from tkinter import ttk


class Theme:
    """Color palette and font constants."""

    BG_MAIN = "#f8fafc"
    BG_CARD = "#ffffff"
    BORDER_COLOR = "#e2e8f0"

    TEXT_MAIN = "#0f172a"
    TEXT_MUTED = "#64748b"

    COLOR_PRIMARY = "#2563eb"
    COLOR_SUCCESS = "#16a34a"
    COLOR_DANGER = "#dc2626"
    COLOR_WARNING = "#d97706"

    FONT_TITLE = ("Segoe UI", 12, "bold")
    FONT_SUBTITLE = ("Segoe UI", 10, "bold")
    FONT_BODY = ("Segoe UI", 9)
    FONT_LABEL = ("Segoe UI", 9, "bold")
    FONT_BUTTON = ("Segoe UI", 10, "bold")
    FONT_SMALL = ("Segoe UI", 8)


def apply_theme(root: tk.Tk) -> ttk.Style:
    """Configure modern ttk styles."""
    style = ttk.Style(root)
    # Use 'clam' for consistent cross-platform styling if available
    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")

    # General widget configurations
    style.configure(".", font=Theme.FONT_BODY, foreground=Theme.TEXT_MAIN)
    style.configure("TLabel", font=Theme.FONT_BODY, foreground=Theme.TEXT_MAIN)
    style.configure("Header.TLabel", font=Theme.FONT_TITLE, foreground=Theme.TEXT_MAIN)
    style.configure("Subheader.TLabel", font=Theme.FONT_SUBTITLE, foreground=Theme.TEXT_MUTED)

    # Notebook styles
    style.configure("TNotebook", background=Theme.BG_MAIN, tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab", font=Theme.FONT_SUBTITLE, padding=[12, 6])
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#ffffff"), ("!selected", "#e2e8f0")],
        foreground=[("selected", Theme.COLOR_PRIMARY), ("!selected", Theme.TEXT_MUTED)],
    )

    # Card / LabelFrame styling
    style.configure(
        "Card.TLabelframe",
        background=Theme.BG_CARD,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "Card.TLabelframe.Label",
        font=Theme.FONT_SUBTITLE,
        foreground=Theme.COLOR_PRIMARY,
        background=Theme.BG_CARD,
    )

    # Button styles
    style.configure(
        "Primary.TButton",
        font=Theme.FONT_BUTTON,
        padding=[10, 6],
    )
    style.configure(
        "Success.TButton",
        font=Theme.FONT_BUTTON,
        background=Theme.COLOR_SUCCESS,
        foreground="#ffffff",
        padding=[12, 8],
    )
    style.map(
        "Success.TButton",
        background=[("active", "#15803d"), ("pressed", "#166534")],
    )

    style.configure(
        "Danger.TButton",
        font=Theme.FONT_BUTTON,
        background=Theme.COLOR_DANGER,
        foreground="#ffffff",
        padding=[12, 8],
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#b91c1c"), ("pressed", "#991b1b")],
    )

    style.configure(
        "Action.TButton",
        font=Theme.FONT_BUTTON,
        background=Theme.COLOR_PRIMARY,
        foreground="#ffffff",
        padding=[10, 6],
    )
    style.map(
        "Action.TButton",
        background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
    )

    return style
