"""
JwNavigator Icon Library

Icon : 図登録 (C058)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+2, y+11.05, x+6, y+7, x+10, y+11.05,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+3, y+11.05, x+9, y+16,
        fill="black", outline=""
    )

    canvas.create_line(
        x+11, y+12, x+12, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+14, y+12, x+11.5, y+13.5, x+11.5, y+10.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+15, y+6, x+21, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+12, x+21, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+18, x+21, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
