"""
JwNavigator Icon Library

Icon : 表示 (G20)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+2, y+6, x+22, y+26,
        start=20, extent=140,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+2, y+-2, x+22, y+18,
        start=200, extent=140,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_oval(
        x+9.2, y+9.2, x+14.8, y+14.8,
        fill="black", outline=""
    )
