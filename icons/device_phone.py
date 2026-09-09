"""
JwNavigator Icon Library

Icon : 電話 (G72)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+3, x+21, y+21,
        start=200, extent=140,
        style=tk.ARC, outline="black", width=4
    )

    canvas.create_oval(
        x+0.5, y+12.1, x+6.5, y+18.1,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+17.5, y+12.1, x+23.5, y+18.1,
        fill="black", outline=""
    )
