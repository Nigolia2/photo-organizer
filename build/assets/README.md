# Icônes pour le packaging

Placer ici les fichiers d'icône avant de lancer les scripts de build.

## Fichiers attendus

| Fichier      | Format | Taille recommandée | Utilisé par          |
|--------------|--------|-------------------|----------------------|
| `icon.png`   | PNG    | 256×256 px minimum | Linux (.deb) + macOS  |
| `icon.ico`   | ICO    | 256×256 px         | Windows (.exe)        |

## Créer icon.ico depuis icon.png (Linux/macOS)

```bash
# avec ImageMagick (apt install imagemagick)
convert icon.png -resize 256x256 icon.ico
```

## Créer icon.ico depuis icon.png (Windows — PowerShell)

```powershell
# avec Pillow (déjà dans le venv)
python -c "
from PIL import Image
img = Image.open('build/assets/icon.png').resize((256, 256))
img.save('build/assets/icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(256,256)])
"
```

## Sans icône

Les scripts de build fonctionnent sans icône (un avertissement est affiché).
L'exécutable aura l'icône par défaut de PyInstaller.
