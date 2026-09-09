"""
JwNavigator Icon Library

Icon : ハンマー (G89)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+6, x+12, y+3, x+18, y+6, x+15, y+11, x+6, y+11,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10.5, y+11, x+7, y+21,
        width=3, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
