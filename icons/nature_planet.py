"""
JwNavigator Icon Library

Icon : 惑星 (G152)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+6, y+6, x+18, y+18,
        outline="black", width=2
    )

    canvas.create_oval(
        x+1, y+9, x+23, y+15,
        outline="black", width=1
    )

    canvas.create_arc(
        x+6, y+6, x+18, y+18,
        start=40, extent=30,
        style=tk.ARC, outline="black", width=1
    )
