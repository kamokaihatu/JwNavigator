"""
JwNavigator Icon Library

Icon : 開く (C040)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+8, x+3, y+5, x+9, y+5, x+11, y+7, x+21, y+7, x+21, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+8, x+5, y+20, x+19, y+20, x+22, y+9, x+5, y+9, x+3, y+8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
