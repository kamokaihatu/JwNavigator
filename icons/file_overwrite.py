"""
JwNavigator Icon Library

Icon : 上書
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+4, y+3, x+20, y+21,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+7,y+3, x+7,y+9, x+16,y+9, x+16,y+3,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+7.5, y+13, x+16.5, y+19,
        outline="black", width=1.7
    )
