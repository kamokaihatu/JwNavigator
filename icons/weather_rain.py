"""
JwNavigator Icon Library

Icon : 雨 (G64)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+4, x+13, y+14,
        start=90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+7, y+2, x+17, y+12,
        start=20, extent=160,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+13, y+5, x+21, y+13,
        start=-60, extent=200,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+8, y+13, x+17, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+16, x+7, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+16, x+11, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+16, x+15, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
