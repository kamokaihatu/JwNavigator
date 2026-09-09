"""
JwNavigator Icon Library

Icon : クラウド (G102)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+2, y+9, x+12, y+19,
        start=90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+6, y+4, x+16, y+14,
        start=20, extent=160,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+12, y+8, x+22, y+18,
        start=-70, extent=210,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+7, y+19, x+17, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
