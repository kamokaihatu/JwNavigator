"""
JwNavigator Icon Library

Icon : 座標 (C060)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+21, x+4, y+5.4,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+4, y+3, x+5.8, y+6, x+2.2, y+6,
        fill="black", outline=""
    )

    canvas.create_line(
        x+4, y+21, x+19.6, y+21,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+22, y+21, x+19, y+22.8, x+19, y+19.2,
        fill="black", outline=""
    )

    canvas.create_line(
        x+15, y+21, x+15, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_line(
        x+4, y+9, x+15, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_oval(
        x+13.5, y+7.5, x+16.5, y+10.5,
        fill="black", outline=""
    )
