"""
notification.py — Bandeau de notification intégré à la fenêtre (pas de popup bloquante).

Utilisation : le parent place le bandeau une fois avec .grid(...), puis le masque
immédiatement avec .grid_remove(). Un appel à show()/hide() bascule sa visibilité
sans perturber la position des autres widgets.
"""
import customtkinter as ctk

from core.theme import APP_THEME

_KIND_STYLES = {
    "success": (APP_THEME["green"], APP_THEME["on_accent"]),
    "error": (APP_THEME["red"], APP_THEME["on_accent"]),
    "info": (APP_THEME["blue"], APP_THEME["on_accent"]),
}


class NotificationBanner(ctk.CTkFrame):
    """Bandeau coloré (succès/erreur/info) avec bouton de fermeture."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, corner_radius=8, **kwargs)
        self._label = ctk.CTkLabel(self, text="", anchor="w", font=ctk.CTkFont(size=13, weight="bold"))
        self._label.pack(side="left", fill="x", expand=True, padx=(14, 8), pady=10)
        self._close_btn = ctk.CTkButton(
            self, text="✕", width=28, height=28, fg_color="transparent",
            hover_color=APP_THEME["gray"], command=self.hide,
        )
        self._close_btn.pack(side="right", padx=(0, 8), pady=8)

    def show(self, message: str, kind: str = "info"):
        """Affiche le bandeau avec le message donné. kind : 'success' | 'error' | 'info'."""
        bg, fg = _KIND_STYLES.get(kind, _KIND_STYLES["info"])
        self.configure(fg_color=bg)
        self._label.configure(text=message, text_color=fg)
        self._close_btn.configure(text_color=fg)
        self.grid()

    def hide(self):
        """Masque le bandeau (sa place dans la grille est conservée pour le prochain show())."""
        self.grid_remove()
