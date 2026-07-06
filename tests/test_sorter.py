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
