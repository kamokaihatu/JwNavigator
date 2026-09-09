"""
JwNavigator Icon Library

Icon : 多角形 (C017)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+3.5, x+20.56, y+9.72, x+17.29, y+19.78, x+6.71, y+19.78, x+3.44, y+9.72,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10.5, y+2, x+13.5, y+5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+19.06, y+8.22, x+22.06, y+11.22,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+15.79, y+18.28, x+18.79, y+21.28,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+5.21, y+18.28, x+8.21, y+21.28,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+1.94, y+8.22, x+4.94, y+11.22,
        fill="black", outline=""
    )
