"""
JwNavigator Icon Library

Icon : 電球 (G56)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+5, y+2, x+19, y+16,
        start=-40, extent=260,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+9.5, y+14, x+9, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14.5, y+14, x+15, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+18, x+15, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+21, x+14, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+6, x+12, y+11,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9.5, y+8.5, x+14.5, y+8.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
