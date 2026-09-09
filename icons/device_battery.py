"""
JwNavigator Icon Library

Icon : 電池 (G59)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+7, x+19, y+17,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+19, y+10, x+22, y+14,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+4.5, y+9.5, x+8, y+14.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+9.5, y+9.5, x+13, y+14.5,
        fill="black", outline=""
    )
