"""
JwNavigator Icon Library

Icon : 表計算
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+4, x+21, y+20,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+3,y+10, x+21,y+10,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3,y+15, x+21,y+15,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9,y+4, x+9,y+20,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15,y+4, x+15,y+20,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
