"""
JwNavigator Icon Library

Icon : ギフト (G155)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+9, x+21, y+21,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+2, y+6, x+22, y+9,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+6, x+12, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+6, y+2, x+12, y+8,
        start=-30, extent=240,
        style=tk.ARC, outline="black", width=1
    )

    canvas.create_arc(
        x+12, y+2, x+18, y+8,
        start=-30, extent=240,
        style=tk.ARC, outline="black", width=1
    )
