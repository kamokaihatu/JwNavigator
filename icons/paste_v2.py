"""
JwNavigator Icon Library

Icon : 貼付 (C046)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+3, x+10, y+3, x+14, y+7, x+14, y+21, x+2, y+21, x+2, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+3, x+10, y+7, x+14, y+7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+5, y+9, x+11, y+16,
        fill="black", outline=""
    )

    canvas.create_line(
        x+21, y+12, x+16.4, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+14, y+12, x+17, y+10.2, x+17, y+13.8,
        fill="black", outline=""
    )
