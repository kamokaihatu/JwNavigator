"""
JwNavigator Icon Library

Icon : 天空図
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+6, x+21, y+24,
        start=-180.0, extent=-180.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_line(
        x+3,y+15, x+21,y+15,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+7, y+6, x+17, y+24,
        start=-180.0, extent=-90.0,
        style=tk.ARC, width=1.7, dash=(1,2)
    )

    canvas.create_arc(
        x+12, y+-3, x+22, y+15,
        start=-90.0, extent=-90.0,
        style=tk.ARC, width=1.7, dash=(1,2)
    )
