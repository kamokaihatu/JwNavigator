"""
JwNavigator Icon Library

Icon : 気球 (G146)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+5, y+2, x+19, y+16,
        outline="black", width=2
    )

    canvas.create_line(
        x+6, y+13, x+9, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+18, y+13, x+15, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+9, y+19, x+15, y+22,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+2, x+12, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+3, x+9, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+3, x+15, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
