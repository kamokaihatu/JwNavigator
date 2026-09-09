"""
JwNavigator Icon Library

Icon : カメラ (G73)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+7, x+22, y+19,
        outline="black", width=2
    )

    canvas.create_line(
        x+8, y+7, x+9.5, y+4, x+14.5, y+4, x+16, y+7,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+8.5, y+9.5, x+15.5, y+16.5,
        outline="black", width=2
    )
