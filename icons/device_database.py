"""
JwNavigator Icon Library

Icon : データベース (G101)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+2, x+20, y+8,
        outline="black", width=2
    )

    canvas.create_line(
        x+4, y+5, x+4, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+20, y+5, x+20, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+4, y+16, x+20, y+22,
        start=180, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+4, y+9, x+20, y+15,
        start=180, extent=180,
        style=tk.ARC, outline="black", width=2
    )
