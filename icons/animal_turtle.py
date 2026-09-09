"""
JwNavigator Icon Library

Icon : カメ (G113)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+4, y+4, x+20, y+20,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+4, y+12, x+20, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+19, y+11.5, x+24, y+16.5,
        outline="black", width=2
    )

    canvas.create_line(
        x+7, y+12, x+5, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+17, y+12, x+19, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+4.5, x+12, y+9, x+14, y+4.5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
