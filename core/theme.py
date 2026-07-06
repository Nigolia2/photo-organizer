"""
theme.py — Palette et configuration du thème CustomTkinter "macOS Big Sur (mode clair)".
La palette de couleurs vit ici (APP_THEME) ; les couleurs par widget CustomTkinter
sont définies dans theme.json et chargées via apply_app_theme().
"""
import os
import sys

import customtkinter as ctk

if sys.platform == "win32":
    MONO_FONT = ("Consolas", 11)
elif sys.platform == "darwin":
    MONO_FONT = ("Menlo", 12)
else:
    MONO_FONT = ("DejaVu Sans Mono", 11)

APP_THEME = {
    "bg": "#FFFFFF",           # Fond principal (fenêtre)
    "bg_secondary": "#F2F2F7",  # Fond secondaire (panneaux, listes)
    "sidebar": "#F6F6F6",        # Fond sidebar (translucide clair)
    "border": "#C6C6C8",          # Séparateurs / bordures
    "text": "#000000",              # Texte principal
    "subtext": "#6E6E73",             # Texte secondaire (équivalent #3C3C43 ~60% opacité)
    "on_accent": "#FFFFFF",             # Texte/icône sur fond de couleur d'accent

    "gray": "#8E8E93",
    "gray2": "#AEAEB2",
    "gray3": "#C7C7CC",
    "gray4": "#D1D1D6",
    "gray5": "#E5E5EA",
    "gray6": "#F2F2F7",

    "blue": "#007AFF",       # Accent principal
    "green": "#34C759",       # Succès
    "red": "#FF3B30",           # Erreur
    "orange": "#FF9500",          # Avertissement
    "purple": "#AF52DE",            # Accent secondaire
    "indigo": "#5856D6",
    "pink": "#FF2D55",
    "yellow": "#FFCC00",
}

_THEME_JSON_PATH = os.path.join(os.path.dirname(__file__), "theme.json")


def apply_app_theme():
    """
    Configure CustomTkinter pour appliquer systématiquement le thème clair
    macOS Big Sur (theme.json), quel que soit le thème système.
    À appeler une seule fois, avant de créer la fenêtre principale (ctk.CTk()).
    """
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme(_THEME_JSON_PATH)
