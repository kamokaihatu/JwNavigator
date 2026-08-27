"""
JwNavigator Icon Library

Icon : 図形
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+4, x+12, y+12,
        outline="black", width=1.7
    )

    canvas.create_rectangle(
        x+13, y+13, x+21, y+21,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+5,y+20, x+10,y+15, x+14,y+20,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
