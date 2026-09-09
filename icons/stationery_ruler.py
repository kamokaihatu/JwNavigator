"""
JwNavigator Icon Library

Icon : 定規 (G121)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+8, x+22, y+16,
        outline="black", width=2
    )

    canvas.create_line(
        x+4, y+8, x+4, y+13,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+8, x+7, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+8, x+10, y+13,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+13, y+8, x+13, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+8, x+16, y+13,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+19, y+8, x+19, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
