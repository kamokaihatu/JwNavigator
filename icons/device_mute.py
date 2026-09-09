"""
JwNavigator Icon Library

Icon : ミュート (G77)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+9, x+7, y+9, x+12, y+4, x+12, y+20, x+7, y+15, x+3, y+15,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+9, x+21, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+21, y+9, x+15, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
