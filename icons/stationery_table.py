"""
JwNavigator Icon Library

Icon : 表 (G97)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+4, x+22, y+20,
        outline="black", width=2
    )

    canvas.create_line(
        x+2, y+9, x+22, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+14.5, x+22, y+14.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+4, x+9, y+20,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15.5, y+4, x+15.5, y+20,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
