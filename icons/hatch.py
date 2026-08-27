"""
JwNavigator Icon Library

Icon : ハッチ
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3.5, y+3.5, x+20.5, y+20.5,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+3.5,y+7, x+7,y+3.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3.5,y+12, x+12,y+3.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3.5,y+17, x+17,y+3.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+5,y+20.5, x+20.5,y+5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10,y+20.5, x+20.5,y+10,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15,y+20.5, x+20.5,y+15,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
