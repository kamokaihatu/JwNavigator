"""
JwNavigator Icon Library

Icon : 本 (G125)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+4, x+12, y+7, x+21, y+4, x+21, y+19, x+12, y+22, x+3, y+19, x+3, y+4,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+7, x+12, y+22,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+6, y+9, x+10, y+10.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+6, y+13, x+10, y+14.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
