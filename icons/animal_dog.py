"""
JwNavigator Icon Library

Icon : 犬 (G107)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+4, x+20, y+20,
        outline="black", width=2
    )

    canvas.create_oval(
        x+2, y+6, x+7, y+18,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+17, y+6, x+22, y+18,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+7.7, y+9.7, x+10.3, y+12.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+13.7, y+9.7, x+16.3, y+12.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10, y+14, x+14, y+17,
        fill="black", outline=""
    )
