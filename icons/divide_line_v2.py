"""
JwNavigator Icon Library

Icon : 分割 (C031)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+12, x+21, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+8, x+9, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+8, x+15, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
