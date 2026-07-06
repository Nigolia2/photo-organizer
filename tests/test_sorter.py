"""Tests pour core/sorter.py"""
import os
import time
from datetime import datetime
from PIL import Image

from core.sorter import sort_by_date, _unique_destination, build_date_path


def _make_fake_photo(path):
    Image.new("RGB", (5, 5)).save(path)


def test_unique_destination_ajoute_un_suffixe_si_collision(tmp_path):
    existing = tmp_path / "photo.jpg"
    existing.write_text("existe déjà")

    result = _unique_destination(str(existing))

    assert result != str(existing)
    assert result.endswith("(1).jpg")


def test_unique_destination_ne_change_rien_si_pas_de_collision(tmp_path):
    target = tmp_path / "nouveau.jpg"
    result = _unique_destination(str(target))
    assert result == str(target)


def test_sort_by_date_copie_par_defaut(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()

    photo = source / "vacances.jpg"
    _make_fake_photo(photo)

    n_ok, n_err = sort_by_date(str(source), str(dest), move_files=False)

    assert n_ok == 1
    assert n_err == 0
    assert photo.exists()  # le fichier source doit toujours exister (copie, pas déplacement)

    # Un fichier doit avoir été créé quelque part sous dest/AAAA/MM - Mois/
    copied_files = list(dest.rglob("vacances.jpg"))
    assert len(copied_files) == 1


def test_sort_by_date_deplace_si_demande(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()

    photo = source / "vacances.jpg"
    _make_fake_photo(photo)

    n_ok, n_err = sort_by_date(str(source), str(dest), move_files=True)

    assert n_ok == 1
    assert n_err == 0
    assert not photo.exists()  # le fichier source doit avoir disparu (déplacement)

    moved_files = list(dest.rglob("vacances.jpg"))
    assert len(moved_files) == 1


def test_sort_by_date_dossier_source_vide(tmp_path):
    """Un dossier source sans fichier média ne doit provoquer aucune erreur."""
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    (source / "readme.txt").write_text("pas une image")

    n_ok, n_err = sort_by_date(str(source), str(dest))

    assert n_ok == 0
    assert n_err == 0


def test_sort_by_date_idempotent_ne_duplique_pas(tmp_path):
    """Un fichier déjà dans le bon répertoire ne doit pas être copié à nouveau."""
    dest = tmp_path / "dest"

    # Créer une photo avec EXIF 2019/01/01 directement dans le répertoire cible attendu
    from PIL import Image as PilImage
    target_dir = dest / "2019" / "01 - Janvier"
    target_dir.mkdir(parents=True)
    photo = target_dir / "deja_triee.jpg"
    img = PilImage.new("RGB", (5, 5))
    exif = img.getexif()
    exif[36867] = "2019:01:01 12:00:00"
    img.save(photo, exif=exif.tobytes())

    # Trier le dossier dest sur lui-même (source == dest) : comportement idempotent
    log_messages = []
    n_ok, n_err = sort_by_date(str(dest), str(dest), move_files=False,
                                log_callback=log_messages.append)

    # Le fichier doit être signalé comme déjà trié, pas copié
    assert any("SKIP" in m for m in log_messages)
    # Un seul fichier doit exister (pas de doublon créé)
    all_photos = list(dest.rglob("deja_triee*"))
    assert len(all_photos) == 1


def test_sort_by_date_gere_les_collisions_de_noms(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()

    photo1 = source / "photo.jpg"
    _make_fake_photo(photo1)

    # Simule une collision : un fichier du même nom existe déjà à destination
    year_month_dir = dest / "2026" / "07 - Juillet"
    year_month_dir.mkdir(parents=True)
    (year_month_dir / "photo.jpg").write_text("déjà présent")

    n_ok, n_err = sort_by_date(str(source), str(dest), move_files=False)

    assert n_ok == 1
    assert n_err == 0
    # Les deux fichiers doivent coexister (celui déjà présent + le nouveau renommé)
    files_in_dest = list(year_month_dir.glob("photo*"))
    assert len(files_in_dest) == 2


def test_build_date_path_couvre_les_sept_granularites():
    """Vérifie le chemin relatif généré pour chacune des 7 combinaisons de granularité."""
    date_taken = datetime(2026, 1, 12, 10, 30)  # un lundi (cf. exemple du cahier des charges)

    assert build_date_path(date_taken, "annee") == "2026"
    assert build_date_path(date_taken, "mois") == "01 - Janvier"
    assert build_date_path(date_taken, "jour") == "12 Lundi"
    assert build_date_path(date_taken, "annee_mois") == os.path.join("2026", "01 - Janvier")
    assert build_date_path(date_taken, "annee_jour") == os.path.join("2026", "12 Lundi")
    assert build_date_path(date_taken, "mois_jour") == os.path.join("01 - Janvier", "12 Lundi")
    assert build_date_path(date_taken, "annee_mois_jour") == os.path.join(
        "2026", "01 - Janvier", "12 Lundi")


def test_sort_by_date_source_egale_destination_granularite_annee_mois(tmp_path):
    """source == destination : les fichiers sont classés dans des sous-dossiers du même
    dossier, sans perte ni duplication (granularité année/mois)."""
    folder = tmp_path / "bibliotheque"
    folder.mkdir()

    photo1 = folder / "vacances.jpg"
    photo2 = folder / "anniversaire.jpg"
    _make_fake_photo(photo1)
    _make_fake_photo(photo2)

    n_ok, n_err = sort_by_date(str(folder), str(folder), move_files=True,
                                granularity="annee_mois")

    assert n_ok == 2
    assert n_err == 0
    assert not photo1.exists()
    assert not photo2.exists()
    assert len(list(folder.rglob("vacances.jpg"))) == 1
    assert len(list(folder.rglob("anniversaire.jpg"))) == 1


def test_sort_by_date_source_egale_destination_granularite_annee_seule(tmp_path):
    """source == destination avec la granularité 'année seule' (un seul niveau de
    sous-dossier) : même garantie de non-perte/non-duplication."""
    folder = tmp_path / "bibliotheque"
    folder.mkdir()

    photo = folder / "photo.jpg"
    _make_fake_photo(photo)

    n_ok, n_err = sort_by_date(str(folder), str(folder), move_files=True,
                                granularity="annee")

    assert n_ok == 1
    assert n_err == 0
    assert not photo.exists()
    matches = list(folder.rglob("photo.jpg"))
    assert len(matches) == 1
    assert matches[0].parent != folder  # déplacé dans un sous-dossier "AAAA/", pas resté à la racine


def test_sort_by_date_change_de_granularite_redeclenche_le_tri(tmp_path):
    """Un fichier bien classé en 'année seule' n'est pas retraité tant que la granularité
    ne change pas ; il doit être reclassé si on passe à 'année/mois'."""
    dest = tmp_path / "dest"

    target_dir = dest / "2019"
    target_dir.mkdir(parents=True)
    photo = target_dir / "photo.jpg"
    img = Image.new("RGB", (5, 5))
    exif = img.getexif()
    exif[36867] = "2019:03:10 09:00:00"
    img.save(photo, exif=exif.tobytes())

    # Avec la granularité "annee", le fichier est déjà bien classé : SKIP, pas de déplacement.
    log_messages = []
    sort_by_date(str(dest), str(dest), move_files=True, granularity="annee",
                 log_callback=log_messages.append)
    assert any("SKIP" in m for m in log_messages)
    assert photo.exists()

    # Avec la granularité "annee_mois", il doit maintenant être déplacé dans 2019/03 - Mars/.
    log_messages.clear()
    sort_by_date(str(dest), str(dest), move_files=True, granularity="annee_mois",
                 log_callback=log_messages.append)
    assert any("OK" in m for m in log_messages)
    assert not photo.exists()
    assert (dest / "2019" / "03 - Mars" / "photo.jpg").exists()


def test_sort_by_date_utilise_la_date_exif_pas_la_date_de_fichier(tmp_path):
    """Le tri doit se baser sur la date EXIF (prise de vue), jamais sur la date de
    modification du fichier, même quand les deux diffèrent nettement."""
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()

    photo = source / "photo.jpg"
    img = Image.new("RGB", (5, 5))
    exif = img.getexif()
    exif[36867] = "2024:03:15 10:00:00"  # DateTimeOriginal : 15 mars 2024
    img.save(photo, exif=exif.tobytes())

    # Date de modification du fichier volontairement différente de l'EXIF (aujourd'hui),
    # pour s'assurer que le tri ignore mtime tant que la date EXIF est présente.
    now = time.time()
    os.utime(photo, (now, now))

    n_ok, n_err = sort_by_date(str(source), str(dest), move_files=False)

    assert n_ok == 1
    assert n_err == 0
    expected_path = dest / "2024" / "03 - Mars" / "photo.jpg"
    assert expected_path.exists()
    # Aucune autre copie ailleurs (ex: dans un dossier basé sur la date du jour) : la seule
    # copie existante est bien celle placée d'après la date EXIF.
    assert list(dest.rglob("photo.jpg")) == [expected_path]
