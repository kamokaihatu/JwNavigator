"""
JwNavigator Icon Library

Icon : 更新 (G11)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+4, y+4, x+20, y+20,
        start=30, extent=300,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_polygon(
        x+19, y+4.5, x+16.36, y+7.14, x+15.43, y+3.41,
        fill="black", outline=""
    )
