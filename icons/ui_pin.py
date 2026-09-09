"""
JwNavigator Icon Library

Icon : ピン (G24)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+8, y+3, x+16, y+3, x+15, y+10, x+19, y+14, x+5, y+14, x+9, y+10,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+14, x+12, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
