"""
JwNavigator Icon Library

Icon : 整理
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4,y+6, x+17,y+6,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4,y+12, x+17,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4,y+18, x+13,y+18,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16,y+15, x+20,y+19,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+20,y+15, x+16,y+19,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
