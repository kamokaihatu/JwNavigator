"""
JwNavigator Icon Library

Icon : X軸角 (C051)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+18, x+19.6, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+22, y+18, x+19, y+19.8, x+19, y+16.2,
        fill="black", outline=""
    )

    canvas.create_line(
        x+5, y+18, x+19, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+-1, y+12, x+11, y+24,
        start=0, extent=40,
        style=tk.ARC, outline="black", width=1
    )
