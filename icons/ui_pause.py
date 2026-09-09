"""
JwNavigator Icon Library

Icon : 一時停止 (G39)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+5, y+4, x+9, y+20,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+15, y+4, x+19, y+20,
        fill="black", outline=""
    )
