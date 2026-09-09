"""
JwNavigator Icon Library

Icon : ハチ (G112)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+5, y+9, x+19, y+19,
        outline="black", width=2
    )

    canvas.create_line(
        x+9.5, y+9.5, x+9.5, y+18.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+13.5, y+9.2, x+13.5, y+18.8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+6, y+2, x+12, y+9,
        outline="black", width=1
    )

    canvas.create_oval(
        x+12, y+2, x+18, y+9,
        outline="black", width=1
    )

    canvas.create_line(
        x+19, y+14, x+23, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
