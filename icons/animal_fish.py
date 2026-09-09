"""
JwNavigator Icon Library

Icon : 魚 (G110)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3, y+7, x+17, y+17,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+16, y+12, x+22, y+6, x+22, y+18,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+6.3, y+9.8, x+8.7, y+12.2,
        fill="black", outline=""
    )

    canvas.create_line(
        x+11, y+7.5, x+13, y+12, x+11, y+16.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
