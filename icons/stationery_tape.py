"""
JwNavigator Icon Library

Icon : テープ (G124)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+3, x+20, y+21,
        outline="black", width=2
    )

    canvas.create_oval(
        x+7.5, y+8.5, x+14.5, y+15.5,
        outline="black", width=2
    )

    canvas.create_line(
        x+17, y+18, x+23, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+20, y+16, x+23, y+18, x+20, y+20,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
