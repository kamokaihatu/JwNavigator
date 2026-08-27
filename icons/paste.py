"""
JwNavigator Icon Library

Icon : 貼付
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+5, y+5, x+19, y+22,
        outline="black", width=1.7
    )

    canvas.create_rectangle(
        x+9, y+3, x+15, y+7,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+8,y+11, x+16,y+11,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8,y+15, x+16,y+15,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8,y+19, x+13,y+19,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
