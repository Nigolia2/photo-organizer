#!/usr/bin/env bash
# build_linux.sh — Construit le paquet .deb de Photo Organizer.
# À exécuter depuis la racine du projet sur une machine Linux (amd64 ou arm64).
# Prérequis système : dpkg-deb (paquet dpkg, standard Debian/Ubuntu).
# Prérequis Python  : venv actif avec requirements.txt + pyinstaller installés.
#
# Usage :
#   cd /chemin/vers/photo_organizer
#   source venv/bin/activate
#   pip install pyinstaller>=6.0
#   bash build/build_linux.sh

set -euo pipefail

APP_NAME="PhotoOrganizer"
BINARY_NAME="photo-organizer"          # nom en minuscules pour le paquet Debian
VERSION="1.0.0"
ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
DEB_STEM="${BINARY_NAME}_${VERSION}_${ARCH}"

DIST_DIR="dist"
PYINST_DIR="${DIST_DIR}/${APP_NAME}"   # répertoire --onedir de PyInstaller
DEB_TREE="${DIST_DIR}/${DEB_STEM}"     # arborescence .deb temporaire

echo "=== Build PyInstaller (--onedir) ==="
pyinstaller \
    --onedir \
    --noconsole \
    --name "${APP_NAME}" \
    --distpath "${DIST_DIR}" \
    --workpath "build/pyinstaller_work" \
    --specpath "build" \
    main.py

echo ""
echo "=== Préparation de l'arborescence .deb ==="
rm -rf "${DEB_TREE}"
mkdir -p "${DEB_TREE}/DEBIAN"
mkdir -p "${DEB_TREE}/opt/${BINARY_NAME}"
mkdir -p "${DEB_TREE}/usr/bin"
mkdir -p "${DEB_TREE}/usr/share/applications"
mkdir -p "${DEB_TREE}/usr/share/pixmaps"

# Copie du bundle PyInstaller dans /opt/
cp -r "${PYINST_DIR}/." "${DEB_TREE}/opt/${BINARY_NAME}/"
chmod 755 "${DEB_TREE}/opt/${BINARY_NAME}/${APP_NAME}"

# Launcher dans /usr/bin/
cat > "${DEB_TREE}/usr/bin/${BINARY_NAME}" << EOF
#!/bin/sh
exec /opt/${BINARY_NAME}/${APP_NAME} "\$@"
EOF
chmod 755 "${DEB_TREE}/usr/bin/${BINARY_NAME}"

# Fichier .desktop (menu applicatif)
cat > "${DEB_TREE}/usr/share/applications/${BINARY_NAME}.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Photo Organizer
GenericName=Gestionnaire de photos
Comment=Trie les photos et vidéos par date, archive les doublons
Exec=/usr/bin/photo-organizer
Icon=photo-organizer
Terminal=false
StartupNotify=true
Categories=Graphics;Photography;
EOF

# Icône (optionnel — placer un PNG 256×256 dans build/assets/icon.png)
if [ -f "build/assets/icon.png" ]; then
    cp "build/assets/icon.png" "${DEB_TREE}/usr/share/pixmaps/${BINARY_NAME}.png"
    echo "Icône incluse depuis build/assets/icon.png"
else
    echo "[AVERTISSEMENT] build/assets/icon.png absent — l'icône du menu sera vide."
fi

# DEBIAN/control
cat > "${DEB_TREE}/DEBIAN/control" << EOF
Package: ${BINARY_NAME}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: Nicolas Dupont <turbo-bravo.0g@icloud.com>
Description: Photo Organizer
 Gestionnaire de bibliothèque de photos et vidéos numériques.
 Trie automatiquement par date de prise de vue (EXIF / métadonnées vidéo)
 et détecte/archive les doublons. Interface graphique thème Catppuccin Mocha.
Depends: libc6 (>= 2.17), libx11-6, libxext6, libxft2, tk
EOF

echo ""
echo "=== Génération du paquet .deb ==="
dpkg-deb --root-owner-group --build "${DEB_TREE}" "${DIST_DIR}/${DEB_STEM}.deb"

echo ""
echo "Paquet créé : ${DIST_DIR}/${DEB_STEM}.deb"
echo ""
echo "Installation :"
echo "  sudo apt install ./${DIST_DIR}/${DEB_STEM}.deb"
echo ""
echo "Désinstallation :"
echo "  sudo apt remove ${BINARY_NAME}"
