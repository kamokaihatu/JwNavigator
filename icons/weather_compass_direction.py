"""
JwNavigator Icon Library

Icon : 方位 (G68)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+2, x+22, y+22,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+12, y+3.5, x+14.5, y+12, x+12, y+10, x+9.5, y+12,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+12, y+20.5, x+14.5, y+12, x+12, y+14, x+9.5, y+12,
        fill="", outline="black", width=1, joinstyle=tk.ROUND
    )
