"""
JwNavigator Icon Library

Icon : コンパス (G92)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+10.2, y+2.2, x+13.8, y+5.8,
        outline="black", width=2
    )

    canvas.create_line(
        x+11, y+6, x+4, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+13, y+6, x+20, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+5, y+9, x+19, y+23,
        start=200, extent=140,
        style=tk.ARC, outline="black", width=1, dash=(2, 2)
    )
