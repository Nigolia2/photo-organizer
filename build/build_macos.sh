#!/usr/bin/env bash
# build_macos.sh — Construit PhotoOrganizer.dmg sur macOS.
# À exécuter sur une machine macOS (Intel ou Apple Silicon) avec Python 3.9+.
# Prérequis : PyInstaller + create-dmg (brew install create-dmg).
#
# Usage :
#   cd /chemin/vers/photo_organizer
#   python3 -m venv venv
#   source venv/bin/activate
#   pip install -r requirements.txt
#   pip install -r requirements-build.txt
#   brew install create-dmg
#   bash build/build_macos.sh

set -euo pipefail

APP_NAME="PhotoOrganizer"
DIST_DIR="dist"
DMG_PATH="${DIST_DIR}/${APP_NAME}.dmg"

echo "=== Build PyInstaller (.app bundle) ==="
# --add-data attend un chemin absolu pour la source : PyInstaller résout un chemin
# relatif par rapport à --specpath (ici "build/"), pas par rapport au dossier courant.
pyinstaller \
    --onefile \
    --windowed \
    --name "${APP_NAME}" \
    --distpath "${DIST_DIR}" \
    --workpath "build/pyinstaller_work" \
    --specpath "build" \
    --add-data "$(pwd)/core/theme.json:core" \
    main.py

APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "Erreur : ${APP_BUNDLE} introuvable après la build."
    exit 1
fi

echo ""
echo "=== Création du .dmg (create-dmg) ==="
rm -f "${DMG_PATH}"

# create-dmg peut retourner un code de sortie non nul même en cas de succès (l'étape
# de personnalisation Finder/AppleScript échoue silencieusement sur les runners CI
# sans session graphique) — on vérifie donc le résultat par la présence du fichier
# plutôt que par le code de sortie.
create-dmg \
    --volname "${APP_NAME}" \
    --window-size 500 300 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 130 130 \
    --app-drop-link 360 130 \
    "${DMG_PATH}" \
    "${APP_BUNDLE}" || true

if [ ! -f "${DMG_PATH}" ]; then
    echo "Erreur : ${DMG_PATH} introuvable après create-dmg."
    exit 1
fi

echo ""
echo "Image disque créée : ${DMG_PATH}"
echo ""
echo "Distribution :"
echo "  Partager ${DMG_PATH} — l'utilisateur double-clique et glisse l'app dans Applications."
