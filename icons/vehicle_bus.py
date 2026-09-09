"""
JwNavigator Icon Library

Icon : バス (G145)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+4, x+22, y+17,
        outline="black", width=2
    )

    canvas.create_line(
        x+2, y+11, x+22, y+11,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+4, x+8, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+4, x+15, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+4, y+16, x+9, y+21,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+15, y+16, x+20, y+21,
        fill="black", outline=""
    )
