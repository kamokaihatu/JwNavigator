"""
JwNavigator Icon Library

Icon : 地球 (G70)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+2, x+22, y+22,
        outline="black", width=2
    )

    canvas.create_oval(
        x+8, y+2, x+16, y+22,
        outline="black", width=1
    )

    canvas.create_line(
        x+2, y+12, x+22, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3.5, y+7, x+20.5, y+7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3.5, y+17, x+20.5, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
