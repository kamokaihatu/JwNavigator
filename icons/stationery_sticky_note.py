"""
JwNavigator Icon Library

Icon : 付箋 (G123)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+3, x+21, y+3, x+21, y+15, x+15, y+21, x+3, y+21, x+3, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+21, x+15, y+15, x+21, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+9, x+17, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+13, x+13, y+13,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
