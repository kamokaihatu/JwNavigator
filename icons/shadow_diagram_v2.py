"""
JwNavigator Icon Library

Icon : 日影図 (C071)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+15.5, y+3.5, x+20.5, y+8.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+14, y+6, x+12, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15.5, y+9, x+14, y+10.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+18, y+10, x+18, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+20, x+22, y+20,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+20, x+9, y+10,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+9, y+20, x+2, y+20, x+2, y+18.5, x+9, y+18.5,
        fill="black", outline=""
    )
