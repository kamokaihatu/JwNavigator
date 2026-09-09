"""
JwNavigator Icon Library

Icon : その他 (G32)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3.2, y+10.2, x+6.8, y+13.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.2, y+10.2, x+13.8, y+13.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+17.2, y+10.2, x+20.8, y+13.8,
        fill="black", outline=""
    )
