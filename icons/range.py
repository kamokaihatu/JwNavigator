"""
JwNavigator Icon Library

Icon : 範囲選択
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+4, x+17, y+17,
        outline="black", width=1, dash=(2,2)
    )

    canvas.create_polygon(
        x+15,y+15, x+22,y+17, x+19,y+19, x+17,y+22,
        fill="black"
    )

    canvas.create_line(
        x+19,y+19, x+22,y+22,
        width=1
    )
