"""Tests pour core/scanner.py"""
import os
from datetime import datetime
from PIL import Image

from core.scanner import (
    is_image_file, is_video_file, is_media_file, find_images, get_date_taken
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
