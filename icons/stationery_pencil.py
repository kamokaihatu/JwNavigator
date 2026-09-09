"""
JwNavigator Icon Library

Icon : 鉛筆 (G93)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+20, x+16, y+8,
        width=3.5, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+8, x+19, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+4, y+20, x+2, y+22, x+4.6, y+21.6,
        fill="black", outline=""
    )

    canvas.create_line(
        x+6.5, y+17.5, x+13.5, y+10.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )
