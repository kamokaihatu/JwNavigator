"""
JwNavigator Icon Library

Icon : 温度計 (G67)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+9, y+4, x+9, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+6, y+2, x+12, y+8,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+15, y+4, x+15, y+14,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+7.5, y+13, x+16.5, y+22,
        outline="black", width=2
    )

    canvas.create_oval(
        x+10, y+15.5, x+14, y+19.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+8, x+12, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
