"""
JwNavigator Icon Library

Icon : 船 (G142)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+14, x+22, y+14, x+19, y+20, x+5, y+20, x+2, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+6, y+14, x+6, y+9, x+16, y+9, x+16, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+11, y+9, x+11, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+11, y+3, x+17, y+6, x+11, y+7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
