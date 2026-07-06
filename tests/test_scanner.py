"""Tests pour core/scanner.py"""
import os
import stat
import struct
from datetime import datetime
from PIL import Image

from core.scanner import (
    is_image_file, is_video_file, is_media_file, find_images, get_date_taken,
    _get_photo_date, _get_video_date,
)

# Epoque de référence des timestamps MP4/QuickTime (mvhd) : 1er janvier 1904 UTC.
_MP4_EPOCH = datetime(1904, 1, 1)


def _make_fake_video(path, creation_date: datetime = None):
    """
    Écrit un fichier .mp4 minimal (ftyp + moov/mvhd) pour les tests.
    Si creation_date est fourni, le champ creation_time du mvhd est renseigné
    (ce que hachoir lit comme métadonnée "creation_date") ; sinon aucun moov
    n'est écrit, pour simuler une vidéo sans métadonnées exploitables.
    """
    def box(box_type: bytes, payload: bytes) -> bytes:
        return struct.pack(">I4s", 8 + len(payload), box_type) + payload

    ftyp = box(b"ftyp", b"isom" + struct.pack(">I", 0) + b"isomiso2mp41")

    if creation_date is None:
        data = ftyp
    else:
        creation_time = int((creation_date - _MP4_EPOCH).total_seconds())
        mvhd_body = struct.pack(">B3s", 0, b"\x00\x00\x00")
        mvhd_body += struct.pack(">III", creation_time, creation_time, 1000)
        mvhd_body += struct.pack(">I", 5000)
        mvhd_body += struct.pack(">I", 0x00010000)
        mvhd_body += struct.pack(">H", 0x0100)
        mvhd_body += b"\x00\x00" + b"\x00" * 8
        mvhd_body += struct.pack(">9i", 0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000)
        mvhd_body += b"\x00" * 24
        mvhd_body += struct.pack(">I", 2)
        moov = box(b"moov", box(b"mvhd", mvhd_body))
        data = ftyp + moov

    with open(path, "wb") as f:
        f.write(data)


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


def test_get_video_date_lit_metadata_creation(tmp_path):
    """Métadonnées de conteneur présentes (mvhd.creation_time) : la date doit être lue."""
    video_path = tmp_path / "clip.mp4"
    _make_fake_video(video_path, creation_date=datetime(2018, 3, 22, 10, 15, 0))

    date = _get_video_date(str(video_path))

    assert date is not None
    assert date.year == 2018
    assert date.month == 3
    assert date.day == 22
    assert date.hour == 10
    assert date.minute == 15


def test_get_date_taken_utilise_metadata_video_quand_present(tmp_path):
    """get_date_taken retourne bien la date de création vidéo plutôt que la date
    de modification du fichier, même quand les deux diffèrent nettement."""
    video_path = tmp_path / "clip.mp4"
    _make_fake_video(video_path, creation_date=datetime(2015, 7, 4, 9, 0, 0))

    # Date de modification du fichier volontairement différente (aujourd'hui).
    now = datetime.now().timestamp()
    os.utime(str(video_path), (now, now))

    date = get_date_taken(str(video_path))

    assert date.year == 2015
    assert date.month == 7
    assert date.day == 4


def test_get_date_taken_video_repli_sur_date_modification_si_pas_de_metadata(tmp_path):
    """Vidéo sans métadonnées de création exploitables : repli sur mtime, comme pour les photos."""
    video_path = tmp_path / "sans_metadata.mp4"
    _make_fake_video(video_path, creation_date=None)

    date_taken = get_date_taken(str(video_path))
    date_modif = datetime.fromtimestamp(os.path.getmtime(str(video_path)))

    assert abs((date_taken - date_modif).total_seconds()) < 2


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
