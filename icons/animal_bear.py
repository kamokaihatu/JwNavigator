"""
JwNavigator Icon Library

Icon : 熊 (G115)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+5, x+20, y+21,
        outline="black", width=2
    )

    canvas.create_oval(
        x+3, y+3, x+9, y+9,
        outline="black", width=2
    )

    canvas.create_oval(
        x+15, y+3, x+21, y+9,
        outline="black", width=2
    )

    canvas.create_oval(
        x+7.7, y+10.7, x+10.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+13.7, y+10.7, x+16.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+9, y+14, x+15, y+18,
        outline="black", width=1
    )

    canvas.create_oval(
        x+11, y+14, x+13, y+16,
        fill="black", outline=""
    )
