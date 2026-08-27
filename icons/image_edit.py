"""
JwNavigator Icon Library

Icon : 画像編集
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+5, x+21, y+19,
        outline="black", width=1.7
    )

    canvas.create_oval(
        x+6.4, y+8.4, x+9.6, y+11.6,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+3,y+16.5, x+9,y+11, x+13.5,y+15, x+18,y+10, x+21,y+13,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
