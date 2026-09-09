"""
JwNavigator Icon Library

Icon : 線 (B01)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+20, x+20, y+4,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+2.5, y+18.5, x+5.5, y+21.5,
        fill="black", outline=""
    )

    canvas.create_oval(
        x+18.5, y+2.5, x+21.5, y+5.5,
        fill="black", outline=""
    )
