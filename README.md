# Gestion Hadj — DAROU SALAM

Application bureau (Windows) pour gérer les pèlerins Hadj/Omra : inscriptions, versements, dépenses, reçus PDF et sauvegarde de la base de données.

Le code source se trouve dans le dossier **`gestion-hadj/`**.

---

## Prérequis (machine neuve)

| Composant | Version minimale |
|-----------|------------------|
| **Système** | Windows 10 ou 11 (64 bits) |
| **Python** | 3.10, 3.11, 3.12 ou 3.13 |
| **pip** | Inclus avec Python |
| **Espace disque** | ~500 Mo (Python + dépendances + application) |

### Installer Python

1. Télécharger Python sur [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Lors de l’installation, cocher **« Add python.exe to PATH »**
3. Vérifier dans un terminal :

```powershell
python --version
pip --version
```

---

## Dépendances Python

Toutes les bibliothèques nécessaires sont listées dans `gestion-hadj-main/requirements.txt` :

| Paquet | Rôle |
|--------|------|
| **PySide6** | Interface graphique (Qt) |
| **openpyxl** | Export Excel (listes, départs confirmés) |
| **reportlab** | Génération des reçus / factures PDF |

Optionnel (uniquement pour créer un `.exe`) :

| Paquet | Rôle |
|--------|------|
| **pyinstaller** | Compilation en exécutable Windows |

---

## Installation sur une machine neuve

Ouvrir **PowerShell** ou **Invite de commandes**, puis :

```powershell
cd "C:\chemin\vers\gestion-hadj-main\gestion-hadj-main"

python -m venv .venv
.\.venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

La première exécution crée automatiquement la base SQLite dans `data/app.db`.

---

## Lancement de l’application

### Méthode 1 — Script Windows (recommandé)

```powershell
cd gestion-hadj-main
.\run_app.bat
```

### Méthode 2 — Ligne de commande

```powershell
cd gestion-hadj-main
.\.venv\Scripts\activate
python main.py
```

---

## Structure du projet

```
gestion-hadj-main/
├── main.py                 # Point d’entrée
├── run_app.bat             # Lancement rapide
├── build_exe.bat           # Création d’un .exe (optionnel)
├── requirements.txt        # Dépendances pip
├── assets/
│   ├── logo.png            # Logo agence (factures + tableau de bord)
│   ├── icons/              # Icônes interface
│   └── styles/             # Feuilles de style (.qss)
├── data/
│   └── app.db              # Base SQLite (créée au premier lancement)
├── database/               # Schéma et initialisation
├── services/               # Logique métier
├── UIs/                    # Fenêtres et vues
└── utils/
    └── import_hadj_excel.py  # Migration depuis un ancien fichier Excel
```

---

## Utilisation

| Menu | Fonction |
|------|----------|
| **Tableau de bord** | Statistiques, actions rapides, logo et nom de l’agence |
| **Pèlerins** | Inscription, recherche, suppression (mot de passe admin) |
| **Versements** | Paiements et génération du reçu PDF A4 |
| **Dépenses** | Sorties de caisse |
| **Paramètres** | Nom agence, saison, mot de passe admin, **export/import** de la base |
| **Départs confirmés** | Liste et export Excel |

### Mot de passe administrateur

- Par défaut : `admin123`
- Modifiable dans **Paramètres**
- Requis pour supprimer un pèlerin ou un versement

### Sauvegarde de la base de données

Dans **Paramètres** :

1. **Exporter la base de données** — enregistrer régulièrement un fichier `.db` (clé USB, cloud, etc.)
2. **Importer une sauvegarde** — restaurer une copie (une sauvegarde automatique `.bak` est créée avant remplacement)

### Import depuis un ancien fichier Excel

```powershell
cd gestion-hadj-main
python utils/import_hadj_excel.py "C:\chemin\vers\HADJ_2027.xlsx"
```

---

## Créer un exécutable Windows (.exe)

```powershell
cd gestion-hadj-main
pip install pyinstaller
.\build_exe.bat
```

L’application compilée se trouve dans `dist/GestionHadj/`.

---

## Règles métier intégrées

- Doublon pèlerin bloqué (nom + prénom + date de naissance)
- Maximum 5 tranches de paiement par pèlerin
- Dépassement du montant prévu bloqué

---

## Dépannage

| Problème | Solution |
|----------|----------|
| `python` introuvable | Réinstaller Python avec « Add to PATH » ou utiliser `py -3` |
| Logo absent | Vérifier que `assets/logo.png` existe |
| Erreur `PySide6` | `pip install -r requirements.txt` dans le bon dossier |
| Base vide après copie | Lancer une fois `python main.py` pour initialiser `data/app.db` |

---

## Licence

Usage interne — Agence DAROU SALAM.
