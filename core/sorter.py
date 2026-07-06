"""
sorter.py — Organise les photos en dossiers selon leur date de prise de vue,
avec une granularité de classement configurable (année / mois / jour, seuls ou combinés).
"""
import os
import shutil
from .scanner import find_images, get_date_taken

_MOIS_FR = [
    "01 - Janvier", "02 - Février", "03 - Mars", "04 - Avril", "05 - Mai", "06 - Juin",
    "07 - Juillet", "08 - Août", "09 - Septembre", "10 - Octobre", "11 - Novembre", "12 - Décembre"
]

_JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# Composants de dossier inclus pour chaque niveau de granularité, dans l'ordre où ils
# doivent apparaître dans le chemin (année, puis mois, puis jour).
_GRANULARITY_COMPONENTS = {
    "annee": ("annee",),
    "mois": ("mois",),
    "jour": ("jour",),
    "annee_mois": ("annee", "mois"),
    "annee_jour": ("annee", "jour"),
    "mois_jour": ("mois", "jour"),
    "annee_mois_jour": ("annee", "mois", "jour"),
}

# Libellés humains pour l'interface — seule source de vérité pour le sélecteur de l'UI.
GRANULARITY_LABELS = {
    "annee": "Année seule",
    "mois": "Mois seul",
    "jour": "Jour seul",
    "annee_mois": "Année / Mois",
    "annee_jour": "Année / Jour",
    "mois_jour": "Mois / Jour",
    "annee_mois_jour": "Année / Mois / Jour",
}

DEFAULT_GRANULARITY = "annee_mois"  # comportement historique de l'application


def _component_str(component: str, date_taken) -> str:
    """Retourne le libellé d'un composant de dossier (année, mois ou jour) pour une date."""
    if component == "annee":
        return str(date_taken.year)
    if component == "mois":
        return _MOIS_FR[date_taken.month - 1]
    if component == "jour":
        return f"{date_taken.day:02d} {_JOURS_FR[date_taken.weekday()]}"
    raise ValueError(f"Composant de granularité inconnu : {component}")


def build_date_path(date_taken, granularity: str = DEFAULT_GRANULARITY) -> str:
    """
    Retourne le chemin relatif (sous-dossiers) correspondant à la date de prise de vue,
    selon la granularité choisie (une clé de GRANULARITY_LABELS).
    """
    if granularity not in _GRANULARITY_COMPONENTS:
        raise ValueError(f"Granularité inconnue : {granularity}")
    parts = [_component_str(c, date_taken) for c in _GRANULARITY_COMPONENTS[granularity]]
    return os.path.join(*parts)


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
                  granularity: str = DEFAULT_GRANULARITY, progress_callback=None, log_callback=None):
    """
    Parcourt source_folder (un seul scan, effectué avant tout déplacement — jamais de
    re-scan en cours de traitement) et copie/déplace chaque fichier média dans
    dest_folder/<chemin selon la granularité>/nom_fichier.

    Fonctionne aussi bien quand source_folder == dest_folder : chaque fichier est comparé
    à l'emplacement où il devrait se trouver compte tenu de sa date et de la granularité
    choisie. S'il y est déjà, il est laissé en place ("SKIP", pas de copie/déplacement
    inutile) ; sinon il est classé vers son sous-dossier de destination.

    progress_callback(current, total) et log_callback(message) sont optionnels,
    utilisés pour mettre à jour l'interface graphique.
    """
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
            relative_path = build_date_path(date_taken, granularity)
            target_dir = os.path.join(dest_folder, relative_path)
            filename = os.path.basename(filepath)

            # Idempotence : ne pas re-traiter un fichier déjà dans le bon répertoire
            # pour la granularité choisie.
            if os.path.abspath(os.path.dirname(filepath)) == os.path.abspath(target_dir):
                skipped += 1
                if log_callback:
                    log_callback(f"SKIP : {filename} (déjà trié dans {relative_path})")
            else:
                os.makedirs(target_dir, exist_ok=True)
                dest_path = _unique_destination(os.path.join(target_dir, filename))
                if move_files:
                    shutil.move(filepath, dest_path)
                else:
                    shutil.copy2(filepath, dest_path)
                if log_callback:
                    log_callback(f"OK  : {filename} -> {relative_path}")

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
