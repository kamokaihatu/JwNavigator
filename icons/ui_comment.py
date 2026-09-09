"""
JwNavigator Icon Library

Icon : コメント (G48)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+4, x+21, y+4, x+21, y+16, x+10, y+16, x+5, y+21, x+5, y+16, x+3, y+16, x+3, y+4,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+9, x+17, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+12, x+14, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
