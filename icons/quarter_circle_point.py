"""
JwNavigator Icon Library

Icon : 円周14点
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4.5, y+4.5, x+19.5, y+19.5,
        outline="black", width=1.5
    )

    canvas.create_oval(
        x+10.7, y+3.2, x+13.3, y+5.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.2, y+10.7, x+20.8, y+13.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.7, y+18.2, x+13.3, y+20.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+3.2, y+10.7, x+5.8, y+13.3,
        fill="black", outline=""
    )
