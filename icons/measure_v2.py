"""
JwNavigator Icon Library

Icon : 測定 (C062)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+11, x+21, y+11,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+3, y+11, x+3, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+6, y+11, x+6, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+11, x+9, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+11, x+12, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+15, y+11, x+15, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+18, y+11, x+18, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+21, y+11, x+21, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
