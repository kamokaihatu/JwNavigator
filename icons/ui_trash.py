"""
JwNavigator Icon Library

Icon : ゴミ箱 (G52)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+6, x+20, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+6, x+9, y+3, x+15, y+3, x+15, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+6, y+6, x+7, y+21, x+17, y+21, x+18, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+10, x+10, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14, y+10, x+14, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
