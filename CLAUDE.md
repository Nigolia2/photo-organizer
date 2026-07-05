# CLAUDE.md — Contexte du projet Photo Organizer

## Objectif
Application de bureau pour gérer une bibliothèque de photos numériques personnelle.
Deux fonctionnalités cœur :
1. Tri automatique des photos par date de prise de vue (EXIF) en dossiers `AAAA/MM - Mois/`.
2. Détection et archivage des doublons (par hash de contenu ou par nom+taille).

## Contraintes
- **Cross-platform** : doit tourner sur Windows, Linux, et si possible macOS, sans réécriture
  de code spécifique à l'OS. Éviter les dépendances qui ne compilent pas facilement sur toutes
  les plateformes (attention en particulier à `pillow-heif` sur Linux).
- **Aucune dépendance cloud/réseau** : tout doit fonctionner en local, sur les photos de
  l'utilisateur. Pas d'appel API externe.
- **Non-destructif par défaut** : privilégier la copie plutôt que le déplacement sauf action
  explicite de l'utilisateur. Toute opération d'archivage de doublons doit être réversible
  facilement (on ne supprime jamais, on déplace vers un dossier d'archive).
- **Interface graphique** : Tkinter avec thème sombre "Catppuccin Mocha" (couleurs définies
  dans `core/theme.py`, palette `MOCHA`). Garder la cohérence visuelle si de nouveaux widgets
  sont ajoutés.

## Stack technique
- Python 3.9+
- Tkinter (ttk) pour l'UI — pas de framework GUI externe (pour rester léger et sans dépendance
  de compilation lourde)
- Pillow + pillow-heif pour la lecture EXIF et le support HEIC (photos iPhone)
- hashlib (stdlib) pour la détection de doublons stricte

## Structure du projet
```
photo_organizer/
├── main.py              # Interface graphique, point d'entrée
├── core/
│   ├── scanner.py        # Détection des fichiers image + extraction date EXIF
│   ├── sorter.py          # Logique de tri par année/mois
│   ├── duplicates.py      # Détection (hash / nom+taille) + archivage des doublons
│   └── theme.py           # Palette et styles ttk Catppuccin Mocha
├── tests/                # Tests (à développer)
├── requirements.txt
└── README.md
```

## Conventions de code
- Toutes les fonctions publiques ont une docstring en français expliquant leur rôle.
- Les fonctions longues (scan, tri, dédoublonnage) acceptent des callbacks optionnels
  `progress_callback(current, total)` et `log_callback(message)` pour rester découplées de l'UI —
  ne pas coupler la logique métier directement à Tkinter.
- Les opérations sur fichiers (copy/move) gèrent toujours les collisions de noms en ajoutant
  un suffixe `(1)`, `(2)`, etc. plutôt que d'écraser un fichier existant.
- Les erreurs sur un fichier individuel ne doivent jamais interrompre le traitement du lot :
  logger l'erreur et continuer.
- Pas de `print()` dans le code métier (`core/`) — tout passe par `log_callback`.

## Roadmap / pistes d'amélioration envisagées
- Tests unitaires (`tests/`) pour scanner, sorter, duplicates — actuellement testé manuellement
  seulement.
- Détection de quasi-doublons par hash perceptuel (`imagehash`) pour repérer les photos
  recompressées ou légèrement recadrées, pas seulement les doublons strictement identiques.
- Support d'une prévisualisation (miniatures) avant archivage des doublons, pour valider
  visuellement avant de déplacer les fichiers.
- Packaging en exécutable autonome via PyInstaller (une build par OS cible).
- Éventuellement : détection de doublons entre le dossier source ET la bibliothèque déjà triée
  (actuellement l'analyse porte sur un seul dossier à la fois).

## Ce qu'il ne faut PAS faire
- Ne pas introduire de dépendance nécessitant une compilation native complexe (ex: OpenCV complet)
  sauf nécessité clairement justifiée — l'app doit rester facile à installer avec un simple
  `pip install -r requirements.txt` sur les trois OS cibles.
- Ne pas supprimer de fichiers directement : toujours archiver/déplacer, jamais `os.remove`
  sur une photo utilisateur sans confirmation explicite.
