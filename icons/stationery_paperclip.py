"""
JwNavigator Icon Library

Icon : クリップ (G120)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+8, y+8, x+8, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+8, y+14, x+16, y+22,
        start=180, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+16, y+18, x+16, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+10, y+2, x+16, y+8,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+10, y+5, x+10, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+10, y+12, x+14, y+18,
        start=180, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+14, y+15, x+14, y+8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
