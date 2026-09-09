"""
JwNavigator Icon Library

Icon : ドライバー (G90)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+20, x+12, y+12,
        width=3, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+11, y+9, x+14, y+6, x+18, y+10, x+15, y+13,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+8, x+21, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
