"""
JwNavigator Icon Library

Icon : 外変 (C061)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+7, x+10, y+17,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+14, y+7, x+22, y+17,
        outline="black", width=2
    )

    canvas.create_line(
        x+16, y+10, x+20, y+10,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+13, x+19, y+13,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+9, x+12, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+14, y+9, x+11.5, y+10.5, x+11.5, y+7.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+14, y+15, x+12, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+10, y+15, x+12.5, y+13.5, x+12.5, y+16.5,
        fill="black", outline=""
    )
