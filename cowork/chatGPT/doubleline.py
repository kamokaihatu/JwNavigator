import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+6,y+7,
        x+18,y+7,
        width=2
    )

    canvas.create_line(
        x+6,y+17,
        x+18,y+17,
        width=2
    )