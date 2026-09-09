"""
JwNavigator Icon Library

Icon : 動画 (G75)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+2, y+6, x+16, y+18,
        outline="black", width=2
    )

    canvas.create_polygon(
        x+16, y+10, x+22, y+6, x+22, y+18, x+16, y+14,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )
