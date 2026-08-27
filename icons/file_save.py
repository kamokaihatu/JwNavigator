"""
JwNavigator Icon Library

Icon : 保存
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2.5, y+2, x+15, y+16,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+5,y+2, x+5,y+6, x+12.5,y+6, x+12.5,y+2,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+5.5, y+9, x+12, y+13.5,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+14,y+21, x+19.25,y+15.75, x+21.5,y+13.5, x+22,y+15.75, x+19.75,y+18,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+17.5,y+15.25, x+20.5,y+18.25,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
