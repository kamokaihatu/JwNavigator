"""
JwNavigator Icon Library

Icon : 建物 (G86)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+3, x+20, y+21,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+7, y+6, x+9.5, y+8.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+7, y+10.5, x+9.5, y+13,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+11, y+6, x+13.5, y+8.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+11, y+10.5, x+13.5, y+13,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15, y+6, x+17.5, y+8.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15, y+10.5, x+17.5, y+13,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+10, y+16, x+14, y+21,
        fill="black", outline=""
    )
