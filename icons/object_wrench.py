"""
JwNavigator Icon Library

Icon : レンチ (G88)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+12, y+2, x+22, y+12,
        start=90, extent=300,
        style=tk.ARC, outline="black", width=3
    )

    canvas.create_line(
        x+14.5, y+9.5, x+4, y+20,
        width=3.5, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
