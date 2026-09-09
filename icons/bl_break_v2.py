"""
JwNavigator Icon Library

Icon : ブロック解除 (B06)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+7, x+3, y+3, x+7, y+3,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+17, y+3, x+21, y+3, x+21, y+7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+17, x+3, y+21, x+7, y+21,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+21, y+17, x+21, y+21, x+17, y+21,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+7, y+7, x+11, y+11,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+14, y+6, x+19, y+10,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+9, y+14, x+16, y+18,
        fill="black", outline=""
    )
