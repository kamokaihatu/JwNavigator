"""
JwNavigator Icon Library

Icon : Line
Size : 24×24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+5,
        y+19,
        x+19,
        y+5,
        width=2,
        fill="black",
        capstyle=tk.ROUND
    )