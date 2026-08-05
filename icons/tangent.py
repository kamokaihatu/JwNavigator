import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+6,y+8,
        x+18,y+20,
        width=2
    )

    canvas.create_line(
        x+5,y+8,
        x+19,y+8,
        width=2
    )