"""
JwNavigator Icon Library

Icon : タグジャンプ
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4,y+4, x+12,y+4, x+20,y+12, x+12,y+20, x+4,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+6.8, y+6.8, x+9.2, y+9.2,
        fill="black", outline=""
    )
