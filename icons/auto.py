"""
JwNavigator Icon Library

Icon : AUTO
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+5.49, y+4, x+18.49, y+17,
        start=89.9, extent=-315.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_polygon(
        x+8.5,y+3, x+7.5,y+6.5, x+11,y+7.5,
        fill="black"
    )

    canvas.create_oval(
        x+10.9, y+10.9, x+13.1, y+13.1,
        fill="black", outline=""
    )
