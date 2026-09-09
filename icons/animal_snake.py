"""
JwNavigator Icon Library

Icon : 蛇 (G114)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+19, x+8, y+21, x+13, y+15, x+10, y+9, x+14, y+4, x+20, y+6,
        width=3, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )

    canvas.create_oval(
        x+19.4, y+4.4, x+22.6, y+7.6,
        fill="black", outline=""
    )
