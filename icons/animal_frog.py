"""
JwNavigator Icon Library

Icon : カエル (G116)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+8, x+22, y+21,
        outline="black", width=2
    )

    canvas.create_oval(
        x+3.5, y+4.5, x+10.5, y+11.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+13.5, y+4.5, x+20.5, y+11.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+5.7, y+6.7, x+8.3, y+9.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+15.7, y+6.7, x+18.3, y+9.3,
        fill="black", outline=""
    )

    canvas.create_arc(
        x+6, y+10, x+18, y+20,
        start=200, extent=140,
        style=tk.ARC, outline="black", width=1
    )
