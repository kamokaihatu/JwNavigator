"""
JwNavigator Icon Library

Icon : 面取
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+6,y+20, x+6,y+13, x+13,y+6, x+20,y+6,
        width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
