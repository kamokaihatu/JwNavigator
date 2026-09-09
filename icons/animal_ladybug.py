"""
JwNavigator Icon Library

Icon : てんとう虫 (G118)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3.5, y+4.5, x+20.5, y+21.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+9, y+2.5, x+15, y+8.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+8, x+12, y+21.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+6.6, y+9.6, x+9.4, y+12.4,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+14.6, y+9.6, x+17.4, y+12.4,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+7.6, y+15.6, x+10.4, y+18.4,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+13.6, y+15.6, x+16.4, y+18.4,
        fill="black", outline=""
    )
