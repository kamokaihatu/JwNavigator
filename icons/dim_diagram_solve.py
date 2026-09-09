"""
JwNavigator Icon Library

Icon : 寸図解 (C068)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+5, x+21, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+8, x+12, y+10.6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+12, y+13, x+10.2, y+10, x+13.8, y+10,
        fill="black", outline=""
    )

    canvas.create_line(
        x+3, y+15, x+3, y+21,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+21, y+15, x+21, y+21,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+18, x+5, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+3, y+18, x+5.5, y+16.5, x+5.5, y+19.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+18, x+19, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+21, y+18, x+18.5, y+19.5, x+18.5, y+16.5,
        fill="black", outline=""
    )
