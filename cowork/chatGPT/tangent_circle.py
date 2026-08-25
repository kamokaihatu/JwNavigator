import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+7,y+7,
        x+17,y+17,
        width=2
    )

    canvas.create_line(
        x+5,y+19,
        x+19,y+5,
        dash=(2,2)
    )