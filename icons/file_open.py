"""
JwNavigator Icon Library

Icon : 開く
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3,y+9, x+3,y+6,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+3, y+5, x+5, y+7,
        start=-180.0, extent=-90.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_line(
        x+4,y+5, x+9,y+5, x+11,y+7, x+20,y+7,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+19, y+7, x+21, y+9,
        start=90.0, extent=-90.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_line(
        x+21,y+8, x+21,y+9,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3,y+9, x+5,y+20,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+5, y+19, x+7, y+21,
        start=-180.0, extent=90.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_line(
        x+6,y+21, x+19,y+21,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+18, y+19, x+20, y+21,
        start=-90.0, extent=90.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_line(
        x+20,y+20, x+22,y+10,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+20, y+9, x+22, y+11,
        start=-0.0, extent=90.0,
        style=tk.ARC, width=1.7
    )

    canvas.create_line(
        x+21,y+9, x+4,y+9,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+2.5, y+8.87, x+4.5, y+10.87,
        start=60.0, extent=60.0,
        style=tk.ARC, width=1.7
    )
