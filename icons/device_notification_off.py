"""
JwNavigator Icon Library

Icon : 通知オフ (G79)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+5, y+4, x+19, y+18,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+5, y+11, x+5, y+17, x+3, y+19, x+21, y+19, x+19, y+17, x+19, y+11,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+9, y+17, x+15, y+23,
        start=180, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+3, y+3, x+21, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
