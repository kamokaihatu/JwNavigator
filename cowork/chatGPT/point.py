import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+10, y+10,
        x+14, y+14,
        fill="black",
        outline=""
    )