"""
JwNavigator Icon Library

Icon : キーボード (G44)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+7, x+22, y+18,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+4.5, y+9.5, x+6.5, y+11.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+8, y+9.5, x+10, y+11.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+11.5, y+9.5, x+13.5, y+11.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15, y+9.5, x+17, y+11.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+18.5, y+9.5, x+20.5, y+11.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+7, y+13.5, x+17, y+15.5,
        fill="black", outline=""
    )
