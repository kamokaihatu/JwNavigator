"""
JwNavigator Icon Library

Icon : 花 (G148)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+9, y+9, x+15, y+15,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+15, y+9, x+21, y+15,
        outline="black", width=2
    )

    canvas.create_oval(
        x+12, y+14.2, x+18, y+20.2,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6, y+14.2, x+12, y+20.2,
        outline="black", width=2
    )

    canvas.create_oval(
        x+3, y+9, x+9, y+15,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6, y+3.8, x+12, y+9.8,
        outline="black", width=2
    )

    canvas.create_oval(
        x+12, y+3.8, x+18, y+9.8,
        outline="black", width=2
    )

    canvas.create_line(
        x+12, y+15, x+12, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
