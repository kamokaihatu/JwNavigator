"""
JwNavigator Icon Library

Icon : 鍵 (G81)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3, y+3, x+13, y+13,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6.4, y+6.4, x+9.6, y+9.6,
        fill="black", outline=""
    )

    canvas.create_line(
        x+11.5, y+11.5, x+21, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+17, y+17, x+20, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+19.5, y+19.5, x+22, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
