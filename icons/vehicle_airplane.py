"""
JwNavigator Icon Library

Icon : 飛行機 (G141)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+12, x+22, y+12,
        width=3, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+9, y+12, x+13, y+12, x+11, y+2,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+13, y+12, x+17, y+12, x+15, y+20,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+2, y+12, x+4, y+12, x+3, y+8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+19.5, y+10.5, x+22.5, y+13.5,
        fill="black", outline=""
    )
