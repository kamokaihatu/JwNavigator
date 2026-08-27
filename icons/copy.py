"""
JwNavigator Icon Library

Icon : 複写
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+11, x+13, y+21,
        outline="black", width=1
    )

    canvas.create_rectangle(
        x+10, y+4, x+20, y+14,
        outline="black", width=1
    )

    canvas.create_line(
        x+8,y+16, x+15,y+9,
        width=1
    )

    canvas.create_polygon(
        x+11,y+8, x+16,y+8, x+16,y+13,
        fill="black"
    )
