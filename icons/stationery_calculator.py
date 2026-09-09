"""
JwNavigator Icon Library

Icon : 電卓 (G126)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+2, x+20, y+22,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+6.5, y+4.5, x+17.5, y+8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+6.7, y+10.7, x+9.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+6.7, y+14.2, x+9.3, y+16.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+6.7, y+17.7, x+9.3, y+20.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.7, y+10.7, x+13.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.7, y+14.2, x+13.3, y+16.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.7, y+17.7, x+13.3, y+20.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+14.7, y+10.7, x+17.3, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+14.7, y+14.2, x+17.3, y+16.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+14.7, y+17.7, x+17.3, y+20.3,
        fill="black", outline=""
    )
