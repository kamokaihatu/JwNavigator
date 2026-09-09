"""
JwNavigator Icon Library

Icon : 複写 (B09)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+10, x+11, y+21,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+13, y+3, x+22, y+14,
        outline="black", width=2
    )

    canvas.create_line(
        x+9, y+12, x+13.59, y+7.41,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+15, y+6, x+14.29, y+8.83, x+12.17, y+6.71,
        fill="black", outline=""
    )
