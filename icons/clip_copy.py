"""
JwNavigator Icon Library

Icon : コピー
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+7, x+15, y+21,
        outline="black", width=1.7
    )

    canvas.create_rectangle(
        x+9, y+3, x+21, y+17,
        outline="black", width=1.7
    )
