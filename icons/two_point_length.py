"""
JwNavigator Icon Library

Icon : 2点長 (C054)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2.5, y+15.5, x+5.5, y+18.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.5, y+5.5, x+21.5, y+8.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+12, x+5.7, y+15.94,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+4, y+17, x+5.32, y+14.4, x+6.91, y+16.95,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+12, x+18.3, y+8.06,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+20, y+7, x+18.68, y+9.6, x+17.09, y+7.05,
        fill="black", outline=""
    )
