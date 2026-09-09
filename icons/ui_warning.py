"""
JwNavigator Icon Library

Icon : 警告 (G05)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+12, y+3, x+22, y+21, x+2, y+21,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+9, x+12, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10.6, y+16.1, x+13.4, y+18.9,
        fill="black", outline=""
    )
