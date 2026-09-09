"""
JwNavigator Icon Library

Icon : うさぎ (G108)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+5.5, y+8.5, x+18.5, y+21.5,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6.5, y+1, x+10.5, y+11,
        outline="black", width=2
    )

    canvas.create_oval(
        x+13.5, y+1, x+17.5, y+11,
        outline="black", width=2
    )

    canvas.create_oval(
        x+8.8, y+12.8, x+11.2, y+15.2,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+12.8, y+12.8, x+15.2, y+15.2,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+11, y+16, x+13, y+18,
        fill="black", outline=""
    )
