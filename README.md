# Photo Organizer

Gestionnaire de bibliothèque de photos numériques — tri automatique par date et
détection/archivage des doublons. Fonctionne sur Windows, Linux et macOS.
Interface graphique avec la palette macOS Big Sur (mode clair).

## Installation

```bash
pip install -r requirements.txt
```

Python 3.9+ requis (Tkinter est inclus nativement dans la plupart des installations Python).

Sur certaines distributions Linux, Tkinter doit être installé séparément :
```bash
# Debian/Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## Lancement

```bash
python main.py
```

## Fonctionnalités

### 1. Tri par date
- Scanne récursivement un dossier source.
- Lit la date de prise de vue dans les métadonnées EXIF (`DateTimeOriginal`).
- Si aucune métadonnée n'est disponible, utilise la date de modification du fichier.
- Copie (par défaut) ou déplace chaque photo dans `Destination/AAAA/MM - Mois/`.
- Gère les conflits de noms en ajoutant un suffixe `(1)`, `(2)`, etc.

### 2. Détection de doublons
Deux méthodes au choix :
- **Contenu identique (hash SHA-256)** : fiable à 100%, détecte les fichiers strictement
  identiques octet pour octet, même si le nom diffère.
- **Nom + taille** : heuristique plus rapide, utile pour repérer des doublons probables
  quand le contenu a été légèrement modifié (recompression, métadonnées différentes).

Le processus se fait en 2 étapes :
1. **Analyser** — identifie les groupes de doublons sans rien déplacer.
2. **Archiver** — déplace tous les doublons (sauf le premier de chaque groupe, conservé
   à sa place d'origine) vers un dossier d'archive dédié.

## Formats supportés
- **Photos** : JPEG, PNG, TIFF, BMP, GIF, WebP, HEIC/HEIF (photos iPhone)
- **Vidéos** : MP4, MOV, AVI, MKV, M4V, 3GP, WMV — date extraite des métadonnées du
  conteneur (via `hachoir`), avec repli sur la date de modification du fichier si absente.

## Lancer les tests

```bash
pytest tests/ -v
```

## Packaging — distribuer sans Python

> **Important — pas de cross-compilation** : PyInstaller génère un exécutable natif pour
> l'OS sur lequel il s'exécute. Chaque artefact de distribution doit être construit sur la
> machine cible correspondante. Les scripts ci-dessous sont prêts ; il suffit de les lancer.

### Windows — PhotoOrganizer.exe

Sur ta machine Windows (PowerShell, depuis la racine du projet) :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-build.txt
.\build\build_windows.ps1
```

Produit : `dist\PhotoOrganizer.exe` (autonome, ~50 Mo, aucune installation requise).

**Icône** (optionnel) : placer `build\assets\icon.ico` avant de lancer le script.

---

### Linux — paquet .deb

Sur ce serveur (venv déjà présent) :

```bash
source venv/bin/activate
pip install -r requirements-build.txt
bash build/build_linux.sh
```

Produit : `dist/photo-organizer_1.0.0_amd64.deb`

Installation sur la machine cible :
```bash
sudo apt install ./dist/photo-organizer_1.0.0_amd64.deb
```

Le paquet installe l'application dans `/opt/photo-organizer/`, crée un lanceur dans
`/usr/bin/photo-organizer`, et enregistre une entrée dans le menu applicatif (catégorie
*Graphisme/Photographie*).

**Dépendances système déclarées** : `libc6`, `libx11-6`, `libxext6`, `libxft2`, `tk`

**Icône** (optionnel) : placer `build/assets/icon.png` (256×256 px min) avant de lancer.

---

### macOS — PhotoOrganizer.dmg

Sur une machine macOS (Python 3.9+ requis) :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-build.txt
brew install create-dmg
bash build/build_macos.sh
```

Produit : `dist/PhotoOrganizer.dmg` — l'utilisateur double-clique et glisse l'app dans
Applications (glisser-déposer classique macOS).

---

### Résumé des artefacts par OS

| OS      | Script                      | Artefact produit                        |
|---------|-----------------------------|-----------------------------------------|
| Windows | `build\build_windows.ps1`   | `dist\PhotoOrganizer.exe`               |
| Linux   | `build/build_linux.sh`      | `dist/photo-organizer_1.0.0_amd64.deb` |
| macOS   | `build/build_macos.sh`      | `dist/PhotoOrganizer.dmg`               |

---

### Release automatique via GitHub Actions

Un workflow (`.github/workflows/build.yml`) construit automatiquement les 3 artefacts
(Windows, Linux, macOS) et les publie dans une GitHub Release à chaque tag de version poussé.

**Déclencher une release :**
```bash
git tag v1.0.0
git push --tags
```

Ça lance 3 jobs en parallèle (un par OS, réutilisant les scripts de `build/` ci-dessus), puis
un job final qui crée la Release GitHub pour le tag et y attache automatiquement :
- `PhotoOrganizer.exe` (Windows)
- `photo-organizer.deb` (Linux)
- `PhotoOrganizer.dmg` (macOS)

> **Non vérifié en conditions réelles** : le workflow a été validé syntaxiquement (YAML +
> relecture manuelle de la logique des jobs), mais n'a pas pu être exécuté dans cet
> environnement — GitHub Actions ne peut être testé qu'une fois le fichier réellement poussé
> sur GitHub. Vérifie le premier run après un push de tag avant de t'y fier pour une vraie
> release.

## Structure du projet

```
photo_organizer/
├── main.py                      # Point d'entrée : assemble sidebar + vues CustomTkinter
├── core/
│   ├── scanner.py                # Détection des médias + lecture EXIF / métadonnées vidéo
│   ├── sorter.py                  # Logique de tri par année/mois (idempotent)
│   ├── duplicates.py              # Détection/archivage des doublons (hashing parallèle + cache)
│   ├── theme.py                    # Palette macOS Big Sur (mode clair) + polices cross-platform
│   └── theme.json                   # Couleurs CustomTkinter par widget, dérivées de theme.py
├── ui/                           # Composants d'interface CustomTkinter (logique métier exclue)
│   ├── sidebar.py                 # Navigation latérale (sections Trier par date / Doublons)
│   ├── toolbar.py                  # Barre d'actions principales d'une vue
│   ├── result_list.py               # Liste défilante des résultats (une ligne par fichier)
│   ├── notification.py               # Bandeau de notification intégré (pas de popup bloquante)
│   ├── widgets.py                      # Petits composants partagés (sélecteur de dossier, etc.)
│   ├── sort_view.py                     # Vue "Trier par date"
│   └── duplicates_view.py                # Vue "Doublons"
├── tests/                        # Tests pytest (29 cas)
│   ├── test_scanner.py
│   ├── test_sorter.py
│   └── test_duplicates.py
├── build/                        # Scripts de packaging (un par OS, réutilisés par la CI)
│   ├── build_linux.sh             # → .deb (Linux, à lancer sur Linux)
│   ├── build_windows.ps1          # → .exe (Windows, à lancer sur Windows)
│   ├── build_macos.sh             # → .dmg (macOS, à lancer sur macOS, via create-dmg)
│   └── assets/                    # Icônes à placer avant le build
│       ├── icon.png               # 256×256 px — Linux & macOS
│       ├── icon.ico               # 256×256 px — Windows
│       └── README.md              # Instructions de création des icônes
├── .github/workflows/
│   └── build.yml                  # Build + GitHub Release automatique à chaque tag vX.Y.Z
├── requirements.txt               # Dépendances runtime
├── requirements-build.txt         # Dépendances de build (PyInstaller)
└── README.md
```
