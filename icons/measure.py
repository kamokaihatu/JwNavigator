"""
JwNavigator Icon Library

Icon : 測定
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+8.5, x+21, y+15.5,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+6,y+8.5, x+6,y+13.5,
        width=1.1, capstyle=tk.ROUND
    )

    canvas.create_line(
        x+9,y+8.5, x+9,y+11,
        width=1.1, capstyle=tk.ROUND
    )

    canvas.create_line(
        x+12,y+8.5, x+12,y+13.5,
        width=1.1, capstyle=tk.ROUND
    )

    canvas.create_line(
        x+15,y+8.5, x+15,y+11,
        width=1.1, capstyle=tk.ROUND
    )

    canvas.create_line(
        x+18,y+8.5, x+18,y+13.5,
        width=1.1, capstyle=tk.ROUND
    )
