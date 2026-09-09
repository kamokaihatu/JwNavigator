"""
JwNavigator Icon Library

Icon : 葉 (G149)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+20, x+3, y+10, x+10, y+3, x+20, y+4, x+21, y+14, x+14, y+21, x+4, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )

    canvas.create_line(
        x+4, y+20, x+18, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+15, x+6, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+13, y+11, x+10, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
