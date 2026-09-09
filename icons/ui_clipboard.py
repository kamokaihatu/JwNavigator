"""
JwNavigator Icon Library

Icon : クリップボード (G46)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+5, y+5, x+19, y+21,
        outline="black", width=2
    )

    canvas.create_rectangle(
        x+9, y+3, x+15, y+7,
        outline="black", width=2
    )

    canvas.create_line(
        x+8, y+11, x+16, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+15, x+16, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
