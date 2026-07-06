"""Tests pour core/duplicates.py"""
import os

from PIL import Image

from core.duplicates import find_duplicates, archive_duplicates, _hash_file, _cache_path


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


def test_find_duplicates_dossier_vide(tmp_path):
    """Un dossier sans fichier média retourne une liste vide de doublons."""
    (tmp_path / "notes.txt").write_text("texte")

    groups = find_duplicates(str(tmp_path), mode="hash")

    assert groups == []


def test_find_duplicates_fichier_illisible_ne_bloque_pas_le_lot(tmp_path):
    """Un fichier avec permissions 000 ne doit pas interrompre l'analyse des autres."""
    import os
    _make_fake_photo(tmp_path / "ok.jpg", color=(10, 20, 30))
    bad = tmp_path / "protege.jpg"
    _make_fake_photo(bad, color=(50, 60, 70))
    os.chmod(str(bad), 0o000)

    errors = []
    try:
        groups = find_duplicates(str(tmp_path), mode="hash",
                                  log_callback=lambda m: errors.append(m))
        # La photo lisible est traitée sans doublon
        assert groups == []
        # Une erreur doit avoir été loggée pour le fichier illisible
        assert any("ERREUR" in e for e in errors)
    finally:
        os.chmod(str(bad), 0o644)


def test_find_duplicates_cache_evite_de_rehacher_fichier_inchange(tmp_path, monkeypatch):
    """En mode aperçu rapide, un fichier inchangé ne doit pas être relu lors d'une 2e analyse."""
    _make_fake_photo(tmp_path / "a.jpg", color=(10, 20, 30))
    _make_fake_photo(tmp_path / "b.jpg", color=(10, 20, 30))

    cache_file = _cache_path(str(tmp_path))
    if os.path.exists(cache_file):
        os.remove(cache_file)

    calls = []
    import core.duplicates as duplicates_module
    original_hash_file = duplicates_module._hash_file

    def counting_hash_file(filepath, *args, **kwargs):
        calls.append(filepath)
        return original_hash_file(filepath, *args, **kwargs)

    monkeypatch.setattr(duplicates_module, "_hash_file", counting_hash_file)

    try:
        groups1 = find_duplicates(str(tmp_path), mode="hash", use_cache=True)
        assert len(calls) == 2  # rien en cache : les 2 fichiers sont hachés

        calls.clear()
        groups2 = find_duplicates(str(tmp_path), mode="hash", use_cache=True)
        assert len(calls) == 0  # tout est en cache : aucun fichier relu
        assert groups2 == groups1
    finally:
        if os.path.exists(cache_file):
            os.remove(cache_file)


def test_find_duplicates_cache_recalcule_si_fichier_modifie(tmp_path):
    """Un fichier modifié après la 1re analyse doit être re-haché (le cache ne doit pas mentir)."""
    fichier = tmp_path / "a.jpg"
    _make_fake_photo(fichier, color=(10, 20, 30))
    _make_fake_photo(tmp_path / "b.jpg", color=(99, 88, 77))

    cache_file = _cache_path(str(tmp_path))
    if os.path.exists(cache_file):
        os.remove(cache_file)

    try:
        groups1 = find_duplicates(str(tmp_path), mode="hash", use_cache=True)
        assert groups1 == []  # aucun doublon au départ

        # a.jpg devient un doublon de b.jpg ; on force un mtime différent pour ne pas
        # dépendre de la résolution de l'horloge du système de fichiers.
        _make_fake_photo(fichier, color=(99, 88, 77))
        nouveau_mtime = os.path.getmtime(str(fichier)) + 5
        os.utime(str(fichier), (nouveau_mtime, nouveau_mtime))

        groups2 = find_duplicates(str(tmp_path), mode="hash", use_cache=True)
        assert len(groups2) == 1
        assert len(groups2[0]) == 2
    finally:
        if os.path.exists(cache_file):
            os.remove(cache_file)


def test_archive_duplicates_gere_collision_dans_archive(tmp_path):
    """Si un fichier du même nom existe déjà dans l'archive, un suffixe est ajouté."""
    archive = tmp_path / "archive"
    archive.mkdir()
    # Pré-existant dans l'archive
    _make_fake_photo(archive / "b.jpg", color=(0, 0, 0))

    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    _make_fake_photo(file1, color=(10, 20, 30))
    _make_fake_photo(file2, color=(10, 20, 30))

    groups = [[str(file1), str(file2)]]
    moved = archive_duplicates(groups, str(archive))

    assert moved == 1
    # Le fichier archivé doit avoir un suffixe pour éviter d'écraser le pré-existant
    assert (archive / "b (1).jpg").exists()
    assert (archive / "b.jpg").exists()  # l'original de l'archive est intact


def test_archive_duplicates_progress_callback_appele(tmp_path):
    """progress_callback doit être appelé une fois par doublon archivé."""
    archive = tmp_path / "archive"
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    file3 = tmp_path / "c.jpg"
    _make_fake_photo(file1, color=(10, 20, 30))
    _make_fake_photo(file2, color=(10, 20, 30))
    _make_fake_photo(file3, color=(10, 20, 30))

    calls = []
    groups = [[str(file1), str(file2), str(file3)]]
    archive_duplicates(groups, str(archive), progress_callback=lambda c, t: calls.append((c, t)))

    assert len(calls) == 2  # deux doublons déplacés
    assert calls[-1] == (2, 2)


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
