#!/usr/bin/env python3
"""
Photo Organizer — Gestionnaire de bibliothèque de photos numériques.
Trie les photos par date (EXIF) et détecte/archive les doublons.
Thème : Catppuccin Mocha.
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

from core.theme import apply_mocha_theme, MOCHA
from core.sorter import sort_by_date
from core.duplicates import find_duplicates, archive_duplicates


class PhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Organizer")
        self.root.geometry("780x620")
        self.root.minsize(680, 520)

        self.style = apply_mocha_theme(root)

        header = ttk.Frame(root, padding=(20, 16, 20, 8))
        header.pack(fill="x")
        ttk.Label(header, text="📷 Photo Organizer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Trie tes photos par date et archive les doublons",
                  style="Subtext.TLabel").pack(anchor="w")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=20, pady=(8, 20))

        self.sort_tab = ttk.Frame(notebook, padding=16)
        self.dup_tab = ttk.Frame(notebook, padding=16)
        notebook.add(self.sort_tab, text="  Trier par date  ")
        notebook.add(self.dup_tab, text="  Doublons  ")

        self._build_sort_tab()
        self._build_dup_tab()

    # ---------- Onglet Tri par date ----------
    def _build_sort_tab(self):
        tab = self.sort_tab

        self.sort_source_var = tk.StringVar()
        self.sort_dest_var = tk.StringVar()
        self.sort_move_var = tk.BooleanVar(value=False)

        self._folder_picker(tab, "Dossier source (photos en vrac)", self.sort_source_var, row=0)
        self._folder_picker(tab, "Dossier destination (bibliothèque triée)", self.sort_dest_var, row=1)

        ttk.Checkbutton(tab, text="Déplacer les fichiers (sinon : copier)",
                         variable=self.sort_move_var).grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 12))

        ttk.Button(tab, text="Lancer le tri", command=self._run_sort).grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        self.sort_progress = ttk.Progressbar(tab, mode="determinate")
        self.sort_progress.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        self.sort_log = scrolledtext.ScrolledText(
            tab, height=16, bg=MOCHA["mantle"], fg=MOCHA["text"],
            insertbackground=MOCHA["text"], borderwidth=0, font=("Consolas", 9))
        self.sort_log.grid(row=5, column=0, columnspan=3, sticky="nsew")

        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(5, weight=1)

    def _run_sort(self):
        source = self.sort_source_var.get()
        dest = self.sort_dest_var.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("Erreur", "Choisis un dossier source valide.")
            return
        if not dest:
            messagebox.showerror("Erreur", "Choisis un dossier de destination.")
            return

        self.sort_log.delete("1.0", tk.END)
        self.sort_progress["value"] = 0

        def worker():
            def on_progress(current, total):
                self.sort_progress["maximum"] = max(total, 1)
                self.sort_progress["value"] = current

            def on_log(message):
                self.sort_log.insert(tk.END, message + "\n")
                self.sort_log.see(tk.END)

            sort_by_date(source, dest, move_files=self.sort_move_var.get(),
                         progress_callback=on_progress, log_callback=on_log)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Onglet Doublons ----------
    def _build_dup_tab(self):
        tab = self.dup_tab

        self.dup_source_var = tk.StringVar()
        self.dup_archive_var = tk.StringVar()
        self.dup_mode_var = tk.StringVar(value="hash")

        self._folder_picker(tab, "Dossier à analyser", self.dup_source_var, row=0)
        self._folder_picker(tab, "Dossier d'archive des doublons", self.dup_archive_var, row=1)

        mode_frame = ttk.Frame(tab)
        mode_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 4))
        ttk.Label(mode_frame, text="Méthode de détection :").pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_frame, text="Contenu identique (fiable)", value="hash",
                         variable=self.dup_mode_var).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_frame, text="Nom + taille (heuristique)", value="name_size",
                         variable=self.dup_mode_var).pack(side="left")

        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 12))
        ttk.Button(btn_frame, text="1. Analyser", command=self._run_scan_duplicates).pack(
            side="left", expand=True, fill="x", padx=(0, 6))
        self.archive_btn = ttk.Button(btn_frame, text="2. Archiver les doublons",
                                       command=self._run_archive_duplicates, state="disabled")
        self.archive_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.dup_progress = ttk.Progressbar(tab, mode="determinate")
        self.dup_progress.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        self.dup_log = scrolledtext.ScrolledText(
            tab, height=14, bg=MOCHA["mantle"], fg=MOCHA["text"],
            insertbackground=MOCHA["text"], borderwidth=0, font=("Consolas", 9))
        self.dup_log.grid(row=5, column=0, columnspan=3, sticky="nsew")

        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(5, weight=1)

        self._duplicate_groups = []

    def _run_scan_duplicates(self):
        source = self.dup_source_var.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("Erreur", "Choisis un dossier valide à analyser.")
            return

        self.dup_log.delete("1.0", tk.END)
        self.dup_progress["value"] = 0
        self.archive_btn.config(state="disabled")

        def worker():
            def on_progress(current, total):
                self.dup_progress["maximum"] = max(total, 1)
                self.dup_progress["value"] = current

            def on_log(message):
                self.dup_log.insert(tk.END, message + "\n")
                self.dup_log.see(tk.END)

            groups = find_duplicates(source, mode=self.dup_mode_var.get(),
                                      progress_callback=on_progress, log_callback=on_log)
            self._duplicate_groups = groups
            if groups:
                self.root.after(0, lambda: self.archive_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _run_archive_duplicates(self):
        archive = self.dup_archive_var.get()
        if not archive:
            messagebox.showerror("Erreur", "Choisis un dossier d'archive.")
            return
        if not self._duplicate_groups:
            messagebox.showinfo("Info", "Aucun doublon détecté. Lance d'abord une analyse.")
            return

        nb = sum(len(g) - 1 for g in self._duplicate_groups)
        if not messagebox.askyesno("Confirmer", f"Déplacer {nb} fichier(s) en double vers {archive} ?"):
            return

        def on_log(message):
            self.dup_log.insert(tk.END, message + "\n")
            self.dup_log.see(tk.END)

        def worker():
            archive_duplicates(self._duplicate_groups, archive, log_callback=on_log)
            self._duplicate_groups = []
            self.root.after(0, lambda: self.archive_btn.config(state="disabled"))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Utilitaire commun ----------
    def _folder_picker(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(parent, text="Parcourir…", style="Secondary.TButton",
                   command=lambda: var.set(filedialog.askdirectory() or var.get())).grid(
            row=row, column=2, pady=4)


def main():
    root = tk.Tk()
    app = PhotoOrganizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
