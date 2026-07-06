"""
widgets.py — Petits composants CTk partagés entre les vues.
"""
from tkinter import filedialog

import customtkinter as ctk

from core.theme import APP_THEME


def folder_picker_row(parent, label_text, variable, row):
    """Ajoute, dans une grille, une ligne label + champ + bouton 'Parcourir…'."""
    ctk.CTkLabel(parent, text=label_text, anchor="w").grid(
        row=row, column=0, sticky="w", padx=(16, 8), pady=8)

    entry = ctk.CTkEntry(parent, textvariable=variable)
    entry.grid(row=row, column=1, sticky="ew", pady=8)

    def browse():
        chosen = filedialog.askdirectory()
        if chosen:
            variable.set(chosen)

    ctk.CTkButton(parent, text="Parcourir…", width=110, fg_color=APP_THEME["gray5"],
                  hover_color=APP_THEME["gray4"], text_color=APP_THEME["text"],
                  command=browse).grid(row=row, column=2, padx=(8, 16), pady=8)
