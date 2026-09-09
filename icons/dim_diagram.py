"""
JwNavigator Icon Library

Icon : 寸図化 (C067)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+3, x+3, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+21, y+3, x+21, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+6, x+5, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+3, y+6, x+5.5, y+4.5, x+5.5, y+7.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+6, x+19, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+21, y+6, x+18.5, y+7.5, x+18.5, y+4.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+10, x+12, y+12.6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+12, y+15, x+10.2, y+12, x+13.8, y+12,
        fill="black", outline=""
    )

    canvas.create_line(
        x+3, y+19, x+21, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
