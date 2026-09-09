"""
JwNavigator Icon Library

Icon : 曲線 (C019)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+18, x+8, y+4, x+16, y+20, x+21, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )

    canvas.create_oval(
        x+1.5, y+16.5, x+4.5, y+19.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+6.5, y+2.5, x+9.5, y+5.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+14.5, y+18.5, x+17.5, y+21.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+19.5, y+4.5, x+22.5, y+7.5,
        fill="black", outline=""
    )
