"""
JwNavigator Icon Library

Icon : 選択図 (C069)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+3, x+21, y+21,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_polygon(
        x+7, y+11.5, x+12, y+7, x+17, y+11.5,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+8, y+11.5, x+16, y+17,
        fill="black", outline=""
    )
