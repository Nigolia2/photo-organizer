"""Tests pour core/sorter.py"""
import os
from PIL import Image

from core.sorter import sort_by_date, _unique_destination


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

    # Trier le dossier dest sur lui-même (source == dest)
    # Doit être refusé ; on teste donc la source = sous-dossier contenant la photo
    # et dest = dossier parent : comportement idempotent
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
