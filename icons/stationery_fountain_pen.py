"""
JwNavigator Icon Library

Icon : 万年筆 (G128)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+21, x+10, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+10, y+14, x+13, y+7, x+19, y+3, x+21, y+5, x+17, y+11,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+14, x+16, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+15, y+7, x+17, y+9,
        fill="black", outline=""
    )
