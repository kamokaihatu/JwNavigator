"""
JwNavigator Icon Library

Icon : 折れ線 (G99)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+21, x+2, y+3,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+21, x+22, y+21,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+17, x+9, y+10, x+13, y+14, x+20, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+2.5, y+15.5, x+5.5, y+18.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+7.5, y+8.5, x+10.5, y+11.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+11.5, y+12.5, x+14.5, y+15.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.5, y+3.5, x+21.5, y+6.5,
        fill="black", outline=""
    )
