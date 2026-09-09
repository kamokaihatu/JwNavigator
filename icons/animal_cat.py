"""
JwNavigator Icon Library

Icon : 猫 (G106)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+5, x+20, y+21,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+5, y+9, x+5, y+2, x+10, y+6,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+19, y+9, x+19, y+2, x+14, y+6,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+7.7, y+10.7, x+10.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+13.7, y+10.7, x+16.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_line(
        x+2, y+14, x+7, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+17, x+7, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+22, y+14, x+17, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+22, y+17, x+17, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+11, y+14.5, x+13, y+16.5,
        fill="black", outline=""
    )
