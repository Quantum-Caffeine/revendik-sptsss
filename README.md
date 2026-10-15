# Revendik-SPTSSS

Application de gestion, de dépôt et de retrait de griefs pour le **SPTSSS** (*Syndicat des professionnelles et professionnels du milieu de la santé et des services sociaux de la Capitale-Nationale*).

---

## Nouveautés de la version 2.0 (Refonte)

- **Interface adaptative et défilement fluide** : Finie la fenêtre tronquée sur les petits écrans d'ordinateurs portables. Les formulaires sont intégrés dans des conteneurs déroulants (*scrollables*) à la molette ou avec barre de défilement.
- **Liste dynamique pour les retraits** : Possibilité d'ajouter autant de griefs que nécessaire ou d'en retirer dynamiquement plutôt que d'être restreint à 4 cases fixes.
- **Aperçu instantané dans le navigateur** : Bouton « Aperçu (Navigateur) » pour visualiser le document mis en page avant l'exportation PDF définitive.
- **Gestionnaire de brouillons et historique récent** : Sauvegarde automatique horodatée, accès direct aux derniers brouillons via le menu *Brouillons*.
- **Fenêtre de préférences** : Configuration claire de l'établissement par défaut, de la signature par défaut et diagnostic du moteur PDF.
- **Architecture modulaire et testée** : Séparation stricte de la logique métier (modèles, rendu Jinja2, génération PDF, gestion des signatures) et de l'interface graphique. Suite de tests unitaires automatisés intégrée.
- **Ligne de commande (CLI)** : Possibilité d'exécuter un diagnostic (`check-env`), de lister les brouillons ou d'exporter des PDF directement en ligne de commande.

---

## Prérequis

- **Python 3.10** ou version plus récente
- **Un navigateur compatible** : Microsoft Edge, Google Chrome, Brave ou Chromium (utilisé pour la conversion sans en-tête/pied-de-page des PDF).

Les dépendances de `requirements.txt` sont communes à Windows, macOS et Linux (`Jinja2` et `Pillow`).

### Windows
Installez Python depuis [python.org](https://www.python.org/downloads/) en cochant **« Add Python to PATH »**. Tkinter et Microsoft Edge sont déjà fournis avec Windows.

### macOS
Installez Python 3 via `brew install python-tk` ou le programme d'installation officiel. Google Chrome ou Edge doit être installé.

### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install python3-tk chromium
```

---

## Installation et lancement

### 1. Cloner ou ouvrir le dossier
Dans un terminal (PowerShell sous Windows, ou Bash sous macOS/Linux) :

#### Windows (PowerShell)
```powershell
py -m venv .env
.\.env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python revendik.py
```

#### macOS et Linux
```bash
python3 -m venv .env
source .env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python revendik.py
```

---

## Utilisation en ligne de commande (CLI)

Le projet peut également être exécuté sans interface graphique pour le diagnostic ou l'automatisation :

```bash
# Vérifier l'environnement et le moteur PDF détecté
python -m revendik check-env

# Lister les brouillons récents
python -m revendik list-drafts

# Lister les signatures enregistrées
python -m revendik list-signatures

# Exporter un PDF à partir d'un fichier brouillon JSON
python -m revendik render config/sauvegardes/mon_brouillon.json -o export.pdf

# Lancer l'interface graphique
python -m revendik gui
# ou
python revendik.py
```

---

## Exécution des tests unitaires

Pour exécuter la suite complète de tests automatisés :

```bash
python -m unittest discover -s tests
```

---

## Structure du projet

```
revendik-sptsss/
├── config/                  # Configuration locale et signatures
│   ├── config.json          # Paramètres utilisateur (établissement, signature)
│   ├── sauvegardes/         # Brouillons et sauvegardes automatiques
│   └── signatures/          # Fichiers de signatures et métadonnées
├── data/
│   ├── gabarits/            # Modèles HTML (gabarit.html, gabarit_retrait.html)
│   └── images/              # Logos officiels (SPTSSS logo, logo_revendik)
├── exports/                 # Dossier d'exportation des PDF générés
│   ├── griefs/
│   └── retraits de grief/
├── revendik/                # Package Python modulaire
│   ├── config.py            # Chemins et chargement de configuration
│   ├── models.py            # Modèles de données typés et validations
│   ├── renderer.py          # Moteur de rendu de gabarits Jinja2
│   ├── pdf.py               # Détection de navigateur et conversion PDF
│   ├── signatures.py        # Gestion et calculs de coordonnées de signature
│   ├── drafts.py            # Sauvegarde, chargement et historique des brouillons
│   ├── cli.py               # Interface en ligne de commande
│   └── ui/                  # Composants graphiques Tkinter / TTK
│       ├── app.py           # Fenêtre principale et menus
│       ├── theme.py         # Styles et thème visuel
│       ├── components/      # Conteneurs réutilisables (ScrollableFrame)
│       ├── tabs/            # Onglets Dépôt, Retrait et Signatures
│       └── dialogs/         # Boîte de dialogue des préférences
├── tests/                   # Suite de tests unitaires automatisés
├── revendik.py              # Point d'entrée rétrocompatible
└── requirements.txt         # Dépendances Python (Jinja2, Pillow)
```
