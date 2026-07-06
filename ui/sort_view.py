"""
sort_view.py — Vue "Trier par date" : classe les photos/vidéos selon la granularité choisie.
"""
import os
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from core.sorter import sort_by_date, GRANULARITY_LABELS, DEFAULT_GRANULARITY
from core.theme import APP_THEME
from ui.notification import NotificationBanner
from ui.result_list import ResultList
from ui.toolbar import Toolbar
from ui.widgets import folder_picker_row

_MOVE_TEXT_NORMAL = "Déplacer les fichiers (sinon : copier)"
_MOVE_TEXT_LOCKED = "Déplacer les fichiers (forcé : source = destination)"


class SortView(ctk.CTkFrame):
    """Vue de tri des fichiers média par date de prise de vue."""

    def __init__(self, parent, root, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.root = root

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.move_var = tk.BooleanVar(value=False)
        self._label_to_granularity = {label: key for key, label in GRANULARITY_LABELS.items()}
        self.granularity_var = tk.StringVar(value=GRANULARITY_LABELS[DEFAULT_GRANULARITY])
        self._move_locked = False
        self._move_value_before_lock = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(header, text="Trier par date", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=APP_THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(header, text="Classe les photos et vidéos par date de prise de vue, selon la granularité choisie.",
                     text_color=APP_THEME["subtext"]).pack(anchor="w")

        form = ctk.CTkFrame(self, fg_color=APP_THEME["bg_secondary"], corner_radius=10)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)

        folder_picker_row(form, "Dossier source (photos en vrac)", self.source_var, row=0)
        folder_picker_row(form, "Dossier destination (bibliothèque triée)", self.dest_var, row=1)

        granularity_frame = ctk.CTkFrame(form, fg_color="transparent")
        granularity_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 4))
        ctk.CTkLabel(granularity_frame, text="Granularité du tri :").pack(side="left", padx=(0, 12))
        ctk.CTkOptionMenu(granularity_frame, variable=self.granularity_var,
                          values=list(GRANULARITY_LABELS.values())).pack(side="left")

        self.move_checkbox = ctk.CTkCheckBox(form, text=_MOVE_TEXT_NORMAL, variable=self.move_var)
        self.move_checkbox.grid(row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 16))

        self.toolbar = Toolbar(self)
        self.toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.toolbar.add_button("sort", "Lancer le tri", self._run_sort)

        self.notification = NotificationBanner(self)
        self.notification.grid(row=3, column=0, sticky="ew")
        self.notification.grid_remove()

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=4, column=0, sticky="ew", pady=(0, 12))

        self.results = ResultList(self)
        self.results.grid(row=5, column=0, sticky="nsew")

        self.source_var.trace_add("write", lambda *_: self._on_folders_changed())
        self.dest_var.trace_add("write", lambda *_: self._on_folders_changed())

    def _on_folders_changed(self):
        """
        Force et verrouille "Déplacer" quand source == destination : copier laisserait
        l'original en place, et une ré-analyse ultérieure le recopierait indéfiniment
        (suffixes (1), (2)... à chaque lancement) puisque l'original resterait mal classé.
        """
        source = self.source_var.get()
        dest = self.dest_var.get()
        same = bool(source) and bool(dest) and os.path.abspath(source) == os.path.abspath(dest)

        if same and not self._move_locked:
            self._move_value_before_lock = self.move_var.get()
            self.move_var.set(True)
            self.move_checkbox.configure(state="disabled", text=_MOVE_TEXT_LOCKED)
            self._move_locked = True
        elif not same and self._move_locked:
            self.move_var.set(self._move_value_before_lock)
            self.move_checkbox.configure(state="normal", text=_MOVE_TEXT_NORMAL)
            self._move_locked = False

    def _run_sort(self):
        source = self.source_var.get()
        dest = self.dest_var.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("Erreur", "Choisis un dossier source valide.")
            return
        if not dest:
            messagebox.showerror("Erreur", "Choisis un dossier de destination.")
            return

        move_files = self.move_var.get()
        granularity = self._label_to_granularity[self.granularity_var.get()]

        self.results.clear()
        self.notification.hide()
        self.progress.set(0)
        self.toolbar.set_enabled("sort", False)

        def on_progress(current, total):
            fraction = current / total if total else 0
            self.root.after(0, lambda: self.progress.set(fraction))

        def on_log(message):
            self.root.after(0, lambda: self.results.add_line(message))

        def worker():
            _, errors = sort_by_date(source, dest, move_files=move_files, granularity=granularity,
                                      progress_callback=on_progress, log_callback=on_log)

            def _finish():
                self.toolbar.set_enabled("sort", True)
                if errors:
                    self.notification.show(f"Tri terminé avec {errors} erreur(s) — voir le détail ci-dessous.", "error")
                else:
                    self.notification.show("Tri terminé avec succès.", "success")
            self.root.after(0, _finish)

        threading.Thread(target=worker, daemon=True).start()
