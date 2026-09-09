"""
JwNavigator Icon Library

Icon : 消しゴム (G94)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+15, x+13, y+5, x+21, y+13, x+11, y+23,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+11, x+15, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+22, x+10, y+22,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
