"""
JwNavigator Icon Library

Icon : 基本設定
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+8.5, y+8.5, x+15.5, y+15.5,
        outline="black", width=1.7
    )

    canvas.create_line(
        x+12,y+3, x+12,y+6,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12,y+18, x+12,y+21,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3,y+12, x+6,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+18,y+12, x+21,y+12,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+5.5,y+5.5, x+7.75,y+7.75,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16.25,y+16.25, x+18.5,y+18.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+18.5,y+5.5, x+16.25,y+7.75,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7.75,y+16.25, x+5.5,y+18.5,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
