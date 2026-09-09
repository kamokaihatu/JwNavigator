"""
JwNavigator Icon Library

Icon : グリッド (G18)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+9, y+3, x+9, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+3, x+15, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+9, x+21, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+15, x+21, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
