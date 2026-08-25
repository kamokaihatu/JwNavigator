import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+5,y+17,
        x+10,y+9,
        x+15,y+14,
        x+19,y+6,
        width=2
    )