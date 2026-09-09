"""
JwNavigator Icon Library

Icon : 寸法 (B12)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+17, x+20, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+5, x+4, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+20, y+5, x+20, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+8, x+6, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+4, y+8, x+6.5, y+6.5, x+6.5, y+9.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+8, x+18, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+20, y+8, x+17.5, y+9.5, x+17.5, y+6.5,
        fill="black", outline=""
    )
