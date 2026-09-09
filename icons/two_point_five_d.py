"""
JwNavigator Icon Library

Icon : 25D (C070)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+4, y+9, x+12, y+5, x+20, y+9, x+12, y+13,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+9, x+4, y+17, x+12, y+21, x+20, y+17, x+20, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+13, x+12, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
