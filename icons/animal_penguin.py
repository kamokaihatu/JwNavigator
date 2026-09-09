"""
JwNavigator Icon Library

Icon : ペンギン (G117)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+5, y+2, x+19, y+22,
        outline="black", width=2
    )

    canvas.create_oval(
        x+8, y+9, x+16, y+21,
        outline="black", width=1
    )

    canvas.create_oval(
        x+9, y+5, x+11, y+7,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+13, y+5, x+15, y+7,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+11, y+7.5, x+13, y+7.5, x+12, y+9.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+5, y+10, x+2, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+19, y+10, x+22, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
