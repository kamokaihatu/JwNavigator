"""
JwNavigator Icon Library

Icon : 多角形
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12,y+3, x+21,y+9.5, x+17.5,y+20, x+6.5,y+20, x+3,y+9.5,
        outline="black", fill="", width=1.7, joinstyle=tk.ROUND
    )
