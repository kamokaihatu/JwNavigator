"""
JwNavigator Icon Library

Icon : Rectangle
Size : 24×24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+5,
        y+5,
        x+19,
        y+19,
        outline="black",
        width=2
    )