"""
JwNavigator Icon Library

Icon : 新規 (C039)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+6, y+3, x+14, y+3, x+18, y+7, x+18, y+21, x+6, y+21, x+6, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14, y+3, x+14, y+7, x+18, y+7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+9, x+12, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+13, x+16, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
