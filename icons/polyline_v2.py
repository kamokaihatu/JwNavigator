"""
JwNavigator Icon Library

Icon : 連続線 (C008)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+19, x+8, y+7, x+13, y+16, x+20, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+1.5, y+17.5, x+4.5, y+20.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+6.5, y+5.5, x+9.5, y+8.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+11.5, y+14.5, x+14.5, y+17.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.5, y+3.5, x+21.5, y+6.5,
        fill="black", outline=""
    )
