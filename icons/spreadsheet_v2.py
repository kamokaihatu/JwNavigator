"""
JwNavigator Icon Library

Icon : 表計算 (C063)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+4, x+21, y+20,
        outline="black", width=2
    )

    canvas.create_line(
        x+9, y+4, x+9, y+20,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+4, x+15, y+20,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+9.3, x+21, y+9.3,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+14.6, x+21, y+14.6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+15.5, y+15, x+20.5, y+19.5,
        fill="black", outline=""
    )
