"""
JwNavigator Icon Library

Icon : SPEED (C078)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+13, y+2, x+5, y+14, x+11, y+14, x+9, y+22, x+19, y+9, x+12.5, y+9,
        fill="black", outline=""
    )
