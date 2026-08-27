"""
JwNavigator Icon Library

Icon : 寸法
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4,y+4, x+4,y+20,
        width=1
    )

    canvas.create_line(
        x+20,y+4, x+20,y+20,
        width=1
    )

    canvas.create_line(
        x+4,y+12, x+20,y+12,
        width=2
    )

    canvas.create_line(
        x+8,y+8, x+4,y+12, x+8,y+16,
        width=1
    )

    canvas.create_line(
        x+16,y+8, x+20,y+12, x+16,y+16,
        width=1
    )
