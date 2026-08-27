"""
JwNavigator Icon Library

Icon : 印刷
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+8,y+8, x+8,y+2.5, x+16,y+2.5, x+16,y+8,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+3.5, y+8, x+20.5, y+16,
        outline="black", width=1.7
    )

    canvas.create_oval(
        x+15.7, y+10.7, x+17.3, y+12.3,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+7, y+13, x+17, y+21.5,
        outline="black", width=1.7
    )
