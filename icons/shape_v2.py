"""
JwNavigator Icon Library

Icon : 図形 (C057)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+6, x+9, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+12, x+9, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+18, x+9, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+12, x+11, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+13, y+12, x+10.5, y+13.5, x+10.5, y+10.5,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+14, y+11.05, x+18, y+7, x+22, y+11.05,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15, y+11.05, x+21, y+16,
        fill="black", outline=""
    )
