"""
JwNavigator Icon Library

Icon : 元に戻す
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+6, y+7, x+18, y+19,
        start=-0.0, extent=180.0,
        style=tk.ARC, width=3
    )

    canvas.create_polygon(
        x+6,y+17, x+2,y+12, x+10,y+12,
        fill="black"
    )
