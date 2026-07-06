#!/usr/bin/env bash
# build_macos.sh — Construit PhotoOrganizer.dmg sur macOS.
# À exécuter sur une machine macOS (Intel ou Apple Silicon) avec Python 3.9+.
# Aucun outil externe requis : PyInstaller + hdiutil (intégré macOS).
#
# Usage :
#   cd /chemin/vers/photo_organizer
#   python3 -m venv venv
#   source venv/bin/activate
#   pip install -r requirements.txt
#   pip install pyinstaller>=6.0
#   bash build/build_macos.sh

set -euo pipefail

APP_NAME="PhotoOrganizer"
DIST_DIR="dist"
DMG_PATH="${DIST_DIR}/${APP_NAME}.dmg"
STAGING_DIR="${DIST_DIR}/dmg_staging"
ICON_PATH="build/assets/icon.png"

echo "=== Build PyInstaller (.app bundle) ==="
pyinstaller \
    --onefile \
    --windowed \
    --name "${APP_NAME}" \
    --distpath "${DIST_DIR}" \
    --workpath "build/pyinstaller_work" \
    --specpath "build" \
    main.py

APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "Erreur : ${APP_BUNDLE} introuvable après la build."
    exit 1
fi

echo ""
echo "=== Création du .dmg ==="
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"
cp -r "${APP_BUNDLE}" "${STAGING_DIR}/"

# Lien symbolique Applications pour faciliter l'installation par glisser-déposer
ln -s /Applications "${STAGING_DIR}/Applications"

rm -f "${DMG_PATH}"
hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${STAGING_DIR}" \
    -ov \
    -format UDZO \
    "${DMG_PATH}"

rm -rf "${STAGING_DIR}"

echo ""
echo "Image disque créée : ${DMG_PATH}"
echo ""
echo "Distribution :"
echo "  Partager ${DMG_PATH} — l'utilisateur double-clique et glisse l'app dans Applications."
