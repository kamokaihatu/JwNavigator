"""
JwNavigator Icon Library

Icon : 画像編集 (C074)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+5, x+21, y+19,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6.5, y+8, x+9.5, y+11,
        outline="black", width=1
    )

    canvas.create_line(
        x+3, y+17, x+9, y+11.5, x+13, y+15, x+18, y+10, x+21, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
