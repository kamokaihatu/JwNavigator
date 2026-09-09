"""
JwNavigator Icon Library

Icon : 線属性 (C047)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+6, x+21, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+9, x+12, y+11.6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+12, y+14, x+10.2, y+11, x+13.8, y+11,
        fill="black", outline=""
    )

    canvas.create_line(
        x+3, y+18, x+21, y+18,
        width=3, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
