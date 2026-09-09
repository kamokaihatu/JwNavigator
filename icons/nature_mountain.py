"""
JwNavigator Icon Library

Icon : 山 (G150)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+20, x+9, y+6, x+13, y+13, x+16, y+8, x+22, y+20, x+2, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+10, x+9, y+12, x+11, y+10,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+9.7, x+16, y+11, x+17, y+9.7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
