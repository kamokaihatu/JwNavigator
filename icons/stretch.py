"""
JwNavigator Icon Library

Icon : 伸縮
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4,y+12, x+12,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12,y+12, x+21,y+12,
        width=1, capstyle=tk.ROUND, dash=(1,2)
    )

    canvas.create_line(
        x+13,y+4, x+21,y+4,
        width=1.3, capstyle=tk.ROUND
    )

    canvas.create_line(
        x+16,y+1, x+21,y+4, x+16,y+7,
        width=1.3, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
