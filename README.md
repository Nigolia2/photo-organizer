# Photo Organizer

Gestionnaire de bibliothèque de photos numériques — tri automatique par date et
détection/archivage des doublons. Fonctionne sur Windows, Linux et macOS.
Interface graphique avec thème sombre Catppuccin Mocha.

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

## Créer un exécutable autonome (optionnel)

Pour distribuer l'application sans installer Python sur la machine cible :

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name PhotoOrganizer main.py
```

L'exécutable sera généré dans le dossier `dist/`. À refaire séparément sur chaque OS cible
(Windows, Linux, macOS) car PyInstaller ne fait pas de cross-compilation.

## Structure du projet

```
photo_organizer/
├── main.py                 # Interface graphique (Tkinter)
├── core/
│   ├── scanner.py           # Détection des images + lecture EXIF
│   ├── sorter.py             # Logique de tri par année/mois
│   ├── duplicates.py         # Détection et archivage des doublons
│   └── theme.py              # Thème Catppuccin Mocha
├── requirements.txt
└── README.md
```
