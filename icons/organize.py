import tkinter as tk

def draw(canvas, x=0, y=0):

    for yy in (6,11,16):

        canvas.create_line(
            x+6,
            y+yy,
            x+18,
            y+yy,
            width=2
        )