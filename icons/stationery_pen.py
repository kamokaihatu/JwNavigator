"""
JwNavigator Icon Library

Icon : ペン (G95)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+21, x+15, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+15, y+9, x+19, y+5, x+21, y+7, x+17, y+11,
        fill="black", outline=""
    )

    canvas.create_line(
        x+3, y+21, x+6, y+20.5, x+4.5, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
