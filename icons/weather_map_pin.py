"""
JwNavigator Icon Library

Icon : 地図ピン (G69)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+5, y+2, x+19, y+16,
        start=-30, extent=240,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+6.1, y+12.5, x+12, y+22, x+17.9, y+12.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+9.5, y+6.5, x+14.5, y+11.5,
        outline="black", width=2
    )
