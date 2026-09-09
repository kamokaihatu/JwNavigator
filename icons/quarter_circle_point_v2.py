"""
JwNavigator Icon Library

Icon : 円周14点 (C077)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4.5, y+4.5, x+19.5, y+19.5,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_oval(
        x+10.2, y+2.7, x+13.8, y+6.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+17.7, y+10.2, x+21.3, y+13.8,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+10.2, y+17.7, x+13.8, y+21.3,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+2.7, y+10.2, x+6.3, y+13.8,
        fill="black", outline=""
    )
