"""
JwNavigator Icon Library

Icon : バーコード (G104)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+4, x+22, y+20,
        outline="black", width=1
    )

    canvas.create_rectangle(
        x+4, y+6, x+5.5, y+18,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+7, y+6, x+8, y+18,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+9.5, y+6, x+11.5, y+18,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+13, y+6, x+14, y+18,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15.5, y+6, x+17, y+18,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+18.5, y+6, x+20, y+18,
        fill="black", outline=""
    )
