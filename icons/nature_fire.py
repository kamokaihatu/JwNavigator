"""
JwNavigator Icon Library

Icon : 火 (G153)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+12, y+2, x+18, y+9, x+19, y+15, x+15, y+21, x+9, y+21, x+5, y+15, x+7, y+9, x+9, y+12, x+12, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )

    canvas.create_line(
        x+12, y+12, x+15, y+16, x+12, y+20, x+9, y+16, x+12, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )
