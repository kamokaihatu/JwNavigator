"""
JwNavigator Icon Library

Icon : 保存 (C042)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+7, y+2, x+14, y+2, x+17, y+5, x+17, y+12, x+7, y+12, x+7, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14, y+2, x+14, y+5, x+17, y+5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+8, x+12, y+14.6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+12, y+17, x+10.2, y+14, x+13.8, y+14,
        fill="black", outline=""
    )

    canvas.create_line(
        x+4, y+16, x+4, y+21, x+20, y+21, x+20, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
