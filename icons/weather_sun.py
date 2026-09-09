"""
JwNavigator Icon Library

Icon : 太陽 (G61)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+7.5, y+7.5, x+16.5, y+16.5,
        outline="black", width=2
    )

    canvas.create_line(
        x+19, y+12, x+21.5, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16.95, y+16.95, x+18.72, y+18.72,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+19, x+12, y+21.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7.05, y+16.95, x+5.28, y+18.72,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+5, y+12, x+2.5, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7.05, y+7.05, x+5.28, y+5.28,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+5, x+12, y+2.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16.95, y+7.05, x+18.72, y+5.28,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
