# Revendik-SPTSSS

Application de dépôt et de retrait de griefs pour le SPTSSS.

## Prérequis

- Python 3.10 ou version plus récente
- Un navigateur Chromium, Google Chrome ou Microsoft Edge, utilisé pour créer les PDF

Les dépendances de `requirements.txt` sont communes à Windows, macOS et Linux.

### Windows

Installez Python depuis [python.org](https://www.python.org/downloads/) en cochant
« Add Python to PATH ». Tkinter et Edge sont normalement déjà disponibles.

### macOS

Installez Python 3 depuis [python.org](https://www.python.org/downloads/) ou Homebrew.
Chrome, Chromium ou Edge doit être installé.

### Linux (Debian/Ubuntu)

Installez Tkinter et un navigateur, si nécessaire :

```bash
sudo apt install python3-tk chromium
```

## Installation et lancement

Exécutez les commandes suivantes à la racine du projet.

### Windows (PowerShell)

```powershell
py -m venv .env
.\.env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python revendik.py
```

### macOS et Linux

```bash
python3 -m venv .env
source .env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python revendik.py
```
