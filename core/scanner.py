"""
scanner.py — Scan d'un dossier pour trouver les photos/vidéos et extraire leur date de prise de vue.
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

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_AVAILABLE = True
except ImportError:
    HACHOIR_AVAILABLE = False

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp", ".heic", ".heif"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp", ".wmv"
}

MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

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


def is_video_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in VIDEO_EXTENSIONS


def is_media_file(path: str) -> bool:
    """Vrai si le fichier est une photo ou une vidéo supportée."""
    return is_image_file(path) or is_video_file(path)


def find_images(root_folder: str):
    """
    Génère la liste de tous les fichiers média (photos ET vidéos) sous root_folder (récursif).
    Le nom est conservé pour compatibilité mais couvre aussi les vidéos.
    """
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if is_media_file(full_path):
                yield full_path


def _get_photo_date(filepath: str):
    """Extrait la date EXIF d'une photo, ou None si absente/illisible."""
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
    return None


def _get_video_date(filepath: str):
    """Extrait la date de création d'une vidéo via les métadonnées du conteneur, ou None."""
    if not HACHOIR_AVAILABLE:
        return None
    try:
        parser = createParser(filepath)
        if not parser:
            return None
        with parser:
            metadata = extractMetadata(parser)
        if metadata and metadata.has("creation_date"):
            value = metadata.get("creation_date")
            if isinstance(value, datetime):
                return value
    except Exception:
        pass
    return None


def get_date_taken(filepath: str) -> datetime:
    """
    Retourne la date de prise de vue/tournage d'un fichier média.
    Priorité :
      - Photos : EXIF DateTimeOriginal > EXIF DateTime > date de modification du fichier.
      - Vidéos : métadonnées de création du conteneur > date de modification du fichier.
    """
    date_found = None
    if is_video_file(filepath):
        date_found = _get_video_date(filepath)
    else:
        date_found = _get_photo_date(filepath)

    if date_found:
        return date_found

    # Repli commun : date de dernière modification du fichier
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp)
