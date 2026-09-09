"""
JwNavigator Icon Library

Icon : ハサミ (G119)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2.5, y+13.5, x+9.5, y+20.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+2.5, y+3.5, x+9.5, y+10.5,
        outline="black", width=2
    )

    canvas.create_line(
        x+8.5, y+15, x+21, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8.5, y+9, x+21, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
