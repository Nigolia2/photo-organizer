"""
theme.py — Applique un thème sombre "Catppuccin Mocha" aux widgets ttk.
"""
from tkinter import ttk

MOCHA = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay": "#6c7086",
    "blue": "#89b4fa",
    "lavender": "#b4befe",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "peach": "#fab387",
    "red": "#f38ba8",
    "mauve": "#cba6f7",
}


def apply_mocha_theme(root):
    """Configure les couleurs et styles ttk pour toute l'application."""
    root.configure(bg=MOCHA["base"])

    style = ttk.Style(root)
    style.theme_use("clam")  # base modifiable, nécessaire pour personnaliser 'clam'

    style.configure(".", background=MOCHA["base"], foreground=MOCHA["text"],
                     fieldbackground=MOCHA["surface0"], bordercolor=MOCHA["surface1"],
                     font=("Segoe UI", 10))

    style.configure("TFrame", background=MOCHA["base"])
    style.configure("TLabel", background=MOCHA["base"], foreground=MOCHA["text"])
    style.configure("Title.TLabel", background=MOCHA["base"], foreground=MOCHA["mauve"],
                     font=("Segoe UI", 14, "bold"))
    style.configure("Subtext.TLabel", background=MOCHA["base"], foreground=MOCHA["subtext"])

    style.configure("TButton", background=MOCHA["mauve"], foreground=MOCHA["crust"],
                     borderwidth=0, focusthickness=0, padding=8, font=("Segoe UI", 10, "bold"))
    style.map("TButton",
              background=[("active", MOCHA["lavender"]), ("disabled", MOCHA["surface2"])],
              foreground=[("disabled", MOCHA["overlay"])])

    style.configure("Secondary.TButton", background=MOCHA["surface1"], foreground=MOCHA["text"],
                     borderwidth=0, padding=8)
    style.map("Secondary.TButton", background=[("active", MOCHA["surface2"])])

    style.configure("TEntry", fieldbackground=MOCHA["surface0"], foreground=MOCHA["text"],
                     insertcolor=MOCHA["text"], bordercolor=MOCHA["surface1"])

    style.configure("TNotebook", background=MOCHA["base"], borderwidth=0)
    style.configure("TNotebook.Tab", background=MOCHA["mantle"], foreground=MOCHA["subtext"],
                     padding=(16, 8), font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", MOCHA["surface0"])],
              foreground=[("selected", MOCHA["mauve"])])

    style.configure("TProgressbar", background=MOCHA["green"], troughcolor=MOCHA["surface0"],
                     borderwidth=0, thickness=14)

    style.configure("TCheckbutton", background=MOCHA["base"], foreground=MOCHA["text"])
    style.map("TCheckbutton", background=[("active", MOCHA["base"])])

    style.configure("TRadiobutton", background=MOCHA["base"], foreground=MOCHA["text"])
    style.map("TRadiobutton", background=[("active", MOCHA["base"])])

    style.configure("TLabelframe", background=MOCHA["base"], foreground=MOCHA["text"],
                     bordercolor=MOCHA["surface1"])
    style.configure("TLabelframe.Label", background=MOCHA["base"], foreground=MOCHA["lavender"],
                     font=("Segoe UI", 10, "bold"))

    return style
