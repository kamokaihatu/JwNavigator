"""
JwNavigator Icon Library

Icon : 中心点
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+5, y+5, x+19, y+19,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+12,y+8, x+12,y+16,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8,y+12, x+16,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
