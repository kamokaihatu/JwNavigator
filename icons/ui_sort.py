"""
JwNavigator Icon Library

Icon : 並替 (G54)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+8, y+20, x+8, y+6.8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+8, y+4, x+10.1, y+7.5, x+5.9, y+7.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+16, y+4, x+16, y+17.2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+16, y+20, x+13.9, y+16.5, x+18.1, y+16.5,
        fill="black", outline=""
    )
