"""
JwNavigator Icon Library

Icon : めがね (G130)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+9.5, x+11, y+18.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+13, y+9.5, x+22, y+18.5,
        outline="black", width=2
    )

    canvas.create_line(
        x+11, y+14, x+13, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+14, x+1, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+22, y+14, x+23, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
