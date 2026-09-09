"""
JwNavigator Icon Library

Icon : 矩形 (B03)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+5, x+20, y+19,
        outline="black", width=2
    )

    canvas.create_oval(
        x+2.5, y+3.5, x+5.5, y+6.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.5, y+17.5, x+21.5, y+20.5,
        fill="black", outline=""
    )
