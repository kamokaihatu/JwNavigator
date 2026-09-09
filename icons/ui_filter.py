"""
JwNavigator Icon Library

Icon : フィルタ (G53)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+4, x+21, y+4, x+14, y+13, x+14, y+20, x+10, y+22, x+10, y+13,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )
