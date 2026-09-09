"""
JwNavigator Icon Library

Icon : 2点角 (C052)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+17, x+21, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_line(
        x+4, y+17, x+20, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+-2, y+11, x+10, y+23,
        start=0, extent=34,
        style=tk.ARC, outline="black", width=1
    )

    canvas.create_oval(
        x+2.5, y+15.5, x+5.5, y+18.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.5, y+4.5, x+21.5, y+7.5,
        fill="black", outline=""
    )
