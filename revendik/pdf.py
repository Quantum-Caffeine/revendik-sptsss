"""PDF conversion and browser discovery."""

import os
import platform
import shutil
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from typing import Optional, Tuple


def find_browser() -> Optional[str]:
    """
    Search for a compatible Chromium-based browser (Chrome, Edge, Chromium)
    across Windows, macOS, and Linux.
    """
    system = platform.system()
    candidates = []

    if system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

        candidates = [
            # Google Chrome
            os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
            # Microsoft Edge
            os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(local_app_data, "Microsoft", "Edge", "Application", "msedge.exe"),
            # Brave
            os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        ]
        # Also check PATH
        for binary in ("chrome.exe", "msedge.exe", "chromium.exe"):
            p = shutil.which(binary)
            if p:
                candidates.append(p)

    elif system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
    else:  # Linux / BSD
        binaries = [
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
            "microsoft-edge",
            "microsoft-edge-stable",
            "brave-browser",
        ]
        for binary in binaries:
            p = shutil.which(binary)
            if p:
                candidates.append(p)

    for path in candidates:
        if path and (os.path.exists(path) or shutil.which(path)):
            return path

    return None


def detect_browser_info() -> Tuple[bool, str]:
    """Return status (found: bool) and descriptive message or path."""
    browser = find_browser()
    if browser:
        name = os.path.basename(browser).replace(".exe", "")
        return True, f"{name.capitalize()} ({browser})"
    return False, "Aucun navigateur Chromium/Edge détecté"


class PDFGenerator:
    """Handles rendering HTML to PDF via headless browser."""

    def __init__(self, browser_path: Optional[str] = None) -> None:
        self.browser_path = browser_path or find_browser()

    def ensure_browser(self) -> str:
        """Ensure a browser is available or raise FileNotFoundError."""
        if not self.browser_path or not (
            os.path.exists(self.browser_path) or shutil.which(self.browser_path)
        ):
            self.browser_path = find_browser()

        if not self.browser_path:
            hint = ""
            if platform.system() == "Linux":
                hint = " Installez Chromium ou Google Chrome via 'sudo apt install chromium'."
            elif platform.system() == "Windows":
                hint = " Assurez-vous que Microsoft Edge ou Google Chrome est installé."
            raise FileNotFoundError(
                "Aucun navigateur compatible (Chrome, Edge ou Chromium) n'a été trouvé." + hint
            )
        return self.browser_path

    def convert_html_to_pdf(self, html_path: str, output_pdf_path: str) -> None:
        """Run headless browser command to print HTML to PDF."""
        browser_cmd = self.ensure_browser()
        out_abs = os.path.abspath(output_pdf_path)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)

        html_abs = os.path.abspath(html_path)
        uri = Path(html_abs).resolve().as_uri()

        command = [
            browser_cmd,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_abs}",
            uri,
        ]

        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Délai d'attente dépassé lors de la génération du PDF.")
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"Erreur du navigateur lors de la conversion PDF: {err_msg}")

    def render_and_export(self, html_content: str, output_pdf_path: str) -> str:
        """Write HTML to a secure temporary file and convert to target PDF path."""
        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name

        try:
            self.convert_html_to_pdf(tmp_path, output_pdf_path)
            return output_pdf_path
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    @staticmethod
    def preview_html(html_content: str) -> str:
        """Write HTML content to temporary file and open in default web browser."""
        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name

        uri = Path(tmp_path).resolve().as_uri()
        webbrowser.open(uri)
        return tmp_path
