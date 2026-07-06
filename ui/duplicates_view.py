"""
duplicates_view.py — Vue "Doublons" : détection et archivage des fichiers en double.
"""
import os
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from core.duplicates import archive_duplicates, find_duplicates
from core.theme import APP_THEME
from ui.notification import NotificationBanner
from ui.result_list import ResultList
from ui.toolbar import Toolbar
from ui.widgets import folder_picker_row


class DuplicatesView(ctk.CTkFrame):
    """Vue de détection et d'archivage des doublons."""

    def __init__(self, parent, root, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.root = root
        self._duplicate_groups = []

        self.source_var = tk.StringVar()
        self.archive_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="hash")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(header, text="Doublons", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=APP_THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(header, text="Détecte les fichiers en double et archive-les (jamais de suppression directe).",
                     text_color=APP_THEME["subtext"]).pack(anchor="w")

        form = ctk.CTkFrame(self, fg_color=APP_THEME["bg_secondary"], corner_radius=10)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)

        folder_picker_row(form, "Dossier à analyser", self.source_var, row=0)
        folder_picker_row(form, "Dossier d'archive des doublons", self.archive_var, row=1)

        mode_frame = ctk.CTkFrame(form, fg_color="transparent")
        mode_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 4))
        ctk.CTkLabel(mode_frame, text="Méthode de détection :").pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(mode_frame, text="Contenu identique (fiable)", value="hash",
                           variable=self.mode_var).pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(mode_frame, text="Nom + taille (heuristique)", value="name_size",
                           variable=self.mode_var).pack(side="left")

        self.use_cache_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Réutiliser le cache de hash si inchangé (aperçu rapide)",
                         variable=self.use_cache_var).grid(
            row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 16))

        self.toolbar = Toolbar(self)
        self.toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.toolbar.add_button("scan", "1. Analyser", self._run_scan)
        self.toolbar.add_button("archive", "2. Archiver les doublons", self._run_archive, primary=False)
        self.toolbar.set_enabled("archive", False)

        self.notification = NotificationBanner(self)
        self.notification.grid(row=3, column=0, sticky="ew")
        self.notification.grid_remove()

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=4, column=0, sticky="ew", pady=(0, 12))

        self.results = ResultList(self)
        self.results.grid(row=5, column=0, sticky="nsew")

    def _run_scan(self):
        source = self.source_var.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("Erreur", "Choisis un dossier valide à analyser.")
            return

        mode = self.mode_var.get()
        use_cache = self.use_cache_var.get()

        self.results.clear()
        self.notification.hide()
        self.progress.set(0)
        self.toolbar.set_enabled("archive", False)
        self.toolbar.set_enabled("scan", False)

        def on_progress(current, total):
            fraction = current / total if total else 0
            self.root.after(0, lambda: self.progress.set(fraction))

        def on_log(message):
            self.root.after(0, lambda: self.results.add_line(message))

        def worker():
            groups = find_duplicates(source, mode=mode, use_cache=use_cache,
                                      progress_callback=on_progress, log_callback=on_log)
            self._duplicate_groups = groups

            def _finish():
                self.toolbar.set_enabled("scan", True)
                if groups:
                    self.toolbar.set_enabled("archive", True)
                    nb = sum(len(g) - 1 for g in groups)
                    self.notification.show(f"{nb} doublon(s) détecté(s) — vérifie puis archive.", "info")
                else:
                    self.notification.show("Aucun doublon détecté.", "success")
            self.root.after(0, _finish)

        threading.Thread(target=worker, daemon=True).start()

    def _run_archive(self):
        archive = self.archive_var.get()
        if not archive:
            messagebox.showerror("Erreur", "Choisis un dossier d'archive.")
            return
        if not self._duplicate_groups:
            messagebox.showinfo("Info", "Aucun doublon détecté. Lance d'abord une analyse.")
            return

        nb = sum(len(g) - 1 for g in self._duplicate_groups)
        if not messagebox.askyesno("Confirmer", f"Déplacer {nb} fichier(s) en double vers {archive} ?"):
            return

        self.toolbar.set_enabled("archive", False)
        self.notification.hide()
        self.progress.set(0)

        def on_progress(current, total):
            fraction = current / total if total else 0
            self.root.after(0, lambda: self.progress.set(fraction))

        def on_log(message):
            self.root.after(0, lambda: self.results.add_line(message))

        def worker():
            moved = archive_duplicates(self._duplicate_groups, archive,
                                        progress_callback=on_progress, log_callback=on_log)
            self._duplicate_groups = []

            def _finish():
                self.notification.show(f"{moved} doublon(s) archivé(s) dans {archive}.", "success")
            self.root.after(0, _finish)

        threading.Thread(target=worker, daemon=True).start()
