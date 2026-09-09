"""
JwNavigator Icon Library

Icon : 切取 (C044)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+4, x+11, y+20,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_line(
        x+11, y+12, x+12.6, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+15, y+12, x+12, y+13.8, x+12, y+10.2,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15, y+8, x+22, y+16,
        outline="black", width=2
    )
