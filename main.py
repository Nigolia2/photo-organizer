#!/usr/bin/env python3
"""
Photo Organizer — Gestionnaire de bibliothèque de photos et vidéos numériques.
Trie les fichiers média par date (EXIF / métadonnées vidéo) et détecte/archive les doublons.
Thème : palette macOS Big Sur, mode clair (CustomTkinter).
"""
import customtkinter as ctk

from core.theme import APP_THEME, apply_app_theme
from ui.duplicates_view import DuplicatesView
from ui.sidebar import Sidebar
from ui.sort_view import SortView


class PhotoOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Photo Organizer")
        self.geometry("980x680")
        self.minsize(820, 560)
        self.configure(fg_color=APP_THEME["bg"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            self,
            items=[("sort", "Trier par date", "▦"), ("dup", "Doublons", "◆")],
            on_select=self._show_view,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        content = ctk.CTkFrame(self, fg_color=APP_THEME["bg"])
        content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.views = {
            "sort": SortView(content, self),
            "dup": DuplicatesView(content, self),
        }
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

        self._show_view("sort")

    def _show_view(self, key):
        self.views[key].tkraise()


def main():
    apply_app_theme()
    app = PhotoOrganizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
