import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+12,y+4,
        x+12,y+20,
        dash=(2,2)
    )

    canvas.create_line(
        x+4,y+12,
        x+20,y+12,
        dash=(2,2)
    )