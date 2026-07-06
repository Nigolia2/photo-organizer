"""
toolbar.py — Barre d'outils horizontale portant les actions principales d'une vue.
"""
import customtkinter as ctk

from core.theme import APP_THEME


class Toolbar(ctk.CTkFrame):
    """Rangée de boutons d'action, ajoutés à la demande par la vue qui l'utilise."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._buttons = {}

    def add_button(self, key, text, command, primary=True):
        """Ajoute un bouton d'action identifié par `key`, dans l'ordre d'appel."""
        style = {} if primary else {
            "fg_color": APP_THEME["gray5"], "hover_color": APP_THEME["gray4"],
            "text_color": APP_THEME["text"],
        }
        btn = ctk.CTkButton(self, text=text, command=command, height=36, **style)
        btn.pack(side="left", padx=(0, 8), fill="x", expand=True)
        self._buttons[key] = btn
        return btn

    def set_enabled(self, key, enabled: bool):
        """Active/désactive le bouton `key`."""
        self._buttons[key].configure(state="normal" if enabled else "disabled")
