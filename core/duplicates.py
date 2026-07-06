"""
duplicates.py — Détecte les photos en double (par contenu ou par nom+taille)
et les déplace dans un dossier d'archive.
"""
import os
import hashlib
import shutil
from collections import defaultdict
from .scanner import find_images


def _hash_file(filepath: str, block_size: int = 65536) -> str:
    """Calcule le hash SHA-256 du contenu d'un fichier."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(source_folder: str, mode: str = "hash", progress_callback=None, log_callback=None):
    """
    mode = "hash"      : doublons stricts (contenu identique, octet pour octet). Fiable à 100%.
    mode = "name_size"  : doublons probables (même nom de fichier + même taille). Heuristique.

    Retourne une liste de groupes de doublons : [[fichier_gardé, doublon1, doublon2, ...], ...]
    """
    files = list(find_images(source_folder))
    total = len(files)
    groups = defaultdict(list)

    for i, filepath in enumerate(files):
        try:
            if mode == "hash":
                key = _hash_file(filepath)
            else:  # name_size
                name = os.path.basename(filepath).lower()
                size = os.path.getsize(filepath)
                key = (name, size)
            groups[key].append(filepath)
        except Exception as e:
            if log_callback:
                log_callback(f"ERREUR lecture {filepath} : {e}")

        if progress_callback:
            progress_callback(i + 1, total)

    # Ne garder que les groupes avec au moins un doublon
    duplicate_groups = [sorted(paths) for paths in groups.values() if len(paths) > 1]

    if log_callback:
        nb_doublons = sum(len(g) - 1 for g in duplicate_groups)
        log_callback(f"{len(duplicate_groups)} groupe(s) de doublons trouvé(s), {nb_doublons} fichier(s) en trop.")

    return duplicate_groups


def archive_duplicates(duplicate_groups, archive_folder: str,
                       progress_callback=None, log_callback=None):
    """
    Pour chaque groupe, garde le premier fichier (ordre alphabétique du chemin)
    et déplace les autres vers archive_folder (en conservant le nom, avec suffixe si collision).
    """
    os.makedirs(archive_folder, exist_ok=True)
    moved = 0
    total = sum(len(g) - 1 for g in duplicate_groups)
    done = 0

    for group in duplicate_groups:
        kept = group[0]
        if log_callback:
            log_callback(f"Conservé : {kept}")

        for dup in group[1:]:
            filename = os.path.basename(dup)
            dest_path = os.path.join(archive_folder, filename)

            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = f"{base} ({counter}){ext}"
                counter += 1

            try:
                shutil.move(dup, dest_path)
                moved += 1
                if log_callback:
                    log_callback(f"  -> Archivé : {dup} -> {dest_path}")
            except Exception as e:
                if log_callback:
                    log_callback(f"  -> ERREUR sur {dup} : {e}")

            done += 1
            if progress_callback:
                progress_callback(done, max(total, 1))

    if log_callback:
        log_callback(f"Terminé : {moved} doublon(s) archivé(s) dans {archive_folder}")

    return moved
