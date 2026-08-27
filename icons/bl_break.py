"""
JwNavigator Icon Library

Icon : ブロック解除
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3,y+7, x+3,y+3, x+7,y+3,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+17,y+3, x+21,y+3, x+21,y+7,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3,y+17, x+3,y+21, x+7,y+21,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+21,y+17, x+21,y+21, x+17,y+21,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+8.5, y+8.5, x+12, y+12,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+13.5, y+7, x+17, y+10.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+9.5, y+13.5, x+13, y+17,
        fill="black", outline=""
    )
