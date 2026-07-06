"""Tests pour core/duplicates.py"""
from PIL import Image

from core.duplicates import find_duplicates, archive_duplicates, _hash_file


def _make_fake_photo(path, color=(0, 0, 0)):
    Image.new("RGB", (5, 5), color=color).save(path)


def test_hash_file_est_identique_pour_un_contenu_identique(tmp_path):
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    _make_fake_photo(file1, color=(10, 20, 30))
    _make_fake_photo(file2, color=(10, 20, 30))

    assert _hash_file(str(file1)) == _hash_file(str(file2))


def test_hash_file_differe_pour_un_contenu_different(tmp_path):
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    _make_fake_photo(file1, color=(10, 20, 30))
    _make_fake_photo(file2, color=(200, 100, 50))

    assert _hash_file(str(file1)) != _hash_file(str(file2))


def test_find_duplicates_mode_hash_detecte_contenu_identique(tmp_path):
    _make_fake_photo(tmp_path / "original.jpg", color=(10, 20, 30))
    _make_fake_photo(tmp_path / "copie.jpg", color=(10, 20, 30))
    _make_fake_photo(tmp_path / "different.jpg", color=(99, 88, 77))

    groups = find_duplicates(str(tmp_path), mode="hash")

    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_find_duplicates_mode_name_size_ignore_contenu(tmp_path):
    (tmp_path / "sous_dossier").mkdir()
    _make_fake_photo(tmp_path / "photo.jpg", color=(10, 20, 30))
    _make_fake_photo(tmp_path / "sous_dossier" / "photo.jpg", color=(10, 20, 30))

    groups = find_duplicates(str(tmp_path), mode="name_size")

    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_find_duplicates_sans_doublon_ne_retourne_rien(tmp_path):
    _make_fake_photo(tmp_path / "unique1.jpg", color=(1, 2, 3))
    _make_fake_photo(tmp_path / "unique2.jpg", color=(4, 5, 6))

    groups = find_duplicates(str(tmp_path), mode="hash")

    assert groups == []


def test_archive_duplicates_garde_le_premier_et_deplace_le_reste(tmp_path):
    archive = tmp_path / "archive"
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    _make_fake_photo(file1, color=(10, 20, 30))
    _make_fake_photo(file2, color=(10, 20, 30))

    groups = [[str(file1), str(file2)]]
    moved = archive_duplicates(groups, str(archive))

    assert moved == 1
    assert file1.exists()  # le premier du groupe est conservé sur place
    assert not file2.exists()  # le second a été déplacé
    assert (archive / "b.jpg").exists()
