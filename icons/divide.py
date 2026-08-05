import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+5,y+12,
        x+19,y+12,
        width=2
    )

    canvas.create_line(
        x+12,y+8,
        x+12,y+16,
        width=2
    )