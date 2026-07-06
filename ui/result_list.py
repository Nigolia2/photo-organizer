"""
result_list.py — Liste structurée des résultats de traitement (une ligne par fichier).
"""
import customtkinter as ctk

from core.theme import APP_THEME, MONO_FONT


def _classify(message: str):
    """Détermine l'icône et la couleur d'une ligne de log selon son contenu."""
    stripped = message.strip()
    if "ERREUR" in stripped:
        return "✗", APP_THEME["red"]
    if stripped.startswith("OK"):
        return "✓", APP_THEME["green"]
    if stripped.startswith("SKIP"):
        return "↷", APP_THEME["orange"]
    if stripped.startswith("Conservé"):
        return "★", APP_THEME["purple"]
    if stripped.startswith("->") or "Archivé" in stripped:
        return "↳", APP_THEME["green"]
    return "•", APP_THEME["subtext"]


class ResultList(ctk.CTkScrollableFrame):
    """Zone défilante affichant une ligne par fichier traité, avec statut coloré."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=APP_THEME["bg_secondary"], **kwargs)
        self._rows = []

    def clear(self):
        """Vide la liste avant un nouveau traitement."""
        for row in self._rows:
            row.destroy()
        self._rows = []

    def add_line(self, message: str):
        """Ajoute une ligne de résultat, en la classant visuellement selon son contenu."""
        icon, color = _classify(message)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=1)

        ctk.CTkLabel(row, text=icon, text_color=color, width=22,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkLabel(row, text=message.strip(), text_color=APP_THEME["text"], anchor="w",
                     justify="left", font=MONO_FONT).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._rows.append(row)
        self.after(10, lambda: self._parent_canvas.yview_moveto(1.0))
