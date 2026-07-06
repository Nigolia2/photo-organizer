"""
sorter.py — Organise les photos en dossiers Année/Mois selon leur date de prise de vue.
"""
import os
import shutil
from .scanner import find_images, get_date_taken


def _unique_destination(dest_path: str) -> str:
    """Si dest_path existe déjà, ajoute un suffixe numérique pour éviter d'écraser un fichier."""
    if not os.path.exists(dest_path):
        return dest_path
    base, ext = os.path.splitext(dest_path)
    counter = 1
    while True:
        candidate = f"{base} ({counter}){ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def sort_by_date(source_folder: str, dest_folder: str, move_files: bool = False,
                  month_names_fr: bool = True, progress_callback=None, log_callback=None):
    """
    Parcourt source_folder, et copie/déplace chaque photo dans
    dest_folder/AAAA/MM - Mois/nom_fichier

    progress_callback(current, total) et log_callback(message) sont optionnels,
    utilisés pour mettre à jour l'interface graphique.
    """
    mois_fr = [
        "01 - Janvier", "02 - Février", "03 - Mars", "04 - Avril", "05 - Mai", "06 - Juin",
        "07 - Juillet", "08 - Août", "09 - Septembre", "10 - Octobre", "11 - Novembre", "12 - Décembre"
    ]

    files = list(find_images(source_folder))
    total = len(files)
    processed = 0
    errors = 0
    skipped = 0

    if log_callback:
        log_callback(f"{total} fichier(s) média trouvé(s) dans {source_folder}")

    for filepath in files:
        try:
            date_taken = get_date_taken(filepath)
            year_str = str(date_taken.year)
            month_str = mois_fr[date_taken.month - 1] if month_names_fr else f"{date_taken.month:02d}"
            target_dir = os.path.join(dest_folder, year_str, month_str)
            filename = os.path.basename(filepath)

            # Idempotence : ne pas re-traiter un fichier déjà dans le bon répertoire
            if os.path.abspath(os.path.dirname(filepath)) == os.path.abspath(target_dir):
                skipped += 1
                if log_callback:
                    log_callback(f"SKIP : {filename} (déjà trié dans {year_str}/{month_str})")
            else:
                os.makedirs(target_dir, exist_ok=True)
                dest_path = _unique_destination(os.path.join(target_dir, filename))
                if move_files:
                    shutil.move(filepath, dest_path)
                else:
                    shutil.copy2(filepath, dest_path)
                if log_callback:
                    log_callback(f"OK  : {filename} -> {year_str}/{month_str}")

        except Exception as e:
            errors += 1
            if log_callback:
                log_callback(f"ERREUR sur {filepath} : {e}")

        processed += 1
        if progress_callback:
            progress_callback(processed, total)

    if log_callback:
        sorted_count = processed - errors - skipped
        log_callback(
            f"Terminé : {sorted_count}/{total} trié(s), "
            f"{skipped} déjà en place, {errors} erreur(s)."
        )

    return processed - errors, errors
