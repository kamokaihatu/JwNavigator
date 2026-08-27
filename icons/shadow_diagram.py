"""
JwNavigator Icon Library

Icon : 日影図
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+3, x+10, y+9,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+7,y+1, x+7,y+2.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3,y+2, x+4,y+3.25,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2,y+6, x+3.5,y+6,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3,y+20, x+21,y+20,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7,y+20, x+13,y+10, x+17,y+20,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
