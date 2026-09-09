"""
JwNavigator Icon Library

Icon : お気に入り (G25)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+3.5, x+14.38, y+9.22, x+20.56, y+9.72, x+15.85, y+13.75, x+17.29, y+19.78, x+12, y+16.55, x+6.71, y+19.78, x+8.15, y+13.75, x+3.44, y+9.72, x+9.62, y+9.22,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )
