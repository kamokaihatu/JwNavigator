"""
JwNavigator Icon Library

Icon : フラグ (G83)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+5, y+22, x+5, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+5, y+3, x+20, y+3, x+16, y+8, x+20, y+13, x+5, y+13,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )
