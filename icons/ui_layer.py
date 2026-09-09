"""
JwNavigator Icon Library

Icon : レイヤ (G19)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+3, x+21, y+8, x+12, y+13, x+3, y+8,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+12, x+12, y+17, x+21, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+16, x+12, y+21, x+21, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
