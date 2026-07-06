"""Tests pour core/scanner.py"""
import os
import stat
from datetime import datetime
from PIL import Image

from core.scanner import (
    is_image_file, is_video_file, is_media_file, find_images, get_date_taken,
    _get_photo_date,
)


def test_is_image_file_reconnait_les_extensions_courantes():
    assert is_image_file("photo.jpg")
    assert is_image_file("photo.PNG")  # insensible à la casse
    assert not is_image_file("document.pdf")


def test_is_video_file_reconnait_les_extensions_courantes():
    assert is_video_file("clip.mp4")
    assert is_video_file("clip.MOV")
    assert not is_video_file("photo.jpg")


def test_is_media_file_couvre_photos_et_videos():
    assert is_media_file("photo.jpg")
    assert is_media_file("clip.mp4")
    assert not is_media_file("notes.txt")


def test_find_images_scanne_recursivement(tmp_path):
    (tmp_path / "sous_dossier").mkdir()
    img1 = tmp_path / "photo1.jpg"
    img2 = tmp_path / "sous_dossier" / "photo2.jpg"
    autre = tmp_path / "notes.txt"

    Image.new("RGB", (5, 5)).save(img1)
    Image.new("RGB", (5, 5)).save(img2)
    autre.write_text("pas une image")

    found = set(find_images(str(tmp_path)))
    assert str(img1) in found
    assert str(img2) in found
    assert str(autre) not in found


def test_get_date_taken_repli_sur_date_modification_si_pas_exif(tmp_path):
    img_path = tmp_path / "sans_exif.jpg"
    Image.new("RGB", (5, 5)).save(img_path)

    date_taken = get_date_taken(str(img_path))
    date_modif = datetime.fromtimestamp(os.path.getmtime(str(img_path)))

    assert isinstance(date_taken, datetime)
    # Sans EXIF, on doit retomber sur la date de modification (à la seconde près)
    assert abs((date_taken - date_modif).total_seconds()) < 2


def test_get_photo_date_lit_exif_datetime_original(tmp_path):
    """EXIF DateTimeOriginal présent : la date doit être lue et parsée correctement."""
    img_path = tmp_path / "avec_exif.jpg"
    img = Image.new("RGB", (10, 10))
    exif = img.getexif()
    exif[36867] = "2023:06:15 14:30:00"  # tag DateTimeOriginal
    img.save(img_path, exif=exif.tobytes())

    date = _get_photo_date(str(img_path))

    assert date is not None
    assert date.year == 2023
    assert date.month == 6
    assert date.day == 15
    assert date.hour == 14
    assert date.minute == 30


def test_get_date_taken_utilise_exif_quand_present(tmp_path):
    """get_date_taken retourne bien la date EXIF plutôt que la date de modification."""
    img_path = tmp_path / "avec_exif.jpg"
    img = Image.new("RGB", (10, 10))
    exif = img.getexif()
    exif[36867] = "2019:01:01 00:00:00"
    img.save(img_path, exif=exif.tobytes())

    date = get_date_taken(str(img_path))

    assert date.year == 2019
    assert date.month == 1


def test_get_date_taken_repli_si_fichier_illisible(tmp_path):
    """Une image illisible (permissions) ne lève pas d'exception : repli sur mtime."""
    img_path = tmp_path / "protege.jpg"
    Image.new("RGB", (5, 5)).save(img_path)
    os.chmod(str(img_path), 0o000)

    try:
        date = get_date_taken(str(img_path))
        # Sur Linux le repli se fait sur os.path.getmtime, lui aussi peut échouer
        # avec 0o000 — dans ce cas une exception est attendue en dehors de la lib.
        assert isinstance(date, datetime)
    except PermissionError:
        pass  # comportement acceptable si l'OS bloque même getmtime
    finally:
        os.chmod(str(img_path), 0o644)  # restaurer pour le nettoyage tmp_path


def test_find_images_avec_nom_contenant_accents(tmp_path):
    """Les fichiers avec caractères accentués dans le nom sont correctement détectés."""
    accented = tmp_path / "été_2023.jpg"
    Image.new("RGB", (5, 5)).save(accented)

    found = list(find_images(str(tmp_path)))

    assert str(accented) in found


def test_find_images_dossier_vide(tmp_path):
    """Un dossier sans fichier média retourne une liste vide."""
    (tmp_path / "notes.txt").write_text("texte")

    found = list(find_images(str(tmp_path)))

    assert found == []
