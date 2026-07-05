"""
scanner.py — Scan d'un dossier pour trouver les images et extraire leur date de prise de vue.
"""
import os
from datetime import datetime
from PIL import Image, ExifTags

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp", ".heic", ".heif"
}

# Tag EXIF pour la date de prise de vue originale
DATETIME_ORIGINAL_TAG = None
for tag_id, tag_name in ExifTags.TAGS.items():
    if tag_name == "DateTimeOriginal":
        DATETIME_ORIGINAL_TAG = tag_id
        break


def is_image_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".heic", ".heif") and not HEIC_SUPPORTED:
        return False
    return ext in IMAGE_EXTENSIONS


def find_images(root_folder: str):
    """Génère la liste de tous les fichiers image sous root_folder (récursif)."""
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if is_image_file(full_path):
                yield full_path


def get_date_taken(filepath: str) -> datetime:
    """
    Retourne la date de prise de vue d'une photo.
    Priorité : EXIF DateTimeOriginal > EXIF DateTime > date de modification du fichier.
    """
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()
            if exif:
                raw_date = exif.get(DATETIME_ORIGINAL_TAG) if DATETIME_ORIGINAL_TAG else None
                if not raw_date:
                    raw_date = exif.get(306)  # tag "DateTime" générique
                if raw_date:
                    # Format EXIF standard : "YYYY:MM:DD HH:MM:SS"
                    return datetime.strptime(raw_date.strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    # Repli : date de dernière modification du fichier
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp)
