"""
JwNavigator Icon Library

Icon : 曲線
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3,y+18, x+4.09,y+17.66, x+4.99,y+16.75, x+5.76,y+15.41, x+6.46,y+13.78, x+7.12,y+12, x+7.82,y+10.22, x+8.61,y+8.59, x+9.53,y+7.25, x+10.64,y+6.34, x+12,y+6, x+13.36,y+6.34, x+14.47,y+7.25, x+15.39,y+8.59, x+16.18,y+10.22, x+16.88,y+12, x+17.54,y+13.78, x+18.24,y+15.41, x+19.01,y+16.75, x+19.91,y+17.66, x+21,y+18,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
