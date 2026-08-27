"""
JwNavigator Icon Library

Icon : 属性取得
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+14, y+2, x+20, y+8,
        fill="black", outline=""
    )

    canvas.create_line(
        x+14.5,y+7.5, x+7.5,y+14.5,
        width=2.3, capstyle=tk.ROUND
    )

    canvas.create_oval(
        x+4.2, y+16.2, x+6.8, y+18.8,
        fill="black", outline=""
    )
