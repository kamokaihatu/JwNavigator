"""
JwNavigator Icon Library

Icon : ズームアウト (G16)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3.5, y+3.5, x+16.5, y+16.5,
        outline="black", width=2
    )

    canvas.create_line(
        x+15, y+15, x+21, y+21,
        width=3, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+10, x+13, y+10,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
