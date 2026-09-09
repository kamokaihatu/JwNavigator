"""
JwNavigator Icon Library

Icon : 鳥 (G109)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+8, x+18, y+19,
        outline="black", width=2
    )

    canvas.create_oval(
        x+12.5, y+4.5, x+19.5, y+11.5,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+19.5, y+8, x+23, y+9, x+19.5, y+10,
        fill="black", outline=""
    )

    canvas.create_line(
        x+4, y+12, x+1, y+8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+14, x+1, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+19, x+9, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+13, y+19, x+13, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+16.1, y+6.1, x+17.9, y+7.9,
        fill="black", outline=""
    )
