"""
JwNavigator Icon Library

Icon : 設定 (G02)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+2.5, x+14.49, y+5.99, x+18.72, y+5.28, x+18.01, y+9.51, x+21.5, y+12, x+18.01, y+14.49, x+18.72, y+18.72, x+14.49, y+18.01, x+12, y+21.5, x+9.51, y+18.01, x+5.28, y+18.72, x+5.99, y+14.49, x+2.5, y+12, x+5.99, y+9.51, x+5.28, y+5.28, x+9.51, y+5.99,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+9.5, y+9.5, x+14.5, y+14.5,
        outline="black", width=2
    )
