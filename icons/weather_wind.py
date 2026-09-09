"""
JwNavigator Icon Library

Icon : 風 (G66)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+8, x+14, y+8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+13, y+5, x+19, y+11,
        start=90, extent=-180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+3, y+13, x+18, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+17, y+13, x+22, y+18,
        start=90, extent=-180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+3, y+18, x+11, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
