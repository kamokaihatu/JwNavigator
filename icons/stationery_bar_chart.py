"""
JwNavigator Icon Library

Icon : 棒グラフ (G98)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+21, x+22, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+4, y+12, x+8, y+21,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+10, y+5, x+14, y+21,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+16, y+9, x+20, y+21,
        fill="black", outline=""
    )
