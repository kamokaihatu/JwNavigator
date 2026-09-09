"""
JwNavigator Icon Library

Icon : ピザ (G137)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+4, x+21, y+4, x+12, y+21,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+3, y+-3, x+21, y+11,
        start=200, extent=140,
        style=tk.ARC, outline="black", width=1
    )

    canvas.create_oval(
        x+8.6, y+6.6, x+11.4, y+9.4,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+13.1, y+7.6, x+15.9, y+10.4,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.6, y+12.1, x+13.4, y+14.9,
        fill="black", outline=""
    )
