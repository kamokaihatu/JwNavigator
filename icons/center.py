"""
JwNavigator Icon Library

Icon : 中心線
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+12, y+2, x+12, y+22,
        width=1.5, capstyle=tk.ROUND, dash=(4, 2)
    )

    canvas.create_line(
        x+2, y+12, x+22, y+12,
        width=1.5, capstyle=tk.ROUND, dash=(4, 2)
    )
