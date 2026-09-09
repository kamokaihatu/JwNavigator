"""
JwNavigator Icon Library

Icon : 線長 (C053)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+15, x+21, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+1.5, y+13.5, x+4.5, y+16.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+19.5, y+13.5, x+22.5, y+16.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+8, x+5, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+3, y+8, x+5.5, y+6.5, x+5.5, y+9.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+8, x+19, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+21, y+8, x+18.5, y+9.5, x+18.5, y+6.5,
        fill="black", outline=""
    )
