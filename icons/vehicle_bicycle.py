"""
JwNavigator Icon Library

Icon : 自転車 (G140)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+1, y+11, x+11, y+21,
        outline="black", width=2
    )

    canvas.create_oval(
        x+13, y+11, x+23, y+21,
        outline="black", width=2
    )

    canvas.create_line(
        x+6, y+16, x+10, y+8, x+16, y+8, x+18, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+8, x+12, y+16, x+6, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+8, x+16, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+5, x+11, y+5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
