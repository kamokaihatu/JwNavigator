"""
JwNavigator Icon Library

Icon : 下へ (G34)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+12, y+4, x+12, y+16.8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+12, y+20, x+9.6, y+16, x+14.4, y+16,
        fill="black", outline=""
    )
