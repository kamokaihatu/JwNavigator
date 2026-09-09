"""
JwNavigator Icon Library

Icon : ロケット (G143)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+12, y+2, x+16, y+7, x+16, y+16, x+8, y+16, x+8, y+7, x+12, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10, y+8, x+14, y+12,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+8, y+12, x+4, y+17, x+8, y+17,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+16, y+12, x+20, y+17, x+16, y+17,
        fill="black", outline=""
    )

    canvas.create_line(
        x+10, y+18, x+12, y+22, x+14, y+18,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
