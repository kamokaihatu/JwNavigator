"""
JwNavigator Icon Library

Icon : 天空図 (C072)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+6, x+21, y+24,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+3, y+15, x+21, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+7, y+6, x+17, y+24,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=1, dash=(2, 2)
    )

    canvas.create_line(
        x+12, y+6, x+12, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )
