"""
JwNavigator Icon Library

Icon : AUTO (C009)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+21, x+11, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+11, y+8, x+21, y+18,
        start=180, extent=-180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_oval(
        x+1.5, y+19.5, x+4.5, y+22.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+9.5, y+11.5, x+12.5, y+14.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+19.5, y+11.5, x+22.5, y+14.5,
        fill="black", outline=""
    )
