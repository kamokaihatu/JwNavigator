"""
JwNavigator Icon Library

Icon : カレンダー (G28)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+5, x+21, y+21,
        outline="black", width=2
    )

    canvas.create_line(
        x+3, y+10, x+21, y+10,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+3, x+8, y+7,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+3, x+16, y+7,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+7, y+13, x+10, y+16,
        fill="black", outline=""
    )
