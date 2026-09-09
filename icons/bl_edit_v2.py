"""
JwNavigator Icon Library

Icon : ブロック編集 (B05)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+3, x+21, y+21,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_rectangle(
        x+6, y+6, x+10, y+10,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+13, y+8, x+18, y+12,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+8, y+13, x+15, y+18,
        outline="black", width=2
    )

    canvas.create_line(
        x+21, y+22, x+17.05, y+18.77,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+15.5, y+17.5, x+18.38, y+17.92, x+16.49, y+20.24,
        fill="black", outline=""
    )
