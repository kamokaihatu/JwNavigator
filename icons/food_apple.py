"""
JwNavigator Icon Library

Icon : りんご (G131)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+4, y+6, x+14, y+22,
        start=90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+10, y+6, x+20, y+22,
        start=-90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+9, y+6, x+15, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+6, x+13, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+13, y+4.5, x+17, y+2, x+16.5, y+5,
        fill="black", outline=""
    )
