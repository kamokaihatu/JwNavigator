"""
JwNavigator Icon Library

Icon : 雲 (G63)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+10, x+13, y+20,
        start=90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+7, y+5, x+17, y+15,
        start=20, extent=160,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+13, y+9, x+21, y+17,
        start=-60, extent=200,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+8, y+20, x+17, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+9.5, x+8, y+10,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16.5, y+9.5, x+17, y+9.2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
