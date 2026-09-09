"""
JwNavigator Icon Library

Icon : パラメ (C066)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+5, x+20, y+19,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_rectangle(
        x+4, y+5, x+13, y+19,
        outline="black", width=2
    )

    canvas.create_line(
        x+15, y+12, x+18, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+20, y+12, x+17.5, y+13.5, x+17.5, y+10.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+18, y+12, x+15, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+13, y+12, x+15.5, y+10.5, x+15.5, y+13.5,
        fill="black", outline=""
    )
