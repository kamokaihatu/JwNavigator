"""
JwNavigator Icon Library

Icon : マウス (G43)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+6, y+9, x+6, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+6, y+3, x+18, y+15,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+6, y+10, x+18, y+22,
        start=180, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+18, y+9, x+18, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+3, x+12, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+6, y+9, x+18, y+9,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
