"""
JwNavigator Icon Library

Icon : 切取
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3.5, y+15.5, x+8.5, y+20.5,
        outline="black", width=1.7
    )

    canvas.create_oval(
        x+3.5, y+3.5, x+8.5, y+8.5,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+8,y+7.5, x+20,y+19.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8,y+16.5, x+20,y+4.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
