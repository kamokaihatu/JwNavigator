"""
JwNavigator Icon Library

Icon : SPEED
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+13,y+2, x+5,y+14, x+11,y+14, x+9,y+22, x+19,y+9, x+12.5,y+9,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
