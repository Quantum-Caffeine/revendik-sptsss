"""Scrollable frame component for flexible screen resolutions."""

import platform
import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame using a Canvas and Scrollbar.
    Handles mousewheel scrolling across Windows, macOS, and Linux.
    """

    def __init__(self, parent: tk.Widget, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = ttk.Frame(self.canvas)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_content, anchor="nw"
        )
        self.canvas.configure(xscrollcommand=None, yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self._bind_mousewheel(self)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """Keep the internal frame width matching canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, widget: tk.Widget) -> None:
        """Recursively bind mouse wheel to widget and children."""
        system = platform.system()
        if system == "Linux":
            widget.bind("<Button-4>", self._on_mousewheel_linux_up, add="+")
            widget.bind("<Button-5>", self._on_mousewheel_linux_down, add="+")
        else:
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")

        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def bind_child_mousewheel(self, widget: tk.Widget) -> None:
        """Call this to bind mousewheel to dynamically added children."""
        self._bind_mousewheel(widget)

    def _on_mousewheel(self, event: tk.Event) -> None:
        # On Windows, event.delta is typically +/- 120
        delta = -1 * int(event.delta / 120)
        self.canvas.yview_scroll(delta, "units")

    def _on_mousewheel_linux_up(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_linux_down(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(1, "units")

    def scroll_to_top(self) -> None:
        """Scroll view back to the top."""
        self.canvas.yview_moveto(0.0)

    def scroll_to_bottom(self) -> None:
        """Scroll view to the bottom."""
        self.canvas.yview_moveto(1.0)
