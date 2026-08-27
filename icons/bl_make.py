"""
JwNavigator Icon Library

Icon : ブロック化
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+3, x+21, y+21,
        outline="black", width=1.7, dash=(4,2)
    )

    canvas.create_rectangle(
        x+6, y+13, x+10.5, y+17.5,
        outline="black", width=1.7
    )

    canvas.create_rectangle(
        x+13, y+13, x+17.5, y+17.5,
        outline="black", width=1.7
    )

    canvas.create_rectangle(
        x+9.5, y+6, x+14, y+10.5,
        outline="black", width=1.7
    )
