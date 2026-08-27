"""
JwNavigator Icon Library

Icon : 2線
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4,y+20, x+14,y+4,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9,y+20, x+19,y+4,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
