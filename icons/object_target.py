"""
JwNavigator Icon Library

Icon : ターゲット (G82)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+2, x+22, y+22,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6.5, y+6.5, x+17.5, y+17.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+10.2, y+10.2, x+13.8, y+13.8,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+1, x+12, y+5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+19, x+12, y+23,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+1, y+12, x+5, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+19, y+12, x+23, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
