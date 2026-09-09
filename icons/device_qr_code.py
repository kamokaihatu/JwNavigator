"""
JwNavigator Icon Library

Icon : QRコード (G105)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+2, x+10, y+10,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+4.5, y+4.5, x+7.5, y+7.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+14, y+2, x+22, y+10,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+16.5, y+4.5, x+19.5, y+7.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+2, y+14, x+10, y+22,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+4.5, y+16.5, x+7.5, y+19.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+14, y+14, x+17, y+17,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+19, y+14, x+22, y+17,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+14, y+19, x+17, y+22,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+19, y+19, x+22, y+22,
        fill="black", outline=""
    )
