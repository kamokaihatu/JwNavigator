"""
JwNavigator Icon Library

Icon : クレヨン (G129)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+20, x+16, y+8,
        width=4, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+16, y+8, x+18.5, y+5.5, x+20, y+4, x+21, y+5, x+18.5, y+10.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+7, y+17, x+8.5, y+18.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+11, y+13, x+12.5, y+14.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
