"""
duplicates.py — Détecte les photos en double (par contenu ou par nom+taille)
et les déplace dans un dossier d'archive.
"""
import hashlib
import json
import os
import shutil
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from .scanner import find_images

# Nombre de threads pour le hashing parallèle. Opération I/O-bound (lecture disque) :
# un nombre de threads supérieur au nombre de cœurs reste utile car ils passent le plus
# clair de leur temps à attendre le disque plutôt qu'à consommer du CPU.
_HASH_WORKERS = 8


def _hash_file(filepath: str, block_size: int = 65536) -> str:
    """Calcule le hash SHA-256 du contenu d'un fichier."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _cache_path(source_folder: str) -> str:
    """Chemin du fichier de cache de hash associé à un dossier (un cache par dossier analysé)."""
    digest = hashlib.sha256(os.path.abspath(source_folder).encode("utf-8")).hexdigest()
    cache_dir = os.path.join(tempfile.gettempdir(), "photo_organizer_hash_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{digest}.json")


def _load_hash_cache(source_folder: str) -> dict:
    """Charge le cache de hash (filepath -> {mtime, size, hash}) du dossier, s'il existe."""
    try:
        with open(_cache_path(source_folder), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_hash_cache(source_folder: str, cache: dict):
    """Sauvegarde le cache de hash mis à jour sur disque."""
    try:
        with open(_cache_path(source_folder), "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except OSError:
        pass


def _hash_file_cached(filepath: str, cache: dict) -> str:
    """
    Calcule le hash d'un fichier, en réutilisant le cache si la taille et la date de
    modification n'ont pas changé depuis le dernier calcul (mode "aperçu rapide") —
    évite de relire le contenu des fichiers inchangés lors d'une ré-analyse du même dossier.
    """
    stat = os.stat(filepath)
    cached = cache.get(filepath)
    if cached and cached["size"] == stat.st_size and cached["mtime"] == stat.st_mtime:
        return cached["hash"]
    digest = _hash_file(filepath)
    cache[filepath] = {"size": stat.st_size, "mtime": stat.st_mtime, "hash": digest}
    return digest


def find_duplicates(source_folder: str, mode: str = "hash", use_cache: bool = False,
                     progress_callback=None, log_callback=None):
    """
    mode = "hash"      : doublons stricts (contenu identique, octet pour octet). Fiable à 100%.
    mode = "name_size"  : doublons probables (même nom de fichier + même taille). Heuristique.

    use_cache : uniquement en mode "hash" — réutilise un cache de hash sur disque (un par
    dossier analysé) pour ne pas relire le contenu des fichiers inchangés depuis la dernière
    analyse ("aperçu rapide", utile en cas de ré-analyse répétée d'une même bibliothèque).

    Le hashing (mode "hash") est parallélisé sur plusieurs threads : c'est une opération
    I/O-bound (lecture disque), les threads restent donc bénéfiques malgré le GIL.

    Retourne une liste de groupes de doublons : [[fichier_gardé, doublon1, doublon2, ...], ...]
    """
    files = list(find_images(source_folder))
    total = len(files)
    groups = defaultdict(list)
    processed = 0

    if mode == "hash":
        cache = _load_hash_cache(source_folder) if use_cache else {}
        hash_fn = (lambda fp: _hash_file_cached(fp, cache)) if use_cache else _hash_file

        with ThreadPoolExecutor(max_workers=_HASH_WORKERS) as executor:
            future_to_path = {executor.submit(hash_fn, filepath): filepath for filepath in files}
            for future in as_completed(future_to_path):
                filepath = future_to_path[future]
                try:
                    groups[future.result()].append(filepath)
                except Exception as e:
                    if log_callback:
                        log_callback(f"ERREUR lecture {filepath} : {e}")
                processed += 1
                if progress_callback:
                    progress_callback(processed, total)

        if use_cache:
            _save_hash_cache(source_folder, cache)
    else:  # name_size
        for filepath in files:
            try:
                name = os.path.basename(filepath).lower()
                size = os.path.getsize(filepath)
                groups[(name, size)].append(filepath)
            except Exception as e:
                if log_callback:
                    log_callback(f"ERREUR lecture {filepath} : {e}")

            processed += 1
            if progress_callback:
                progress_callback(processed, total)

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
