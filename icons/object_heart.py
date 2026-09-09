"""
JwNavigator Icon Library

Icon : ハート (G85)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+2, y+3, x+12, y+13,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+12, y+3, x+22, y+13,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+2, y+8, x+12, y+21, x+22, y+8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
