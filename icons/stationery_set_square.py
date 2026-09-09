"""
JwNavigator Icon Library

Icon : 三角定規 (G91)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+21, x+21, y+21, x+21, y+3,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+10, y+19, x+19, y+19, x+19, y+10,
        fill="", outline="black", width=1, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+21, x+7, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+21, x+12, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+17, y+21, x+17, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
