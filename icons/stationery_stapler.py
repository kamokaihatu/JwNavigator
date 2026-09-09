"""
JwNavigator Icon Library

Icon : ホッチキス (G122)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+8, x+18, y+4, x+21, y+7, x+6, y+11,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+8, x+3, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+3, y+16, x+21, y+20,
        outline="black", width=2
    )

    canvas.create_line(
        x+9, y+12, x+18, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
