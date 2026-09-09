"""
JwNavigator Icon Library

Icon : メモ (G29)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+5, y+3, x+19, y+3, x+19, y+21, x+5, y+21, x+5, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+8, x+16, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+12, x+16, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+16, x+13, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
