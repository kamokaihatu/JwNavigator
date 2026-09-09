"""
JwNavigator Icon Library

Icon : 目玉焼き (G135)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+5, x+22, y+20,
        outline="black", width=2
    )

    canvas.create_oval(
        x+8, y+8, x+16, y+16,
        fill="black", outline=""
    )
