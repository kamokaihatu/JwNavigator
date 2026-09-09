"""
JwNavigator Icon Library

Icon : WiFi (G103)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+10, y+17, x+14, y+21,
        fill="black", outline=""
    )

    canvas.create_arc(
        x+7, y+9, x+17, y+19,
        start=30, extent=120,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+3, y+5, x+21, y+23,
        start=30, extent=120,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+-1, y+1, x+25, y+25,
        start=30, extent=120,
        style=tk.ARC, outline="black", width=2
    )
