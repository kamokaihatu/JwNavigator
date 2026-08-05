"""
JwNavigator Icon Library

Icon : Text
Size : 24×24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_text(
        x+12,
        y+12,
        text="A",
        font=("Arial",14,"bold"),
        fill="black"
    )