"""
JwNavigator Icon Library

Icon : 新規
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+6,y+3, x+14,y+3, x+18,y+7, x+18,y+21, x+6,y+21,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14,y+3, x+14,y+7, x+18,y+7,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9,y+13, x+15,y+13,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12,y+10, x+12,y+16,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
