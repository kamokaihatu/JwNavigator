"""
JwNavigator Icon Library

Icon : おにぎり (G132)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+3, x+22, y+20, x+2, y+20,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+8, y+13, x+16, y+20,
        fill="black", outline=""
    )
