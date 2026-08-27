"""
JwNavigator Icon Library

Icon : 分割
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3,y+12, x+10,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14,y+12, x+21,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+11,y+8, x+9,y+16,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15,y+8, x+13,y+16,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
