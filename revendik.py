import os
import sys
import base64
import json
import shutil
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageTk

# ==========================================
# GESTION DES DOSSIERS ET CONFIGURATION
# ==========================================
def obtenir_dossier_app():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.dirname(__file__))

BASE_DIR = obtenir_dossier_app()
DIRS = {
    "images": os.path.join(BASE_DIR, "data", "images"),
    "gabarits": os.path.join(BASE_DIR, "data", "gabarits"),
    "signatures": os.path.join(BASE_DIR, "config", "signatures"),
    "sauvegardes": os.path.join(BASE_DIR, "config", "sauvegardes"), # NOUVEAU DOSSIER
    "exports_griefs": os.path.join(BASE_DIR, "exports", "griefs"),
    "exports_retraits": os.path.join(BASE_DIR, "exports", "retraits de grief")
}

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"etablissement_defaut": "Santé-Québec - CIUSSS de la Capitale Nationale", "signature_defaut": ""}

def save_config(config_data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

config_app = load_config()

if sys.stdout is None: sys.stdout = open(os.devnull, "w")
if sys.stderr is None: sys.stderr = open(os.devnull, "w")

def encoder_image_base64(chemin_image):
    if not chemin_image or not os.path.exists(chemin_image): return None
    try:
        with open(chemin_image, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            ext = chemin_image.lower().split('.')[-1]
            mime_type = "image/png" if ext == "png" else "image/jpeg"
            return f"data:{mime_type};base64,{encoded_string}"
    except Exception: return None

def obtenir_date_jour_fr():
    mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    now = datetime.now()
    return f"{now.day} {mois_fr[now.month - 1]} {now.year}"

def ouvrir_dossier(chemin):
    if platform.system() == "Windows": os.startfile(chemin)
    elif platform.system() == "Darwin": subprocess.Popen(["open", chemin])
    else: subprocess.Popen(["xdg-open", chemin])

# ==========================================
# MOTEUR DE CONVERSION PDF
# ==========================================
def html_vers_pdf_via_navigateur(chemin_html, chemin_pdf):
    systeme = platform.system()
    navigateurs_possibles = []

    if systeme == "Windows":
        navigateurs_possibles = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        ]
    elif systeme == "Darwin":
        navigateurs_possibles = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        ]
    else:
        navigateurs_possibles = ["google-chrome", "chromium-browser", "chromium", "microsoft-edge"]

    navigateur_cmd = None
    for nav in navigateurs_possibles:
        if os.path.exists(nav) or systeme == "Linux":
            navigateur_cmd = nav
            break

    if not navigateur_cmd:
        raise FileNotFoundError("Aucun navigateur compatible (Chrome/Edge/Chromium) n'a été trouvé.")

    html_uri = f"file:///{os.path.abspath(chemin_html).replace(os.sep, '/')}"
    commande = [navigateur_cmd, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={os.path.abspath(chemin_pdf)}", html_uri]

    try:
        subprocess.run(commande, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Erreur PDF : {e.stderr.decode('utf-8', errors='ignore')}")

# ==========================================
# GESTION DES BROUILLONS (DÉPÔT ET RETRAIT)
# ==========================================
def sauvegarder_brouillon_depot():
    data = {
        "no_grief": ent_nogrief.get(), "nom": ent_nom.get(), "no_employe": ent_no_emp.get(),
        "titre": ent_titre.get(), "installation": ent_inst.get(), "service": ent_serv.get(),
        "etablissement": ent_etab.get(), "date": ent_date.get(), "type": var_type.get(),
        "signature": combo_sig.get(), "description": txt_desc.get("1.0", "end-1c"),
        "reclamation": txt_recl.get("1.0", "end-1c")
    }
    filepath = filedialog.asksaveasfilename(initialdir=DIRS["sauvegardes"], defaultextension=".json", filetypes=[("Fichiers JSON brouillon", "*.json")])
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Succès", "Le brouillon du dépôt a été sauvegardé !")

def charger_brouillon_depot():
    filepath = filedialog.askopenfilename(initialdir=DIRS["sauvegardes"], filetypes=[("Fichiers JSON brouillon", "*.json")])
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f: data = json.load(f)
            ent_nogrief.delete(0, tk.END); ent_nogrief.insert(0, data.get("no_grief", ""))
            ent_nom.delete(0, tk.END); ent_nom.insert(0, data.get("nom", ""))
            ent_no_emp.delete(0, tk.END); ent_no_emp.insert(0, data.get("no_employe", ""))
            ent_titre.delete(0, tk.END); ent_titre.insert(0, data.get("titre", ""))
            ent_inst.delete(0, tk.END); ent_inst.insert(0, data.get("installation", ""))
            ent_serv.delete(0, tk.END); ent_serv.insert(0, data.get("service", ""))
            ent_etab.delete(0, tk.END); ent_etab.insert(0, data.get("etablissement", config_app.get("etablissement_defaut", "")))
            ent_date.delete(0, tk.END); ent_date.insert(0, data.get("date", obtenir_date_jour_fr()))
            var_type.set(data.get("type", "Individuel"))
            combo_sig.set(data.get("signature", ""))
            txt_desc.delete("1.0", tk.END); txt_desc.insert("1.0", data.get("description", ""))
            txt_recl.delete("1.0", tk.END); txt_recl.insert("1.0", data.get("reclamation", ""))
        except Exception as e: messagebox.showerror("Erreur", f"Impossible de charger : {e}")

def sauvegarder_brouillon_retrait():
    griefs_liste = []
    for i in range(1, 5):
        griefs_liste.append({
            "num": entries_retrait[i]['num'].get(),
            "nom": entries_retrait[i]['nom'].get(),
            "mat": entries_retrait[i]['mat'].get()
        })
    data = {
        "griefs": griefs_liste,
        "motif": var_motif.get(),
        "signature": combo_sig_retrait.get()
    }
    filepath = filedialog.asksaveasfilename(initialdir=DIRS["sauvegardes"], defaultextension=".json", filetypes=[("Fichiers JSON brouillon", "*.json")])
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Succès", "Le brouillon du retrait a été sauvegardé !")

def charger_brouillon_retrait():
    filepath = filedialog.askopenfilename(initialdir=DIRS["sauvegardes"], filetypes=[("Fichiers JSON brouillon", "*.json")])
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f: data = json.load(f)
            griefs = data.get("griefs", [])
            for i in range(1, 5):
                entries_retrait[i]['num'].delete(0, tk.END)
                entries_retrait[i]['nom'].delete(0, tk.END)
                entries_retrait[i]['mat'].delete(0, tk.END)
                if i - 1 < len(griefs):
                    entries_retrait[i]['num'].insert(0, griefs[i-1].get("num", ""))
                    entries_retrait[i]['nom'].insert(0, griefs[i-1].get("nom", ""))
                    entries_retrait[i]['mat'].insert(0, griefs[i-1].get("mat", ""))
            var_motif.set(data.get("motif", motifs[0]))
            combo_sig_retrait.set(data.get("signature", ""))
        except Exception as e: messagebox.showerror("Erreur", f"Impossible de charger : {e}")

# ==========================================
# FONCTIONS GLOBALES
# ==========================================
def charger_liste_signatures():
    signatures = []
    if os.path.exists(DIRS["signatures"]):
        for f in os.listdir(DIRS["signatures"]):
            if f.endswith(".json"): signatures.append(f.replace(".json", ""))
    
    combo_sig['values'] = signatures
    combo_sig_retrait['values'] = signatures
    combo_gestion_sig['values'] = signatures
    
    if config_app.get("signature_defaut") in signatures:
        combo_sig.set(config_app["signature_defaut"])
        combo_sig_retrait.set(config_app["signature_defaut"])

def definir_etablissement_defaut():
    config_app['etablissement_defaut'] = ent_etab.get()
    save_config(config_app)
    messagebox.showinfo("Succès", "L'établissement actuel est défini par défaut.")

def recuperer_data_signature(nom_fichier):
    if not nom_fichier: return None
    chemin_json = os.path.join(DIRS["signatures"], f"{nom_fichier}.json")
    if os.path.exists(chemin_json):
        with open(chemin_json, 'r', encoding='utf-8') as f: return json.load(f)
    return None

def generer_depot():
    nom_gabarit = "gabarit.html"
    chemin_gabarit = os.path.join(DIRS["gabarits"], nom_gabarit)
    if not os.path.exists(chemin_gabarit):
        messagebox.showerror("Erreur", f"Le gabarit '{nom_gabarit}' est introuvable.")
        return

    no_grief = ent_nogrief.get().strip()
    if not no_grief:
        messagebox.showerror("Erreur", "Le numéro de grief est obligatoire.")
        return

    # --- SAUVEGARDE AUTOMATIQUE HORODATÉE ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    auto_brouillon_path = os.path.join(DIRS["sauvegardes"], f"depot_{no_grief.replace('/', '-')}_{timestamp}.json")
    data_brouillon = {
        "no_grief": no_grief, "nom": ent_nom.get(), "no_employe": ent_no_emp.get(),
        "titre": ent_titre.get(), "installation": ent_inst.get(), "service": ent_serv.get(),
        "etablissement": ent_etab.get(), "date": ent_date.get(), "type": var_type.get(),
        "signature": combo_sig.get(), "description": txt_desc.get("1.0", "end-1c"),
        "reclamation": txt_recl.get("1.0", "end-1c")
    }
    with open(auto_brouillon_path, "w", encoding="utf-8") as f:
        json.dump(data_brouillon, f, ensure_ascii=False, indent=4)
    # ----------------------------------------

    sig_data = recuperer_data_signature(combo_sig.get())
    sig_img_base64 = ""; sig_b = 2; sig_l = 0; sig_w = 200
    
    if sig_data:
        chemin_img = os.path.join(DIRS["signatures"], sig_data["image"])
        sig_img_base64 = encoder_image_base64(chemin_img)
        sig_b = sig_data.get("css_bottom", 2)
        sig_l = sig_data.get("css_left", 0)
        sig_w = sig_data.get("css_width", 200)

    data = {
        "no_grief": no_grief, "nom_employe": ent_nom.get(), "no_employe": ent_no_emp.get(),
        "titre_emploi": ent_titre.get(), "installation": ent_inst.get(), "service": ent_serv.get(),
        "etablissement": ent_etab.get(), "date_depot": ent_date.get(),
        "description_grief": txt_desc.get("1.0", "end-1c").replace('\n', '<br>'),
        "reclamation_grief": txt_recl.get("1.0", "end-1c").replace('\n', '<br>'),
        "logo_base64": encoder_image_base64(os.path.join(DIRS["images"], "SPTSSS logo.png")) or "",
        "signature_img_base64": sig_img_base64, "signature_text": ent_nom.get(),
        "sig_bottom": sig_b, "sig_left": sig_l, "sig_width": sig_w,
        "i": "checked" if var_type.get() == "Individuel" else "",
        "g": "checked" if var_type.get() == "Groupe" else "",
        "s": "checked" if var_type.get() == "Syndical" else ""
    }

    nom_pdf = f"Grief_{no_grief.replace('/', '-')}.pdf"
    chemin_export = os.path.join(DIRS["exports_griefs"], nom_pdf)
    chemin_html_tmp = os.path.join(DIRS["gabarits"], "temp_render.html")
    
    try:
        html_content = Environment(loader=FileSystemLoader(DIRS["gabarits"])).get_template(nom_gabarit).render(data)
        with open(chemin_html_tmp, "w", encoding="utf-8") as f: f.write(html_content)
        html_vers_pdf_via_navigateur(chemin_html_tmp, chemin_export)
        if os.path.exists(chemin_html_tmp): os.remove(chemin_html_tmp)
        if messagebox.askyesno("Succès", f"Dépôt généré : {nom_pdf}\n\nOuvrir le dossier d'exportation ?"):
            ouvrir_dossier(DIRS["exports_griefs"])
    except Exception as e:
        if os.path.exists(chemin_html_tmp): os.remove(chemin_html_tmp)
        messagebox.showerror("Erreur", str(e))

def generer_retrait():
    nom_gabarit = "gabarit_retrait.html"
    if not os.path.exists(os.path.join(DIRS["gabarits"], nom_gabarit)): return

    griefs_liste = []; liste_numeros = []
    for i in range(1, 5):
        num = entries_retrait[i]['num'].get().strip()
        nom = entries_retrait[i]['nom'].get().strip()
        if i == 1 and not (num and nom):
            messagebox.showerror("Erreur", "Le Grief #1 est obligatoire."); return
        if num:
            griefs_liste.append({"numero": num, "nom": nom, "matricule": entries_retrait[i]['mat'].get().strip()})
            liste_numeros.append(num.replace("/", "-").replace("\\", "-").replace(":", "-"))

    # --- SAUVEGARDE AUTOMATIQUE HORODATÉE ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    auto_brouillon_path = os.path.join(DIRS["sauvegardes"], f"retrait_{liste_numeros[0]}_{timestamp}.json")
    data_brouillon = {
        "griefs": [{"num": e['num'].get(), "nom": e['nom'].get(), "mat": e['mat'].get()} for e in entries_retrait.values()],
        "motif": var_motif.get(),
        "signature": combo_sig_retrait.get()
    }
    with open(auto_brouillon_path, "w", encoding="utf-8") as f:
        json.dump(data_brouillon, f, ensure_ascii=False, indent=4)
    # ----------------------------------------

    sig_data = recuperer_data_signature(combo_sig_retrait.get())
    sig_img_base64 = ""; sig_b = 2; sig_l = 0; sig_w = 200
    if sig_data:
        chemin_img = os.path.join(DIRS["signatures"], sig_data["image"])
        sig_img_base64 = encoder_image_base64(chemin_img)
        sig_b = sig_data.get("css_bottom", 2); sig_l = sig_data.get("css_left", 0); sig_w = sig_data.get("css_width", 200)

    data = {
        "motif": var_motif.get(), "date_retrait": obtenir_date_jour_fr(), "griefs": griefs_liste,
        "logo_base64": encoder_image_base64(os.path.join(DIRS["images"], "SPTSSS logo.png")) or "",
        "signature_img_base64": sig_img_base64, "sig_bottom": sig_b, "sig_left": sig_l, "sig_width": sig_w
    }

    nom_pdf = "Retrait " + ", ".join(liste_numeros) + ".pdf"
    chemin_export = os.path.join(DIRS["exports_retraits"], nom_pdf)
    chemin_html_tmp = os.path.join(DIRS["gabarits"], "temp_render_retrait.html")
    
    try:
        html_content = Environment(loader=FileSystemLoader(DIRS["gabarits"])).get_template(nom_gabarit).render(data)
        with open(chemin_html_tmp, "w", encoding="utf-8") as f: f.write(html_content)
        html_vers_pdf_via_navigateur(chemin_html_tmp, chemin_export)
        if os.path.exists(chemin_html_tmp): os.remove(chemin_html_tmp)
        if messagebox.askyesno("Succès", f"Retrait généré : {nom_pdf}\n\nOuvrir le dossier d'exportation ?"):
            ouvrir_dossier(DIRS["exports_retraits"])
    except Exception as e:
        if os.path.exists(chemin_html_tmp): os.remove(chemin_html_tmp)
        messagebox.showerror("Erreur", str(e))

# ==========================================
# INTERFACE GRAPHIQUE PRINCIPALE
# ==========================================
root = tk.Tk()
root.title("Revendik-SPTSSS - Gestion des Griefs")
root.geometry("700x1000")

menu_bar = tk.Menu(root)
fichier_menu = tk.Menu(menu_bar, tearoff=0)
fichier_menu.add_command(label="Ouvrir dossier des griefs", command=lambda: ouvrir_dossier(DIRS["exports_griefs"]))
fichier_menu.add_command(label="Ouvrir dossier des retraits", command=lambda: ouvrir_dossier(DIRS["exports_retraits"]))
fichier_menu.add_separator()
fichier_menu.add_command(label="Quitter", command=root.quit)
menu_bar.add_cascade(label="Fichier", menu=fichier_menu)
root.config(menu=menu_bar)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=10, pady=10)

# ==========================================
# ONGLET 1: DÉPÔT
# ==========================================
tab_depot = ttk.Frame(notebook)
notebook.add(tab_depot, text="Nouveau Dépôt")

# Barre de raccourcis brouillon pour le dépôt
f_brouillon_depot = tk.Frame(tab_depot)
f_brouillon_depot.pack(fill="x", padx=10, pady=5)
tk.Button(f_brouillon_depot, text="📁 Charger un brouillon", command=charger_brouillon_depot).pack(side="left")
tk.Button(f_brouillon_depot, text="💾 Sauvegarder le brouillon", command=sauvegarder_brouillon_depot).pack(side="left", padx=5)

f1 = tk.LabelFrame(tab_depot, text="Informations Salarié / Installation", padx=10, pady=6)
f1.pack(fill="x", padx=10, pady=5)
tk.Label(f1, text="Numéro de grief:").grid(row=0, column=0, sticky="w")
ent_nogrief = tk.Entry(f1); ent_nogrief.grid(row=0, column=1, sticky="ew")
tk.Label(f1, text="Nom complet:").grid(row=1, column=0, sticky="w")
ent_nom = tk.Entry(f1); ent_nom.grid(row=1, column=1, sticky="ew")
tk.Label(f1, text="No. Employé / Matricule:").grid(row=2, column=0, sticky="w")
ent_no_emp = tk.Entry(f1); ent_no_emp.grid(row=2, column=1, sticky="ew")
tk.Label(f1, text="Titre d'emploi:").grid(row=3, column=0, sticky="w")
ent_titre = tk.Entry(f1); ent_titre.grid(row=3, column=1, sticky="ew")
tk.Label(f1, text="Installation:").grid(row=4, column=0, sticky="w")
ent_inst = tk.Entry(f1); ent_inst.grid(row=4, column=1, sticky="ew")
tk.Label(f1, text="Service:").grid(row=5, column=0, sticky="w")
ent_serv = tk.Entry(f1); ent_serv.grid(row=5, column=1, sticky="ew")

tk.Label(f1, text="Établissement:").grid(row=6, column=0, sticky="w")
frame_etab = tk.Frame(f1)
frame_etab.grid(row=6, column=1, sticky="ew")
ent_etab = tk.Entry(frame_etab)
ent_etab.pack(side="left", fill="x", expand=True)
ent_etab.insert(0, config_app.get("etablissement_defaut", ""))
tk.Button(frame_etab, text="Définir par défaut", command=definir_etablissement_defaut, font=("Arial", 8)).pack(side="right", padx=(5,0))

tk.Label(f1, text="Date de dépôt:").grid(row=7, column=0, sticky="w")
ent_date = tk.Entry(f1); ent_date.grid(row=7, column=1, sticky="ew"); ent_date.insert(0, obtenir_date_jour_fr())
f1.columnconfigure(1, weight=1)

f_type = tk.LabelFrame(tab_depot, text="Type de grief", padx=10, pady=5)
f_type.pack(fill="x", padx=10, pady=5)
var_type = tk.StringVar(value="Individuel")
tk.Radiobutton(f_type, text="Individuel", variable=var_type, value="Individuel").pack(side="left")
tk.Radiobutton(f_type, text="Groupe", variable=var_type, value="Groupe").pack(side="left")
tk.Radiobutton(f_type, text="Syndical", variable=var_type, value="Syndical").pack(side="left")

f_sig = tk.LabelFrame(tab_depot, text="Signature de la personne", padx=10, pady=5)
f_sig.pack(fill="x", padx=10, pady=5)
combo_sig = ttk.Combobox(f_sig, state="readonly")
combo_sig.pack(fill="x", expand=True)

tk.Label(tab_depot, text="Description du grief (Détails) :").pack(anchor="w", padx=10, pady=(10, 0))
txt_desc = tk.Text(tab_depot, height=8, wrap="word")
txt_desc.pack(fill="x", padx=10, pady=5)
tk.Label(tab_depot, text="Réclamation (Correctifs) :").pack(anchor="w", padx=10)
txt_recl = tk.Text(tab_depot, height=6, wrap="word")
txt_recl.pack(fill="x", padx=10, pady=5)

tk.Button(tab_depot, text="GÉNÉRER LE DÉPÔT (PDF)", command=generer_depot, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2).pack(pady=10, fill="x", padx=10)

# ==========================================
# ONGLET 2: RETRAIT
# ==========================================
tab_retrait = ttk.Frame(notebook)
notebook.add(tab_retrait, text="Retrait de Griefs")

# Barre de raccourcis brouillon pour le retrait
f_brouillon_retrait = tk.Frame(tab_retrait)
f_brouillon_retrait.pack(fill="x", padx=10, pady=5)
tk.Button(f_brouillon_retrait, text="📁 Charger un brouillon", command=charger_brouillon_retrait).pack(side="left")
tk.Button(f_brouillon_retrait, text="💾 Sauvegarder le brouillon", command=sauvegarder_brouillon_retrait).pack(side="left", padx=5)

entries_retrait = {}
for i in range(1, 5):
    frame = tk.LabelFrame(tab_retrait, text=f"Grief #{i} {'(Obligatoire)' if i == 1 else '(Optionnel)'}", padx=10, pady=5)
    frame.pack(fill="x", padx=10, pady=5)
    tk.Label(frame, text="N° grief:").grid(row=0, column=0, sticky="w")
    num_ent = tk.Entry(frame); num_ent.grid(row=0, column=1, sticky="ew")
    tk.Label(frame, text="Nom:").grid(row=1, column=0, sticky="w")
    nom_ent = tk.Entry(frame); nom_ent.grid(row=1, column=1, sticky="ew")
    tk.Label(frame, text="Matricule:").grid(row=2, column=0, sticky="w")
    mat_ent = tk.Entry(frame); mat_ent.grid(row=2, column=1, sticky="ew")
    frame.columnconfigure(1, weight=1)
    entries_retrait[i] = {'num': num_ent, 'nom': nom_ent, 'mat': mat_ent}

motif_frame = tk.LabelFrame(tab_retrait, text="Motif du retrait", padx=10, pady=5)
motif_frame.pack(fill="x", padx=10, pady=5)
motifs = ["L’Employeur a fait droit au grief.", "Règlement par entente entre les parties.", "Retrait sans admission de la part du Syndicat."]
var_motif = tk.StringVar(value=motifs[0])
ttk.Combobox(motif_frame, textvariable=var_motif, values=motifs, state="readonly").pack(fill="x", pady=5)

f_sig_retrait = tk.LabelFrame(tab_retrait, text="Signature de l'agent", padx=10, pady=5)
f_sig_retrait.pack(fill="x", padx=10, pady=5)
combo_sig_retrait = ttk.Combobox(f_sig_retrait, state="readonly")
combo_sig_retrait.pack(fill="x", expand=True)

tk.Button(tab_retrait, text="GÉNÉRER LE RETRAIT (PDF)", command=generer_retrait, bg="#c0392b", fg="white", font=("Arial", 12, "bold"), height=2).pack(pady=10, fill="x", padx=10)

# ==========================================
# ONGLET 3: GESTION DES SIGNATURES
# ==========================================
tab_sig = ttk.Frame(notebook)
notebook.add(tab_sig, text="Gestion des Signatures")

img_ref = {"original": None, "photo": None, "x": 10, "y": 145, "filepath": None}
ratio_pdf = 0.84

def actualiser_canvas_sig(*args):
    if img_ref["original"]:
        w, h = img_ref["original"].size
        new_w = int(w * scale_var_sig.get())
        new_h = int(h * scale_var_sig.get())
        if new_w > 0 and new_h > 0:
            resized = img_ref["original"].resize((new_w, new_h), Image.Resampling.LANCZOS)
            img_ref["photo"] = ImageTk.PhotoImage(resized)
            canvas_sig.coords(img_id_sig, img_ref["x"], img_ref["y"])
            canvas_sig.itemconfig(img_id_sig, image=img_ref["photo"])

def importer_image_sig():
    filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
    if filepath:
        try:
            img_ouvre = Image.open(filepath).convert("RGBA")
            max_taille = 800
            w, h = img_ouvre.size
            if max(w, h) > max_taille:
                if w > h:
                    new_w = max_taille; new_h = int(h * (max_taille / w))
                else:
                    new_h = max_taille; new_w = int(w * (max_taille / h))
                img_ouvre = img_ouvre.resize((new_w, new_h), Image.Resampling.LANCZOS)

            img_ref["original"] = img_ouvre
            img_ref["filepath"] = filepath
            img_ref["x"] = 10; img_ref["y"] = 145
            scale_var_sig.set(0.5)
            combo_gestion_sig.set("")
            actualiser_canvas_sig()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'importer l'image :\n{e}")

def charger_signature_editeur():
    nom = combo_gestion_sig.get()
    if not nom: return
    data = recuperer_data_signature(nom)
    if not data: return
    
    img_path = os.path.join(DIRS["signatures"], data["image"])
    if not os.path.exists(img_path): return
    
    img_ref["original"] = Image.open(img_path).convert("RGBA")
    img_ref["filepath"] = img_path
    img_ref["x"] = (data.get("css_left", 0) / ratio_pdf) + 10
    img_ref["y"] = 150 - (data.get("css_bottom", 2) / ratio_pdf)
    scale_var_sig.set(data.get("tk_scale", 0.5))
    actualiser_canvas_sig()

def sauvegarder_signature_tab():
    if not img_ref.get("original"): return
    nom_actuel = combo_gestion_sig.get()
    nom_sig = simpledialog.askstring("Sauvegarder", "Nom de la signature :", initialvalue=nom_actuel, parent=root)
    if not nom_sig: return
    
    left_px = (img_ref["x"] - 10) * ratio_pdf
    w_px = (img_ref["original"].size[0] * scale_var_sig.get()) * ratio_pdf
    bottom_px = (150 - img_ref["y"]) * ratio_pdf

    base_nom = nom_sig.replace(" ", "_").lower()
    img_dest = os.path.join(DIRS["signatures"], f"{base_nom}.png")
    json_dest = os.path.join(DIRS["signatures"], f"{base_nom}.json")

    img_ref["original"].save(img_dest, "PNG")
        
    data = {
        "nom": nom_sig, "image": f"{base_nom}.png", "css_left": round(left_px, 2),
        "css_bottom": round(bottom_px, 2), "css_width": round(w_px, 2), "tk_scale": scale_var_sig.get()
    }
    with open(json_dest, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
        
    messagebox.showinfo("Succès", "Signature sauvegardée.")
    charger_liste_signatures()
    combo_gestion_sig.set(nom_sig)

def supprimer_signature_tab():
    sig_nom = combo_gestion_sig.get()
    if not sig_nom: return
    if messagebox.askyesno("Confirmation", f"Supprimer '{sig_nom}' ?"):
        chemin_json = os.path.join(DIRS["signatures"], f"{sig_nom}.json")
        if os.path.exists(chemin_json):
            with open(chemin_json, 'r') as f: data = json.load(f)
            chemin_img = os.path.join(DIRS["signatures"], data["image"])
            if os.path.exists(chemin_img): os.remove(chemin_img)
            os.remove(chemin_json)
        
        if config_app.get("signature_defaut") == sig_nom:
            config_app["signature_defaut"] = ""
            save_config(config_app)
            
        canvas_sig.itemconfig(img_id_sig, image="")
        img_ref["original"] = None
        charger_liste_signatures()
        combo_gestion_sig.set("")

def definir_signature_defaut_tab():
    if not combo_gestion_sig.get(): return
    config_app['signature_defaut'] = combo_gestion_sig.get()
    save_config(config_app)
    charger_liste_signatures()
    messagebox.showinfo("Succès", "Cette signature est maintenant utilisée par défaut.")

f_action = tk.LabelFrame(tab_sig, text="Signatures existantes", padx=10, pady=10)
f_action.pack(fill="x", padx=10, pady=5)
combo_gestion_sig = ttk.Combobox(f_action, state="readonly")
combo_gestion_sig.pack(side="left", fill="x", expand=True, padx=(0, 10))
tk.Button(f_action, text="Charger", command=charger_signature_editeur).pack(side="left", padx=2)
tk.Button(f_action, text="Définir par défaut", command=definir_signature_defaut_tab).pack(side="left", padx=2)
tk.Button(f_action, text="Supprimer", fg="#c0392b", command=supprimer_signature_tab).pack(side="left", padx=2)

f_edit = tk.LabelFrame(tab_sig, text="Prévisualisation et Édition", padx=10, pady=10)
f_edit.pack(fill="both", expand=True, padx=10, pady=5)
tk.Button(f_edit, text="Importer une nouvelle image...", command=importer_image_sig).pack(pady=5)

canvas_sig = tk.Canvas(f_edit, width=400, height=200, bg="white", highlightthickness=1, highlightbackground="black")
canvas_sig.pack(pady=10)
canvas_sig.create_line(10, 150, 390, 150, fill="#94a3b8", width=2)
canvas_sig.create_text(10, 155, text="Signature de la personne salariée", anchor="nw", fill="#64748b", font=("Arial", 8))
img_id_sig = canvas_sig.create_image(img_ref["x"], img_ref["y"], anchor="sw")

def on_drag_start(event): img_ref["drag_data"] = {"x": event.x, "y": event.y}
def on_drag_motion(event):
    if "drag_data" in img_ref:
        dx, dy = event.x - img_ref["drag_data"]["x"], event.y - img_ref["drag_data"]["y"]
        img_ref["x"] += dx; img_ref["y"] += dy
        canvas_sig.coords(img_id_sig, img_ref["x"], img_ref["y"])
        img_ref["drag_data"] = {"x": event.x, "y": event.y}

canvas_sig.bind("<ButtonPress-1>", on_drag_start)
canvas_sig.bind("<B1-Motion>", on_drag_motion)

scale_var_sig = tk.DoubleVar(value=0.5)
tk.Label(f_edit, text="Échelle de l'image (Ajustez avec le curseur)").pack()
tk.Scale(f_edit, variable=scale_var_sig, from_=0.1, to=2.0, resolution=0.05, orient="horizontal", command=actualiser_canvas_sig).pack(fill="x", padx=50)

tk.Button(f_edit, text="Sauvegarder", command=sauvegarder_signature_tab, bg="#3498db", fg="white", font=("Arial", 10, "bold"), width=20).pack(pady=15)

# ==========================================
# PIED DE PAGE : LOGO REVENDIK
# ==========================================
chemin_logo_pied = os.path.join(DIRS["images"], "logo_revendik.jpg")
if not os.path.exists(chemin_logo_pied):
    chemin_logo_pied = os.path.join(DIRS["images"], "logo_revendik.png")

if os.path.exists(chemin_logo_pied):
    try:
        img_logo = Image.open(chemin_logo_pied)
        w_base = 220
        w_percent = (w_base / float(img_logo.size[0]))
        h_size = int((float(img_logo.size[1]) * float(w_percent)))
        img_resized = img_logo.resize((w_base, h_size), Image.Resampling.LANCZOS)
        logo_tk = ImageTk.PhotoImage(img_resized)
        lbl_logo = tk.Label(root, image=logo_tk)
        lbl_logo.image = logo_tk
        lbl_logo.pack(side="bottom", pady=(0, 5))
    except Exception as e:
        print(f"Erreur logo pied de page : {e}")

# Initialisation
charger_liste_signatures()

if __name__ == '__main__':
    root.mainloop()