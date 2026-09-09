"""
JwNavigator Icon Library

Icon : 木 (G147)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+2, x+19, y+9, x+15, y+9, x+21, y+16, x+3, y+16, x+9, y+9, x+5, y+9,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+10.5, y+16, x+13.5, y+22,
        fill="black", outline=""
    )
