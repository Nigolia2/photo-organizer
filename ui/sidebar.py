"""
sidebar.py — Barre de navigation latérale (sections "Trier par date" / "Doublons").
"""
import customtkinter as ctk

from core.theme import APP_THEME


class Sidebar(ctk.CTkFrame):
    """
    Liste de boutons de navigation verticaux. Appelle on_select(key) quand
    l'utilisateur choisit une section, et met en évidence la section active.
    """

    def __init__(self, parent, items, on_select, **kwargs):
        """items : liste de tuples (key, label, icone_texte)."""
        super().__init__(parent, corner_radius=0, fg_color=APP_THEME["sidebar"], **kwargs)
        self._on_select = on_select
        self._buttons = {}
        self._active_key = None

        ctk.CTkLabel(
            self, text="Photo Organizer", font=ctk.CTkFont(size=15, weight="bold"),
            text_color=APP_THEME["blue"], anchor="w"
        ).pack(fill="x", padx=16, pady=(20, 4))
        ctk.CTkLabel(
            self, text="Bibliothèque locale", font=ctk.CTkFont(size=11),
            text_color=APP_THEME["subtext"], anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 20))

        for key, label, icon in items:
            btn = ctk.CTkButton(
                self, text=f"{icon}  {label}", anchor="w", corner_radius=8,
                fg_color="transparent", text_color=APP_THEME["subtext"],
                hover_color=APP_THEME["gray5"], font=ctk.CTkFont(size=13),
                command=lambda k=key: self.select(k),
            )
            btn.pack(fill="x", padx=12, pady=4)
            self._buttons[key] = btn

        if items:
            self.select(items[0][0], fire_callback=False)

    def select(self, key, fire_callback=True):
        """Active la section `key` visuellement, et appelle on_select(key) si demandé."""
        if key == self._active_key:
            return
        for btn_key, btn in self._buttons.items():
            if btn_key == key:
                btn.configure(fg_color=APP_THEME["blue"], text_color=APP_THEME["on_accent"])
            else:
                btn.configure(fg_color="transparent", text_color=APP_THEME["subtext"])
        self._active_key = key
        if fire_callback:
            self._on_select(key)
