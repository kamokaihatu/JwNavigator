"""
JwNavigator Icon Library

Icon : アイス (G136)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+6, y+2, x+18, y+14,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+6.5, y+10, x+17.5, y+10, x+12, y+22,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+13, x+15, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9.5, y+16.5, x+14, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
