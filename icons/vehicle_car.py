"""
JwNavigator Icon Library

Icon : 車 (G139)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+16, x+2, y+10, x+6, y+9, x+8, y+5, x+16, y+5, x+18, y+9, x+22, y+10, x+22, y+16, x+2, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+4, y+14.5, x+9, y+19.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+15, y+14.5, x+20, y+19.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+8, y+9, x+16, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
