"""
JwNavigator Icon Library

Icon : 電車 (G144)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+2, x+20, y+17,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+6.5, y+5, x+17.5, y+10,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+6.7, y+12.2, x+9.3, y+14.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+14.7, y+12.2, x+17.3, y+14.8,
        fill="black", outline=""
    )

    canvas.create_line(
        x+8, y+17, x+5, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+17, x+19, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+22, x+22, y+22,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
