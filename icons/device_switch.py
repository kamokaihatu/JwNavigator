"""
JwNavigator Icon Library

Icon : スイッチ (G58)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+7, x+22, y+17,
        outline="black", width=2
    )

    canvas.create_oval(
        x+4, y+9, x+10, y+15,
        fill="black", outline=""
    )
